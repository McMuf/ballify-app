"""Sync teams + rosters into the DB. Safe to re-run (upserts).

Usage: ./venv/bin/python -m app.seed.sync_league
"""

from app.db.session import SessionLocal, init_db
from app.db.models import Player, Team
from app.services import nba_data


def sync_teams(db) -> dict[int, Team]:
    by_id: dict[int, Team] = {}
    for t in nba_data.get_static_teams():
        team = db.get(Team, t["id"])
        if team is None:
            team = Team(id=t["id"])
            db.add(team)
        team.abbreviation = t["abbreviation"]
        team.name = t["nickname"]
        team.city = t["city"]
        team.logo_url = nba_data.team_logo_url(t["id"])
        by_id[t["id"]] = team
    db.commit()

    standings = nba_data.fetch_league_standings()
    for row in standings:
        team = by_id.get(row["TeamID"])
        if team:
            team.conference = row["Conference"]
            team.division = row["Division"]
    db.commit()
    return by_id


def sync_rosters(db, teams: dict[int, Team]) -> int:
    count = 0
    for team_id in teams:
        roster = nba_data.fetch_team_roster(team_id)
        for row in roster:
            player_id = row["PLAYER_ID"]
            player = db.get(Player, player_id)
            if player is None:
                player = Player(id=player_id)
                db.add(player)
            player.full_name = row["PLAYER"]
            player.team_id = team_id
            player.position = row["POSITION"] or ""
            player.jersey_number = str(row["NUM"]) if row["NUM"] else ""
            player.headshot_url = nba_data.headshot_url(player_id)
            player.is_active = True
            count += 1
        db.commit()
    return count


def run() -> None:
    init_db()
    db = SessionLocal()
    try:
        teams = sync_teams(db)
        print(f"synced {len(teams)} teams")
        n_players = sync_rosters(db, teams)
        print(f"synced {n_players} roster spots")
    finally:
        db.close()


if __name__ == "__main__":
    run()
