"use client";

type Gauge = {
  score: number | null;
  label: string;
  volume: number;
  by_source: Record<string, number>;
};

const SOURCE_LABELS: Record<string, string> = {
  espn_news: "ESPN news",
  reddit: "Reddit",
};

function gaugeColor(score: number): string {
  if (score >= 0.1) return "var(--color-good)";
  if (score <= -0.1) return "var(--color-critical)";
  return "var(--color-ink-muted)";
}

export default function SentimentGauge({ gauge, title }: { gauge: Gauge; title: string }) {
  if (gauge.score === null) {
    return (
      <div className="rounded-lg border border-hairline bg-surface p-4">
        <h3 className="text-sm font-medium uppercase tracking-wide text-ink-muted">{title}</h3>
        <p className="mt-2 text-sm text-ink-muted">
          No sentiment data yet — nothing matched in the last 72 hours of ESPN/Reddit activity.
        </p>
      </div>
    );
  }

  const pct = ((gauge.score + 1) / 2) * 100; // -1..1 -> 0..100
  const color = gaugeColor(gauge.score);

  return (
    <div className="rounded-lg border border-hairline bg-surface p-4">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-medium uppercase tracking-wide text-ink-muted">{title}</h3>
        <span className="text-xs text-ink-muted">{gauge.volume} mentions (72h)</span>
      </div>

      <div className="mt-3 flex items-center gap-3">
        <span className="text-lg font-semibold capitalize" style={{ color }}>
          {gauge.label}
        </span>
        <span className="text-sm tabular-nums text-ink-secondary">{gauge.score.toFixed(2)}</span>
      </div>

      <div className="relative mt-3 h-2 rounded-full bg-page">
        <div className="absolute left-1/2 top-0 h-full w-px bg-baseline" aria-hidden />
        <div
          className="absolute top-0 h-full rounded-full"
          style={{
            left: `${Math.min(pct, 50)}%`,
            right: `${100 - Math.max(pct, 50)}%`,
            backgroundColor: color,
          }}
        />
      </div>
      <div className="mt-1 flex justify-between text-xs text-ink-muted">
        <span>Bearish</span>
        <span>Bullish</span>
      </div>

      {Object.keys(gauge.by_source).length > 0 && (
        <div className="mt-3 flex gap-4 border-t border-hairline pt-2 text-xs text-ink-secondary">
          {Object.entries(gauge.by_source).map(([source, score]) => (
            <span key={source}>
              {SOURCE_LABELS[source] ?? source}: <span className="tabular-nums">{score.toFixed(2)}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
