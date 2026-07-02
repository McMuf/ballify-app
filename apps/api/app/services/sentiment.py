import re
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.db.models import Player, SentimentSnapshot, Team
from app.services import news_service, reddit_service
from app.services.text_utils import fold

_analyzer = SentimentIntensityAnalyzer()


def score_text(text: str) -> float:
    """-1 (bearish) .. 1 (bullish), via VADER's compound score."""
    return _analyzer.polarity_scores(text)["compound"]


def _mentions(text: str, players: list[Player], teams: list[Team]) -> tuple[list[Player], list[Team]]:
    folded = fold(text)
    matched_players = [p for p in players if fold(p.full_name) in folded]
    matched_teams = []
    for t in teams:
        # word-boundary match on the nickname (e.g. "Magic") to cut down false
        # positives from common-English team names inside unrelated prose
        if re.search(rf"\b{re.escape(fold(t.name))}\b", folded):
            matched_teams.append(t)
    return matched_players, matched_teams


def _existing_keys(db: Session, source: str, since: datetime) -> set[tuple[str, int, datetime]]:
    """(subject_type, subject_id, captured_at) triples already stored for this
    source — re-running a refresh on an RSS/subreddit feed that hasn't moved
    should not re-insert (and silently inflate mention volume for) the same
    article/post every time."""
    rows = db.execute(
        select(SentimentSnapshot.subject_type, SentimentSnapshot.subject_id, SentimentSnapshot.captured_at)
        .where(SentimentSnapshot.source == source)
        .where(SentimentSnapshot.captured_at >= since)
    ).all()
    return {(r[0], r[1], r[2]) for r in rows}


def refresh_news_sentiment(db: Session) -> int:
    players = db.execute(select(Player).where(Player.is_active.is_(True))).scalars().all()
    teams = db.execute(select(Team)).scalars().all()
    seen = _existing_keys(db, "espn_news", datetime.utcnow() - timedelta(days=7))

    count = 0
    for article in news_service.fetch_espn_news():
        text = f"{article['title']}. {article['summary']}"
        score = score_text(text)
        matched_players, matched_teams = _mentions(text, players, teams)
        captured_at = article["published_at"]
        for p in matched_players:
            key = ("player", p.id, captured_at)
            if key in seen:
                continue
            seen.add(key)
            db.add(
                SentimentSnapshot(
                    subject_type="player", subject_id=p.id, source="espn_news",
                    score=score, volume=1, captured_at=captured_at,
                )
            )
            count += 1
        for t in matched_teams:
            key = ("team", t.id, captured_at)
            if key in seen:
                continue
            seen.add(key)
            db.add(
                SentimentSnapshot(
                    subject_type="team", subject_id=t.id, source="espn_news",
                    score=score, volume=1, captured_at=captured_at,
                )
            )
            count += 1
    db.commit()
    return count


def refresh_reddit_sentiment(db: Session) -> int:
    if reddit_service.get_client() is None:
        return 0

    players = db.execute(select(Player).where(Player.is_active.is_(True))).scalars().all()
    teams = db.execute(select(Team)).scalars().all()
    teams_by_abbr = {t.abbreviation: t for t in teams}
    seen = _existing_keys(db, "reddit", datetime.utcnow() - timedelta(days=7))

    count = 0

    def score_posts(posts: list[dict], home_team: Team | None) -> None:
        nonlocal count
        for post in posts:
            text = f"{post['title']}. {post['selftext']}"
            score = score_text(text)
            matched_players, matched_teams = _mentions(text, players, teams)
            if home_team and home_team not in matched_teams:
                matched_teams.append(home_team)
            captured_at = post["created_at"]
            for p in matched_players:
                key = ("player", p.id, captured_at)
                if key in seen:
                    continue
                seen.add(key)
                db.add(
                    SentimentSnapshot(
                        subject_type="player", subject_id=p.id, source="reddit",
                        score=score, volume=1, captured_at=captured_at,
                    )
                )
                count += 1
            for t in matched_teams:
                key = ("team", t.id, captured_at)
                if key in seen:
                    continue
                seen.add(key)
                db.add(
                    SentimentSnapshot(
                        subject_type="team", subject_id=t.id, source="reddit",
                        score=score, volume=1, captured_at=captured_at,
                    )
                )
                count += 1

    score_posts(reddit_service.fetch_recent_posts("nba", limit=25), None)
    for abbr, subreddit in reddit_service.TEAM_SUBREDDITS.items():
        team = teams_by_abbr.get(abbr)
        score_posts(reddit_service.fetch_recent_posts(subreddit, limit=8), team)

    db.commit()
    return count


def gauge_for(db: Session, subject_type: str, subject_id: int, window_hours: int = 72) -> dict:
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    rows = (
        db.execute(
            select(SentimentSnapshot)
            .where(SentimentSnapshot.subject_type == subject_type)
            .where(SentimentSnapshot.subject_id == subject_id)
            .where(SentimentSnapshot.captured_at >= cutoff)
        )
        .scalars()
        .all()
    )
    if not rows:
        return {"score": None, "label": "no data", "volume": 0, "by_source": {}}

    avg = sum(r.score for r in rows) / len(rows)
    by_source: dict[str, list[float]] = {}
    for r in rows:
        by_source.setdefault(r.source, []).append(r.score)
    by_source_avg = {k: round(sum(v) / len(v), 3) for k, v in by_source.items()}

    return {
        "score": round(avg, 3),
        "label": _label(avg),
        "volume": len(rows),
        "by_source": by_source_avg,
    }


def _label(score: float) -> str:
    if score >= 0.3:
        return "bullish"
    if score >= 0.1:
        return "leaning bullish"
    if score <= -0.3:
        return "bearish"
    if score <= -0.1:
        return "leaning bearish"
    return "neutral"
