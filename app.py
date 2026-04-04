import streamlit as st
import cloudscraper
import pandas as pd

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="CSE Stock Terminal", layout="wide")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 CSE Real-Time Terminal")
st.subheader("Colombo Stock Exchange - Market Overview")

# --- 2. DATA ENGINE (The Scraper) ---
@st.cache_data(ttl=300) 
def get_cse_market_data():
    try:
        scraper = cloudscraper.create_scraper()
        url = "https://www.cse.lk/api/tradeSummary"
        response = scraper.post(url, json={})
        data = response.json()
        
        df = pd.DataFrame(data['reqTradeSummery'])
        
        # Identify the Price Column
        price_col = [c for c in df.columns if 'price' in c.lower()][0]
        
        # Select and Clean
        clean_df = df[['name', 'symbol', price_col]].copy()
        clean_df.columns = ['Company Name', 'Symbol', 'Price (Rs.)']
        clean_df['Company Name'] = clean_df['Company Name'].str.strip()
        
        # Sort Alphabetically
        clean_df = clean_df.sort_values(by='Company Name')
        
        # Ensure Price is a number for formatting
        clean_df['Price (Rs.)'] = pd.to_numeric(clean_df['Price (Rs.)'], errors='coerce')
        
        return clean_df
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return pd.DataFrame()

# --- 3. APP LOGIC & UI ---
df_market = get_cse_market_data()

if not df_market.empty:
    search_query = st.text_input("🔍 Search by Company Name or Symbol (e.g., VPEL, ACL)")

    # Filter data
    if search_query:
        display_df = df_market[
            df_market['Company Name'].str.contains(search_query, case=False) | 
            df_market['Symbol'].str.contains(search_query, case=False)
        ].copy()
    else:
        display_df = df_market.copy()

    # --- 4. ACCOUNTING FORMATTING ---
    # We create a display version with commas, while keeping the original for logic
    display_df['Price (Rs.)'] = display_df['Price (Rs.)'].map('{:,.2f}'.format)
    
    # Reset index to start from 1
    display_df.index = range(1, len(display_df) + 1)

    # Show the table
    st.table(display_df) # Using st.table for fixed accounting-style display

    st.info(f"✅ Total Stocks: {len(df_market)} | Data refreshes every 5 Minutes")
else:
    st.warning("🔄 Attempting to reconnect...")

st.sidebar.write("### App Status")
st.sidebar.success("🟢 System Online")
st.sidebar.write("Developed for groceries.lk")
