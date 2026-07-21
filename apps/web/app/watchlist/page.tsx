"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { AlertEntry, PlayerSummary, TeamSummary, WatchlistEntry } from "@/lib/types";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function AddToWatchlist({ onAdded }: { onAdded: () => void }) {
  const [query, setQuery] = useState("");
  const [players, setPlayers] = useState<PlayerSummary[]>([]);
  const [teams, setTeams] = useState<TeamSummary[]>([]);
  const [allTeams, setAllTeams] = useState<TeamSummary[]>([]);

  useEffect(() => {
    apiFetch<TeamSummary[]>("/teams").then(setAllTeams).catch(() => {});
  }, []);

  useEffect(() => {
    if (!query) {
      return;
    }
    const handle = setTimeout(() => {
      apiFetch<PlayerSummary[]>(`/players?search=${encodeURIComponent(query)}&limit=6`)
        .then(setPlayers)
        .catch(() => {});
      const needle = query.toLowerCase();
      setTeams(
        allTeams
          .filter((t) => `${t.city} ${t.name}`.toLowerCase().includes(needle))
          .slice(0, 6)
      );
    }, 200);
    return () => clearTimeout(handle);
  }, [query, allTeams]);

  async function add(subjectType: "player" | "team", subjectId: number) {
    await apiFetch("/watchlist", {
      method: "POST",
      body: JSON.stringify({ subject_type: subjectType, subject_id: subjectId }),
    });
    setQuery("");
    onAdded();
  }

  return (
    <div className="rounded-lg border border-hairline bg-surface p-4">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search players or teams to watch…"
        className="w-full rounded-md border border-hairline bg-page px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:border-accent focus:outline-none"
      />
      {query && (players.length > 0 || teams.length > 0) && (
        <div className="mt-2 flex flex-col gap-1">
          {players.map((p) => (
            <button
              key={`p-${p.id}`}
              onClick={() => add("player", p.id)}
              className="flex items-center justify-between rounded-md px-2 py-1.5 text-left text-sm hover:bg-page"
            >
              <span className="text-ink">{p.full_name}</span>
              <span className="text-xs text-ink-muted">{p.team_abbreviation}</span>
            </button>
          ))}
          {teams.map((t) => (
            <button
              key={`t-${t.id}`}
              onClick={() => add("team", t.id)}
              className="flex items-center justify-between rounded-md px-2 py-1.5 text-left text-sm hover:bg-page"
            >
              <span className="text-ink">
                {t.city} {t.name}
              </span>
              <span className="text-xs text-ink-muted">{t.abbreviation}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistEntry[] | null>(null);
  const [alerts, setAlerts] = useState<AlertEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    apiFetch<WatchlistEntry[]>("/watchlist").then(setItems).catch(() => setError("Could not load watchlist."));
    apiFetch<AlertEntry[]>("/alerts").then(setAlerts).catch(() => {});
  }

  useEffect(refresh, []);

  async function remove(id: number) {
    await apiFetch(`/watchlist/${id}`, { method: "DELETE" });
    refresh();
  }

  async function toggleAlert(id: number, field: "alert_big_stat_night" | "alert_sentiment_swing", value: boolean) {
    await apiFetch(`/watchlist/${id}`, { method: "PATCH", body: JSON.stringify({ [field]: value }) });
    refresh();
  }

  async function markAllRead() {
    await apiFetch("/alerts/read-all", { method: "POST" });
    refresh();
  }

  const unreadCount = alerts?.filter((a) => !a.read).length ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Watchlist</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Follow players and teams, and get alerted on big stat nights or sentiment swings.
        </p>
      </div>

      <AddToWatchlist onAdded={refresh} />

      {error && <p className="text-sm text-critical">{error}</p>}

      <div className="rounded-lg border border-hairline bg-surface p-4">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">
            Alerts {unreadCount > 0 && <span className="text-accent">({unreadCount} unread)</span>}
          </h2>
          {unreadCount > 0 && (
            <button onClick={markAllRead} className="text-xs text-accent hover:underline">
              Mark all read
            </button>
          )}
        </div>
        {alerts && alerts.length === 0 && (
          <p className="text-sm text-ink-muted">
            No alerts yet. They show up here once a watched player has a standout game or a team/player&apos;s
            sentiment swings.
          </p>
        )}
        <div className="flex flex-col gap-2">
          {alerts?.slice(0, 20).map((a) => (
            <div
              key={a.id}
              className={`flex items-center justify-between rounded-md px-3 py-2 text-sm ${
                a.read ? "text-ink-secondary" : "bg-page text-ink"
              }`}
            >
              <span>
                <span className="font-medium">{a.subject_name}</span>: {a.message}
              </span>
              <span className="text-xs text-ink-muted">{timeAgo(a.triggered_at)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {items && items.length === 0 && (
          <p className="text-sm text-ink-muted">Nothing on your watchlist yet. Search above to add one.</p>
        )}
        {items?.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between rounded-lg border border-hairline bg-surface p-4"
          >
            <Link
              href={item.subject_type === "player" ? `/players/${item.subject_id}` : `/teams/${item.subject_id}`}
              className="flex items-center gap-3"
            >
              <div>
                <p className="font-medium text-ink hover:text-accent">
                  {item.name}
                  {item.unread_alert_count > 0 && (
                    <span className="ml-2 rounded-full bg-critical px-1.5 py-0.5 text-xs font-medium text-white">
                      {item.unread_alert_count}
                    </span>
                  )}
                </p>
                <p className="text-xs text-ink-muted">{item.subtitle}</p>
              </div>
            </Link>
            <div className="flex items-center gap-4 text-xs text-ink-secondary">
              {item.subject_type === "player" && (
                <label className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={item.alert_big_stat_night}
                    onChange={(e) => toggleAlert(item.id, "alert_big_stat_night", e.target.checked)}
                  />
                  Big stat nights
                </label>
              )}
              <label className="flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={item.alert_sentiment_swing}
                  onChange={(e) => toggleAlert(item.id, "alert_sentiment_swing", e.target.checked)}
                />
                Sentiment swings
              </label>
              <button onClick={() => remove(item.id)} className="text-critical hover:underline">
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
