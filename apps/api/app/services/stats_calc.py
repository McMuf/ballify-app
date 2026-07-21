"""Derived stat calculations shared across routes."""


def true_shooting_pct(pts: float, fga: float, fta: float) -> float:
    denom = 2 * (fga + 0.44 * fta)
    if denom <= 0:
        return 0.0
    return round(pts / denom, 4)


def efficiency(pts: float, reb: float, ast: float, stl: float, blk: float, fgm: float,
                fga: float, ftm: float, fta: float, tov: float) -> float:
    """NBA's own box-score 'EFF' stat (not full PER, which needs league-wide pace
    normalization), simple, precedented, and honestly labeled as EFF in the UI."""
    return round(
        (pts + reb + ast + stl + blk) - (fga - fgm) - (fta - ftm) - tov,
        1,
    )


def season_high_low(values: list[float]) -> dict:
    if not values:
        return {"high": 0, "low": 0}
    return {"high": max(values), "low": min(values)}
