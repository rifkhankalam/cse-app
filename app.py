
import streamlit as st
import cloudscraper
import pandas as pd

# 1. Web Page Setup
st.set_page_config(page_title="CSE Stock Terminal", layout="wide")
st.title("📊 CSE Real-Time Terminal")

# 2. The Data Engine
@st.cache_data(ttl=300) # Auto-refresh every 5 minutes
def get_data():
    try:
        scraper = cloudscraper.create_scraper()
        url = "https://www.cse.lk/api/tradeSummary"
        response = scraper.post(url, json={})
        data = response.json()
        df = pd.DataFrame(data['reqTradeSummery'])
        
        # Find price column
        price_col = [c for c in df.columns if 'price' in c.lower()][0]
        
        # Clean
        clean_df = df[['name', 'symbol', price_col]].copy()
        clean_df.columns = ['Company Name', 'Symbol', 'Price (Rs.)']
        clean_df['Company Name'] = clean_df['Company Name'].str.strip()
        return clean_df.sort_values(by='Company Name')
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# 3. Running the UI
data = get_data()

if not data.empty:
    search = st.text_input("🔍 Search for a stock (e.g., VPEL, Laxapana)")
    
    if search:
        filtered = data[data['Company Name'].str.contains(search, case=False) | 
                        data['Symbol'].str.contains(search, case=False)]
    else:
        filtered = data
        
    st.dataframe(filtered, use_container_width=True, height=600)
    st.caption(f"Showing {len(data)} stocks. Data refreshes every 5 mins.")
else:
    st.warning("Connecting to CSE... Please refresh the page.")
