"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { DraftPick, DraftResponse } from "@/lib/types";

function PickRow({ pick }: { pick: DraftPick }) {
  return (
    <div className="flex items-center gap-4 border-b border-hairline px-4 py-3 last:border-0 hover:bg-page">
      <span className="w-8 shrink-0 text-right tabular-nums text-ink-muted">{pick.overall}</span>
      {pick.headshot_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={pick.headshot_url}
          alt=""
          className="h-10 w-10 shrink-0 rounded-full bg-page object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).style.visibility = "hidden";
          }}
        />
      ) : (
        <div className="h-10 w-10 shrink-0 rounded-full bg-page" />
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium text-ink">{pick.player_name}</p>
        <p className="truncate text-xs text-ink-muted">
          {pick.position} · {pick.college}
          {pick.height ? ` · ${pick.height}` : ""}
        </p>
      </div>
      {pick.team ? (
        <Link
          href={`/teams/${pick.team.id}`}
          className="shrink-0 rounded-full border border-hairline px-3 py-1 text-xs font-medium text-ink-secondary hover:border-accent hover:text-accent"
        >
          {pick.team.abbreviation}
        </Link>
      ) : (
        <span className="shrink-0 text-xs text-ink-muted">-</span>
      )}
    </div>
  );
}

export default function DraftPage() {
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<DraftResponse>("/draft")
      .then(setDraft)
      .catch(() => setError("Could not load the draft."));
  }, []);

  if (error) return <p className="text-sm text-critical">{error}</p>;
  if (!draft) return <p className="text-sm text-ink-secondary">Loading…</p>;

  const round1 = draft.picks.filter((p) => p.round === 1);
  const round2 = draft.picks.filter((p) => p.round === 2);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Draft</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          The {draft.year} class, presented like new listings. {draft.status}.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="overflow-hidden rounded-lg border border-hairline bg-surface">
          <div className="border-b border-hairline px-4 py-3">
            <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">Round 1</h2>
          </div>
          {round1.map((p) => (
            <PickRow key={p.overall} pick={p} />
          ))}
        </div>
        <div className="overflow-hidden rounded-lg border border-hairline bg-surface">
          <div className="border-b border-hairline px-4 py-3">
            <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">Round 2</h2>
          </div>
          {round2.map((p) => (
            <PickRow key={p.overall} pick={p} />
          ))}
        </div>
      </div>
    </div>
  );
}
