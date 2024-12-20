import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

def fetch_ipo_gmp():
    """Fetch IPO data from investorgain.com"""
    url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://www.investorgain.com/sme-ipo-dashboard/",
        "Connection": "keep-alive",
    }
    
    try:
        # Make request
        response = requests.get(url, headers=headers)
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main table
        table = soup.find('table', {'id': 'mainTable'})
        if not table:
            return "Error: Could not find GMP data table"

        # Extract headers - handle the sorting links in th
        headers = []
        for th in table.find('tr').find_all('th'):
            # Get the text inside the a tag if it exists, otherwise use th text
            a_tag = th.find('a')
            header = a_tag.text if a_tag else th.text
            # Remove the 'asc' text and strip whitespace
            header = header.replace('asc', '').strip()
            headers.append(header)
            
        # Extract rows
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            row = []
            for td in tr.find_all('td'):
                # Get all text content, including nested elements
                cell_content = td.get_text(strip=True)
                row.append(cell_content)
            if row:  # Only add non-empty rows
                rows.append(row)
                
        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Specify exact column names from source
        columns_to_keep = ['IPO', 'Price', 'Est Listing', 'IPO Size', 'Open', 'Close']
        df = df[columns_to_keep]
        
        return df[df['IPO'].str.contains('Open|Upcoming|Closing Today', case=False)]
        
    except requests.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return pd.DataFrame()

def parse_ipo_details(ipo_text):
    """Parse IPO text to extract name, type, status and subscription details"""
    # Check if it's SME IPO
    ipo_type = "SME" if "SME" in ipo_text else "Mainboard"
    
    # Extract status
    if "Upcoming" in ipo_text:
        status = "Upcoming"
    elif "Open" in ipo_text:
        status = "Open"
    elif "Closing Today" in ipo_text:
        status = "Closing Today"
    else:
        status = "Unknown"
    
    # Extract subscription times if available
    sub_match = re.search(r'Sub:(\d+\.?\d*x)', ipo_text)
    sub_times = sub_match.group(1) if sub_match else "N.A."
    
    # Extract name by removing the status and subscription info
    name = ipo_text.split("IPO")[0].replace("BSE SME", "").replace("NSE SME", "").strip()
    
    return {
        "name": name,
        "type": ipo_type,
        "status": status,
        "subscription": sub_times
    }

def format_price(price):
    """Format price with ₹ symbol"""
    try:
        return f"₹{float(price):,.2f}"
    except:
        return price

def show_gmp_info():
    """Display GMP information section"""
    with st.expander("ℹ️ What is Grey Market Premium (GMP)?", expanded=True):
        st.markdown("""
        ### 📚 Definition
        The Grey Market Premium refers to the unofficial premium or discount at which IPO 
        (Initial Public Offering) shares trade before they are officially listed on the stock exchange.
        """)
        
        # Formula in info box
        st.info("""
        **Formula:**
        GMP = Unofficial Grey Market Price - IPO Issue Price
        """)
        
        # Importance
        st.markdown("### 🎯 Importance in India")
        st.markdown("""
        - **Market Sentiment Indicator:** GMP serves as an early indicator of market sentiment 
        towards an upcoming IPO. A high positive GMP suggests strong demand and potential listing gains.
        """)

def main():
    st.set_page_config(
        page_title="IPO Dashboard",
        page_icon="🚀",
        layout="wide"
    )
    
    # Add custom CSS for better spacing and styling
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
        }
        .status-card {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .listing-date {
            color: #FF4B4B;
            font-weight: bold;
            font-size: 1.1em;
            padding: 5px;
            background-color: #ffeaea;
            border-radius: 4px;
            display: inline-block;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🚀 Live IPO Dashboard")
    # Add GMP Info
    show_gmp_info()
    st.markdown("---")
    
    # Warning note
    st.warning("""
    **Disclaimer:** 
    * GMP is an unofficial metric and should not be the sole basis for investment decisions. 
    * Data below is sourced from third party sources and investors should check the correctness of the data by themselves.
    * The IPOs displayed here are not investment advice.
    * Always conduct thorough research and consider multiple factors before investing in IPOs.
    """)
    
    # Add a refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    # Fetch data
    with st.spinner("Fetching latest IPO data..."):
        df = fetch_ipo_gmp()
        
    if df.empty:
        st.error("Unable to fetch IPO data. Please try again later.")
        return
    
    # Create three columns for different IPO statuses
    col1, col2, col3 = st.columns(3)
    
    # Process each IPO entry
    processed_data = []
    for _, row in df.iterrows():
        ipo_details = parse_ipo_details(row['IPO'])
        processed_data.append({
            **ipo_details,
            "price": row['Price'],
            "est_listing": row['Est Listing'],
            "ipo_size": row['IPO Size']
        })
    
    # Convert to DataFrame for easier filtering
    processed_df = pd.DataFrame(processed_data)
    
    # Display Upcoming IPOs
    with col1:
        st.subheader("📅 Upcoming IPOs")
        upcoming = processed_df[processed_df['status'] == 'Upcoming']
        if upcoming.empty:
            st.info("No upcoming IPOs at the moment")
        else:
            for _, ipo in upcoming.iterrows():
                with st.container():
                    st.markdown(f"""
                    ### {ipo['name']}
                    **Type:** {ipo['type']}  
                    **Price:** {format_price(ipo['price'])}  
                    **Issue Size:** {ipo['ipo_size']}  
                    <div class='listing-date'>🗓️ Expected Listing: {ipo['est_listing']}</div>
                    """, unsafe_allow_html=True)
                    st.divider()
    
    # Display Open IPOs
    with col2:
        st.subheader("🟢 Open IPOs")
        open_ipos = processed_df[processed_df['status'] == 'Open']
        if open_ipos.empty:
            st.info("No IPOs open for subscription")
        else:
            for _, ipo in open_ipos.iterrows():
                with st.container():
                    st.markdown(f"""
                    ### {ipo['name']}
                    **Type:** {ipo['type']}  
                    **Price:** {format_price(ipo['price'])}  
                    **Subscription:** {ipo['subscription']}  
                    **Issue Size:** {ipo['ipo_size']}  
                    <div class='listing-date'>🗓️ Expected Listing: {ipo['est_listing']}</div>
                    """, unsafe_allow_html=True)
                    st.divider()
    
    # Display Closing Today IPOs
    with col3:
        st.subheader("🔔 Closing Today")
        closing = processed_df[processed_df['status'] == 'Closing Today']
        if closing.empty:
            st.info("No IPOs closing today")
        else:
            for _, ipo in closing.iterrows():
                with st.container():
                    st.markdown(f"""
                    ### {ipo['name']}
                    **Type:** {ipo['type']}  
                    **Price:** {format_price(ipo['price'])}  
                    **Subscription:** {ipo['subscription']}  
                    **Issue Size:** {ipo['ipo_size']}  
                    <div class='listing-date'>🗓️ Expected Listing: {ipo['est_listing']}</div>
                    """, unsafe_allow_html=True)
                    st.divider()
    
    st.markdown("---")
    st.markdown(f"*Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} IST*")

if __name__ == "__main__":
    main()
