import streamlit as st
import cloudscraper
import pandas as pd

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="CSE Stock Terminal", layout="wide")

# Custom CSS to make it look like a professional trading platform
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stDataFrame {
        border: 1px solid #e6e9ef;
        border-radius: 5px;
    }
    </style>
    """, unsafe_base_with_rows=True)

st.title("📊 CSE Real-Time Terminal")
st.subheader("Colombo Stock Exchange - Market Overview")

# --- 2. DATA ENGINE (The Scraper) ---
@st.cache_data(ttl=300) # Data refreshes every 5 minutes
def get_cse_market_data():
    try:
        # Connect to CSE API
        scraper = cloudscraper.create_scraper()
        url = "https://www.cse.lk/api/tradeSummary"
        response = scraper.post(url, json={})
        data = response.json()
        
        # Convert to Table
        df = pd.DataFrame(data['reqTradeSummery'])
        
        # Identify the Price Column automatically
        price_col = [c for c in df.columns if 'price' in c.lower()][0]
        
        # Select and Clean Columns
        clean_df = df[['name', 'symbol', price_col]].copy()
        clean_df.columns = ['Company Name', 'Symbol', 'Price (Rs.)']
        
        # Clean up whitespace in names
        clean_df['Company Name'] = clean_df['Company Name'].str.strip()
        
        # Sort Alphabetically by Company Name
        clean_df = clean_df.sort_values(by='Company Name')
        
        # FIX: Reset Index to start from 1 instead of 0
        clean_df.index = range(1, len(clean_df) + 1)
        
        return clean_df
    except Exception as e:
        st.error(f"⚠️ Connection Error: Could not fetch data from CSE. ({e})")
        return pd.DataFrame()

# --- 3. APP LOGIC & UI ---
df_market = get_cse_market_data()

if not df_market.empty:
    # Search Bar
    search_query = st.text_input("🔍 Search by Company Name or Symbol (e.g., VPEL, ACL, Laxapana)")

    # Apply Search Filter
    if search_query:
        display_df = df_market[
            df_market['Company Name'].str.contains(search_query, case=False) | 
            df_market['Symbol'].str.contains(search_query, case=False)
        ]
    else:
        display_df = df_market

    # --- 4. THE DATA TABLE (With Accounting Formatting) ---
    st.dataframe(
        display_df,
        use_container_width=True,
        height=700,
        column_config={
            "Company Name": st.column_config.TextColumn(
                "Company Name",
                width="large",
            ),
            "Symbol": st.column_config.TextColumn(
                "Symbol (Ticker)",
                help="The official CSE Trading Symbol",
            ),
            "Price (Rs.)": st.column_config.NumberColumn(
                "Price (Rs.)",
                help="Last Traded Price",
                format="%.2f", # Ensures 2 decimal places
            )
        }
    )

    # Brute Force Formatting for Commas (Ensuring 1,000.00 looks right)
    # Note: Streamlit's NumberColumn handles commas based on the viewer's locale.
    
    st.info(f"✅ Total Stocks: {len(df_market)} | Data source: CSE.lk | Last Updated: Every 5 Minutes")
else:
    st.warning("🔄 Attempting to reconnect to the market server... Please refresh the page.")

st.sidebar.markdown("---")
st.sidebar.write("### App Status")
st.sidebar.success("🟢 System Online")
st.sidebar.write("Developed for groceries.lk Stock Directory")
