"""Backfills demo backtest rows against real historical game outcomes.

There's no accumulated real sentiment history on day one of this app, so
the backtest page would otherwise start empty. This seeds `is_demo_seed=True`
rows, a synthetic-but-plausible "sentiment favorite" (correct ~62% of the
time, a believable-but-imperfect signal) paired with real final scores from
ESPN's scoreboard across the back half of the season. Clearly distinguished
from real accumulated results (is_demo_seed=False) everywhere it's surfaced.

Usage: ./venv/bin/python -m app.seed.seed_backtest_demo
"""

import random
from datetime import datetime, timedelta

from sqlalchemy import select

from app.db.models import BacktestResult, Team
from app.db.session import SessionLocal, init_db
from app.services import live_games
from app.services.text_utils import team_key

DAYS_TO_SAMPLE = 45
SENTIMENT_HIT_RATE = 0.62


def run(days_to_sample: int = DAYS_TO_SAMPLE) -> int:
    init_db()
    db = SessionLocal()
    try:
        teams = {team_key(t.name): t for t in db.execute(select(Team)).scalars().all()}
        existing_ids = set(db.execute(select(BacktestResult.game_id)).scalars().all())

        count = 0
        today = datetime.utcnow()
        for days_ago in range(15, 15 + days_to_sample):  # skip the last ~2 weeks for the "real" path to own
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

                actual_winner = home_team if g["home_score"] > g["away_score"] else away_team
                actual_loser = away_team if actual_winner is home_team else home_team
                hit = random.random() < SENTIMENT_HIT_RATE
                favored = actual_winner if hit else actual_loser

                db.add(
                    BacktestResult(
                        game_id=g["id"],
                        game_date=datetime.strptime(g["date"][:10], "%Y-%m-%d"),
                        sentiment_favored_team_id=favored.id,
                        actual_winner_team_id=actual_winner.id,
                        sentiment_confidence=round(random.uniform(0.15, 0.55), 3),
                        correct=hit,
                        is_demo_seed=True,
                    )
                )
                existing_ids.add(g["id"])
                count += 1

        db.commit()
        print(f"seeded {count} demo backtest rows")
        return count
    finally:
        db.close()


if __name__ == "__main__":
    run()
