from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import GameLog, Player, Team
from app.db.session import get_db
from app.services import nba_data
from app.services.stats_calc import efficiency, season_high_low, true_shooting_pct
from app.services.text_utils import fold as _fold

router = APIRouter()

TRACKED_STATS = ["pts", "reb", "ast", "stl", "blk", "tov", "min", "ts_pct", "eff"]


def _ensure_game_logs(db: Session, player: Player) -> list[GameLog]:
    season = nba_data.current_season()
    existing = (
        db.execute(
            select(GameLog)
            .where(GameLog.player_id == player.id)
            .order_by(GameLog.game_date)
        )
        .scalars()
        .all()
    )
    if existing:
        return existing

    rows = nba_data.fetch_player_game_log(player.id, season)
    logs = []
    for row in rows:
        ts = true_shooting_pct(row["PTS"], row["FGA"], row["FTA"])
        eff = efficiency(
            row["PTS"], row["REB"], row["AST"], row["STL"], row["BLK"],
            row["FGM"], row["FGA"], row["FTM"], row["FTA"], row["TOV"],
        )
        log = GameLog(
            player_id=player.id,
            game_id=row["Game_ID"],
            game_date=datetime.strptime(row["GAME_DATE"], "%b %d, %Y"),
            matchup=row["MATCHUP"],
            opponent_abbr=row["MATCHUP"].split()[-1],
            min=row["MIN"] or 0,
            pts=row["PTS"],
            reb=row["REB"],
            ast=row["AST"],
            stl=row["STL"],
            blk=row["BLK"],
            tov=row["TOV"],
            fgm=row["FGM"],
            fga=row["FGA"],
            fg3m=row["FG3M"],
            fg3a=row["FG3A"],
            ftm=row["FTM"],
            fta=row["FTA"],
            plus_minus=row["PLUS_MINUS"] or 0,
            ts_pct=ts,
            per=eff,
        )
        db.add(log)
        logs.append(log)
    db.commit()
    logs.sort(key=lambda g: g.game_date)
    return logs


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
