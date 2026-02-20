import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import load_restaurant_data
from utils.scoring import calculate_total_score, get_top_n_merchants
from utils.ui import render_header, render_sidebar, kpi_card, GREEN, DARK

st.set_page_config(page_title="Merchant Scoring", page_icon=None, layout="wide")
render_header()
render_sidebar()

TIER_COLORS = {'S': '#06C167', 'A': '#34A853', 'B': '#F9A825', 'C': '#D32F2F'}

# ─── Data ────────────────────────────────────────────────────────────────────
df = load_restaurant_data()
if df.empty:
    st.error("Unable to load data.")
    st.stop()

df_scored = calculate_total_score(df)
df_scored = df_scored.sort_values('Rank')
top10 = get_top_n_merchants(df_scored, 10)

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("Merchant Scoring")
st.markdown(
    "<p style='color:#757575; font-size:14px; margin-bottom:1.5rem;'>"
    "200 restaurant brands ranked across Volume, Ops Quality, and Economics "
    "using PERCENTRANK scoring to handle the skewed trip distribution.</p>",
    unsafe_allow_html=True,
)

# ─── Summary KPIs ────────────────────────────────────────────────────────────
enterprise = df_scored[df_scored['Segment'] == 'Enterprise']
smb        = df_scored[df_scored['Segment'] == 'SMB']
tier_avgs  = df_scored.groupby('Tier')['Total_Score'].mean()

c1, c2, c3, c4, c5, c6 = st.columns(6)

kpi_card(c1, "200",                             "Total merchants")
kpi_card(c2, str(len(enterprise)),              "Enterprise (≥20 locations)")
kpi_card(c3, str(len(smb)),                     "SMB (<20 locations)")
kpi_card(c4, f"{tier_avgs.get('S', 0):.1f}",   "Tier S avg score (top 10)")
kpi_card(c5, f"{tier_avgs.get('A', 0):.1f}",   "Tier A avg score (11–50)")
kpi_card(c6, f"{tier_avgs.get('B', 0):.1f}",   "Tier B avg score (51–150)")

st.markdown("---")

# ─── Full Scoring Table ───────────────────────────────────────────────────────
st.markdown("### All 200 Merchants")

col_f1, col_f2 = st.columns(2)
with col_f1:
    tier_filter = st.multiselect(
        "Tier", options=['S', 'A', 'B', 'C'], default=['S', 'A', 'B', 'C']
    )
with col_f2:
    seg_filter = st.multiselect(
        "Segment", options=['Enterprise', 'SMB'], default=['Enterprise', 'SMB']
    )

table_df = df_scored[
    df_scored['Tier'].isin(tier_filter) &
    df_scored['Segment'].isin(seg_filter)
][[
    'Rank', 'Brand Name', 'Segment', 'Total_Score',
    'Volume_Score', 'Ops_Quality_Score', 'Economics_Score', 'Tier',
]].copy()

table_df.columns = [
    'Rank', 'Brand Name', 'Segment', 'Total (100)',
    'Volume (35)', 'Ops (30)', 'Economics (35)', 'Tier',
]

st.caption(f"{len(table_df)} merchants shown")

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
    },
)

# ─── Score Distribution ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Score Distribution by Tier")

fig_hist = px.histogram(
    df_scored,
    x='Total_Score',
    color='Tier',
    nbins=30,
    color_discrete_map=TIER_COLORS,
    category_orders={'Tier': ['S', 'A', 'B', 'C']},
    labels={'Total_Score': 'Total Score (0–100)', 'count': 'Merchants'},
)

fig_hist.update_layout(
    height=360,
    plot_bgcolor='white',
    paper_bgcolor='white',
    bargap=0.05,
    font=dict(family='DM Sans, sans-serif', size=12, color=DARK),
    xaxis=dict(gridcolor='#E0E0E0', griddash='dot', title='Total Score (0–100)'),
    yaxis=dict(gridcolor='#E0E0E0', griddash='dot', title='Merchants'),
    legend=dict(title='Tier', orientation='v'),
    margin=dict(t=10, b=40, l=50, r=20),
)

st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})

# ─── Top 10 Score Breakdown ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Top 10 — Score Component Breakdown")

chart_data = top10.sort_values('Total_Score', ascending=True)

fig_bar = go.Figure()

fig_bar.add_trace(go.Bar(
    name='Volume (35 pts)',
    y=chart_data['Brand Name'],
    x=chart_data['Volume_Score'],
    orientation='h',
    marker_color='#3D9BE9',
    text=chart_data['Volume_Score'].round(1),
    textposition='inside',
    insidetextanchor='middle',
    hovertemplate='<b>%{y}</b><br>Volume: %{x:.1f}/35<extra></extra>',
))

fig_bar.add_trace(go.Bar(
    name='Ops Quality (30 pts)',
    y=chart_data['Brand Name'],
    x=chart_data['Ops_Quality_Score'],
    orientation='h',
    marker_color='#F9A825',
    text=chart_data['Ops_Quality_Score'].round(1),
    textposition='inside',
    insidetextanchor='middle',
    hovertemplate='<b>%{y}</b><br>Ops: %{x:.1f}/30<extra></extra>',
))

fig_bar.add_trace(go.Bar(
    name='Economics (35 pts)',
    y=chart_data['Brand Name'],
    x=chart_data['Economics_Score'],
    orientation='h',
    marker_color=GREEN,
    text=chart_data['Economics_Score'].round(1),
    textposition='inside',
    insidetextanchor='middle',
    hovertemplate='<b>%{y}</b><br>Economics: %{x:.1f}/35<extra></extra>',
))

fig_bar.update_layout(
    barmode='stack',
    xaxis=dict(
        title='Score (max 100)', range=[0, 108],
        gridcolor='#E0E0E0', griddash='dot',
    ),
    yaxis_title='',
    height=480,
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(family='DM Sans, sans-serif', size=12, color=DARK),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    margin=dict(t=10, b=40, l=180, r=20),
)

for _, row in chart_data.iterrows():
    fig_bar.add_annotation(
        y=row['Brand Name'],
        x=row['Total_Score'] + 1,
        text=f"<b>{row['Total_Score']:.1f}</b>",
        showarrow=False,
        font=dict(size=12, color=DARK),
        xanchor='left',
    )

st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# ─── Tier Summary ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Tier Summary")

summary_rows = []
for tier in ['S', 'A', 'B', 'C']:
    t = df_scored[df_scored['Tier'] == tier]
    ent_pct = len(t[t['Segment'] == 'Enterprise']) / len(t) * 100 if len(t) else 0
    summary_rows.append({
        'Tier':            tier,
        'Count':           len(t),
        'Avg Score':       round(t['Total_Score'].mean(), 1),
        'Avg Trips':       f"{t['Annualized Trips'].mean():,.0f}",
        'Avg Wait (min)':  round(t['Avg. Courier Wait Time (min)'].mean(), 2),
        'Avg Defect Rate': f"{t['Order Defect Rate'].mean():.1%}",
        'Avg Basket':      f"${t['Avg. Basket Size'].mean():.2f}",
        'Enterprise %':    f"{ent_pct:.0f}%",
    })

st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

# ─── Methodology expander ─────────────────────────────────────────────────────
with st.expander("Scoring methodology"):
    st.markdown("""
    | Category | Points | Formula |
    |---|---|---|
    | **Volume** | 35 | `PERCENTRANK(Annualized Trips) × 35` |
    | **Wait Time** | 18 | `(1 − PERCENTRANK(Wait Time)) × 18` |
    | **Defect Rate** | 12 | `(1 − PERCENTRANK(Defect Rate)) × 12` |
    | **Economics** | 35 | `PERCENTRANK(Basket × Fee) × 35` |
    | **Total** | **100** | Sum of above |

    PERCENTRANK normalises relative position across a right-skewed distribution,
    giving each merchant a fair score regardless of outliers.

    Tier assignment is rank-based: S = 1–10 · A = 11–50 · B = 51–150 · C = 151–200.
    """)
