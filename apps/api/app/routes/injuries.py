from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Injury, Player, Team
from app.db.session import get_db
from app.services import injury_service

router = APIRouter()


@router.get("/injuries")
def list_injuries(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(Injury, Player, Team)
            .join(Player, Injury.player_id == Player.id)
            .join(Team, Player.team_id == Team.id)
        )
        .all()
    )
    out = [
        {
            "player_id": player.id,
            "player_name": player.full_name,
            "team_id": team.id,
            "team_abbreviation": team.abbreviation,
            "status": injury.status,
            "description": injury.description,
            "win_prob_impact": injury.win_prob_impact,
            "updated_at": injury.updated_at.isoformat(),
        }
        for injury, player, team in rows
    ]
    out.sort(key=lambda r: r["win_prob_impact"])
    return out


@router.post("/injuries/refresh")
def refresh_injuries(db: Session = Depends(get_db)):
    count = injury_service.refresh_injuries(db)
    return {"tracked_injuries": count}
