# Ballify

NBA players and teams tracked like a financial market: stat tickers, sentiment gauges, live win probability, and betting-style odds.

## Requirements
- Python 3.10+
- Node 18+

## Backend
```bash
cd apps/api
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env
./venv/bin/uvicorn app.main:app --reload --port 8000
```
On Windows, use `venv\Scripts\pip` and `venv\Scripts\uvicorn` instead.

Runs fine with no keys set, sentiment/odds just show no data until you add `REDDIT_CLIENT_ID`/`SECRET` and `ODDS_API_KEY` to `.env`.

## Seed the database
Run once, from `apps/api` with the venv active:
```bash
./venv/bin/python -m app.seed.sync_league
```
Everything else (sentiment, trades, injuries, odds, backtest results) fills in automatically once the API is running.

## Frontend
```bash
cd apps/web
npm install
npm run dev
```
Visit http://localhost:3000. The API is expected at http://localhost:8000.
