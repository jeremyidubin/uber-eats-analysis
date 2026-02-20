"""
Shared simulation logic for the Fee Simulator and Revenue Impact Dashboard.

Session-state architecture
--------------------------
A single set of keys stores values in percentage-point format
(matching the slider display directly):

    s_fee_change, a_fee_change, b_fee_change, c_fee_change  (e.g. -2.0 means -2 pp)
    s_volume,     a_volume,     b_volume,     c_volume       (e.g. 20.0 means +20%)

init_session_state() initialises these keys if absent (safe to call on every page).
run_simulation() reads them, divides by 100 for the revenue formula, and enforces
a hard fee floor of 10% and cap of 30% per the case study specification.
"""
import streamlit as st

# ── Fee bounds (case study requirement) ───────────────────────────────────────
FEE_FLOOR = 0.10   # 10% minimum marketplace fee
FEE_CAP   = 0.30   # 30% maximum marketplace fee

# ── Defaults in percentage-point format (matches slider display) ───────────────
SS_DEFAULTS = {
    's_fee_change': -2.0,
    'a_fee_change': -0.5,
    'b_fee_change':  2.0,
    'c_fee_change':  3.0,
    's_volume':     20.0,
    'a_volume':     10.0,
    'b_volume':     -5.0,
    'c_volume':    -15.0,
}


def init_session_state():
    """
    Initialise all simulation session-state keys with defaults.
    Safe to call on every page load — skips keys that already exist.
    Call at the top of every page so values are set even if Home was never visited.
    """
    for k, v in SS_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def is_at_defaults():
    """Return True if every session-state value equals its default."""
    ss = st.session_state
    return all(ss.get(k, v) == v for k, v in SS_DEFAULTS.items())


def run_simulation(df):
    """
    Run the tiered fee/volume simulation using current session-state values.

    Session-state values are stored in percentage-point format (e.g. -2.0 for -2pp)
    and divided by 100 here for the revenue formula.

    The proposed fee is always clamped to [FEE_FLOOR, FEE_CAP] = [10%, 30%].
    This means some merchants may have their fee increase truncated (cap) or
    fee decrease truncated (floor), reducing the simulated revenue delta.

    Parameters
    ----------
    df : pd.DataFrame
        Output of load_restaurant_data() (contains both raw and Default columns).

    Returns
    -------
    sim : pd.DataFrame
        One row per merchant, all columns needed for display on both pages:
          Brand Name, Segment, Tier, Rank
          Annualized Trips, Avg. Basket Size, Marketplace Fee, Active Locations
          Curr Rev        — current annual revenue (= Estimated_Annual_Revenue)
          New Fee         — proposed marketplace fee after cap/floor (decimal)
          New Trips       — projected annualised trips
          New Rev         — projected annual revenue
          Rev Delta       — New Rev - Curr Rev
          Rev Delta %     — Rev Delta / Curr Rev * 100
          Fee Chg pp      — intended fee adjustment in percentage points (pre-clamp)
          Vol Lift %      — volume assumption in percentage points
          Fee Dir         — '↑' / '↓' / '—'
          Fee Capped      — True if this merchant hit the 30% cap
          Fee Floored     — True if this merchant hit the 10% floor

    tier_fee : dict  {S/A/B/C → decimal fee adjustment (pre-clamp)}
    tier_vol : dict  {S/A/B/C → decimal volume lift}
    """
    ss = st.session_state
    # Read PP values from session state, divide by 100 for revenue formula
    fee_s = ss.get('s_fee_change', SS_DEFAULTS['s_fee_change']) / 100
    fee_a = ss.get('a_fee_change', SS_DEFAULTS['a_fee_change']) / 100
    fee_b = ss.get('b_fee_change', SS_DEFAULTS['b_fee_change']) / 100
    fee_c = ss.get('c_fee_change', SS_DEFAULTS['c_fee_change']) / 100
    vol_s = ss.get('s_volume',     SS_DEFAULTS['s_volume'])     / 100
    vol_a = ss.get('a_volume',     SS_DEFAULTS['a_volume'])     / 100
    vol_b = ss.get('b_volume',     SS_DEFAULTS['b_volume'])     / 100
    vol_c = ss.get('c_volume',     SS_DEFAULTS['c_volume'])     / 100

    tier_fee = {'S': fee_s, 'A': fee_a, 'B': fee_b, 'C': fee_c}
    tier_vol = {'S': vol_s, 'A': vol_a, 'B': vol_b, 'C': vol_c}

    sim = df[[
        'Brand Name', 'Segment', 'Tier', 'Rank',
        'Annualized Trips', 'Avg. Basket Size', 'Marketplace Fee',
        'Active Locations', 'Estimated_Annual_Revenue',
        'Target_Fee_Default', 'New_Trips_Default',
        'New_Revenue_Default', 'Revenue_Delta_Default',
    ]].copy()

    sim['Curr Rev']   = sim['Estimated_Annual_Revenue']
    sim['Fee Chg pp'] = sim['Tier'].map(tier_fee) * 100   # intended adjustment (pre-clamp)
    sim['Vol Lift %'] = sim['Tier'].map(tier_vol) * 100
    sim['Fee Dir']    = sim['Tier'].map(tier_fee).apply(
        lambda x: '\u2191' if x > 0 else ('\u2193' if x < 0 else '\u2014')
    )

    # Compute raw (unclamped) proposed fee, rounded to avoid floating-point
    # false positives (e.g. 0.27 + 0.03 = 0.30000000000000004).
    # A merchant landing exactly at 30% is NOT flagged; only strictly-over is.
    raw_new_fee        = (sim['Marketplace Fee'] + sim['Tier'].map(tier_fee)).round(6)
    sim['New Fee']     = raw_new_fee.clip(lower=FEE_FLOOR, upper=FEE_CAP)
    sim['Fee Capped']  = raw_new_fee > FEE_CAP    # strictly above 30%
    sim['Fee Floored'] = raw_new_fee < FEE_FLOOR   # strictly below 10%

    sim['New Trips']  = sim['Annualized Trips'] * (1 + sim['Tier'].map(tier_vol))
    sim['New Rev']    = sim['New Trips'] * sim['Avg. Basket Size'] * sim['New Fee']
    sim['Rev Delta']  = sim['New Rev'] - sim['Curr Rev']
    sim['Rev Delta %'] = sim['Rev Delta'] / sim['Curr Rev'] * 100

    return sim, tier_fee, tier_vol
