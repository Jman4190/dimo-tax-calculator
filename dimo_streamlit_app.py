import streamlit as st
import requests
import json
from datetime import datetime
import time
import csv
from io import StringIO

#DIMO Token Address
DIMO_TOKEN_ADDRESS = "0xe261d618a959afffd53168cd07d12e37b26761db" 

# Function to fetch historical price of $DIMO from CoinGecko
# note the header should be modified for non demo API keys
def fetch_historical_price(coingecko_api_key, date):
    base_url = "https://api.coingecko.com/api/v3/coins/dimo/history"
    headers = {
        'x-cg-demo-api-key': coingecko_api_key
    }
    params = {
        "date": date,  # Date in format 'dd-mm-yyyy'
        "localization": "false"
    }
    response = requests.get(base_url, params=params, headers=headers)
    time.sleep(4)  # Add a delay to avoid hitting rate limits
    if response.status_code == 200:
        price_data = response.json()
        return price_data.get('market_data', {}).get('current_price', {}).get('usd')
    else:
        st.error(f"Failed to fetch historical price for date {date}. Status code: {response.status_code}")
        return None

# Function to fetch transactions for the $DIMO token
def fetch_dimo_transactions(wallet_address, polyscan_api_key, year=2023):
    base_url = f"https://api.polygonscan.com/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": DIMO_TOKEN_ADDRESS,
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": polyscan_api_key
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        error_message = f"Failed to fetch transactions. Status code: {response.status_code}\nRaw Response: {response.text}"
        st.error(error_message)  # Corrected error handling
        return None
    
    try:
        transactions = json.loads(response.text).get("result", [])
        
        return [tx for tx in transactions if datetime.fromtimestamp(int(tx["timeStamp"])).year == year]
    except Exception as e:
        error_message = f"Error in parsing transactions: {e}"
        st.error(error_message)
        return None

# function to process each historical transaction
def process_transactions(transactions, coingecko_api_key):
    total_value = 0
    transaction_details = []
    transaction_count = 0  # Initialize a counter for processed transactions
    
    # Create a status container that will be updated with transaction details
    status_container = st.status("Processing transactions...", expanded=False)
    
    for tx in transactions:
        timestamp = int(tx["timeStamp"])
        date = datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y')
        dimo_amount = int(tx["value"]) / (10 ** int(tx["tokenDecimal"]))  # Adjust for token decimals
        price_usd = fetch_historical_price(coingecko_api_key, date)
        
        if price_usd is not None:
            transaction_value_usd = dimo_amount * price_usd
            total_value += transaction_value_usd
            transaction_count += 1  # Increment the transaction counter
            
            # Update the status container with the new transaction detail and the number of transactions processed
            status_container.update(label=f"Processing transaction {transaction_count} of {len(transactions)}...", expanded=False)
            status_container.write(f"Processed transaction on {date}: {dimo_amount} DIMO valued at ${transaction_value_usd:.2f} USD")

            # Append transaction details to the list as a dictionary
            transaction_details.append({
                "Transaction Date": date,
                "DIMO Tokens": dimo_amount,
                "Cost Basis Value": f"${transaction_value_usd:.2f}"
            })

    # Once all transactions are processed, update the status to 'complete'
    status_container.update(label="Transactions Processed", state="complete")

    # After processing, create a CSV string
    csv_stringio = StringIO()
    writer = csv.DictWriter(csv_stringio, fieldnames=["Transaction Date", "DIMO Tokens", "Cost Basis Value"])
    writer.writeheader()
    writer.writerows(transaction_details)
    csv_string = csv_stringio.getvalue()
    csv_stringio.close()

    # fire off some fun balloons
    st.balloons()
    # display success message
    st.success(f"""Total Value of Airdropped DIMO in 2023: ${total_value:.2f} USD""", icon="✅")
    # Display the download button
    st.download_button(label="📄 Download as CSV",
                       data=csv_string,
                       file_name='dimo_transactions.csv',
                       mime='text/csv')
    

# Streamlit interface
st.title('🚗 DIMO 2023 Tax Calculator')
#st.subheader("Get help calculating your cost basis for the upcoming tax season.")
# Input for the Wallet Address
wallet_address = st.text_input("Polygon Wallet Address")

# Sidebar layout
st.sidebar.header("How to Use")
st.sidebar.markdown("""
1. Enter your Coingecko API key below 🔑
2. Enter your Polyscan API Key below 🔑
""")

# Input for the CoinGecko API Key
coingecko_api_key = st.sidebar.text_input("CoinGecko API Key", type="password")
# Input for the Polyscan API Key
polyscan_api_key = st.sidebar.text_input("Polyscan API Key", type="password")

st.sidebar.markdown("---")  # This adds a horizontal line
# About section
st.sidebar.markdown("## About")
st.sidebar.markdown("""
This tool allows you to easily track your weekly DIMO airdrops and get a 2023 cost basis for tax purposes.
You can share your feedback and suggestions on Twitter. 
                    
Made by [@learnwithjabe](https://twitter.com/learnwithjabe).
""")
st.sidebar.markdown("---")  # This adds a horizontal line
# FAQ section
st.sidebar.markdown("## FAQ")
st.sidebar.markdown("""
<h3>How do I get a Coingecko API Key?</h3>
Learn how to sign up for <a href="https://support.coingecko.com/hc/en-us/articles/21880397454233" target="_blank">CoinGecko Demo API</a> and generate an API key.<br><br>

<h3>Why does it go so slow?</h3>
Since we are using a Demo API Key, Coingecko applies rate limits. You can learn more about the rate limits <a href="https://support.coingecko.com/hc/en-us/articles/21880397454233" target="_blank">here</a>.<br><br>

<h3>How do I get a Polyscan API Key?</h3>
Learn how to sign up for <a href="https://docs.polygonscan.com/getting-started/viewing-api-usage-statistics" target="_blank">Polyscan API</a> key for free.<br><br>
""", unsafe_allow_html=True)

         
if st.button('💰 Calculate Cost Basis'):
    if not all([coingecko_api_key, wallet_address, polyscan_api_key]):
        st.warning("Please provide all required inputs.")
    else:
        st.info("Note: this may take a while because of Coingecko Demo API rate limits", icon="⌛")
        transactions = fetch_dimo_transactions(wallet_address, polyscan_api_key)
        if transactions is not None:
            process_transactions(transactions, coingecko_api_key)
        else:
            st.error("Failed to process transactions.")
