"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/players", label: "Players" },
  { href: "/teams", label: "Teams" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/markets", label: "Markets" },
  { href: "/trades", label: "Trades" },
  { href: "/injuries", label: "Injuries" },
  { href: "/draft", label: "Draft" },
  { href: "/backtest", label: "Backtest" },
  { href: "/about", label: "About" },
];

export default function TopNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-10 border-b border-hairline bg-surface">
      <div className="mx-auto flex max-w-6xl items-center gap-8 px-6 py-3">
        <Link
          href="/"
          className="flex items-center gap-1.5 text-lg font-semibold tracking-tight text-ink transition-colors hover:text-accent"
        >
          <span aria-hidden>🏀</span>
          Ballify
        </Link>
        <nav className="flex flex-1 items-center gap-6 text-sm">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={
                  active
                    ? "border-b-2 border-accent pb-1 font-medium text-accent"
                    : "border-b-2 border-transparent pb-1 text-ink-secondary transition-colors hover:border-accent hover:text-accent"
                }
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
