from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TradeRumor
from app.db.session import get_db
from app.services import trades_service

router = APIRouter()


@router.get("/trades")
def list_trades(limit: int = 50, db: Session = Depends(get_db)):
    rumors = (
        db.execute(select(TradeRumor).order_by(TradeRumor.published_at.desc()).limit(limit))
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "headline": r.headline,
            "url": r.url,
            "source_name": r.source_name,
            "team_abbr": r.team_abbr,
            "players_mentioned": [p for p in r.players_mentioned.split(", ") if p],
            "teams_mentioned": [t for t in r.teams_mentioned.split(", ") if t],
            "published_at": r.published_at.isoformat(),
        }
        for r in rumors
    ]


@router.post("/trades/refresh")
def refresh_trades(db: Session = Depends(get_db)):
    count = trades_service.refresh_trade_rumors(db)
    return {"new_rumors": count}
