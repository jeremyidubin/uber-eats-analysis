import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.ui import render_header, render_sidebar, TIER_COLORS, GREEN, DARK

st.set_page_config(page_title="Methodology & Assumptions", page_icon="📐", layout="wide")
render_header()
render_sidebar()

st.title("📐 Methodology & Assumptions")
st.markdown("Everything behind the model — what's in, what's out, and why.")
st.markdown("---")

# ─── SECTION 1: GUIDING PRINCIPLES ──────────────────────────────────────────
st.markdown("## 1  Scoring Model — Guiding Principles")

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

for i, (title, body) in enumerate(principles, 1):
    st.markdown(f"""
    <div style="background:#f0faf5; border-left:5px solid {GREEN};
                padding:1rem 1.2rem; border-radius:6px; margin-bottom:0.8rem;">
        <p style="margin:0 0 4px 0; font-weight:700; color:{DARK}; font-size:1rem;">
            {i}. {title}
        </p>
        <p style="margin:0; color:#374151; line-height:1.5;">{body}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ─── SECTION 2: IN VS OUT ────────────────────────────────────────────────────
st.markdown("## 2  What's In vs What's Out")

col_in, col_out = st.columns(2)

with col_in:
    st.markdown(f"""
    <div style="background:#f0faf5; border:2px solid {GREEN};
                border-radius:8px; padding:1.2rem 1.5rem; height:100%;">
        <h4 style="color:{GREEN}; margin-top:0;">✅ In the Model</h4>
    """, unsafe_allow_html=True)

    inputs = [
        ("Volume (35 pts)", "Annualized Trips", "Measures proven consumer demand — the most direct signal of merchant importance."),
        ("Ops Quality (30 pts)", "Wait Time (18 pts) + Defect Rate (12 pts)", "Measures the customer experience. Low wait + low defects → retention and repeat orders."),
        ("Economics (35 pts)", "Basket Size × Marketplace Fee", "Measures revenue per order. Captures fee level without making scoring circular."),
    ]

    for label, metric, reason in inputs:
        st.markdown(f"""
        <div style="margin-bottom:1rem; padding:0.8rem; background:white;
                    border-radius:6px; border-left:3px solid {GREEN};">
            <p style="margin:0; font-weight:700; color:{DARK};">{label}</p>
            <p style="margin:2px 0; font-size:0.85rem; color:#374151;"><em>Input: {metric}</em></p>
            <p style="margin:0; font-size:0.85rem; color:#6b7280;">{reason}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with col_out:
    st.markdown(f"""
    <div style="background:#fff8f8; border:2px solid #e74c3c;
                border-radius:8px; padding:1.2rem 1.5rem; height:100%;">
        <h4 style="color:#e74c3c; margin-top:0;">❌ Considered but Excluded</h4>
    """, unsafe_allow_html=True)

    exclusions = [
        ("First-Time Eater %", "Ambiguous signal",
         "High % could mean rapid growth OR high churn. Direction is unclear. Used for Feed allocation instead."),
        ("Location Activation Rate", "Backwards logic",
         "Low activation = growth opportunity OR operational failure. Ambiguous. Used to define Enterprise/SMB segment."),
        ("% Franchised", "No directional signal",
         "Franchised doesn't mean better or worse — it means different account management. Used for AM strategy only."),
        ("Fee Rate alone", "Circular",
         "We're about to set fees. Scoring on fee creates a circular dependency. Captured cleanly via Basket × Fee."),
    ]

    for label, reason_short, reason in exclusions:
        st.markdown(f"""
        <div style="margin-bottom:1rem; padding:0.8rem; background:white;
                    border-radius:6px; border-left:3px solid #e74c3c;">
            <p style="margin:0; font-weight:700; color:{DARK};">{label}</p>
            <p style="margin:2px 0; font-size:0.85rem; color:#e74c3c;"><em>Reason: {reason_short}</em></p>
            <p style="margin:0; font-size:0.85rem; color:#6b7280;">{reason}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ─── SECTION 3: FEE SIMULATOR ASSUMPTIONS ───────────────────────────────────
st.markdown("## 3  Fee Simulator — Key Assumptions")

assumptions = [
    ("🎯", "Volume changes are tied to Feed promotion, not fee elasticity",
     "The simulator models what happens when we change Feed ranking — top-tier merchants get "
     "more prominent placement and more orders. The fee adjustment is a separate, simultaneous lever."),
    ("📵", "Fee reductions don't directly increase orders",
     "Eaters don't see the marketplace fee — it's a B2B rate between Uber Eats and the restaurant. "
     "Volume lifts come from Feed placement changes, not fee changes themselves."),
    ("👁", "Fee increases have minimal volume impact",
     "Because eaters never see the marketplace fee, a 2pp fee increase to a C-tier merchant "
     "does not cause eaters to order less. The volume impact comes from Feed deprioritization."),
    ("📐", "Asymmetric volume effects (intentional)",
     "Feed promotion lift for S/A tier is larger in magnitude than deprioritization loss for B/C tier. "
     "This reflects real platform dynamics: promoting the best merchants drives outsized gains "
     "relative to the modest losses from deprioritizing weaker performers."),
]

for icon, title, body in assumptions:
    st.markdown(f"""
    <div style="background:#f8f9fa; border-left:5px solid #3498db;
                padding:1rem 1.2rem; border-radius:6px; margin-bottom:0.8rem;">
        <p style="margin:0 0 4px 0; font-weight:700; color:{DARK}; font-size:1rem;">
            {icon} {title}
        </p>
        <p style="margin:0; color:#374151; line-height:1.5;">{body}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ─── SECTION 4: DATA NOTES ───────────────────────────────────────────────────
st.markdown("## 4  Data Notes")

notes = [
    ("Dataset", "200 restaurant brands operating in U-City, sourced from the 2026 Business Case dataset."),
    ("Enterprise definition", "Active Locations ≥ 20 → Enterprise (~50 merchants). Below 20 → SMB (~150 merchants)."),
    ("PERCENTRANK scoring", "Percentile ranking is used instead of min-max normalization. This handles the heavily "
     "right-skewed trip distribution: a handful of merchants have 1M+ trips while most are under 100K. "
     "Min-max would compress the majority into a near-zero range. Percentile rank gives each merchant "
     "a fair relative position regardless of outliers."),
    ("Market share formula", "Estimated new share = 18% × (1 + trip growth %). The 18% is the stated current "
     "U-City market share. Trip growth is the aggregate % change in annualized trips under the simulated scenario."),
    ("Revenue figures", "Estimated annual revenue = Annualized Trips × Avg. Basket Size × Marketplace Fee. "
     "This is a Uber Eats take-rate estimate, not restaurant gross revenue."),
    ("Tier boundaries", "S: rank 1–10 (top 10 merchants). A: rank 11–50. B: rank 51–150. C: rank 151–200. "
     "Boundaries are rank-based, not score-threshold-based, ensuring exactly 10 S-tier merchants always."),
]

for label, note in notes:
    col_l, col_r = st.columns([1, 4])
    with col_l:
        st.markdown(f"**{label}**")
    with col_r:
        st.markdown(note)
    st.markdown("<hr style='margin:0.4rem 0; border-color:#e5e7eb;'>", unsafe_allow_html=True)

st.markdown("---")

# ─── SCORING FORMULA REFERENCE ───────────────────────────────────────────────
st.markdown("## 5  Scoring Formula Quick Reference")

st.markdown("""
| Component | Max Pts | Formula | Direction |
|---|---|---|---|
| **Volume** | 35 | `PERCENTRANK(Annualized Trips) × 35` | Higher trips → higher score |
| **Wait Time** | 18 | `(1 − PERCENTRANK(Wait Time)) × 18` | Lower wait → higher score |
| **Defect Rate** | 12 | `(1 − PERCENTRANK(Defect Rate)) × 12` | Lower defect → higher score |
| **Economics** | 35 | `PERCENTRANK(Basket × Fee) × 35` | Higher rev/order → higher score |
| **Total** | **100** | Sum of above | — |

*PERCENTRANK implemented via `scipy.stats.percentileofscore` with `kind='rank'`, returning values in [0, 1].*
""")

st.info("""
**Tier Assignment (rank-based, not score-threshold-based)**

| Tier | Rank Range | Count | Strategy |
|---|---|---|---|
| S | 1 – 10 | 10 | Fee reduction + top Feed placement → maximize volume & loyalty |
| A | 11 – 50 | 40 | Modest fee reduction + good Feed placement → grow share |
| B | 51 – 150 | 100 | Modest fee increase + standard placement → optimize margins |
| C | 151 – 200 | 50 | Larger fee increase + deprioritized → harvest or convert |
""")
