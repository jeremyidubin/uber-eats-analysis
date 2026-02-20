import streamlit as st
import sys
import io
import zipfile
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent))

from utils.data_loader import load_restaurant_data
from utils.scoring import calculate_total_score, get_top_n_merchants

st.set_page_config(
    page_title="Uber Eats U-City · Merchant Optimization",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Data ─────────────────────────────────────────────────────────────────────
df = load_restaurant_data()

if not df.empty:
    df_scored = calculate_total_score(df)
    top_10    = get_top_n_merchants(df_scored, 10)
else:
    df_scored = pd.DataFrame()
    top_10    = pd.DataFrame()

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="font-size:2.4rem; font-weight:700; color:#142328; margin-bottom:0.2rem;">
    Uber Eats U-City — Merchant Optimization Simulator
</h1>
<p style="color:#06C167; font-size:1.05rem; margin-bottom:0.3rem; font-weight:500;">
    Score → Segment → Optimize Fee &amp; Feed Placement
</p>
<p style="color:#888; font-size:0.9rem; margin-bottom:1.5rem;">
    Jeremy Dubin &nbsp;|&nbsp; DCO Regional Insights &amp; Analytics &nbsp;|&nbsp; February 2026
</p>
""", unsafe_allow_html=True)

# ─── Key Metrics ──────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Merchants Analyzed", "200")
with c2:
    st.metric("S-Tier Partners", "10", delta="Priority targets")
with c3:
    if not df_scored.empty:
        total_rev = df_scored['Estimated_Annual_Revenue'].sum()
        st.metric("Current Annual Revenue", f"${total_rev/1e6:.1f}M")
    else:
        st.metric("Current Annual Revenue", "--")
with c4:
    st.metric("Projected Revenue Impact", "+$3.6M", delta="+2.9% trip growth")

st.markdown("---")

# ─── Navigation Cards ─────────────────────────────────────────────────────────
st.markdown("## Tools")

n1, n2, n3, n4 = st.columns(4)

with n1:
    st.markdown("""
    <div style="background:#f8f9fa; border-left:5px solid #06C167;
                padding:1.2rem 1rem; border-radius:6px; min-height:130px;">
        <h4 style="margin:0 0 0.5rem 0;">🎯 Merchant Scoring</h4>
        <p style="color:#555; font-size:0.9rem; margin:0;">
            200 merchants ranked by a 100-pt PERCENTRANK model
            across Volume, Ops Quality, and Economics.
        </p>
    </div>
    """, unsafe_allow_html=True)

with n2:
    st.markdown("""
    <div style="background:#f8f9fa; border-left:5px solid #06C167;
                padding:1.2rem 1rem; border-radius:6px; min-height:130px;">
        <h4 style="margin:0 0 0.5rem 0;">💸 Fee Simulator</h4>
        <p style="color:#555; font-size:0.9rem; margin:0;">
            Adjust tier-level fee and volume assumptions with live
            sliders. See revenue impact recalculate instantly.
        </p>
    </div>
    """, unsafe_allow_html=True)

with n3:
    st.markdown("""
    <div style="background:#f8f9fa; border-left:5px solid #06C167;
                padding:1.2rem 1rem; border-radius:6px; min-height:130px;">
        <h4 style="margin:0 0 0.5rem 0;">📊 Revenue Impact</h4>
        <p style="color:#555; font-size:0.9rem; margin:0;">
            Waterfall chart, top gainers and losers, and a full
            merchant-level breakdown of the simulated scenario.
        </p>
    </div>
    """, unsafe_allow_html=True)

with n4:
    st.markdown("""
    <div style="background:#f8f9fa; border-left:5px solid #06C167;
                padding:1.2rem 1rem; border-radius:6px; min-height:130px;">
        <h4 style="margin:0 0 0.5rem 0;">📐 Methodology</h4>
        <p style="color:#555; font-size:0.9rem; margin:0;">
            Scoring rationale, data sources, assumptions, and
            what's in vs. out of the model.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("*Use the sidebar to navigate between pages.*")

st.markdown("---")

# ─── Downloads ────────────────────────────────────────────────────────────────
st.markdown("## Downloads")

col_dl1, col_dl2, col_dl3 = st.columns(3)

with col_dl1:
    if not top_10.empty:
        st.download_button(
            label="📥 Top 10 Merchants (CSV)",
            data=top_10.to_csv(index=False),
            file_name="top_10_merchants.csv",
            mime="text/csv",
            use_container_width=True
        )

with col_dl2:
    if not df_scored.empty:
        all_scores_csv = df_scored[['Brand Name', 'Rank', 'Tier', 'Total_Score',
                                    'Volume_Score', 'Ops_Quality_Score',
                                    'Economics_Score']].to_csv(index=False)
        st.download_button(
            label="📥 All Merchant Scores (CSV)",
            data=all_scores_csv,
            file_name="all_merchant_scores.csv",
            mime="text/csv",
            use_container_width=True
        )

with col_dl3:
    if not df_scored.empty:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('top_10_merchants.csv', top_10.to_csv(index=False))
            zf.writestr('all_merchant_scores.csv',
                        df_scored[['Brand Name', 'Rank', 'Tier', 'Total_Score',
                                   'Volume_Score', 'Ops_Quality_Score',
                                   'Economics_Score']].to_csv(index=False))
            tier_summary = df_scored.groupby('Tier').agg({
                'Brand Name': 'count',
                'Estimated_Annual_Revenue': 'sum',
                'Annualized Trips': 'sum',
                'Revenue_Delta_Default': 'sum',
            }).rename(columns={'Brand Name': 'Merchants'})
            zf.writestr('tier_summary.csv', tier_summary.to_csv())

        st.download_button(
            label="📦 Full Package (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="merchant_optimization_analysis.zip",
            mime="application/zip",
            use_container_width=True
        )

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("## Navigation")
st.sidebar.markdown("---")
st.sidebar.markdown("""
**🏠 Home** (Current)

**🎯 [Merchant Scoring](1_Merchant_Scoring)**

**💸 [Fee Simulator](2_Fee_Optimization)**

**📊 [Revenue Impact](3_Revenue_Impact_Dashboard)**

**📐 [Methodology](4_Methodology)**
""")

st.sidebar.markdown("---")

if not df_scored.empty:
    avg_fee     = df_scored['Marketplace Fee'].mean()
    total_trips = df_scored['Annualized Trips'].sum()
    top10_range = (f"{top_10['Total_Score'].min():.1f}–"
                   f"{top_10['Total_Score'].max():.1f}") if not top_10.empty else "N/A"

    st.sidebar.markdown("### Quick Stats")
    st.sidebar.info(f"""
**200 merchants** · 10 S · 40 A · 100 B · 50 C

**S-tier score:** {top10_range}

**Avg fee:** {avg_fee:.1%}

**Total trips:** {total_trips/1e6:.1f}M

**Platform rev:** ${df_scored['Estimated_Annual_Revenue'].sum()/1e6:.1f}M
""")

st.sidebar.markdown("---")
st.sidebar.markdown("Jeremy Dubin · DCO Regional Insights & Analytics · Feb 2026")
