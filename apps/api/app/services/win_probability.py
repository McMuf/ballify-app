from sqlalchemy.orm import Session

from app.services import sentiment


def sentiment_home_share(db: Session, home_team_id: int, away_team_id: int) -> float | None:
    """A crowd-mood reference line, NOT a predictive signal: maps the gap
    between each team's current sentiment gauge onto the same 0..1 'home
    share' scale as the play-by-play win-probability line, so they can sit
    on one chart for contrast. Capped well short of 0/1 since fan sentiment
    should never read as near-certainty. Returns None if neither team has
    any recent sentiment data."""
    home_gauge = sentiment.gauge_for(db, "team", home_team_id)
    away_gauge = sentiment.gauge_for(db, "team", away_team_id)

    home_score = home_gauge["score"]
    away_score = away_gauge["score"]
    if home_score is None and away_score is None:
        return None

    diff = (home_score or 0) - (away_score or 0)
    share = 0.5 + diff / 4
    return round(min(max(share, 0.05), 0.95), 3)
