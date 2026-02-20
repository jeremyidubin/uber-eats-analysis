"""
Shared UI helpers used by every page.
Import with:
    from utils.ui import render_header, render_sidebar
"""
import streamlit as st

# ─── Brand colors ─────────────────────────────────────────────────────────────
TIER_COLORS = {
    'S': '#048A46',   # dark green
    'A': '#06C167',   # Uber green
    'B': '#FF8F00',   # amber
    'C': '#E53935',   # red
}
GREEN   = '#06C167'
DARK    = '#142328'
RED     = '#E53935'
AMBER   = '#FF8F00'


def render_header(page_subtitle: str = ""):
    """Render the standard app header (call at the top of every page, before st.title)."""
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, {DARK} 0%, #1e3a42 100%);
                padding: 0.75rem 1.5rem; border-radius: 8px; margin-bottom: 1rem;
                border-bottom: 3px solid {GREEN};">
        <p style="margin:0; color:{GREEN}; font-size:0.75rem; font-weight:600; letter-spacing:1px; text-transform:uppercase;">
            Uber Eats U-City · Merchant Optimization Simulator
        </p>
        <p style="margin:0; color:#9ab8c0; font-size:0.72rem;">
            Jeremy Dubin — DCO Regional Insights &amp; Analytics
        </p>
    </div>
    """, unsafe_allow_html=True)


def _compute_sidebar_metrics():
    """
    Return (revenue_delta, market_share_pct) based on current session-state values.
    Delegates entirely to run_simulation() so numbers are identical across all pages.
    Falls back to (None, None) on any error.
    """
    try:
        from utils.data_loader import load_restaurant_data
        from utils.simulation import run_simulation

        df  = load_restaurant_data()
        sim, _, _ = run_simulation(df)

        curr_trips   = sim['Annualized Trips'].sum()
        new_trips    = sim['New Trips'].sum()
        trip_chg_pct = (new_trips - curr_trips) / curr_trips * 100
        delta        = sim['Rev Delta'].sum()
        mkt_share    = 0.18 * (1 + trip_chg_pct / 100) * 100
        return delta, mkt_share

    except Exception:
        return None, None


def render_sidebar():
    """Render sidebar nav context and live fee simulator metrics."""
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:0.6rem 0; border-bottom: 1px solid #2a4a52; margin-bottom:0.8rem;">
            <p style="color:{GREEN}; font-size:0.7rem; font-weight:700;
                      letter-spacing:1px; text-transform:uppercase; margin:0;">
                Uber Eats U-City
            </p>
            <p style="color:#9ab8c0; font-size:0.65rem; margin:0;">
                Merchant Optimization Simulator
            </p>
        </div>
        """, unsafe_allow_html=True)

        delta, mkt_share = _compute_sidebar_metrics()

        if delta is not None:
            delta_color = GREEN if delta >= 0 else RED
            delta_sign  = "+" if delta >= 0 else ""
            share_color = GREEN if mkt_share >= 18 else AMBER

            st.markdown(f"""
            <div style="background:#0d1f25; border-radius:6px; padding:0.8rem 1rem;
                        margin-bottom:0.5rem; border-left:3px solid {delta_color};">
                <p style="color:#9ab8c0; font-size:0.65rem; margin:0 0 2px 0; text-transform:uppercase; letter-spacing:0.5px;">
                    Fee Simulator Delta
                </p>
                <p style="color:{delta_color}; font-size:1.3rem; font-weight:700; margin:0;">
                    {delta_sign}${delta/1e6:.1f}M
                </p>
            </div>
            <div style="background:#0d1f25; border-radius:6px; padding:0.8rem 1rem;
                        margin-bottom:0.5rem; border-left:3px solid {share_color};">
                <p style="color:#9ab8c0; font-size:0.65rem; margin:0 0 2px 0; text-transform:uppercase; letter-spacing:0.5px;">
                    Est. Market Share
                </p>
                <p style="color:{share_color}; font-size:1.3rem; font-weight:700; margin:0;">
                    {mkt_share:.1f}%
                </p>
            </div>
            """, unsafe_allow_html=True)
