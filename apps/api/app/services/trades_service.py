from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Player, Team, TradeRumor
from app.services.text_utils import find_mentions, fold

ESPN_TRANSACTIONS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/transactions"

TRADE_KEYWORDS = ["trade", "traded", "acquired", "in exchange for", "sent to"]


def _is_trade(description: str) -> bool:
    folded = fold(description)
    return any(kw in folded for kw in TRADE_KEYWORDS)


def fetch_espn_transactions() -> list[dict]:
    resp = httpx.get(ESPN_TRANSACTIONS_URL, timeout=15)
    resp.raise_for_status()
    return resp.json().get("transactions", [])


def _parse_date(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except (KeyError, ValueError, AttributeError):
        return None


def _existing_keys(db: Session, since: datetime) -> set[tuple[datetime, str]]:
    rows = db.execute(
        select(TradeRumor.published_at, TradeRumor.headline).where(TradeRumor.published_at >= since)
    ).all()
    return {(r[0], r[1]) for r in rows}


def refresh_trade_rumors(db: Session) -> int:
    """Pulls from ESPN's public transactions log instead of RSS keyword-matching
    plus Reddit. It's not live play-by-play, but it's a structured official feed
    that doesn't need Reddit OAuth or headline-guessing, so it's up more often
    and the rumor-vs-confirmed distinction stops mattering (everything here is
    the actual reported move, not a leak)."""
    players = db.execute(select(Player).where(Player.is_active.is_(True))).scalars().all()
    teams = db.execute(select(Team)).scalars().all()
    seen = _existing_keys(db, datetime.utcnow() - timedelta(days=60))

    count = 0
    for txn in fetch_espn_transactions():
        description = txn.get("description", "")
        if not description or not _is_trade(description):
            continue

        date = _parse_date(txn.get("date", ""))
        if date is None:
            continue

        key = (date, description)
        if key in seen:
            continue
        seen.add(key)

        team = txn.get("team") or {}
        matched_players, matched_teams = find_mentions(description, players, teams)

        db.add(
            TradeRumor(
                headline=description,
                url="",
                source_name="ESPN Transactions",
                team_abbr=team.get("abbreviation", ""),
                players_mentioned=", ".join(p.full_name for p in matched_players),
                teams_mentioned=", ".join(t.abbreviation for t in matched_teams),
                published_at=date,
            )
        )
        count += 1

    db.commit()
    return count
