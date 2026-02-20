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
from utils.simulation import run_simulation, is_at_defaults

st.set_page_config(page_title="Revenue Impact", page_icon=None, layout="wide")
render_header()
render_sidebar()

TIER_COLORS = {'S': '#06C167', 'A': '#34A853', 'B': '#F9A825', 'C': '#D32F2F'}

# ─── Data & Simulation ────────────────────────────────────────────────────────
df_raw = load_restaurant_data()
if df_raw.empty:
    st.error("Unable to load data.")
    st.stop()

df = calculate_total_score(df_raw)
sim, tier_fee, tier_vol = run_simulation(df)

total_curr   = sim['Curr Rev'].sum()
total_new    = sim['New Rev'].sum()
total_delta  = sim['Rev Delta'].sum()
curr_trips   = sim['Annualized Trips'].sum()
new_trips    = sim['New Trips'].sum()
trip_chg_pct = (new_trips - curr_trips) / curr_trips * 100
new_mkt_share = 0.18 * (1 + trip_chg_pct / 100) * 100
n_capped     = int(sim['Fee Capped'].sum())
n_floored    = int(sim['Fee Floored'].sum())

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("Revenue Impact")
st.markdown(
    "<p style='color:#757575; font-size:14px; margin-bottom:1.5rem;'>"
    "End-to-end view of the tiered fee strategy — revenue gain, where it comes from, "
    "and which merchants drive the outcome. Figures reflect current Fee Simulator settings.</p>",
    unsafe_allow_html=True,
)

if is_at_defaults():
    st.info("Showing default scenario (S: −2pp, A: −0.5pp, B: +2pp, C: +3pp). "
            "Adjust on the Fee Simulator page to model alternatives.")

if n_capped > 0:
    st.warning(
        f"**{n_capped} merchant{'s' if n_capped > 1 else ''} capped at 30% maximum fee** — "
        "fee increase truncated."
    )
if n_floored > 0:
    st.warning(
        f"**{n_floored} merchant{'s' if n_floored > 1 else ''} floored at 10% minimum fee** — "
        "fee decrease truncated."
    )

st.markdown("---")

# ─── Headline Metrics ─────────────────────────────────────────────────────────
st.markdown("### Headline Impact")

c1, c2, c3, c4, c5 = st.columns(5)

sign    = "+" if total_delta >= 0 else ""
t_sign  = "+" if trip_chg_pct >= 0 else ""
d_color = GREEN if total_delta >= 0 else RED
t_color = GREEN if trip_chg_pct >= 0 else RED
s_color = GREEN if new_mkt_share >= 18 else AMBER

kpi_card(c1, f"{sign}${total_delta/1e6:.2f}M",  "Total revenue delta",          accent=d_color)
kpi_card(c2, f"${total_new/1e6:.1f}M",           "Projected total revenue")
kpi_card(c3, f"{t_sign}{trip_chg_pct:.1f}%",     "Trip volume change",           accent=t_color)
kpi_card(c4, f"{new_mkt_share:.1f}%",             "Est. market share (base 18%)", accent=s_color)
kpi_card(c5, f"${total_curr/1e6:.1f}M",           "Current total revenue",        accent='#BDBDBD')

st.markdown("")
st.markdown("---")

# ─── Revenue by Tier ──────────────────────────────────────────────────────────
tier_rev = sim.groupby('Tier').agg(
    Curr=('Curr Rev', 'sum'),
    New=('New Rev', 'sum'),
    Delta=('Rev Delta', 'sum'),
).reindex(['S', 'A', 'B', 'C'])

st.markdown("### Revenue by Tier")

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    name='Current', x=tier_rev.index, y=tier_rev['Curr'],
    marker_color='#BDBDBD',
    text=[f"${v/1e6:.1f}M" for v in tier_rev['Curr']],
    textposition='outside',
))
fig_bar.add_trace(go.Bar(
    name='Projected', x=tier_rev.index, y=tier_rev['New'],
    marker_color=[TIER_COLORS[t] for t in tier_rev.index],
    text=[f"${v/1e6:.1f}M" for v in tier_rev['New']],
    textposition='outside',
))

fig_bar.update_layout(
    barmode='group',
    xaxis_title='Tier',
    yaxis=dict(title='Revenue ($)', gridcolor='#E0E0E0', griddash='dot', tickformat='$,.0f'),
    height=400,
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif', size=12, color=DARK),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    margin=dict(t=10, b=40, l=80, r=20),
)
st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

st.markdown("### Delta by Tier")

fig_delta = go.Figure(go.Bar(
    x=tier_rev.index,
    y=tier_rev['Delta'],
    marker_color=[GREEN if v >= 0 else RED for v in tier_rev['Delta']],
    text=[f"${v/1e6:+.2f}M" for v in tier_rev['Delta']],
    textposition='outside',
))

fig_delta.update_layout(
    xaxis_title='Tier',
    yaxis=dict(
        title='Revenue Delta ($)', gridcolor='#E0E0E0', griddash='dot',
        tickformat='$,.0f', zeroline=True, zerolinecolor='#BDBDBD', zerolinewidth=1.5,
    ),
    height=400,
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif', size=12, color=DARK),
    showlegend=False,
    margin=dict(t=10, b=40, l=80, r=20),
)
st.plotly_chart(fig_delta, use_container_width=True, config={'displayModeBar': False})

st.markdown("---")

# ─── Top / Bottom Merchants ───────────────────────────────────────────────────
top_gainers = sim.nlargest(15, 'Rev Delta')[
    ['Brand Name', 'Tier', 'Curr Rev', 'New Rev', 'Rev Delta', 'Vol Lift %', 'Fee Chg pp']
]
top_losers  = sim.nsmallest(15, 'Rev Delta')[
    ['Brand Name', 'Tier', 'Curr Rev', 'New Rev', 'Rev Delta', 'Vol Lift %', 'Fee Chg pp']
]

col_g, col_l = st.columns(2)

with col_g:
    st.markdown("### Top 15 Gainers")
    gain_max = top_gainers['Rev Delta'].max()
    fig_g = go.Figure(go.Bar(
        y=top_gainers['Brand Name'].str[:25],
        x=top_gainers['Rev Delta'],
        orientation='h',
        marker_color=GREEN,
        text=[f"${v/1e3:+.0f}K" for v in top_gainers['Rev Delta']],
        textposition='outside',
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>Delta: $%{x:,.0f}<extra></extra>',
    ))
    fig_g.update_layout(
        xaxis=dict(title='Revenue Delta ($)', gridcolor='#E0E0E0', griddash='dot',
                   tickformat='$,.0f', range=[0, gain_max * 1.30]),
        yaxis=dict(autorange='reversed'),
        height=480, plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif', size=12, color=DARK),
        showlegend=False, margin=dict(t=10, b=40, l=170, r=20),
    )
    st.plotly_chart(fig_g, use_container_width=True, config={'displayModeBar': False})

with col_l:
    st.markdown("### Top 15 Losers")
    loss_min = top_losers['Rev Delta'].min()
    fig_l = go.Figure(go.Bar(
        y=top_losers['Brand Name'].str[:25],
        x=top_losers['Rev Delta'],
        orientation='h',
        marker_color=RED,
        text=[f"${v/1e3:+.0f}K" for v in top_losers['Rev Delta']],
        textposition='outside',
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>Delta: $%{x:,.0f}<extra></extra>',
    ))
    fig_l.update_layout(
        xaxis=dict(title='Revenue Delta ($)', gridcolor='#E0E0E0', griddash='dot',
                   tickformat='$,.0f', range=[loss_min * 1.30, 0]),
        yaxis=dict(autorange='reversed'),
        height=480, plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif', size=12, color=DARK),
        showlegend=False, margin=dict(t=10, b=40, l=170, r=20),
    )
    st.plotly_chart(fig_l, use_container_width=True, config={'displayModeBar': False})

st.markdown("---")

# ─── Scatter: Rev Delta vs Volume ─────────────────────────────────────────────
st.markdown("### Revenue Delta vs Merchant Volume")

fig_sc = go.Figure()
for tier in ['S', 'A', 'B', 'C']:
    t = sim[sim['Tier'] == tier]
    fig_sc.add_trace(go.Scatter(
        x=t['Annualized Trips'],
        y=t['Rev Delta'],
        mode='markers',
        name=f'Tier {tier}',
        marker=dict(
            color=TIER_COLORS[tier],
            size=10, opacity=0.75,
            line=dict(width=1, color='white'),
        ),
        text=t['Brand Name'],
        hovertemplate='<b>%{text}</b><br>Trips: %{x:,.0f}<br>Rev Delta: $%{y:,.0f}<extra></extra>',
    ))

fig_sc.add_hline(y=0, line_dash='dash', line_color='#BDBDBD', line_width=1.5)

fig_sc.update_layout(
    xaxis=dict(title='Current Annualized Trips', gridcolor='#E0E0E0', griddash='dot', tickformat=','),
    yaxis=dict(title='Revenue Delta ($)', gridcolor='#E0E0E0', griddash='dot', tickformat='$,.0f'),
    height=440,
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif', size=12, color=DARK),
    legend=dict(title='Tier'),
    margin=dict(t=10, b=40, l=80, r=20),
)
st.caption("Double-click to reset zoom.")
st.plotly_chart(fig_sc, use_container_width=True, config={
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines'],
})

st.markdown("---")

# ─── Tier Strategy Summary ────────────────────────────────────────────────────
st.markdown("### Tier Strategy Summary")

summary_rows = []
for tier in ['S', 'A', 'B', 'C']:
    t = sim[sim['Tier'] == tier]
    summary_rows.append({
        'Tier':               tier,
        'Merchants':          len(t),
        'Fee Change':         f"{tier_fee[tier]*100:+.1f}pp",
        'Vol Assumption':     f"{tier_vol[tier]*100:+.1f}%",
        'Curr Revenue':       f"${t['Curr Rev'].sum()/1e6:.2f}M",
        'New Revenue':        f"${t['New Rev'].sum()/1e6:.2f}M",
        'Revenue Delta':      f"${t['Rev Delta'].sum()/1e6:+.2f}M",
        'Avg Delta/Merchant': f"${t['Rev Delta'].mean()/1e3:+.0f}K",
    })

st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

# ─── Download ─────────────────────────────────────────────────────────────────
st.markdown("---")
export = sim[[
    'Brand Name', 'Segment', 'Tier', 'Rank',
    'Annualized Trips', 'New Trips', 'Marketplace Fee', 'New Fee',
    'Curr Rev', 'New Rev', 'Rev Delta', 'Rev Delta %',
    'Fee Chg pp', 'Vol Lift %',
]].copy()
export.columns = [
    'Brand', 'Segment', 'Tier', 'Rank',
    'Curr Trips', 'New Trips', 'Curr Fee', 'New Fee',
    'Curr Revenue', 'New Revenue', 'Rev Delta', 'Rev Delta %',
    'Fee Chg (pp)', 'Vol Lift (%)',
]

st.download_button(
    "Download Full Revenue Impact (CSV)",
    data=export.to_csv(index=False),
    file_name="revenue_impact_dashboard.csv",
    mime="text/csv",
)
