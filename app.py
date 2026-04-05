import streamlit as st
import pandas as pd
import pandas_ta as ta

# --- 1. SET PAGE CONFIG ---
st.set_page_config(
    page_title="CSE Insider Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS FOR A "TERMINAL" LOOK ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #00ffcc; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 10px; }
    /* Style for the search box */
    .stTextInput input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🛡️ Solid Platform")
    st.subheader("Filters & Controls")
    
    view_mode = st.radio("Select View", ["Market Overview", "RSI Alerts", "My Watchlist"])
    st.divider()
    
    rsi_filter = st.slider("Min RSI (Oversold)", 0, 100, 30)
    price_range = st.slider("Price Range (Rs.)", 0, 2000, (0, 500))
    
    st.info("Connected to: CSE_Market_Database")

# --- 4. TOP METRIC BAR ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Market Status", "OPEN", delta="Live Feed")
with col2:
    st.metric("Stocks Tracked", "284", delta="+2 Today")
with col3:
    st.metric("Avg. Market RSI", "52.4", delta="-1.2%")
with col4:
    st.metric("Last Sync", "17:00 SLT")

st.divider()

# --- 5. MAIN DATA DISPLAY ---
st.subheader(f"📊 {view_mode}")

# (Temporary Data Load - We will link your Google Sheet here tomorrow)
# This is a sample to show you the new UI design
data = {
    "Symbol": ["JKH.N0000", "LOLC.N0000", "HAYL.N0000", "DIAL.N0000"],
    "Company Name": ["John Keells Holdings", "LOLC Holdings", "Hayleys PLC", "Dialog Axiata"],
    "Price (Rs.)": [192.50, 445.00, 88.20, 11.40],
    "RSI (14)": [68, 28, 45, 32],
    "Trend": ["Neutral", "OVERSOLD", "Neutral", "Neutral"]
}
df = pd.DataFrame(data)

# Filter logic for the UI demo
filtered_df = df[(df['Price (Rs.)'] >= price_range[0]) & (df['Price (Rs.)'] <= price_range[1])]

# --- 6. THE STYLED TABLE ---
st.dataframe(
    filtered_df,
    use_container_width=True,
    height=500,
    column_config={
        "Price (Rs.)": st.column_config.NumberColumn(format="Rs. %.2f"),
        "RSI (14)": st.column_config.ProgressColumn(
            "Technical RSI",
            help="30 is Oversold (Buy), 70 is Overbought (Sell)",
            min_value=0,
            max_value=100,
            format="%f"
        ),
        "Trend": st.column_config.TextColumn("Signal")
    }
)

st.success("💡 Tip: Stocks with RSI under 30 are statistically primed for a mid-term bounce.")
