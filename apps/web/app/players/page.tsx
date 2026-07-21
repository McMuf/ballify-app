"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import PlayerCompareTable from "@/components/PlayerCompareTable";
import type { ScreenerPlayer } from "@/lib/types";

type SentimentFilter = "any" | "bullish" | "bearish";

function sentimentBadge(score: number | null) {
  if (score === null) return <span className="text-ink-muted">-</span>;
  const color = score >= 0.1 ? "text-good-text" : score <= -0.1 ? "text-critical" : "text-ink-secondary";
  return <span className={`tabular-nums ${color}`}>{score.toFixed(2)}</span>;
}

export default function PlayersPage() {
  const [query, setQuery] = useState("");
  const [minPts, setMinPts] = useState(0);
  const [minReb, setMinReb] = useState(0);
  const [minAst, setMinAst] = useState(0);
  const [sentimentFilter, setSentimentFilter] = useState<SentimentFilter>("any");
  const [players, setPlayers] = useState<ScreenerPlayer[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<number[]>([]);

  useEffect(() => {
    const handle = setTimeout(() => {
      const params = new URLSearchParams({
        search: query,
        min_pts: String(minPts),
        min_reb: String(minReb),
        min_ast: String(minAst),
        sentiment: sentimentFilter,
        limit: "50",
      });
      apiFetch<ScreenerPlayer[]>(`/players/screener?${params}`)
        .then(setPlayers)
        .catch(() => setError("Could not load players."));
    }, 250);
    return () => clearTimeout(handle);
  }, [query, minPts, minReb, minAst, sentimentFilter]);

  function toggleSelected(id: number) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 4 ? [...prev, id] : prev
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Players</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Screen by season averages and sentiment, or select up to 4 to compare side by side.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-hairline bg-surface p-4">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink-muted">Search</label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Player name…"
            className="w-40 rounded-md border border-hairline bg-page px-2 py-1.5 text-sm text-ink placeholder:text-ink-muted focus:border-accent focus:outline-none"
          />
        </div>
        {[
          { label: "Min PPG", value: minPts, set: setMinPts },
          { label: "Min RPG", value: minReb, set: setMinReb },
          { label: "Min APG", value: minAst, set: setMinAst },
        ].map((f) => (
          <div key={f.label} className="flex flex-col gap-1">
            <label className="text-xs text-ink-muted">{f.label}</label>
            <input
              type="number"
              min={0}
              value={f.value || ""}
              onChange={(e) => f.set(Number(e.target.value) || 0)}
              placeholder="0"
              className="w-20 rounded-md border border-hairline bg-page px-2 py-1.5 text-sm text-ink focus:border-accent focus:outline-none"
            />
          </div>
        ))}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink-muted">Sentiment</label>
          <select
            value={sentimentFilter}
            onChange={(e) => setSentimentFilter(e.target.value as SentimentFilter)}
            className="rounded-md border border-hairline bg-page px-2 py-1.5 text-sm text-ink focus:border-accent focus:outline-none"
          >
            <option value="any">Any</option>
            <option value="bullish">Bullish</option>
            <option value="bearish">Bearish</option>
          </select>
        </div>
        {selected.length > 0 && (
          <button onClick={() => setSelected([])} className="text-xs text-critical hover:underline">
            Clear {selected.length} selected
          </button>
        )}
      </div>

      {selected.length >= 2 && <PlayerCompareTable playerIds={selected} />}

      {error && <p className="text-sm text-critical">{error}</p>}

      {players && (
        <div className="overflow-hidden rounded-lg border border-hairline bg-surface">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-hairline text-left text-xs uppercase tracking-wide text-ink-muted">
                <th className="w-8 px-4 py-2"></th>
                <th className="px-4 py-2 font-medium">Player</th>
                <th className="px-4 py-2 font-medium">Team</th>
                <th className="px-4 py-2 text-right font-medium">PTS</th>
                <th className="px-4 py-2 text-right font-medium">REB</th>
                <th className="px-4 py-2 text-right font-medium">AST</th>
                <th className="px-4 py-2 text-right font-medium">TS%</th>
                <th className="px-4 py-2 text-right font-medium">Sentiment</th>
              </tr>
            </thead>
            <tbody>
              {players.map((p) => (
                <tr key={p.id} className="border-b border-hairline last:border-0 hover:bg-page">
                  <td className="px-4 py-2">
                    <input
                      type="checkbox"
                      checked={selected.includes(p.id)}
                      onChange={() => toggleSelected(p.id)}
                      disabled={!selected.includes(p.id) && selected.length >= 4}
                    />
                  </td>
                  <td className="px-4 py-2">
                    <Link href={`/players/${p.id}`} className="font-medium text-ink hover:text-accent">
                      {p.full_name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-ink-secondary">{p.team_abbreviation}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-ink">{p.pts.toFixed(1)}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-ink">{p.reb.toFixed(1)}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-ink">{p.ast.toFixed(1)}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-ink">
                    {(p.ts_pct * 100).toFixed(1)}%
                  </td>
                  <td className="px-4 py-2 text-right">{sentimentBadge(p.sentiment_score)}</td>
                </tr>
              ))}
              {players.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-ink-muted">
                    No players match these filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
