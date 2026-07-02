from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Injury, Player, Team
from app.services import nba_data
from app.services.text_utils import fold

ESPN_INJURIES_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"

STATUS_MAP = {
    "out": "out",
    "doubtful": "doubtful",
    "questionable": "questionable",
    "probable": "probable",
    "day-to-day": "day-to-day",
}

# How much of a player's scoring load is "lost" for the estimate, by
# severity. Deliberately blunt (not a real injury-substitution model) —
# dampened by the 25-point scale factor below so a star being ruled out
# lands in a believable single-digit percentage-point range rather than
# implying points lost equals win-probability points lost 1:1.
SEVERITY_WEIGHT = {
    "out": 1.0,
    "doubtful": 0.75,
    "questionable": 0.4,
    "probable": 0.15,
    "day-to-day": 0.25,
}
IMPACT_SCALE = 25


def fetch_espn_injuries() -> list[dict]:
    resp = httpx.get(ESPN_INJURIES_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    out = []
    for team_group in data.get("injuries", []):
        for inj in team_group.get("injuries", []):
            athlete = inj.get("athlete", {})
            team = athlete.get("team") or {}
            status_raw = (inj.get("status") or "").lower()
            try:
                updated_at = datetime.strptime(inj["date"][:10], "%Y-%m-%d")
            except (KeyError, ValueError):
                updated_at = datetime.utcnow()
            out.append(
                {
                    "player_name": athlete.get("displayName", ""),
                    "team_abbreviation": team.get("abbreviation", ""),
                    "status": STATUS_MAP.get(status_raw, "day-to-day"),
                    "description": inj.get("shortComment") or inj.get("longComment") or "",
                    "updated_at": updated_at,
                }
            )
    return out


def _estimate_impact(player_id: int, team_ppg: float, status: str) -> float:
    if team_ppg <= 0:
        return 0.0
    try:
        rows = nba_data.fetch_player_career_row(player_id)
    except Exception:
        return 0.0
    if not rows:
        return 0.0
    pts_per_game = rows.get("PTS", 0)
    weight = SEVERITY_WEIGHT.get(status, 0.25)
    return round(-(pts_per_game / team_ppg) * weight * IMPACT_SCALE, 1)


def refresh_injuries(db: Session) -> int:
    players = db.execute(select(Player).where(Player.is_active.is_(True))).scalars().all()
    players_by_team: dict[int, list[Player]] = {}
    for p in players:
        if p.team_id:
            players_by_team.setdefault(p.team_id, []).append(p)

    teams = {t.abbreviation: t for t in db.execute(select(Team)).scalars().all()}
    standings_ppg = {row["TeamID"]: row.get("PointsPG", 0) for row in nba_data.fetch_league_standings()}

    raw_injuries = fetch_espn_injuries()

    count = 0
    touched_player_ids: set[int] = set()
    for raw in raw_injuries:
        team = teams.get(raw["team_abbreviation"])
        if team is None:
            continue
        roster = players_by_team.get(team.id, [])
        folded_name = fold(raw["player_name"])
        player = next((p for p in roster if fold(p.full_name) == folded_name), None)
        if player is None:
            continue

        impact = _estimate_impact(player.id, standings_ppg.get(team.id, 0), raw["status"])

        existing = db.execute(select(Injury).where(Injury.player_id == player.id)).scalar_one_or_none()
        if existing is None:
            existing = Injury(player_id=player.id)
            db.add(existing)
        existing.status = raw["status"]
        existing.description = raw["description"]
        existing.win_prob_impact = impact
        existing.updated_at = raw["updated_at"]
        touched_player_ids.add(player.id)
        count += 1

    # Players who recovered since the last refresh drop out of ESPN's feed —
    # clear their stale row so the report reflects who's hurt *now*. Only do
    # this when the feed actually returned something, so a transient
    # matching failure can't wipe the whole report to empty.
    if raw_injuries:
        stale = db.execute(select(Injury).where(Injury.player_id.notin_(touched_player_ids))).scalars().all()
        for row in stale:
            db.delete(row)

    db.commit()
    return count
