"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { WatchlistEntry } from "@/lib/types";

export default function WatchButton({
  subjectType,
  subjectId,
}: {
  subjectType: "player" | "team";
  subjectId: number;
}) {
  const [entry, setEntry] = useState<WatchlistEntry | null | undefined>(undefined);

  function refresh() {
    apiFetch<WatchlistEntry[]>("/watchlist")
      .then((items) =>
        setEntry(items.find((i) => i.subject_type === subjectType && i.subject_id === subjectId) ?? null)
      )
      .catch(() => setEntry(null));
  }

  useEffect(refresh, [subjectType, subjectId]);

  async function toggle() {
    if (entry) {
      await apiFetch(`/watchlist/${entry.id}`, { method: "DELETE" });
    } else {
      await apiFetch("/watchlist", {
        method: "POST",
        body: JSON.stringify({ subject_type: subjectType, subject_id: subjectId }),
      });
    }
    refresh();
  }

  if (entry === undefined) return null;

  return (
    <button
      onClick={toggle}
      className={
        entry
          ? "rounded-full border border-accent px-3 py-1.5 text-xs font-medium text-accent"
          : "rounded-full border border-hairline px-3 py-1.5 text-xs font-medium text-ink-secondary hover:border-accent hover:text-accent"
      }
    >
      {entry ? "✓ Watching" : "+ Watch"}
    </button>
  );
}
