import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

st.set_page_config(
    page_title="Uber Eats U-City · Merchant Optimization",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page("app_home.py",                             title="Home",             default=True),
    st.Page("pages/1_Merchant_Scoring.py",             title="Merchant Scoring"),
    st.Page("pages/2_Fee_Optimization.py",             title="Fee Simulator"),
    st.Page("pages/3_Revenue_Impact_Dashboard.py",     title="Revenue Impact"),
    st.Page("pages/4_Methodology.py",                  title="Methodology"),
]

nav = st.navigation(pages)
nav.run()
