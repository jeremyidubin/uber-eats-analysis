import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import load_restaurant_data
from utils.scoring import calculate_total_score
from utils.ui import render_header, render_sidebar, kpi_card, GREEN, RED, AMBER, DARK
from utils.simulation import run_simulation, SS_DEFAULTS

st.set_page_config(page_title="Fee Simulator", page_icon=None, layout="wide")
render_header()
render_sidebar()

TIER_COLORS = {'S': '#06C167', 'A': '#34A853', 'B': '#F9A825', 'C': '#D32F2F'}

# ─── Data ────────────────────────────────────────────────────────────────────
df_raw = load_restaurant_data()
if df_raw.empty:
    st.error("Unable to load data.")
    st.stop()

df = calculate_total_score(df_raw)

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("Fee Simulator")
st.markdown(
    "<p style='color:#757575; font-size:14px; margin-bottom:1.5rem;'>"
    "Simulate tiered fee adjustments and Feed placement volume lifts. "
    "Fee changes are relative to each merchant's current rate. "
    "Volume changes reflect Feed algorithm shifts, not fee elasticity.</p>",
    unsafe_allow_html=True,
)

# ─── Sliders ─────────────────────────────────────────────────────────────────
reset_col, _ = st.columns([1, 5])
with reset_col:
    if st.button("Reset to defaults", use_container_width=True):
        for k in SS_DEFAULTS:
            st.session_state.pop(k, None)
        st.rerun()

st.markdown(
    "<p style='font-size:13px; font-weight:500; color:#1A1A1A; margin:0.5rem 0 0.3rem 0;'>"
    "Fee adjustments by tier (percentage points, relative to current fee)</p>",
    unsafe_allow_html=True,
)
fc1, fc2, fc3, fc4 = st.columns(4)

with fc1:
    st.markdown("<p style='font-size:13px; font-weight:600; color:#06C167; margin:0;'>S-tier — top 10</p>", unsafe_allow_html=True)
    st.slider("S-tier fee change (%pt)", min_value=-5.0, max_value=5.0, step=0.1,
              value=SS_DEFAULTS['s_fee_change'], key='s_fee_change', format="%g%%",
              help="Default: −2pp")
with fc2:
    st.markdown("<p style='font-size:13px; font-weight:600; color:#34A853; margin:0;'>A-tier — rank 11–50</p>", unsafe_allow_html=True)
    st.slider("A-tier fee change (%pt)", min_value=-5.0, max_value=5.0, step=0.1,
              value=SS_DEFAULTS['a_fee_change'], key='a_fee_change', format="%g%%",
              help="Default: −0.5pp")
with fc3:
    st.markdown("<p style='font-size:13px; font-weight:600; color:#F9A825; margin:0;'>B-tier — rank 51–150</p>", unsafe_allow_html=True)
    st.slider("B-tier fee change (%pt)", min_value=-5.0, max_value=5.0, step=0.1,
              value=SS_DEFAULTS['b_fee_change'], key='b_fee_change', format="%g%%",
              help="Default: +2pp")
with fc4:
    st.markdown("<p style='font-size:13px; font-weight:600; color:#D32F2F; margin:0;'>C-tier — rank 151–200</p>", unsafe_allow_html=True)
    st.slider("C-tier fee change (%pt)", min_value=-5.0, max_value=5.0, step=0.1,
              value=SS_DEFAULTS['c_fee_change'], key='c_fee_change', format="%g%%",
              help="Default: +3pp")

st.markdown(
    "<p style='font-size:13px; font-weight:500; color:#1A1A1A; margin:0.8rem 0 0.3rem 0;'>"
    "Volume assumptions by tier (Feed placement effect)</p>",
    unsafe_allow_html=True,
)
vc1, vc2, vc3, vc4 = st.columns(4)

with vc1:
    st.slider("S-tier volume change (%)", min_value=-40.0, max_value=40.0, step=1.0,
              value=SS_DEFAULTS['s_volume'], key='s_volume', format="%g%%",
              help="Default: +20%")
with vc2:
    st.slider("A-tier volume change (%)", min_value=-40.0, max_value=40.0, step=1.0,
              value=SS_DEFAULTS['a_volume'], key='a_volume', format="%g%%",
              help="Default: +10%")
with vc3:
    st.slider("B-tier volume change (%)", min_value=-40.0, max_value=40.0, step=1.0,
              value=SS_DEFAULTS['b_volume'], key='b_volume', format="%g%%",
              help="Default: −5%")
with vc4:
    st.slider("C-tier volume change (%)", min_value=-40.0, max_value=40.0, step=1.0,
              value=SS_DEFAULTS['c_volume'], key='c_volume', format="%g%%",
              help="Default: −15%")

st.markdown("---")

# ─── Simulation ──────────────────────────────────────────────────────────────
sim, tier_fee, tier_vol = run_simulation(df)

sim['Current Revenue'] = sim['Curr Rev']
sim['Revenue Delta']   = sim['Rev Delta']
sim['New Revenue']     = sim['New Rev']
sim['Fee Change']      = sim['Fee Chg pp']
sim['Fee Direction']   = sim['Fee Dir']

total_delta      = sim['Revenue Delta'].sum()
total_curr_trips = sim['Annualized Trips'].sum()
total_new_trips  = sim['New Trips'].sum()
trip_change_pct  = (total_new_trips - total_curr_trips) / total_curr_trips * 100
new_market_share = 0.18 * (1 + trip_change_pct / 100) * 100
n_capped  = int(sim['Fee Capped'].sum())
n_floored = int(sim['Fee Floored'].sum())

# Fee cap/floor warnings
if n_capped > 0:
    st.warning(
        f"**{n_capped} merchant{'s' if n_capped > 1 else ''} capped at 30% maximum fee** — "
        "fee increase truncated to stay within the case study limit."
    )
if n_floored > 0:
    st.warning(
        f"**{n_floored} merchant{'s' if n_floored > 1 else ''} floored at 10% minimum fee** — "
        "fee decrease truncated to stay within the case study limit."
    )

# ─── Impact Summary ───────────────────────────────────────────────────────────
st.markdown("### Impact Summary")

m1, m2, m3, m4 = st.columns(4)

d_sign  = "+" if total_delta >= 0 else ""
t_sign  = "+" if trip_change_pct >= 0 else ""
d_color = GREEN if total_delta >= 0 else RED
t_color = GREEN if trip_change_pct >= 0 else RED
s_color = GREEN if new_market_share >= 18 else AMBER
c_color = AMBER if (n_capped + n_floored) > 0 else GREEN

kpi_card(m1, f"{d_sign}${total_delta/1e6:.2f}M", "Total revenue delta",         accent=d_color)
kpi_card(m2, f"{t_sign}{trip_change_pct:.2f}%",   "Total trip change",           accent=t_color)
kpi_card(m3, f"{new_market_share:.1f}%",           "Est. market share (base 18%)", accent=s_color)
kpi_card(m4, f"{n_capped} cap / {n_floored} floor","Merchants at fee bounds",     accent=c_color)

st.markdown("---")

# ─── Waterfall Chart ──────────────────────────────────────────────────────────
st.markdown("### Revenue Waterfall by Tier")

tier_deltas = sim.groupby('Tier')['Revenue Delta'].sum()
total_curr  = sim['Current Revenue'].sum()

fig_wf = go.Figure(go.Waterfall(
    orientation='v',
    measure=['absolute', 'relative', 'relative', 'relative', 'relative', 'total'],
    x=['Current\nRevenue', 'S-tier', 'A-tier', 'B-tier', 'C-tier', 'New\nRevenue'],
    y=[
        total_curr,
        tier_deltas.get('S', 0), tier_deltas.get('A', 0),
        tier_deltas.get('B', 0), tier_deltas.get('C', 0),
        total_curr + total_delta,
    ],
    text=[f"${v/1e6:.2f}M" for v in [
        total_curr,
        tier_deltas.get('S', 0), tier_deltas.get('A', 0),
        tier_deltas.get('B', 0), tier_deltas.get('C', 0),
        total_curr + total_delta,
    ]],
    textposition='outside',
    increasing={'marker': {'color': GREEN}},
    decreasing={'marker': {'color': RED}},
    totals={'marker': {'color': DARK}},
    connector={'line': {'color': '#BDBDBD', 'dash': 'dot'}},
))

fig_wf.update_layout(
    yaxis=dict(title='Revenue ($)', gridcolor='#E0E0E0', griddash='dot', tickformat='$,.0f'),
    height=420,
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif', size=12, color=DARK),
    showlegend=False,
    margin=dict(t=10, b=40, l=80, r=20),
)

st.plotly_chart(fig_wf, use_container_width=True, config={'displayModeBar': False})

# ─── Fee Scatter ──────────────────────────────────────────────────────────────
st.markdown("### Current Fee vs Proposed Fee")

fee_min = sim['Marketplace Fee'].min() * 0.95
fee_max = max(sim['Marketplace Fee'].max(), sim['New Fee'].max()) * 1.05

fig_sc = go.Figure()
fig_sc.add_trace(go.Scatter(
    x=[fee_min, fee_max], y=[fee_min, fee_max],
    mode='lines', line=dict(color='#BDBDBD', dash='dash', width=1.5),
    name='No change', hoverinfo='skip',
))

max_trips = sim['Annualized Trips'].max()
for tier in ['S', 'A', 'B', 'C']:
    t = sim[sim['Tier'] == tier]
    fig_sc.add_trace(go.Scatter(
        x=t['Marketplace Fee'], y=t['New Fee'],
        mode='markers', name=f'Tier {tier}',
        marker=dict(
            color=TIER_COLORS[tier],
            size=(t['Annualized Trips'] / max_trips * 30 + 6),
            opacity=0.8, line=dict(width=1, color='white'),
        ),
        text=t['Brand Name'],
        customdata=t[['Fee Change', 'Annualized Trips']].values,
        hovertemplate=(
            '<b>%{text}</b><br>Current: %{x:.1%}<br>'
            'Proposed: %{y:.1%}<br>Change: %{customdata[0]:+.1f}pp<br>'
            'Trips: %{customdata[1]:,.0f}<extra></extra>'
        ),
    ))

fig_sc.add_annotation(
    xref='paper', yref='paper', x=0.98, y=0.96,
    text="Above line = fee increase",
    showarrow=False, font=dict(size=11, color=RED), xanchor='right',
)
fig_sc.add_annotation(
    xref='paper', yref='paper', x=0.98, y=0.90,
    text="Below line = fee decrease",
    showarrow=False, font=dict(size=11, color=GREEN), xanchor='right',
)

fig_sc.update_layout(
    xaxis=dict(title='Current Marketplace Fee', tickformat='.1%', gridcolor='#E0E0E0', griddash='dot'),
    yaxis=dict(title='Proposed Fee', tickformat='.1%', gridcolor='#E0E0E0', griddash='dot'),
    height=480,
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif', size=12, color=DARK),
    legend=dict(title='Tier'),
    margin=dict(t=10, b=40, l=80, r=20),
)

st.plotly_chart(fig_sc, use_container_width=True, config={
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines'],
})
st.caption("Bubble size reflects annualized trip volume. Double-click to reset zoom.")

# ─── Detail Table ─────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("All 200 merchants — detail table"):

    detail = sim.copy().sort_values('Revenue Delta', ascending=False)

    display = pd.DataFrame({
        'Brand Name':    detail['Brand Name'],
        'Segment':       detail['Segment'],
        'Tier':          detail['Tier'],
        'Curr Fee':      detail['Marketplace Fee'].apply(lambda x: f"{x:.1%}"),
        'New Fee':       detail['New Fee'].apply(lambda x: f"{x:.1%}"),
        'Fee Change':    detail['Fee Change'].apply(lambda x: f"{x:+.1f}pp"),
        'Curr Trips':    detail['Annualized Trips'].apply(lambda x: f"{x:,.0f}"),
        'New Trips':     detail['New Trips'].apply(lambda x: f"{x:,.0f}"),
        'Curr Revenue':  detail['Current Revenue'].apply(lambda x: f"${x:,.0f}"),
        'New Revenue':   detail['New Revenue'].apply(lambda x: f"${x:,.0f}"),
        'Rev Delta':     detail['Revenue Delta'].apply(lambda x: f"${x:+,.0f}"),
        'Dir':           detail['Fee Direction'],
    })

    st.caption("Sorted by Revenue Delta — largest gain first")
    st.dataframe(display, use_container_width=True, hide_index=True, height=420)

    st.download_button(
        label="Download CSV",
        data=sim[[
            'Brand Name', 'Segment', 'Tier',
            'Marketplace Fee', 'New Fee', 'Fee Change',
            'Annualized Trips', 'New Trips',
            'Current Revenue', 'New Revenue', 'Revenue Delta', 'Fee Direction',
        ]].to_csv(index=False),
        file_name="fee_simulator_detail.csv",
        mime="text/csv",
    )
