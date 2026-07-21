"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import AccuracyChart from "@/components/AccuracyChart";
import type { BacktestSummary } from "@/lib/types";

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-hairline bg-page px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-ink-muted">{label}</p>
      <p className="mt-1 text-lg font-semibold tabular-nums text-ink">{value}</p>
    </div>
  );
}

export default function BacktestPage() {
  const [data, setData] = useState<BacktestSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<BacktestSummary>("/backtest")
      .then(setData)
      .catch(() => setError("Could not load backtest results."));
  }, []);

  if (error) return <p className="text-sm text-critical">{error}</p>;
  if (!data) return <p className="text-sm text-ink-secondary">Loading…</p>;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Backtesting</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          How often the team with the more bullish sentiment actually won. this is what earns trust in the
          signal, or shows where it falls short.
        </p>
      </div>

      {data.total_games === 0 ? (
        <p className="border border-hairline p-4 text-sm text-ink-muted">
          No backtest history yet. It fills in automatically as games complete and sentiment accumulates.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile
              label="Overall accuracy"
              value={data.overall_accuracy !== null ? `${(data.overall_accuracy * 100).toFixed(1)}%` : "-"}
            />
            <StatTile label="Games backtested" value={data.total_games.toString()} />
            <StatTile label="Real results" value={data.real_count.toString()} />
            <StatTile label="Demo-seeded results" value={data.demo_seed_count.toString()} />
          </div>

          {data.demo_seed_count > 0 && (
            <p className="border border-hairline bg-page px-3 py-2 text-xs text-ink-muted">
              {data.real_count === 0
                ? "All results below are demo-seeded: a synthetic sentiment pick against real historical game outcomes, since there's no accumulated real sentiment history yet. Real results (unlabeled) take over as the app runs."
                : "Mix of demo-seeded and real results. demo rows are labeled below."}
            </p>
          )}

          <div className="border border-hairline p-4">
            <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-ink-muted">
              Accuracy by week
            </h2>
            <AccuracyChart weeks={data.accuracy_over_time} />
          </div>

          <div className="overflow-hidden border border-hairline">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-hairline text-left text-xs uppercase tracking-wide text-ink-muted">
                  <th className="px-4 py-2 font-medium">Date</th>
                  <th className="px-4 py-2 font-medium">Sentiment favored</th>
                  <th className="px-4 py-2 font-medium">Actual winner</th>
                  <th className="px-4 py-2 text-right font-medium">Confidence</th>
                  <th className="px-4 py-2 text-right font-medium">Result</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_results.map((r) => (
                  <tr key={r.game_id} className="border-b border-hairline last:border-0 hover:bg-page">
                    <td className="px-4 py-2 text-ink-secondary">{r.game_date}</td>
                    <td className="px-4 py-2 text-ink">
                      {r.favored}
                      {r.is_demo_seed && (
                        <span className="ml-2 bg-page px-1.5 py-0.5 text-xs text-ink-muted">
                          demo
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-ink-secondary">{r.actual_winner}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-ink-secondary">
                      {r.confidence.toFixed(2)}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <span className={r.correct ? "text-good-text" : "text-critical"}>
                        {r.correct ? "Correct" : "Wrong"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
