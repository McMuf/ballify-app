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
