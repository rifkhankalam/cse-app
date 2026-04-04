import streamlit as st
import cloudscraper
import pandas as pd

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="CSE Stock Terminal", layout="wide")

# Custom CSS for Left Alignment
st.markdown("""
    <style>
    /* Force left alignment for all cells */
    [data-testid="stDataFrame"] td {
        text-align: left !important;
    }
    .main {
        background-color: #f5f7f9;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 CSE Real-Time Terminal")
st.subheader("Colombo Stock Exchange - Market Overview")

# --- 2. DATA ENGINE ---
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
        
        # Force Price to be a Float (Number) and remove any non-numeric characters
        clean_df['Price (Rs.)'] = pd.to_numeric(clean_df['Price (Rs.)'], errors='coerce')
        
        # Remove any rows where price is missing
        clean_df = clean_df.dropna(subset=['Price (Rs.)'])
        
        # Clean up company names
        clean_df['Company Name'] = clean_df['Company Name'].str.strip()
        
        # Default Sort: A-Z
        clean_df = clean_df.sort_values(by='Company Name')
        
        return clean_df
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return pd.DataFrame()

# --- 3. APP LOGIC & UI ---
df_market = get_cse_market_data()

if not df_market.empty:
    search_query = st.text_input("🔍 Search by Company Name or Symbol (e.g., VPEL, ACL)")

    # Filter data based on search
    if search_query:
        display_df = df_market[
            df_market['Company Name'].str.contains(search_query, case=False) | 
            df_market['Symbol'].str.contains(search_query, case=False)
        ].copy()
    else:
        display_df = df_market.copy()

    # Reset index to start from 1
    display_df.index = range(1, len(display_df) + 1)

    # --- 4. THE DATA TABLE ---
    # We use 'format="%f"' but let Streamlit handle the thousands separator 
    # to avoid the instruction text error you saw.
    st.dataframe(
        display_df,
        use_container_width=True,
        height=700,
        column_config={
            "Company Name": st.column_config.TextColumn("Company Name", width="large"),
            "Symbol": st.column_config.TextColumn("Symbol", width="medium"),
            "Price (Rs.)": st.column_config.NumberColumn(
                "Price (Rs.)",
                width="medium",
                format="%.2f" # This ensures two decimal points
            )
        }
    )

    st.info(f"✅ Total Stocks: {len(df_market)} | Click headers to sort | Refreshes every 5 Mins")
else:
    st.warning("🔄 Attempting to reconnect...")

st.sidebar.write("### App Status")
st.sidebar.success("🟢 System Online")
st.sidebar.write("Developed for groceries.lk")
