"""Shared UI helpers — typography, colors, KPI cards, header, sidebar."""
import streamlit as st

# ── Brand colors ───────────────────────────────────────────────────────────────
TIER_COLORS = {
    'S': '#06C167',   # Uber green
    'A': '#34A853',   # mid green
    'B': '#F9A825',   # amber
    'C': '#D32F2F',   # red
}
GREEN = '#06C167'
DARK  = '#1A1A1A'
RED   = '#D32F2F'
AMBER = '#F9A825'
GRAY  = '#757575'

# ── Global CSS ─────────────────────────────────────────────────────────────────
_CSS = """
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&display=swap" rel="stylesheet">
<style>
/* Base font */
html, body, [class*="css"], [data-testid], .stMarkdown, .stText,
.stDataFrame, .stMetric, button, input, select, textarea {
    font-family: 'DM Sans', sans-serif !important;
}

/* White sidebar */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div:first-child {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E0E0E0 !important;
}

/* Clean main bg */
.stApp { background: #FFFFFF; }
.block-container { padding-top: 1.5rem !important; }

/* Typography */
h1 { font-size: 24px !important; font-weight: 700 !important;
     color: #1A1A1A !important; letter-spacing: -0.3px; }
h2 { font-size: 20px !important; font-weight: 600 !important; color: #1A1A1A !important; }
h3 { font-size: 18px !important; font-weight: 500 !important; color: #1A1A1A !important; }

/* Horizontal rule */
hr { border: none; border-top: 1px solid #E0E0E0 !important; margin: 1.5rem 0; }

/* Native st.metric: white card with thin border */
[data-testid="stMetric"] {
    background: #FAFAFA;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 0.75rem 1rem;
}

/* Slider accent */
[data-testid="stSlider"] > div > div > div > div { background-color: #06C167 !important; }

/* Buttons */
button[kind="secondary"], button[data-testid="baseButton-secondary"] {
    border: 1px solid #E0E0E0 !important;
    border-radius: 4px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #1A1A1A !important;
    background: #FFFFFF !important;
}
button[kind="secondary"]:hover, button[data-testid="baseButton-secondary"]:hover {
    border-color: #06C167 !important;
    color: #06C167 !important;
}

/* Alert / info boxes */
[data-testid="stAlert"] { border-radius: 4px !important; font-size: 13px !important; }

/* Table header */
.dvn-scroller thead th {
    background-color: #F5F5F5 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}

/* Captions */
small, .stCaption { font-size: 12px !important; color: #757575 !important; }
</style>
"""


def inject_global_css():
    """Inject DM Sans font and global styles. Safe to call multiple times."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_header():
    """Inject global CSS and render a single-line page-top context strip."""
    inject_global_css()
    st.markdown(
        "<p style='font-size:11px; color:#757575; margin:0 0 1.5rem 0;"
        "padding-bottom:0.6rem; border-bottom:1px solid #E0E0E0;'>"
        "Uber Eats U-City &mdash; Merchant Optimization Simulator"
        "&nbsp;&nbsp;&middot;&nbsp;&nbsp; Jeremy Dubin"
        "</p>",
        unsafe_allow_html=True,
    )


def kpi_card(col, value: str, label: str, accent: str = None):
    """
    Render a clean white KPI card.
    accent — left-border color (defaults to green).
    """
    border = accent or GREEN
    col.markdown(
        f"<div style='background:#FAFAFA; border:1px solid #E0E0E0;"
        f"border-left:3px solid {border}; border-radius:4px;"
        f"padding:1rem 1.2rem;'>"
        f"<p style='font-size:1.5rem; font-weight:700; color:#1A1A1A; margin:0; line-height:1.2;'>{value}</p>"
        f"<p style='font-size:12px; color:#757575; margin:5px 0 0 0;'>{label}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _compute_sidebar_metrics():
    """Return (revenue_delta, market_share_pct) from current session state."""
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
    """Render a clean white sidebar with branding and live scenario metrics."""
    inject_global_css()
    with st.sidebar:
        # ── Brand strip ───────────────────────────────────────────────────────
        st.markdown(
            f"<div style='padding:0.5rem 0 0.8rem 0; border-bottom:2px solid {GREEN}; margin-bottom:1.2rem;'>"
            f"<p style='font-size:15px; font-weight:700; color:{DARK}; margin:0; letter-spacing:-0.2px;'>Uber Eats U-City</p>"
            f"<p style='font-size:12px; color:{GRAY}; margin:3px 0 0 0;'>Jeremy Dubin &nbsp;&middot;&nbsp; DCO I&amp;A</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── Live scenario metrics ─────────────────────────────────────────────
        delta, mkt_share = _compute_sidebar_metrics()
        if delta is not None:
            sign  = "+" if delta >= 0 else ""
            color = GREEN if delta >= 0 else RED
            st.markdown(
                f"<div style='margin-bottom:1rem;'>"
                f"<p style='font-size:11px; color:{GRAY}; margin:0 0 1px 0; text-transform:uppercase; letter-spacing:0.5px;'>Revenue Delta</p>"
                f"<p style='font-size:1.35rem; font-weight:700; color:{color}; margin:0; line-height:1.2;'>{sign}${delta/1e6:.1f}M</p>"
                f"</div>"
                f"<div style='margin-bottom:1rem;'>"
                f"<p style='font-size:11px; color:{GRAY}; margin:0 0 1px 0; text-transform:uppercase; letter-spacing:0.5px;'>Est. Market Share</p>"
                f"<p style='font-size:1.35rem; font-weight:700; color:{DARK}; margin:0; line-height:1.2;'>{mkt_share:.1f}%</p>"
                f"</div>"
                f"<p style='font-size:11px; color:{GRAY}; margin:0.8rem 0 0 0;"
                f"border-top:1px solid #E0E0E0; padding-top:0.6rem; line-height:1.8;'>"
                f"S &minus;2pp / A &minus;0.5pp / B +2pp / C +3pp<br>"
                f"S +20% / A +10% / B &minus;5% / C &minus;15%"
                f"</p>",
                unsafe_allow_html=True,
            )
