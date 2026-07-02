from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import backtest_service

router = APIRouter()


@router.get("/backtest")
def get_backtest(db: Session = Depends(get_db)):
    return backtest_service.summary(db)


@router.post("/backtest/refresh")
def refresh_backtest(db: Session = Depends(get_db)):
    count = backtest_service.check_recent_games(db)
    return {"new_results": count}
