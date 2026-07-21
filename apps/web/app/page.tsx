"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type HealthResponse = {
  status: string;
  reddit_configured: boolean;
  odds_configured: boolean;
};

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<HealthResponse>("/health")
      .then(setHealth)
      .catch(() => setError("Could not reach the Ballify API. Is uvicorn running on :8000?"));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="border border-hairline p-8">
        <h1 className="text-2xl font-semibold text-ink">Ballify</h1>
        <p className="mt-2 max-w-xl text-sm text-ink-secondary">
          NBA players and teams, tracked like a market: stat tickers, sentiment gauges, live win
          probability, trade rumors, injuries, and a screener.
        </p>
      </div>

      <div className="border border-hairline p-6">
        <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">API connection</h2>
        {error && (
          <p className="mt-2 flex items-center gap-2 text-sm text-critical">
            <span aria-hidden>●</span> {error}
          </p>
        )}
        {!error && !health && <p className="mt-2 text-sm text-ink-secondary">Checking…</p>}
        {health && (
          <div className="mt-3 flex flex-col gap-1 text-sm text-ink-secondary">
            <p className="flex items-center gap-2 text-good-text">
              <span aria-hidden>●</span> API reachable ({health.status})
            </p>
            <p>
              Reddit source: {health.reddit_configured ? (
                <span className="text-good-text">configured</span>
              ) : (
                <span className="text-ink-muted">not configured (fallback mode)</span>
              )}
            </p>
            <p>
              Odds source: {health.odds_configured ? (
                <span className="text-good-text">configured</span>
              ) : (
                <span className="text-ink-muted">not configured (fallback mode)</span>
              )}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
