from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import GameLog, Player
from app.services import nba_data
from app.services.stats_calc import efficiency, true_shooting_pct


def ensure_game_logs(db: Session, player: Player) -> list[GameLog]:
    """Cached on first fetch per player, per the current season — shared by
    the player ticker page and the watchlist's big-stat-night alert check."""
    existing = (
        db.execute(select(GameLog).where(GameLog.player_id == player.id).order_by(GameLog.game_date))
        .scalars()
        .all()
    )
    if existing:
        return existing

    rows = nba_data.fetch_player_game_log(player.id, nba_data.current_season())
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
