"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import SentimentGauge from "@/components/SentimentGauge";
import WatchButton from "@/components/WatchButton";
import BasketballLoader from "@/components/BasketballLoader";
import type { GameSummary, SentimentGaugeData, TeamDetail } from "@/lib/types";

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-hairline bg-page px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-ink-muted">{label}</p>
      <p className="mt-1 text-lg font-semibold tabular-nums text-ink">{value}</p>
    </div>
  );
}

export default function TeamDetailClient({ teamId }: { teamId: number }) {
  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [sentimentGauge, setSentimentGauge] = useState<SentimentGaugeData | null>(null);
  const [todaysGame, setTodaysGame] = useState<GameSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<TeamDetail>(`/teams/${teamId}`)
      .then(setTeam)
      .catch(() => setError("Could not load this team."));
    apiFetch<SentimentGaugeData>(`/sentiment/team/${teamId}`)
      .then(setSentimentGauge)
      .catch(() => {});
    apiFetch<GameSummary[]>("/games/today")
      .then((games) => {
        const match = games.find((g) => g.home_team_id === teamId || g.away_team_id === teamId);
        setTodaysGame(match ?? null);
      })
      .catch(() => {});
  }, [teamId]);

  if (error) return <p className="text-sm text-critical">{error}</p>;
  if (!team) return <BasketballLoader label="Loading…" />;

  const s = team.standings;
  const pctColor = s.win_pct >= 0.5 ? "text-good-text" : "text-critical";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4 border border-hairline p-6">
        <div className="flex items-center gap-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={team.logo_url}
            alt=""
            className="h-16 w-16"
            onError={(e) => {
              (e.target as HTMLImageElement).style.visibility = "hidden";
            }}
          />
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-muted">
              {team.conference}ern Conference · {team.division}
            </p>
            <h1 className="text-2xl font-semibold text-ink">
              {team.city} {team.name}
            </h1>
            <p className={`mt-1 text-sm font-medium tabular-nums ${pctColor}`}>
              {s.wins}-{s.losses} ({(s.win_pct * 100).toFixed(1)}%) · Rank #{s.conference_rank} ·{" "}
              {s.streak}
            </p>
          </div>
        </div>
        <WatchButton subjectType="team" subjectId={team.id} />
      </div>

      {todaysGame && (
        <Link
          href={`/games/${todaysGame.id}`}
          className="flex items-center justify-between border border-hairline p-4 transition-all hover:scale-[1.01] hover:border-accent"
        >
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-muted">
              {todaysGame.state === "live" ? "Live now" : todaysGame.status_detail}
            </p>
            <p className="mt-1 font-medium text-ink">
              {todaysGame.away_team_abbr} {todaysGame.away_score} @ {todaysGame.home_team_abbr}{" "}
              {todaysGame.home_score}
            </p>
          </div>
          <span className="text-sm text-accent">View win probability →</span>
        </Link>
      )}

      {sentimentGauge && <SentimentGauge gauge={sentimentGauge} title="Sentiment" />}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Playoff odds" value={`${(team.playoff_odds * 100).toFixed(0)}%`} />
        <StatTile label="Games back" value={s.conference_games_back.toString()} />
        <StatTile label="Home / Road" value={`${s.home_record} / ${s.road_record}`} />
        <StatTile label="Last 10" value={s.last_10} />
        <StatTile label="Pts/G" value={s.points_per_game.toFixed(1)} />
        <StatTile label="Opp Pts/G" value={s.opp_points_per_game.toFixed(1)} />
      </div>

      <div className="overflow-hidden border border-hairline">
        <div className="border-b border-hairline px-4 py-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">Roster</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left text-xs uppercase tracking-wide text-ink-muted">
              <th className="px-4 py-2 font-medium">Player</th>
              <th className="px-4 py-2 font-medium">Pos</th>
              <th className="px-4 py-2 font-medium">#</th>
            </tr>
          </thead>
          <tbody>
            {team.roster.map((p) => (
              <tr key={p.id} className="border-b border-hairline last:border-0 hover:bg-page">
                <td className="px-4 py-2">
                  <Link href={`/players/${p.id}`} className="font-medium text-ink hover:text-accent">
                    {p.full_name}
                  </Link>
                </td>
                <td className="px-4 py-2 text-ink-secondary">{p.position}</td>
                <td className="px-4 py-2 text-ink-secondary tabular-nums">{p.jersey_number}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
