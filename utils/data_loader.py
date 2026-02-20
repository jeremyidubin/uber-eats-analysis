import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

# ─── Primary data source: CSV exported from the VSCode scoring model tab ─────
_CSV_FILE    = "[Model] Resturant Brands Scoring Model_VSCode.csv"
# ─── Fallback Excel workbook (demographic data only) ─────────────────────────
_DATA_FILE   = "[2026 Business Case] Insights & Analytics- Restaurant Brands Data Sheet_JD_W_Calculations.xlsx"
_DEMO_SHEET  = "RAW Demographic Data"

# Columns that contain formatted currency strings → strip $ and , → float
_DOLLAR_COLS = {
    'Avg. Basket Size', 'Current Rev',
    'New Rev / Order', 'New Revenue', 'Revenue Delta',
}
# Columns that contain formatted percentage strings → strip % → divide by 100
_PCT_COLS = {
    '% Franchised', 'Marketplace Fee', '%Orders from First Time Eaters',
    'Order Defect Rate', 'Target Fee', 'Fee Change',
}
# Columns that contain integer strings with comma separators → strip , → int
_COMMA_INT_COLS = {
    'Annualized Trips', 'Active Locations', 'Total Locations', 'New Trips',
}

# Default slider values (must match DEFAULTS in pages 2 & 3)
SLIDER_DEFAULTS = {
    'fee_s': -2.0, 'fee_a': -0.5, 'fee_b': 2.0,  'fee_c':  3.0,
    'vol_s': 20.0, 'vol_a': 10.0, 'vol_b': -5.0,  'vol_c': -15.0,
}


def _clean_dollar(series: pd.Series) -> pd.Series:
    """Remove $ and commas from a currency-formatted string column → float."""
    return (
        series.astype(str)
              .str.replace(r'[\$,]', '', regex=True)
              .str.strip()
              .pipe(pd.to_numeric, errors='coerce')
    )


def _clean_pct(series: pd.Series) -> pd.Series:
    """Strip % sign and divide by 100 → decimal fraction."""
    return (
        series.astype(str)
              .str.replace('%', '', regex=False)
              .str.strip()
              .pipe(pd.to_numeric, errors='coerce')
              .div(100)
    )


def _clean_comma_int(series: pd.Series) -> pd.Series:
    """Remove thousand-separator commas → numeric."""
    return (
        series.astype(str)
              .str.replace(',', '', regex=False)
              .str.strip()
              .pipe(pd.to_numeric, errors='coerce')
    )


@st.cache_data
def load_restaurant_data():
    """
    Load pre-calculated merchant data from the VSCode scoring model CSV.

    All scores, tiers, and default-scenario revenue projections are read directly
    from the CSV (source of truth). The ``_Default`` columns represent the
    pre-calculated simulation at the standard slider defaults:
        S: −2pp / +20%   A: −0.5pp / +10%   B: +2pp / −5%   C: +3pp / −15%

    Returns:
        pd.DataFrame: 200 rows, all scoring + revenue columns ready to use.
    """
    try:
        csv_path = Path(__file__).parent.parent / "data" / _CSV_FILE
        # dtype=str so we can clean the formatted values ourselves
        df = pd.read_csv(csv_path, header=0, dtype=str)

        # Strip whitespace from column names and any stray blank rows
        df.columns = df.columns.str.strip()
        df = df.dropna(how='all').reset_index(drop=True)

        # ── Parse formatted value columns ─────────────────────────────────────
        for col in _DOLLAR_COLS:
            if col in df.columns:
                df[col] = _clean_dollar(df[col])

        for col in _PCT_COLS:
            if col in df.columns:
                df[col] = _clean_pct(df[col])

        for col in _COMMA_INT_COLS:
            if col in df.columns:
                df[col] = _clean_comma_int(df[col])

        # ── Rename CSV columns → app-standard names ───────────────────────────
        df = df.rename(columns={
            'Type':                  'Segment',
            'Rev / Order (Helper)':  'Rev per Order',
            'Volume Score':          'Volume_Score',
            'Wait Time Score':       'Wait_Time_Score',
            'Defect Score':          'Defect_Rate_Score',
            'Quality Score Total':   'Ops_Quality_Score',
            'Econ Score':            'Economics_Score',
            'Total Score':           'Total_Score',
            'Current Rev':           'Estimated_Annual_Revenue',
            'Target Fee':            'Target_Fee_Default',
            'Fee Change':            'Fee_Change_Default',
            'New Trips':             'New_Trips_Default',
            'New Rev / Order':       'New_Rev_Per_Order_Default',
            'New Revenue':           'New_Revenue_Default',
            'Revenue Delta':         'Revenue_Delta_Default',
        })

        # ── Ops_Quality_Score is pre-calculated in the CSV; derive only if missing ──
        if 'Ops_Quality_Score' not in df.columns and {'Wait_Time_Score', 'Defect_Rate_Score'}.issubset(df.columns):
            df['Ops_Quality_Score'] = (df['Wait_Time_Score'] + df['Defect_Rate_Score']).round(2)

        # ── Ensure remaining score/rank columns are numeric ───────────────────
        plain_numeric = [
            'Avg. Courier Wait Time (min)',
            'Volume_Score', 'Wait_Time_Score', 'Defect_Rate_Score',
            'Ops_Quality_Score', 'Economics_Score', 'Total_Score', 'Rank',
            'New_Trips_Default', 'New_Revenue_Default', 'Revenue_Delta_Default',
            'Target_Fee_Default', 'Fee_Change_Default',
        ]
        for col in plain_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # ── Legacy derived columns (kept for page compatibility) ──────────────
        df['Revenue_Per_Trip']         = df['Avg. Basket Size'] * df['Marketplace Fee']
        df['Location_Activation_Rate'] = (
            df['Active Locations'] / df['Total Locations']
        ).fillna(0).round(4)
        df['Is_Franchised']            = df['% Franchised'] > 0.5

        # Fill any residual nulls in numeric columns with median
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())

        return df

    except FileNotFoundError:
        st.error(f"Data file not found. Expected: data/{_CSV_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


@st.cache_data
def load_demographic_data():
    """Load Demographic Data sheet from the same workbook."""
    try:
        data_path = Path(__file__).parent.parent / "data" / _DATA_FILE
        df = pd.read_excel(data_path, sheet_name=_DEMO_SHEET)
        df.columns = df.columns.str.strip()

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())

        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            if df[col].isnull().any():
                df[col] = df[col].fillna('Unknown')

        return df
    except FileNotFoundError:
        st.error(f"Data file not found. Expected: data/{_DATA_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading demographic data: {e}")
        return pd.DataFrame()


def get_data_summary(df):
    return {
        "rows":         len(df),
        "columns":      len(df.columns),
        "column_names": df.columns.tolist(),
        "dtypes":       df.dtypes.to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
    }
