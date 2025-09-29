import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile, os

# --------- Subgraph Setup ---------
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

# --------- 1. Q&A Section ---------
st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question", value="Why is NVDA at risk from China trade?")
if st.button("Submit"):
    st.markdown("### 💡 ICE Answer")
    st.write(
        "Nvidia (NVDA) is exposed to China-related trade risks via both supply and demand channels.\n\n"
        "- **Supply-side**: NVDA relies on TSMC, which manufactures advanced chips in China. U.S. export controls targeting these chips directly constrain TSMC’s ability to fulfill high-end GPU orders.\n"
        "- **Demand-side**: NVDA’s key OEM partners serve Chinese enterprise and consumer markets. Recent signs of spending slowdown, combined with policy uncertainty, suggest softening end demand.\n"
        "- **Revenue Impact**: Data Center segment, NVDA’s fastest-growing business line, is most vulnerable.\n"
    )
    st.markdown("**🧾 Sources**")
    st.markdown(
        "- TSMC Supply Chain Report (2025 Q2)\n"
        "- Nvidia 10-Q filing (July 2025)\n"
        "- Reuters: 'China to expand chip export curbs' (2025-07-29)\n"
        "- JPM Tech Desk Note: 'OEM Orderbook Compression' (2025-08-01)"
    )
    st.markdown("**🧠 Reasoning Chain**")
    st.code("NVDA → TSMC → China → Export Controls → Advanced Chips → Data Center Revenue → NVDA")

# --------- 2. Subgraph ---------
st.subheader("🕸️ Exposure Subgraph – Ticker-in-Question")
html_path = draw_subgraph("NVDA")
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
components.html(html, height=500, scrolling=True)

# --------- 3. Daily Portfolio Brief ---------
st.subheader("📬 Daily Portfolio Brief")
portfolio = pd.DataFrame([
    {
        "Ticker": "NVDA", "Name": "Nvidia", "Sector": "Semis", "Alert Priority": 92,
        "What Changed": "Export curbs expanded → Data center GPU slowdown (cited)",
        "Top Causal Path": "NVDA → TSMC → China Risk (3 src)",
        "Themes": "AI infra • .8 • 2d | China policy • .6 • 1d",
        "KPIs": "Gross margin • 1d | Datacenter Rev • 2d",
        "Soft Signal": "⚠️ mgmt cautious on China", "Recency": "6h", "Confidence": "0.91 (3 src)"
    },
    {
        "Ticker": "AAPL", "Name": "Apple", "Sector": "Consumer Tech", "Alert Priority": 76,
        "What Changed": "iPhone SE delays → Q3 topline risk (cited)",
        "Top Causal Path": "AAPL → Foxconn → China lockdown (2 src)",
        "Themes": "Consumer sentiment • .7 • 3d", "KPIs": "Unit sales • 2d",
        "Soft Signal": "⚠️ weak Asia demand flagged", "Recency": "18h", "Confidence": "0.82 (2 src)"
    },
    {
        "Ticker": "TSMC", "Name": "Taiwan Semi", "Sector": "Semis", "Alert Priority": 88,
        "What Changed": "China export curbs → capacity rerouting (cited)",
        "Top Causal Path": "TSMC → China Risk → Export Controls (4 src)",
        "Themes": "Supply chain • .9 • 1d | Trade war • .6 • 1d",
        "KPIs": "CapEx • 1d", "Soft Signal": "⚠️ geopolitical warnings in earnings call",
        "Recency": "9h", "Confidence": "0.94 (4 src)"
    }
])
st.dataframe(portfolio, use_container_width=True)

# --------- 4. Watchlist Brief ---------
st.subheader("👁 Watchlist Brief – ICE Alert Format")
watchlist = pd.DataFrame([
    {
        "Ticker": "COIN", "Name": "Coinbase", "Sector": "Crypto", "Alert Priority": 81,
        "What Changed": "SEC lawsuit update → Trading fee model risk (cited)",
        "Top Causal Path": "COIN → SEC Action → Fee Revenue (2 src)",
        "Themes": "Regulatory overhang • .7 • 1d", "KPIs": "Volume • 2d",
        "Soft Signal": "⚠️ legal risk flagged in internal memo", "Recency": "14h", "Confidence": "0.85 (2 src)"
    },
    {
        "Ticker": "RBLX", "Name": "Roblox", "Sector": "Gaming", "Alert Priority": 73,
        "What Changed": "DAU plateauing → User fatigue (cited)",
        "Top Causal Path": "RBLX → DAU Trend → Engagement Risk (3 src)",
        "Themes": "Consumer apps • .6 • 2d", "KPIs": "DAU • 1d | ARPU • 3d",
        "Soft Signal": "⚠️ usage down in Asia cohort", "Recency": "10h", "Confidence": "0.78 (3 src)"
    },
    {
        "Ticker": "BABA", "Name": "Alibaba", "Sector": "China E-com", "Alert Priority": 87,
        "What Changed": "New export regs → Logistics bottleneck (cited)",
        "Top Causal Path": "BABA → CN Exports → Q3 Revenue Risk (4 src)",
        "Themes": "China macro • .9 • 1d | Logistics • .7 • 2d",
        "KPIs": "Rev growth • 1d | Delivery time • 2d",
        "Soft Signal": "⚠️ mgmt guided lower on earnings call", "Recency": "5h", "Confidence": "0.92 (4 src)"
    }
])
st.dataframe(watchlist, use_container_width=True)

# --------- 5. Email Input ---------
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
