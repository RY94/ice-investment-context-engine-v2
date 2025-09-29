import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# --------- Sample Static Data for MVP Table ---------
now = datetime.utcnow()

def rand_hours():
    return random.randint(1, 72)

def recency_str(hours):
    return f"{hours//24}d" if hours >= 24 else f"{hours}h"

data = [
    {
        "Ticker": "NVDA",
        "Name": "Nvidia",
        "Sector": "Semis",
        "Alert Priority": 92,
        "What Changed": "Export curbs expanded → Data center GPU slowdown (cited)",
        "Top Causal Path": "NVDA → TSMC → China Risk (3 src)",
        "Themes": "AI infra • .8 • 2d | China policy • .6 • 1d",
        "KPIs": "Gross margin • 1d | Datacenter Rev • 2d",
        "Soft Signal": "⚠️ mgmt cautious on China",
        "Recency": recency_str(rand_hours()),
        "Confidence": "0.91 (3 src)"
    },
    {
        "Ticker": "AAPL",
        "Name": "Apple",
        "Sector": "Consumer Tech",
        "Alert Priority": 76,
        "What Changed": "iPhone SE delays → Q3 topline risk (cited)",
        "Top Causal Path": "AAPL → Foxconn → China lockdown (2 src)",
        "Themes": "Consumer sentiment • .7 • 3d",
        "KPIs": "Unit sales • 2d",
        "Soft Signal": "⚠️ weak Asia demand flagged",
        "Recency": recency_str(rand_hours()),
        "Confidence": "0.82 (2 src)"
    },
    {
        "Ticker": "TSMC",
        "Name": "Taiwan Semi",
        "Sector": "Semis",
        "Alert Priority": 88,
        "What Changed": "China export curbs → capacity rerouting (cited)",
        "Top Causal Path": "TSMC → China Risk → Export Controls (4 src)",
        "Themes": "Supply chain risk • .9 • 1d | Trade war • .6 • 1d",
        "KPIs": "CapEx • 1d",
        "Soft Signal": "⚠️ geopolitical warnings in earnings call",
        "Recency": recency_str(rand_hours()),
        "Confidence": "0.94 (4 src)"
    }
]

df = pd.DataFrame(data)

# --------- Streamlit UI ---------
st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

st.subheader("🔥 MVP Alert Table – Prioritized View")
st.dataframe(df, use_container_width=True)

# Optionally: sorting, filtering → AgGrid or experimental_data_editor
