import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
import time

# --- 1. PAGE CONFIG & REFRESH ---
st.set_page_config(page_title="Solid Platform | LIVE", page_icon="📈", layout="wide")
st_autorefresh(interval=30000, key="cse_final_bypass")

# --- 2. TIME LOGIC ---
sl_tz = pytz.timezone('Asia/Colombo')
now = datetime.now(sl_tz)
is_live_hours = (now.weekday() < 5) and (now.hour >= 8 and now.hour < 15)

# --- 3. COLAB-STYLE BYPASS SCRAPER ---
@st.cache_data(ttl=25)
def get_cse_live_data():
    try:
        # Exact configuration that works in Colab environments
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        url = "https://www.cse.lk/equity/trade-summary"
        
        # Mimic human delay
        time.sleep(1.5) 
        response = scraper.get(url, timeout=30)
        
        if response.status_code != 200:
            return pd.DataFrame()

        # Parse tables
        tables = pd.read_html(response.text)
        target_df = None
        for df in tables:
            # Look for the symbol column
            if 'Symbol' in df.columns:
                target_df = df
                break
        
        if target_df is not None:
            # Clean headers
            target_df.columns = [str(c).replace('*', '').strip() for c in target_df.columns]
            price_col = [c for c in target_df.columns if 'Last Trade' in c][0]
            
            df_clean = target_df[['Symbol', price_col]].copy()
            df_clean.columns = ['Symbol', 'Live Price']
            
            # FORCE NUMERIC: Remove commas and handle non-numeric strings
            df_clean['Live Price'] = pd.to_numeric(
                df_clean['Live Price'].astype(str).str.replace(',', ''), 
                errors='coerce'
            )
            return df_clean
            
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# --- 4. DATA LOADING (GOOGLE SHEET) ---
@st.cache_data(ttl=600)
def load_sheet_data():
    try:
        SHEET_ID = "1YpLpgj7BcxYn_70c0XUv_L-PtiboYY-uJlQVqiSZXi0"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        # Clean headers
        df.columns = [c.strip() for c in df.columns]
        # Force numeric on all date columns
        date_cols = [c for c in df.columns if c not in ['Symbol', 'Name']]
        for col in date_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
        return df, date_cols
    except:
        return pd.DataFrame(), []

# --- 5. MAIN UI ---
st.title("🛡️ Solid Platform: Live Terminal")

df_hist, hist_date_cols = load_sheet_data()
df_live = get_cse_live_data()

# Status Row
c1, c2, c3 = st.columns(3)
with c1: st.metric("Market Status", "🟢 LIVE" if is_live_hours else "🌙 CLOSED")
with c2: 
    status_text = "CONNECTED" if not df_live.empty else "STALLED"
    st.metric("Live Feed", status_text)
with c3: st.metric("System Refresh", now.strftime("%H:%M:%S"))

st.divider()

# --- 6. DATA MERGE & MATH ---
if not df_hist.empty and hist_date_cols:
    # Build base frame
    final_df = df_hist[['Symbol', 'Name', hist_date_cols[-1]]].copy()
    final_df.columns = ['Symbol', 'Name', 'Prev Close']
    
    # Ensure 'Prev Close' is a float for math
    final_df['Prev Close'] = pd.to_numeric(final_df['Prev Close'], errors='coerce')

    if not df_live.empty:
        final_df = final_df.merge(df_live, on='Symbol', how='left')
        final_df['Current'] = final_df['Live Price'].fillna(final_df['Prev Close'])
        st.success("Live pricing synced.")
    else:
        final_df['Current'] = final_df['Prev Close']
        st.warning("Using static prices from Sheet.")

    # FINAL MATH GUARD: Force 'Current' to numeric one last time
    final_df['Current'] = pd.to_numeric(final_df['Current'], errors='coerce')
    
    # Now math will work:
    final_df['Change'] = ((final_df['Current'] - final_df['Prev Close']) / final_df['Prev Close']) * 100
    
    # --- 7. DISPLAY ---
    st.dataframe(
        final_df[['Symbol', 'Name', 'Current', 'Change']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Current": st.column_config.NumberColumn("Last Trade (Rs.)", format="%.2f"),
            "Change": st.column_config.NumberColumn("Day Change", format="%.2f%%")
        }
    )
else:
    st.error("Google Sheet structure error. Check Symbol/Name headers.")
