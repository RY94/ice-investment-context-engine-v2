import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile, os

# ----------- Graph Setup -----------
edges = [
    ("NVDA", "TSMC", "depends_on"),
    ("TSMC", "China", "manufactures_in"),
    ("China", "Export Restrictions", "faces"),
    ("Export Restrictions", "NVDA", "risks"),
    ("NVDA", "Data Center Chips", "sells"),
    ("Data Center Chips", "China", "exposed_to")
]
G = nx.MultiDiGraph()
for u, v, l in edges:
    G.add_edge(u, v, label=l)

def draw_subgraph(ticker):
    sub = G.subgraph({n for e in G.edges() for n in e if ticker in e})
    net = Network(height="300px", width="100%", directed=True)
    for u, v, d in sub.edges(data=True):
        net.add_node(u)
        net.add_node(v)
        net.add_edge(u, v, label=d['label'])
    path = os.path.join(tempfile.gettempdir(), "graph.html")
    net.write_html(path)
    return path

# ----------- UI -----------
st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question", value="Why is NVDA at risk from China trade?")
if st.button("Submit"):
    st.write("**Answer:** NVDA depends on TSMC, which manufactures in China. Export restrictions and demand risks expose NVDA's data center chip revenue.")
    st.markdown("**Citations:** TSMC Supply Chain Report, Nvidia 10-Q, China Trade Policy")

# Portfolio + Watchlist
portfolio = pd.DataFrame([{
    "Ticker": "TSMC", "Timestamp": "2025-08-02", "What Changed": "China exposure risk", "Soft Signal": "Insider sell", "Sources": "SEC"
}])
watchlist = pd.DataFrame([{
    "Ticker": "NVDA", "Timestamp": "2025-08-02", "What Changed": "Margin compression; export tension", "Soft Signal": "Options volume", "Sources": "BAML"
}])

st.subheader("📬 Daily Portfolio Brief")
st.dataframe(portfolio)

st.subheader("👁 Watchlist Brief")
st.dataframe(watchlist)

# Subgraph
st.subheader("🕸️ Subgraph for NVDA – China Exposure")
html_path = draw_subgraph("NVDA")
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
components.html(html, height=300, scrolling=True)

# Email placeholder
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
