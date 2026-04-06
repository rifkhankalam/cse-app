@st.cache_data(ttl=25)
def get_cse_live_data():
    try:
        # Use a more realistic browser header to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        scraper = cloudscraper.create_scraper()
        url = "https://www.cse.lk/equity/trade-summary"
        
        response = scraper.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return pd.DataFrame()

        soup = BeautifulSoup(response.text, 'lxml')
        
        # CSE tables are often loaded dynamically; this targets the standard HTML fallback
        tables = pd.read_html(response.text)
        
        # We search all tables found on the page for the one containing 'Symbol'
        df = None
        for t in tables:
            if 'Symbol' in t.columns:
                df = t
                break
        
        if df is not None:
            # Clean column names (removing the ** and extra spaces)
            df.columns = [str(c).replace('*', '').strip() for c in df.columns]
            
            # Select exactly what we need
            df_clean = df[['Symbol', 'Company', 'Last Trade (Rs.)']].copy()
            df_clean.columns = ['Symbol', 'Name', 'Last Trade']
            
            # Convert prices to numbers
            df_clean['Last Trade'] = pd.to_numeric(
                df_clean['Last Trade'].astype(str).str.replace(',', ''), 
                errors='coerce'
            )
            return df_clean
            
        return pd.DataFrame()
    except Exception as e:
        # Log the error for debugging in the Streamlit console
        print(f"Scrape Error: {e}")
        return pd.DataFrame()
