import httpx

DRAFT_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/draft"


def fetch_draft() -> dict:
    resp = httpx.get(DRAFT_URL, timeout=15)
    resp.raise_for_status()
    return resp.json()


def parse_picks(data: dict) -> list[dict]:
    positions = {p["id"]: p["abbreviation"] for p in data.get("positions", [])}
    out = []
    for pick in data.get("picks", []):
        athlete = pick.get("athlete") or {}
        attrs = {a["name"]: a["displayValue"] for a in athlete.get("attributes", [])}
        college = athlete.get("team") or {}
        out.append(
            {
                "overall": pick.get("overall"),
                "round": pick.get("round"),
                "pick": pick.get("pick"),
                "traded": pick.get("traded", False),
                "player_name": athlete.get("displayName", ""),
                "position": positions.get((athlete.get("position") or {}).get("id"), ""),
                "height": athlete.get("displayHeight", ""),
                "weight": athlete.get("displayWeight", ""),
                "college": college.get("shortDisplayName") or college.get("name", ""),
                "headshot_url": (athlete.get("headshot") or {}).get("href", ""),
                "overall_rank": attrs.get("overall"),
            }
        )
    return out


def team_lookup(data: dict) -> dict[str, dict]:
    """ESPN team id -> {location, name} for resolving each pick's drafting team."""
    return {t["id"]: {"location": t["location"], "name": t["name"]} for t in data.get("teams", [])}
