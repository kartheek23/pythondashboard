# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# Set up Streamlit page
st.set_page_config(page_title="Options Dashboard", layout="wide")
st.title("📊 Options Trading Market Dashboard")

# Function to get Nifty index data
def get_index_data():
    nifty = yf.Ticker("^NSEI")
    hist = nifty.history(period="5d")
    return hist

# Function to get India VIX data
def get_vix_data():
    vix = yf.Ticker("^INDIAVIX")
    return vix.history(period="5d")

# Function to get Option Chain from NSE
def get_nifty_option_chain():
    url = "https://www.nseindia.com/option-chain"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/"
    }
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    res = session.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY", headers=headers)
    data = res.json()['records']['data']

    records = []
    for row in data:
        ce = row.get('CE')
        pe = row.get('PE')
        if ce and pe:
            records.append({
                'strikePrice': ce['strikePrice'],
                'CE_OI': ce['openInterest'],
                'PE_OI': pe['openInterest'],
                'CE_ChngOI': ce['changeinOpenInterest'],
                'PE_ChngOI': pe['changeinOpenInterest']
            })
    return pd.DataFrame(records)

# PCR & Max Pain Calculation
def calculate_pcr(df):
    return round(df['PE_OI'].sum() / df['CE_OI'].sum(), 2)

def find_max_pain(df):
    df['pain'] = df['CE_OI'] + df['PE_OI']
    return df.loc[df['pain'].idxmin(), 'strikePrice']

# 1. Index Overview
st.subheader("Nifty 50")
nifty_data = get_index_data()
st.metric("Last Close", f"{nifty_data['Close'][-1]:.2f}")
st.plotly_chart(px.line(nifty_data, y="Close", title="Nifty 50 - Last 5 Days"), use_container_width=True)

# 2. India VIX
st.subheader("India VIX")
vix_data = get_vix_data()
st.metric("Current VIX", f"{vix_data['Close'][-1]:.2f}")
st.line_chart(vix_data["Close"])

# 3. Option Chain
st.subheader("Nifty Option Chain")
try:
    df_oi = get_nifty_option_chain()
    st.dataframe(df_oi)
except Exception as e:
    st.error("Option chain load failed: " + str(e))

# 4. PCR and Max Pain
st.subheader("📌 Market Sentiment")
try:
    pcr = calculate_pcr(df_oi)
    max_pain = find_max_pain(df_oi)
    st.metric("Put/Call Ratio (PCR)", pcr)
    st.metric("Max Pain Strike", max_pain)
except:
    st.warning("Unable to compute PCR or Max Pain")

# 5. Suggested Strategy
st.subheader("🧠 Strategy Suggestions")
vix_val = vix_data['Close'][-1]
if vix_val > 18:
    st.warning("High volatility: Consider credit spreads or iron condors.")
elif vix_val < 13:
    st.info("Low volatility: Consider buying options or debit spreads.")
else:
    st.info("Moderate volatility: Range-bound strategies like short straddles/strangles might work.")

st.caption("Built with 💡 by ChatGPT")