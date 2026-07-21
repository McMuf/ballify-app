export default function AboutPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">About</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          What Ballify is, how it&apos;s built, and how the main features actually work.
        </p>
      </div>

      <section className="border border-hairline p-6">
        <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">What it does</h2>
        <ul className="mt-3 flex flex-col gap-2 text-sm text-ink-secondary list-disc pl-5">
          <li>Tracks NBA players and teams like market tickers, with stat trend charts</li>
          <li>Shows a bullish/bearish sentiment gauge built from Reddit and ESPN news</li>
          <li>Lists confirmed trades pulled from ESPN&apos;s transactions log</li>
          <li>Tracks current injuries with a rough win probability impact estimate</li>
          <li>Streams live win probability during games, with a sentiment overlay for comparison</li>
          <li>Lets you build a watchlist and get alerted on big games or sentiment swings</li>
          <li>Has a player screener/comparison tool and a draft board</li>
          <li>Backtests the sentiment signal against real game outcomes</li>
        </ul>
      </section>

      <section className="border border-hairline p-6">
        <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">Architecture</h2>
        <ul className="mt-3 flex flex-col gap-2 text-sm text-ink-secondary list-disc pl-5">
          <li>Frontend: Next.js (App Router) and TypeScript, styled with Tailwind</li>
          <li>Backend: FastAPI (Python), SQLite via SQLAlchemy</li>
          <li>APScheduler runs background jobs so data refreshes without the user waiting on a request</li>
          <li>No accounts or auth, this is single-user by design</li>
          <li>Stats come from stats.nba.com via the nba_api package</li>
          <li>Scores, injuries, draft data, and transactions come from ESPN&apos;s public endpoints</li>
          <li>Sentiment is scored locally with VADER, no external sentiment API</li>
          <li>Odds come from The Odds API&apos;s free tier, when a key is configured</li>
        </ul>
      </section>

      <section className="border border-hairline p-6">
        <h2 className="text-sm font-medium uppercase tracking-wide text-ink-muted">Some of the logic</h2>
        <ul className="mt-3 flex flex-col gap-2 text-sm text-ink-secondary list-disc pl-5">
          <li>Sentiment gauge: VADER scores headlines and posts, matched to a player or team by name, averaged over a rolling window</li>
          <li>Win probability chart: the blue line is ESPN&apos;s own play-by-play model, the sentiment line is fan mood on a separate cadence, and the odds line is sportsbook-implied probability, none of them are predictions of each other</li>
          <li>Backtest: compares whichever team had the higher sentiment gauge as of game day (not today) against who actually won, so it can&apos;t cheat with hindsight</li>
          <li>Watchlist alerts: fire on a big stat night (season-average outlier or a multi-category outburst) or a real swing in sentiment over the last day</li>
          <li>Team matching across ESPN and nba.com is done by nickname, since city names and abbreviations don&apos;t agree between the two</li>
          <li>Everything degrades gracefully without API keys, it just shows no data instead of erroring</li>
        </ul>
      </section>
    </div>
  );
}
