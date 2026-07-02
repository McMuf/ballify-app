import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.services import sentiment

logger = logging.getLogger("ballify.scheduler")

scheduler = BackgroundScheduler()


def _refresh_sentiment_job() -> None:
    db = SessionLocal()
    try:
        news_count = sentiment.refresh_news_sentiment(db)
        reddit_count = sentiment.refresh_reddit_sentiment(db)
        logger.info("sentiment refresh: %d news, %d reddit snapshots", news_count, reddit_count)
    except Exception:
        logger.exception("sentiment refresh failed")
    finally:
        db.close()


def start() -> None:
    if scheduler.running:
        return
    scheduler.add_job(_refresh_sentiment_job, "interval", minutes=10, id="sentiment_refresh")
    scheduler.start()


def stop() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
