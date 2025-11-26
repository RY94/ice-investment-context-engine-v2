# ICE News API Integration Architecture

**File**: `INTEGRATION.md`
**Last Updated**: 2025-11-17
**Purpose**: How news APIs integrate into ICE system architecture

---

## Table of Contents

1. [ICE System Overview](#ice-system-overview)
2. [News Integration Architecture](#news-integration-architecture)
3. [Data Pipeline Flow](#data-pipeline-flow)
4. [Storage Integration](#storage-integration)
5. [Query Integration](#query-integration)
6. [System Interactions](#system-interactions)

---

## ICE System Overview

### ICE Architecture (UDMA - User-Directed Modular Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│ ICE SYSTEM ARCHITECTURE                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ice_simplified.py (Orchestrator - 2,508 lines)                │
│       ↓                                                          │
│  ┌──────────────┬──────────────┬──────────────┐                │
│  │ Data Sources │ Processing   │ Storage      │                │
│  ├──────────────┼──────────────┼──────────────┤                │
│  │ • News APIs  │ • LightRAG   │ • Graph DB   │                │
│  │ • Financial  │ • Entities   │ • Signal     │                │
│  │ • Market     │ • Relations  │   Store      │                │
│  │ • SEC        │ • Temporal   │ • Manifest   │                │
│  │ • Emails     │              │              │                │
│  └──────────────┴──────────────┴──────────────┘                │
│       ↓                ↓                ↓                        │
│  Knowledge Graph   Query Engine   Portfolio Intelligence       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Where News APIs Fit

**Role**: Primary real-time signal source for market events and sentiment

**Integration Points**:
1. **Data Ingestion** (`data_ingestion.py`) - Fetches news from 5 APIs
2. **Knowledge Graph** (LightRAG) - Stores news as documents + extracts entities/relations
3. **Query Engine** (`query_router.py`) - Routes news-related queries
4. **Signal Store** (`signal_store.py`) - Stores structured sentiment/events (future)

---

## News Integration Architecture

### Three-Layer Integration

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: API ORCHESTRATION (data_ingestion.py)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  fetch_company_news(symbol, limit, context)                    │
│       ↓                                                          │
│  Proportional distribution: Quota spread across ALL sources    │
│  (Finnhub + MarketAux + Benzinga + NewsAPI*)                   │
│  *NewsAPI excluded in 'live'/'portfolio' when real-time sources available │
│  *Graceful degradation: NewsAPI used if ONLY source (with warning) │
│       ↓                                                          │
│  Inline deduplication → Score & rank → Top N                   │
│       ↓                                                          │
│  Returns: List[Dict] with multi-source metadata                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: KNOWLEDGE GRAPH BUILDING (ice_simplified.py)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  build_knowledge_graph()                                       │
│       ↓                                                          │
│  For each ticker:                                              │
│    news_docs = ingester.fetch_company_news(ticker)            │
│    doc_list.append({                                           │
│        'content': doc['content'],                              │
│        'file_path': doc['file_path'],  # Source attribution   │
│        'type': 'news'                                          │
│    })                                                           │
│       ↓                                                          │
│  lightrag.insert(doc_list)  # Insert into graph               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: QUERY PROCESSING (query_router.py)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User query: "What's the latest news on NVDA?"                 │
│       ↓                                                          │
│  QueryRouter detects: NEWS_PATTERNS                            │
│       ↓                                                          │
│  Routes to: lightrag.query(mode='hybrid')                     │
│       ↓                                                          │
│  Returns: Synthesized answer + source attribution             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Flow Diagram

```
USER
 ↓
ice_building_workflow.ipynb (Cell 15)
 ↓
ice.build_knowledge_graph(holdings=['NVDA', 'AMD'])
 ↓
┌─────────────────────────────────────────────────────────────┐
│ ice_simplified.py:build_knowledge_graph()                   │
│                                                             │
│ For each ticker in holdings:                               │
│   ┌─────────────────────────────────────────────────────┐ │
│   │ Call: self.ingester.fetch_company_news()            │ │
│   │   ↓                                                  │ │
│   │ data_ingestion.py:fetch_company_news()             │ │
│   │   ├─ Fetch Finnhub (real-time)                     │ │
│   │   ├─ Fetch MarketAux (real-time, NLP)              │ │
│   │   ├─ Fetch Benzinga (premium)                      │ │
│   │   └─ Fetch NewsAPI (delayed, conditional)          │ │
│   │   ↓                                                  │ │
│   │ Returns: List[Dict] with metadata                  │ │
│   └─────────────────────────────────────────────────────┘ │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐ │
│   │ Process metadata:                                   │ │
│   │ for doc in news_docs:                               │ │
│   │   content_with_marker = (                          │ │
│   │     f"[SOURCE:{doc['source']}|SYMBOL:{ticker}]\n"  │ │
│   │     f"{doc['content']}"                            │ │
│   │   )                                                 │ │
│   │   doc_list.append({                                │ │
│   │     'content': content_with_marker,                │ │
│   │     'file_path': doc['file_path'],                 │ │
│   │     'type': 'news'                                 │ │
│   │   })                                                │ │
│   └─────────────────────────────────────────────────────┘ │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐ │
│   │ Insert into LightRAG:                              │ │
│   │ self.rag.insert(doc_list)                          │ │
│   │   ↓                                                  │ │
│   │ LightRAG extracts:                                 │ │
│   │   • Entities (companies, people, products)         │ │
│   │   • Relationships (NVDA announced new chip)        │ │
│   │   • Temporal markers (2024-11-15)                  │ │
│   │   ↓                                                  │
│   │ Stores in:                                          │ │
│   │   • Neo4j / NetworkX (graph structure)             │ │
│   │   • nanoDB (vector embeddings)                     │ │
│   └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
 ↓
Knowledge Graph Built
 ↓
Ready for queries
```

---

## Data Pipeline Flow

### Ingestion Pipeline

```
TRIGGER: ice.build_knowledge_graph(holdings=['NVDA'])
     ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 1: API Configuration Check                               │
│ • Check API keys in .env                                       │
│ • Check API switches (finnhub_enabled, etc.)                  │
│ • Initialize ProductionDataIngester                            │
└────────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 2: News Fetching (for each ticker)                       │
│                                                                │
│ news_docs = ingester.fetch_company_news(                      │
│     symbol='NVDA',                                             │
│     limit=5,                                                   │
│     context='portfolio'  ← Default context                    │
│ )                                                              │
│                                                                │
│ Internally (Proportional Distribution):                        │
│ ┌────────────────────────────────────────────────────────────┐│
│ │ Step 1: Determine active sources                           ││
│ │   active = ['finnhub', 'marketaux', 'benzinga']            ││
│ │   (NewsAPI: Included for research/sentiment, or as fallback if only source) ││
│ │                                                            ││
│ │ Step 2: Calculate proportional quotas                      ││
│ │   fetch_budget = 5 * 1.2 = 6  (20% dedup buffer)          ││
│ │   quotas = [2, 2, 2]  (distributed across 3 sources)      ││
│ │                                                            ││
│ │ Step 3: Fetch from ALL sources simultaneously              ││
│ │   Finnhub:   GET api.finnhub.io/v1/company-news           ││
│ │     ↓ Fetch: 2 articles                                   ││
│ │     ↓ Enrich: {freshness:'real-time', tier:1, score:12.0} ││
│ │                                                            ││
│ │   MarketAux: GET api.marketaux.com/v1/news/all            ││
│ │     ↓ Fetch: 2 articles                                   ││
│ │     ↓ Enrich: {freshness:'real-time', tier:1, score:10.0} ││
│ │                                                            ││
│ │   Benzinga:  GET api.benzinga.com/api/v2/news             ││
│ │     ↓ Fetch: 2 articles                                   ││
│ │     ↓ Enrich: {premium:True, tier:1, score:19.5}          ││
│ │                                                            ││
│ │ Step 4: Inline deduplication (normalized headlines)        ││
│ │   Total fetched: 6 articles                                ││
│ │   Unique after dedup: ~5 articles                          ││
│ │                                                            ││
│ │ Step 5: Score & rank, return top 5                         ││
│ └────────────────────────────────────────────────────────────┘│
│                                                                │
│ Result: List[Dict] with multi-source metadata (3 sources)     │
└────────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 3: Metadata Enhancement                                  │
│                                                                │
│ for doc in news_docs:                                         │
│     # Add SOURCE markers for statistics tracking              │
│     content_with_marker = (                                   │
│         f"[SOURCE:{doc['source'].upper()}|"                   │
│         f"SYMBOL:NVDA|"                                        │
│         f"DATE:{datetime.now().isoformat()}]\n"               │
│         f"{doc['content']}"                                   │
│     )                                                          │
│                                                                │
│     # Prepare for LightRAG insertion                          │
│     doc_list.append({                                         │
│         'content': content_with_marker,                       │
│         'file_path': doc['file_path'],  # Unique ID          │
│         'type': 'news'                                        │
│     })                                                         │
└────────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 4: Deduplication Check (Manifest)                        │
│                                                                │
│ for doc in doc_list:                                          │
│     doc_id = doc['file_path']  # e.g., "finnhub:NVDA_123"    │
│                                                                │
│     if manifest.is_document_ingested(doc_id):                 │
│         logger.info(f"Skipping duplicate: {doc_id}")          │
│         continue  # Already in graph, skip                    │
│                                                                │
│     # New document, proceed with insertion                    │
│     filtered_docs.append(doc)                                 │
│     manifest.add_document(doc_id, ...)                        │
└────────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 5: LightRAG Insertion                                    │
│                                                                │
│ self.rag.insert(filtered_docs)                                │
│                                                                │
│ LightRAG Processing:                                           │
│ ┌────────────────────────────────────────────────────────────┐│
│ │ For each document:                                         ││
│ │   1. Entity Extraction (LLM/NLP):                          ││
│ │      • Companies: "NVIDIA", "AMD", "Intel"                 ││
│ │      • People: "Jensen Huang", "Lisa Su"                   ││
│ │      • Products: "H100", "MI300", "CUDA"                   ││
│ │      • Events: "earnings", "product launch", "acquisition" ││
│ │                                                            ││
│ │   2. Relationship Extraction:                              ││
│ │      • (NVIDIA, ANNOUNCED, H100 GPU)                       ││
│ │      • (Jensen Huang, CEO_OF, NVIDIA)                      ││
│ │      • (H100, COMPETES_WITH, AMD MI300)                    ││
│ │                                                            ││
│ │   3. Temporal Enhancement:                                 ││
│ │      • Extract dates: "2024-11-15"                         ││
│ │      • Add temporal edges to graph                         ││
│ │                                                            ││
│ │   4. Vector Embedding:                                     ││
│ │      • Generate embeddings for semantic search             ││
│ │      • Store in nanoDB vector store                        ││
│ │                                                            ││
│ │   5. Graph Storage:                                        ││
│ │      • Add nodes (entities)                                ││
│ │      • Add edges (relationships)                           ││
│ │      • Index for fast retrieval                            ││
│ └────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
     ↓
COMPLETE: News integrated into Knowledge Graph
```

---

## Storage Integration

### Dual Storage Architecture

ICE uses **dual storage** for news data:

```
NEWS DOCUMENT
     ↓
┌─────────────────────────────────────────────────────────────┐
│ STORAGE LAYER 1: LightRAG Knowledge Graph                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Purpose: Relationship-based reasoning, multi-hop queries   │
│                                                             │
│ Stores:                                                     │
│ • Full document text (with SOURCE markers)                 │
│ • Extracted entities (NVIDIA, Jensen Huang, H100)          │
│ • Relationships (NVIDIA ANNOUNCED H100)                    │
│ • Temporal markers (2024-11-15)                            │
│ • Vector embeddings (for semantic search)                  │
│                                                             │
│ Query Types:                                                │
│ • "What companies did NVIDIA mention?"                     │
│ • "Find connections between NVDA and AI trends"            │
│ • "Show me news about H100 GPU"                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
     ↓ (Future enhancement)
┌─────────────────────────────────────────────────────────────┐
│ STORAGE LAYER 2: Signal Store (Planned Future Integration) │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Purpose: Structured signals for quantitative analysis      │
│                                                             │
│ Planned Tables:                                             │
│ • news_sentiment (ticker, date, sentiment_score, source)   │
│ • news_events (ticker, date, event_type, impact)           │
│ • news_volume (ticker, date, article_count, sources)       │
│                                                             │
│ Query Types (future):                                       │
│ • "Show sentiment trend for NVDA last 30 days"             │
│ • "Find stocks with >5 articles today"                     │
│ • "Detect sentiment inflection points"                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Storage Flow

```
News Document
     ↓
┌──────────────────────────────┐
│ SOURCE Attribution           │
│ [SOURCE:FINNHUB|SYMBOL:NVDA] │
└──────────────────────────────┘
     ↓
┌──────────────────────────────┐
│ LightRAG Graph               │
│ • Nodes: Entities            │
│ • Edges: Relationships       │
│ • Properties: Metadata       │
└──────────────────────────────┘
     ↓ (Future)
┌──────────────────────────────┐
│ Signal Store                 │
│ • Structured sentiment       │
│ • Event indicators           │
│ • Volume metrics             │
└──────────────────────────────┘
```

---

## Query Integration

### Query Routing Patterns

```python
# query_router.py integration

NEWS_PATTERNS = [
    r'latest news',
    r'recent (news|articles|updates)',
    r'what.*happening',
    r'breaking news',
    r'news about',
]

def route_query(query: str) -> QueryType:
    """Route query based on pattern matching"""
    
    # Check if query is about news
    if any(re.search(pattern, query.lower()) for pattern in NEWS_PATTERNS):
        return QueryType.NEWS_SEMANTIC
    
    # ... other routing logic
```

### Query Flow

```
USER: "What's the latest news on NVIDIA?"
     ↓
┌────────────────────────────────────────────────────────────────┐
│ query_router.py: Detect NEWS_PATTERNS                         │
│ → QueryType.NEWS_SEMANTIC                                     │
└────────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────────┐
│ lightrag.query(                                               │
│     query="latest news on NVIDIA",                            │
│     mode='hybrid',  # Combine graph + semantic search         │
│     only_need_context=False                                   │
│ )                                                              │
└────────────────────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────────────────────┐
│ LightRAG Processing:                                          │
│                                                                │
│ 1. Semantic Search (nanoDB):                                  │
│    Find documents with embeddings similar to query            │
│    → Returns: Top 5 most relevant news articles               │
│                                                                │
│ 2. Graph Traversal:                                            │
│    Find entities related to "NVIDIA"                          │
│    → Returns: Related companies, products, events             │
│                                                                │
│ 3. Synthesis (LLM):                                            │
│    Combine search results + graph context                     │
│    Generate answer with source attribution                    │
│    → Returns: "Based on recent news from [FINNHUB], NVIDIA..."│
└────────────────────────────────────────────────────────────────┘
     ↓
ANSWER with SOURCE markers intact
```

---

## System Interactions

### Component Interaction Map

```
┌─────────────────────────────────────────────────────────────────┐
│ ICE SYSTEM COMPONENT INTERACTIONS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ice_building_workflow.ipynb (User Interface)                  │
│       ↓                                                          │
│  ice_simplified.py (Orchestrator)                              │
│       ↓                ↓                ↓                        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                   │
│  │  Data    │   │ Process  │   │ Storage  │                   │
│  │ Ingestion│   │  Layer   │   │  Layer   │                   │
│  └──────────┘   └──────────┘   └──────────┘                   │
│       ↓              ↓              ↓                            │
│                                                                  │
│  NEWS INTEGRATION FLOW:                                         │
│                                                                  │
│  data_ingestion.py ────→ ProductionDataIngester                 │
│       ↓                                                          │
│  fetch_company_news() ───→ [API Calls]                         │
│       ↓                         ↓                                │
│  List[Dict] ────→ Add metadata ────→ Score & rank              │
│       ↓                                                          │
│  ice_simplified.py ────→ Process for LightRAG                   │
│       ↓                                                          │
│  lightrag.insert() ────→ Extract entities/relations             │
│       ↓                                                          │
│  Knowledge Graph ────→ Query-ready                              │
│       ↓                                                          │
│  query_router.py ────→ Route news queries                       │
│       ↓                                                          │
│  lightrag.query() ────→ Answer with attribution                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cross-Module Dependencies

```
ice_simplified.py
    ↓ imports
data_ingestion.py (ProductionDataIngester)
    ↓ imports
config.py (ICEConfig)
    ↓ loads
.env (API keys)

ice_simplified.py
    ↓ uses
lightrag (ice_rag_fixed.py)
    ↓ stores in
nanoDB + NetworkX/Neo4j
```

---

**Last Updated**: 2025-11-17
**Version**: 1.1 (with graceful degradation)
**Maintained By**: ICE Development Team

**Recent Updates**:
- 2025-11-17: Added graceful degradation pattern - NewsAPI used as fallback when it's the only available source
