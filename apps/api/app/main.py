from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import scheduler
from app.core.config import get_settings
from app.db.session import init_db
from app.routes import games, health, injuries, news, players, sentiment, teams, trades, watchlist

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title="Ballify API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(players.router, prefix="/api")
app.include_router(sentiment.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(trades.router, prefix="/api")
app.include_router(injuries.router, prefix="/api")
app.include_router(games.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
