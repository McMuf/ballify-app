"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { TeamSummary } from "@/lib/types";

function pctColor(pct: number) {
  if (pct >= 0.5) return "text-good-text";
  if (pct >= 0.4) return "text-ink-secondary";
  return "text-critical";
}

function ConferenceTable({ conference, teams }: { conference: string; teams: TeamSummary[] }) {
  return (
    <div className="overflow-hidden border border-hairline">
      <div className="border-b border-hairline px-4 py-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">
          {conference}ern Conference
        </h2>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-hairline text-left text-xs uppercase tracking-wide text-ink-muted">
            <th className="px-4 py-2 font-medium">#</th>
            <th className="px-4 py-2 font-medium">Team</th>
            <th className="px-4 py-2 text-right font-medium tabular-nums">W-L</th>
            <th className="px-4 py-2 text-right font-medium tabular-nums">Win%</th>
            <th className="px-4 py-2 text-right font-medium tabular-nums">Streak</th>
            <th className="px-4 py-2 text-right font-medium tabular-nums">Playoff odds</th>
          </tr>
        </thead>
        <tbody>
          {teams.map((t) => (
            <tr key={t.id} className="border-b border-hairline last:border-0 hover:bg-page">
              <td className="px-4 py-2 text-ink-muted tabular-nums">{t.conference_rank}</td>
              <td className="px-4 py-2">
                <Link href={`/teams/${t.id}`} className="font-medium text-ink hover:text-accent">
                  {t.city} {t.name}
                </Link>
                <span className="ml-2 text-xs text-ink-muted">{t.abbreviation}</span>
              </td>
              <td className="px-4 py-2 text-right tabular-nums text-ink-secondary">
                {t.wins}-{t.losses}
              </td>
              <td className={`px-4 py-2 text-right tabular-nums font-medium ${pctColor(t.win_pct)}`}>
                {(t.win_pct * 100).toFixed(1)}%
              </td>
              <td className="px-4 py-2 text-right tabular-nums text-ink-secondary">{t.streak}</td>
              <td className="px-4 py-2 text-right tabular-nums text-ink-secondary">
                {(t.playoff_odds * 100).toFixed(0)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function TeamsPage() {
  const [teams, setTeams] = useState<TeamSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<TeamSummary[]>("/teams").then(setTeams).catch(() => setError("Could not load teams."));
  }, []);

  if (error) return <p className="text-sm text-critical">{error}</p>;
  if (!teams) return <p className="text-sm text-ink-secondary">Loading teams…</p>;

  const east = teams.filter((t) => t.conference === "East");
  const west = teams.filter((t) => t.conference === "West");

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Teams</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Standings treated like a market index. Playoff odds are a simple rank-based estimate, not a
          simulation.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ConferenceTable conference="East" teams={east} />
        <ConferenceTable conference="West" teams={west} />
      </div>
    </div>
  );
}
