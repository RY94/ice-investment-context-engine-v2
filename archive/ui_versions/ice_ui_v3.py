import streamlit as st
import pandas as pd

st.set_page_config(page_title="ICE – Investment Context Engine", layout="wide")
st.title("🧊 ICE – Investment Context Engine")
st.subheader("🔍 Ask ICE a Question")

query = st.text_input("Your Question", placeholder="e.g., Why did TSMC drop yesterday?")
if st.button("Submit"):
    st.write("**Answer:** TSMC declined 3.2% due to renewed U.S.-China export control fears...")
    st.markdown("**Citations:** [Nvidia call](#), [Bloomberg](#)")
    st.markdown("**Reasoning Graph Preview:** `TSMC → exposed_to → Nvidia → exposed_to → China risk`")

# Sample portfolio data
portfolio_data = [
    {"Ticker": "TSMC", "Timestamp": "2025-08-02", "What Changed": "US export controls affect chip exports", "Soft Signal": "CFO selling", "Sources": "SEC, JPM"},
    {"Ticker": "AAPL", "Timestamp": "2025-08-02", "What Changed": "iPhone sales miss in China", "Soft Signal": "Retail downgrades", "Sources": "Bloomberg, WSJ"},
    {"Ticker": "MSFT", "Timestamp": "2025-08-02", "What Changed": "Azure growth slows", "Soft Signal": "Job postings drop", "Sources": "Earnings, CNBC"},
    {"Ticker": "AMZN", "Timestamp": "2025-08-02", "What Changed": "Prime sign-ups down YoY", "Soft Signal": "Social media complaints rise", "Sources": "Call, Reddit"},
    {"Ticker": "GOOGL", "Timestamp": "2025-08-02", "What Changed": "Ad revenue headwinds", "Soft Signal": "Insider selling", "Sources": "10-Q, FT"},
    {"Ticker": "META", "Timestamp": "2025-08-02", "What Changed": "Instagram engagement drops", "Soft Signal": "Influencer exits", "Sources": "Bloomberg"},
    {"Ticker": "NFLX", "Timestamp": "2025-08-02", "What Changed": "Weak international growth", "Soft Signal": "Subscriber churn uptick", "Sources": "Earnings, JPM"},
    {"Ticker": "NVDA", "Timestamp": "2025-08-02", "What Changed": "Margin pressure", "Soft Signal": "Options volume spike", "Sources": "10-Q, BAML"},
    {"Ticker": "DIS", "Timestamp": "2025-08-02", "What Changed": "Disney+ subscriber decline", "Soft Signal": "Talent exodus", "Sources": "CNBC, WSJ"},
    {"Ticker": "AMD", "Timestamp": "2025-08-02", "What Changed": "Inventory build-up", "Soft Signal": "Channel checks weak", "Sources": "Analyst note"},
]
portfolio_df = pd.DataFrame(portfolio_data)

# Sample watchlist data
watchlist_data = [
    {"Ticker": "BABA", "Timestamp": "2025-08-02", "What Changed": "New Chinese regulations", "Soft Signal": "Short interest spikes", "Sources": "Reuters, Weibo"},
    {"Ticker": "TSLA", "Timestamp": "2025-08-02", "What Changed": "Recall notice filed", "Soft Signal": "Retail sentiment dive", "Sources": "SEC, X"},
    {"Ticker": "UBER", "Timestamp": "2025-08-02", "What Changed": "Driver protests in key cities", "Soft Signal": "Churn rate up", "Sources": "Call summary"},
    {"Ticker": "SHOP", "Timestamp": "2025-08-02", "What Changed": "Platform outages", "Soft Signal": "Developer complaints", "Sources": "Blog, Hacker News"},
    {"Ticker": "SNOW", "Timestamp": "2025-08-02", "What Changed": "Slowing cloud adoption", "Soft Signal": "Sales team layoffs", "Sources": "FT, Layoffs.fyi"},
    {"Ticker": "PLTR", "Timestamp": "2025-08-02", "What Changed": "Gov contract delayed", "Soft Signal": "Slack mentions drop", "Sources": "Gov DB"},
    {"Ticker": "COIN", "Timestamp": "2025-08-02", "What Changed": "SEC litigation risk rises", "Soft Signal": "Insider stock sales", "Sources": "SEC, Reddit"},
    {"Ticker": "RBLX", "Timestamp": "2025-08-02", "What Changed": "User time spent falls", "Soft Signal": "Influencer backlash", "Sources": "YT, Discord"},
    {"Ticker": "LYFT", "Timestamp": "2025-08-02", "What Changed": "Loses city contract", "Soft Signal": "Driver sentiment negative", "Sources": "Call, HR data"},
    {"Ticker": "CRM", "Timestamp": "2025-08-02", "What Changed": "Customer churn in APAC", "Soft Signal": "NPS drop", "Sources": "Zendesk, Report"},
]
watchlist_df = pd.DataFrame(watchlist_data)

# Display tables
st.subheader("📬 Daily Portfolio Brief")
st.dataframe(portfolio_df)

st.subheader("👁 Watchlist Brief")
st.dataframe(watchlist_df)

# Email section
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
