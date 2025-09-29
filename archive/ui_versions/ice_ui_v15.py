# /app/ice_streamlit_app.py
# Streamlit MVP for ICE per-ticker view with triage header, KPI/Theme/Soft-signal panels,
# reasoning paths, "what changed", sources stack, and a mini subgraph with filters.
# Cleaned and updated with robust string handling for "New edges" rendering.

import os
import tempfile
from datetime import datetime, timedelta

import networkx as nx
import pandas as pd
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components

# ------------------------------------------------------------------------------
#                           D A T A   (D U M M Y   M V P)
# In production, replace these with the nightly JSON bundle produced by ICE:
# llm_context_package, ranked_paths, claims, edges (with confidence/last_seen).
# ------------------------------------------------------------------------------

NOW = datetime.utcnow()

# Minimal edge record for lazy subgraph rendering and filters
EDGE_RECORDS = [
    # source, target, edge_type, confidence [0..1], last_seen_days, contrarian_flag
    ("NVDA", "TSMC", "depends_on", 0.90, 1, False),
    ("TSMC", "China", "manufactures_in", 0.75, 2, False),
    ("China", "Export Controls", "imposes", 0.80, 1, False),
    ("Export Controls", "Advanced Chips", "targets", 0.78, 3, False),
    ("Advanced Chips", "Data Center Revenue", "drives", 0.72, 7, False),
    ("Data Center Revenue", "NVDA", "linked_to", 0.70, 10, False),
    ("NVDA", "OEMs", "sells_to", 0.65, 14, True),  # mark one as contrarian for demo
    ("OEMs", "Chinese Consumers", "serves", 0.60, 21, True),
    ("Chinese Consumers", "Spending Slowdown", "affected_by", 0.82, 2, False),
    ("Spending Slowdown", "NVDA", "pressures", 0.80, 1, False),
]

# Per-ticker bundle (normally from ICE nightly output)
TICKER_BUNDLE = {
    "NVDA": {
        "meta": {"name": "NVIDIA", "sector": "Semis"},
        "priority": 92,
        "recency_hours": 6,
        "confidence": 0.91,
        "next_catalyst": {"type": "Earnings", "date": "2025-08-21"},
        "tldr": "Mgmt flagged China logistics; supplier TSMC constraints → AI infra risk.",
        "kpis": [
            {
                "name": "Data Center Revenue",
                "last_seen": (NOW - timedelta(days=1)).date().isoformat(),
                "snippet": "Mgmt noted export logistics uncertainty around high-end GPUs.",
                "evidence_count": 4,
            },
            {
                "name": "Lead times",
                "last_seen": (NOW - timedelta(days=5)).date().isoformat(),
                "snippet": "Lead times stabilizing; mix shift to H200 in H2.",
                "evidence_count": 3,
            },
        ],
        "themes": [
            {"name": "China Risk", "confidence": 0.87, "last_seen": (NOW - timedelta(hours=6)).date().isoformat()},
            {"name": "AI Infrastructure", "confidence": 0.80, "last_seen": (NOW - timedelta(days=2)).date().isoformat()},
            {"name": "Supply Chain", "confidence": 0.76, "last_seen": (NOW - timedelta(days=1)).date().isoformat()},
        ],
        "soft_signals": [
            {
                "date": (NOW - timedelta(hours=6)).date().isoformat(),
                "polarity": "neg",
                "text": "Cautious on Asia ops; export permits under review.",
                "source_id": "doc123",
            },
            {
                "date": (NOW - timedelta(days=2)).date().isoformat(),
                "polarity": "uncertain",
                "text": "OEM reorder cadence softening in China region.",
                "source_id": "doc456",
            },
        ],
        "paths_ranked": [
            {
                "path_id": "p001",
                "path_str": "NVDA → depends_on → TSMC → exposed_to → China Risk",
                "hop_count": 3,
                "path_score": 0.92,
                "confidence": 0.88,
                "last_seen": (NOW - timedelta(hours=6)).isoformat(),
                "hops": [
                    {"edge_type": "depends_on", "target": "TSMC", "confidence": 0.90, "last_seen": (NOW - timedelta(days=1)).isoformat(), "evidence_count": 3},
                    {"edge_type": "exposed_to", "target": "China Risk", "confidence": 0.84, "last_seen": (NOW - timedelta(hours=6)).isoformat(), "evidence_count": 3},
                ],
                "claims": [
                    {"id": "c001", "date": (NOW - timedelta(hours=6)).date().isoformat(), "text": "Mgmt warned on export logistics", "source_id": "doc123"},
                    {"id": "c002", "date": (NOW - timedelta(days=1)).date().isoformat(), "text": "TSMC noted capacity constraints", "source_id": "doc456"},
                ],
                "sources": ["doc123", "doc456", "doc789"],
            },
            {
                "path_id": "p002",
                "path_str": "NVDA → exposed_to → AI Infrastructure",
                "hop_count": 1,
                "path_score": 0.78,
                "confidence": 0.80,
                "last_seen": (NOW - timedelta(days=2)).isoformat(),
                "hops": [
                    {"edge_type": "exposed_to", "target": "AI Infrastructure", "confidence": 0.80, "last_seen": (NOW - timedelta(days=2)).isoformat(), "evidence_count": 2}
                ],
                "claims": [{"id": "c003", "date": (NOW - timedelta(days=2)).date().isoformat(), "text": "AI capex plans supportive", "source_id": "doc777"}],
                "sources": ["doc777"],
            },
        ],
        "diff_since_prev": {
            "new_claims": ["c001"],
            "new_edges": [{"edge_type": "exposed_to", "target": "China Risk"}],
            "confidence_delta": +0.06,
        },
        "sources_ranked": [
            {"doc_id": "doc123", "title": "Q2 call transcript", "type": "transcript", "date": (NOW - timedelta(hours=6)).date().isoformat(), "snippet": "...export logistics..."},
            {"doc_id": "doc456", "title": "Supplier note", "type": "broker_note", "date": (NOW - timedelta(days=1)).date().isoformat(), "snippet": "...capacity constraints..."},
            {"doc_id": "doc789", "title": "Reuters: export curbs", "type": "news", "date": (NOW - timedelta(days=3)).date().isoformat(), "snippet": "...curbs on advanced chips..."},
        ],
    }
}

# Small portfolio/watchlist mock
PORTFOLIO_ROWS = [
    {
        "Ticker": "NVDA", "Name": "Nvidia", "Sector": "Semis", "Alert Priority": 92,
        "What Changed": "Export curbs expanded → DC GPU slowdown (cited)",
        "Top Causal Path": "NVDA → TSMC → China Risk (3 src)",
        "Themes": "AI infra • .8 • 2d | China policy • .6 • 1d",
        "KPIs": "Datacenter Rev • 1d | Lead times • 5d",
        "Soft Signal": "⚠️ mgmt cautious on China", "Recency": "6h", "Confidence": "0.91 (3 src)"
    },
    {
        "Ticker": "AAPL", "Name": "Apple", "Sector": "Consumer Tech", "Alert Priority": 76,
        "What Changed": "iPhone SE delays → Q3 topline risk (cited)",
        "Top Causal Path": "AAPL → Foxconn → China lockdown (2 src)",
        "Themes": "Consumer sentiment • .7 • 3d", "KPIs": "Unit sales • 2d",
        "Soft Signal": "⚠️ weak Asia demand flagged", "Recency": "18h", "Confidence": "0.82 (2 src)"
    },
]

WATCHLIST_ROWS = [
    {
        "Ticker": "COIN", "Name": "Coinbase", "Sector": "Crypto", "Alert Priority": 81,
        "What Changed": "SEC lawsuit update → fee model risk (cited)",
        "Top Causal Path": "COIN → SEC Action → Fee Revenue (2 src)",
        "Themes": "Regulatory • .7 • 1d", "KPIs": "Volume • 2d",
        "Soft Signal": "⚠️ legal risk in internal memo", "Recency": "14h", "Confidence": "0.85 (2 src)"
    }
]

# ------------------------------------------------------------------------------
#                               U T I L S
# ------------------------------------------------------------------------------

def build_graph(edge_records, min_conf=0.0, max_age_days=365, edge_types=None, contrarian_only=False):
    """Filter edges by confidence/recency/type and return a MultiDiGraph."""
    edge_types = set(edge_types or [])
    G = nx.MultiDiGraph()
    for s, t, et, conf, age_days, contrarian in edge_records:
        if conf < min_conf:
            continue
        if age_days > max_age_days:
            continue
        if edge_types and et not in edge_types:
            continue
        if contrarian_only and not contrarian:
            continue
        G.add_edge(s, t, label=et, confidence=conf, last_seen_days=age_days)
    return G

def draw_subgraph(G, center, radius=2):
    """Return an HTML path for the PyVis rendering of an ego subgraph."""
    if center not in G.nodes:
        sub = G.copy()
    else:
        sub = nx.ego_graph(G, center, radius=radius, center=True, undirected=False)
    net = Network(height="520px", width="100%", bgcolor="#111111", font_color="white", directed=True)

    # Minimal color palette
    color_map = {
        center: "#32CD32", "TSMC": "#FFD700", "China": "#FF4500",
        "Export Controls": "#DC143C", "Advanced Chips": "#FF69B4",
        "Data Center Revenue": "#1E90FF", "OEMs": "#00CED1",
        "Chinese Consumers": "#9370DB", "Spending Slowdown": "#FF8C00"
    }
    for node in sub.nodes:
        net.add_node(node, label=node, color=color_map.get(node, "#9aa0a6"), shape="dot", size=18)
    for u, v, d in sub.edges(data=True):
        label = d.get("label", "")
        conf = d.get("confidence", 0.5)
        net.add_edge(u, v, label=f"{label} ({conf:.2f})", color="lime")

    tmp = os.path.join(tempfile.gettempdir(), f"ice_graph_{center}.html")
    net.set_options("""var options = { "edges": { "color": { "inherit": false } }, "physics": { "enabled": false } }""")
    net.write_html(tmp)
    return tmp

def chip(text):
    st.markdown(
        f"<span style='background-color:#263238; color:#e0e0e0; padding:4px 8px; border-radius:10px; margin-right:6px;'>{text}</span>",
        unsafe_allow_html=True,
    )

def section_header(title, icon=""):
    st.markdown(f"### {icon} {title}")

# ------------------------------------------------------------------------------
#                              S T R E A M L I T
# ------------------------------------------------------------------------------

st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

# 1) Q&A (kept simple for MVP demo)
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

# 2) Portfolio & Watchlist briefs
st.subheader("📬 Daily Portfolio Brief")
st.dataframe(pd.DataFrame(PORTFOLIO_ROWS), use_container_width=True)

st.subheader("👁 Watchlist Brief – ICE Alert Format")
st.dataframe(pd.DataFrame(WATCHLIST_ROWS), use_container_width=True)

# 3) Per-ticker detail view (click-through replacement via selectbox for MVP)
st.markdown("---")
st.subheader("📌 Per-Ticker View (click a row → open here)")

available_tickers = ["NVDA"] + [r["Ticker"] for r in PORTFOLIO_ROWS if r["Ticker"] != "NVDA"]
ticker = st.selectbox("Open details for:", options=available_tickers, index=0)

bundle = TICKER_BUNDLE.get(ticker)
if not bundle:
    st.info("No detail bundle available for this ticker in the MVP dataset.")
else:
    # ===== Sticky Header (triage bar) =====
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.markdown(f"## {ticker} — {bundle['meta']['name']}  ·  {bundle['meta']['sector']}")
        st.markdown(f"**TL;DR:** {bundle['tldr']}")
    with col2:
        st.metric("Alert Priority", bundle["priority"])
    with col3:
        st.metric("Recency", f"{bundle['recency_hours']}h")
    with col4:
        st.metric("Confidence", f"{bundle['confidence']:.2f}")
    cat = bundle["next_catalyst"]
    chip(f"Next: {cat['type']} • {cat['date']}")

    st.markdown("")

    # ===== Left/Middle/Right panels =====
    left, middle, right = st.columns([1.2, 1.8, 1.2])

    # --- Left: KPI / Themes / Soft signals ---
    with left:
        section_header("KPI Watchlist", "📈")
        for k in bundle["kpis"]:
            st.markdown(
                f"- **{k['name']}** • last_seen: {k['last_seen']}  \n"
                f"  _{k['snippet']}_  \n"
                f"  evidence: {k['evidence_count']}"
            )

        section_header("Theme Exposure", "🏷️")
        for t in bundle["themes"][:3]:
            chip(f"{t['name']} • {t['confidence']:.2f} • {t['last_seen']}")

        section_header("Soft Signals", "🧭")
        for srec in bundle["soft_signals"][:3]:
            icon = "⚠️" if srec["polarity"] == "neg" else "❓"
            st.markdown(f"- {icon} {srec['date']}: {srec['text']}  \n  _source: {srec['source_id']}_")

    # --- Middle: Reasoning paths & What changed ---
    with middle:
        section_header("Top Reasoning Path", "🧠")
        top = bundle["paths_ranked"][0]
        st.markdown(
            f"**{top['path_str']}**  \n"
            f"score: {top['path_score']:.2f} • conf: {top['confidence']:.2f} • last_seen: {top['last_seen']}"
        )
        for hop in top["hops"]:
            st.markdown(
                f"- **{hop['edge_type']} → {hop['target']}** • "
                f"conf {hop['confidence']:.2f} • last_seen {hop['last_seen']} • evidence {hop['evidence_count']}"
            )
        st.markdown("**Supporting claims**")
        for c in top["claims"]:
            st.markdown(f"- {c['date']}: {c['text']}  \n  _source: {c['source_id']}_")

        # Alternative paths
        if len(bundle["paths_ranked"]) > 1:
            section_header("Alternative Paths", "🔀")
            for alt in bundle["paths_ranked"][1:3]:
                st.markdown(
                    f"- **{alt['path_str']}**  \n"
                    f"  score {alt['path_score']:.2f} • conf {alt['confidence']:.2f} • last_seen {alt['last_seen']}"
                )

        section_header("What changed since yesterday", "🆕")
        diff = bundle["diff_since_prev"]
        st.markdown(f"- New claims: {', '.join(diff.get('new_claims', [])) or '–'}")
        # ✅ Fix: precompute new_edges string to avoid nested f-string parsing issues
        new_edges_str = ", ".join(f"{e['edge_type']}→{e['target']}" for e in diff.get("new_edges", [])) or "–"
        st.markdown(f"- New edges: {new_edges_str}")
        st.markdown(f"- Confidence Δ: {diff.get('confidence_delta', 0):+0.02f}")

    # --- Right: Sources stack + Mini subgraph ---
    with right:
        section_header("Sources", "📚")
        for sdoc in bundle["sources_ranked"]:
            st.markdown(
                f"- **{sdoc['title']}** ({sdoc['type']}, {sdoc['date']})  \n"
                f"  _{sdoc['snippet']}_"
            )

        section_header("Mini Subgraph", "🕸️")

        # Controls (hop, recency, confidence, type, contrarian)
        hop_depth = st.slider("Hop depth", min_value=1, max_value=3, value=2, step=1)
        max_age = st.select_slider("Recency window (days)", options=[7, 14, 30, 90, 180, 365], value=30)
        min_conf = st.slider("Min. confidence", min_value=0.0, max_value=1.0, value=0.6, step=0.05)
        edge_types_sel = st.multiselect(
            "Edge types",
            options=sorted(set(e[2] for e in EDGE_RECORDS)),
            default=[],
            help="Leave empty to include all edge types.",
        )
        contrarian_only = st.checkbox("Show contrarian only", value=False)

        G = build_graph(
            EDGE_RECORDS,
            min_conf=min_conf,
            max_age_days=max_age,
            edge_types=edge_types_sel,
            contrarian_only=contrarian_only,
        )
        html_path = draw_subgraph(G, ticker, radius=hop_depth)
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        components.html(html, height=520, scrolling=True)

# 4) Email stub
st.markdown("---")
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
