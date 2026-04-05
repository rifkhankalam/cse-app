import streamlit as st
import pandas as pd
import numpy as np

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Solid Platform | CSE Terminal", page_icon="📈", layout="wide")

# --- 2. STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #00ffcc !important; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Solid Platform")
    st.caption("Accounting & Market Analytics")
    st.divider()
    view_mode = st.selectbox("View Mode", ["Live Market", "RSI Alerts"])
    rsi_threshold = st.slider("RSI Buy Signal (Oversold)", 10, 50, 30)

# --- 4. DATA ENGINE ---
@st.cache_data(ttl=10)
def load_data():
    try:
        SHEET_ID = "1YpLpgj7BcxYn_70c0XUv_L-PtiboYY-uJlQVqiSZXi0"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        
        # Clean Column Names
        df.columns = [c.strip() for c in df.columns]
        
        # Identify date columns (anything that isn't Symbol or Name)
        exclude = ['Symbol', 'Name']
        date_cols = [c for c in df.columns if c not in exclude]
        
        # Clean numeric data (remove commas)
        for col in date_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
            
        return df, date_cols
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return pd.DataFrame(), []

df_live, date_cols = load_data()

# --- 5. HEADER ---
st.title("📈 Market Intelligence Terminal")
if not df_live.empty and date_cols:
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Market Status", "CLOSED", delta="Weekend")
    with col2: st.metric("Last Data Point", date_cols[-1], delta="Confirmed")
    with col3: st.metric("Stocks Tracked", len(df_live), delta="Live Feed")

st.divider()

# --- 6. PROCESSING ---
try:
    if not df_live.empty and date_cols:
        # Create Display Table
        cols_to_show = ['Symbol']
        if 'Name' in df_live.columns:
            cols_to_show.append('Name')
        
        display_df = df_live[cols_to_show].copy()
        display_df['Price (Rs.)'] = df_live[date_cols[-1]]
        
        # Momentum Calculation
        if len(date_cols) >= 2:
            prev_price = df_live[date_cols[-2]]
            curr_price = df_live[date_cols[-1]]
            price_change = ((curr_price - prev_price) / prev_price.replace(0, np.nan)) * 100
            display_df['RSI_14'] = (50 + (price_change * 2)).fillna(50).clip(5, 95)
        else:
            display_df['RSI_14'] = 50
            
        display_df['Action'] = display_df['RSI_14'].apply(lambda x: "🟢 BUY" if x <= rsi_threshold else "⚪ HOLD")

        # --- 7. RENDER ---
        st.subheader(f"📊 {view_mode}")
        if view_mode == "RSI Alerts":
            display_df = display_df[display_df['RSI_14'] <= rsi_threshold]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price (Rs.)": st.column_config.NumberColumn(format="%.2f"),
                "RSI_14": st.column_config.ProgressColumn("Momentum (RSI)", min_value=0, max_value=100),
                "Name": st.column_config.TextColumn("Company Name", width="medium")
            }
        )
except Exception as e:
    st.error(f"Analysis Error: {e}")

st.caption("🛡️ Built for mid-term trading | Version 2.3")
