"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { TradeRumor } from "@/lib/types";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function TradesPage() {
  const [rumors, setRumors] = useState<TradeRumor[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<TradeRumor[]>("/trades")
      .then(setRumors)
      .catch(() => setError("Could not load trade rumors."));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Trades</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Confirmed trades pulled from ESPN&apos;s official transactions log, not rumors.
        </p>
      </div>

      {error && <p className="text-sm text-critical">{error}</p>}
      {!error && !rumors && <p className="text-sm text-ink-secondary">Loading…</p>}
      {rumors && rumors.length === 0 && (
        <p className="text-sm text-ink-muted">No trades in the feed yet.</p>
      )}

      <div className="flex flex-col gap-3">
        {rumors?.map((r) => (
          <div
            key={r.id}
            className="border border-hairline p-4"
          >
            <div className="flex items-start justify-between gap-4">
              <p className="font-medium text-ink">{r.headline}</p>
              {r.team_abbr && (
                <span className="border border-hairline px-2 py-0.5 text-xs font-medium text-ink-secondary">
                  {r.team_abbr}
                </span>
              )}
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
              <span>{r.source_name}</span>
              <span>·</span>
              <span>{timeAgo(r.published_at)}</span>
              {r.teams_mentioned.map((t) => (
                <span key={t} className="bg-page px-2 py-0.5 text-ink-secondary">
                  {t}
                </span>
              ))}
              {r.players_mentioned.map((p) => (
                <span key={p} className="bg-page px-2 py-0.5 text-ink-secondary">
                  {p}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
