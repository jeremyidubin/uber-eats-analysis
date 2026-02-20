import streamlit as st
import sys
import io
import zipfile
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent))

from utils.data_loader import load_restaurant_data
from utils.scoring import calculate_total_score, get_top_n_merchants
# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Uber Eats U-City · Merchant Optimization",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header {
    font-size: 2.8rem; font-weight: 700; color: #142328;
    text-align: center; padding: 1rem 0 0.4rem 0;
}
.sub-header {
    font-size: 1.15rem; color: #06C167; text-align: center;
    margin-bottom: 0.5rem; font-weight: 500;
}
.author-line {
    text-align: center; color: #888; font-size: 0.9rem; margin-bottom: 1.5rem;
}
.rec-card {
    background-color: #f8f9fa; border-left: 5px solid #06C167;
    padding: 1.5rem; border-radius: 8px; margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ─── Data ─────────────────────────────────────────────────────────────────────
df = load_restaurant_data()

if not df.empty:
    df_scored = calculate_total_score(df)
    top_10    = get_top_n_merchants(df_scored, 10)
else:
    df_scored = pd.DataFrame()
    top_10    = pd.DataFrame()

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown('<h1 class="main-header">Uber Eats U-City &mdash; Merchant Optimization Simulator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Recommendation 1: Score &rarr; Segment &rarr; Optimize Fee &amp; Feed Placement</p>', unsafe_allow_html=True)
st.markdown('<p class="author-line">Jeremy Dubin &nbsp;|&nbsp; DCO Regional Insights &amp; Analytics Case Study &nbsp;|&nbsp; February 2026</p>', unsafe_allow_html=True)

st.markdown("---")

# ─── AT A GLANCE ──────────────────────────────────────────────────────────────
st.markdown("## At a Glance")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Merchants Analyzed", "200",
              help="All restaurant brands in the U-City dataset")

with col2:
    st.metric("S-Tier Partners", "10", delta="Priority targets",
              help="Rank 1-10 merchants: fee reduction + Feed boost")

with col3:
    if not df_scored.empty:
        total_rev = df_scored['Estimated_Annual_Revenue'].sum()
        st.metric("Current Annual Revenue", f"${total_rev/1e6:.1f}M",
                  help="Sum of Trips x Basket x Fee across all 200 merchants")
    else:
        st.metric("Current Annual Revenue", "--")

with col4:
    st.metric("Projected Revenue Impact", "+$3.6M",
              delta="+2.9% trip growth",
              help="Default assumptions: S:-2pp/+20%, A:-0.5pp/+10%, B:+2pp/-5%, C:+3pp/-15%")

st.markdown("---")

# ─── EXECUTIVE SUMMARY ────────────────────────────────────────────────────────
st.markdown("## Executive Summary")

st.success("""
**Recommendation 1: Merchant Optimization**

Score 200 merchants, optimize Feed placement, and restructure fees by tier.
Projected revenue impact: **+$3.6M annually** with **2.9% trip growth**,
lifting estimated market share from 18% to approximately **18.5%**.
""")

st.markdown("""
<div class="rec-card">
<h4 style="color:#06C167; margin-top:0;">Four-Step Methodology</h4>
<ol style="color:#333; line-height:2.0; margin:0; padding-left:1.2rem;">
  <li><strong>Score</strong> &mdash; Rank all 200 merchants on Volume (35 pts), Ops Quality (30 pts),
      and Economics (35 pts) using PERCENTRANK to handle skewed trip distributions.</li>
  <li><strong>Segment</strong> &mdash; Assign S/A/B/C tiers by rank:
      S = top 10, A = 11&ndash;50, B = 51&ndash;150, C = 151&ndash;200.</li>
  <li><strong>Restructure fees</strong> &mdash; S: &minus;2pp, A: &minus;0.5pp, B: +2pp, C: +3pp
      (relative to each merchant's current rate).</li>
  <li><strong>Optimize Feed</strong> &mdash; Tier-based placement lifts:
      S: +20%, A: +10%, B: &minus;5%, C: &minus;15% (Feed algorithm, not fee elasticity).</li>
</ol>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─── DETAILED ANALYSIS TABS ───────────────────────────────────────────────────
st.markdown("## Detailed Analysis")

tab1, tab2, tab3 = st.tabs([
    "🎯 Merchant Scoring",
    "💸 Fee Simulator",
    "📊 Revenue Impact",
])

with tab1:
    st.markdown("### Merchant Prioritization Model")
    st.markdown("""
    **100-Point PERCENTRANK Scoring System:**
    - 📊 **Volume (35 pts)**: PERCENTRANK(Annualized Trips) — proven order demand
    - ⚙️ **Ops Quality (30 pts)**: Wait time (18 pts) + Defect rate (12 pts) — lower is better
    - 💰 **Economics (35 pts)**: PERCENTRANK(Basket × Fee) — revenue per order

    PERCENTRANK is used instead of min-max normalization to handle the right-skewed trip
    distribution (top brands have 10× the volume of median brands).
    """)

    if not top_10.empty:
        st.dataframe(
            top_10[['Brand Name', 'Rank', 'Tier', 'Total_Score',
                    'Volume_Score', 'Ops_Quality_Score', 'Economics_Score']].head(10),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("👉 **[View Full Scoring Analysis →](1_Merchant_Scoring)**", unsafe_allow_html=True)

with tab2:
    st.markdown("### Marketplace Fee Optimization")
    st.markdown("""
    **Tiered Fee Strategy (default assumptions):**

    | Tier | Merchants | Fee Change | Rationale |
    |---|---|---|---|
    | S (top 10) | 10 | −2 pp | Reward winners, lock in loyalty |
    | A (rank 11–50) | 40 | −0.5 pp | Slight incentive to push to S |
    | B (rank 51–150) | 100 | +2 pp | Modest yield improvement |
    | C (rank 151–200) | 50 | +3 pp | Maximize yield on low-performers |

    Eaters do **not** see marketplace fees, so fee increases do not directly reduce eater demand.
    Volume changes come from Feed placement shifts, not fee elasticity.
    """)

    st.markdown("👉 **[Run Interactive Fee Simulator →](2_Fee_Optimization)**", unsafe_allow_html=True)

with tab3:
    st.markdown("### Revenue Impact Dashboard")
    st.markdown("""
    **Default scenario result:**

    | Tier | Rev Delta | Drivers |
    |---|---|---|
    | S (top 10) | +$0.83M | Fee cut offset by +20% volume |
    | A (rank 11–50) | +$2.40M | Small fee cut + +10% volume |
    | B (rank 51–150) | +$0.63M | Fee increase, partially offset by −5% volume |
    | C (rank 151–200) | −$0.21M | Fee increase offset by −15% volume |
    | **Total** | **+$3.6M** | **+2.9% trip growth** |

    Adjust assumptions interactively on the Fee Simulator page.
    """)

    st.markdown("👉 **[View Revenue Impact Dashboard →](3_Revenue_Impact_Dashboard)**", unsafe_allow_html=True)

st.markdown("---")

# ─── RISK & MITIGATION ────────────────────────────────────────────────────────
st.markdown("## Risk Assessment & Mitigation")

st.info("**Approach:** Phased rollout over 12 months with real-time monitoring and tier-level circuit breakers.")

risk_col1, risk_col2 = st.columns(2)

with risk_col1:
    st.markdown("""
    <div class="rec-card">
    <h4 style="color:#e74c3c; margin-top:0;">Key Risks</h4>
    <ul style="color:#333; line-height:1.9;">
      <li><strong>B/C Merchant Churn:</strong> Fee increases could trigger departures,
          reducing volume more than the modeled &minus;5%/&minus;15%</li>
      <li><strong>Competitive Response:</strong> DoorDash may match S-tier fee reductions,
          neutralizing our Feed boost advantage</li>
      <li><strong>Volume Lift Uncertainty:</strong> +20% for S-tier is an assumption &mdash;
          actual Feed lift depends on Uber Eats product decisions</li>
      <li><strong>S-tier Dependency:</strong> If any of the 10 S-tier merchants churn
          after fee reduction, the revenue upside erodes quickly</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

with risk_col2:
    st.markdown("""
    <div class="rec-card">
    <h4 style="color:#06C167; margin-top:0;">Mitigation Strategies</h4>
    <ul style="color:#333; line-height:1.9;">
      <li><strong>Pilot First:</strong> Test fee changes on top 20 merchants for 60 days
          before full rollout; gate go/no-go on churn rate</li>
      <li><strong>S-tier Lock-in:</strong> Secure 12-month partnership agreements
          before reducing fees &mdash; tie benefits to exclusivity</li>
      <li><strong>Circuit Breakers:</strong> If a tier loses &gt;10% volume vs. model,
          auto-revert fee to current level</li>
      <li><strong>Validate Volume Lift:</strong> A/B test Feed placement changes
          with a control group before committing to full rollout</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("### Risk-Adjusted Projections (Recommendation 1 only)")

r1, r2, r3 = st.columns(3)
with r1:
    st.metric("Conservative (P25)", "+$2.0M",
              help="If B/C churn is 2x assumed, or S-tier volume lift is +10% instead of +20%")
with r2:
    st.metric("Base Case (P50)", "+$3.6M",
              help="Default assumptions from the spreadsheet model")
with r3:
    st.metric("Optimistic (P75)", "+$5.0M",
              help="If S-tier volume lift reaches +30% and B/C churn stays below model")

st.markdown("**Plan for base case (+$3.6M). Full rollout should be gated on pilot results exceeding the conservative threshold (+$2.0M).**")

st.markdown("---")

# ─── KEY INSIGHTS ─────────────────────────────────────────────────────────────
st.markdown("## Key Insights")

if not df_scored.empty:
    top_10_trips   = top_10['Annualized Trips'].sum()
    total_trips    = df_scored['Annualized Trips'].sum()
    top_10_pct     = top_10_trips / total_trips * 100

    top_10_rev     = top_10['Estimated_Annual_Revenue'].sum()
    total_rev      = df_scored['Estimated_Annual_Revenue'].sum()
    top_10_rev_pct = top_10_rev / total_rev * 100

    avg_fee    = df_scored['Marketplace Fee'].mean()
    min_fee    = df_scored['Marketplace Fee'].min()
    max_fee    = df_scored['Marketplace Fee'].max()

    ci1, ci2, ci3 = st.columns(3)

    with ci1:
        st.success(f"""
        **Merchant Concentration**
        - Top 10 drive **{top_10_pct:.1f}%** of total trips
        - Generate **{top_10_rev_pct:.1f}%** of total revenue
        - Concentrated impact from a small group
        """)

    with ci2:
        st.success(f"""
        **Revenue Opportunity**
        - Fee restructuring: **+$3.6M** (base case)
        - Net trip growth: **+2.9%** across all 200 merchants
        - Market share: **18% → ~18.5%**
        """)

    with ci3:
        st.success(f"""
        **Key Assumptions to Validate**
        - Avg fee: **{avg_fee:.1%}** (range {min_fee:.0%}–{max_fee:.0%})
        - Volume lifts are from **Feed placement**, not fee elasticity
        - 18% baseline is from the case statement, not modeled here
        """)

st.markdown("---")

# ─── DOWNLOADS ────────────────────────────────────────────────────────────────
st.markdown("## Download Analysis Package")

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
            zf.writestr('README.txt',
                "UBER EATS U-CITY MERCHANT OPTIMIZATION\n"
                "=======================================\n\n"
                "RECOMMENDATION 1: Merchant Optimization\n"
                "Score 200 merchants (PERCENTRANK model), assign S/A/B/C tiers,\n"
                "apply tiered fee restructuring + Feed placement lifts.\n\n"
                "DEFAULT ASSUMPTIONS\n"
                "Fee:    S -2pp | A -0.5pp | B +2pp | C +3pp\n"
                "Volume: S +20% | A +10%   | B -5%  | C -15%\n"
                "Result: +$3.6M revenue, +2.9% trips, 18% -> ~18.5% market share\n\n"
                "FILES\n"
                "top_10_merchants.csv    - S-tier merchants (rank 1-10)\n"
                "all_merchant_scores.csv - All 200 merchants scored and ranked\n"
                "tier_summary.csv        - Revenue and trip summary by tier\n\n"
                "Prepared by: Jeremy Dubin | February 2026\n"
                "DCO Regional Insights & Analytics Case Study\n"
            )

        st.download_button(
            label="📦 Full Package (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="merchant_optimization_analysis.zip",
            mime="application/zip",
            use_container_width=True
        )

st.markdown("---")

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("# Navigation")
st.sidebar.markdown("---")

st.sidebar.markdown("""
### Pages

**🏠 [Home](/)** (Current)
- Executive summary
- Key insights
- Data downloads

**🎯 [1. Merchant Scoring](1_Merchant_Scoring)**
- PERCENTRANK model
- Top 10 identification
- Tier S/A/B/C breakdown

**💸 [2. Fee Simulator](2_Fee_Optimization)**
- Interactive sliders
- Live revenue impact
- 3 charts + detail table

**📊 [3. Revenue Impact](3_Revenue_Impact_Dashboard)**
- Waterfall chart
- Top gainers/losers
- Tier comparison

**📐 [4. Methodology](4_Methodology)**
- Scoring rationale
- What's in vs out
- Data notes
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Stats")

if not df_scored.empty:
    avg_fee     = df_scored['Marketplace Fee'].mean()
    total_trips = df_scored['Annualized Trips'].sum()
    top10_range = (f"{top_10['Total_Score'].min():.1f} - "
                   f"{top_10['Total_Score'].max():.1f}") if not top_10.empty else "N/A"

    st.sidebar.info(f"""
    **Merchants:** 200 (10 S · 40 A · 100 B · 50 C)

    **S-tier Score Range:** {top10_range}

    **Avg Marketplace Fee:** {avg_fee:.1%}

    **Total Annual Trips:** {total_trips/1e6:.1f}M

    **Platform Revenue:** ${df_scored['Estimated_Annual_Revenue'].sum()/1e6:.1f}M
    """)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### About
**Jeremy Dubin**
DCO Regional Insights & Analytics
February 2026 · Python / Streamlit / Plotly
""")

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; color:#888; padding:1.5rem 0;
            border-top:1px solid #e0e0e0; margin-top:2rem; font-size:0.85rem;'>
    <strong>Uber Eats U-City &mdash; Merchant Optimization Simulator</strong><br>
    Built with Streamlit &nbsp;&bull;&nbsp; Recommendation 1 of the DCO Regional Insights &amp; Analytics case
</div>
""", unsafe_allow_html=True)
