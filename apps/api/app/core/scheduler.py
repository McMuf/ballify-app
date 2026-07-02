import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.services import alerts_service, injury_service, sentiment, trades_service

logger = logging.getLogger("ballify.scheduler")

scheduler = BackgroundScheduler()


def _refresh_sentiment_job() -> None:
    db = SessionLocal()
    try:
        news_count = sentiment.refresh_news_sentiment(db)
        reddit_count = sentiment.refresh_reddit_sentiment(db)
        logger.info("sentiment refresh: %d news, %d reddit snapshots", news_count, reddit_count)

        # runs right after, in the same job, so swing detection always sees
        # this refresh's data rather than racing a separately-scheduled job
        big_nights = alerts_service.check_big_stat_nights(db)
        swings = alerts_service.check_sentiment_swings(db)
        logger.info("watchlist alerts: %d big-stat-night, %d sentiment-swing", big_nights, swings)
    except Exception:
        logger.exception("sentiment refresh failed")
    finally:
        db.close()


def _refresh_trades_job() -> None:
    db = SessionLocal()
    try:
        count = trades_service.refresh_trade_rumors(db)
        logger.info("trade rumor refresh: %d new rumors", count)
    except Exception:
        logger.exception("trade rumor refresh failed")
    finally:
        db.close()


def _refresh_injuries_job() -> None:
    db = SessionLocal()
    try:
        count = injury_service.refresh_injuries(db)
        logger.info("injury refresh: %d tracked", count)
    except Exception:
        logger.exception("injury refresh failed")
    finally:
        db.close()


def start() -> None:
    if scheduler.running:
        return
    scheduler.add_job(_refresh_sentiment_job, "interval", minutes=10, id="sentiment_refresh")
    scheduler.add_job(_refresh_trades_job, "interval", minutes=10, id="trades_refresh")
    scheduler.add_job(_refresh_injuries_job, "interval", minutes=30, id="injuries_refresh")
    scheduler.start()


def stop() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
