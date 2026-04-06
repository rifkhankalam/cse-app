import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
import time

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Solid Platform | LIVE", page_icon="📈", layout="wide")
st_autorefresh(interval=30000, key="cse_bypass_heartbeat")

# --- 2. TIME LOGIC ---
sl_tz = pytz.timezone('Asia/Colombo')
now = datetime.now(sl_tz)
is_live_hours = (now.weekday() < 5) and (now.hour >= 8 and now.hour < 15)

# --- 3. ADVANCED BYPASS SCRAPER ---
@st.cache_data(ttl=25)
def get_cse_live_data():
    try:
        # Mimicking a high-end desktop browser more precisely
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        url = "https://www.cse.lk/equity/trade-summary"
        
        # Adding a small human-like delay
        time.sleep(1) 
        response = scraper.get(url, timeout=25)
        
        if response.status_code != 200:
            return pd.DataFrame()

        soup = BeautifulSoup(response.text, 'lxml')
        # We look for the main stats table specifically
        tables = pd.read_html(str(soup))
        
        target_df = None
        for df in tables:
            # Standardize columns for checking
            cols = [str(c).strip() for c in df.columns]
            # CSE uses double asterisks for the live trade column
            if 'Symbol' in cols and any('Last Trade' in c for c in cols):
                df.columns = cols # Apply cleaned names
                target_df = df
                break
        
        if target_df is not None:
            # Find the exact name of the Last Trade column (handling the asterisks)
            price_col = [c for c in target_df.columns if 'Last Trade' in c][0]
            
            df_clean = target_df[['Symbol', price_col]].copy()
            df_clean.columns = ['Symbol', 'Live Price']
            
            # Clean numeric data
            df_clean['Live Price'] = pd.to_numeric(
                df_clean['Live Price'].astype(str).str.replace(',', ''), 
                errors='coerce'
            )
            return df_clean
            
        return pd.DataFrame()
    except Exception as e:
        st.sidebar.error(f"Bypass Attempt Failed: {e}")
        return pd.DataFrame()

# --- 4. DATA LOADING ---
@st.cache_data(ttl=600)
def load_sheet_data():
    try:
        SHEET_ID = "1YpLpgj7BcxYn_70c0XUv_L-PtiboYY-uJlQVqiSZXi0"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        date_cols = [c.strip() for c in df.columns if c not in ['Symbol', 'Name']]
        return df, date_cols
    except:
        return pd.DataFrame(), []

# --- 5. MAIN UI ---
st.title("🛡️ Solid Platform: Live Terminal")

df_hist, hist_date_cols = load_sheet_data()
df_live = get_cse_live_data()

# Header Status
c1, c2, c3 = st.columns(3)
with c1: st.metric("Market Status", "🟢 LIVE" if is_live_hours else "🌙 CLOSED")
with c2: st.metric("Live Feed", "CONNECTED" if not df_live.empty else "BLOCKED", 
                   delta="Bypass Active" if not df_live.empty else "Security Barrier")
with c3: st.metric("Last Sync", now.strftime("%H:%M:%S"))

st.divider()

# --- 6. MERGE & DISPLAY ---
if not df_hist.empty:
    # Use your sheet as the base so we keep your custom names
    final_df = df_hist[['Symbol', 'Name', hist_date_cols[-1]]].copy()
    final_df.columns = ['Symbol', 'Name', 'Prev Close']
    
    if not df_live.empty:
        # Update the sheet data with the live scraped prices
        final_df = final_df.merge(df_live, on='Symbol', how='left')
        # If live price is missing for a specific stock, keep the previous close
        final_df['Current'] = final_df['Live Price'].fillna(final_df['Prev Close'])
        st.success(f"Successfully bypassed CSE block. Data fresh as of {now.strftime('%I:%M %p')}")
    else:
        final_df['Current'] = final_df['Prev Close']
        st.warning("Bypass failed. Showing static data from Google Sheets.")

    # Calculations
    final_df['Change'] = ((final_df['Current'] - final_df['Prev Close']) / final_df['Prev Close']) * 100
    
    st.dataframe(
        final_df[['Symbol', 'Name', 'Current', 'Change']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Current": st.column_config.NumberColumn("Last Trade (Rs.)", format="%.2f"),
            "Change": st.column_config.NumberColumn("Day Change", format="%.2f%%")
        }
    )
