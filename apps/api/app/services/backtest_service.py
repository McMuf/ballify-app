from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import BacktestResult, Team
from app.services import live_games, sentiment
from app.services.text_utils import team_key


def check_recent_games(db: Session, days_back: int = 3) -> int:
    """Real (non-demo) backtesting: for newly-completed games, compare
    whichever team had the higher sentiment gauge as of game day against
    the actual winner. Only meaningful once real sentiment history has
    accumulated for both teams, silently skips games where it hasn't."""
    teams = {team_key(t.name): t for t in db.execute(select(Team)).scalars().all()}
    existing_ids = set(db.execute(select(BacktestResult.game_id)).scalars().all())

    count = 0
    today = datetime.utcnow()
    for days_ago in range(days_back):
        date_str = (today - timedelta(days=days_ago)).strftime("%Y%m%d")
        try:
            games = live_games.fetch_scoreboard(date_str)
        except Exception:
            continue
        for g in games:
            if g["state"] != "final" or g["id"] in existing_ids:
                continue
            home_team = teams.get(g["home_team_key"])
            away_team = teams.get(g["away_team_key"])
            if home_team is None or away_team is None:
                continue

            game_date = datetime.strptime(g["date"][:10], "%Y-%m-%d")
            home_gauge = sentiment.gauge_for(db, "team", home_team.id, window_hours=72, asof=game_date)
            away_gauge = sentiment.gauge_for(db, "team", away_team.id, window_hours=72, asof=game_date)
            if home_gauge["score"] is None or away_gauge["score"] is None:
                continue  # no real sentiment coverage for this matchup yet

            favored = home_team if home_gauge["score"] >= away_gauge["score"] else away_team
            actual_winner = home_team if g["home_score"] > g["away_score"] else away_team
            confidence = abs(home_gauge["score"] - away_gauge["score"])

            db.add(
                BacktestResult(
                    game_id=g["id"],
                    game_date=game_date,
                    sentiment_favored_team_id=favored.id,
                    actual_winner_team_id=actual_winner.id,
                    sentiment_confidence=round(confidence, 3),
                    correct=favored.id == actual_winner.id,
                    is_demo_seed=False,
                )
            )
            existing_ids.add(g["id"])
            count += 1

    db.commit()
    return count


def _week_bucket(d: datetime) -> str:
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%Y-%m-%d")


def summary(db: Session) -> dict:
    results = db.execute(select(BacktestResult).order_by(BacktestResult.game_date)).scalars().all()
    if not results:
        return {
            "total_games": 0, "overall_accuracy": None, "demo_seed_count": 0,
            "real_count": 0, "accuracy_over_time": [], "recent_results": [],
        }

    demo_count = sum(1 for r in results if r.is_demo_seed)
    real_count = len(results) - demo_count
    overall_accuracy = sum(1 for r in results if r.correct) / len(results)

    buckets: dict[str, list[BacktestResult]] = {}
    for r in results:
        buckets.setdefault(_week_bucket(r.game_date), []).append(r)
    accuracy_over_time = [
        {
            "week": week,
            "accuracy": round(sum(1 for r in rows if r.correct) / len(rows), 3),
            "games": len(rows),
        }
        for week, rows in sorted(buckets.items())
    ]

    teams = {t.id: t for t in db.execute(select(Team)).scalars().all()}

    def team_abbr(team_id: int | None) -> str:
        t = teams.get(team_id) if team_id else None
        return t.abbreviation if t else "?"

    recent = sorted(results, key=lambda r: r.game_date, reverse=True)[:30]
    recent_results = [
        {
            "game_id": r.game_id,
            "game_date": r.game_date.strftime("%Y-%m-%d"),
            "favored": team_abbr(r.sentiment_favored_team_id),
            "actual_winner": team_abbr(r.actual_winner_team_id),
            "correct": r.correct,
            "confidence": r.sentiment_confidence,
            "is_demo_seed": r.is_demo_seed,
        }
        for r in recent
    ]

    return {
        "total_games": len(results),
        "overall_accuracy": round(overall_accuracy, 3),
        "demo_seed_count": demo_count,
        "real_count": real_count,
        "accuracy_over_time": accuracy_over_time,
        "recent_results": recent_results,
    }
