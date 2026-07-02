import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.db.models import Team
from app.db.session import get_db
from app.services import live_games, win_probability
from app.services.text_utils import team_key

router = APIRouter()

# Completed games replay their real historical timeline through the SSE
# stream at this cadence, purely so the "live" code path can be exercised
# and watched end-to-end without an actual game in progress (e.g. off-season).
REPLAY_INTERVAL_SECONDS = 0.12
LIVE_POLL_INTERVAL_SECONDS = 15


def _team_by_key(db: Session) -> dict[str, Team]:
    # keyed by city+nickname, not abbreviation: ESPN's scoreboard/summary
    # endpoints use short-form abbreviations ("SA", "NY") that don't match
    # nba.com's stats API convention ("SAS", "NYK") for the same teams.
    return {team_key(t.city, t.name): t for t in db.execute(select(Team)).scalars().all()}


def _espn_team_key(team_obj: dict) -> str:
    return team_key(team_obj["location"], team_obj["name"])


@router.get("/games/today")
def games_today(db: Session = Depends(get_db)):
    teams = _team_by_key(db)
    games = live_games.fetch_scoreboard()
    out = []
    for g in games:
        home = teams.get(g["home_team_key"])
        away = teams.get(g["away_team_key"])
        out.append(
            {
                **g,
                "home_team_id": home.id if home else None,
                "away_team_id": away.id if away else None,
            }
        )
    return out


@router.get("/games/{game_id}")
def game_detail(game_id: str, db: Session = Depends(get_db)):
    try:
        summary = live_games.fetch_game_summary(game_id)
    except Exception:
        raise HTTPException(404, "game not found")

    teams = _team_by_key(db)
    comp = summary["header"]["competitions"][0]
    competitors = comp["competitors"]
    home = next(c for c in competitors if c["homeAway"] == "home")
    away = next(c for c in competitors if c["homeAway"] == "away")
    home_team = teams.get(_espn_team_key(home["team"]))
    away_team = teams.get(_espn_team_key(away["team"]))

    state = live_games.game_state(comp["status"], competitors)
    timeline = live_games.build_win_prob_timeline(summary)

    sentiment_share = None
    if home_team and away_team:
        sentiment_share = win_probability.sentiment_home_share(db, home_team.id, away_team.id)

    return {
        "id": game_id,
        "state": state,
        "home_team": {"id": home_team.id, "abbreviation": home_team.abbreviation, "name": home_team.name}
        if home_team
        else {"abbreviation": home["team"]["abbreviation"], "name": home["team"]["name"]},
        "away_team": {"id": away_team.id, "abbreviation": away_team.abbreviation, "name": away_team.name}
        if away_team
        else {"abbreviation": away["team"]["abbreviation"], "name": away["team"]["name"]},
        "timeline": timeline,
        "sentiment_home_share": sentiment_share,
    }


@router.get("/games/{game_id}/stream")
async def game_stream(game_id: str, db: Session = Depends(get_db)):
    async def event_generator():
        try:
            summary = live_games.fetch_game_summary(game_id)
        except Exception:
            yield {"event": "error", "data": json.dumps({"message": "game not found"})}
            return

        header_comp = summary["header"]["competitions"][0]
        state = live_games.game_state(header_comp["status"], header_comp["competitors"])

        teams = _team_by_key(db)
        competitors = header_comp["competitors"]
        home = next(c for c in competitors if c["homeAway"] == "home")
        away = next(c for c in competitors if c["homeAway"] == "away")
        home_team = teams.get(_espn_team_key(home["team"]))
        away_team = teams.get(_espn_team_key(away["team"]))
        sentiment_share = None
        if home_team and away_team:
            sentiment_share = win_probability.sentiment_home_share(db, home_team.id, away_team.id)

        yield {
            "event": "meta",
            "data": json.dumps(
                {
                    "state": state["state"],
                    "sentiment_home_share": sentiment_share,
                    "replay": state["state"] == "final",
                }
            ),
        }

        if state["state"] == "scheduled":
            yield {"event": "done", "data": json.dumps({"reason": "scheduled"})}
            return

        if state["state"] == "final":
            timeline = live_games.build_win_prob_timeline(summary)
            for point in timeline:
                yield {"event": "point", "data": json.dumps(point)}
                await asyncio.sleep(REPLAY_INTERVAL_SECONDS)
            yield {"event": "done", "data": json.dumps({"reason": "final"})}
            return

        # live: poll until the game ends, emitting only newly-seen points
        sent = 0
        while True:
            try:
                summary = live_games.fetch_game_summary(game_id)
            except Exception:
                await asyncio.sleep(LIVE_POLL_INTERVAL_SECONDS)
                continue
            timeline = live_games.build_win_prob_timeline(summary)
            for point in timeline[sent:]:
                yield {"event": "point", "data": json.dumps(point)}
            sent = len(timeline)

            header_comp = summary["header"]["competitions"][0]
            state = live_games.game_state(header_comp["status"], header_comp["competitors"])
            if state["state"] == "final":
                yield {"event": "done", "data": json.dumps({"reason": "final"})}
                return
            await asyncio.sleep(LIVE_POLL_INTERVAL_SECONDS)

    return EventSourceResponse(event_generator())
