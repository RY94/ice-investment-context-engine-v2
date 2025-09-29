import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile, os

# ----------- Expanded Graph Setup -----------
edges = [
    ("NVDA", "TSMC", "depends_on"),
    ("TSMC", "China", "manufactures_in"),
    ("China", "Export Restrictions", "faces"),
    ("Export Restrictions", "Advanced Chips", "targets"),
    ("Advanced Chips", "Data Center Revenue", "impacts"),
    ("Data Center Revenue", "NVDA", "drives"),
    ("NVDA", "OEMs", "sells_to"),
    ("OEMs", "China Demand", "influenced_by"),
    ("China Demand", "NVDA", "exposes"),
]
G = nx.MultiDiGraph()
for u, v, l in edges:
    G.add_edge(u, v, label=l)

def draw_subgraph(ticker):
    # Gather all edges up to 3 hops away from ticker
    hops = nx.ego_graph(G, ticker, radius=3, center=True, undirected=False)
    net = Network(height="400px", width="100%", directed=True)
    for u, v, d in hops.edges(data=True):
        net.add_node(u)
        net.add_node(v)
        net.add_edge(u, v, label=d["label"])
    path = os.path.join(tempfile.gettempdir(), "nvda_subgraph.html")
    net.write_html(path)
    return path

# ----------- UI -----------
st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

# Question Input
st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question", value="Why is NVDA at risk from China trade?")
if st.button("Submit"):
    st.write("**Answer:** NVDA is exposed through TSMC dependency, chip restrictions, and weakening OEM demand driven by China’s policy changes.")
    st.markdown("**Citations:** Nvidia 10-Q, Reuters China policy, TSMC earnings")

# Portfolio Table
portfolio = pd.DataFrame([{
    "Ticker": "TSMC", "Timestamp": "2025-08-02", "What Changed": "Export restrictions rising", "Soft Signal": "Short activity ↑", "Sources": "SEC, JPM"
}])
st.subheader("📬 Daily Portfolio Brief")
st.dataframe(portfolio)

# Watchlist Table
watchlist = pd.DataFrame([{
    "Ticker": "NVDA", "Timestamp": "2025-08-02", "What Changed": "Margin pressure; China risk", "Soft Signal": "Options volume spike", "Sources": "BAML, 10-Q"
}])
st.subheader("👁 Watchlist Brief")
st.dataframe(watchlist)

# Subgraph Display
st.subheader("🕸️ NVDA Exposure Subgraph")
html_path = draw_subgraph("NVDA")
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
components.html(html, height=400, scrolling=True)

# Email Section
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
