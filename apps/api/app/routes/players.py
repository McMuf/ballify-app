from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Player, SentimentSnapshot, Team
from app.db.session import get_db
from app.services import nba_data
from app.services.game_logs import ensure_game_logs as _ensure_game_logs
from app.services.stats_calc import season_high_low, true_shooting_pct
from app.services.text_utils import fold as _fold

router = APIRouter()

TRACKED_STATS = ["pts", "reb", "ast", "stl", "blk", "tov", "min", "ts_pct", "eff"]


@router.get("/players/screener")
def player_screener(
    search: str = Query(default=""),
    min_pts: float = Query(default=0),
    min_reb: float = Query(default=0),
    min_ast: float = Query(default=0),
    min_stl: float = Query(default=0),
    min_blk: float = Query(default=0),
    sentiment: str = Query(default="any"),  # any | bullish | bearish
    limit: int = Query(default=100, le=300),
    db: Session = Depends(get_db),
):
    rows = nba_data.fetch_league_player_stats()
    teams = {t.id: t for t in db.execute(select(Team)).scalars().all()}

    cutoff = datetime.utcnow() - timedelta(hours=72)
    sentiment_rows = db.execute(
        select(SentimentSnapshot.subject_id, SentimentSnapshot.score)
        .where(SentimentSnapshot.subject_type == "player")
        .where(SentimentSnapshot.captured_at >= cutoff)
    ).all()
    sentiment_by_player: dict[int, list[float]] = {}
    for pid, score in sentiment_rows:
        sentiment_by_player.setdefault(pid, []).append(score)
    avg_sentiment = {pid: sum(v) / len(v) for pid, v in sentiment_by_player.items()}

    needle = _fold(search) if search else ""
    out = []
    for row in rows:
        if row["GP"] == 0:
            continue
        pts, reb, ast, stl, blk = row["PTS"], row["REB"], row["AST"], row["STL"], row["BLK"]
        if pts < min_pts or reb < min_reb or ast < min_ast or stl < min_stl or blk < min_blk:
            continue
        if needle and needle not in _fold(row["PLAYER_NAME"]):
            continue

        s = avg_sentiment.get(row["PLAYER_ID"])
        if sentiment == "bullish" and (s is None or s < 0.1):
            continue
        if sentiment == "bearish" and (s is None or s > -0.1):
            continue

        team = teams.get(row["TEAM_ID"])
        out.append(
            {
                "id": row["PLAYER_ID"],
                "full_name": row["PLAYER_NAME"],
                "team_abbreviation": team.abbreviation if team else row["TEAM_ABBREVIATION"],
                "games_played": row["GP"],
                "pts": pts,
                "reb": reb,
                "ast": ast,
                "stl": stl,
                "blk": blk,
                "ts_pct": true_shooting_pct(pts, row["FGA"], row["FTA"]),
                "sentiment_score": round(s, 3) if s is not None else None,
            }
        )

    out.sort(key=lambda r: -r["pts"])
    return out[:limit]


@router.get("/players")
def list_players(
    search: str = Query(default=""),
    team_id: int | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Player).where(Player.is_active.is_(True))
    if team_id:
        stmt = stmt.where(Player.team_id == team_id)
    players = db.execute(stmt.order_by(Player.full_name)).scalars().all()

    if search:
        needle = _fold(search)
        players = [p for p in players if needle in _fold(p.full_name)]
    players = players[:limit]

    team_ids = {p.team_id for p in players if p.team_id}
    teams = {t.id: t for t in db.execute(select(Team).where(Team.id.in_(team_ids))).scalars()}

    return [
        {
            "id": p.id,
            "full_name": p.full_name,
            "position": p.position,
            "headshot_url": p.headshot_url,
            "team_abbreviation": teams[p.team_id].abbreviation if p.team_id in teams else "",
            "team_id": p.team_id,
        }
        for p in players
    ]


@router.get("/players/{player_id}")
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(404, "player not found")

    team = db.get(Team, player.team_id) if player.team_id else None
    logs = _ensure_game_logs(db, player)

    def series(stat: str) -> list[dict]:
        return [
            {"game_date": g.game_date.strftime("%Y-%m-%d"), "opponent": g.opponent_abbr, "value": getattr(g, stat)}
            for g in logs
        ]

    games_played = len(logs)
    averages = {}
    high_low = {}
    for stat in ["pts", "reb", "ast", "stl", "blk", "tov", "min"]:
        values = [getattr(g, stat) for g in logs]
        averages[stat] = round(sum(values) / games_played, 1) if games_played else 0
        high_low[stat] = season_high_low(values)
    for stat in ["ts_pct", "per"]:
        values = [getattr(g, stat) for g in logs]
        averages["ts_pct" if stat == "ts_pct" else "eff"] = (
            round(sum(values) / games_played, 3) if games_played else 0
        )
        high_low["ts_pct" if stat == "ts_pct" else "eff"] = season_high_low(values)

    return {
        "id": player.id,
        "full_name": player.full_name,
        "position": player.position,
        "jersey_number": player.jersey_number,
        "headshot_url": player.headshot_url,
        "team": (
            {"id": team.id, "abbreviation": team.abbreviation, "name": team.name, "city": team.city}
            if team
            else None
        ),
        "games_played": games_played,
        "averages": averages,
        "season_high_low": high_low,
        "trend": {
            "pts": series("pts"),
            "reb": series("reb"),
            "ast": series("ast"),
            "min": series("min"),
            "ts_pct": series("ts_pct"),
            "eff": series("per"),
        },
    }
