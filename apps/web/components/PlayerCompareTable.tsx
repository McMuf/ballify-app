"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import BasketballLoader from "@/components/BasketballLoader";
import type { PlayerDetail } from "@/lib/types";

const ROWS: { key: string; label: string; format?: (v: number) => string }[] = [
  { key: "pts", label: "Points" },
  { key: "reb", label: "Rebounds" },
  { key: "ast", label: "Assists" },
  { key: "stl", label: "Steals" },
  { key: "blk", label: "Blocks" },
  { key: "min", label: "Minutes" },
  { key: "ts_pct", label: "True Shooting %", format: (v) => `${(v * 100).toFixed(1)}%` },
  { key: "eff", label: "EFF" },
];

export default function PlayerCompareTable({ playerIds }: { playerIds: number[] }) {
  const [players, setPlayers] = useState<PlayerDetail[] | null>(null);

  useEffect(() => {
    let stale = false;
    Promise.all(playerIds.map((id) => apiFetch<PlayerDetail>(`/players/${id}`))).then((result) => {
      // ignore responses from a selection that's since changed, without this,
      // a faster later request racing a slower earlier one could leave the
      // table showing a stale player set that doesn't match the checkboxes
      if (!stale) setPlayers(result);
    });
    return () => {
      stale = true;
    };
  }, [playerIds]);

  if (!players) return <BasketballLoader label="Loading comparison…" />;

  return (
    <div className="overflow-x-auto border border-hairline">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-hairline text-left">
            <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-ink-muted">Stat</th>
            {players.map((p) => (
              <th key={p.id} className="px-4 py-3 font-medium text-ink">
                {p.full_name}
                <span className="ml-1 text-xs font-normal text-ink-muted">
                  {p.team ? p.team.abbreviation : ""}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map((row) => {
            const values = players.map((p) => p.averages[row.key] ?? 0);
            const best = Math.max(...values);
            return (
              <tr key={row.key} className="border-b border-hairline last:border-0">
                <td className="px-4 py-2 text-ink-secondary">{row.label}</td>
                {players.map((p, i) => (
                  <td
                    key={p.id}
                    className={`px-4 py-2 tabular-nums ${
                      values[i] === best && values.length > 1 ? "font-semibold text-good-text" : "text-ink"
                    }`}
                  >
                    {row.format ? row.format(values[i]) : values[i]}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
