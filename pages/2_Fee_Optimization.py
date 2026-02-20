import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import load_restaurant_data
from utils.scoring import calculate_total_score
from utils.ui import render_header, render_sidebar
from utils.simulation import run_simulation, SS_DEFAULTS

st.set_page_config(page_title="Fee Simulator", page_icon="💸", layout="wide")
render_header()
render_sidebar()

st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #142328 0%, #1e3a42 100%);
    color: white; padding: 1.4rem 1.5rem; border-radius: 10px;
    border-left: 5px solid #06C167; text-align: center;
}
.metric-card h2 { margin: 0; font-size: 2.2rem; }
.metric-card p  { margin: 0; font-size: 0.85rem; opacity: 0.85; margin-top: 4px; }
.positive { color: #06C167; }
.negative { color: #e74c3c; }
</style>
""", unsafe_allow_html=True)

# ─── Data ────────────────────────────────────────────────────────────────────
df_raw = load_restaurant_data()
if df_raw.empty:
    st.error("Unable to load data.")
    st.stop()

df = calculate_total_score(df_raw)

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("💸 Fee Simulator")
st.markdown("""
Simulate how **tiered fee adjustments** and **Feed placement volume lifts** affect total marketplace revenue.
Fee changes are relative (±pp from each merchant's current rate). Volume lifts reflect Feed algorithm changes, not fee elasticity.
""")
st.markdown("---")

# ─── TOP: SLIDERS ────────────────────────────────────────────────────────────
reset_col, _ = st.columns([1, 5])
with reset_col:
    if st.button("🔄 Reset to Defaults", use_container_width=True):
        # Delete keys so sliders reinitialise from their value= parameter on rerun
        for k in SS_DEFAULTS:
            st.session_state.pop(k, None)
        st.rerun()

st.markdown("#### Fee Adjustments by Tier (percentage points, relative to current fee)")
fc1, fc2, fc3, fc4 = st.columns(4)

with fc1:
    st.markdown("**🏆 S-tier (top 10)**")
    st.slider("S-tier fee change (%pt)", min_value=-5.0, max_value=5.0, step=0.1,
              value=SS_DEFAULTS['s_fee_change'], key='s_fee_change', format="%g%%",
              help="Default: −2pp. Negative = fee reduction, positive = fee increase.")
with fc2:
    st.markdown("**🥇 A-tier (rank 11–50)**")
    st.slider("A-tier fee change (%pt)", min_value=-5.0, max_value=5.0, step=0.1,
              value=SS_DEFAULTS['a_fee_change'], key='a_fee_change', format="%g%%",
              help="Default: −0.5pp.")
with fc3:
    st.markdown("**🥈 B-tier (rank 51–150)**")
    st.slider("B-tier fee change (%pt)", min_value=-5.0, max_value=5.0, step=0.1,
              value=SS_DEFAULTS['b_fee_change'], key='b_fee_change', format="%g%%",
              help="Default: +2pp.")
with fc4:
    st.markdown("**🥉 C-tier (rank 151–200)**")
    st.slider("C-tier fee change (%pt)", min_value=-5.0, max_value=5.0, step=0.1,
              value=SS_DEFAULTS['c_fee_change'], key='c_fee_change', format="%g%%",
              help="Default: +3pp.")

st.markdown("#### Volume Assumptions by Tier (Feed placement effect)")
vc1, vc2, vc3, vc4 = st.columns(4)

with vc1:
    st.slider("S-tier volume change (%)", min_value=-40.0, max_value=40.0, step=1.0,
              value=SS_DEFAULTS['s_volume'], key='s_volume', format="%g%%",
              help="Default: +20%. Reflects Feed placement boost, not fee elasticity.")
with vc2:
    st.slider("A-tier volume change (%)", min_value=-40.0, max_value=40.0, step=1.0,
              value=SS_DEFAULTS['a_volume'], key='a_volume', format="%g%%",
              help="Default: +10%.")
with vc3:
    st.slider("B-tier volume change (%)", min_value=-40.0, max_value=40.0, step=1.0,
              value=SS_DEFAULTS['b_volume'], key='b_volume', format="%g%%",
              help="Default: −5%.")
with vc4:
    st.slider("C-tier volume change (%)", min_value=-40.0, max_value=40.0, step=1.0,
              value=SS_DEFAULTS['c_volume'], key='c_volume', format="%g%%",
              help="Default: −15%.")

st.markdown("---")

# ─── CALCULATIONS ────────────────────────────────────────────────────────────
sim, tier_fee, tier_vol = run_simulation(df)

# Column aliases expected by the rest of this page
sim['Current Revenue'] = sim['Curr Rev']
sim['Revenue Delta']   = sim['Rev Delta']
sim['New Revenue']     = sim['New Rev']
sim['Fee Change']      = sim['Fee Chg pp']
sim['Fee Direction']   = sim['Fee Dir']
sim['Fee Adj']         = sim['Fee Chg pp'] / 100
sim['Vol Lift']        = sim['Vol Lift %'] / 100

total_delta      = sim['Revenue Delta'].sum()
total_curr_trips = sim['Annualized Trips'].sum()
total_new_trips  = sim['New Trips'].sum()
trip_change_pct  = (total_new_trips - total_curr_trips) / total_curr_trips * 100
new_market_share = 0.18 * (1 + trip_change_pct / 100) * 100
fee_increases    = len(sim[sim['Fee Chg pp'] > 0])
fee_decreases    = len(sim[sim['Fee Chg pp'] < 0])

# ─── FEE CAP/FLOOR WARNINGS ───────────────────────────────────────────────────
n_capped  = int(sim['Fee Capped'].sum())
n_floored = int(sim['Fee Floored'].sum())
if n_capped > 0:
    st.warning(
        f"**{n_capped} merchant{'s' if n_capped > 1 else ''} capped at 30% maximum fee** — "
        "their fee increase was truncated to stay within the case study limit."
    )
if n_floored > 0:
    st.warning(
        f"**{n_floored} merchant{'s' if n_floored > 1 else ''} floored at 10% minimum fee** — "
        "their fee decrease was truncated to stay within the case study limit."
    )

# ─── MIDDLE: KEY METRICS ─────────────────────────────────────────────────────
st.markdown("### Impact Summary")

m1, m2, m3, m4 = st.columns(4)

delta_color = "positive" if total_delta >= 0 else "negative"
delta_sign  = "+" if total_delta >= 0 else ""
trip_sign   = "+" if trip_change_pct >= 0 else ""
share_color = "positive" if new_market_share >= 18 else "negative"

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <h2 class="{delta_color}">{delta_sign}${total_delta/1e6:.2f}M</h2>
        <p>Total Revenue Delta</p>
    </div>""", unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <h2 class="{'positive' if trip_change_pct >= 0 else 'negative'}">{trip_sign}{trip_change_pct:.1f}%</h2>
        <p>Total Trip Change</p>
    </div>""", unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-card">
        <h2 class="{share_color}">{new_market_share:.1f}%</h2>
        <p>Est. New Market Share<br><small style="opacity:0.7">(baseline 18%)</small></p>
    </div>""", unsafe_allow_html=True)

with m4:
    constraint_color = "#FFB800" if (n_capped + n_floored) > 0 else "#06C167"
    st.markdown(f"""
    <div class="metric-card">
        <h2 style="color:{constraint_color};">{n_capped} cap / {n_floored} floor</h2>
        <p>Merchants at Fee Bounds<br><small style="opacity:0.7">(30% cap · 10% floor)</small></p>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─── CHART 1: WATERFALL ──────────────────────────────────────────────────────
st.markdown("### Revenue Waterfall by Tier")

tier_deltas = sim.groupby('Tier')['Revenue Delta'].sum()
total_curr  = sim['Current Revenue'].sum()

fig_wf = go.Figure(go.Waterfall(
    orientation='v',
    measure=['absolute', 'relative', 'relative', 'relative', 'relative', 'total'],
    x=['Current\nRevenue', 'S-tier\nImpact', 'A-tier\nImpact',
       'B-tier\nImpact', 'C-tier\nImpact', 'New\nRevenue'],
    y=[
        total_curr,
        tier_deltas.get('S', 0),
        tier_deltas.get('A', 0),
        tier_deltas.get('B', 0),
        tier_deltas.get('C', 0),
        total_curr + total_delta,
    ],
    text=[f"${v/1e6:.2f}M" for v in [
        total_curr,
        tier_deltas.get('S', 0),
        tier_deltas.get('A', 0),
        tier_deltas.get('B', 0),
        tier_deltas.get('C', 0),
        total_curr + total_delta,
    ]],
    textposition='outside',
    increasing={'marker': {'color': '#06C167'}},
    decreasing={'marker': {'color': '#e74c3c'}},
    totals={'marker': {'color': '#3498db'}},
    connector={'line': {'color': '#bbb', 'dash': 'dot'}},
))

fig_wf.update_layout(
    title='Revenue Impact Path: Current → New (by tier)',
    yaxis=dict(title='Revenue ($)', gridcolor='#e0e0e0', tickformat='$,.0f'),
    height=430,
    plot_bgcolor='white',
    paper_bgcolor='white',
    showlegend=False,
)

st.plotly_chart(fig_wf, use_container_width=True, config={'displayModeBar': False})

# ─── CHART 2: GROUPED BAR ────────────────────────────────────────────────────
st.markdown("### Current vs New Revenue by Tier")

tier_rev = sim.groupby('Tier').agg(
    Current=('Current Revenue', 'sum'),
    New=('New Revenue', 'sum')
).reindex(['S', 'A', 'B', 'C'])

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    name='Current Revenue', x=tier_rev.index, y=tier_rev['Current'],
    marker_color='#95a5a6',
    text=[f"${v/1e6:.1f}M" for v in tier_rev['Current']],
    textposition='outside',
))
fig_bar.add_trace(go.Bar(
    name='New Revenue', x=tier_rev.index, y=tier_rev['New'],
    marker_color='#06C167',
    text=[f"${v/1e6:.1f}M" for v in tier_rev['New']],
    textposition='outside',
))

fig_bar.update_layout(
    barmode='group',
    title='Revenue by Tier: Current vs Simulated',
    xaxis_title='Tier', yaxis_title='Total Revenue ($)',
    height=400,
    plot_bgcolor='white', paper_bgcolor='white',
    yaxis=dict(gridcolor='#e0e0e0', tickformat='$,.0f'),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
)

st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# ─── CHART 3: SCATTER ────────────────────────────────────────────────────────
st.markdown("### Current Fee vs Proposed Fee")

tier_color_map = {'S': '#048A46', 'A': '#06C167', 'B': '#FF8F00', 'C': '#E53935'}
fee_min = sim['Marketplace Fee'].min() * 0.95
fee_max = max(sim['Marketplace Fee'].max(), sim['New Fee'].max()) * 1.05

fig_sc = go.Figure()

# No-change reference line
fig_sc.add_trace(go.Scatter(
    x=[fee_min, fee_max], y=[fee_min, fee_max],
    mode='lines', line=dict(color='#aaa', dash='dash', width=1.5),
    name='No change', hoverinfo='skip'
))

max_trips = sim['Annualized Trips'].max()
for tier in ['S', 'A', 'B', 'C']:
    t = sim[sim['Tier'] == tier]
    fig_sc.add_trace(go.Scatter(
        x=t['Marketplace Fee'], y=t['New Fee'],
        mode='markers', name=f'Tier {tier}',
        marker=dict(
            color=tier_color_map[tier],
            size=(t['Annualized Trips'] / max_trips * 30 + 6),
            opacity=0.8, line=dict(width=1, color='white')
        ),
        text=t['Brand Name'],
        customdata=t[['Fee Change', 'Annualized Trips']].values,
        hovertemplate=(
            '<b>%{text}</b><br>Current Fee: %{x:.1%}<br>'
            'New Fee: %{y:.1%}<br>Change: %{customdata[0]:+.1f}pp<br>'
            'Trips: %{customdata[1]:,.0f}<extra></extra>'
        )
    ))

fig_sc.add_annotation(
    xref='paper', yref='paper', x=0.98, y=0.95,
    text="Above line = fee increase ↑",
    showarrow=False, font=dict(size=11, color='#e74c3c'), xanchor='right'
)
fig_sc.add_annotation(
    xref='paper', yref='paper', x=0.98, y=0.88,
    text="Below line = fee decrease ↓",
    showarrow=False, font=dict(size=11, color='#06C167'), xanchor='right'
)

fig_sc.update_layout(
    title='Current Fee vs Proposed Fee (bubble size = annual trips)',
    xaxis=dict(title='Current Marketplace Fee', tickformat='.1%', gridcolor='#e0e0e0'),
    yaxis=dict(title='Proposed Fee', tickformat='.1%', gridcolor='#e0e0e0'),
    height=500,
    plot_bgcolor='white', paper_bgcolor='white',
    legend=dict(title='Tier'),
)

st.plotly_chart(fig_sc, use_container_width=True,
                config={'displayModeBar': True, 'displaylogo': False})

# ─── DETAIL TABLE ────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📋 All 200 Merchants — Full Detail", expanded=False):

    detail = sim.copy().sort_values('Revenue Delta', ascending=False)

    display = pd.DataFrame({
        'Brand Name':     detail['Brand Name'],
        'Segment':        detail['Segment'],
        'Tier':           detail['Tier'],
        'Curr Fee':       detail['Marketplace Fee'].apply(lambda x: f"{x:.1%}"),
        'New Fee':        detail['New Fee'].apply(lambda x: f"{x:.1%}"),
        'Fee Change':     detail['Fee Change'].apply(lambda x: f"{x:+.1f}pp"),
        'Curr Trips':     detail['Annualized Trips'].apply(lambda x: f"{x:,.0f}"),
        'New Trips':      detail['New Trips'].apply(lambda x: f"{x:,.0f}"),
        'Curr Revenue':   detail['Current Revenue'].apply(lambda x: f"${x:,.0f}"),
        'New Revenue':    detail['New Revenue'].apply(lambda x: f"${x:,.0f}"),
        'Revenue Delta':  detail['Revenue Delta'].apply(lambda x: f"${x:+,.0f}"),
        'Dir':            detail['Fee Direction'],
    })

    st.caption("Sorted by Revenue Delta (largest gain first)")
    st.dataframe(display, use_container_width=True, hide_index=True, height=420)

    st.download_button(
        label="📥 Download CSV",
        data=sim[[
            'Brand Name', 'Segment', 'Tier',
            'Marketplace Fee', 'New Fee', 'Fee Change',
            'Annualized Trips', 'New Trips',
            'Current Revenue', 'New Revenue', 'Revenue Delta', 'Fee Direction'
        ]].to_csv(index=False),
        file_name="fee_simulator_detail.csv",
        mime="text/csv"
    )
