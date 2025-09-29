# /app/ice_streamlit_app.py
# ------------------------------------------------------------------
# MVP one-file demo for ICE Investment Context Engine
# – Ask-ICE Q&A
# – Per-ticker triage view (KPI / themes / soft-signals / paths)
# – Mini subgraph with edge-type colour coding
# – Portfolio + watchlist tables
# – Email stub
# ------------------------------------------------------------------

import os, tempfile
from datetime import datetime, timedelta

import networkx as nx
import pandas as pd
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components

# --------------------------- DUMMY DATA ---------------------------
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
        "priority": 92, "recency_hours": 6, "confidence": 0.91,
        "next_catalyst": {"type": "Earnings", "date": "2025-08-21"},
        "tldr": "Mgmt flagged China logistics; supplier TSMC constraints → AI infra risk.",
        "kpis": [
            {"name": "Data Center Revenue", "last_seen": (NOW-timedelta(days=1)).date().isoformat(),
             "snippet": "Mgmt noted export logistics uncertainty around high-end GPUs.", "evidence_count": 4},
            {"name": "Lead times", "last_seen": (NOW-timedelta(days=5)).date().isoformat(),
             "snippet": "Lead times stabilizing; mix shift to H200 in H2.", "evidence_count": 3},
        ],
        "themes": [
            {"name": "China Risk", "confidence": 0.87, "last_seen": (NOW-timedelta(hours=6)).date().isoformat()},
            {"name": "AI Infrastructure", "confidence": 0.80, "last_seen": (NOW-timedelta(days=2)).date().isoformat()},
            {"name": "Supply Chain", "confidence": 0.76, "last_seen": (NOW-timedelta(days=1)).date().isoformat()},
        ],
        "soft_signals": [
            {"date": (NOW-timedelta(hours=6)).date().isoformat(), "polarity": "neg",
             "text": "Cautious on Asia ops; export permits under review.", "source_id": "doc123"},
            {"date": (NOW-timedelta(days=2)).date().isoformat(), "polarity": "uncertain",
             "text": "OEM reorder cadence softening in China region.", "source_id": "doc456"},
        ],
        "paths_ranked": [{
            "path_id": "p001",
            "path_str": "NVDA → depends_on → TSMC → exposed_to → China Risk",
            "hop_count": 3, "path_score": 0.92, "confidence": 0.88,
            "last_seen": (NOW-timedelta(hours=6)).isoformat(),
            "hops": [
                {"edge_type": "depends_on", "target": "TSMC", "confidence": 0.90,
                 "last_seen": (NOW-timedelta(days=1)).isoformat(), "evidence_count": 3},
                {"edge_type": "exposed_to", "target": "China Risk", "confidence": 0.84,
                 "last_seen": (NOW-timedelta(hours=6)).isoformat(), "evidence_count": 3},
            ],
            "claims": [
                {"id": "c001", "date": (NOW-timedelta(hours=6)).date().isoformat(),
                 "text": "Mgmt warned on export logistics", "source_id": "doc123"},
                {"id": "c002", "date": (NOW-timedelta(days=1)).date().isoformat(),
                 "text": "TSMC noted capacity constraints", "source_id": "doc456"},
            ],
            "sources": ["doc123", "doc456", "doc789"],
        }],
        "diff_since_prev": {"new_claims": ["c001"],
                            "new_edges": [{"edge_type": "exposed_to", "target": "China Risk"}],
                            "confidence_delta": +0.06},
        "sources_ranked": [
            {"doc_id": "doc123", "title": "Q2 call transcript", "type": "transcript",
             "date": (NOW-timedelta(hours=6)).date().isoformat(), "snippet": "...export logistics..."},
            {"doc_id": "doc456", "title": "Supplier note", "type": "broker_note",
             "date": (NOW-timedelta(days=1)).date().isoformat(), "snippet": "...capacity constraints..."},
            {"doc_id": "doc789", "title": "Reuters: export curbs", "type": "news",
             "date": (NOW-timedelta(days=3)).date().isoformat(), "snippet": "...curbs on advanced chips..."},
        ],
    }
}

######################################################################################
# PORTFOLIO_ROWS = [
#     {
#         "Ticker": "NVDA", "Name": "Nvidia", "Sector": "Semis", "Alert Priority": 92,
#         "What Changed": "Export curbs expanded → DC GPU slowdown (cited)",
#         "Top Causal Path": "NVDA → TSMC → China Risk (3 src)",
#         "Themes": "AI infra • .8 • 2d | China policy • .6 • 1d",
#         "KPIs": "Datacenter Rev • 1d | Lead times • 5d",
#         "Soft Signal": "⚠️ mgmt cautious on China", "Recency": "6h", "Confidence": "0.91 (3 src)"
#     },
#     {
#         "Ticker": "AAPL", "Name": "Apple", "Sector": "Consumer Tech", "Alert Priority": 76,
#         "What Changed": "iPhone SE delays → Q3 topline risk (cited)",
#         "Top Causal Path": "AAPL → Foxconn → China lockdown (2 src)",
#         "Themes": "Consumer sentiment • .7 • 3d", "KPIs": "Unit sales • 2d",
#         "Soft Signal": "⚠️ weak Asia demand flagged", "Recency": "18h", "Confidence": "0.82 (2 src)"
#     },
# ]


# WATCHLIST_ROWS = [
#     {"Ticker": "COIN", "Name": "Coinbase", "Sector": "Crypto", "Alert Priority": 81,
#      "What Changed": "SEC lawsuit update → fee model risk (cited)",
#      "Top Causal Path": "COIN → SEC Action → Fee Revenue (2 src)",
#      "Themes": "Regulatory • .7 • 1d", "KPIs": "Volume • 2d",
#      "Soft Signal": "⚠️ legal risk in internal memo", "Recency": "14h", "Confidence": "0.85 (2 src)"}
# ]


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
    {
        "Ticker": "MSFT", "Name": "Microsoft", "Sector": "Software", "Alert Priority": 73,
        "What Changed": "Azure bookings downshift → Cloud growth risk",
        "Top Causal Path": "MSFT → Azure → CapEx Pullback (2 src)",
        "Themes": "Cloud slowdown • .6 • 2d", "KPIs": "Azure NRR • 1d",
        "Soft Signal": "⚠️ hiring freeze in cloud ops", "Recency": "12h", "Confidence": "0.79 (2 src)"
    },
    {
        "Ticker": "AMZN", "Name": "Amazon", "Sector": "E-commerce", "Alert Priority": 68,
        "What Changed": "Prime sign-ups lag seasonal norm → Demand drag",
        "Top Causal Path": "AMZN → Consumer Spend → Macro Weakness (2 src)",
        "Themes": "US consumer • .5 • 4d", "KPIs": "Prime subs • 2d",
        "Soft Signal": "⚠️ CSAT complaints trending up", "Recency": "2d", "Confidence": "0.76 (2 src)"
    },
    {
        "Ticker": "GOOGL", "Name": "Alphabet", "Sector": "Digital Ads", "Alert Priority": 70,
        "What Changed": "Ad budgets trimmed → Rev softness",
        "Top Causal Path": "GOOGL → SMB Ad Spend → Macro Risk (2 src)",
        "Themes": "Ad slowdown • .6 • 3d", "KPIs": "Ad RPM • 1d",
        "Soft Signal": "⚠️ internal memo on cost cuts", "Recency": "1d", "Confidence": "0.78 (2 src)"
    }
]

WATCHLIST_ROWS = [
    {
        "Ticker": "COIN", "Name": "Coinbase", "Sector": "Crypto", "Alert Priority": 81,
        "What Changed": "SEC lawsuit update → fee model risk (cited)",
        "Top Causal Path": "COIN → SEC Action → Fee Revenue (2 src)",
        "Themes": "Regulatory • .7 • 1d", "KPIs": "Volume • 2d",
        "Soft Signal": "⚠️ legal risk in internal memo", "Recency": "14h", "Confidence": "0.85 (2 src)"
    },
    {
        "Ticker": "TSLA", "Name": "Tesla", "Sector": "Auto", "Alert Priority": 78,
        "What Changed": "Recall filing → Delivery disruption risk",
        "Top Causal Path": "TSLA → Recall → Q3 ASP (3 src)",
        "Themes": "EV demand • .6 • 2d", "KPIs": "Deliveries • 1d",
        "Soft Signal": "⚠️ social sentiment down", "Recency": "8h", "Confidence": "0.83 (3 src)"
    },
    {
        "Ticker": "BABA", "Name": "Alibaba", "Sector": "China E-com", "Alert Priority": 85,
        "What Changed": "New export regs → Logistics bottleneck",
        "Top Causal Path": "BABA → CN Exports → Revenue Risk (4 src)",
        "Themes": "China macro • .9 • 1d", "KPIs": "GMV • 1d",
        "Soft Signal": "⚠️ mgmt guided lower", "Recency": "6h", "Confidence": "0.90 (4 src)"
    },
    {
        "Ticker": "SNOW", "Name": "Snowflake", "Sector": "SaaS", "Alert Priority": 67,
        "What Changed": "Consumption softness → FY guide at risk",
        "Top Causal Path": "SNOW → Cloud budgets → Usage (2 src)",
        "Themes": "Cloud slowdown • .6 • 2d", "KPIs": "DBNRR • 3d",
        "Soft Signal": "⚠️ layoffs rumor", "Recency": "20h", "Confidence": "0.75 (2 src)"
    }
]


# ----------------------- small UI helpers -----------------------
def chip(text):
    st.markdown(
        f"<span style='background:#263238;color:#e0e0e0;padding:4px 8px;border-radius:10px;"
        f"margin-right:6px;font-size:0.8rem'>{text}</span>",
        unsafe_allow_html=True)

def section_header(txt, icon=""): st.markdown(f"### {icon} {txt}")

def build_graph(recs, *, min_conf=0, max_age_days=365, edge_types=None, contrarian_only=False):
    sel = set(edge_types or [])
    G = nx.MultiDiGraph()
    for s, t, et, conf, age, contr in recs:
        if conf < min_conf or age > max_age_days: continue
        if sel and et not in sel:                continue
        if contrarian_only and not contr:        continue
        G.add_edge(s, t, label=et, confidence=conf)
    return G

# ---- UPDATED draw_subgraph: colour per edge-type, highlight core ----
EDGE_COLORS = {
    "depends_on":      "#f44336",  "manufactures_in": "#ff9800",
    "imposes":         "#9c27b0",  "targets":         "#e91e63",
    "drives":          "#3f51b5",  "linked_to":       "#2196f3",
    "sells_to":        "#4caf50",  "serves":          "#00bcd4",
    "affected_by":     "#ffc107",  "pressures":       "#795548",
}

def draw_subgraph(G, center, *, radius=2):
    sg = nx.ego_graph(G, center, radius=radius, center=True, undirected=False) if center in G else G
    net = Network("520px", "100%", bgcolor="#111111", font_color="white", directed=True)
    for n in sg.nodes:
        net.add_node(n, label=n,
                     color="#32CD32" if n == center else "#9aa0a6",
                     size=26 if n == center else 16)
    for u, v, d in sg.edges(data=True):
        net.add_edge(u, v, label=d.get("label", ""),
                     color=EDGE_COLORS.get(d.get("label"), "lime"))
    tmp = os.path.join(tempfile.gettempdir(), f"sg_{center}.html")
    net.write_html(tmp); return tmp

# ------------------------ STREAMLIT LAYOUT ------------------------
st.set_page_config(layout="wide")
st.title("🧊 ICE – Investment Context Engine")

# 1. Ask ICE
st.subheader("🔍 Ask ICE a Question")
query = st.text_input("Your Question", value="Why is NVDA at risk from China trade?")
if st.button("Submit"):
    # st.markdown("### 💡 ICE Answer")
    # st.write("Nvidia exposed to China trade risk via supply (TSMC) and demand (OEM) channels.")
    # st.markdown("**🧠 Reasoning Chain**")
    # st.code("NVDA → TSMC → China → Export Controls → Data Center")

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


# 2. Exa Web Search & Research
st.markdown("## 🔍 Exa Web Search & Research")

with st.expander("🌐 Advanced Web Search & Company Research", expanded=False):
    search_col1, search_col2 = st.columns([3, 1])
    
    with search_col1:
        search_query = st.text_input("Search Query", 
                                   placeholder="e.g., 'NVIDIA Q3 2024 earnings results'",
                                   help="Enter your search query for web search or company research")
        
        search_type = st.selectbox("Search Type", [
            "Web Search",
            "Company Research", 
            "Competitor Analysis",
            "Research Papers",
            "Financial News",
            "Industry Insights",
            "LinkedIn Search"
        ])
        
        if search_type == "Company Research":
            company = st.text_input("Company Name", placeholder="e.g., NVIDIA")
            topics = st.multiselect("Research Topics", ["earnings", "AI", "semiconductors", "supply chain", "China", "regulation"])
        elif search_type == "Competitor Analysis":
            company = st.text_input("Company Name", placeholder="e.g., NVIDIA")
            industry = st.text_input("Industry", placeholder="e.g., semiconductors")
        elif search_type == "Financial News":
            symbol = st.text_input("Stock Symbol", placeholder="e.g., NVDA")
            days_back = st.slider("Days Back", 1, 30, 7)
        elif search_type == "Industry Insights":
            industry = st.text_input("Industry", placeholder="e.g., artificial intelligence")
            insight_topics = st.multiselect("Topics", ["trends", "outlook", "regulation", "competition"])
    
    with search_col2:
        st.markdown("**Search Settings**")
        num_results = st.slider("Results", 5, 20, 10)
        include_domains = st.text_area("Include Domains", 
                                     placeholder="bloomberg.com, reuters.com\n(one per line)",
                                     height=80)
        exclude_domains = st.text_area("Exclude Domains",
                                     placeholder="reddit.com, twitter.com\n(one per line)",
                                     height=80)
    
    if st.button("🔍 Search with Exa", type="primary"):
        with st.spinner("Searching with Exa..."):
            # Mock results for demonstration - replace with actual Exa connector
            st.success("Search completed! (Mock results shown below)")
            
            # Mock search results
            mock_results = [
                {
                    "title": "NVIDIA Q3 2024 Earnings: Record Revenue Driven by AI Demand",
                    "url": "https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Announces-Financial-Results-for-Third-Quarter-Fiscal-2024/",
                    "text": "NVIDIA reported record third-quarter revenue of $60.9 billion, up 17% from Q2 and up 206% from a year ago...",
                    "highlights": ["record revenue", "AI demand", "data center growth"],
                    "published_date": "2024-11-20",
                    "score": 0.95
                },
                {
                    "title": "AI Chip Demand Continues to Drive NVIDIA's Growth",
                    "url": "https://www.bloomberg.com/news/articles/2024-11-21/ai-chip-demand-nvidia-growth",
                    "text": "Strong demand for artificial intelligence chips continues to fuel NVIDIA's remarkable growth trajectory...",
                    "highlights": ["AI chips", "growth trajectory", "market leadership"],
                    "published_date": "2024-11-21",
                    "score": 0.88
                }
            ]
            
            st.markdown("### Search Results")
            for i, result in enumerate(mock_results, 1):
                with st.container():
                    st.markdown(f"**{i}. {result['title']}**")
                    st.markdown(f"🔗 [{result['url']}]({result['url']})")
                    st.markdown(f"📅 {result['published_date']} | ⭐ Score: {result['score']}")
                    if result['highlights']:
                        st.markdown(f"🔍 **Highlights:** {', '.join(result['highlights'])}")
                    st.markdown(f"📝 {result['text'][:200]}...")
                    
                    # Add to knowledge graph button
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if st.button(f"Add to KG", key=f"add_kg_{i}"):
                            st.success("Added to knowledge graph!")
                    with col2:
                        if st.button(f"Analyze", key=f"analyze_{i}"):
                            st.info("Analysis would be performed here")
                    st.markdown("---")
            
            # Add integration with ICE knowledge graph
            st.markdown("### 🧠 ICE Analysis")
            with st.container():
                st.info("**Graph Integration Ready**: These search results can be automatically processed through ICE's LightRAG system to extract entities, relationships, and insights for your investment knowledge graph.")
                if st.button("🚀 Process All Results with ICE LightRAG"):
                    st.success("Results queued for LightRAG processing! Check the knowledge graph for new connections.")

# 3. Per-ticker view  
st.markdown("## 📌 Per-Ticker View")
tickers = ["NVDA"] + [r["Ticker"] for r in PORTFOLIO_ROWS if r["Ticker"] != "NVDA"]
ticker = st.selectbox("Open details for:", tickers, index=0)
bundle = TICKER_BUNDLE[ticker]

c1, c2, c3, c4 = st.columns([3,1,1,1])
with c1:
    st.markdown(f"## {ticker} — {bundle['meta']['name']} · {bundle['meta']['sector']}")
    st.markdown(f"**TL;DR:** {bundle['tldr']}")
with c2: st.metric("Priority", bundle["priority"])
with c3: st.metric("Recency", f"{bundle['recency_hours']}h")
with c4: st.metric("Confidence", f"{bundle['confidence']:.2f}")
chip(f"Next: {bundle['next_catalyst']['type']} • {bundle['next_catalyst']['date']}")

l, m, r = st.columns([1.2,1.8,1.2])

with l:
    section_header("KPI Watchlist", "📈")
    for k in bundle["kpis"]:
        st.markdown(f"- **{k['name']}** ({k['last_seen']})  \n_{k['snippet']}_ • ev {k['evidence_count']}")
    section_header("Themes", "🏷️")
    for t in bundle["themes"]: chip(f"{t['name']} • {t['confidence']:.2f}")
    section_header("Soft Signals", "🧭")
    for s in bundle["soft_signals"]:
        icon = "⚠️" if s["polarity"]=="neg" else "❓"
        st.markdown(f"- {icon} {s['date']}: {s['text']}")

with m:
    section_header("Top Reasoning Path", "🧠")
    p = bundle["paths_ranked"][0]
    st.markdown(f"**{p['path_str']}**  \nscore {p['path_score']:.2f} • conf {p['confidence']:.2f}")
    section_header("What changed", "🆕")
    diff=bundle["diff_since_prev"]; new_e=", ".join(f"{e['edge_type']}→{e['target']}" for e in diff["new_edges"])
    st.markdown(f"- New claims: {', '.join(diff['new_claims']) or '–'}")
    st.markdown(f"- New edges: {new_e or '–'}")
    st.markdown(f"- Confidence Δ {diff['confidence_delta']:+0.02f}")

with r:
    section_header("Sources", "📚")
    for s in bundle["sources_ranked"]:
        st.markdown(f"- **{s['title']}** ({s['type']}, {s['date']})")

# 3. Mini subgraph
st.markdown("## 🕸️ Mini Subgraph")
hop = st.slider("Hop depth", 1,3,2)
age = st.select_slider("Recency (days)", [7,14,30,90,180,365], 30)
conf = st.slider("Min conf", 0.0,1.0,0.6,0.05)
etypes = st.multiselect("Edge types", sorted({e[2] for e in EDGE_RECORDS}), [])
contr = st.checkbox("Contrarian only", False)
G = build_graph(EDGE_RECORDS, min_conf=conf, max_age_days=age,
                edge_types=etypes, contrarian_only=contr)
components.html(open(draw_subgraph(G,ticker,radius=hop)).read(), height=520, scrolling=True)

# 4. Tables
st.markdown("---")
st.subheader("📬 Daily Portfolio Brief")
st.dataframe(pd.DataFrame(PORTFOLIO_ROWS), use_container_width=True)
st.subheader("👁 Watchlist Brief")
st.dataframe(pd.DataFrame(WATCHLIST_ROWS), use_container_width=True)


# --------- Email Section ---------
st.subheader("✉️ Email Summary")
email = st.text_input("Recipient Email")
if st.button("Send Email"):
    st.success(f"Summary sent to {email}")
