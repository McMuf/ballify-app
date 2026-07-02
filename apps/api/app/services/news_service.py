from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser

ESPN_NBA_RSS = "https://www.espn.com/espn/rss/nba/news"


def fetch_espn_news() -> list[dict]:
    feed = feedparser.parse(ESPN_NBA_RSS)
    articles = []
    for e in feed.entries:
        try:
            published_at = parsedate_to_datetime(e.published).replace(tzinfo=None)
        except Exception:
            published_at = datetime.utcnow()
        articles.append(
            {
                "title": e.title,
                "link": e.link,
                "summary": e.get("summary", ""),
                "published_at": published_at,
                "source_name": "ESPN",
            }
        )
    return articles
