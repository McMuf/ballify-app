"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import StatTrendChart from "@/components/StatTrendChart";
import SentimentGauge from "@/components/SentimentGauge";
import type { PlayerDetail, SentimentGaugeData, TrendStat } from "@/lib/types";
import { TREND_STATS } from "@/lib/types";

const STAT_LABELS: Record<TrendStat, string> = {
  pts: "Points",
  reb: "Rebounds",
  ast: "Assists",
  min: "Minutes",
  ts_pct: "True Shooting %",
  eff: "EFF",
};

function formatStat(stat: TrendStat, value: number): string {
  if (stat === "ts_pct") return `${(value * 100).toFixed(1)}%`;
  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}

export default function PlayerDetailClient({ playerId }: { playerId: number }) {
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [sentimentGauge, setSentimentGauge] = useState<SentimentGaugeData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeStat, setActiveStat] = useState<TrendStat>("pts");

  useEffect(() => {
    apiFetch<PlayerDetail>(`/players/${playerId}`)
      .then(setPlayer)
      .catch(() => setError("Could not load this player."));
    apiFetch<SentimentGaugeData>(`/sentiment/player/${playerId}`)
      .then(setSentimentGauge)
      .catch(() => {});
  }, [playerId]);

  if (error) return <p className="text-sm text-critical">{error}</p>;
  if (!player) return <p className="text-sm text-ink-secondary">Loading…</p>;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4 rounded-lg border border-hairline bg-surface p-6">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={player.headshot_url}
          alt=""
          className="h-20 w-20 rounded-full bg-page object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).style.visibility = "hidden";
          }}
        />
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-muted">
            {player.team ? `${player.team.city} ${player.team.name}` : "Free agent"} ·{" "}
            {player.position}
            {player.jersey_number ? ` · #${player.jersey_number}` : ""}
          </p>
          <h1 className="text-2xl font-semibold text-ink">{player.full_name}</h1>
          <p className="mt-1 text-sm text-ink-secondary">{player.games_played} games played this season</p>
        </div>
      </div>

      {sentimentGauge && <SentimentGauge gauge={sentimentGauge} title="Sentiment" />}

      <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
        {TREND_STATS.map((stat) => (
          <div key={stat} className="rounded-md border border-hairline bg-page px-3 py-2 text-center">
            <p className="text-xs uppercase tracking-wide text-ink-muted">{STAT_LABELS[stat]}</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-ink">
              {formatStat(stat, player.averages[stat] ?? 0)}
            </p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-hairline bg-surface p-4">
        <div className="mb-2 flex flex-wrap gap-1">
          {TREND_STATS.map((stat) => (
            <button
              key={stat}
              onClick={() => setActiveStat(stat)}
              className={
                stat === activeStat
                  ? "rounded-full bg-accent px-3 py-1 text-xs font-medium text-white"
                  : "rounded-full px-3 py-1 text-xs font-medium text-ink-secondary hover:bg-page"
              }
            >
              {STAT_LABELS[stat]}
            </button>
          ))}
        </div>
        <StatTrendChart
          data={player.trend[activeStat]}
          highLow={player.season_high_low[activeStat]}
          formatValue={(v) => formatStat(activeStat, v)}
        />
      </div>
    </div>
  );
}
