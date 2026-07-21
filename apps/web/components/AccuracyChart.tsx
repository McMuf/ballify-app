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
import type { BacktestWeek } from "@/lib/types";

function pct(v: number) {
  return `${Math.round(v * 100)}%`;
}

function AccuracyTooltip({ active, payload }: { active?: boolean; payload?: { payload: BacktestWeek }[] }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="border border-hairline bg-surface px-3 py-2 text-xs shadow-sm">
      <p className="font-medium text-ink">Week of {p.week}</p>
      <p className="mt-0.5 text-ink-secondary">
        {pct(p.accuracy)} accurate ({p.games} games)
      </p>
    </div>
  );
}

export default function AccuracyChart({ weeks }: { weeks: BacktestWeek[] }) {
  if (weeks.length === 0) {
    return <p className="py-12 text-center text-sm text-ink-muted">Not enough backtest history yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={weeks} margin={{ top: 16, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--color-gridline)" vertical={false} />
        <XAxis
          dataKey="week"
          stroke="var(--color-baseline)"
          tick={{ fill: "var(--color-ink-muted)", fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "var(--color-baseline)" }}
        />
        <YAxis
          domain={[0, 1]}
          tickFormatter={pct}
          stroke="var(--color-baseline)"
          tick={{ fill: "var(--color-ink-muted)", fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          width={40}
        />
        <Tooltip content={<AccuracyTooltip />} />
        <ReferenceLine
          y={0.5}
          stroke="var(--color-ink-muted)"
          strokeDasharray="4 4"
          label={{ value: "Random chance", position: "insideBottomRight", fill: "var(--color-ink-muted)", fontSize: 11 }}
        />
        <Line
          type="monotone"
          dataKey="accuracy"
          stroke="var(--color-accent)"
          strokeWidth={2}
          dot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
