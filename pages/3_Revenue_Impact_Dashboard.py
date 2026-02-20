import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import load_restaurant_data
from utils.scoring import calculate_total_score
from utils.ui import render_header, render_sidebar, TIER_COLORS, GREEN, DARK, RED, AMBER
from utils.simulation import run_simulation, is_at_defaults

st.set_page_config(page_title="Revenue Impact Dashboard", page_icon="📊", layout="wide")
render_header()
render_sidebar()

# ─── Constants ────────────────────────────────────────────────────────────────
TIER_COLOR_MAP = {'S': '#048A46', 'A': '#06C167', 'B': '#FF8F00', 'C': '#E53935'}

# ─── Data & simulation ────────────────────────────────────────────────────────
df_raw = load_restaurant_data()
if df_raw.empty:
    st.error("Unable to load data.")
    st.stop()

df = calculate_total_score(df_raw)

sim, tier_fee, tier_vol = run_simulation(df)

total_curr    = sim['Curr Rev'].sum()
total_new     = sim['New Rev'].sum()
total_delta   = sim['Rev Delta'].sum()
curr_trips    = sim['Annualized Trips'].sum()
new_trips     = sim['New Trips'].sum()
trip_chg_pct  = (new_trips - curr_trips) / curr_trips * 100
new_mkt_share = 0.18 * (1 + trip_chg_pct / 100) * 100
n_capped      = int(sim['Fee Capped'].sum())
n_floored     = int(sim['Fee Floored'].sum())

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("📊 Revenue Impact Dashboard")
st.markdown("""
End-to-end view of the tiered fee strategy — how much revenue we gain, where it comes from,
and which merchants drive the outcome. All figures reflect the **current Fee Simulator settings**
(edit on Page 2).
""")

if is_at_defaults():
    st.info("Showing **default scenario** (S: −2%, A: −0.5%, B: +2%, C: +3%). Adjust sliders on Page 2 to model alternatives.")

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

st.markdown("---")

# ─── SECTION 1: HEADLINE METRICS ─────────────────────────────────────────────
st.markdown("### Headline Impact")

c1, c2, c3, c4, c5 = st.columns(5)

delta_color = GREEN if total_delta >= 0 else RED
sign        = "+" if total_delta >= 0 else ""

def kpi(col, value, label, color=None):
    col.markdown(f"""
    <div style="background:linear-gradient(135deg,{DARK} 0%,#1e3a42 100%);
                border-left:5px solid {color or GREEN}; border-radius:8px;
                padding:1.1rem 1rem; text-align:center;">
        <p style="margin:0;font-size:1.6rem;font-weight:700;color:{color or GREEN};">{value}</p>
        <p style="margin:0;font-size:0.75rem;color:#9ab8c0;margin-top:3px;">{label}</p>
    </div>""", unsafe_allow_html=True)

kpi(c1, f"{sign}${total_delta/1e6:.2f}M", "Total Revenue Delta", delta_color)
kpi(c2, f"${total_new/1e6:.1f}M",          "Projected Total Revenue")
kpi(c3, f"{sign}{trip_chg_pct:.1f}%",      "Trip Volume Change",
    GREEN if trip_chg_pct >= 0 else RED)
kpi(c4, f"{new_mkt_share:.1f}%",           "Est. Market Share",
    GREEN if new_mkt_share >= 18 else AMBER)
kpi(c5, f"${total_curr/1e6:.1f}M",         "Current Total Revenue", "#9ab8c0")

st.markdown("")
st.markdown("---")

# ─── SECTION 2: REVENUE WATERFALL ────────────────────────────────────────────
st.markdown("### Revenue Waterfall")

tier_deltas = sim.groupby('Tier')['Rev Delta'].sum()
tier_labels = {
    'S': f"S-tier\n(top 10)",
    'A': f"A-tier\n(rank 11–50)",
    'B': f"B-tier\n(rank 51–150)",
    'C': f"C-tier\n(rank 151–200)",
}

fig_wf = go.Figure(go.Waterfall(
    orientation='v',
    measure=['absolute', 'relative', 'relative', 'relative', 'relative', 'total'],
    x=['Current\nRevenue',
       tier_labels['S'], tier_labels['A'],
       tier_labels['B'], tier_labels['C'],
       'Projected\nRevenue'],
    y=[
        total_curr,
        tier_deltas.get('S', 0),
        tier_deltas.get('A', 0),
        tier_deltas.get('B', 0),
        tier_deltas.get('C', 0),
        total_new,
    ],
    text=[
        f"${total_curr/1e6:.2f}M",
        f"{'+' if tier_deltas.get('S',0)>=0 else ''}${tier_deltas.get('S',0)/1e6:.2f}M",
        f"{'+' if tier_deltas.get('A',0)>=0 else ''}${tier_deltas.get('A',0)/1e6:.2f}M",
        f"{'+' if tier_deltas.get('B',0)>=0 else ''}${tier_deltas.get('B',0)/1e6:.2f}M",
        f"{'+' if tier_deltas.get('C',0)>=0 else ''}${tier_deltas.get('C',0)/1e6:.2f}M",
        f"${total_new/1e6:.2f}M",
    ],
    textposition='outside',
    increasing={'marker': {'color': GREEN}},
    decreasing={'marker': {'color': RED}},
    totals={'marker': {'color': '#3498db'}},
    connector={'line': {'color': '#ccc', 'dash': 'dot'}},
))

fig_wf.update_layout(
    title='Revenue Path: Current → Projected (by tier contribution)',
    yaxis=dict(title='Revenue ($)', gridcolor='#e0e0e0', tickformat='$,.0f'),
    height=440,
    plot_bgcolor='white', paper_bgcolor='white',
    showlegend=False,
    margin=dict(t=50, b=40)
)

st.plotly_chart(fig_wf, use_container_width=True, config={'displayModeBar': False})

# ─── SECTION 3: TIER COMPARISON ──────────────────────────────────────────────
tier_rev = sim.groupby('Tier').agg(
    Curr=('Curr Rev', 'sum'),
    New=('New Rev', 'sum'),
    Delta=('Rev Delta', 'sum')
).reindex(['S', 'A', 'B', 'C'])

st.markdown("### Revenue by Tier: Before vs After")

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    name='Current', x=tier_rev.index, y=tier_rev['Curr'],
    marker_color='#95a5a6',
    text=[f"${v/1e6:.1f}M" for v in tier_rev['Curr']],
    textposition='outside',
))
fig_bar.add_trace(go.Bar(
    name='Projected', x=tier_rev.index, y=tier_rev['New'],
    marker_color=[TIER_COLOR_MAP[t] for t in tier_rev.index],
    text=[f"${v/1e6:.1f}M" for v in tier_rev['New']],
    textposition='outside',
))

fig_bar.update_layout(
    barmode='group',
    xaxis_title='Tier', yaxis_title='Revenue ($)',
    height=420,
    plot_bgcolor='white', paper_bgcolor='white',
    yaxis=dict(gridcolor='#e0e0e0', tickformat='$,.0f'),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    margin=dict(t=40, b=40, l=60, r=40),
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
    xaxis_title='Tier', yaxis_title='Revenue Delta ($)',
    height=420,
    plot_bgcolor='white', paper_bgcolor='white',
    yaxis=dict(gridcolor='#e0e0e0', tickformat='$,.0f', zeroline=True,
               zerolinecolor='#aaa', zerolinewidth=1.5),
    showlegend=False,
    margin=dict(t=40, b=40, l=60, r=40),
)
st.plotly_chart(fig_delta, use_container_width=True, config={'displayModeBar': False})

st.markdown("---")

# ─── SECTION 4: TOP/BOTTOM MERCHANTS ─────────────────────────────────────────
col_g, col_l2 = st.columns(2)

top_gainers = sim.nlargest(15, 'Rev Delta')[['Brand Name','Tier','Curr Rev','New Rev','Rev Delta','Vol Lift %','Fee Chg pp']]
top_losers  = sim.nsmallest(15, 'Rev Delta')[['Brand Name','Tier','Curr Rev','New Rev','Rev Delta','Vol Lift %','Fee Chg pp']]

with col_g:
    st.markdown("### Top 15 Revenue Gainers")

    fig_g = go.Figure(go.Bar(
        y=top_gainers['Brand Name'].str[:22],
        x=top_gainers['Rev Delta'],
        orientation='h',
        marker_color=GREEN,
        text=[f"${v/1e3:+.0f}K" for v in top_gainers['Rev Delta']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Delta: $%{x:,.0f}<extra></extra>'
    ))
    fig_g.update_layout(
        xaxis=dict(title='Revenue Delta ($)', gridcolor='#e0e0e0', tickformat='$,.0f'),
        yaxis=dict(autorange='reversed'),
        height=480, plot_bgcolor='white', paper_bgcolor='white',
        showlegend=False, margin=dict(l=150)
    )
    st.plotly_chart(fig_g, use_container_width=True, config={'displayModeBar': False})

with col_l2:
    st.markdown("### Top 15 Revenue Losers")

    fig_l = go.Figure(go.Bar(
        y=top_losers['Brand Name'].str[:22],
        x=top_losers['Rev Delta'],
        orientation='h',
        marker_color=RED,
        text=[f"${v/1e3:+.0f}K" for v in top_losers['Rev Delta']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Delta: $%{x:,.0f}<extra></extra>'
    ))
    fig_l.update_layout(
        xaxis=dict(title='Revenue Delta ($)', gridcolor='#e0e0e0', tickformat='$,.0f'),
        yaxis=dict(autorange='reversed'),
        height=480, plot_bgcolor='white', paper_bgcolor='white',
        showlegend=False, margin=dict(l=150)
    )
    st.plotly_chart(fig_l, use_container_width=True, config={'displayModeBar': False})

st.markdown("---")

# ─── SECTION 5: SCATTER — Rev Delta vs Volume ─────────────────────────────────
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
            color=TIER_COLOR_MAP[tier],
            size=10, opacity=0.75,
            line=dict(width=1, color='white')
        ),
        text=t['Brand Name'],
        hovertemplate='<b>%{text}</b><br>Trips: %{x:,.0f}<br>Rev Delta: $%{y:,.0f}<extra></extra>'
    ))

fig_sc.add_hline(y=0, line_dash='dash', line_color='#aaa', line_width=1.5)

fig_sc.update_layout(
    xaxis=dict(title='Current Annualized Trips', gridcolor='#e0e0e0', tickformat=','),
    yaxis=dict(title='Revenue Delta ($)', gridcolor='#e0e0e0', tickformat='$,.0f',
               zeroline=False),
    height=450,
    plot_bgcolor='white', paper_bgcolor='white',
    legend=dict(title='Tier'),
    title='Revenue Delta by Merchant Volume (above line = gainer, below = loser)',
)
st.plotly_chart(fig_sc, use_container_width=True, config={'displayModeBar': True, 'displaylogo': False})

st.markdown("---")

# ─── SECTION 6: TIER SUMMARY TABLE ───────────────────────────────────────────
st.markdown("### Tier Strategy Summary")

summary_rows = []
for tier in ['S', 'A', 'B', 'C']:
    t = sim[sim['Tier'] == tier]
    fee_adj = tier_fee[tier] * 100
    vol_adj = tier_vol[tier] * 100
    summary_rows.append({
        'Tier':            tier,
        'Merchants':       len(t),
        'Fee Change':      f"{fee_adj:+.1f}pp",
        'Vol Assumption':  f"{vol_adj:+.1f}%",
        'Curr Revenue':    f"${t['Curr Rev'].sum()/1e6:.2f}M",
        'New Revenue':     f"${t['New Rev'].sum()/1e6:.2f}M",
        'Revenue Delta':   f"${t['Rev Delta'].sum()/1e6:+.2f}M",
        'Avg Delta/Merchant': f"${t['Rev Delta'].mean()/1e3:+.0f}K",
    })

summary_df = pd.DataFrame(summary_rows)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ─── DOWNLOAD ─────────────────────────────────────────────────────────────────
st.markdown("---")
export = sim[['Brand Name','Segment','Tier','Rank',
              'Annualized Trips','New Trips','Marketplace Fee','New Fee',
              'Curr Rev','New Rev','Rev Delta','Rev Delta %',
              'Fee Chg pp','Vol Lift %']].copy()
export.columns = ['Brand','Segment','Tier','Rank',
                  'Curr Trips','New Trips','Curr Fee','New Fee',
                  'Curr Revenue','New Revenue','Rev Delta','Rev Delta %',
                  'Fee Chg (pp)','Vol Lift (%)']

st.download_button(
    "📥 Download Full Revenue Impact (CSV)",
    data=export.to_csv(index=False),
    file_name="revenue_impact_dashboard.csv",
    mime="text/csv"
)
