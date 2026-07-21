"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import BasketballLoader from "@/components/BasketballLoader";
import type { InjuryReportRow } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  out: "var(--color-critical)",
  doubtful: "var(--color-serious)",
  questionable: "var(--color-warning)",
  probable: "var(--color-ink-secondary)",
  "day-to-day": "var(--color-ink-secondary)",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? "var(--color-ink-muted)";
  return (
    <span className="px-2 py-0.5 text-xs font-medium capitalize" style={{ color, backgroundColor: "var(--color-page)" }}>
      {status}
    </span>
  );
}

export default function InjuriesPage() {
  const [rows, setRows] = useState<InjuryReportRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<InjuryReportRow[]>("/injuries")
      .then(setRows)
      .catch(() => setError("Could not load the injury report."));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Injuries</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Win-probability impact is a modeled estimate from scoring load and severity, not a
          real substitution model.
        </p>
      </div>

      {error && <p className="text-sm text-critical">{error}</p>}
      {!error && !rows && <BasketballLoader label="Loading…" />}
      {rows && rows.length === 0 && <p className="text-sm text-ink-muted">No injuries currently tracked.</p>}

      {rows && rows.length > 0 && (
        <div className="overflow-hidden border border-hairline">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-hairline text-left text-xs uppercase tracking-wide text-ink-muted">
                <th className="px-4 py-2 font-medium">Player</th>
                <th className="px-4 py-2 font-medium">Team</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Note</th>
                <th className="px-4 py-2 text-right font-medium">Win prob impact</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.player_id} className="border-b border-hairline last:border-0 hover:bg-page">
                  <td className="px-4 py-3">
                    <Link
                      href={`/players/${r.player_id}`}
                      className="font-medium text-ink hover:text-accent"
                    >
                      {r.player_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-ink-secondary">{r.team_abbreviation}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={r.status} />
                  </td>
                  <td className="max-w-md px-4 py-3 text-ink-secondary">{r.description}</td>
                  <td className="px-4 py-3 text-right tabular-nums font-medium text-critical">
                    {r.win_prob_impact.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
