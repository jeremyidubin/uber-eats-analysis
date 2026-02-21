import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.ui import render_header, render_sidebar

st.set_page_config(page_title="Methodology", page_icon=None, layout="wide")
render_header()
render_sidebar()

st.title("Methodology")
st.markdown(
    "<p style='color:#757575; font-size:14px; margin-bottom:1.5rem;'>"
    "What's in the model, what's out, and why.</p>",
    unsafe_allow_html=True,
)

# ─── Scoring Model ────────────────────────────────────────────────────────────
st.markdown("## Scoring Model")

st.markdown("""
| Component | Max Pts | Formula | Direction |
|---|---|---|---|
| **Volume** | 35 | `PERCENTRANK(Annualized Trips) × 35` | Higher trips → higher score |
| **Wait Time** | 18 | `(1 − PERCENTRANK(Wait Time)) × 18` | Lower wait → higher score |
| **Defect Rate** | 12 | `(1 − PERCENTRANK(Defect Rate)) × 12` | Lower defect → higher score |
| **Economics** | 35 | `PERCENTRANK(Basket × Fee) × 35` | Higher rev/order → higher score |
| **Total** | **100** | Sum of above | — |
""")

st.markdown(
    "Trip volume is heavily right-skewed — a few brands have 1M+ annualized trips. "
    "Min-max normalization would let 3 merchants dominate the score. Percentile rank "
    "compresses this into a relative ranking where every merchant's position reflects "
    "how they compare to the full set."
)

st.markdown("**Variables in vs out**")

st.markdown("""
| Variable | Decision | Reason |
|---|---|---|
| Annualized Trips | In — Volume (35 pts) | Most direct signal of consumer demand and merchant importance. |
| Avg. Courier Wait Time | In — Ops Quality (18 pts) | Lower wait time correlates with better retention and repeat orders. |
| Order Defect Rate | In — Ops Quality (12 pts) | Directly measures experience quality; lower is unambiguously better. |
| Basket Size × Fee | In — Economics (35 pts) | Revenue per order — captures fee level without making scoring circular. |
| First-Time Eater % | Excluded | High % could mean rapid growth or high churn; direction is unclear. |
| Location Activation Rate | Excluded | Low activation is either a growth opportunity or an operational failure — ambiguous. |
| % Franchised | Excluded | Franchised vs. corporate doesn't indicate performance; it indicates account management type. |
| Fee Rate alone | Excluded | Fee is set in Phase 3. Scoring on it creates a circular dependency. |
| Active Locations | Excluded | Used only for the Enterprise/SMB split. Including it in scoring double-counts scale. |
""")

st.markdown(
    "Enterprise = 20+ active locations. "
    "Tiers are rank-based (S: 1–10, A: 11–50, B: 51–150, C: 151–200), not score-threshold-based."
)

st.markdown("---")

# ─── Fee Simulator Assumptions ────────────────────────────────────────────────
st.markdown("## Fee Simulator Assumptions")

st.markdown(
    "The simulator models two parallel levers applied in Phase 3: fee restructuring changes "
    "what Uber earns per trip, Feed reordering changes how many trips each merchant gets. "
    "These are independent — the fee adjustment doesn't cause the volume change."
)

st.markdown(
    "Volume shifts reflect Feed promotion and deprioritization, not fee elasticity. "
    "Eaters don't see the marketplace fee — it's a B2B rate between Uber Eats and the restaurant. "
    "A fee increase on a C-tier merchant doesn't reduce consumer demand. The volume lift for "
    "S/A tiers is intentionally larger than the loss for B/C because promoting top merchants "
    "drives outsized gains."
)

st.markdown(
    "Revenue = Annualized Trips × Avg. Basket Size × Marketplace Fee. "
    "This is Uber Eats take-rate revenue, not restaurant gross revenue. "
    "Market share = 18% × (1 + trip growth %)."
)
