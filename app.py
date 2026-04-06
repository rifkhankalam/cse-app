import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
import numpy as np

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Solid Platform | CSE Terminal", 
    page_icon="📈", 
    layout="wide"
)

# --- 2. AUTO-REFRESH (30 Seconds) ---
# This keeps the app live during market hours without manual refreshing
st_autorefresh(interval=30000, key="cse_live_refresh")

# --- 3. STYLING (Terminal Look) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #00ffcc !important; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TIME & MODE LOGIC ---
sl_tz = pytz.timezone('Asia/Colombo')
now = datetime.now(sl_tz)
# Live Mode: Monday-Friday, 08:30 to 15:00
is_weekday = now.weekday() < 5
is_live_hours = is_weekday and (now.hour >= 8 and now.hour < 15)
if now.hour == 8 and now.minute < 30:
    is_live_hours = False

# --- 5. DATA ENGINES ---

@st.cache_data(ttl=20)
def get_cse_live_data():
    """Scrapes live prices directly from the CSE Trade Summary page."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        scraper = cloudscraper.create_scraper()
        url = "https://www.cse.lk/equity/trade-summary"
        response = scraper.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return pd.DataFrame()

        # Parse tables using lxml engine
        tables = pd.read_html(response.text)
        df = None
        for t in tables:
            # Look for the table that actually contains stock symbols
            if 'Symbol' in t.columns:
                df = t
                break
        
        if df is not None:
            # Clean headers: Remove asterisks and spaces
            df.columns = [str(c).replace('*', '').strip() for c in df.columns]
            
            # Select relevant columns based on your Trade Summary screenshot
            # Some browsers see 'Company' or 'Company Name'
            name_col = 'Company' if 'Company' in df.columns else df.columns[0]
            
            df_clean = df[['Symbol', name_col, 'Last Trade (Rs.)']].copy()
            df_clean.columns = ['Symbol', 'Name', 'Price']
            
            # Data Cleaning: Remove commas and force to numeric
            df_clean['Price'] = pd.to_numeric(
                df_clean['Price'].astype(str).str.replace(',', ''), 
                errors='coerce'
            )
            return df_clean
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_historical_data():
    """Loads your archived prices from the Google Sheet."""
    try:
        SHEET_ID = "1YpLpgj7BcxYn_70c0XUv_L-PtiboYY-uJlQVqiSZXi0"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        
        # Clean numeric columns (excluding Symbol/Name)
        date_cols = [c for c in df.columns if c not in ['Symbol', 'Name']]
        for col in date_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
        return df, date_cols
    except:
        return pd.DataFrame(), []

# --- 6. MAIN INTERFACE ---
st.title("📈 Market Intelligence Terminal")

# Sidebar Controls
with st.sidebar:
    st.title("🛡️ Solid Platform")
    st.caption("Accounting & Market Analytics")
    st.divider()
    view_mode = st.radio("Display Mode", ["Full Market", "Top Gainers", "Watchlist"])
    rsi_threshold = st.slider("Momentum Alert (RSI)", 10, 70, 30)
    st.info(f"Last System Heartbeat: {now.strftime('%H:%M:%S')}")

# Execute Data Loading
df_hist, hist_date_cols = load_historical_data()
df_live = get_cse_live_data()

# Status Metrics
col1, col2, col3 = st.columns(3)
with col1:
    status = "🟢 LIVE" if is_live_hours else "🌙 CLOSED"
    st.metric("Market Status", status, delta="Trade Summary Feed")
with col2:
    last_date = hist_date_cols[-1] if hist_date_cols else "N/A"
    st.metric("Sheet Last Entry", last_date)
with col3:
    count = len(df_live) if not df_live.empty else len(df_hist)
    st.metric("Stocks Tracked", count)

st.divider()

# --- 7. DATA MERGING & MOMENTUM ---
try:
    if not df_live.empty:
        # We merge live prices with historical names/symbols for a complete view
        display_df = df_live.copy()
        
        # Calculate intraday change if historical data exists
        if not df_hist.empty and hist_date_cols:
            last_close = df_hist[['Symbol', hist_date_cols[-1]]]
            display_df = display_df.merge(last_close, on='Symbol', how='left')
            display_df['Change %'] = ((display_df['Price'] - display_df[hist_date_cols[-1]]) / display_df[hist_date_cols[-1]]) * 100
    
    elif not df_hist.empty:
        # Fallback to historical data if live feed fails or market is closed
        display_df = df_hist[['Symbol', 'Name']].copy()
        display_df['Price'] = df_hist[hist_date_cols[-1]]
        display_df['Change %'] = 0.0
        st.warning("Displaying static Archive data (Live feed unavailable).")

    # --- 8. RENDER TABLE ---
    st.subheader(f"📊 {view_mode}")
    
    # Simple RSI-style momentum indicator for the progress bar
    # (Based on % change from last closing)
    display_df['Momentum'] = (50 + (display_df.get('Change %', 0) * 2)).clip(5, 95)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn("Last Trade (Rs.)", format="%.2f"),
            "Change %": st.column_config.NumberColumn("Day Change", format="%.2f%%"),
            "Momentum": st.column_config.ProgressColumn("Intraday Momentum", min_value=0, max_value=100),
            "Name": st.column_config.TextColumn("Company Name", width="large")
        }
    )

except Exception as e:
    st.error(f"Operational Error: {e}")

st.caption("🛡️ Built for mid-term trading | v2.5 (Live Auto-Refresh Enabled)")
