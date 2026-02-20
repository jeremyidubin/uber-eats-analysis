import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import load_restaurant_data
from utils.scoring import calculate_total_score, get_top_n_merchants
from utils.ui import render_header, render_sidebar

st.set_page_config(page_title="Merchant Scoring Model", page_icon="🎯", layout="wide")
render_header()
render_sidebar()

st.markdown("""
<style>
.tier-s  { background-color:#048A46; color:white; padding:3px 10px; border-radius:4px; font-weight:700; }
.tier-a  { background-color:#06C167; color:white; padding:3px 10px; border-radius:4px; font-weight:700; }
.tier-b  { background-color:#FF8F00; color:white; padding:3px 10px; border-radius:4px; font-weight:700; }
.tier-c  { background-color:#E53935; color:white; padding:3px 10px; border-radius:4px; font-weight:700; }
.summary-card {
    background: linear-gradient(135deg, #142328 0%, #1e3a42 100%);
    color: white; padding: 1.2rem 1.5rem; border-radius: 10px;
    border-left: 5px solid #06C167; text-align: center;
}
.summary-card h2 { margin:0; font-size:2rem; color:#06C167; }
.summary-card p  { margin:0; font-size:0.85rem; opacity:0.85; }
</style>
""", unsafe_allow_html=True)

# ─── Data ────────────────────────────────────────────────────────────────────
df = load_restaurant_data()
if df.empty:
    st.error("Unable to load data. Ensure the Excel file is in data/.")
    st.stop()

df_scored = calculate_total_score(df)
df_scored = df_scored.sort_values('Rank')

top10 = get_top_n_merchants(df_scored, 10)

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("🎯 Merchant Scoring Model")
st.markdown("""
Ranks all **200 restaurant brands** across three dimensions using **PERCENTRANK scoring**
to handle the skewed trip distribution (top merchants 10×+ average volume).
""")
st.markdown("---")

# ─── 1. SUMMARY CARDS ────────────────────────────────────────────────────────
st.markdown("### Summary")

enterprise = df_scored[df_scored['Segment'] == 'Enterprise']
smb        = df_scored[df_scored['Segment'] == 'SMB']

tier_avgs = df_scored.groupby('Tier')['Total_Score'].mean()

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(f"""
    <div class="summary-card">
        <h2>200</h2><p>Total Merchants</p>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="summary-card">
        <h2>{len(enterprise)}</h2><p>Enterprise<br>(≥20 locations)</p>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="summary-card">
        <h2>{len(smb)}</h2><p>SMB<br>(&lt;20 locations)</p>
    </div>""", unsafe_allow_html=True)

with col4:
    s_avg = tier_avgs.get('S', 0)
    st.markdown(f"""
    <div class="summary-card">
        <h2>{s_avg:.1f}</h2><p>Tier S Avg Score<br>(top 10)</p>
    </div>""", unsafe_allow_html=True)

with col5:
    a_avg = tier_avgs.get('A', 0)
    st.markdown(f"""
    <div class="summary-card">
        <h2>{a_avg:.1f}</h2><p>Tier A Avg Score<br>(rank 11–50)</p>
    </div>""", unsafe_allow_html=True)

with col6:
    b_avg = tier_avgs.get('B', 0)
    st.markdown(f"""
    <div class="summary-card">
        <h2>{b_avg:.1f}</h2><p>Tier B Avg Score<br>(rank 51–150)</p>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ─── 2. FULL SORTABLE TABLE ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("### All 200 Merchants — Full Scoring Table")

col_f1, col_f2 = st.columns([1, 1])
with col_f1:
    tier_filter = st.multiselect(
        "Filter by Tier",
        options=['S', 'A', 'B', 'C'],
        default=['S', 'A', 'B', 'C']
    )
with col_f2:
    seg_filter = st.multiselect(
        "Filter by Segment",
        options=['Enterprise', 'SMB'],
        default=['Enterprise', 'SMB']
    )

table_df = df_scored[
    df_scored['Tier'].isin(tier_filter) &
    df_scored['Segment'].isin(seg_filter)
][[
    'Rank', 'Brand Name', 'Segment', 'Total_Score',
    'Volume_Score', 'Ops_Quality_Score', 'Economics_Score', 'Tier'
]].copy()

table_df.columns = [
    'Rank', 'Brand Name', 'Segment', 'Total (100)',
    'Volume (35)', 'Ops (30)', 'Economics (35)', 'Tier'
]

st.caption(f"Showing {len(table_df)} merchants")

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    height=420,
    column_config={
        'Tier': st.column_config.TextColumn('Tier', width='small'),
        'Total (100)': st.column_config.ProgressColumn(
            'Total (100)', min_value=0, max_value=100, format="%.1f"
        ),
        'Volume (35)': st.column_config.ProgressColumn(
            'Volume (35)', min_value=0, max_value=35, format="%.1f"
        ),
        'Ops (30)': st.column_config.ProgressColumn(
            'Ops (30)', min_value=0, max_value=30, format="%.1f"
        ),
        'Economics (35)': st.column_config.ProgressColumn(
            'Economics (35)', min_value=0, max_value=35, format="%.1f"
        ),
    }
)

# ─── 3. SCORE DISTRIBUTION HISTOGRAM ────────────────────────────────────────
st.markdown("---")
st.markdown("### Score Distribution by Tier")

tier_color_map = {'S': '#064e3b', 'A': '#06C167', 'B': '#FFB800', 'C': '#e74c3c'}

fig_hist = px.histogram(
    df_scored,
    x='Total_Score',
    color='Tier',
    nbins=30,
    color_discrete_map=tier_color_map,
    category_orders={'Tier': ['S', 'A', 'B', 'C']},
    labels={'Total_Score': 'Total Score (0–100)', 'count': 'Number of Merchants'},
    title='Total Score Distribution (All 200 Merchants, Colored by Tier)'
)

fig_hist.update_layout(
    height=380,
    plot_bgcolor='white',
    paper_bgcolor='white',
    bargap=0.05,
    xaxis=dict(gridcolor='#e0e0e0'),
    yaxis=dict(gridcolor='#e0e0e0', title='Merchant Count'),
    legend=dict(title='Tier', orientation='v')
)

st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})

# ─── 4. TOP 10 STACKED BAR ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Top 10 Merchants — Score Component Breakdown")

chart_data = top10.sort_values('Total_Score', ascending=True)

fig_bar = go.Figure()

fig_bar.add_trace(go.Bar(
    name='Volume (35 pts)',
    y=chart_data['Brand Name'],
    x=chart_data['Volume_Score'],
    orientation='h',
    marker_color='#3498db',
    text=chart_data['Volume_Score'].round(1),
    textposition='inside',
    insidetextanchor='middle',
    hovertemplate='<b>%{y}</b><br>Volume: %{x:.1f}/35<extra></extra>'
))

fig_bar.add_trace(go.Bar(
    name='Ops Quality (30 pts)',
    y=chart_data['Brand Name'],
    x=chart_data['Ops_Quality_Score'],
    orientation='h',
    marker_color='#e67e22',
    text=chart_data['Ops_Quality_Score'].round(1),
    textposition='inside',
    insidetextanchor='middle',
    hovertemplate='<b>%{y}</b><br>Ops: %{x:.1f}/30<extra></extra>'
))

fig_bar.add_trace(go.Bar(
    name='Economics (35 pts)',
    y=chart_data['Brand Name'],
    x=chart_data['Economics_Score'],
    orientation='h',
    marker_color='#06C167',
    text=chart_data['Economics_Score'].round(1),
    textposition='inside',
    insidetextanchor='middle',
    hovertemplate='<b>%{y}</b><br>Economics: %{x:.1f}/35<extra></extra>'
))

fig_bar.update_layout(
    barmode='stack',
    title='Volume | Ops Quality | Economics — Top 10 Merchants',
    xaxis_title='Score Points (max 100)',
    yaxis_title='',
    height=500,
    plot_bgcolor='white',
    paper_bgcolor='white',
    xaxis=dict(gridcolor='#e0e0e0', range=[0, 105]),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    margin=dict(l=180)
)

# Add total score labels at end of bars
for _, row in chart_data.iterrows():
    fig_bar.add_annotation(
        y=row['Brand Name'],
        x=row['Total_Score'] + 1,
        text=f"<b>{row['Total_Score']:.1f}</b>",
        showarrow=False,
        font=dict(size=12, color='#142328'),
        xanchor='left'
    )

st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# ─── 5. TIER SUMMARY TABLE ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Tier Summary")

summary_rows = []
for tier in ['S', 'A', 'B', 'C']:
    t = df_scored[df_scored['Tier'] == tier]
    ent_pct = len(t[t['Segment'] == 'Enterprise']) / len(t) * 100 if len(t) else 0
    smb_pct = 100 - ent_pct
    summary_rows.append({
        'Tier': tier,
        'Count': len(t),
        'Avg Score': round(t['Total_Score'].mean(), 1),
        'Avg Trips': f"{t['Annualized Trips'].mean():,.0f}",
        'Avg Wait (min)': round(t['Avg. Courier Wait Time (min)'].mean(), 2),
        'Avg Defect Rate': f"{t['Order Defect Rate'].mean():.1%}",
        'Avg Basket Size': f"${t['Avg. Basket Size'].mean():.2f}",
        'Enterprise %': f"{ent_pct:.0f}%",
        'SMB %': f"{smb_pct:.0f}%",
    })

summary_df = pd.DataFrame(summary_rows)

st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ─── Methodology expander ─────────────────────────────────────────────────────
with st.expander("📐 Scoring Methodology"):
    st.markdown("""
    | Category | Points | Formula |
    |---|---|---|
    | **Volume** | 35 | `PERCENTRANK(Annualized Trips) × 35` |
    | **Wait Time** | 18 | `(1 − PERCENTRANK(Wait Time)) × 18` |
    | **Defect Rate** | 12 | `(1 − PERCENTRANK(Defect Rate)) × 12` |
    | **Economics** | 35 | `PERCENTRANK(Rev per Order) × 35` |
    | **Total** | **100** | Sum of above |

    **Why PERCENTRANK?** Trip volume is heavily right-skewed — a handful of merchants
    have 1M+ trips while most are under 100K. Min-max scaling would compress
    most merchants near zero. PERCENTRANK normalises relative position, giving
    each merchant a fair score regardless of outliers.

    **Tier assignment** is rank-based (not score-based):
    S = rank 1–10 · A = rank 11–50 · B = rank 51–150 · C = rank 151–200
    """)
