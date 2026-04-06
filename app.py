import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
import numpy as np

# --- 1. PAGE CONFIG & AUTO-REFRESH ---
st.set_page_config(page_title="Solid Platform | LIVE", page_icon="📈", layout="wide")
st_autorefresh(interval=30000, key="cse_heartbeat")

# --- 2. TIME LOGIC ---
sl_tz = pytz.timezone('Asia/Colombo')
now = datetime.now(sl_tz)
is_live_hours = (now.weekday() < 5) and (now.hour >= 8 and now.hour < 15)

# --- 3. THE REFINED SCRAPER ---
@st.cache_data(ttl=25)
def get_cse_live_data():
    try:
        # Using a session to look more like a real browser
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        url = "https://www.cse.lk/equity/trade-summary"
        
        response = scraper.get(url, timeout=20)
        if response.status_code != 200:
            return pd.DataFrame()

        # Parse with BeautifulSoup to find the specific 'Summary' table
        soup = BeautifulSoup(response.text, 'lxml')
        tables = pd.read_html(str(soup))
        
        target_df = None
        for df in tables:
            # Clean columns immediately to check for 'Symbol'
            df.columns = [str(c).replace('*', '').strip() for c in df.columns]
            if 'Symbol' in df.columns and 'Last Trade (Rs.)' in df.columns:
                target_df = df
                break
        
        if target_df is not None:
            # Extract and rename
            df_clean = target_df[['Symbol', 'Last Trade (Rs.)']].copy()
            df_clean.columns = ['Symbol', 'Live Price']
            df_clean['Live Price'] = pd.to_numeric(df_clean['Live Price'].astype(str).str.replace(',', ''), errors='coerce')
            return df_clean
            
        return pd.DataFrame()
    except Exception as e:
        print(f"Scrape Error: {e}")
        return pd.DataFrame()

# --- 4. DATA LOADING (SHEET) ---
@st.cache_data(ttl=600)
def load_sheet_data():
    try:
        SHEET_ID = "1YpLpgj7BcxYn_70c0XUv_L-PtiboYY-uJlQVqiSZXi0"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        # Convert date columns to numeric
        date_cols = [c for c in df.columns if c not in ['Symbol', 'Name']]
        for col in date_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
        return df, date_cols
    except:
        return pd.DataFrame(), []

# --- 5. MAIN UI ---
st.title("🛡️ Solid Platform: Market Terminal")

df_hist, hist_date_cols = load_sheet_data()
df_live_price = get_cse_live_data()

# Header Metrics
m1, m2, m3 = st.columns(3)
with m1: st.metric("Market Status", "🟢 LIVE" if is_live_hours else "🌙 CLOSED")
with m2: st.metric("Sheet Last Entry", hist_date_cols[-1] if hist_date_cols else "N/A")
with m3: st.metric("System Time", now.strftime("%H:%M:%S"))

st.divider()

# --- 6. MERGING LOGIC ---
if not df_hist.empty:
    main_df = df_hist[['Symbol', 'Name', hist_date_cols[-1]]].copy()
    main_df.columns = ['Symbol', 'Company Name', 'Prev Close']
    
    if not df_live_price.empty:
        # Merge live scrape into the sheet data
        main_df = main_df.merge(df_live_price, on='Symbol', how='left')
        main_df['Last Trade (Rs.)'] = main_df['Live Price'].fillna(main_df['Prev Close'])
        st.success("Live Feed Connected")
    else:
        # Fallback
        main_df['Last Trade (Rs.)'] = main_df['Prev Close']
        st.warning("Displaying static Archive data (Live feed unavailable).")

    # Calculate Intraday Change
    main_df['Day Change'] = ((main_df['Last Trade (Rs.)'] - main_df['Prev Close']) / main_df['Prev Close']) * 100
    main_df['Momentum'] = (50 + (main_df['Day Change'] * 5)).clip(5, 95)

    # --- 7. DISPLAY ---
    st.dataframe(
        main_df[['Symbol', 'Company Name', 'Last Trade (Rs.)', 'Day Change', 'Momentum']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Last Trade (Rs.)": st.column_config.NumberColumn(format="%.2f"),
            "Day Change": st.column_config.NumberColumn(format="%.2f%%"),
            "Momentum": st.column_config.ProgressColumn(min_value=0, max_value=100)
        }
    )
else:
    st.error("Check Google Sheet Connection.")
