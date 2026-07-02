from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # nba.com team id
    abbreviation: Mapped[str] = mapped_column(String(8), index=True)
    name: Mapped[str] = mapped_column(String(64))
    city: Mapped[str] = mapped_column(String(64))
    conference: Mapped[str] = mapped_column(String(16), default="")
    division: Mapped[str] = mapped_column(String(32), default="")
    logo_url: Mapped[str] = mapped_column(String(256), default="")

    players: Mapped[list["Player"]] = relationship(back_populates="team")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # nba.com player id
    full_name: Mapped[str] = mapped_column(String(128), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    position: Mapped[str] = mapped_column(String(16), default="")
    jersey_number: Mapped[str] = mapped_column(String(8), default="")
    headshot_url: Mapped[str] = mapped_column(String(256), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    team: Mapped["Team | None"] = relationship(back_populates="players")
    game_logs: Mapped[list["GameLog"]] = relationship(back_populates="player")


class GameLog(Base):
    __tablename__ = "game_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    game_id: Mapped[str] = mapped_column(String(32), index=True)
    game_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    opponent_abbr: Mapped[str] = mapped_column(String(8), default="")
    matchup: Mapped[str] = mapped_column(String(32), default="")
    min: Mapped[float] = mapped_column(Float, default=0)
    pts: Mapped[int] = mapped_column(Integer, default=0)
    reb: Mapped[int] = mapped_column(Integer, default=0)
    ast: Mapped[int] = mapped_column(Integer, default=0)
    stl: Mapped[int] = mapped_column(Integer, default=0)
    blk: Mapped[int] = mapped_column(Integer, default=0)
    tov: Mapped[int] = mapped_column(Integer, default=0)
    fgm: Mapped[int] = mapped_column(Integer, default=0)
    fga: Mapped[int] = mapped_column(Integer, default=0)
    fg3m: Mapped[int] = mapped_column(Integer, default=0)
    fg3a: Mapped[int] = mapped_column(Integer, default=0)
    ftm: Mapped[int] = mapped_column(Integer, default=0)
    fta: Mapped[int] = mapped_column(Integer, default=0)
    plus_minus: Mapped[float] = mapped_column(Float, default=0)
    ts_pct: Mapped[float] = mapped_column(Float, default=0)
    per: Mapped[float] = mapped_column(Float, default=0)

    player: Mapped["Player"] = relationship(back_populates="game_logs")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # espn event id
    season: Mapped[str] = mapped_column(String(16), default="")
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    home_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    away_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    home_score: Mapped[int] = mapped_column(Integer, default=0)
    away_score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="scheduled")  # scheduled|live|final
    period: Mapped[int] = mapped_column(Integer, default=0)
    clock: Mapped[str] = mapped_column(String(16), default="")


class SentimentSnapshot(Base):
    __tablename__ = "sentiment_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_type: Mapped[str] = mapped_column(String(16), index=True)  # player|team
    subject_id: Mapped[int] = mapped_column(Integer, index=True)
    source: Mapped[str] = mapped_column(String(16))  # reddit|espn_news
    score: Mapped[float] = mapped_column(Float)  # -1 (bearish) .. 1 (bullish)
    volume: Mapped[int] = mapped_column(Integer, default=0)
    captured_at: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)


class TradeRumor(Base):
    __tablename__ = "trade_rumors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    headline: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(512), default="")
    source_name: Mapped[str] = mapped_column(String(128))
    credibility_tier: Mapped[int] = mapped_column(Integer, default=3)  # 1=insider,2=beat,3=aggregator
    players_mentioned: Mapped[str] = mapped_column(Text, default="")  # comma-separated names
    teams_mentioned: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class Injury(Base):
    __tablename__ = "injuries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    status: Mapped[str] = mapped_column(String(32))  # out|doubtful|questionable|probable|day-to-day
    description: Mapped[str] = mapped_column(Text, default="")
    win_prob_impact: Mapped[float] = mapped_column(Float, default=0)  # negative delta to team win prob
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_type: Mapped[str] = mapped_column(String(16))  # player|team
    subject_id: Mapped[int] = mapped_column(Integer)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    alert_big_stat_night: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_sentiment_swing: Mapped[bool] = mapped_column(Boolean, default=True)

    alerts: Mapped[list["Alert"]] = relationship(back_populates="watchlist_item")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    watchlist_item_id: Mapped[int] = mapped_column(ForeignKey("watchlist_items.id"))
    kind: Mapped[str] = mapped_column(String(32))  # big_stat_night|sentiment_swing
    message: Mapped[str] = mapped_column(String(512))
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    read: Mapped[bool] = mapped_column(Boolean, default=False)

    watchlist_item: Mapped["WatchlistItem"] = relationship(back_populates="alerts")


class DraftProspect(Base):
    __tablename__ = "draft_prospects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    position: Mapped[str] = mapped_column(String(16), default="")
    height: Mapped[str] = mapped_column(String(16), default="")
    school_or_team: Mapped[str] = mapped_column(String(128), default="")
    mock_rank: Mapped[int] = mapped_column(Integer, default=0)
    projected_team_abbr: Mapped[str] = mapped_column(String(8), default="")
    stat_comp: Mapped[str] = mapped_column(String(128), default="")  # "pro comparison"
    notes: Mapped[str] = mapped_column(Text, default="")


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(32), index=True)
    bookmaker: Mapped[str] = mapped_column(String(64), default="")
    home_implied_prob: Mapped[float] = mapped_column(Float, default=0)
    away_implied_prob: Mapped[float] = mapped_column(Float, default=0)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(32), index=True)
    game_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    sentiment_favored_team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_winner_team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sentiment_confidence: Mapped[float] = mapped_column(Float, default=0)
    correct: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo_seed: Mapped[bool] = mapped_column(Boolean, default=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
