export default function BasketballLoader({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-14">
      <div className="flex h-14 w-12 flex-col items-center justify-end">
        <div className="animate-bball-bounce">
          <svg viewBox="0 0 40 40" className="h-10 w-10 animate-bball-spin">
            <circle cx="20" cy="20" r="18" fill="var(--color-accent)" stroke="var(--color-seam)" strokeWidth="1.5" />
            <path d="M20 2 V38" stroke="var(--color-seam)" strokeWidth="1.5" fill="none" />
            <path d="M2 20 H38" stroke="var(--color-seam)" strokeWidth="1.5" fill="none" />
            <path d="M6 7 Q22 20 6 33" stroke="var(--color-seam)" strokeWidth="1.5" fill="none" />
            <path d="M34 7 Q18 20 34 33" stroke="var(--color-seam)" strokeWidth="1.5" fill="none" />
          </svg>
        </div>
      </div>
      <div className="h-1.5 w-7 animate-bball-shadow bg-ink-muted/40" />
      {label && <p className="text-sm text-ink-secondary">{label}</p>}
    </div>
  );
}
