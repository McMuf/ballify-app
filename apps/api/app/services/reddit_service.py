from datetime import datetime, timezone

import praw

from app.core.config import get_settings

TEAM_SUBREDDITS = {
    "ATL": "AtlantaHawks", "BOS": "bostonceltics", "BKN": "GoNets", "CHA": "CharlotteHornets",
    "CHI": "chicagobulls", "CLE": "clevelandcavs", "DAL": "mavericks", "DEN": "denvernuggets",
    "DET": "DetroitPistons", "GSW": "warriors", "HOU": "rockets", "IND": "pacers",
    "LAC": "LAClippers", "LAL": "lakers", "MEM": "memphisgrizzlies", "MIA": "heat",
    "MIL": "MkeBucks", "MIN": "timberwolves", "NOP": "NOLAPelicans", "NYK": "NYKnicks",
    "OKC": "Thunder", "ORL": "OrlandoMagic", "PHI": "sixers", "PHX": "suns",
    "POR": "ripcity", "SAC": "kings", "SAS": "NBASpurs", "TOR": "torontoraptors",
    "UTA": "UtahJazz", "WAS": "washingtonwizards",
}  # fmt: skip

_client: praw.Reddit | None = None


def get_client() -> praw.Reddit | None:
    global _client
    settings = get_settings()
    if not settings.reddit_configured:
        return None
    if _client is None:
        _client = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
    return _client


def fetch_recent_posts(subreddit_name: str, limit: int = 15) -> list[dict]:
    """Returns [] whenever Reddit isn't configured or the call fails — sentiment
    refresh should never crash the app over a flaky/unauthenticated source."""
    client = get_client()
    if client is None:
        return []
    try:
        posts = []
        for post in client.subreddit(subreddit_name).new(limit=limit):
            posts.append(
                {
                    "title": post.title,
                    "selftext": post.selftext or "",
                    "created_at": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).replace(
                        tzinfo=None
                    ),
                    "permalink": f"https://www.reddit.com{post.permalink}",
                }
            )
        return posts
    except Exception:
        return []
