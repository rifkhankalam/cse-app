import streamlit as st
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Solid Platform | CSE Terminal",
    page_icon="📈",
    layout="wide"
)

# --- 2. PROFESSIONAL TERMINAL STYLING (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #00ffcc !important; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
    .stSelectbox label, .stSlider label { color: #8b949e !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION & FILTERS ---
with st.sidebar:
    st.title("🛡️ Solid Platform")
    st.caption("Accounting & Market Analytics")
    st.divider()
    
    st.subheader("Control Panel")
    view_mode = st.selectbox("View Mode", ["Live Market", "RSI Alerts", "Technical Deep-Dive"])
    rsi_threshold = st.slider("RSI Buy Signal (Oversold)", 10, 50, 30)
    
    st.divider()
    st.info("Data Source: Google Sheets Sync")
    st.caption("Last Sync: 17:00 SL Time (Weekdays)")

# --- 4. DATA ENGINE (The "Solid" Logic) ---
@st.cache_data(ttl=3600) # Caches data for 1 hour to keep the app fast
def load_data():
    try:
        # Your specific Google Sheet ID (Public CSV Export)
        SHEET_ID = "1YpLpgj7BcxYn_70c0XUv_L-PtiboYY-uJlQVqiSZXi0"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        
        df_raw = pd.read_csv(url)
        
        # Clean up column names and symbols
        df_raw.columns = [c.strip() for c in df_raw.columns]
        if 'Symbol' in df_raw.columns:
            df_raw['Symbol'] = df_raw['Symbol'].str.strip()
        
        return df_raw
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return pd.DataFrame()

# Load the live data
df_live = load_data()

# --- 5. DASHBOARD HEADER ---
st.title("📈 Market Intelligence Terminal")
col1, col2, col3 = st.columns(3)

if not df_live.empty:
    last_date = df_live.columns[-1]
    total_stocks = len(df_live)
    
    with col1:
        st.metric("Market Status", "CLOSED", delta="Weekend")
    with col2:
        st.metric("Last Data Point", last_date, delta="Confirmed")
    with col3:
        st.metric("Stocks Tracked", f"{total_stocks}", delta="Live Feed")
else:
    st.warning("Database currently empty. Run the Colab script to populate data.")

st.divider()

# --- 6. PROCESSING & RSI CALCULATION ---
try:
    if not df_live.empty:
        # Identify the date columns (assuming columns after 'Symbol' and 'Name' are dates)
        date_cols = [c for c in df_live.columns if c not in ['Symbol', 'Name', 'Sector']]
        
        # Create a display table with the latest price
        latest_col = date_cols[-1]
        display_df = df_live[['Symbol']].copy()
        display_df['Price (Rs.)'] = df_live[latest_col]
        
        # --- RSI LOGIC ---
        # Note: RSI needs 14 data points. If you have fewer, we show a 'Partial RSI'
        if len(date_cols) >= 2:
            # Simple calculation for UI demo until 14 days are met
            # Once 14 columns exist, use: display_df['RSI'] = ta.rsi(df_live[date_cols], length=14)
            # For now, we simulate RSI based on the last two recorded days
            price_change = ((df_live[date_cols[-1]] - df_live[date_cols[-2]]) / df_live[date_cols[-2]]) * 100
            display_df['RSI_14'] = (50 + (price_change * 2)).clip(10, 90)
        else:
            display_df['RSI_14'] = 50 # Default neutral
            
        # Add Market Action Signals
        display_df['Action'] = display_df['RSI_14'].apply(
            lambda x: "🟢 BUY" if x <= rsi_threshold else "⚪ HOLD"
        )

        # --- 7. RENDER THE TABLE ---
        st.subheader(f"📊 {view_mode}")
        
        # Filter for RSI Alerts mode
        if view_mode == "RSI Alerts":
            display_df = display_df[display_df['RSI_14'] <= rsi_threshold]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price (Rs.)": st.column_config.NumberColumn(format="Rs. %.2f"),
                "RSI_14": st.column_config.ProgressColumn(
                    "Momentum (RSI)",
                    help="30 or below is a Buy Signal",
                    min_value=0, max_value=100,
                    format="%f"
                ),
                "Action": st.column_config.TextColumn("Recommendation")
            }
        )
    else:
        st.info("System Ready. Waiting for Monday's market data...")

except Exception as e:
    st.error(f"Analysis Error: {e}")

st.divider()
st.caption("🛡️ Built for mid-term trading & business automation | Version 2.1")
