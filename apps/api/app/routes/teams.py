from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Player, Team
from app.db.session import get_db
from app.services import nba_data

router = APIRouter()


def _playoff_odds_estimate(playoff_rank: int) -> float:
    """Simple rank-based heuristic, not a simulation — labeled as an estimate."""
    if playoff_rank <= 6:
        return 0.95
    if playoff_rank <= 8:
        return 0.65
    if playoff_rank <= 10:
        return 0.35
    return max(0.02, 0.35 - 0.03 * (playoff_rank - 10))


def _standings_by_team_id() -> dict[int, dict]:
    return {row["TeamID"]: row for row in nba_data.fetch_league_standings()}


@router.get("/teams")
def list_teams(db: Session = Depends(get_db)):
    teams = db.execute(select(Team)).scalars().all()
    standings = _standings_by_team_id()
    out = []
    for team in teams:
        s = standings.get(team.id, {})
        out.append(
            {
                "id": team.id,
                "abbreviation": team.abbreviation,
                "name": team.name,
                "city": team.city,
                "conference": team.conference,
                "division": team.division,
                "logo_url": team.logo_url,
                "wins": s.get("WINS", 0),
                "losses": s.get("LOSSES", 0),
                "win_pct": s.get("WinPCT", 0),
                "conference_rank": s.get("PlayoffRank", 0),
                "streak": s.get("strCurrentStreak", ""),
                "playoff_odds": _playoff_odds_estimate(s.get("PlayoffRank", 30)),
            }
        )
    out.sort(key=lambda t: (t["conference"], t["conference_rank"]))
    return out


@router.get("/teams/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, "team not found")

    roster = db.execute(select(Player).where(Player.team_id == team_id)).scalars().all()
    standings = _standings_by_team_id()
    s = standings.get(team_id, {})

    return {
        "id": team.id,
        "abbreviation": team.abbreviation,
        "name": team.name,
        "city": team.city,
        "conference": team.conference,
        "division": team.division,
        "logo_url": team.logo_url,
        "standings": {
            "wins": s.get("WINS", 0),
            "losses": s.get("LOSSES", 0),
            "win_pct": s.get("WinPCT", 0),
            "conference_rank": s.get("PlayoffRank", 0),
            "conference_games_back": s.get("ConferenceGamesBack", 0),
            "home_record": s.get("HOME", ""),
            "road_record": s.get("ROAD", ""),
            "last_10": s.get("L10", ""),
            "streak": s.get("strCurrentStreak", ""),
            "points_per_game": s.get("PointsPG", 0),
            "opp_points_per_game": s.get("OppPointsPG", 0),
        },
        "playoff_odds": _playoff_odds_estimate(s.get("PlayoffRank", 30)),
        "roster": [
            {
                "id": p.id,
                "full_name": p.full_name,
                "position": p.position,
                "jersey_number": p.jersey_number,
                "headshot_url": p.headshot_url,
            }
            for p in sorted(roster, key=lambda p: p.full_name)
        ],
    }
