import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile, os

# -------------------- Graph Setup --------------------
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
    nodes = {u for u, v in G.edges() if u == ticker or v == ticker}
    nodes |= {v for u, v in G.edges() if u == ticker or v == ticker}
    sub = G.subgraph(nodes)
    net = Network(height="300px", width="100%", directed=True)
    for u, v, d in sub.edges(data=True):
        net.add_node(u)
        net.add_node(v)
        net.add_edge(u, v, label=d['label'])
    path = os.path.join(tempfile.gettempdir(), "nvda_graph.html")
    net.write_html(path)
    return path

# -------------------- UI ---------------
# -----
st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

# Q&A
st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question", value="Why is NVDA at risk from China trade?")
if st.button("Submit"):
    st.write("**Answer:** NVDA's exposure to China through TSMC and reliance on advanced chip exports puts it at risk under tightening U.S.-China trade tensions.")
    st.markdown("**Citations:** TSMC supply chain disclosure, Nvidia 10-Q, Reuters China policy")

# Portfolio Table
st.subheader("📬 Daily Portfolio Brief")
portfolio = pd.DataFrame([
    {"Ticker": "TSMC", "Timestamp": "2025-08-02", "What Changed": "Geopolitical export risk", "Soft Signal": "Short volume up", "Sources": "SEC, Bloomberg"},
    {"Ticker": "NVDA", "Timestamp": "2025-08-02", "What Changed": "Margin pressure; China risk", "Soft Signal": "Options spike", "Sources": "10-Q, BAML"},
])
st.dataframe(portfolio)

# Watchlist Table
st.subheader("👁 Watchlist Brief")
watchlist = pd.DataFrame([
    {"Ticker": "NVDA", "Timestamp": "2025-08-02", "What Changed": "China trade tension", "Soft Signal": "Analyst downgrade", "Sources": "BAML, Reuters"},
    {"Ticker": "AMD", "Timestamp": "2025-08-02", "What Changed": "Weak demand", "Soft Signal": "Insider sales", "Sources": "SEC"},
])
st.dataframe(watchlist)

# Subgraph
st.subheader("🕸️ Subgraph for NVDA – China Exposure")
graph_path = draw_subgraph("NVDA")
components.iframe(graph_path, height=300)

# Email Input
st.subheader("✉️ Email Summary")
email = st.text_input("Enter recipient email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
