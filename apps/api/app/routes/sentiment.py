from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import sentiment

router = APIRouter()


@router.get("/sentiment/player/{player_id}")
def player_sentiment(player_id: int, db: Session = Depends(get_db)):
    return sentiment.gauge_for(db, "player", player_id)


@router.get("/sentiment/team/{team_id}")
def team_sentiment(team_id: int, db: Session = Depends(get_db)):
    return sentiment.gauge_for(db, "team", team_id)


@router.post("/sentiment/refresh")
def refresh_sentiment(db: Session = Depends(get_db)):
    """Manual trigger. the scheduler also runs this on an interval."""
    news_count = sentiment.refresh_news_sentiment(db)
    reddit_count = sentiment.refresh_reddit_sentiment(db)
    return {"news_snapshots": news_count, "reddit_snapshots": reddit_count}
