# /app/ice_streamlit_app.py
# -------------------------------------------------------------------
#  Full MVP demo – ICE Investment Context Engine (single-file version)
#  Includes: Q&A, per-ticker triage view, KPI / Theme / Soft-signal
#  panels, reasoning paths, “what changed”, sources stack, mini
#  subgraph with filters, portfolio + watchlist tables, email stub.
# -------------------------------------------------------------------

import os, tempfile
from datetime import datetime, timedelta

import networkx as nx
import pandas as pd
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components

# ------------------------------ DUMMY DATA ------------------------------
NOW = datetime.utcnow()

EDGE_RECORDS = [
    ("NVDA", "TSMC", "depends_on", 0.90, 1, False),
    ("TSMC", "China", "manufactures_in", 0.75, 2, False),
    ("China", "Export Controls", "imposes", 0.80, 1, False),
    ("Export Controls", "Advanced Chips", "targets", 0.78, 3, False),
    ("Advanced Chips", "Data Center Revenue", "drives", 0.72, 7, False),
    ("Data Center Revenue", "NVDA", "linked_to", 0.70, 10, False),
    ("NVDA", "OEMs", "sells_to", 0.65, 14, True),
    ("OEMs", "Chinese Consumers", "serves", 0.60, 21, True),
    ("Chinese Consumers", "Spending Slowdown", "affected_by", 0.82, 2, False),
    ("Spending Slowdown", "NVDA", "pressures", 0.80, 1, False),
]

TICKER_BUNDLE = {
    "NVDA": {
        "meta": {"name": "NVIDIA", "sector": "Semis"},
        "priority": 92,
        "recency_hours": 6,
        "confidence": 0.91,
        "next_catalyst": {"type": "Earnings", "date": "2025-08-21"},
        "tldr": "Mgmt flagged China logistics; supplier TSMC constraints → AI infra risk.",
        "kpis": [
            {"name": "Data Center Revenue", "last_seen": (NOW - timedelta(days=1)).date().isoformat(),
             "snippet": "Mgmt noted export logistics uncertainty around high-end GPUs.", "evidence_count": 4},
            {"name": "Lead times", "last_seen": (NOW - timedelta(days=5)).date().isoformat(),
             "snippet": "Lead times stabilizing; mix shift to H200 in H2.", "evidence_count": 3},
        ],
        "themes": [
            {"name": "China Risk", "confidence": 0.87, "last_seen": (NOW - timedelta(hours=6)).date().isoformat()},
            {"name": "AI Infrastructure", "confidence": 0.80, "last_seen": (NOW - timedelta(days=2)).date().isoformat()},
            {"name": "Supply Chain", "confidence": 0.76, "last_seen": (NOW - timedelta(days=1)).date().isoformat()},
        ],
        "soft_signals": [
            {"date": (NOW - timedelta(hours=6)).date().isoformat(), "polarity": "neg",
             "text": "Cautious on Asia ops; export permits under review.", "source_id": "doc123"},
            {"date": (NOW - timedelta(days=2)).date().isoformat(), "polarity": "uncertain",
             "text": "OEM reorder cadence softening in China region.", "source_id": "doc456"},
        ],
        "paths_ranked": [
            {
                "path_id": "p001",
                "path_str": "NVDA → depends_on → TSMC → exposed_to → China Risk",
                "hop_count": 3, "path_score": 0.92, "confidence": 0.88,
                "last_seen": (NOW - timedelta(hours=6)).isoformat(),
                "hops": [
                    {"edge_type": "depends_on", "target": "TSMC", "confidence": 0.90,
                     "last_seen": (NOW - timedelta(days=1)).isoformat(), "evidence_count": 3},
                    {"edge_type": "exposed_to", "target": "China Risk", "confidence": 0.84,
                     "last_seen": (NOW - timedelta(hours=6)).isoformat(), "evidence_count": 3},
                ],
                "claims": [
                    {"id": "c001", "date": (NOW - timedelta(hours=6)).date().isoformat(),
                     "text": "Mgmt warned on export logistics", "source_id": "doc123"},
                    {"id": "c002", "date": (NOW - timedelta(days=1)).date().isoformat(),
                     "text": "TSMC noted capacity constraints", "source_id": "doc456"},
                ],
                "sources": ["doc123", "doc456", "doc789"],
            }
        ],
        "diff_since_prev": {
            "new_claims": ["c001"],
            "new_edges": [{"edge_type": "exposed_to", "target": "China Risk"}],
            "confidence_delta": +0.06,
        },
        "sources_ranked": [
            {"doc_id": "doc123", "title": "Q2 call transcript", "type": "transcript",
             "date": (NOW - timedelta(hours=6)).date().isoformat(), "snippet": "...export logistics..."},
            {"doc_id": "doc456", "title": "Supplier note", "type": "broker_note",
             "date": (NOW - timedelta(days=1)).date().isoformat(), "snippet": "...capacity constraints..."},
            {"doc_id": "doc789", "title": "Reuters: export curbs", "type": "news",
             "date": (NOW - timedelta(days=3)).date().isoformat(), "snippet": "...curbs on advanced chips..."},
        ],
    }
}

PORTFOLIO_ROWS = [
    {"Ticker": "NVDA", "Name": "Nvidia", "Sector": "Semis", "Alert Priority": 92,
     "What Changed": "Export curbs expanded → DC GPU slowdown (cited)",
     "Top Causal Path": "NVDA → TSMC → China Risk (3 src)",
     "Themes": "AI infra • .8 • 2d | China policy • .6 • 1d",
     "KPIs": "Datacenter Rev • 1d | Lead times • 5d",
     "Soft Signal": "⚠️ mgmt cautious on China", "Recency": "6h", "Confidence": "0.91 (3 src)"},
    {"Ticker": "AAPL", "Name": "Apple", "Sector": "Consumer Tech", "Alert Priority": 76,
     "What Changed": "iPhone SE delays → Q3 topline risk (cited)",
     "Top Causal Path": "AAPL → Foxconn → China lockdown (2 src)",
     "Themes": "Consumer sentiment • .7 • 3d", "KPIs": "Unit sales • 2d",
     "Soft Signal": "⚠️ weak Asia demand flagged", "Recency": "18h", "Confidence": "0.82 (2 src)"},
]

WATCHLIST_ROWS = [
    {"Ticker": "COIN", "Name": "Coinbase", "Sector": "Crypto", "Alert Priority": 81,
     "What Changed": "SEC lawsuit update → fee model risk (cited)",
     "Top Causal Path": "COIN → SEC Action → Fee Revenue (2 src)",
     "Themes": "Regulatory • .7 • 1d", "KPIs": "Volume • 2d",
     "Soft Signal": "⚠️ legal risk in internal memo", "Recency": "14h", "Confidence": "0.85 (2 src)"}
]

# --------------------------- HELPER FUNCTIONS ---------------------------
def chip(text):
    st.markdown(
        f"<span style='background:#263238;color:#e0e0e0;padding:4px 8px;border-radius:10px;"
        f"margin-right:6px;font-size:0.8rem'>{text}</span>", unsafe_allow_html=True)

def section_header(title, icon=""):
    st.markdown(f"### {icon} {title}")

def build_graph(edge_records, *, min_conf=0, max_age_days=365,
                edge_types=None, contrarian_only=False):
    sel = set(edge_types or [])
    G = nx.MultiDiGraph()
    for s, t, et, conf, age, contr in edge_records:
        if conf < min_conf or age > max_age_days:            continue
        if sel and et not in sel:                            continue
        if contrarian_only and not contr:                    continue
        G.add_edge(s, t, label=et, confidence=conf)
    return G

def draw_subgraph(G, center, *, radius=2):
    sg = nx.ego_graph(G, center, radius=radius, center=True, undirected=False) \
         if center in G else G
    net = Network(height="520px", width="100%", bgcolor="#111111",
                  font_color="white", directed=True)
    for n in sg.nodes:
        net.add_node(n, color="#32CD32" if n == center else "#9aa0a6")
    for u, v, d in sg.edges(data=True):
        net.add_edge(u, v, label=d.get("label", ""), color="lime")
    path = os.path.join(tempfile.gettempdir(), f"sg_{center}.html")
    net.write_html(path)
    return path



# ------------------------- STREAMLIT LAYOUT -------------------------
st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

# 1) Ask ICE a Question
st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question", value="Why is NVDA at risk from China trade?")
if st.button("Submit"):
    st.markdown("### 💡 ICE Answer")
    st.write(
        "Nvidia (NVDA) is exposed to China-related trade risks via both supply and demand channels.\n\n"
        "- **Supply-side**: NVDA relies on TSMC, which manufactures advanced chips in China. "
        "U.S. export controls targeting these chips directly constrain TSMC’s ability to fulfil high-end GPU orders.\n"
        "- **Demand-side**: NVDA’s key OEM partners serve Chinese enterprise and consumer markets. "
        "Recent signs of spending slowdown, combined with policy uncertainty, suggest softening end demand.\n"
        "- **Revenue Impact**: Data Center segment, NVDA’s fastest-growing business line, is most vulnerable.\n"
    )
    st.markdown("**🧾 Sources**")
    st.markdown("- TSMC Supply Chain Report (2025 Q2)\n- Nvidia 10-Q (Jul 2025)\n"
                "- Reuters: China chip export curbs (2025-07-29)\n- JPM Tech Desk (2025-08-01)")
    st.markdown("**🧠 Reasoning Chain**")
    st.code("NVDA → TSMC → China → Export Controls → Advanced Chips → Data Center Revenue → NVDA")

# 2) Per-Ticker Detail View
st.markdown("## 📌 Per-Ticker View *(click a row → open here)*")
available_tickers = ["NVDA"] + [r["Ticker"] for r in PORTFOLIO_ROWS if r["Ticker"] != "NVDA"]
ticker = st.selectbox("Open details for:", available_tickers, index=0)
bundle = TICKER_BUNDLE.get(ticker)

if bundle:
    # triage header
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1:
        st.markdown(f"## {ticker} — {bundle['meta']['name']} · {bundle['meta']['sector']}")
        st.markdown(f"**TL;DR:** {bundle['tldr']}")
    with c2: st.metric("Alert Priority", bundle["priority"])
    with c3: st.metric("Recency", f"{bundle['recency_hours']}h")
    with c4: st.metric("Confidence", f"{bundle['confidence']:.2f}")
    chip(f"Next: {bundle['next_catalyst']['type']} • {bundle['next_catalyst']['date']}")

    left, mid, right = st.columns([1.2, 1.8, 1.2])

    # left panel
    with left:
        section_header("KPI Watchlist", "📈")
        for k in bundle["kpis"]:
            st.markdown(f"- **{k['name']}** • {k['last_seen']}  \n_{k['snippet']}_  \n evidence: {k['evidence_count']}")
        section_header("Theme Exposure", "🏷️")
        for t in bundle["themes"][:3]:
            chip(f"{t['name']} • {t['confidence']:.2f} • {t['last_seen']}")
        section_header("Soft Signals", "🧭")
        for s in bundle["soft_signals"][:3]:
            icon = "⚠️" if s["polarity"] == "neg" else "❓"
            st.markdown(f"- {icon} {s['date']}: {s['text']}  \n_source {s['source_id']}_")

    # middle panel
    with mid:
        section_header("Top Reasoning Path", "🧠")
        top = bundle["paths_ranked"][0]
        st.markdown(f"**{top['path_str']}**  \nscore {top['path_score']:.2f} • conf {top['confidence']:.2f}")
        for h in top["hops"]:
            st.markdown(f"- **{h['edge_type']} → {h['target']}** • conf {h['confidence']:.2f} • "
                        f"evidence {h['evidence_count']}")
        st.markdown("**Supporting claims**")
        for c in top["claims"]:
            st.markdown(f"- {c['date']}: {c['text']} _({c['source_id']})_")

        if len(bundle["paths_ranked"]) > 1:
            section_header("Alternative Paths", "🔀")
            for alt in bundle["paths_ranked"][1:3]:
                st.markdown(f"- **{alt['path_str']}** • score {alt['path_score']:.2f}")

        section_header("What changed since yesterday", "🆕")
        diff = bundle["diff_since_prev"]
        new_edges = diff.get("new_edges", [])
        new_edges_str = ", ".join(f"{e['edge_type']}→{e['target']}" for e in new_edges) or "–"
        st.markdown(f"- New claims: {', '.join(diff.get('new_claims', [])) or '–'}")
        st.markdown(f"- New edges: {new_edges_str}")
        st.markdown(f"- Confidence Δ: {diff.get('confidence_delta', 0):+0.02f}")

    # right panel
    with right:
        section_header("Sources", "📚")
        for sdoc in bundle["sources_ranked"]:
            st.markdown(f"- **{sdoc['title']}** ({sdoc['type']}, {sdoc['date']})  \n_{sdoc['snippet']}_")

# 3) Mini Subgraph
st.markdown("## 🕸️ Mini Subgraph")
hop = st.slider("Hop depth", 1, 3, 2)
age = st.select_slider("Recency window (days)", [7, 14, 30, 90, 180, 365], 30)
conf = st.slider("Min. confidence", 0.0, 1.0, 0.6, 0.05)
etypes = st.multiselect("Edge types", sorted(set(e[2] for e in EDGE_RECORDS)), [])
contr_only = st.checkbox("Show contrarian only", False)

graph = build_graph(EDGE_RECORDS, min_conf=conf, max_age_days=age,
                    edge_types=etypes, contrarian_only=contr_only)
g_html = draw_subgraph(graph, ticker, radius=hop)
components.html(open(g_html).read(), height=520, scrolling=True)

# 4) Tables
st.markdown("---")
st.subheader("📬 Daily Portfolio Brief")
st.dataframe(pd.DataFrame(PORTFOLIO_ROWS), use_container_width=True)
st.subheader("👁 Watchlist Brief – ICE Alert Format")
st.dataframe(pd.DataFrame(WATCHLIST_ROWS), use_container_width=True)

# 5) Email stub
st.markdown("---")
st.subheader("✉️ Email Summary")
to = st.text_input("Recipient Email")
if st.button("Send Email"): st.success(f"Summary sent to {to}")
