import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.ui import render_header, render_sidebar, GREEN, DARK, RED

st.set_page_config(page_title="Methodology", page_icon=None, layout="wide")
render_header()
render_sidebar()

st.title("Methodology")
st.markdown(
    "<p style='color:#757575; font-size:14px; margin-bottom:1.5rem;'>"
    "What's in the model, what's out, and why.</p>",
    unsafe_allow_html=True,
)

# ─── Guiding Principles ───────────────────────────────────────────────────────
st.markdown("## Scoring Model")

principles = [
    ("Each input answers one question",
     "Volume: do they drive orders? Quality: is the experience good? "
     "Economics: do we make money per order? If an input doesn't answer "
     "one of those three questions cleanly, it doesn't belong in the model."),
    ("No ambiguous signals",
     "Every input has a clear direction. If you can argue it both ways, "
     "it's out. Ambiguous signals add noise and make the model harder to "
     "defend in a business review."),
    ("Don't score what you're about to change",
     "Fees are set in Phase 3 (the Fee Simulator). Scoring merchants on fee "
     "rate alone would be circular — we'd reward merchants for having a high "
     "fee, then turn around and reduce it. Fee is captured legitimately via "
     "Basket × Fee (i.e., revenue per order)."),
    ("One job per data point",
     "Active Locations define the Enterprise / SMB segment threshold. "
     "Using them in scoring would double-count — we'd reward large merchants "
     "just for being large, independent of quality or economics."),
    ("Simple model, smart strategy",
     "Three inputs rank merchants. Everything else — First-Time Eater %, "
     "franchising, location activation — shapes how we act on those rankings "
     "(Feed allocation, account management, expansion planning). "
     "Complexity belongs in the strategy, not the scoring."),
]

for title, body in principles:
    st.markdown(
        f"<div style='background:#FAFAFA; border:1px solid #E0E0E0; border-left:3px solid {GREEN};"
        f"padding:1rem 1.2rem; border-radius:4px; margin-bottom:0.6rem;'>"
        f"<p style='margin:0 0 4px 0; font-weight:600; color:{DARK}; font-size:14px;'>{title}</p>"
        f"<p style='margin:0; color:#555; font-size:13px; line-height:1.6;'>{body}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ─── In vs Out ────────────────────────────────────────────────────────────────
st.markdown("## What's In vs Out")

col_in, col_out = st.columns(2)

with col_in:
    st.markdown(
        f"<p style='font-weight:600; font-size:14px; color:{GREEN}; "
        f"border-bottom:2px solid {GREEN}; padding-bottom:4px; margin-bottom:0.8rem;'>"
        f"In the Model</p>",
        unsafe_allow_html=True,
    )
    inputs = [
        ("Volume — 35 pts",       "Annualized Trips",
         "Proven consumer demand — the most direct signal of merchant importance."),
        ("Ops Quality — 30 pts",  "Wait Time (18 pts) + Defect Rate (12 pts)",
         "Low wait + low defects → better retention and repeat orders."),
        ("Economics — 35 pts",    "Basket Size × Marketplace Fee",
         "Revenue per order. Captures fee level without making scoring circular."),
    ]
    for label, metric, reason in inputs:
        st.markdown(
            f"<div style='background:#FAFAFA; border:1px solid #E0E0E0; border-left:3px solid {GREEN};"
            f"padding:0.8rem 1rem; border-radius:4px; margin-bottom:0.6rem;'>"
            f"<p style='margin:0; font-weight:600; font-size:13px; color:{DARK};'>{label}</p>"
            f"<p style='margin:2px 0; font-size:12px; color:#757575;'>{metric}</p>"
            f"<p style='margin:0; font-size:13px; color:#555;'>{reason}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

with col_out:
    st.markdown(
        f"<p style='font-weight:600; font-size:14px; color:{RED}; "
        f"border-bottom:2px solid {RED}; padding-bottom:4px; margin-bottom:0.8rem;'>"
        f"Excluded</p>",
        unsafe_allow_html=True,
    )
    exclusions = [
        ("First-Time Eater %",       "Ambiguous signal",
         "High % could mean rapid growth or high churn. Direction is unclear."),
        ("Location Activation Rate", "Backwards logic",
         "Low activation is a growth opportunity or an operational failure — ambiguous."),
        ("% Franchised",             "No directional signal",
         "Franchised doesn't mean better or worse; it means different account management."),
        ("Fee Rate alone",           "Circular",
         "We're about to set fees. Scoring on fee rate creates a circular dependency."),
    ]
    for label, reason_short, reason in exclusions:
        st.markdown(
            f"<div style='background:#FAFAFA; border:1px solid #E0E0E0; border-left:3px solid {RED};"
            f"padding:0.8rem 1rem; border-radius:4px; margin-bottom:0.6rem;'>"
            f"<p style='margin:0; font-weight:600; font-size:13px; color:{DARK};'>{label}</p>"
            f"<p style='margin:2px 0; font-size:12px; color:{RED};'>{reason_short}</p>"
            f"<p style='margin:0; font-size:13px; color:#555;'>{reason}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("---")

# ─── Fee Simulator Assumptions ────────────────────────────────────────────────
st.markdown("## Fee Simulator Assumptions")

assumptions = [
    ("Volume changes are tied to Feed promotion, not fee elasticity",
     "The simulator models what happens when we change Feed ranking — top-tier merchants get "
     "more prominent placement and more orders. The fee adjustment is a separate, simultaneous lever."),
    ("Fee reductions don't directly increase orders",
     "Eaters don't see the marketplace fee — it's a B2B rate between Uber Eats and the restaurant. "
     "Volume lifts come from Feed placement changes, not fee changes."),
    ("Fee increases have minimal volume impact",
     "Because eaters never see the marketplace fee, a 2pp fee increase to a C-tier merchant "
     "does not cause eaters to order less. The volume impact comes from Feed deprioritization."),
    ("Asymmetric volume effects (intentional)",
     "Feed promotion lift for S/A tier is larger in magnitude than deprioritization loss for B/C tier. "
     "Promoting the best merchants drives outsized gains relative to the modest losses from "
     "deprioritizing weaker performers."),
]

for title, body in assumptions:
    st.markdown(
        f"<div style='background:#FAFAFA; border:1px solid #E0E0E0; border-left:3px solid #E0E0E0;"
        f"padding:1rem 1.2rem; border-radius:4px; margin-bottom:0.6rem;'>"
        f"<p style='margin:0 0 4px 0; font-weight:600; color:{DARK}; font-size:14px;'>{title}</p>"
        f"<p style='margin:0; color:#555; font-size:13px; line-height:1.6;'>{body}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ─── Data Notes ───────────────────────────────────────────────────────────────
st.markdown("## Data Notes")

notes = [
    ("Dataset",
     "200 restaurant brands in U-City, from the 2026 Business Case dataset."),
    ("Enterprise definition",
     "Active Locations ≥ 20 → Enterprise. Below 20 → SMB."),
    ("PERCENTRANK scoring",
     "Percentile ranking is used instead of min-max normalization to handle the heavily "
     "right-skewed trip distribution. Min-max would compress most merchants near zero."),
    ("Market share formula",
     "Estimated new share = 18% × (1 + trip growth %). The 18% is the stated current U-City market share."),
    ("Revenue figures",
     "Estimated annual revenue = Annualized Trips × Avg. Basket Size × Marketplace Fee. "
     "This is Uber Eats take-rate revenue, not restaurant gross revenue."),
    ("Tier boundaries",
     "S: rank 1–10 · A: rank 11–50 · B: rank 51–150 · C: rank 151–200. "
     "Rank-based, not score-threshold-based — exactly 10 S-tier merchants always."),
]

for label, note in notes:
    col_l, col_r = st.columns([1, 4])
    with col_l:
        st.markdown(f"**{label}**")
    with col_r:
        st.markdown(f"<p style='font-size:13px; color:#555; margin:0;'>{note}</p>",
                    unsafe_allow_html=True)
    st.markdown("<hr style='margin:0.5rem 0; border-color:#E0E0E0;'>", unsafe_allow_html=True)

st.markdown("---")

# ─── Formula Reference ────────────────────────────────────────────────────────
st.markdown("## Formula Reference")

st.markdown("""
| Component | Max Pts | Formula | Direction |
|---|---|---|---|
| **Volume** | 35 | `PERCENTRANK(Annualized Trips) × 35` | Higher trips → higher score |
| **Wait Time** | 18 | `(1 − PERCENTRANK(Wait Time)) × 18` | Lower wait → higher score |
| **Defect Rate** | 12 | `(1 − PERCENTRANK(Defect Rate)) × 12` | Lower defect → higher score |
| **Economics** | 35 | `PERCENTRANK(Basket × Fee) × 35` | Higher rev/order → higher score |
| **Total** | **100** | Sum of above | — |

*PERCENTRANK via `scipy.stats.percentileofscore` with `kind='rank'`, returning values in [0, 1].*
""")

st.markdown("""
| Tier | Rank Range | Count | Strategy |
|---|---|---|---|
| S | 1 – 10 | 10 | Fee reduction + top Feed placement |
| A | 11 – 50 | 40 | Modest fee reduction + good placement |
| B | 51 – 150 | 100 | Modest fee increase + standard placement |
| C | 151 – 200 | 50 | Larger fee increase + deprioritized placement |
""")
