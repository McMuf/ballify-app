# Ballify

NBA players and teams presented like a Yahoo Finance–style market: player "tickers" with stat trend
charts, sentiment gauges from Reddit/ESPN, trade rumor and injury tracking, live win-probability during
games, watchlists, a comparison/screener tool, a draft "IPO" section, and a backtesting page for the
sentiment signal.

## Stack
- `apps/api` — FastAPI (Python), SQLite via SQLAlchemy, APScheduler for background data refresh.
- `apps/web` — Next.js (TypeScript, Tailwind).

## Data sources (all free tier)
- Stats: [`nba_api`](https://github.com/swar/nba_api) (`stats.nba.com`), no key required.
- Live scores/injuries: ESPN's public scoreboard/injury JSON endpoints, no key required.
- News/trade rumors: ESPN public RSS feeds.
- Sentiment: Reddit (via `praw`), scored locally with VADER. Requires a free Reddit API app.
- Win probability: ESPN's own trained per-play win-probability model (exposed on their game summary
  endpoint) + [The Odds API](https://the-odds-api.com/) free tier for market-implied odds.
- Draft: ESPN's public draft endpoint turned out to have real, complete draft results — no seed data
  needed after all.

X/Twitter sentiment is intentionally excluded from v1 (the API is paid) — the gauge runs on Reddit + ESPN
news sentiment, with X pluggable later.

## Setup

### Backend (`apps/api`)
```bash
cd apps/api
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in REDDIT_CLIENT_ID/SECRET and ODDS_API_KEY if you have them
./venv/bin/uvicorn app.main:app --reload --port 8000
```
Runs without any secrets filled in — sentiment/odds features just report no data until configured.

### Frontend (`apps/web`)
```bash
cd apps/web
npm install
npm run dev
```
Visit http://localhost:3000. The API is expected at http://localhost:8000.

### Seed / sync scripts (run from `apps/api`, with the venv active)
```bash
./venv/bin/python -m app.seed.sync_league          # teams + rosters — run this first
./venv/bin/python -m app.seed.seed_backtest_demo   # optional: backfills demo backtest history
                                                    # so the Backtest page isn't empty on day one
```
Everything else (sentiment, trades, injuries, odds, real backtest results) fills in automatically via a
background scheduler once the API is running — see `app/core/scheduler.py` for the refresh intervals, or
hit the matching `/api/.../refresh` endpoint to trigger one immediately.

## Project status
All planned stages are built: player tickers, team indices, sentiment gauges, trade rumors, injuries,
live win-probability with SSE streaming, watchlist/alerts, player comparison/screener, the draft page, odds
integration, and backtesting. See commit history for how each stage was verified.
