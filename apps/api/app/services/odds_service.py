import re

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import OddsSnapshot, Team
from app.services import live_games
from app.services.text_utils import fold, team_key

ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"


def fetch_odds_events() -> list[dict]:
    """[] when unconfigured — same graceful-degrade pattern as Reddit."""
    settings = get_settings()
    if not settings.odds_configured:
        return []
    params = {
        "apiKey": settings.odds_api_key,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american",
    }
    resp = httpx.get(ODDS_API_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _implied_prob(american_odds: float) -> float:
    if american_odds < 0:
        return -american_odds / (-american_odds + 100)
    return 100 / (american_odds + 100)


def parse_event_odds(event: dict) -> dict | None:
    """Averages the de-vigged implied home/away probability across all books
    offering a moneyline (h2h) market on this game. None if no book has one."""
    home_name = event.get("home_team", "")
    away_name = event.get("away_team", "")
    home_probs, away_probs = [], []

    for bookmaker in event.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") != "h2h":
                continue
            outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
            if home_name not in outcomes or away_name not in outcomes:
                continue
            home_raw = _implied_prob(outcomes[home_name])
            away_raw = _implied_prob(outcomes[away_name])
            total = home_raw + away_raw
            if total <= 0:
                continue
            # de-vig: raw implied probabilities sum to >1 (the sportsbook's
            # margin) — normalize so home+away read as a fair probability
            home_probs.append(home_raw / total)
            away_probs.append(away_raw / total)

    if not home_probs:
        return None
    return {
        "home_team_name": home_name,
        "away_team_name": away_name,
        "commence_time": event.get("commence_time"),
        "home_implied_prob": round(sum(home_probs) / len(home_probs), 3),
        "away_implied_prob": round(sum(away_probs) / len(away_probs), 3),
        "bookmaker_count": len(home_probs),
    }


def match_team(full_name: str, teams: list[Team]) -> Team | None:
    """The Odds API gives full team names ('Los Angeles Lakers'); match by
    nickname word-boundary the same way trade/sentiment mention-matching
    does, since city naming has proven inconsistent across providers."""
    folded = fold(full_name)
    for t in teams:
        if re.search(rf"\b{re.escape(fold(t.name))}\b", folded):
            return t
    return None


def refresh_odds(db: Session) -> int:
    """Odds API events carry their own ids, unrelated to ESPN's — so events
    are matched back to a live/upcoming ESPN game by team pair (today's
    scoreboard is the only game set close enough in time for this to be
    unambiguous) rather than by any shared id."""
    events = fetch_odds_events()
    if not events:
        return 0

    teams = db.execute(select(Team)).scalars().all()
    todays_games = {(g["home_team_key"], g["away_team_key"]): g for g in live_games.fetch_scoreboard()}

    count = 0
    for event in events:
        parsed = parse_event_odds(event)
        if parsed is None:
            continue
        home_team = match_team(parsed["home_team_name"], teams)
        away_team = match_team(parsed["away_team_name"], teams)
        if home_team is None or away_team is None:
            continue

        game = todays_games.get((team_key(home_team.name), team_key(away_team.name)))
        if game is None:
            continue  # no matching ESPN game today/soon to attach these odds to

        db.add(
            OddsSnapshot(
                game_id=game["id"],
                bookmaker=f"{parsed['bookmaker_count']}-book average",
                home_implied_prob=parsed["home_implied_prob"],
                away_implied_prob=parsed["away_implied_prob"],
            )
        )
        count += 1

    db.commit()
    return count


def latest_odds(db: Session, game_id: str) -> OddsSnapshot | None:
    return db.execute(
        select(OddsSnapshot)
        .where(OddsSnapshot.game_id == game_id)
        .order_by(OddsSnapshot.captured_at.desc())
    ).scalars().first()
