### ice_ui.py

import streamlit as st

st.set_page_config(page_title="ICE – Investment Context Engine", layout="wide")

st.title("🧊 ICE – Investment Context Engine")
st.subheader("Daily Briefing & On-Demand Equity Intelligence")

# Section: Ask ICE a Question
st.markdown("### 🔍 Ask ICE a Question")
query = st.text_input("Enter your equity-related question:", placeholder="e.g., Why did TSMC drop yesterday?")
if st.button("Submit"):
    st.markdown("**Answer:**")
    st.success("TSMC declined 3.2% due to renewed U.S.-China export control fears, as highlighted during Nvidia’s earnings call and a Bloomberg report citing downstream supply risks.")
    st.markdown("**Citations:**")
    st.markdown("- [Nvidia Q2 Earnings Call](#)\n- [Bloomberg – 2025/07/31](#)")
    st.markdown("**Reasoning Graph Preview:**\n\n`TSMC → exposed_to → Nvidia → exposed_to → China policy risk`")

# Section: Daily Portfolio Brief
st.markdown("### 📬 Daily Portfolio Brief")
ticker = st.selectbox("Select Ticker", ["AAPL", "TSMC", "NVDA"])
if ticker:
    st.markdown("**🕒 Timestamp:** 2025-08-02 07:00 AM")
    st.markdown("**🗞️ What changed:**")
    st.info("TSMC faces increased geopolitical risks from new U.S. export controls. NVDA commentary suggests near-term demand pullback. Sector-wide downgrades from JPM Tech Desk.")
    st.markdown("**🔍 Soft Signal Highlight:**\n- Increased short volume reported on TSMC\n- CFO insider selling reported 48 hours ago")
    st.markdown("**🔗 Source Links:**\n- [SEC 8-K filing – 2025/08/01](#)\n- [Nvidia Earnings Transcript](#)\n- [JPM Sector Note (summary)](#)")

slack_push = st.checkbox("📦 Push summary to Slack")

# Footer
st.markdown("---")
st.caption("ICE is an internal AI research assistant. Always verify insights with primary sources before trading.")
