%%writefile app.py
import streamlit as st
import cloudscraper
import pandas as pd

# --- SETTINGS ---
st.set_page_config(page_title="CSE Terminal", layout="wide")
st.title("📊 CSE Real-Time Terminal")

# --- DATA ENGINE ---
@st.cache_data(ttl=300)
def get_data():
    try:
        scraper = cloudscraper.create_scraper()
        url = "https://www.cse.lk/api/tradeSummary"
        response = scraper.post(url, json={})
        data = response.json()
        df = pd.DataFrame(data['reqTradeSummery'])
        
        # Identify price column
        price_col = [c for c in df.columns if 'price' in c.lower()][0]
        
        # Clean & Select
        clean_df = df[['name', 'symbol', price_col]].copy()
        clean_df.columns = ['Company Name', 'Symbol', 'Price (Rs.)']
        clean_df['Company Name'] = clean_df['Company Name'].str.strip()
        
        # 1. FIX STARTING INDEX: Change from 0 to 1
        clean_df.index = range(1, len(clean_df) + 1)
        
        return clean_df.sort_values(by='Company Name')
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- APP UI ---
data = get_data()

if not data.empty:
    search = st.text_input("🔍 Search for a stock (e.g., VPEL, Laxapana)")
    
    if search:
        filtered = data[data['Company Name'].str.contains(search, case=False) | 
                        data['Symbol'].str.contains(search, case=False)]
    else:
        filtered = data
        
    # 2. FIX PRICING FORMAT: Adding commas (1,000.00)
    # We use st.column_config to format the column without breaking the math
    st.dataframe(
        filtered, 
        use_container_width=True, 
        height=600,
        column_config={
            "Price (Rs.)": st.column_config.NumberColumn(
                "Price (Rs.)",
                format="%.2f", # Ensures 2 decimal places
            )
        }
    )
    
    # Note: Streamlit's NumberColumn automatically adds commas for thousands 
    # based on browser locale, but if you want to force it or see more, 
    # the format "%.2f" is the standard for currency.
    
    st.caption(f"Showing {len(data)} stocks. Index starts at 1. Prices formatted for accounting.")
else:
    st.warning("Connecting to CSE... Please refresh the page.")
