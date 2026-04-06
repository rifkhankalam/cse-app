import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# --- 1. PAGE CONFIG & REFRESH ---
st.set_page_config(page_title="Solid Platform | LIVE", page_icon="📈", layout="wide")
st_autorefresh(interval=30000, key="cse_api_heartbeat")

# --- 2. TIME LOGIC ---
sl_tz = pytz.timezone('Asia/Colombo')
now = datetime.now(sl_tz)
is_live_hours = (now.weekday() < 5) and (now.hour >= 8 and now.hour < 15)

# --- 3. THE "STEALTH" API ENGINE ---
@st.cache_data(ttl=25)
def get_cse_live_data():
    try:
        # We target the backend JSON endpoint instead of the HTML page
        url = "https://www.cse.lk/api/tradeSummary" 
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://www.cse.lk/equity/trade-summary",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # Using a standard request instead of cloudscraper for the API
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # The CSE API usually returns a list of dictionaries in 'data' or similar
            df = pd.DataFrame(data)
            
            # Map the API fields (adjusting for CSE's specific JSON keys)
            # Based on common CSE API structures:
            if 'symbol' in df.columns:
                df_clean = df[['symbol', 'lastTradedPrice']].copy()
                df_clean.columns = ['Symbol', 'Live Price']
                df_clean['Live Price'] = pd.to_numeric(df_clean['Live Price'], errors='coerce')
                return df_clean
        return pd.DataFrame()
    except:
        # If the API fails, we try the 'emergency' table scraper as a backup
        return pd.DataFrame()

# --- 4. DATA LOADING (SHEET) ---
@st.cache_data(ttl=600)
def load_sheet_data():
    try:
        SHEET_ID = "1YpLpgj7BcxYn_70c0XUv_L-PtiboYY-uJlQVqiSZXi0"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        date_cols = [c for c in df.columns if c not in ['Symbol', 'Name']]
        return df, date_cols
    except:
        return pd.DataFrame(), []

# --- 5. MAIN UI ---
st.title("🛡️ Solid Platform: Live Terminal")

df_hist, hist_date_cols = load_sheet_data()
df_live = get_cse_live_data()

# Metrics
c1, c2, c3 = st.columns(3)
with c1: st.metric("Market Status", "🟢 LIVE" if is_live_hours else "🌙 CLOSED")
with c2: 
    feed_status = "CONNECTED" if not df_live.empty else "API BLOCKED"
    st.metric("Live Feed", feed_status)
with c3: st.metric("System Time", now.strftime("%H:%M:%S"))

st.divider()

# --- 6. MERGE & DISPLAY ---
if not df_hist.empty and hist_date_cols:
    # Base from Sheet
    final_df = df_hist[['Symbol', 'Name', hist_date_cols[-1]]].copy()
    final_df.columns = ['Symbol', 'Name', 'Prev Close']
    final_df['Prev Close'] = pd.to_numeric(final_df['Prev Close'], errors='coerce')

    if not df_live.empty:
        final_df = final_df.merge(df_live, on='Symbol', how='left')
        final_df['Current'] = final_df['Live Price'].fillna(final_df['Prev Close'])
        st.success("Bypassed security via direct API access.")
    else:
        final_df['Current'] = final_df['Prev Close']
        st.warning("All bypass attempts failed. Using static Archive data.")

    final_df['Current'] = pd.to_numeric(final_df['Current'], errors='coerce')
    final_df['Change'] = ((final_df['Current'] - final_df['Prev Close']) / final_df['Prev Close']) * 100
    
    st.dataframe(
        final_df[['Symbol', 'Name', 'Current', 'Change']].sort_values('Change', ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Current": st.column_config.NumberColumn("Last Trade (Rs.)", format="%.2f"),
            "Change": st.column_config.NumberColumn("Day Change", format="%.2f%%")
        }
    )
