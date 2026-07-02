from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import odds_service

router = APIRouter()


@router.get("/odds/{game_id}")
def get_odds(game_id: str, db: Session = Depends(get_db)):
    snapshot = odds_service.latest_odds(db, game_id)
    if snapshot is None:
        return {"available": False}
    return {
        "available": True,
        "bookmaker": snapshot.bookmaker,
        "home_implied_prob": snapshot.home_implied_prob,
        "away_implied_prob": snapshot.away_implied_prob,
        "captured_at": snapshot.captured_at.isoformat(),
    }


@router.post("/odds/refresh")
def refresh_odds(db: Session = Depends(get_db)):
    count = odds_service.refresh_odds(db)
    return {"snapshots_stored": count}
