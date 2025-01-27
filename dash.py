import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re, json

# Common utility functions
def format_price(price):
    """Format price with ₹ symbol"""
    try:
        return f"₹{float(price):,.2f}"
    except:
        return price

# GMP Tab Functions
def fetch_ipo_gmp():
    """Fetch IPO data from investorgain.com and process it."""
    url = "https://webnodejs.investorgain.com/cloud/report/data-read/331/1/1/2025/2024-25/0/all?search="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }
    
    try:
        # Fetch the data
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return pd.DataFrame()
        
        # Parse the JSON response
        data = json.loads(response.text)
        table_data = data.get("reportTableData", [])
        if not table_data:
            return pd.DataFrame()

        # Create a DataFrame
        df = pd.DataFrame(table_data)
        if df.empty:
            return df

        # Function to clean HTML from text
        def clean_html(text):
            return BeautifulSoup(text, "html.parser").get_text() if text else text

        # Clean specific columns
        columns_to_clean = ["Status", "GMP", "Est Listing", "IPO Size", "Fire Rating"]
        for col in columns_to_clean:
            if col in df:
                df[col] = df[col].apply(clean_html)

        # Keep relevant columns
        columns_to_keep = ["IPO", "Status","Price","IPO Size", "Est Listing", "~Str_Listing", "~IPO_Category"]
        df = df[columns_to_keep]

        # Filter rows by status
        df = df[df['Status'].str.contains("Upcoming|Open|Closing Today", case=False)]

        return df

    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return pd.DataFrame()


# Updated parse_ipo_details function
def parse_ipo_details(ipo_text, status_text):
    """
    Parse IPO text to extract name, type, status, and subscription details.
    
    Args:
        ipo_text (str): The text in the 'IPO' column.
        status_text (str): The text in the 'Status' column.
    
    Returns:
        dict: A dictionary containing parsed IPO details.
    """
    # Extract IPO type
    ipo_type = "SME" if "SME" in ipo_text else "Mainboard"
    
    # Extract status from the 'Status' column
    status = status_text.strip()
    
    # Extract subscription details (if available in the status text)
    sub_match = re.search(r'Sub:(\d+\.?\d*x)', status_text)
    sub_times = sub_match.group(1) if sub_match else "N.A."
    
    # Extract IPO name
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
    """Fetch additional IPO data from investorgain.com and process it."""
    url = "https://webnodejs.investorgain.com/cloud/report/data-read/333/1/1/2025/2024-25/0/all?search="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }
    
    try:
        # Fetch the data
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return pd.DataFrame()

        # Parse the JSON response
        #print(response.text)
        data = json.loads(response.text)
        table_data = data.get("reportTableData", [])
        if not table_data:
            return pd.DataFrame()

        # Create a DataFrame
        df = pd.DataFrame(table_data)
        if df.empty:
            return df

        # Function to clean HTML from text
        def clean_html(text):
            return BeautifulSoup(text, "html.parser").get_text() if text else text

        # Clean specific columns
        columns_to_clean = ["Status", "GMP", "IPO Price", "IPO Size", "Total"]
        for col in columns_to_clean:
            if col in df:
                df[col] = df[col].apply(clean_html)

        # Keep relevant columns
        columns_to_keep = ["IPO", "IPO Price", "IPO Size", "Status", "QIB","SHNI","BHNI","NII","RII","Total", "Close Date", "~IPO_Category"]
        df = df[columns_to_keep]

        # Filter rows by status
        df = df[df['Status'].str.contains("O|CT", case=False)]

        return df

    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

def parse_subscription_ipo_name(ipo_text, status_text):
    """Parse IPO text for subscription data"""
    # Extract GMP details if available
    gmp_match = re.search(r'GMP:\$(\d+)\s*\(([^)]+)\)', ipo_text)
    gmp_value = gmp_match.group(1) if gmp_match else 'N/A'
    gmp_percentage = gmp_match.group(2) if gmp_match else 'N/A'
    
    # Determine IPO type (SME or Mainboard)
    is_sme = "SME" in ipo_text
    name = ipo_text.split("GMP")[0].strip()
    name = re.sub(r'\s*SME\s*$', '', name)
    name = re.sub(r'\s*IPO\s*$', '', name)
    
    # Map status codes to their corresponding statuses
    status_mapping = {
        'O': 'Open',
        'C': 'Closed',
        'CT': 'Closing Today',  # If "CT" is used for "Closing Today"
        # Add more mappings if needed
    }
    
    # Extract status from the 'Status' column and map it
    status_code = status_text.strip()
    status = status_mapping.get(status_code, status_code)  # Default to the code if not mapped
    
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
            col1, col2, col3 = st.columns(3, gap='medium')
            
            # Process the DataFrame
            processed_data = []
            for _, row in df.iterrows():
                ipo_details = parse_ipo_details(row['IPO'], row['Status'])
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
                upcoming = processed_df[processed_df['status'].str.contains("Upcoming")]
                if upcoming.empty:
                    st.info("No upcoming IPOs at the moment")
                else:
                    for _, ipo in upcoming.iterrows():
                        with st.container():
                            st.markdown(f"""
                            ### {ipo['name']}
                            **Type:** {ipo['type']}  
                            **Price:** {ipo['price']}  
                            **Issue Size:** {ipo['ipo_size']}  
                            <div class='listing-date'>🗓️ Expected Listing: {ipo['est_listing']}</div>
                            """, unsafe_allow_html=True)
                            st.divider()
            
            with col2:
                st.subheader("🟢 Open IPOs")
                open_ipos = processed_df[processed_df['status'].str.contains("Open")]
                if open_ipos.empty:
                    st.info("No IPOs open for subscription")
                else:
                    for _, ipo in open_ipos.iterrows():
                        with st.container():
                            st.markdown(f"""
                            ### {ipo['name']}
                            **Type:** {ipo['type']}  
                            **Price:** {ipo['price']}  
                            **Subscription:** {ipo['subscription']}  
                            **Issue Size:** {ipo['ipo_size']}  
                            <div class='listing-date'>🗓️ Expected Listing: {ipo['est_listing']}</div>
                            """, unsafe_allow_html=True)
                            st.divider()
            
            with col3:
                st.subheader("🔔 Closing Today")
                closing = processed_df[processed_df['status'].str.contains("Closing Today")]
                if closing.empty:
                    st.info("No IPOs closing today")
                else:
                    for _, ipo in closing.iterrows():
                        with st.container():
                            st.markdown(f"""
                            ### {ipo['name']}
                            **Type:** {ipo['type']}  
                            **Price:** {ipo['price']}  
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
            # Display a single column titled "Current IPOs"
            st.subheader("📊 Current IPOs")
            
            # Process and display IPOs
            for _, row in df.iterrows():
                ipo_details = parse_subscription_ipo_name(row['IPO'], row['Status'])
                if not ipo_details['status']:
                    continue
                
                # Prepare subscription data
                subscription_data = {
                    'QIB': row.get('QIB', '0.00x'),
                    'SHNI': row.get('SHNI', '0.00x'),
                    'NII': row.get('NII', '0.00x'),
                    'RII': row.get('RII', '0.00x'),
                    'Total': row.get('Total', '0.00x')
                }
                
                # Display IPO details in a single column
                with st.container():
                    # Extract numbers and percentage using regex
                    matches = re.findall(r'\d+\.\d+|\d+', ipo_details['status'])

                    # Format the extracted numbers as "115(43.73%)"
                    result = f"{matches[0]}({matches[1]}%)"
                    st.markdown(f"""
                        <div class='ipo-card'>
                            <div class='ipo-title'>{ipo_details['name']} ({ipo_details['type']})</div>
                            <div class='ipo-detail'><strong>Price:</strong> ₹{row['IPO Price']}</div>
                            <div class='ipo-detail'><strong>Size:</strong> {row['IPO Size']}</div>
                            <div class='ipo-detail'><strong>GMP:</strong> ₹{result}</div>
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
    st.markdown(f"*Last updated: {(pd.Timestamp.now() + pd.Timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')} IST*")

if __name__ == "__main__":
    main()