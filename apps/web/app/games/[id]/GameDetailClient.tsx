"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE, apiFetch } from "@/lib/api";
import WinProbChart from "@/components/WinProbChart";
import type { GameDetail, WinProbPoint } from "@/lib/types";

type Meta = { state: string; sentiment_home_share: number | null; replay: boolean };

export default function GameDetailClient({ gameId }: { gameId: string }) {
  const [detail, setDetail] = useState<GameDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [points, setPoints] = useState<WinProbPoint[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [streamDone, setStreamDone] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    apiFetch<GameDetail>(`/games/${gameId}`)
      .then(setDetail)
      .catch(() => setError("Could not load this game."));
  }, [gameId]);

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/api/games/${gameId}/stream`);
    esRef.current = es;

    es.addEventListener("meta", (e) => {
      try {
        setMeta(JSON.parse((e as MessageEvent).data));
      } catch {
        /* ignore malformed frame */
      }
    });
    es.addEventListener("point", (e) => {
      try {
        const point: WinProbPoint = JSON.parse((e as MessageEvent).data);
        setPoints((prev) => [...prev, point]);
      } catch {
        /* ignore malformed frame */
      }
    });
    es.addEventListener("done", () => {
      setStreamDone(true);
      es.close();
    });
    es.addEventListener("error", () => {
      // fired both for our application-level "error" SSE event and for
      // real connection drops; either way there's nothing more to stream
      setStreamDone(true);
      es.close();
    });

    return () => es.close();
  }, [gameId]);

  if (error) return <p className="text-sm text-critical">{error}</p>;
  if (!detail) return <p className="text-sm text-ink-secondary">Loading…</p>;

  const latest = points.length > 0 ? points[points.length - 1] : null;
  const homeScore = latest?.home_score ?? detail.state.home_score;
  const awayScore = latest?.away_score ?? detail.state.away_score;

  return (
    <div className="flex flex-col gap-6">
      <div className="border border-hairline p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-muted">{detail.state.status_detail}</p>
            <h1 className="text-2xl font-semibold text-ink">
              {detail.away_team.abbreviation} {awayScore} @ {detail.home_team.abbreviation} {homeScore}
            </h1>
          </div>
          {meta?.replay && (
            <span className="border border-hairline px-3 py-1 text-xs text-ink-muted">
              Replaying final result
            </span>
          )}
          {meta?.state === "live" && (
            <span className="flex items-center gap-1.5 bg-critical/10 px-3 py-1 text-xs font-medium text-critical">
              <span className="h-1.5 w-1.5 bg-critical" /> Live
            </span>
          )}
        </div>
      </div>

      <div className="border border-hairline p-4">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">
            Win probability: {detail.home_team.abbreviation}
          </h2>
          {!streamDone && <span className="text-xs text-ink-muted">{points.length} plays streamed</span>}
        </div>
        <WinProbChart
          points={points}
          homeAbbr={detail.home_team.abbreviation}
          sentimentHomeShare={meta?.sentiment_home_share ?? detail.sentiment_home_share}
          oddsHomeShare={detail.odds_home_share}
        />
        <p className="mt-2 text-xs text-ink-muted">
          Blue line is ESPN&apos;s play-by-play win-probability model. The violet reference line is a
          crowd-sentiment estimate from recent news/Reddit activity. fan mood, not a prediction, and it
          doesn&apos;t update play-by-play.
          {detail.odds_home_share !== null && " The orange line is the sportsbook-market-implied probability."}
        </p>
      </div>
    </div>
  );
}
