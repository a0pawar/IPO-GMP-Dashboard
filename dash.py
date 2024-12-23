import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# Common utility functions
def format_price(price):
    """Format price with ₹ symbol"""
    try:
        return f"₹{float(price):,.2f}"
    except:
        return price

# GMP Tab Functions
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
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'mainTable'})
        if not table:
            return pd.DataFrame()

        headers = []
        for th in table.find('tr').find_all('th'):
            a_tag = th.find('a')
            header = a_tag.text if a_tag else th.text
            header = header.replace('asc', '').strip()
            headers.append(header)
            
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            row = []
            for td in tr.find_all('td'):
                cell_content = td.get_text(strip=True)
                row.append(cell_content)
            if row:
                rows.append(row)
                
        df = pd.DataFrame(rows, columns=headers)
        columns_to_keep = ['IPO', 'Price', 'Est Listing', 'IPO Size', 'Open', 'Close']
        df = df[columns_to_keep]
        
        return df[df['IPO'].str.contains('Open|Upcoming|Closing Today', case=False)]
        
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

def parse_ipo_details(ipo_text):
    """Parse IPO text to extract name, type, status and subscription details"""
    ipo_type = "SME" if "SME" in ipo_text else "Mainboard"
    
    if "Upcoming" in ipo_text:
        status = "Upcoming"
    elif "Open" in ipo_text:
        status = "Open"
    elif "Closing Today" in ipo_text:
        status = "Closing Today"
    else:
        status = "Unknown"
    
    sub_match = re.search(r'Sub:(\d+\.?\d*x)', ipo_text)
    sub_times = sub_match.group(1) if sub_match else "N.A."
    
    name = ipo_text.split("IPO")[0].replace("BSE SME", "").replace("NSE SME", "").strip()
    
    return {
        "name": name,
        "type": ipo_type,
        "status": status,
        "subscription": sub_times
    }

def show_gmp_info():
    """Display GMP information section"""
    with st.expander("ℹ️ What is Grey Market Premium (GMP)?", expanded=False):
        st.markdown("""
        ### 📚 Definition
        The Grey Market Premium refers to the unofficial premium or discount at which IPO 
        shares trade before they are officially listed on the stock exchange.
        """)
        
        st.info("""
        **Formula:**
        GMP = Unofficial Grey Market Price - IPO Issue Price
        """)
        
        st.markdown("### 🎯 Importance in India")
        st.markdown("""
        - **Market Sentiment Indicator:** GMP serves as an early indicator of market sentiment 
        towards an upcoming IPO. A high positive GMP suggests strong demand and potential listing gains.
        """)

# Subscription Tab Functions
def fetch_subscription_data():
    """Fetch IPO subscription data from investorgain.com"""
    url = "https://www.investorgain.com/report/ipo-subscription-live/333/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://www.investorgain.com/",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'mainTable'})
        
        if not table:
            return pd.DataFrame()
            
        headers = [th.get_text(strip=True).replace('asc', '') for th in table.find('tr').find_all('th')]
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            row = [td.get_text(strip=True) for td in tr.find_all('td')]
            if row:
                rows.append(row)
                
        df = pd.DataFrame(rows, columns=headers)
        
        df['Close_Date_DT'] = pd.to_datetime(df['Close Date'].str.replace(r'(?:st|nd|rd|th)', '', regex=True), format='%d %b %Y')
        
        ist_now = pd.Timestamp.now(tz='Asia/Kolkata').date()
        
        df = df[df['Close_Date_DT'].dt.date >= ist_now]
        return df
        
    except Exception as e:
        st.error(f"Error fetching subscription data: {str(e)}")
        return pd.DataFrame()

def parse_subscription_ipo_name(ipo_text):
    """Parse IPO text for subscription data"""
    gmp_match = re.search(r'GMP:â¹(\d+)\s*\(([^)]+)\)', ipo_text)
    gmp_value = gmp_match.group(1) if gmp_match else 'N/A'
    gmp_percentage = gmp_match.group(2) if gmp_match else 'N/A'
    
    is_sme = "SME" in ipo_text
    name = ipo_text.split("GMP")[0].strip()
    name = re.sub(r'\s*SME\s*$', '', name)
    name = re.sub(r'\s*IPO\s*$', '', name)
    
    status = None
    if "CT" in ipo_text:
        status = "Closing Today"
    elif "O" in ipo_text:
        status = "Open"
    
    return {
        'name': name.strip(),
        'type': "SME" if is_sme else "Mainboard",
        'gmp_value': gmp_value,
        'gmp_percentage': gmp_percentage,
        'status': status
    }

def display_subscription_metrics(subscription_data):
    """Display subscription metrics in a formatted way"""
    metrics = [
        ('QIB', subscription_data.get('QIB', '0.00x')),
        ('SHNI', subscription_data.get('SHNI', '0.00x')),
        ('BHNI', subscription_data.get('BHNI', '0.00x')),
        ('NII', subscription_data.get('NII', '0.00x')),
        ('RII', subscription_data.get('RII', '0.00x')),
        ('Total', subscription_data.get('Total', '0.00x'))
    ]
    
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(f"""
                <div style='background-color: #1E2329; padding: 8px; border-radius: 4px; text-align: center;'>
                    <div style='font-size: 0.8rem; font-weight: bold; color: #E2E8F0;'>{label}</div>
                    <div style='font-size: 0.9rem; color: white;'>{value}</div>
                </div>
            """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="IPO Dashboard", page_icon="🚀", layout="wide")
    
    
    st.title("🚀 Live IPO Dashboard")
    
    show_gmp_info()
    st.markdown("---")
    
    st.warning("""
    **Disclaimer:** 
    * GMP is an unofficial metric and should not be the sole basis for investment decisions. 
    * Data below is sourced from third party sources and investors should check the correctness of the data by themselves.
    * The IPOs displayed here are not investment advice.
    * Always conduct thorough research and consider multiple factors before investing in IPOs.
    """)

    # Create tabs
    tab1, tab2 = st.tabs(["🎯 GMP Details", "📊 Subscription Details"])
    
    # GMP Details Tab
    with tab1:
        if st.button("🔄 Refresh GMP Data", key="refresh_gmp"):
            st.rerun()
        
        with st.spinner("Fetching latest GMP data..."):
            df = fetch_ipo_gmp()
            
        if df.empty:
            st.error("Unable to fetch IPO data. Please try again later.")
        else:
            col1, col2, col3 = st.columns(3)
            
            processed_data = []
            for _, row in df.iterrows():
                ipo_details = parse_ipo_details(row['IPO'])
                processed_data.append({
                    **ipo_details,
                    "price": row['Price'],
                    "est_listing": row['Est Listing'],
                    "ipo_size": row['IPO Size']
                })
            
            processed_df = pd.DataFrame(processed_data)
            
            # Display in columns
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
    
    # Subscription Details Tab
    with tab2:
        # Add a refresh button
        if st.button("🔄 Refresh Subscription Data", key="refresh_sub"):
            st.rerun()
        
        # Fetch and process data
        df = fetch_subscription_data()
        if df.empty:
            st.error("Unable to fetch IPO data. Please try again later.")
        else:
            # Create two columns for different IPO statuses
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🟢 Open IPOs")
            with col2:
                st.subheader("🔔 Closing Today")
            
            # Process and display IPOs
            for _, row in df.iterrows():
                ipo_details = parse_subscription_ipo_name(row['IPO'])
                if not ipo_details['status']:
                    continue
                
                # Prepare subscription data
                subscription_data = {
                    'QIB': row.get('QIB', '0.00x'),
                    'SHNI': row.get('SHNI', '0.00x'),
                    'BHNI': row.get('BHNI', '0.00x'),
                    'NII': row.get('NII', '0.00x'),
                    'RII': row.get('RII', '0.00x'),
                    'Total': row.get('Total', '0.00x')
                }
                
                # Select display column based on status
                display_col = col1 if ipo_details['status'] == "Open" else col2
                
                with display_col:
                    st.markdown(f"""
                        <div class='ipo-card'>
                            <div class='ipo-title'>{ipo_details['name']} ({ipo_details['type']})</div>
                            <div class='ipo-detail'><strong>Price:</strong> ₹{row['IPO Price']}</div>
                            <div class='ipo-detail'><strong>Size:</strong> {row['IPO Size']}</div>
                            <div class='ipo-detail'><strong>GMP:</strong> ₹{ipo_details['gmp_value']} ({ipo_details['gmp_percentage']})</div>
                            <div class='ipo-detail'><strong>P/E:</strong> {row.get('P/E', 'N/A')}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**Subscription Status:**")
                    display_subscription_metrics(subscription_data)
                    
                    st.markdown(f"""
                        <div class='closing-date'>
                            🗓️ Closes: {row['Close Date']}
                        </div>
                    """, unsafe_allow_html=True)
                    st.divider()
    
    st.markdown("---")
    st.markdown("Data Source: www.investorgain.com")
    st.markdown(f"*Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} IST*")

if __name__ == "__main__":
    main()