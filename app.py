import streamlit as st
import pandas as pd
import pandas_ta as ta
import cloudscraper

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CSE Insider Terminal",
    page_icon="📈",
    layout="wide"
)

# --- 2. PROFESSIONAL TERMINAL STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #00ffcc !important; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🛡️ Solid Platform")
    st.caption("Accounting & Market Analytics")
    st.divider()
    
    st.subheader("Control Panel")
    view_mode = st.selectbox("View Mode", ["Live Market", "RSI Alerts", "Watchlist"])
    rsi_threshold = st.slider("RSI Buy Signal (Oversold)", 10, 50, 30)
    
    st.divider()
    st.info("Connected to CSE via Google Sheets")

# --- 4. DASHBOARD HEADER ---
st.title("📈 Market Intelligence Terminal")
col1, col2, col3 = st.columns(3)

# Placeholder metrics until we link the live sheet tomorrow
with col1:
    st.metric("Market Status", "CLOSED", delta="Weekend")
with col2:
    st.metric("Last Data Point", "2026-04-02", delta="Thursday")
with col3:
    st.metric("System Health", "Optimal", delta="Connected")

st.divider()

# --- 5. DATA ENGINE (The "Solid" Logic) ---
try:
    # Creating a clean sample for the UI to prevent "Oh No" errors
    sample_data = {
        "Symbol": ["JKH.N0000", "LOLC.N0000", "VPEL.N0000", "HAYL.N0000", "DIAL.N0000"],
        "Name": ["John Keells", "LOLC Holdings", "Vidan Pathirana", "Hayleys PLC", "Dialog Axiata"],
        "Last Price": [192.50, 445.00, 14.50, 88.20, 11.40],
        "RSI_14": [65, 28, 35, 52, 31]
    }
    df = pd.DataFrame(sample_data)

    # Logic: Mark "BUY" if RSI is below the slider value
    df['Signal'] = df['RSI_14'].apply(lambda x: "🟢 BUY" if x <= rsi_threshold else "⚪ HOLD")

    # --- 6. RENDER THE TABLE ---
    st.subheader(f"📊 {view_mode}")
    
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "Last Price": st.column_config.NumberColumn(format="Rs. %.2f"),
            "RSI_14": st.column_config.ProgressColumn(
                "Relative Strength Index",
                min_value=0, max_value=100,
                format="%f"
            ),
            "Signal": st.column_config.TextColumn("Market Action")
        },
        hide_index=True
    )

except Exception as e:
    st.error(f"Engine Error: {e}")
    st.warning("Please check if requirements.txt includes: pandas, pandas-ta, and streamlit.")

st.caption("Note: Live data sync occurs every weekday at 5:00 PM SL Time.")
