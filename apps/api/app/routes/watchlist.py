from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Alert, Player, Team, WatchlistItem
from app.db.session import get_db
from app.services import alerts_service

router = APIRouter()


class WatchlistCreate(BaseModel):
    subject_type: str
    subject_id: int


class WatchlistUpdate(BaseModel):
    alert_big_stat_night: bool | None = None
    alert_sentiment_swing: bool | None = None


def _subject_info(db: Session, subject_type: str, subject_id: int) -> dict | None:
    if subject_type == "player":
        p = db.get(Player, subject_id)
        if p is None:
            return None
        team = db.get(Team, p.team_id) if p.team_id else None
        return {
            "name": p.full_name,
            "subtitle": f"{team.abbreviation} · {p.position}" if team else p.position,
            "headshot_url": p.headshot_url,
        }
    if subject_type == "team":
        t = db.get(Team, subject_id)
        if t is None:
            return None
        return {"name": f"{t.city} {t.name}", "subtitle": t.abbreviation, "headshot_url": t.logo_url}
    return None


@router.get("/watchlist")
def list_watchlist(db: Session = Depends(get_db)):
    items = db.execute(select(WatchlistItem).order_by(WatchlistItem.added_at.desc())).scalars().all()
    out = []
    for item in items:
        subject = _subject_info(db, item.subject_type, item.subject_id)
        if subject is None:
            continue
        unread_count = db.execute(
            select(Alert)
            .where(Alert.watchlist_item_id == item.id)
            .where(Alert.read.is_(False))
        ).scalars().all()
        out.append(
            {
                "id": item.id,
                "subject_type": item.subject_type,
                "subject_id": item.subject_id,
                "added_at": item.added_at.isoformat(),
                "alert_big_stat_night": item.alert_big_stat_night,
                "alert_sentiment_swing": item.alert_sentiment_swing,
                "unread_alert_count": len(unread_count),
                **subject,
            }
        )
    return out


@router.post("/watchlist")
def add_watchlist_item(body: WatchlistCreate, db: Session = Depends(get_db)):
    if body.subject_type not in ("player", "team"):
        raise HTTPException(400, "subject_type must be 'player' or 'team'")
    subject = _subject_info(db, body.subject_type, body.subject_id)
    if subject is None:
        raise HTTPException(404, "subject not found")

    existing = db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.subject_type == body.subject_type)
        .where(WatchlistItem.subject_id == body.subject_id)
    ).scalar_one_or_none()
    if existing:
        return {"id": existing.id, "already_watched": True}

    item = WatchlistItem(subject_type=body.subject_type, subject_id=body.subject_id, added_at=datetime.utcnow())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "already_watched": False}


@router.patch("/watchlist/{item_id}")
def update_watchlist_item(item_id: int, body: WatchlistUpdate, db: Session = Depends(get_db)):
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(404, "watchlist item not found")
    if body.alert_big_stat_night is not None:
        item.alert_big_stat_night = body.alert_big_stat_night
    if body.alert_sentiment_swing is not None:
        item.alert_sentiment_swing = body.alert_sentiment_swing
    db.commit()
    return {"ok": True}


@router.delete("/watchlist/{item_id}")
def remove_watchlist_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(404, "watchlist item not found")
    db.execute(Alert.__table__.delete().where(Alert.watchlist_item_id == item_id))
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.get("/alerts")
def list_alerts(unread_only: bool = False, db: Session = Depends(get_db)):
    stmt = select(Alert, WatchlistItem).join(WatchlistItem, Alert.watchlist_item_id == WatchlistItem.id)
    if unread_only:
        stmt = stmt.where(Alert.read.is_(False))
    rows = db.execute(stmt.order_by(Alert.triggered_at.desc()).limit(100)).all()

    out = []
    for alert, item in rows:
        subject = _subject_info(db, item.subject_type, item.subject_id)
        out.append(
            {
                "id": alert.id,
                "watchlist_item_id": item.id,
                "kind": alert.kind,
                "message": alert.message,
                "triggered_at": alert.triggered_at.isoformat(),
                "read": alert.read,
                "subject_name": subject["name"] if subject else "Unknown",
            }
        )
    return out


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(404, "alert not found")
    alert.read = True
    db.commit()
    return {"ok": True}


@router.post("/alerts/read-all")
def mark_all_alerts_read(db: Session = Depends(get_db)):
    db.execute(Alert.__table__.update().values(read=True).where(Alert.read.is_(False)))
    db.commit()
    return {"ok": True}


@router.post("/watchlist/check")
def run_alert_checks(db: Session = Depends(get_db)):
    big_nights = alerts_service.check_big_stat_nights(db)
    swings = alerts_service.check_sentiment_swings(db)
    return {"big_stat_night_alerts": big_nights, "sentiment_swing_alerts": swings}
