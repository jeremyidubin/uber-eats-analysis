# ─── Model Configuration ─────────────────────────────────────────────────────
# Central config dictionary for all scoring model inputs.
# Import this in any page/util: from utils.config import CONFIG

CONFIG = {

    # ── Scoring weights (must sum to 100) ────────────────────────────────────
    # PERCENTRANK-based model: handles skewed trip distribution.
    "volume_points":    35,   # PERCENTRANK(Annualized Trips) × 35
    "ops_points":       30,   # wait_time + defect combined
    "wait_time_points": 18,   # (1 − PERCENTRANK(wait)) × 18
    "defect_points":    12,   # (1 − PERCENTRANK(defect)) × 12
    "econ_points":      35,   # PERCENTRANK(Rev per Order) × 35

    # ── Tier cut-offs (rank-based, top-N per tier) ───────────────────────────
    # S: top 10, A: next 40 (rank 11–50), B: next 100, C: rest
    "tier_cutoffs": {
        "S":  10,
        "A":  50,
        "B": 150,
        "C": 200,
    },

    # ── Segment threshold ────────────────────────────────────────────────────
    "enterprise_threshold": 20,   # Active Locations >= 20 → Enterprise, else SMB

    # ── Branding ─────────────────────────────────────────────────────────────
    "colors": {
        "green":  "#06C167",
        "dark":   "#142328",
        "red":    "#E53935",
        "amber":  "#FF8F00",
        "blue":   "#3498db",
        "white":  "#FFFFFF",
    },
    # ── Tier colors ───────────────────────────────────────────────────────────
    "tier_colors": {
        "S": "#048A46",   # dark green
        "A": "#06C167",   # Uber green
        "B": "#FF8F00",   # amber
        "C": "#E53935",   # red
    },

    # ── Unit economics assumptions ───────────────────────────────────────────
    "avg_delivery_fee":    2.50,   # $ baseline delivery fee
    "target_defect_rate":  0.045,  # 4.5% quality target
    "cac_per_new_eater":  15.00,   # $ cost to acquire a new customer

    # ── LTV assumptions ──────────────────────────────────────────────────────
    "retention_curve": {
        "month_1":  0.65,
        "month_3":  0.45,
        "month_6":  0.35,
        "month_12": 0.20,
        "month_24": 0.10,
    },
    "avg_orders_per_month":   2.5,
    "ltv_cac_healthy_ratio":  3.0,
    "cac_payback_ideal_months": 6,
}
