"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import BasketballLoader from "@/components/BasketballLoader";
import type { GameDetail, GameSummary, MarketGame } from "@/lib/types";

const REFRESH_INTERVAL_MS = 30_000;

function pct(v: number) {
  return `${Math.round(v * 100)}%`;
}

function toEspnDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}

function addDays(d: Date, n: number): Date {
  const next = new Date(d);
  next.setDate(next.getDate() + n);
  return next;
}

function toInputDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function isSameDay(a: Date, b: Date): boolean {
  return toEspnDate(a) === toEspnDate(b);
}

function formatDisplayDate(d: Date): string {
  const today = new Date();
  if (isSameDay(d, today)) return "Today";
  if (isSameDay(d, addDays(today, -1))) return "Yesterday";
  if (isSameDay(d, addDays(today, 1))) return "Tomorrow";
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" });
}

async function enrichGame(g: GameSummary): Promise<MarketGame> {
  try {
    const detail = await apiFetch<GameDetail>(`/games/${g.id}`);
    const lastPoint =
      detail.timeline.length > 0 ? detail.timeline[detail.timeline.length - 1].home_win_pct : null;
    if (lastPoint !== null) {
      return { ...g, home_win_pct: lastPoint, win_pct_source: "model" };
    }
    if (detail.odds_home_share !== null) {
      return { ...g, home_win_pct: detail.odds_home_share, win_pct_source: "odds" };
    }
    return { ...g, home_win_pct: null, win_pct_source: null };
  } catch {
    return { ...g, home_win_pct: null, win_pct_source: null };
  }
}

function OddsBar({ game }: { game: MarketGame }) {
  if (game.home_win_pct === null) {
    return (
      <p className="mt-3 text-xs text-ink-muted">
        {game.state === "scheduled" ? "No odds yet for this one." : "No win-probability data for this one."}
      </p>
    );
  }
  const homePct = game.home_win_pct;
  const awayPct = 1 - homePct;
  return (
    <div className="mt-3">
      <div className="flex items-center justify-between text-xs font-medium">
        <span className="text-ink-secondary">{game.away_team_abbr} {pct(awayPct)}</span>
        <span className="text-ink">{game.home_team_abbr} {pct(homePct)}</span>
      </div>
      <div className="mt-1 flex h-2 overflow-hidden bg-page">
        <div className="h-full bg-ink-muted" style={{ width: `${awayPct * 100}%` }} />
        <div className="h-full bg-accent" style={{ width: `${homePct * 100}%` }} />
      </div>
      <p className="mt-1.5 text-xs text-ink-muted">
        {game.win_pct_source === "model" ? "Live win-probability model" : "Sportsbook-implied odds"}
      </p>
    </div>
  );
}

function GameCard({ game }: { game: MarketGame }) {
  return (
    <Link
      href={`/games/${game.id}`}
      className="block border border-hairline p-4 transition-all hover:scale-[1.02] hover:border-accent"
    >
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide text-ink-muted">{game.status_detail}</p>
        {game.state === "live" && (
          <span className="flex items-center gap-1.5 bg-critical/10 px-2 py-0.5 text-xs font-medium text-critical">
            <span className="h-1.5 w-1.5 bg-critical" /> Live
          </span>
        )}
      </div>
      <p className="mt-2 text-lg font-semibold text-ink">
        {game.away_team_abbr} {game.away_score} @ {game.home_team_abbr} {game.home_score}
      </p>
      <OddsBar game={game} />
    </Link>
  );
}

export default function MarketsPage() {
  const [selectedDate, setSelectedDate] = useState(() => new Date());
  const [games, setGames] = useState<MarketGame[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const viewingToday = isSameDay(selectedDate, new Date());

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const dayGames = await apiFetch<GameSummary[]>(`/games/today?date=${toEspnDate(selectedDate)}`);
        const enriched = await Promise.all(dayGames.map(enrichGame));
        if (!cancelled) setGames(enriched);
      } catch {
        if (!cancelled) setError("Could not load games for this day.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    const handle = viewingToday ? setInterval(load, REFRESH_INTERVAL_MS) : null;
    return () => {
      cancelled = true;
      if (handle) clearInterval(handle);
    };
  }, [selectedDate, viewingToday]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Markets</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Games with live win probability, like a betting market. Odds come from ESPN&apos;s play-by-play
          model once a game starts, or sportsbook-implied odds before tip-off. Step back to any past date to
          see how it played out.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <input
          type="date"
          value={toInputDate(selectedDate)}
          disabled={loading}
          onChange={(e) => {
            const [y, m, d] = e.target.value.split("-").map(Number);
            if (y && m && d) setSelectedDate(new Date(y, m - 1, d));
          }}
          className="[color-scheme:light_dark] border border-hairline bg-page px-2 py-1.5 text-sm text-ink focus:border-accent focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        />
        <span className="text-sm font-medium text-ink">{formatDisplayDate(selectedDate)}</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setSelectedDate((d) => addDays(d, -1))}
            disabled={loading}
            aria-label="Previous day"
            className="border border-hairline px-2 py-1.5 text-sm text-ink-secondary hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-50"
          >
            ←
          </button>
          <button
            onClick={() => setSelectedDate((d) => addDays(d, 1))}
            disabled={loading}
            aria-label="Next day"
            className="border border-hairline px-2 py-1.5 text-sm text-ink-secondary hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-50"
          >
            →
          </button>
        </div>
        {!viewingToday && (
          <button
            onClick={() => setSelectedDate(new Date())}
            disabled={loading}
            className="text-sm text-accent hover:underline disabled:cursor-not-allowed disabled:opacity-50"
          >
            Jump to today
          </button>
        )}
      </div>

      {error && <p className="text-sm text-critical">{error}</p>}
      {!error && !games && <BasketballLoader label="Loading…" />}
      {games && games.length === 0 && (
        <p className="text-sm text-ink-muted">No games on this day.</p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {games?.map((g) => <GameCard key={g.id} game={g} />)}
      </div>
    </div>
  );
}
