import pandas as pd
import numpy as np
from scipy.stats import percentileofscore


# ─── PERCENTRANK helper ───────────────────────────────────────────────────────

def _prank(series: pd.Series, kind: str = "rank") -> pd.Series:
    """
    Vectorised PERCENTRANK equivalent (mirrors Excel PERCENTRANK.INC).
    Returns values in [0, 1].
    """
    arr = series.values
    return pd.Series(
        [percentileofscore(arr, v, kind=kind) / 100 for v in arr],
        index=series.index
    )


# ─── Component score functions ────────────────────────────────────────────────

def calculate_volume_score(df: pd.DataFrame) -> pd.Series:
    """
    Volume Score (35 pts max).
    Formula: PERCENTRANK(Annualized Trips) × 35  — higher trips = higher score.
    """
    return (_prank(df['Annualized Trips']) * 35).round(2)


def calculate_wait_time_score(df: pd.DataFrame) -> pd.Series:
    """
    Wait Time Score (18 pts max).
    Formula: (1 − PERCENTRANK(wait)) × 18  — lower wait = higher score.
    """
    return ((1 - _prank(df['Avg. Courier Wait Time (min)'])) * 18).round(2)


def calculate_defect_score(df: pd.DataFrame) -> pd.Series:
    """
    Defect Score (12 pts max).
    Formula: (1 − PERCENTRANK(defect rate)) × 12  — lower defect = higher score.
    """
    return ((1 - _prank(df['Order Defect Rate'])) * 12).round(2)


def calculate_economics_score(df: pd.DataFrame) -> pd.Series:
    """
    Economics Score (35 pts max).
    Input: Rev per Order = Basket Size × Marketplace Fee.
    Formula: PERCENTRANK(rev_per_order) × 35  — higher rev = higher score.
    """
    rev_per_order = df['Avg. Basket Size'] * df['Marketplace Fee']
    return (_prank(rev_per_order) * 35).round(2)


def calculate_ops_quality_score(df: pd.DataFrame):
    """
    Ops Quality Score (30 pts max = wait 18 + defect 12).
    Returns (total, wait_score, defect_score).
    """
    wait = calculate_wait_time_score(df)
    defect = calculate_defect_score(df)
    return (wait + defect).round(2), wait, defect


# ─── Main scoring entry point ─────────────────────────────────────────────────

def calculate_total_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a scored dataframe.

    If the dataframe already contains pre-calculated score columns (loaded from
    the spreadsheet via data_loader.load_restaurant_data), this function is a
    pass-through — it returns the dataframe unchanged so that the spreadsheet
    values are preserved as the source of truth.

    If the score columns are absent (e.g. in unit tests with synthetic data),
    it falls back to computing scores from scratch using PERCENTRANK.

    Scoring spec (100 pts total):
      Volume    35 pts  PERCENTRANK(Annualized Trips) × 35
      Wait Time 18 pts  (1 − PERCENTRANK(Wait)) × 18
      Defect    12 pts  (1 − PERCENTRANK(Defect)) × 12
      Economics 35 pts  PERCENTRANK(Rev per Order) × 35

    Tier assignment (rank-based):
      S  → rank  1–10
      A  → rank 11–50
      B  → rank 51–150
      C  → rank 151–200
    """
    # Pass-through: pre-calculated scores already loaded from spreadsheet
    if 'Total_Score' in df.columns and 'Tier' in df.columns:
        return df.copy()

    # Fallback: compute from scratch (for synthetic/test data)
    df_scored = df.copy()

    df_scored['Volume_Score']    = calculate_volume_score(df)
    ops_total, wait_s, defect_s  = calculate_ops_quality_score(df)
    df_scored['Wait_Time_Score'] = wait_s
    df_scored['Defect_Rate_Score'] = defect_s
    df_scored['Ops_Quality_Score'] = ops_total
    df_scored['Economics_Score'] = calculate_economics_score(df)

    df_scored['Total_Score'] = (
        df_scored['Volume_Score'] +
        df_scored['Ops_Quality_Score'] +
        df_scored['Economics_Score']
    ).round(2)

    df_scored['Rank'] = (
        df_scored['Total_Score']
        .rank(ascending=False, method='min')
        .astype(int)
    )

    def _tier(rank):
        if rank <= 10:   return 'S'
        elif rank <= 50:  return 'A'
        elif rank <= 150: return 'B'
        return 'C'

    df_scored['Tier'] = df_scored['Rank'].apply(_tier)
    return df_scored


# ─── Utility helpers ──────────────────────────────────────────────────────────

def get_top_n_merchants(df_scored: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return df_scored.nsmallest(n, 'Rank')


def get_score_color(score: float) -> str:
    if score >= 80:
        return '#06C167'
    elif score >= 60:
        return '#FFB800'
    elif score >= 40:
        return '#FF8C00'
    return '#E74C3C'


def get_tier_color(tier: str) -> str:
    return {
        'S': '#048A46',   # dark green
        'A': '#06C167',   # Uber green
        'B': '#FF8F00',   # amber
        'C': '#E53935',   # red
    }.get(tier, '#95a5a6')


def get_strength_badge(strength: str) -> str:
    return {'Volume': '📊', 'Operations': '⚙️', 'Growth': '📈', 'Economics': '💰'}.get(strength, '⭐')
