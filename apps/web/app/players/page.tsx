"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { PlayerSummary } from "@/lib/types";

export default function PlayersPage() {
  const [query, setQuery] = useState("");
  const [players, setPlayers] = useState<PlayerSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      const search = query ? `?search=${encodeURIComponent(query)}` : "";
      apiFetch<PlayerSummary[]>(`/players${search}`)
        .then(setPlayers)
        .catch(() => setError("Could not load players."));
    }, 200);
    return () => clearTimeout(handle);
  }, [query]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Players</h1>
        <p className="mt-1 text-sm text-ink-secondary">Search any active player to open their ticker.</p>
      </div>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search players…"
        className="w-full max-w-sm rounded-md border border-hairline bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:border-accent focus:outline-none"
      />

      {error && <p className="text-sm text-critical">{error}</p>}

      {players && (
        <div className="overflow-hidden rounded-lg border border-hairline bg-surface">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-hairline text-left text-xs uppercase tracking-wide text-ink-muted">
                <th className="px-4 py-2 font-medium">Player</th>
                <th className="px-4 py-2 font-medium">Pos</th>
                <th className="px-4 py-2 font-medium">Team</th>
              </tr>
            </thead>
            <tbody>
              {players.map((p) => (
                <tr key={p.id} className="border-b border-hairline last:border-0 hover:bg-page">
                  <td className="px-4 py-2">
                    <Link href={`/players/${p.id}`} className="font-medium text-ink hover:text-accent">
                      {p.full_name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-ink-secondary">{p.position}</td>
                  <td className="px-4 py-2 text-ink-secondary">{p.team_abbreviation}</td>
                </tr>
              ))}
              {players.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-ink-muted">
                    No players match &ldquo;{query}&rdquo;.
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
