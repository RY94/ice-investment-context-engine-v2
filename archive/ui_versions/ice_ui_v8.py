import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile, os

# --------- Expanded Subgraph ---------
edges = [
    ("NVDA", "TSMC", "depends_on"),
    ("TSMC", "China", "manufactures_in"),
    ("China", "Export Controls", "imposes"),
    ("Export Controls", "Advanced Chips", "targets"),
    ("Advanced Chips", "Data Center Revenue", "drives"),
    ("Data Center Revenue", "NVDA", "linked_to"),
    ("NVDA", "OEMs", "sells_to"),
    ("OEMs", "Chinese Consumers", "serves"),
    ("Chinese Consumers", "Spending Slowdown", "affected_by"),
    ("Spending Slowdown", "NVDA", "pressures")
]
G = nx.MultiDiGraph()
for u, v, l in edges:
    G.add_edge(u, v, label=l)

def draw_subgraph(ticker):
    sub = nx.ego_graph(G, ticker, radius=3, center=True, undirected=False)
    net = Network(height="400px", width="100%", directed=True)
    for u, v, d in sub.edges(data=True):
        net.add_node(u)
        net.add_node(v)
        net.add_edge(u, v, label=d["label"])
    path = os.path.join(tempfile.gettempdir(), "nvda_graph.html")
    net.write_html(path)
    return path

# --------- UI Layout ---------
st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question", value="Why is NVDA at risk from China trade?")
if st.button("Submit"):
    st.write("**Answer:** NVDA relies on TSMC, which manufactures in China. Export controls on advanced chips risk impacting NVDA’s data center revenue. Consumer-side demand also faces macro pressure.")
    st.markdown("**Citations:** Nvidia 10-Q, China Policy Reports, TSMC Supply Chain Disclosure")

# Portfolio Brief
st.subheader("📬 Daily Portfolio Brief")
portfolio = pd.DataFrame([
    {"Ticker": "TSMC", "Timestamp": "2025-08-02", "What Changed": "Export control risks", "Soft Signal": "Insider selling", "Sources": "SEC"},
    {"Ticker": "AAPL", "Timestamp": "2025-08-02", "What Changed": "iPhone sales miss", "Soft Signal": "Retail downgrade", "Sources": "Bloomberg"},
    {"Ticker": "MSFT", "Timestamp": "2025-08-02", "What Changed": "Azure growth slows", "Soft Signal": "Hiring freeze", "Sources": "Earnings"},
    {"Ticker": "GOOGL", "Timestamp": "2025-08-02", "What Changed": "Ad revenue down", "Soft Signal": "Insider trading", "Sources": "10-Q"},
    {"Ticker": "AMZN", "Timestamp": "2025-08-02", "What Changed": "Prime sign-ups slow", "Soft Signal": "Social complaints", "Sources": "WSJ"},
    {"Ticker": "META", "Timestamp": "2025-08-02", "What Changed": "Engagement drops", "Soft Signal": "Influencer exits", "Sources": "CNBC"},
    {"Ticker": "NFLX", "Timestamp": "2025-08-02", "What Changed": "Churn spikes", "Soft Signal": "Negative sentiment", "Sources": "JPM"},
    {"Ticker": "DIS", "Timestamp": "2025-08-02", "What Changed": "Streaming revenue dips", "Soft Signal": "Exec exit", "Sources": "FT"},
    {"Ticker": "AMD", "Timestamp": "2025-08-02", "What Changed": "Inventory build", "Soft Signal": "Channel checks weak", "Sources": "Analyst Note"},
    {"Ticker": "CRM", "Timestamp": "2025-08-02", "What Changed": "APAC churn", "Soft Signal": "NPS drop", "Sources": "Zendesk"},
])
st.dataframe(portfolio)

# Watchlist Brief
st.subheader("👁 Watchlist Brief")
watchlist = pd.DataFrame([
    {"Ticker": "NVDA", "Timestamp": "2025-08-02", "What Changed": "China export risk", "Soft Signal": "Whale options", "Sources": "10-Q"},
    {"Ticker": "BABA", "Timestamp": "2025-08-02", "What Changed": "New China regulations", "Soft Signal": "Short spike", "Sources": "Weibo"},
    {"Ticker": "TSLA", "Timestamp": "2025-08-02", "What Changed": "Recall issued", "Soft Signal": "Sentiment down", "Sources": "Reddit"},
    {"Ticker": "UBER", "Timestamp": "2025-08-02", "What Changed": "Driver protest", "Soft Signal": "Churn up", "Sources": "Call"},
    {"Ticker": "SHOP", "Timestamp": "2025-08-02", "What Changed": "Platform outages", "Soft Signal": "Dev complaints", "Sources": "Blog"},
    {"Ticker": "SNOW", "Timestamp": "2025-08-02", "What Changed": "Cloud demand down", "Soft Signal": "Layoffs", "Sources": "FT"},
    {"Ticker": "PLTR", "Timestamp": "2025-08-02", "What Changed": "Contract delays", "Soft Signal": "Slack mentions down", "Sources": "Gov DB"},
    {"Ticker": "COIN", "Timestamp": "2025-08-02", "What Changed": "SEC pressure", "Soft Signal": "Insider sales", "Sources": "Reddit"},
    {"Ticker": "RBLX", "Timestamp": "2025-08-02", "What Changed": "User drop", "Soft Signal": "Influencer backlash", "Sources": "YT"},
    {"Ticker": "LYFT", "Timestamp": "2025-08-02", "What Changed": "Lost contract", "Soft Signal": "Driver feedback", "Sources": "Notes"},
])
st.dataframe(watchlist)

# Subgraph Viewer
st.subheader("🕸️ Expanded Subgraph – NVDA and China Trade")
html_path = draw_subgraph("NVDA")
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
components.html(html, height=400, scrolling=True)

# Email Input
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
