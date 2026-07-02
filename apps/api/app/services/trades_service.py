from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Player, Team, TradeRumor
from app.services import news_service, reddit_service
from app.services.text_utils import find_mentions, fold

TRADE_KEYWORDS = [
    "trade", "traded", "trading", "sign-and-trade", "acquire", "acquired",
    "sending", "deal", "agrees to", "agreement", "waived", "buyout",
]

# Reporters widely regarded as top NBA insiders — a mention of their name in a
# headline/byline is the standard signal readers use to gauge how solid a
# report is, long before the trade is officially announced.
TIER_1_INSIDERS = [
    "shams charania", "adrian wojnarowski", "marc stein", "chris haynes",
    "jake fischer", "brian windhorst", "ramona shelburne",
]


def _is_trade_related(text: str) -> bool:
    folded = fold(text)
    return any(kw in folded for kw in TRADE_KEYWORDS)


def _credibility_tier(text: str, source_name: str) -> int:
    folded = fold(text)
    if any(name in folded for name in TIER_1_INSIDERS) or folded.startswith("sources:"):
        return 1
    if source_name == "ESPN":
        return 2
    return 3


def _existing_urls(db: Session, since: datetime) -> set[str]:
    rows = db.execute(
        select(TradeRumor.url).where(TradeRumor.published_at >= since)
    ).scalars().all()
    return set(rows)


def refresh_trade_rumors(db: Session) -> int:
    players = db.execute(select(Player).where(Player.is_active.is_(True))).scalars().all()
    teams = db.execute(select(Team)).scalars().all()
    seen_urls = _existing_urls(db, datetime.utcnow() - timedelta(days=14))

    count = 0

    for article in news_service.fetch_espn_news():
        text = f"{article['title']}. {article['summary']}"
        if not _is_trade_related(text):
            continue
        if article["link"] in seen_urls:
            continue
        seen_urls.add(article["link"])

        matched_players, matched_teams = find_mentions(text, players, teams)
        db.add(
            TradeRumor(
                headline=article["title"],
                url=article["link"],
                source_name=article["source_name"],
                credibility_tier=_credibility_tier(text, article["source_name"]),
                players_mentioned=", ".join(p.full_name for p in matched_players),
                teams_mentioned=", ".join(t.abbreviation for t in matched_teams),
                published_at=article["published_at"],
            )
        )
        count += 1

    if reddit_service.get_client() is not None:
        for post in reddit_service.fetch_recent_posts("nba", limit=40):
            text = f"{post['title']}. {post['selftext']}"
            if not _is_trade_related(text):
                continue
            if post["permalink"] in seen_urls:
                continue
            seen_urls.add(post["permalink"])

            matched_players, matched_teams = find_mentions(text, players, teams)
            db.add(
                TradeRumor(
                    headline=post["title"],
                    url=post["permalink"],
                    source_name="Reddit r/nba",
                    credibility_tier=_credibility_tier(text, "Reddit r/nba"),
                    players_mentioned=", ".join(p.full_name for p in matched_players),
                    teams_mentioned=", ".join(t.abbreviation for t in matched_teams),
                    published_at=post["created_at"],
                )
            )
            count += 1

    db.commit()
    return count
