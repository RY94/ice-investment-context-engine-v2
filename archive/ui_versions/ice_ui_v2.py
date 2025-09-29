import streamlit as st
import pandas as pd

# Sample data
portfolio = pd.DataFrame([{
    "Ticker": "TSMC",
    "Timestamp": "2025-08-02 07:00 AM",
    "What Changed": "TSMC faces increased geopolitical risks... JPM Tech Desk.",
    "Soft Signal Highlight": "Short volume up; CFO selling",
    "Source Links": "SEC | Earnings | JPM"
}])

watchlist = pd.DataFrame([{
    "Ticker": "NVDA",
    "Timestamp": "2025-08-02 07:00 AM",
    "What Changed": "NVDA margin pressure; China softness",
    "Soft Signal Highlight": "Whale options; BAML downgrade",
    "Source Links": "10-Q | Call | BAML"
}])

# Ask ICE
st.title("🧊 ICE – Investment Context Engine")
st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question")
if st.button("Submit"):
    st.write("**Answer:** TSMC declined due to...")  # Mocked
    st.markdown("**Citations:** Nvidia call, Bloomberg")
    st.code("TSMC → Nvidia → China risk", language="")

# Daily Brief
st.subheader("📬 Daily Portfolio Brief")
st.dataframe(portfolio)

# Watchlist Brief
st.subheader("👁 Watchlist Brief")
st.dataframe(watchlist)

# Email Summary
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
