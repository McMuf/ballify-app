export default function StagePlaceholder({
  title,
  stage,
  description,
}: {
  title: string;
  stage: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-hairline bg-surface p-8">
      <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">{stage}</p>
      <h1 className="mt-2 text-2xl font-semibold text-ink">{title}</h1>
      <p className="mt-3 max-w-xl text-sm text-ink-secondary">{description}</p>
    </div>
  );
}
