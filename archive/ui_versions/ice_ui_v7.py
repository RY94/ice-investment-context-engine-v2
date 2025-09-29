import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile, os

# --------- Expanded Subgraph Definition ---------
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
    path = os.path.join(tempfile.gettempdir(), "nvda_subgraph.html")
    net.write_html(path)
    return path

# --------- UI ---------
st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question", value="Why is NVDA at risk from China trade?")
if st.button("Submit"):
    st.write("**Answer:** NVDA relies on TSMC for advanced chips made in China. Export restrictions targeting these chips threaten NVDA's data center revenue. OEM demand from Chinese consumers is also under pressure due to macro slowdown.")
    st.markdown("**Citations:** Nvidia 10-Q, TSMC Supply Chain Disclosure, Reuters China Trade Policy")

# Portfolio & Watchlist
portfolio = pd.DataFrame([{
    "Ticker": "TSMC", "Timestamp": "2025-08-02", "What Changed": "Export risk", "Soft Signal": "Insider selling", "Sources": "SEC"
}])
watchlist = pd.DataFrame([{
    "Ticker": "NVDA", "Timestamp": "2025-08-02", "What Changed": "China policy exposure", "Soft Signal": "Options spike", "Sources": "10-Q"
}])
st.subheader("📬 Daily Portfolio Brief")
st.dataframe(portfolio)

st.subheader("👁 Watchlist Brief")
st.dataframe(watchlist)

# Expanded Subgraph Render
st.subheader("🕸️ Expanded Subgraph – NVDA and China Trade")
html_path = draw_subgraph("NVDA")
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
components.html(html, height=400, scrolling=True)

# Email
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
