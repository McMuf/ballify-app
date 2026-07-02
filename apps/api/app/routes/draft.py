from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Team
from app.db.session import get_db
from app.services import draft_service
from app.services.text_utils import team_key

router = APIRouter()


@router.get("/draft")
def get_draft(db: Session = Depends(get_db)):
    data = draft_service.fetch_draft()
    picks = draft_service.parse_picks(data)
    espn_teams = draft_service.team_lookup(data)
    our_teams = {team_key(t.name): t for t in db.execute(select(Team)).scalars().all()}

    raw_picks = data.get("picks", [])
    for pick, raw in zip(picks, raw_picks):
        espn_team = espn_teams.get(raw.get("teamId"))
        team = our_teams.get(team_key(espn_team["name"])) if espn_team else None
        pick["team"] = (
            {"id": team.id, "abbreviation": team.abbreviation, "name": team.name} if team else None
        )

    return {
        "year": data.get("year"),
        "status": data.get("status", {}).get("description", ""),
        "picks": picks,
    }
