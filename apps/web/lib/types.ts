export type WatchlistEntry = {
  id: number;
  subject_type: "player" | "team";
  subject_id: number;
  added_at: string;
  alert_big_stat_night: boolean;
  alert_sentiment_swing: boolean;
  unread_alert_count: number;
  name: string;
  subtitle: string;
  headshot_url: string;
};

export type AlertEntry = {
  id: number;
  watchlist_item_id: number;
  kind: "big_stat_night" | "sentiment_swing";
  message: string;
  triggered_at: string;
  read: boolean;
  subject_name: string;
};

export type TradeRumor = {
  id: number;
  headline: string;
  url: string;
  source_name: string;
  team_abbr: string;
  players_mentioned: string[];
  teams_mentioned: string[];
  published_at: string;
};

export type InjuryReportRow = {
  player_id: number;
  player_name: string;
  team_id: number;
  team_abbreviation: string;
  status: string;
  description: string;
  win_prob_impact: number;
  updated_at: string;
};

export type GameSummary = {
  id: string;
  date: string;
  state: "scheduled" | "live" | "final";
  status_detail: string;
  period: number;
  clock: string;
  home_team_abbr: string;
  home_team_key: string;
  home_team_id: number | null;
  home_score: number;
  away_team_abbr: string;
  away_team_key: string;
  away_team_id: number | null;
  away_score: number;
};

export type WinProbPoint = {
  sequence: number;
  period: number;
  clock: string;
  home_score: number;
  away_score: number;
  home_win_pct: number;
};

export type GameTeamRef = { id?: number; abbreviation: string; name: string };

export type MarketGame = GameSummary & {
  home_win_pct: number | null;
  win_pct_source: "model" | "odds" | null;
};

export type GameDetail = {
  id: string;
  state: {
    state: "scheduled" | "live" | "final";
    status_detail: string;
    period: number;
    clock: string;
    home_score: number;
    away_score: number;
  };
  home_team: GameTeamRef;
  away_team: GameTeamRef;
  timeline: WinProbPoint[];
  sentiment_home_share: number | null;
  odds_home_share: number | null;
};

export type BacktestWeek = { week: string; accuracy: number; games: number };

export type BacktestResultRow = {
  game_id: string;
  game_date: string;
  favored: string;
  actual_winner: string;
  correct: boolean;
  confidence: number;
  is_demo_seed: boolean;
};

export type BacktestSummary = {
  total_games: number;
  overall_accuracy: number | null;
  demo_seed_count: number;
  real_count: number;
  accuracy_over_time: BacktestWeek[];
  recent_results: BacktestResultRow[];
};

export type TeamSummary = {
  id: number;
  abbreviation: string;
  name: string;
  city: string;
  conference: string;
  division: string;
  logo_url: string;
  wins: number;
  losses: number;
  win_pct: number;
  conference_rank: number;
  streak: string;
  playoff_odds: number;
};

export type RosterPlayer = {
  id: number;
  full_name: string;
  position: string;
  jersey_number: string;
  headshot_url: string;
};

export type TeamDetail = {
  id: number;
  abbreviation: string;
  name: string;
  city: string;
  conference: string;
  division: string;
  logo_url: string;
  standings: {
    wins: number;
    losses: number;
    win_pct: number;
    conference_rank: number;
    conference_games_back: number;
    home_record: string;
    road_record: string;
    last_10: string;
    streak: string;
    points_per_game: number;
    opp_points_per_game: number;
  };
  playoff_odds: number;
  roster: RosterPlayer[];
};

export type PlayerSummary = {
  id: number;
  full_name: string;
  position: string;
  headshot_url: string;
  team_abbreviation: string;
  team_id: number | null;
};

export type TrendPoint = {
  game_date: string;
  opponent: string;
  value: number;
};

export type HighLow = { high: number; low: number };

export const TREND_STATS = ["pts", "reb", "ast", "min", "ts_pct", "eff"] as const;
export type TrendStat = (typeof TREND_STATS)[number];

export type SentimentGaugeData = {
  score: number | null;
  label: string;
  volume: number;
  by_source: Record<string, number>;
};

export type ScreenerPlayer = {
  id: number;
  full_name: string;
  team_abbreviation: string;
  games_played: number;
  pts: number;
  reb: number;
  ast: number;
  stl: number;
  blk: number;
  ts_pct: number;
  sentiment_score: number | null;
};

export type DraftPick = {
  overall: number;
  round: number;
  pick: number;
  traded: boolean;
  player_name: string;
  position: string;
  height: string;
  weight: string;
  college: string;
  headshot_url: string;
  overall_rank: string | null;
  team: { id: number; abbreviation: string; name: string } | null;
};

export type DraftResponse = {
  year: number;
  status: string;
  picks: DraftPick[];
};

export type PlayerDetail = {
  id: number;
  full_name: string;
  position: string;
  jersey_number: string;
  headshot_url: string;
  team: { id: number; abbreviation: string; name: string; city: string } | null;
  games_played: number;
  averages: Record<string, number>;
  season_high_low: Record<string, HighLow>;
  trend: Record<TrendStat, TrendPoint[]>;
};
