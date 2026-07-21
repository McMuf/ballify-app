from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Alert, GameLog, Player, SentimentSnapshot, WatchlistItem
from app.services.game_logs import ensure_game_logs

# A game clears the bar if it's a big scoring night relative to the player's
# own season, or a rare cross-category outburst (double/triple-double style
# thresholds), either is genuinely "watchlist-worthy," not just noise.
BIG_NIGHT_PTS_FLOOR = 30
BIG_NIGHT_MULTIPLIER = 1.5
BIG_NIGHT_CATEGORY_THRESHOLD = 15

SENTIMENT_SWING_THRESHOLD = 0.4
SENTIMENT_RECENT_WINDOW_HOURS = 24
SENTIMENT_BASELINE_WINDOW_HOURS = 96


def _is_big_night(game: GameLog, season_avg_pts: float) -> str | None:
    if game.pts >= max(BIG_NIGHT_PTS_FLOOR, season_avg_pts * BIG_NIGHT_MULTIPLIER):
        return f"{game.pts} points"
    big_categories = [
        (game.pts, "pts"), (game.reb, "reb"), (game.ast, "ast"),
        (game.stl, "stl"), (game.blk, "blk"),
    ]
    over_threshold = [label for value, label in big_categories if value >= BIG_NIGHT_CATEGORY_THRESHOLD]
    if len(over_threshold) >= 3:
        return f"{game.pts}pt/{game.reb}reb/{game.ast}ast"
    return None


def check_big_stat_nights(db: Session) -> int:
    items = (
        db.execute(select(WatchlistItem).where(WatchlistItem.subject_type == "player"))
        .scalars()
        .all()
    )
    count = 0
    for item in items:
        if not item.alert_big_stat_night:
            continue
        player = db.get(Player, item.subject_id)
        if player is None:
            continue
        logs = ensure_game_logs(db, player)
        if not logs:
            continue
        latest = logs[-1]
        season_avg_pts = sum(g.pts for g in logs) / len(logs)

        headline = _is_big_night(latest, season_avg_pts)
        if headline is None:
            continue

        last_alert = db.execute(
            select(Alert)
            .where(Alert.watchlist_item_id == item.id)
            .where(Alert.kind == "big_stat_night")
            .order_by(Alert.triggered_at.desc())
        ).scalars().first()
        if last_alert and last_alert.triggered_at >= latest.game_date:
            continue  # already alerted for this game (or a newer one)

        db.add(
            Alert(
                watchlist_item_id=item.id,
                kind="big_stat_night",
                message=f"{player.full_name} put up {headline} vs {latest.opponent_abbr}",
                triggered_at=latest.game_date,
            )
        )
        count += 1
    db.commit()
    return count


def _window_avg_score(db: Session, subject_type: str, subject_id: int, start: datetime, end: datetime) -> float | None:
    rows = db.execute(
        select(SentimentSnapshot.score)
        .where(SentimentSnapshot.subject_type == subject_type)
        .where(SentimentSnapshot.subject_id == subject_id)
        .where(SentimentSnapshot.captured_at >= start)
        .where(SentimentSnapshot.captured_at < end)
    ).scalars().all()
    if not rows:
        return None
    return sum(rows) / len(rows)


def check_sentiment_swings(db: Session) -> int:
    items = db.execute(select(WatchlistItem).where(WatchlistItem.alert_sentiment_swing.is_(True))).scalars().all()
    now = datetime.utcnow()
    recent_start = now - timedelta(hours=SENTIMENT_RECENT_WINDOW_HOURS)
    baseline_start = now - timedelta(hours=SENTIMENT_BASELINE_WINDOW_HOURS)

    count = 0
    for item in items:
        recent = _window_avg_score(db, item.subject_type, item.subject_id, recent_start, now)
        baseline = _window_avg_score(db, item.subject_type, item.subject_id, baseline_start, recent_start)
        if recent is None or baseline is None:
            continue  # not enough history yet to compare against

        delta = recent - baseline
        if abs(delta) < SENTIMENT_SWING_THRESHOLD:
            continue

        recent_alert = db.execute(
            select(Alert)
            .where(Alert.watchlist_item_id == item.id)
            .where(Alert.kind == "sentiment_swing")
            .where(Alert.triggered_at >= recent_start)
        ).scalars().first()
        if recent_alert:
            continue  # already flagged this swing episode

        direction = "up" if delta > 0 else "down"
        db.add(
            Alert(
                watchlist_item_id=item.id,
                kind="sentiment_swing",
                message=f"Sentiment swung {direction} {abs(delta):.2f} over the last {SENTIMENT_RECENT_WINDOW_HOURS}h",
                triggered_at=now,
            )
        )
        count += 1
    db.commit()
    return count
