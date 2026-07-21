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
import type { HighLow, TrendPoint } from "@/lib/types";

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function TrendTooltip({
  active,
  payload,
  formatValue,
}: {
  active?: boolean;
  payload?: { payload: TrendPoint }[];
  formatValue: (v: number) => string;
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="border border-hairline bg-surface px-3 py-2 text-xs shadow-sm">
      <p className="font-medium text-ink">
        {formatDate(point.game_date)} vs {point.opponent}
      </p>
      <p className="mt-0.5 text-ink-secondary">{formatValue(point.value)}</p>
    </div>
  );
}

export default function StatTrendChart({
  data,
  highLow,
  formatValue = (v) => v.toString(),
}: {
  data: TrendPoint[];
  highLow: HighLow;
  formatValue?: (v: number) => string;
}) {
  if (data.length === 0) {
    return <p className="py-12 text-center text-sm text-ink-muted">No games logged yet this season.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 16, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--color-gridline)" vertical={false} />
        <XAxis
          dataKey="game_date"
          tickFormatter={formatDate}
          stroke="var(--color-baseline)"
          tick={{ fill: "var(--color-ink-muted)", fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: "var(--color-baseline)" }}
          minTickGap={30}
        />
        <YAxis
          stroke="var(--color-baseline)"
          tick={{ fill: "var(--color-ink-muted)", fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          width={40}
          tickFormatter={formatValue}
        />
        <Tooltip content={<TrendTooltip formatValue={formatValue} />} />
        <ReferenceLine
          y={highLow.high}
          stroke="var(--color-good)"
          strokeDasharray="4 4"
          label={{
            value: `High ${formatValue(highLow.high)}`,
            position: "insideTopRight",
            fill: "var(--color-good-text)",
            fontSize: 11,
          }}
        />
        <ReferenceLine
          y={highLow.low}
          stroke="var(--color-critical)"
          strokeDasharray="4 4"
          label={{
            value: `Low ${formatValue(highLow.low)}`,
            position: "insideBottomRight",
            fill: "var(--color-critical)",
            fontSize: 11,
          }}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="var(--color-accent)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
