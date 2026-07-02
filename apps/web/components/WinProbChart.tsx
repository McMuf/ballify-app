"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { WinProbPoint } from "@/lib/types";

function pct(v: number) {
  return `${Math.round(v * 100)}%`;
}

function WinProbTooltip({
  active,
  payload,
  homeAbbr,
}: {
  active?: boolean;
  payload?: { payload: WinProbPoint }[];
  homeAbbr: string;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-md border border-hairline bg-surface px-3 py-2 text-xs shadow-sm">
      <p className="font-medium text-ink">
        Q{p.period} {p.clock} · {p.away_score}-{p.home_score}
      </p>
      <p className="mt-0.5 text-ink-secondary">
        {homeAbbr} win prob: {pct(p.home_win_pct)}
      </p>
    </div>
  );
}

export default function WinProbChart({
  points,
  homeAbbr,
  sentimentHomeShare,
}: {
  points: WinProbPoint[];
  homeAbbr: string;
  sentimentHomeShare: number | null;
}) {
  if (points.length === 0) {
    return <p className="py-12 text-center text-sm text-ink-muted">Waiting for play data…</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={points} margin={{ top: 16, right: 60, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--color-gridline)" vertical={false} />
        <XAxis dataKey="sequence" hide />
        <YAxis
          domain={[0, 1]}
          tickFormatter={pct}
          stroke="var(--color-baseline)"
          tick={{ fill: "var(--color-ink-muted)", fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          width={40}
        />
        <Tooltip content={<WinProbTooltip homeAbbr={homeAbbr} />} />
        <ReferenceLine y={0.5} stroke="var(--color-baseline)" strokeDasharray="2 4" />
        {sentimentHomeShare !== null && (
          <ReferenceLine
            y={sentimentHomeShare}
            stroke="var(--color-accent-violet)"
            strokeDasharray="4 4"
            label={{
              value: `Sentiment ${pct(sentimentHomeShare)}`,
              position: "right",
              fill: "var(--color-accent-violet)",
              fontSize: 11,
            }}
          />
        )}
        <Line
          type="monotone"
          dataKey="home_win_pct"
          stroke="var(--color-accent)"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
