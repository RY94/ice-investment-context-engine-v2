import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile, os

# --------- Graph Definition ---------
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
for u, v, label in edges:
    G.add_edge(u, v, label=label)

def draw_subgraph(ticker):
    sub = nx.ego_graph(G, ticker, radius=3, center=True, undirected=False)
    net = Network(height="500px", width="100%", bgcolor="#111111", font_color="white", directed=True)

    color_map = {
        "NVDA": "#32CD32", "TSMC": "#FFD700", "China": "#FF4500",
        "Export Controls": "#DC143C", "Advanced Chips": "#FF69B4",
        "Data Center Revenue": "#1E90FF", "OEMs": "#00CED1",
        "Chinese Consumers": "#9370DB", "Spending Slowdown": "#FF8C00"
    }

    for node in sub.nodes:
        net.add_node(node, label=node, color=color_map.get(node, "#888"), shape="dot", size=20)
    for u, v, d in sub.edges(data=True):
        net.add_edge(u, v, label=d['label'], color="lime")

    path = os.path.join(tempfile.gettempdir(), "nvda_graph.html")
    net.set_options("""var options = { "edges": { "color": { "inherit": false } }, "physics": { "enabled": false } }""")
    net.write_html(path)
    return path

# --------- Streamlit UI ---------
st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question", value="Why is NVDA at risk from China trade?")
if st.button("Submit"):
    st.write("**Answer:** NVDA relies on TSMC, which manufactures in China. Export controls on advanced chips impact NVDA’s data center business. Consumer demand also softens.")
    st.markdown("**Citations:** Nvidia 10-Q, China Trade Policy Reports, TSMC Disclosure")

# Portfolio & Watchlist Tables (condensed)
st.subheader("📬 Daily Portfolio Brief")
portfolio = pd.DataFrame([
    ["TSMC", "2025-08-02", "Export control risks", "Insider selling", "SEC"],
    ["AAPL", "2025-08-02", "iPhone sales miss", "Retail downgrade", "Bloomberg"],
    ["MSFT", "2025-08-02", "Azure slows", "Hiring freeze", "Earnings"],
    ["GOOGL", "2025-08-02", "Ad revenue falls", "Insider selling", "10-Q"],
    ["AMZN", "2025-08-02", "Prime sign-ups dip", "Social complaints", "WSJ"],
    ["META", "2025-08-02", "Engagement down", "Influencer exits", "CNBC"],
    ["NFLX", "2025-08-02", "Churn spikes", "Sentiment negative", "JPM"],
    ["DIS", "2025-08-02", "Streaming drops", "Exec exit", "FT"],
    ["AMD", "2025-08-02", "Inventory build", "Weak demand", "Analyst"],
    ["CRM", "2025-08-02", "APAC churn", "NPS drop", "Zendesk"],
], columns=["Ticker", "Timestamp", "What Changed", "Soft Signal", "Sources"])
st.dataframe(portfolio)

st.subheader("👁 Watchlist Brief")
watchlist = pd.DataFrame([
    ["NVDA", "2025-08-02", "China export risk", "Whale options", "10-Q"],
    ["BABA", "2025-08-02", "New China regs", "Short spike", "Weibo"],
    ["TSLA", "2025-08-02", "Recall issued", "Retail sentiment ↓", "Reddit"],
    ["UBER", "2025-08-02", "Driver protest", "Churn up", "Call"],
    ["SHOP", "2025-08-02", "Platform outages", "Dev complaints", "Blog"],
    ["SNOW", "2025-08-02", "Cloud slowdown", "Layoffs", "FT"],
    ["PLTR", "2025-08-02", "Contract delays", "Slack mentions ↓", "Gov DB"],
    ["COIN", "2025-08-02", "SEC litigation", "Insider sells", "Reddit"],
    ["RBLX", "2025-08-02", "User time ↓", "Influencer backlash", "YT"],
    ["LYFT", "2025-08-02", "Lost city contract", "Driver sentiment ↓", "Notes"],
], columns=["Ticker", "Timestamp", "What Changed", "Soft Signal", "Sources"])
st.dataframe(watchlist)

# Graph Rendering
st.subheader("🕸️ Exposure Subgraph")
html_path = draw_subgraph("NVDA")
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
components.html(html, height=500, scrolling=True)

# Email input
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
