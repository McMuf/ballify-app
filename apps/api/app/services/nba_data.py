"""Live NBA stats access.

nba_api ships two things: static data (teams/players, bundled with the package,
zero network calls) and live HTTP endpoint wrappers that go through `requests`.
In this environment `requests` hangs against stats.nba.com (likely a TLS/HTTP2
fingerprinting quirk with their bot protection) while a plain `httpx` GET to the
exact same URL succeeds in well under a second. So: use nba_api's static module
for teams/players, and a small hand-rolled httpx client for everything live.
"""

from datetime import datetime, timedelta

import httpx

from nba_api.stats.static import players as static_players
from nba_api.stats.static import teams as static_teams

STATS_BASE = "https://stats.nba.com/stats"

HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Connection": "keep-alive",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
}


def current_season() -> str:
    """NBA season string like '2025-26'. Season flips over in October."""
    now = datetime.utcnow()
    start_year = now.year if now.month >= 10 else now.year - 1
    return f"{start_year}-{str(start_year + 1)[2:]}"


def headshot_url(player_id: int) -> str:
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"


def team_logo_url(team_id: int) -> str:
    return f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"


def get_static_teams() -> list[dict]:
    return static_teams.get_teams()


def get_static_players() -> list[dict]:
    return static_players.get_players()


def _get(endpoint: str, params: dict) -> dict:
    url = f"{STATS_BASE}/{endpoint}"
    resp = httpx.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _result_set_to_dicts(payload: dict, index: int = 0) -> list[dict]:
    rs = payload["resultSets"][index]
    cols = rs["headers"]
    return [dict(zip(cols, row)) for row in rs["rowSet"]]


def fetch_team_roster(team_id: int, season: str | None = None) -> list[dict]:
    season = season or current_season()
    payload = _get("commonteamroster", {"TeamID": team_id, "Season": season, "LeagueID": "00"})
    return _result_set_to_dicts(payload, 0)


def fetch_player_game_log(player_id: int, season: str | None = None) -> list[dict]:
    season = season or current_season()
    payload = _get(
        "playergamelog",
        {"PlayerID": player_id, "Season": season, "SeasonType": "Regular Season", "LeagueID": "00"},
    )
    return _result_set_to_dicts(payload, 0)


def fetch_player_career_row(player_id: int, season: str | None = None) -> dict | None:
    """Current-season per-game averages via the lightweight career-stats
    endpoint — used where a full game log isn't otherwise needed (e.g.
    injury impact estimates for players whose ticker page nobody has
    opened yet)."""
    season = season or current_season()
    payload = _get("playercareerstats", {"PlayerID": player_id, "PerMode": "PerGame", "LeagueID": "00"})
    result_sets = {rs["name"]: rs for rs in payload["resultSets"]}
    season_totals = result_sets.get("SeasonTotalsRegularSeason")
    if not season_totals or not season_totals["rowSet"]:
        return None
    rows = [dict(zip(season_totals["headers"], row)) for row in season_totals["rowSet"]]
    matching = [r for r in rows if r["SEASON_ID"] == season]
    return matching[-1] if matching else rows[-1]


_standings_cache: dict[str, tuple[datetime, list[dict]]] = {}
_STANDINGS_TTL = timedelta(minutes=10)


def fetch_league_standings(season: str | None = None) -> list[dict]:
    season = season or current_season()
    cached = _standings_cache.get(season)
    if cached and datetime.utcnow() - cached[0] < _STANDINGS_TTL:
        return cached[1]
    payload = _get(
        "leaguestandingsv3", {"LeagueID": "00", "Season": season, "SeasonType": "Regular Season"}
    )
    rows = _result_set_to_dicts(payload, 0)
    _standings_cache[season] = (datetime.utcnow(), rows)
    return rows
