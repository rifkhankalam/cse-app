import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# --- 1. PAGE CONFIG & LIVE REFRESH ---
st.set_page_config(page_title="Solid Platform | LIVE", page_icon="⚡", layout="wide")

# This triggers a refresh every 30 seconds
count = st_autorefresh(interval=30000, key="fizzbuzz")

# --- 2. TIME-BASED LOGIC ---
sl_tz = pytz.timezone('Asia/Colombo')
now = datetime.now(sl_tz)
is_live_hours = (now.hour >= 8 and now.minute >= 30) and (now.hour < 15)

# --- 3. LIVE SCRAPER ENGINE ---
@st.cache_data(ttl=25) # Cache for slightly less than the refresh rate
def get_cse_live_data():
    try:
        scraper = cloudscraper.create_scraper()
        # Targeting the exact page from your screenshot
        url = "https://www.cse.lk/equity/trade-summary"
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Finding the 'Daily Share Trading Statistics' table
        table = soup.find('table') 
        df = pd.read_html(str(table))[0]
        
        # Mapping the columns from your screenshot
        # Column 0: Company, Column 1: Symbol, Column 8: **Last Trade (Rs.)
        df_clean = df.iloc[:, [1, 0, 8]].copy()
        df_clean.columns = ['Symbol', 'Name', 'Last Trade']
        
        # Clean numeric data
        df_clean['Last Trade'] = pd.to_numeric(
            df_clean['Last Trade'].astype(str).str.replace(',', ''), 
            errors='coerce'
        )
        return df_clean
    except Exception as e:
        return pd.DataFrame()

# --- 4. UI HEADER ---
st.title("🛡️ Solid Platform: Live Terminal")

if is_live_hours:
    st.markdown("### 🟢 LIVE MARKET MODE")
    st.caption(f"Last Update: {now.strftime('%I:%M:%S %p')} | Refreshing every 30s")
else:
    st.markdown("### 🌙 ARCHIVE MODE")
    st.caption("Market is currently closed. Showing last recorded closing prices.")

# --- 5. DATA DISPLAY ---
with st.spinner("Fetching Real-Time Prices..."):
    df_display = get_cse_live_data()

if not df_display.empty:
    # Sidebar for RSI threshold (using live price vs yesterday's close from your sheet)
    with st.sidebar:
        st.header("Control Panel")
        rsi_limit = st.slider("RSI Alert Level", 10, 50, 30)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Last Trade": st.column_config.NumberColumn("Last Trade (Rs.)", format="%.2f"),
            "Symbol": st.column_config.TextColumn("Ticker"),
            "Name": st.column_config.TextColumn("Company Name")
        }
    )
else:
    st.error("Unable to reach CSE Live Feed. Please check connection.")
