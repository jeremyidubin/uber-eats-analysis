import streamlit as st
import sys
import io
import zipfile
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent))

from utils.data_loader import load_restaurant_data
from utils.scoring import calculate_total_score, get_top_n_merchants
from utils.ui import inject_global_css, render_sidebar, kpi_card, GREEN, RED, DARK

st.set_page_config(
    page_title="Uber Eats U-City · Merchant Optimization",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_sidebar()

# ─── Data ─────────────────────────────────────────────────────────────────────
df = load_restaurant_data()
if not df.empty:
    df_scored = calculate_total_score(df)
    top_10    = get_top_n_merchants(df_scored, 10)
else:
    df_scored = pd.DataFrame()
    top_10    = pd.DataFrame()

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    f"<h1 style='margin-bottom:0.2rem;'>Merchant Optimization Simulator</h1>"
    f"<p style='color:{GREEN}; font-size:14px; font-weight:500; margin-bottom:0.2rem;'>"
    f"Score &rarr; Segment &rarr; Optimize Fee &amp; Feed Placement</p>"
    f"<p style='color:#757575; font-size:12px; margin-bottom:1.5rem;'>"
    f"Jeremy Dubin &nbsp;&middot;&nbsp; DCO Regional Insights &amp; Analytics &nbsp;&middot;&nbsp; February 2026"
    f"</p>",
    unsafe_allow_html=True,
)

# ─── Key Metrics ──────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

kpi_card(c1, "200", "Merchants analyzed")
kpi_card(c2, "10", "S-tier partners")

if not df_scored.empty:
    total_rev  = df_scored['Estimated_Annual_Revenue'].sum()
    rev_delta  = df_scored['Revenue_Delta_Default'].sum()
    new_trips  = df_scored['New_Trips_Default'].sum()
    curr_trips = df_scored['Annualized Trips'].sum()
    trip_pct   = (new_trips / curr_trips - 1) * 100
    sign       = "+" if rev_delta >= 0 else ""
    d_color    = GREEN if rev_delta >= 0 else RED

    kpi_card(c3, f"${total_rev/1e6:.1f}M",  "Current annual revenue")
    kpi_card(c4, f"{sign}${rev_delta/1e6:.1f}M",
             f"Projected revenue impact ({sign}{trip_pct:.1f}% trips)", accent=d_color)
else:
    kpi_card(c3, "--", "Current annual revenue")
    kpi_card(c4, "--", "Projected revenue impact")

st.markdown("---")

# ─── Navigation Cards ─────────────────────────────────────────────────────────
st.markdown("### Tools")

n1, n2, n3, n4 = st.columns(4)

_card = (
    "<div style='background:#FAFAFA; border:1px solid #E0E0E0;"
    "border-left:3px solid #06C167; padding:1.2rem; border-radius:4px; height:100%;'>"
    "<p style='font-weight:700; font-size:15px; color:#1A1A1A; margin:0 0 0.4rem 0;'>{title}</p>"
    "<p style='font-size:13px; color:#757575; margin:0; line-height:1.5;'>{desc}</p>"
    "</div>"
)

n1.markdown(_card.format(
    title="Merchant Scoring",
    desc="200 merchants ranked on a 100-pt PERCENTRANK model across Volume, Ops Quality, and Economics.",
), unsafe_allow_html=True)

n2.markdown(_card.format(
    title="Fee Simulator",
    desc="Adjust tier-level fee and volume assumptions with live sliders and see revenue impact instantly.",
), unsafe_allow_html=True)

n3.markdown(_card.format(
    title="Revenue Impact",
    desc="Waterfall chart, top gainers and losers, and a full merchant-level breakdown of the scenario.",
), unsafe_allow_html=True)

n4.markdown(_card.format(
    title="Methodology",
    desc="Scoring rationale, data sources, assumptions, and what's in vs. out of the model.",
), unsafe_allow_html=True)

st.markdown(
    "<p style='font-size:12px; color:#757575; margin-top:0.6rem;'>"
    "Use the sidebar to navigate between pages.</p>",
    unsafe_allow_html=True,
)

st.markdown("---")

# ─── Downloads ────────────────────────────────────────────────────────────────
st.markdown("### Downloads")

col_dl1, col_dl2, col_dl3 = st.columns(3)

with col_dl1:
    if not top_10.empty:
        st.download_button(
            label="Top 10 Merchants (CSV)",
            data=top_10.to_csv(index=False),
            file_name="top_10_merchants.csv",
            mime="text/csv",
            use_container_width=True,
        )

with col_dl2:
    if not df_scored.empty:
        all_scores_csv = df_scored[[
            'Brand Name', 'Rank', 'Tier', 'Total_Score',
            'Volume_Score', 'Ops_Quality_Score', 'Economics_Score',
        ]].to_csv(index=False)
        st.download_button(
            label="All Merchant Scores (CSV)",
            data=all_scores_csv,
            file_name="all_merchant_scores.csv",
            mime="text/csv",
            use_container_width=True,
        )

with col_dl3:
    if not df_scored.empty:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('top_10_merchants.csv', top_10.to_csv(index=False))
            zf.writestr(
                'all_merchant_scores.csv',
                df_scored[[
                    'Brand Name', 'Rank', 'Tier', 'Total_Score',
                    'Volume_Score', 'Ops_Quality_Score', 'Economics_Score',
                ]].to_csv(index=False),
            )
            tier_summary = df_scored.groupby('Tier').agg({
                'Brand Name': 'count',
                'Estimated_Annual_Revenue': 'sum',
                'Annualized Trips': 'sum',
                'Revenue_Delta_Default': 'sum',
            }).rename(columns={'Brand Name': 'Merchants'})
            zf.writestr('tier_summary.csv', tier_summary.to_csv())

        st.download_button(
            label="Full Package (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="merchant_optimization_analysis.zip",
            mime="application/zip",
            use_container_width=True,
        )
