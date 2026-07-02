import httpx

from app.services.text_utils import team_key

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"

STATE_MAP = {"pre": "scheduled", "in": "live", "post": "final"}


def fetch_scoreboard(date: str | None = None) -> list[dict]:
    """date, if given, is YYYYMMDD (ESPN's format)."""
    params = {"dates": date} if date else {}
    resp = httpx.get(SCOREBOARD_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    games = []
    for event in data.get("events", []):
        comp = event["competitions"][0]
        home = next(c for c in comp["competitors"] if c["homeAway"] == "home")
        away = next(c for c in comp["competitors"] if c["homeAway"] == "away")
        status = event["status"]
        games.append(
            {
                "id": event["id"],
                "date": event["date"],
                "state": STATE_MAP.get(status["type"]["state"], "scheduled"),
                "status_detail": status["type"]["shortDetail"],
                "period": status.get("period", 0),
                "clock": status.get("displayClock", ""),
                "home_team_abbr": home["team"]["abbreviation"],
                "home_team_key": team_key(home["team"]["name"]),
                "home_score": int(home.get("score", 0) or 0),
                "away_team_abbr": away["team"]["abbreviation"],
                "away_team_key": team_key(away["team"]["name"]),
                "away_score": int(away.get("score", 0) or 0),
            }
        )
    return games


def fetch_game_summary(event_id: str) -> dict:
    resp = httpx.get(SUMMARY_URL, params={"event": event_id}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def build_win_prob_timeline(summary: dict) -> list[dict]:
    """ESPN's summary endpoint carries its own trained win-probability model,
    one point per play — real, well-calibrated data rather than a hand-rolled
    formula. We just join it back to the play (for score/clock/period)."""
    plays_by_id = {p["id"]: p for p in summary.get("plays", [])}
    timeline = []
    for i, wp in enumerate(summary.get("winprobability", [])):
        play = plays_by_id.get(wp.get("playId"))
        if play is None:
            continue
        timeline.append(
            {
                "sequence": i,
                "period": play["period"]["number"],
                "clock": play["clock"]["displayValue"],
                "home_score": play["homeScore"],
                "away_score": play["awayScore"],
                "home_win_pct": round(wp["homeWinPercentage"], 3),
            }
        )
    return timeline


def game_state(status: dict, competitors: list) -> dict:
    """Takes the `status` and `competitors` sub-dicts directly rather than a
    whole event/header object — the scoreboard endpoint nests status at the
    event's top level while the summary endpoint nests it one level deeper
    under competitions[0], so callers extract the right one and pass it in."""
    home = next(c for c in competitors if c["homeAway"] == "home")
    away = next(c for c in competitors if c["homeAway"] == "away")
    return {
        "state": STATE_MAP.get(status["type"]["state"], "scheduled"),
        "status_detail": status["type"]["shortDetail"],
        "period": status.get("period", 0),
        "clock": status.get("displayClock", ""),
        "home_score": int(home.get("score", 0) or 0),
        "away_score": int(away.get("score", 0) or 0),
    }
