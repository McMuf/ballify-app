import re
import unicodedata

from app.db.models import Player, Team

# Common shorthand nicknames used in headlines/speech that differ enough from
# the official nickname (Team.name) to miss a plain word-boundary match.
TEAM_NAME_ALIASES: dict[str, list[str]] = {
    "PHI": ["Sixers"],
    "DAL": ["Mavs"],
    "CLE": ["Cavs"],
    "POR": ["Blazers"],
    "MIN": ["Wolves", "T-Wolves"],
    "GSW": ["Dubs"],
    "NOP": ["Pels"],
}


def fold(text: str) -> str:
    """Strip diacritics + lowercase, so 'jokic' matches 'Jokić' either direction."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c)).lower()


def team_key(name: str) -> str:
    """Match key for teams across data sources with inconsistent abbreviation
    AND city naming (nba.com's stats API says 'SAS'/'NYK', ESPN's scoreboard
    says 'SA'/'NY'; ESPN's draft endpoint says city 'LA' for the Clippers
    where its own scoreboard endpoint says 'Los Angeles') — nba nicknames
    are unique league-wide with no collisions, so the nickname alone is a
    stable key where combining it with a city is not."""
    return fold(name)


def find_mentions(text: str, players: list[Player], teams: list[Team]) -> tuple[list[Player], list[Team]]:
    folded = fold(text)
    matched_players = [p for p in players if fold(p.full_name) in folded]
    matched_teams = []
    for t in teams:
        # word-boundary match on the nickname (e.g. "Magic") to cut down false
        # positives from common-English team names inside unrelated prose
        names = [t.name, *TEAM_NAME_ALIASES.get(t.abbreviation, [])]
        if any(re.search(rf"\b{re.escape(fold(n))}\b", folded) for n in names):
            matched_teams.append(t)
    return matched_players, matched_teams
