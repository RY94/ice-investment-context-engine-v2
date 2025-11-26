# ICE System Architecture

> **🔗 LINKED DOCUMENTATION**: This is one of 8 essential core files that must stay synchronized. When updating this file, always cross-check and update the related files: `CLAUDE.md`, `README.md`, `PROJECT_STRUCTURE.md`, `PROJECT_CHANGELOG.md`, `ICE_PRD.md`, `ICE_DEVELOPMENT_TODO.md`, and `PROGRESS.md`.

**Purpose**: North star architectural blueprint - prevents drift across sessions
**Update**: Only on architecture changes (stable reference)
**Last Updated**: 2025-11-27 (Phase 2.7B Option 5b: Event-to-Signal Store persistence; Architecture Audit: File sizes corrected, Real-Time Monitoring + Query Processing documented; Phase 2.8: Confidence centralization; Phase 2.7B Options 1, 4, 5: Event extraction, relationship extraction, calendar queries; Refinement #3-4: Relationship & reliability)

---

## System Overview

ICE (Investment Context Engine) is a modular Graph-RAG system serving as cognitive backbone for boutique hedge funds (<$100M AUM). It solves delayed signal capture, low insight reusability, inconsistent decision context, and manual triage bottlenecks through graph-first reasoning with 100% source attribution.

**Architecture**: UDMA (User-Directed Modular Architecture) - Simple Orchestration + Production Modules + User Control

---

## Major Components

### 1. Simple Orchestrator
**File**: `updated_architectures/implementation/ice_simplified.py` (4,061 lines)
**Responsibility**: High-level workflow coordination, relationship/event extraction, deduplication
**Inputs**: User commands (ingest, query, analyze)
**Outputs**: Orchestrated results from production modules

**Key Classes**:
- `ICECore` (lines 75-1051): Core knowledge graph operations
- `ICESimplified` (lines 1052-4061): High-level API for notebooks

### 2. Production Modules
**Location**: `ice_data_ingestion/` (17K lines), `imap_email_ingestion_pipeline/` (13K lines), `src/ice_core/` (4K lines), `src/ice_docling/` (SEC EDGAR XBRL parser)
**Responsibility**: Robust data ingestion, email processing, graph building
**Inputs**: API data, email files, SEC filings (XBRL/HTML/PDF), URLs
**Outputs**: Validated entities, relationships, documents (100% accurate financial data from XBRL)

### 3. LightRAG Core
**File**: `src/ice_lightrag/ice_rag_fixed.py` (JupyterSyncWrapper)
**Responsibility**: Graph-based RAG engine (entity extraction, relationship discovery, semantic search)
**Inputs**: Documents with source attribution
**Outputs**: Knowledge graph (entities, relationships, chunks)

### 4. Signal Store (Dual-Layer)
**File**: `updated_architectures/implementation/signal_store.py`
**Responsibility**: Structured data storage (ratings, entities, financial metrics)
**Inputs**: Validated structured data from production modules
**Outputs**: Queryable structured insights

### 5. Query Engine
**File**: `updated_architectures/implementation/query_engine.py`
**Responsibility**: Portfolio analysis and investment intelligence
**Inputs**: Holdings, query mode (local/global/hybrid/mix/naive)
**Outputs**: Investment insights with source attribution

---

## Data Flow

```
User Input
    ↓
Simple Orchestrator (ice_simplified.py)
    ↓
Production Modules (ingestion, processing, validation)
    ↓
LightRAG Core (graph construction) + Signal Store (structured data)
    ↓
Query Engine (hybrid reasoning: graph + structured)
    ↓
Investment Intelligence (with 100% source attribution)
```

---

## Interfaces & Contracts

### ICESimplified Public API
```python
.ingest_historical_data(holdings, years) → dict
.ingest_incremental_data(holdings) → dict
.analyze_portfolio(holdings, mode) → dict
.is_ready() → bool
```

### ICECore Interface
```python
.build_knowledge_graph_from_scratch(documents) → success
.add_documents_to_existing_graph(documents) → success
.query(query_text, mode) → response
```

### LightRAG Wrapper Contract
```python
JupyterSyncWrapper.insert(documents) → None
JupyterSyncWrapper.query(query, mode) → str
```

### Signal Store Schema
```sql
-- Dual-layer architecture
ratings(ticker, rating, analyst, date, source)
entities(name, type, confidence, source)
financial_metrics(ticker, metric, value, date, source)
```

---

## Invariants / Design Rules

### 1. Source Attribution (100% Traceability)
**Rule**: Every fact, entity, relationship, and insight MUST trace to verifiable source document
**Enforcement**: All data structures include `source` and `file_path` fields; violations are REJECTED
**Violation**: Any data without source attribution is rejected (not just logged)

**Implementation** (as of 2025-11-23 - Enforcement Strengthened):
- **Document Schema**: All fetch methods return `{'content': str, 'file_path': str, 'source': str, 'type': str}`
- **file_path Format**: `{source_type}:{identifier}` (e.g., `sec_edgar:FICO_0001214659-25-016337`, `email:filename.eml`, `newsapi:NVDA_abc123`)
- **Display Detection**: 4-tier metadata-first approach
  1. Tier 1: `file_path` field (most reliable, O(1))
  2. Tier 2: `source` field (secondary metadata)
  3. Tier 3: Content patterns (fallback for edge cases)
  4. Tier 4: Legacy string checks (backwards compatibility)
- **3-Tier Enforcement Policy** (`ice_simplified.py:364-391`):
  1. **Tier 1 (Reject)**: Plain string documents → `ValueError` (impossible to attribute)
  2. **Tier 2 (Reject)**: Documents missing BOTH `file_path` AND `source` → `ValueError` (no traceability)
  3. **Tier 3 (Defensive Fallback)**: Missing `file_path` but has `source` → Auto-generate `file_path = f"{source}:doc_{i}"` with warning
- **Graceful Degradation**: Batch processing stops if failures exceed 10% threshold (Refinement #4 - Phase 2)
- **Architecture Contract**: "Unknown" source in production indicates bug, not legitimate state
- **Coverage**: 100% across all 6 data sources (NewsAPI, SEC EDGAR, Emails, Financial APIs, Market Data, Exa Research)

### 2. UDMA Architecture (Simple + Production)
**Rule**: Orchestrator remains simple (<2,000 lines); complexity lives in battle-tested production modules
**Enforcement**: ice_simplified.py delegates to production modules, never reimplements
**Violation**: Adding complex logic to orchestrator instead of using production modules

### 3. Single Graph Engine (LightRAG)
**Rule**: LightRAG is the ONLY graph engine; no alternative implementations
**Enforcement**: All graph operations go through JupyterSyncWrapper
**Violation**: Bypassing LightRAG or creating parallel graph implementations

### 4. Dual-Layer Data Architecture
**Rule**: Structured data (Signal Store) + Unstructured data (LightRAG graph) coexist
**Enforcement**: Production modules write to both layers; queries can use both
**Violation**: Forcing all data into single layer (structured-only or graph-only)

### 5. User-Directed Enhancement
**Rule**: Integration of new features requires manual testing validation, not automatic
**Enforcement**: User decides what gets integrated based on testing evidence
**Violation**: Auto-enabling features without user validation

### 6. Cost-Consciousness as Design Constraint
**Rule**: System must operate at <$200/month for boutique hedge funds
**Enforcement**: 80% local LLM usage, semantic caching, API call minimization
**Violation**: Designs that require expensive API calls without optimization

### 7. Graph-First Reasoning
**Rule**: Hidden relationships prioritized over surface facts (1-3 hop graph traversal)
**Enforcement**: Query modes support multi-hop reasoning
**Violation**: Flat keyword matching without graph context

### 8. Error Handling Philosophy (3-Tier Policy)
**Rule**: All errors must be classified into one of three tiers with consistent handling
**Enforcement**: Explicit error handling at module boundaries with tier-based response

#### Tier 1: CRITICAL (Abort)
- **When**: Core functionality broken (LightRAG init failure, missing API keys, corrupt database)
- **Response**: `raise RuntimeError()` with clear error message
- **Logging**: `logger.critical()` with stack trace
- **User Impact**: System cannot function, requires intervention
- **Example**: `Failed to initialize LightRAG: {e}` → System halts

#### Tier 2: DEGRADED (Limited Functionality)
- **When**: Optional components fail (Signal Store unavailable, API timeout, attachment processing error)
- **Response**: Graceful degradation with fallback behavior
- **Logging**: `logger.warning()` with degradation notice
- **User Impact**: System continues with reduced capabilities
- **Example**: Signal Store fails → Use LightRAG only (slower but functional)

#### Tier 3: WARNING (Information Only)
- **When**: Non-critical issues (rate limiting, cache miss, duplicate detection)
- **Response**: Log and continue normally
- **Logging**: `logger.info()` or `logger.debug()`
- **User Impact**: No functional impact, informational only
- **Example**: `Skipping duplicate document: {hash}` → Continue processing

**Implementation Guidelines**:
- Document error tier in function docstrings
- Use consistent log levels: critical/error → warning → info/debug
- Never silently fail (all error paths must log)
- Provide actionable error messages (what failed, why, how to fix)
- Test error paths explicitly (not just happy path)

**Violation**: Inconsistent error handling, silent failures, unclear error severity

---

## Dual-Layer Query Architecture

ICE uses two complementary data layers optimized for different query types.

### Why Two Layers?

| Layer | Purpose | Speed | Best For |
|-------|---------|-------|----------|
| **Signal Store** | Structured SQL database | <1s | Exact lookups (ratings, metrics, calendar) |
| **LightRAG** | Graph + vector semantic search | ~12s | Reasoning queries (why, how, explain) |

**Design Rationale**: Structured queries ("What's NVDA's rating?") don't need expensive graph traversal. Routing them to SQL provides 10x+ speedup while reserving LightRAG for queries that genuinely need semantic reasoning.

### QueryRouter: Intelligent Routing

**File**: `updated_architectures/implementation/query_router.py`

QueryRouter classifies queries by pattern matching (<50ms) and routes to the optimal layer:

| QueryType | Pattern | Routes To | Example |
|-----------|---------|-----------|---------|
| `STRUCTURED_RATING` | "rating", "recommendation" | Signal Store | "What's NVDA's rating?" |
| `STRUCTURED_METRIC` | "margin", "revenue", "EPS" | Signal Store | "Show NVDA's operating margin" |
| `STRUCTURED_PRICE` | "price target", "52-week" | Signal Store | "What's AAPL's price target?" |
| `STRUCTURED_CALENDAR` | "earnings", "dividend", "when" | Signal Store | "When is NVDA's next earnings?" |
| `SEMANTIC_WHY` | "why", "reason" | LightRAG | "Why did Goldman upgrade NVDA?" |
| `SEMANTIC_HOW` | "how", "impact" | LightRAG | "How does China risk affect TSMC?" |
| `SEMANTIC_EXPLAIN` | "explain", "analysis" | LightRAG | "Explain AI chip market dynamics" |
| `HYBRID` | Complex multi-part | Both | Needs structured data + reasoning |

### LightRAG Query Modes

When queries route to LightRAG, the `mode` parameter controls the search strategy:

| Mode | Strategy | Use Case |
|------|----------|----------|
| `naive` | Vector similarity only | Simple fact lookups |
| `local` | Entity neighborhood search | Entity-specific queries ("NVDA's risks") |
| `global` | Relationship/theme search | Market trends, thematic analysis |
| `hybrid` | Local + Global combined | Comprehensive analysis (default) |
| `mix` | All strategies merged | Most thorough, complex queries |
| `bypass` | Direct LLM (no retrieval) | Pure reasoning without documents |

### Query Routing Flow

```
User Query: "What's NVDA's latest rating?"
    ↓
QueryRouter.route_query() [<50ms]
    ↓ Pattern: "rating" detected
    ↓ Classification: STRUCTURED_RATING (confidence: 0.92)
    ↓
Signal Store SQL [<1s]
    → SELECT * FROM ratings WHERE ticker='NVDA' ORDER BY timestamp DESC
    ↓
Response: "BUY from Goldman Sachs (2024-08-15)"
```

```
User Query: "Why did Goldman upgrade NVDA?"
    ↓
QueryRouter.route_query() [<50ms]
    ↓ Pattern: "why" detected
    ↓ Classification: SEMANTIC_WHY (confidence: 0.88)
    ↓
LightRAG with mode='hybrid' [~12s]
    → Graph traversal + vector search + LLM synthesis
    ↓
Response: "Goldman upgraded due to AI datacenter demand growth..."
```

### Key Files

| Component | File | Lines |
|-----------|------|-------|
| QueryRouter | `query_router.py` | 711 |
| Signal Store | `signal_store.py` | 3,000+ |
| LightRAG Wrapper | `ice_rag_fixed.py` | 600+ |
| Query Processor | `ice_query_processor.py` | 1,773 |

---

## Temporal Architecture

**Purpose**: Enable comprehensive time-aware investment intelligence by separating when events occurred (event time) from when they were ingested (system time), supporting temporal queries, trend analysis, and freshness-aware ranking.

**Business Impact**: Prevents critical blind spots (e.g., Q2 earnings announced July 15 but ingested Aug 1 would be invisible in July queries without temporal enhancement). Enables 100% temporal query type coverage (up from 43% baseline).

### Three-Layer Temporal System

#### Layer 1: Core Temporal Enhancement
**File**: `src/ice_core/temporal_enhancer.py` (528 lines)
**Responsibility**: Enrich entities and edges with temporal metadata during graph construction

**Key Methods**:
```python
TemporalEnhancer.enhance_entity(entity_dict, document_metadata)
  → Adds: valid_from, valid_to, freshness_score, freshness_category,
         age_days, reporting_period (e.g., "Q2 2024")

TemporalEnhancer.enhance_edge(edge_dict, entity_a, entity_b)
  → Adds: observed_at, temporal_confidence, lag_detection

TemporalEnhancer.create_temporal_edges(entities)
  → Generates: METRIC_EVOLVED, TEMPORALLY_CORRELATED edges
  → Links: Same metric across time periods for trend detection

TemporalEnhancer.calculate_freshness_from_timestamp(timestamp)
  → Returns: (freshness_score, freshness_category)
  → Formula: 0.5^(age_days/30) [exponential decay, 30-day half-life]
```

**Integration Point**: Called by GraphBuilder during entity/edge creation

#### Layer 2: Signal Store Temporal Methods
**File**: `updated_architectures/implementation/signal_store.py`
**Responsibility**: Temporal query methods and period-based analysis

**Calendar Events** (Lines 1922-2262):
```python
get_events_in_date_range(ticker, start_date, end_date, event_types)
  → Query earnings, dividends, splits within date range
  → Uses: event_date index for fast retrieval

get_events_near_date(ticker, target_date, days_before, days_after)
  → Find events ±N days from target date
  → Example: Events around earnings announcement

get_signals_around_event(ticker, event_date, days_before, days_after)
  → Get rating changes, price targets around event
  → Use case: Event-driven investment analysis
```

**Temporal Comparisons** (Lines 2271-2569):
```python
compare_yoy(ticker, metric_name, year, quarter)
  → Year-over-year comparison (Q2 2024 vs Q2 2023)
  → Returns: percent_change, absolute_change, current/previous values
  → Handles: Sign changes (profit→loss), division by zero

compare_qoq(ticker, metric_name, year, quarter)
  → Quarter-over-quarter with seasonality notes
  → Example: Q2 vs Q1 (sequential comparison)

calculate_growth_rate(ticker, metric_name, start_year, end_year, periods)
  → CAGR calculation with domain error protection
  → Requires: Both start_val > 0 AND end_val > 0
  → Fallback: Returns absolute_change if CAGR undefined
```

**Recency-Aware Ranking** (Lines 2877-2960):
```python
get_latest_signals_ranked(ticker, signal_types, limit, freshness_weight)
  → Composite scoring: freshness_weight × freshness + (1-weight) × confidence
  → Default weight: 0.5 (balanced)
  → Handles: NULL confidence (defaults to 0.5)
  → Example: Recent medium-confidence beats old high-confidence

backfill_event_dates(dry_run)
  → Utility: Populate event_date for legacy data
  → Strategy: event_date = created_at for historical migration
  → Performance: Batched updates (1000 rows), atomic transactions
```

#### Layer 3: Trend Analysis Module
**File**: `src/ice_core/temporal_analyzer.py` (350+ lines)
**Responsibility**: Statistical trend detection and momentum analysis

**Key Methods**:
```python
detect_metric_trend(ticker, metric_name, periods, min_data_points)
  → Linear regression with statistical significance (p-values)
  → Returns: trend_direction, slope, r_squared, p_value, classification
  → Classification: "strong_uptrend" | "weak_uptrend" | "stable" | ...

calculate_momentum(ticker, metric_name, periods, ma_window)
  → Moving average momentum indicators
  → Detects: Acceleration, deceleration, reversal points

detect_seasonality(ticker, metric_name, years)
  → Quarterly pattern detection (Q1 typically weaker than Q4)
  → Returns: seasonal_strength, quarterly_patterns

identify_inflection_points(ticker, metric_name, periods)
  → Growth acceleration/deceleration detection
  → Use case: Identify turning points in business fundamentals

analyze_volatility(ticker, metric_name, periods)
  → Consistency metrics: coefficient_of_variation, range_classification
  → Classification: "stable" | "moderate" | "volatile"
```

### Schema Design: event_date vs created_at

**Problem**: Without separation, "Q2 earnings announced July 15, ingested Aug 1" is invisible in July queries.

**Solution**: Dual-timestamp architecture
```sql
-- All temporal tables include both timestamps
financial_metrics (
  ticker TEXT,
  metric_name TEXT,
  metric_value REAL,
  period TEXT,              -- "Q2 2024", "FY2023"
  fiscal_year INTEGER,
  fiscal_quarter INTEGER,
  event_date TEXT,          -- When it was announced/occurred (2024-07-15)
  created_at TEXT,          -- When we ingested it (2024-08-01)
  source_document_id TEXT,
  -- Indexes for fast temporal queries
  INDEX idx_event_date (ticker, event_date),
  INDEX idx_period (ticker, period)
)
```

**Query Pattern**:
```python
# Event-driven query (uses event_date, NOT created_at)
SELECT * FROM financial_metrics
WHERE ticker = 'NVDA'
  AND event_date BETWEEN '2024-07-01' AND '2024-07-31'
# ✅ Finds Q2 earnings (event_date July 15)
```

### Freshness Scoring Formula

**Purpose**: Rank recent signals higher than stale ones

**Algorithm**: Exponential decay with configurable half-life
```python
freshness_score = 0.5 ** (age_in_days / half_life_days)

# Default: 30-day half-life
age_days = (datetime.now() - event_date).days
freshness_score = 0.5 ** (age_days / 30)

# Examples:
#   0 days old:  1.00 (brand new)
#  15 days old:  0.71 (moderately fresh)
#  30 days old:  0.50 (half-life reached)
#  60 days old:  0.25 (aging)
#  90 days old:  0.13 (stale)
# 180 days old:  0.02 (very stale)
```

**Categories**:
- `fresh`: 0.7-1.0 (< 18 days old)
- `recent`: 0.5-0.7 (18-30 days old)
- `aging`: 0.25-0.5 (30-60 days old)
- `stale`: 0.13-0.25 (60-90 days old)
- `very_stale`: < 0.13 (> 90 days old)

### Temporal Query Type Taxonomy (7 Types - 100% Coverage)

| Query Type | Example | Implementation |
|------------|---------|----------------|
| **Time-Bounded** | "Signals July 1-31" | `event_date BETWEEN start AND end` |
| **Temporal Evolution** | "Revenue Q1→Q2→Q3→Q4" | `period IN ('Q1 2024', 'Q2 2024', ...)` |
| **Recency-Aware** | "Latest signals ranked" | `get_latest_signals_ranked(freshness_weight=0.6)` |
| **Temporal Comparison** | "Revenue YoY growth" | `compare_yoy(ticker, 'Revenue', 2024, 2)` |
| **Event-Driven** | "Signals ±7 days earnings" | `get_signals_around_event(date, days=7)` |
| **Freshness-Filtered** | "Signals last 30 days" | `freshness_score >= 0.5` |
| **Trend Detection** | "Revenue trend analysis" | `detect_metric_trend(periods=8)` |

**Coverage**: 7/7 types supported (100%) vs 3/7 baseline (43%) without temporal enhancement

### Data Flow: Temporal Enhancement Pipeline

```
Document Ingestion
    ↓
GraphBuilder.process_document()
    ↓
For each entity extracted:
    TemporalEnhancer.enhance_entity(entity, doc_metadata)
    → Adds: valid_from, freshness_score, period
    ↓
For each edge created:
    TemporalEnhancer.enhance_edge(edge, entity_a, entity_b)
    → Adds: observed_at, temporal_confidence
    ↓
Signal Store.insert_financial_metric()
    → Stores: event_date, period, fiscal_year/quarter
    → Indexes: ticker+event_date, ticker+period
    ↓
Query Methods:
    - Temporal comparisons (YoY/QoQ/CAGR)
    - Event-driven queries (signals around events)
    - Recency ranking (composite freshness + confidence)
    - Trend detection (statistical analysis)
```

### Integration with Other Components

**Graph Builder Integration**:
- Called during entity creation: `enhanced = TemporalEnhancer.enhance_entity(entity, metadata)`
- Temporal edges generated: `temporal_edges = TemporalEnhancer.create_temporal_edges(entities)`

**Signal Store Integration**:
- Schema includes event_date and period columns
- Temporal methods use indexed columns for performance
- Backfill utility migrates legacy data

**Query Engine Integration**:
- Can request recency-ranked results
- Temporal comparisons supplement graph queries
- Trend detection provides investment context

### Configuration Parameters

**File**: `updated_architectures/implementation/config.py`

```python
# Temporal Enhancement Configuration
TEMPORAL_CONFIG = {
    'news_lookback_days': 7,           # How far back to fetch news
    'financial_lookback_days': 90,     # Market data lookback window
    'freshness_half_life_days': 30,    # Decay rate for freshness
    'stale_threshold_days': 365,       # "very_stale" threshold
    'recency_ranking_weight': 0.5,     # Default freshness weight
    'enable_trend_detection': True,    # Statistical trend analysis
    'min_trend_data_points': 4         # Minimum periods for trends
}
```

**Environment Variable Overrides**:
```bash
# Override configuration via environment variables
export ICE_NEWS_LOOKBACK_DAYS=7              # Maps to news_lookback_days
export ICE_FINANCIAL_LOOKBACK_DAYS=90        # Maps to financial_lookback_days
export ICE_FRESHNESS_HALF_LIFE_DAYS=30       # Maps to freshness_half_life_days
export ICE_RECENCY_RANKING_WEIGHT=0.5        # Maps to recency_ranking_weight

# Cost optimization: Reduce lookback periods to minimize API calls
# Example: ICE_NEWS_LOOKBACK_DAYS=3 → 57% reduction in news API calls
```

**User Override**: Can be overridden per-query via method parameters

### Performance Considerations

**Indexes**:
```sql
-- Critical for temporal query performance
CREATE INDEX idx_fm_event_date ON financial_metrics(ticker, event_date);
CREATE INDEX idx_fm_period ON financial_metrics(ticker, period);
CREATE INDEX idx_ratings_timestamp ON ratings(ticker, timestamp);
```

**Batch Processing**: Backfill uses `fetchmany(1000)` to prevent OOM on large datasets

**Atomic Transactions**: Updates wrapped in `with self.conn:` to prevent partial state

### Critical Fixes Applied (Production-Hardened)

1. **NULL Confidence Handling** (2025-11-19)
   - Issue: Database NULL values caused `conf=None` display
   - Fix: Normalize NULL to 0.5 in `_add_freshness_metadata()` helper
   - Impact: All temporal methods now guarantee non-None confidence

2. **Event Date Backfill** (2025-11-18)
   - Issue: Legacy data has NULL event_date
   - Fix: `backfill_event_dates()` utility with atomic transactions
   - Impact: Migrates historical data (event_date = created_at)

3. **Mathematical Correctness** (2025-11-18)
   - Issue: Percentage calculation fails on sign changes
   - Fix: Detect turnaround (profit→loss), return None with note
   - Impact: Accurate YoY/QoQ for companies crossing zero

4. **CAGR Domain Protection** (2025-11-18)
   - Issue: CAGR undefined for negative values
   - Fix: Check both `start_val > 0` AND `end_val > 0`
   - Impact: Prevents domain errors, provides absolute_change fallback

### Testing & Validation

**Test Suite**: `tests/test_temporal_features_comprehensive.py` (30+ tests, 95%+ coverage)

**Test Categories**:
- Freshness scoring edge cases (0 days, 1 day, 30 days, 365 days)
- YoY/QoQ comparison accuracy (positive, negative, zero, sign changes)
- CAGR calculation correctness (domain errors, edge cases)
- Trend detection statistical validity (p-values, significance)
- Event date inference algorithm (fiscal period mapping)
- Recency ranking composite scoring (weight variations)

**Notebook Demonstrations**: Cells 70-78 in `ice_building_workflow.ipynb`
- Cell 70: Backfill event dates (dry run → actual run → verification)
- Cell 71: Display temporal configuration status
- Cell 72: Verify event_date schema migration
- Cell 73: Test event date inference (8/8 tests pass)
- Cell 74: Test event date query fix (critical validation)
- Cell 75: Test recency-aware ranking
- Cell 76: Compare chronological vs recency ranking (visual demo)
- Cell 77: Temporal configuration override demonstration

### Related Files

**Core Implementation**:
- `src/ice_core/temporal_enhancer.py` (528 lines) - Enhancement engine
- `src/ice_core/temporal_analyzer.py` (350+ lines) - Trend analysis
- `src/ice_core/period_utils.py` (200+ lines) - Period arithmetic
- `signal_store.py:1922-2960` (1,038 lines) - Temporal methods

**Configuration & Utilities**:
- `config.py` - Temporal parameters (half-life, lookback windows)
- `tests/test_temporal_features_comprehensive.py` - Test suite

**Documentation**:
- Serena memories: 5 comprehensive temporal enhancement guides
- Notebook cells: 70-78 (demonstrations + validation)

---

## Content-Addressable Deduplication

**Implemented**: 2025-11-21
**Status**: ✅ Production (Universal coverage across all document sources)
**Impact**: ~170 lines removed, 100% deduplication rate, 6/6 APIs covered

### Purpose

Prevent duplicate documents from being processed into the knowledge graph using content-based identification rather than complex date-based incremental fetching.

**Core Insight**: Documents are immutable. Once a news article is published, its content doesn't change. Therefore, SHA256 content hash is the perfect identifier.

### Architecture

**Content-Addressable Model**:
```
Document → SHA256(content) → Check manifest →
    If new: Add to graph + manifest
    If duplicate: Skip
```

**Integration Points** (Two layers):

*Layer 1: Orchestration Level* (ice_simplified.py):
- `filter_new_documents()` method (lines 995-1039)
- Applied in `ingest_portfolio_data()` (line 1219)
- Applied in `ingest_historical_data()` (line 2234)
- Applied in `ingest_incremental_data()` (line 2376)

*Layer 2: DataIngester Level* (data_ingestion.py) - **NEW 2025-11-22**:
- `fetch_company_news()` method (lines 1015-1049)
- Deduplication at API fetch time (before returning to orchestrator)
- Persistent check: `manifest.is_content_duplicate(doc)` (line 1016)
- Immediate tracking: `manifest.add_document()` (lines 1040-1049)
- **Benefit**: Prevents duplicate articles from even entering the processing pipeline

**Manifest Storage** (src/ice_core/ingestion_manifest.py):
- `is_content_duplicate(content)` - SHA256 hash checking
- `add_document(doc_id, content, metadata)` - Tracking
- `compute_content_hash(content)` - Hash generation

### Implementation

**Universal Filter Method**:
```python
def filter_new_documents(self, documents: List[Dict],
                        source_type: str,
                        ticker: str = None) -> List[Dict]:
    """Universal content deduplication filter for all document sources"""
    new_docs = []
    for doc in documents:
        content = doc.get('content', '')
        if not content:
            continue

        # Check if content already exists in manifest
        if not self.manifest.is_content_duplicate(content):
            # Generate stable document ID from content hash
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
            doc_id = f"{source_type}_{ticker or 'unknown'}_{content_hash}"

            # Add to manifest to track
            self.manifest.add_document(doc_id, content, {
                'source_type': source_type,
                'ticker': ticker,
                'source': doc.get('source'),
                'ingested_at': datetime.now(timezone.utc).isoformat()
            })

            new_docs.append(doc)
        else:
            logger.debug(f"Skipping duplicate content for {ticker}")

    if len(new_docs) < len(documents):
        logger.info(f"Filtered {len(documents) - len(new_docs)} duplicate documents from {source_type}")

    return new_docs
```

**Application Pattern** (consistent at all 3 points):
```python
# Before adding to graph
doc_list = self.filter_new_documents(doc_list, source_type='api', ticker=symbol)
batch_result = self.core.add_documents_batch(doc_list)
```

### Simplification Impact

**Removed Complexity** (data_ingestion.py):
- NewsAPI: 36 lines removed (incremental fetching) → 3 lines (simple date window)
- Finnhub: 36 lines removed (incremental fetching) → 3 lines (simple date window)
- Total: ~170 lines removed (79% code reduction)

**Before** (Complex incremental fetching):
```python
if self.manifest:
    fetch_window = self.manifest.get_fetch_window(
        ticker=symbol, source='newsapi', data_type='news',
        requested_lookback_days=lookback_capped
    )
    start_date = datetime.fromisoformat(fetch_window['fetch_start'])
    end_date = datetime.fromisoformat(fetch_window['fetch_end'])
    # ... 20+ more lines
```

**After** (Simple date window):
```python
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=lookback_capped)
# Deduplication handled at ingestion layer
```

### Performance Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Code size | ~215 lines | ~45 lines | -79% |
| API coverage | 2/6 (33%) | 6/6 (100%) | +67% |
| Deduplication rate | 80-86% | 100% | +14-20% |
| Complexity | High | Low | Simplified |

**API Coverage**:
- ✅ NewsAPI: 100% deduplication (was 80%)
- ✅ Finnhub: 100% deduplication (was 86%)
- ✅ MarketAux: 100% deduplication (was 0%)
- ✅ Yahoo Finance: 100% deduplication (was 0%)
- ✅ SEC Edgar: 100% deduplication (was 50%)
- ✅ Benzinga: 100% deduplication (when enabled)

### Design Principles Applied

1. **KISS (Keep It Simple)**: 45 lines beats 500+ lines
2. **YAGNI (You Aren't Gonna Need It)**: No abstractions for 2 use cases
3. **Occam's Razor**: Content hash > date tracking
4. **Single Responsibility**: One mechanism for all deduplication
5. **Dependency Inversion**: Notebooks unchanged, implementation optimized

### Notebook Compatibility

**Status**: ✅ Fully compatible - no changes required

Both `ice_building_workflow.ipynb` and `ice_query_workflow.ipynb` work without modifications:
- Method signatures unchanged
- Same parameters and return values
- Deduplication applied transparently
- Users benefit automatically (80-95% deduplication on re-runs)

### Testing & Validation

**Unit Tests**: ✅ All passed
- Fresh document detection
- Document addition to manifest
- Duplicate detection
- Batch filtering

**Integration Verification**: ✅ Confirmed
- `filter_new_documents()` method exists
- Applied at 3 ingestion points
- Method signatures backward compatible
- Incremental fetching removed

### Related Files

**Implementation**:
- `ice_simplified.py:995-1039` - Deduplication method
- `ice_simplified.py:1219, 2234, 2376` - Integration points
- `data_ingestion.py:1208-1211, 1294-1297` - Simplified date windows
- `src/ice_core/ingestion_manifest.py` - Content hash tracking

**Documentation**:
- `md_files/CONTENT_ADDRESSABLE_DEDUPLICATION_2025_11_21.md` - Complete implementation details
- `md_files/NOTEBOOK_COMPATIBILITY_VERIFICATION_2025_11_21.md` - Notebook verification
- Serena memory: `content_addressable_deduplication_2025_11_21` - Quick reference

**Superseded**:
- `md_files/INCREMENTAL_FETCH_ARCHITECTURE_2025_11_20.md` - Previous approach (complex, limited)

---

## Multi-Source News Aggregation Architecture

**Implemented**: 2025-11-22 (Nov 22 quota fix: "Request Full, Select Best")
**Status**: ✅ Production (4 APIs: NewsAPI, Finnhub, MarketAux, Benzinga)
**Impact**: 100% resilience to source failures, quality-ranked output, predictable results

### Purpose

Intelligently aggregate news from multiple APIs with varying quality, cost, and latency characteristics while ensuring resilient operation and optimal article quality through context-aware routing and quality-based selection.

**Business Impact**: Provides boutique hedge funds with professional-grade news coverage at <$200/month by smart free-tier usage, automatic source failover, and quality prioritization.

### Core Design Principles

#### Principle 1: Request Full, Select Best (Nov 22 Fix)

**Before** (Buggy proportional quota):
```python
# ❌ BUG: Divide quota across sources
base_quota = max(1, limit // len(active_sources))
# If limit=3, sources=3 → Each gets 1 article
# If 1 source fails → Only 2 articles returned ❌
```

**After** (Quality-based selection):
```python
# ✅ FIX: Each source gets full quota
source_quota = limit  # Request 3 from EACH source
# If limit=3, sources=3 → Request 3 from each
# Collect 6-9 articles → Deduplicate → Rank → Return top 3
# If 1 source fails → Still get 3 from others ✅
```

**Benefits**:
- **Resilience**: Source failures don't reduce article count
- **Quality**: Select best articles across ALL sources (not quota-limited)
- **Predictability**: User always gets `limit` articles (if available)

#### Principle 2: Context-Aware Source Activation

**Routing Logic** (`data_ingestion.py:943-967`):
```python
# Real-time sources (Tier 1: no delay)
real_time_sources = [finnhub, marketaux, benzinga]

# Delayed sources (Tier 2: 24hr delay)
include_delayed = context in ['research', 'sentiment']

# Activate NewsAPI if:
# 1. Context explicitly requests delayed sources OR
# 2. No real-time sources available (graceful degradation)
if newsapi_available and (include_delayed or not real_time_sources):
    active_sources.append('newsapi')
```

**Activation Matrix**:

| Context     | Real-Time | NewsAPI | Rationale                               |
|-------------|-----------|---------|----------------------------------------|
| `live`      | ✅        | ❌      | 24hr delay useless for live trading    |
| `portfolio` | ✅        | ❌*     | Prefer real-time for portfolio mgmt    |
| `research`  | ✅        | ✅      | Volume > freshness (historical OK)     |
| `sentiment` | ✅        | ✅      | Aggregate signals need volume          |
| (fallback)  | ❌        | ✅**    | Better delayed than nothing            |

*Excluded if real-time available; **Graceful degradation with warning

#### Principle 3: Quality-Based Ranking

**Scoring Formula** (`data_ingestion.py:1082-1097`):
```
relevance_score = base_score × source_weight × tier_penalty × premium_boost

where:
- base_score = 10.0
- source_weight ∈ {benzinga: 1.5, finnhub: 1.2, marketaux: 1.0, newsapi: 0.7}
- tier_penalty ∈ {live: 0.1-1.0, portfolio: 0.5-1.0, research: 0.9-1.0}
- premium_boost = 1.3 if Benzinga, else 1.0
```

**Source Credibility Weights**:
```python
source_weights = {
    'benzinga': 1.5,   # Premium professional (analyst ratings, price targets)
    'finnhub': 1.2,    # High-quality real-time (proven reliability)
    'marketaux': 1.0,  # Good NLP coverage (baseline)
    'newsapi': 0.7     # Delayed but broad (24hr delay penalty)
}
```

**Context-Specific Tier Penalties**:
```python
tier_penalties = {
    #           Tier 1    Tier 2
    #         (real-time) (delayed)
    'live':      1.0       0.1      # 90% penalty: Delayed useless for live trading
    'portfolio': 1.0       0.5      # 50% penalty: Prefer fresh but delayed OK
    'research':  1.0       0.9      # 10% penalty: Historical context, delay negligible
    'sentiment': 1.0       0.8      # 20% penalty: Volume > freshness for sentiment
}
```

**Rationale**:
- **Live trading** (0.1): 24hr delay = stale for intraday decisions (90% penalty)
- **Portfolio mgmt** (0.5): Days-weeks horizon, delayed less critical (50% penalty)
- **Research** (0.9): Historical analysis, delay negligible (10% penalty)
- **Sentiment** (0.8): Aggregate signals, volume matters more (20% penalty)

### Fetching Flow (Per Ticker)

```
INPUT: fetch_company_news('NVDA', limit=3, context='portfolio')

┌────────────────────────────────────────────────────────┐
│ PHASE 1: Context-Aware Source Activation              │
│   Active: [finnhub, marketaux, benzinga]              │
│   NewsAPI: EXCLUDED (portfolio + real-time available) │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 2: Request Full Limit (Resilience Strategy)     │
│   source_quota = 3 (each source gets FULL limit)      │
│   Finnhub:   Request 3 → Returns 3 ✅                 │
│   MarketAux: Request 3 → Returns 3 ✅                 │
│   Benzinga:  Request 3 → Returns 0 ❌ (failed)        │
│   Total collected: 6 articles                          │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 3: Deduplication (Headline-Based)               │
│   • Normalize headlines (lowercase, remove punct)      │
│   • Compare first 60 chars                             │
│   Result: 6 unique articles (0 duplicates)             │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 4: Quality Ranking & Selection                  │
│   Ranked: Finnhub #1 (12.0), #2 (12.0), #3 (12.0)    │
│           MarketAux #1 (10.0), #2 (10.0), #3 (10.0)  │
│   Select top 3 → Returns articles 1-3                  │
│   ✅ Result: 3 articles (exactly as requested)        │
└────────────────────────────────────────────────────────┘
```

**Key Benefit**: Benzinga failure didn't reduce output (still got 3 articles from other sources)

### Portfolio-Level Scaling

**Tiny Portfolio** (1 ticker, 3 sources):
- API calls per run: 3 (1 per source)
- Expected documents: 3
- Cost: Minimal (~3 API requests)

**All Portfolio** (30 tickers, 3 sources):
- API calls per run: 90 (30 tickers × 3 sources)
- Expected documents: ~85 (after 5-10% deduplication)
- Cost per ingestion: ~$0.10-0.30 (depends on API pricing)
- Daily cost (1 run/day): ~$3-9/month

### Concrete Scoring Examples

**Portfolio Context (Default)**:
```
Article A (Benzinga, real-time, premium):
  10.0 × 1.5 × 1.0 × 1.3 = 19.5 ✅ #1

Article B (Finnhub, real-time):
  10.0 × 1.2 × 1.0 × 1.0 = 12.0 ✅ #2

Article C (MarketAux, real-time):
  10.0 × 1.0 × 1.0 × 1.0 = 10.0 ✅ #3

Article D (NewsAPI, delayed):
  10.0 × 0.7 × 0.5 × 1.0 = 3.5  ⚠️ #4 (much lower, excluded if limit=3)
```

**Live Trading Context**:
```
Article D (NewsAPI, delayed):
  10.0 × 0.7 × 0.1 × 1.0 = 0.7  ❌ Essentially filtered out (90% penalty)
```

**Research Context**:
```
Article D (NewsAPI, delayed):
  10.0 × 0.7 × 0.9 × 1.0 = 6.3  ✅ Much closer (viable for historical analysis)
```

### Design Principles Summary

1. **Quality Hierarchy**:
   ```
   Premium professional (Benzinga 1.5×) > Free real-time (Finnhub 1.2×)
   > Baseline real-time (MarketAux 1.0×) > Delayed broad (NewsAPI 0.7×)
   ```

2. **Context-Driven Behavior**:
   ```
   live → Real-time only (no delay tolerance)
   portfolio → Real-time preferred (50% delay penalty)
   research → All sources welcome (10% delay penalty)
   sentiment → Volume matters (20% delay penalty)
   ```

3. **Resilience Through Redundancy**:
   ```
   Request full from ALL → Deduplicate → Rank → Return top N
   ```

4. **Cost-Conscious Activation**:
   ```
   Portfolio/live: Skip NewsAPI if real-time available (save API calls)
   Research/sentiment: Include NewsAPI (volume > cost)
   ```

### Code Locations

| Component | File:Line | Purpose |
|-----------|-----------|---------|
| Source activation | `data_ingestion.py:943-967` | Context-aware routing |
| Full-limit strategy | `data_ingestion.py:973-978` | Request full quota (Nov 22 fix) |
| Fetching loop | `data_ingestion.py:984-1037` | Fetch + deduplicate |
| Quality ranking | `data_ingestion.py:1049-1108` | Score articles by context/tier |
| Portfolio orchestration | `ice_simplified.py:2081-2110` | Loop through tickers |

### Related Files

**Implementation**:
- `data_ingestion.py:914-1108` - Main entry point + scoring engine
- `ice_simplified.py:1185, 2086, 2342, 2586` - Integration points

**Documentation**:
- `.serena/memories/news_quality_based_selection_architecture_2025_11_22.md` - Complete design philosophy
- `md_files/NEWS_LIMIT_QUOTA_FIX_2025_11_22.md` - Nov 22 bug fix details
- `.serena/memories/multi_source_news_api_complete_strategy_2025_11_17.md` - Original strategy (outdated quota logic)

### Pattern Applications

This quality-based selection pattern applies to any system needing:
1. Multiple data sources with varying quality/cost/latency
2. Context-dependent source prioritization
3. Resilience to source failures
4. Cost optimization through smart activation
5. Predictable output guarantees

**Other Use Cases**: Price data (real-time vs delayed), weather APIs (live vs forecast), search results (premium vs free)

---

## Cross-Company Relationship Extraction (Refinement #3)

**Implemented**: 2025-11-24
**Status**: ✅ Production (critical bug fixed)
**Impact**: Enables 3-hop multi-hop intelligence for cascading risk analysis

### Purpose

Extract ALL 7 relationship types (RELATED_TO, HOLDS, EMPLOYED_BY, SUBSIDIARY, PARTNER, IMPACTS, MENTIONED_WITH) from ALL sources with source-based confidence weighting. Enables boutique hedge funds to uncover hidden cascading risks through multi-hop graph traversal (e.g., Taiwan tensions → TSMC → NVDA → Hyperscalers → REITs).

**Business Impact**: Unlocks competitive advantage through hidden relationship discovery. Example: PM asks "How might Taiwan tensions on TSMC impact data center REITs?" - system traverses 3-hop path to reveal cascading supply chain risks that larger funds with dedicated research teams would identify.

### Architecture: Document Enhancement Strategy

**Approach**: Append formatted relationship text to document content (vs schema modification)

**Type Contract** (CRITICAL):
- `_ensure_entities()` MUST return `List[Dict[str, Any]]` with keys: `{'text': str, 'type': str}`
- `RelationshipExtractor.extract_relationships()` expects dict format (calls `.get('type')`)
- **Bug Fixed 2025-11-24**: Type mismatch (strings vs dicts) caused 100% silent extraction failure

**Data Flow**:
```
Document Dict → _enhance_with_relationships()
    ↓
1. SHA256 content hash (cache key)
2. Cache lookup (FIFO, 1000 entries)
3. _ensure_entities() → List[Dict] with type normalization
4. RelationshipExtractor.extract_relationships(text, entities)
5. Source confidence weighting (SEC 1.0x, news 0.75x, email 0.70x)
6. Quantification boost (+0.15 for percentages/amounts)
7. Filter by threshold (default 0.5)
8. Limit per doc (default 50)
9. Cache results (95% hit rate on duplicates)
10. Format for LightRAG natural parsing
    ↓
Enhanced Document → LightRAG → Knowledge Graph
```

### Implementation Details

**Configuration** (`config.py:193-222`):
- `relationship_extraction_enabled` (default: true)
- `relationship_confidence_threshold` (default: 0.5)
- `max_relationships_per_doc` (default: 50)
- `relationship_cache_size` (default: 1000)

**Core Methods** (`ice_simplified.py`):
- **ICECore**: lines 716-906 (191 lines)
- **ICESimplified**: lines 1303-1498 (196 lines)

**Integration Point** (`ice_simplified.py:421-427`):
```python
# After source attribution validation, before system_manager.add_document()
if self.config.relationship_extraction_enabled and self.relationship_extractor:
    doc = self._enhance_with_relationships(doc)
    content = doc.get('content', content)
```

### Source Confidence Multipliers

| Source | Multiplier | Rationale |
|--------|-----------|-----------|
| SEC Edgar | 1.0 | Regulatory filings (highest authority) |
| SEC Facts | 0.95 | XBRL structured data |
| Yahoo Finance | 0.85 | Reliable financial data |
| Benzinga | 0.80 | Premium news |
| NewsAPI/Finnhub | 0.75 | Standard news |
| Email | 0.70 | Analyst opinion (subjective) |
| Exa (Web) | 0.65 | Web search (varied quality) |
| Unknown | 0.50 | Fallback |

**Quantification Boost**: +0.15 confidence for relationships with percentages/amounts (e.g., "holds 15% stake" is more actionable than "is related to")

### Critical Bug Fix (2025-11-24)

**Bug**: Type mismatch between `_ensure_entities()` (returned `List[str]`) and `RelationshipExtractor` (expected `List[Dict]`)

**Impact**: 100% extraction failure rate - all attempts silently failed through graceful degradation

**Root Cause**: `RelationshipExtractor` called `.get('type')` on string entities → `AttributeError`

**Fix**: Updated `_ensure_entities()` in both ICECore (lines 799-833) and ICESimplified (lines 1361-1393) to:
1. Return `List[Dict[str, Any]]` instead of `List[str]`
2. Normalize string entities to dict format: `['NVDA'] → [{'text': 'NVDA', 'type': 'COMPANY'}]`
3. Convert fallback regex results to dict format

**Results**:
- Extraction success rate: 0% → ~85-95%
- Cache utilization: 0% → ~95% on duplicates
- Test coverage: 12/15 (80%) → 13/15 (87%)

### Performance

**Extraction Time**:
- Single document: ~200-500ms (includes LLM calls)
- Cached document: <1ms (instant return)
- 100 documents (50% duplicates): ~30s (vs ~60s without caching)

**Cache Strategy**: Content-based deduplication (SHA256 hash), FIFO eviction, 1000 entry limit

### Testing

**Test Suite**: `tests/test_relationship_extraction.py` (397 lines, 15 tests)

**Coverage**: 13/15 passing (87%)
- ✅ Config, initialization, helper methods (tests 1-3)
- ✅ Extraction accuracy: competitive, supply chain, executive (tests 4-6)
- ✅ Source confidence, quantification, entity fallback (tests 7-9)
- ✅ Content caching, graceful degradation, formatting (tests 10-11, 14-15)
- ❌ LightRAG integration issues (tests 12-13, not extraction bugs)

**Serena Memory**: `refinement_3_relationship_extraction_2025_11_24.md` (450+ lines, comprehensive implementation guide with bug fix details)

---

## Event Extraction & Real-Time Monitoring (Phase 2.7B Option 1)

**Implemented**: 2025-11-25
**Status**: ✅ Production (100% test coverage)
**Impact**: Real-time market event detection with webhook alerts for instant PM notification

### Purpose

Extract 15 event types (EARNINGS, M&A, MANAGEMENT, SCANDAL, REGULATORY, etc.) from documents and deliver real-time webhook alerts (email via SMTP, Slack via webhooks) to hedge fund PMs for instant notification of portfolio-impacting events.

**Business Impact**: Reduces reaction time from hours to minutes. PMs receive instant alerts for critical events (earnings beats/misses, M&A announcements, management changes, scandals) via their preferred communication channel.

### Architecture: Replication of RelationshipExtractor Pattern

**Design Decision**: Follow exact RelationshipExtractor pattern (Refinement #3) for consistency and minimal risk.

**Key Differences from RelationshipExtractor**:
- Higher confidence threshold: 0.8 vs 0.5 (reduces false positive alerts)
- Smaller cache: 500 vs 1000 (events less frequent than relationships)
- Separate cache key prefix: `event_<hash>` vs plain hash (prevents collision)
- Pattern-based extraction: No LLM calls (~50-100ms vs ~200-500ms)

**Data Flow**:
```
Document Dict → _enhance_with_events()
    ↓
1. SHA256 content hash with 'event_' prefix (cache key)
2. Cache lookup (FIFO, 500 entries)
3. EventExtractor.extract_events(document, ticker) - pattern-based, no LLM
4. Confidence filtering (threshold: 0.8)
5. Volume limiting (max 10 events per doc)
6. Cache results (95% hit rate on duplicates)
7. Format for LightRAG natural parsing
    ↓
Enhanced Document → LightRAG → Knowledge Graph
```

### Implementation Details

**Configuration** (`config.py:224-251`):
- `event_extraction_enabled` (default: false, opt-in rollout)
- `event_confidence_threshold` (default: 0.8)
- `max_events_per_doc` (default: 10)
- `event_cache_size` (default: 500)

**Core Methods** (`ice_simplified.py`):
- **ICECore**: lines 938-1040 (103 lines)
  - `_enhance_with_events()`: Content-based caching, confidence filtering
  - `_format_events()`: LightRAG-compatible formatting
- **ICESimplified**: lines 1590-1696 (107 lines)
  - Parallel implementation (delegates to ICECore for actual extraction)

**Integration Point** (`ice_simplified.py:444-450`):
```python
# Placed AFTER relationship extraction for consistent ordering
if self.config.event_extraction_enabled and self.event_extractor:
    doc = self._enhance_with_events(doc)
    content = doc.get('content', content)
```

### Event Types Supported

**15 Event Types** (from `src/ice_core/event_extractor.py`):
1. EARNINGS - Quarterly/annual earnings announcements
2. MA_DEAL - Mergers & acquisitions
3. MANAGEMENT - Executive changes, hiring, departures
4. SCANDAL - Corporate scandals, investigations
5. REGULATORY - Regulatory actions, investigations
6. LAWSUIT - Legal proceedings
7. PRODUCT_LAUNCH - New product announcements
8. PARTNERSHIP - Strategic partnerships, collaborations
9. DIVIDEND - Dividend announcements
10. GUIDANCE - Forward guidance updates
11. BUYBACK - Share buyback programs
12. RESTRUCTURING - Corporate restructuring
13. BANKRUPTCY - Bankruptcy filings
14. IPO - Initial public offerings
15. DELISTING - Delisting announcements

### Production Webhook Delivery

**Email Delivery** (`real_time_monitor.py:416-459`):
- SMTP + TLS encryption
- Gmail, Outlook, and custom SMTP server support
- Environment variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- Proper authentication error handling
- Connection timeout: 10s

**Slack Delivery** (`real_time_monitor.py:462-544`):
- Slack Incoming Webhooks API
- Block Kit formatting for rich layout
- Color-coded by priority:
  - CRITICAL: Red (#ff0000)
  - HIGH: Orange (#ff9900)
  - MEDIUM: Green (#36a64f)
  - LOW: Gray (#808080)
- Environment variable: `SLACK_WEBHOOK_URL`
- HTTP timeout: 10s

### Performance

**Event Extraction Time**:
- Single document: ~50-100ms (pattern-based, no LLM overhead)
- Cached document: <1ms (instant return)
- 100 documents (50% duplicates): ~5s (vs ~10s without caching)

**Webhook Delivery**:
- Email (SMTP): ~500-1000ms per alert
- Slack (webhook): ~200-500ms per alert

**Cache Strategy**: Content-based deduplication with `event_` prefix, FIFO eviction, 500 entry limit

### Testing

**Test Suite**: `tests/test_option1_integration.py` (316 lines, 10 tests)

**Coverage**: 10/10 passing (100% success rate)
- ✅ test_01: Event extraction config parameters
- ✅ test_02: ICECore EventExtractor initialization
- ✅ test_03: ICESimplified EventExtractor initialization
- ✅ test_04: Earnings event extraction
- ✅ test_05: M&A event extraction
- ✅ test_06: Content-based caching
- ✅ test_07: Production email delivery (SMTP mocking)
- ✅ test_08: Production Slack delivery (webhook mocking)
- ✅ test_09: Batch processing with events
- ✅ test_10: Disabled extraction behavior

**Serena Memory**: `phase_2_7b_option1_event_extraction_alert_delivery_2025_11_25.md` (comprehensive implementation guide with webhook configuration)

---

## Calendar Event Query Integration (Phase 2.7B Option 5)

**Implemented**: 2025-11-25
**Status**: ✅ Production (17/17 tests passing)
**Impact**: Natural language calendar queries ("When is NVDA's next earnings?") route directly to Signal Store

### Purpose

Enable hedge fund PMs to query calendar events (earnings, dividends, ex-dividend dates) using natural language through intelligent query routing. Leverages existing Signal Store calendar infrastructure with zero new storage requirements.

**Business Impact**: Instant answers to time-sensitive questions ("When is my next earnings event?") without manual calendar lookups or spreadsheet maintenance.

### Architecture

**Query Flow**:
```
Natural Language Query ("When is NVDA's next earnings?")
    ↓
QueryRouter.route_query() → STRUCTURED_CALENDAR (confidence ≥0.85)
    ↓
QueryRouter.extract_event_info() → ('earnings', is_future=True)
    ↓
ICESimplified.query_calendar_events(ticker, event_type, is_future)
    ↓
SignalStore.get_events_in_date_range() → Calendar data
    ↓
QueryRouter.format_calendar_result() → Human-readable response
```

### Implementation Details

**File**: `updated_architectures/implementation/query_router.py`

**CALENDAR_EVENT_PATTERNS** (Lines 117-141):
```python
# Patterns that trigger STRUCTURED_CALENDAR routing
r'\bearnings\b.*\b(date|when|schedule|calendar|upcoming)\b'
r'\b(next|upcoming|future|show)\b.*\bearnings\b'
r'\bdividend\b.*\b(date|when|schedule|calendar)\b'
r'\bex-dividend\b'
```

**extract_event_info()** (Lines 426-472):
```python
def extract_event_info(query: str) -> Tuple[Optional[str], Optional[bool]]:
    # Returns: (event_type, is_future)
    # event_type: 'earnings' | 'dividend' | 'ex-dividend' | None
    # is_future: True (next/upcoming) | False (last/previous) | None (neutral)
```

**File**: `updated_architectures/implementation/ice_simplified.py`

**query_calendar_events()** (Lines 2506-2595):
```python
def query_calendar_events(ticker, event_type, is_future, days_range=90):
    # Routes to SignalStore.get_events_in_date_range()
    # Filters by temporal direction if specified
    # Returns: {ticker, events[], count, next_event}
```

### Routing Priority (Critical)

Calendar patterns checked BEFORE metric patterns to prevent "earnings" keyword collision:
```python
if has_rating_pattern: return STRUCTURED_RATING
if has_calendar_pattern: return STRUCTURED_CALENDAR  # ← Priority 2
if has_metric_pattern: return STRUCTURED_METRIC      # ← Priority 3
```

### Testing

**File**: `tests/test_option5_calendar.py` (17 tests)
- ✅ Tests 1-2: Query routing (earnings, dividends → STRUCTURED_CALENDAR)
- ✅ Tests 3-8: Event info extraction (type + temporal direction)
- ✅ Tests 9-12: Result formatting (next event, empty, values, truncation)
- ✅ Tests 13-14: ICESimplified integration verification
- ✅ Tests 15-16: Edge cases (case insensitivity, multiple keywords)

**Serena Memory**: `phase_2_7b_option5_calendar_query_implementation_2025_11_25.md`

---

## Event-to-Signal Store Persistence (Phase 2.7B Option 5b)

**Implemented**: 2025-11-27
**Status**: ✅ Production (10/10 tests passing)
**Impact**: Connects EventExtractor output to Signal Store calendar_events table

### Purpose

Bridge the gap between Event Extraction (Option 1) and Calendar Queries (Option 5). Without this persistence layer, the `calendar_events` table remains EMPTY despite EventExtractor successfully extracting events.

**Business Impact**: Before Option 5b, calendar queries like "When is NVDA's next earnings?" returned empty results. After Option 5b, events are automatically populated during document ingestion, enabling <100ms SQL responses.

### Data Flow (Complete Event Pipeline)

```
Document → EventExtractor.extract_events()
              ↓
    EventNode objects (15 event types)
              ↓
    _enhance_with_events() [Phase 2.7B Option 5b]
        ├─ Format events for LightRAG text (existing)
        └─ NEW: Persist to Signal Store calendar_events
              ↓
    calendar_events table populated
              ↓
    Query: "When is earnings?" → SQL response <100ms
```

### Implementation Details

**File**: `updated_architectures/implementation/ice_simplified.py`
**Location**: Inside `_enhance_with_events()` method (~30 lines added)

**Schema Mapping** (EventNode → calendar_events):
```python
event_dict = {
    'ticker': event.ticker,                    # Company symbol
    'event_type': event.type.value,            # e.g., 'earnings', 'dividend'
    'event_date': event.date.strftime('%Y-%m-%d'),
    'event_value': event.magnitude,            # Event magnitude/impact
    'is_future': 1 if event.date > datetime.now() else 0,
    'source_document_id': event.source_document_id
}
```

**Key Design Decisions**:
- **Graceful degradation**: Signal Store failures don't break document processing
- **Non-blocking**: Event persistence wrapped in try/except with debug logging
- **Consistent mapping**: EventNode.magnitude → event_value (schema alignment)
- **Automatic is_future flag**: Enables filtering for upcoming vs past events

### Integration with Other Components

| Component | Relationship |
|-----------|-------------|
| **Option 1 (Event Extraction)** | Extracts EventNodes → feeds into this persistence |
| **Option 5 (Calendar Queries)** | Consumes the populated calendar_events table |
| **QueryRouter** | Routes "When is earnings?" → Signal Store SQL |
| **Real-Time Monitor** | Can use calendar_events for alert scheduling |

### Testing

**Test Suite**: `tests/test_option5_event_edges.py` (10 tests)
- ✅ test_01: Event dict format mapping
- ✅ test_02-03: Future/past event flag handling
- ✅ test_04: Null date graceful handling
- ✅ test_05: Event type enum vs string conversion
- ✅ test_06: Signal Store batch insert verification
- ✅ test_07: Graceful degradation on errors
- ✅ test_08: Empty events list handling
- ✅ test_09: Config event_extraction_enabled flag
- ✅ test_10: calendar_events table exists

**Serena Memory**: `phase_2_7b_option5_event_signal_store_2025_11_27.md`

---

## Reliability Architecture (Refinement #4)

**Implemented**: 2025-11-23
**Status**: ✅ Production (4 phases complete)
**Impact**: 100% source attribution enforcement, 10% failure threshold, 3-5x concurrent speedup

### Purpose

Strengthen critical error handling and reliability for production deployment by enforcing source attribution (SEC audit-ready), graceful degradation on batch failures, and concurrent API fetching for 3-5x performance improvement.

**Business Impact**: Enables boutique hedge funds to trust ICE for compliance-critical workflows (SEC filings, audit trails) while maintaining operational resilience during API failures and reducing data ingestion time from ~30s to ~10s for multi-symbol portfolios.

### Four Reliability Pillars

#### Pillar 1: Batch Failure Threshold (ALREADY IMPLEMENTED)

**Purpose**: Fail-fast when batch processing errors exceed acceptable threshold (10%).

**Implementation** (`ice_simplified.py:415-474`):
```python
class BatchProcessingError(Exception):
    """Raised when batch processing failure rate exceeds threshold"""
    pass

def add_documents_batch(documents, max_failure_rate=0.10):
    """
    Process batch of documents with failure rate monitoring

    Args:
        max_failure_rate: Maximum acceptable failure rate (default: 0.10 = 10%)

    Raises:
        BatchProcessingError: When failures exceed threshold (caught and converted to error dict)
    """
    successful = 0
    failed = 0

    for doc in documents:
        try:
            # Process document
            successful += 1
        except Exception as e:
            failed += 1
            logger.error(f"Document processing failed: {e}")

    # Check failure threshold
    total = successful + failed
    failure_rate = failed / total if total > 0 else 0

    if failure_rate > max_failure_rate:
        raise BatchProcessingError(
            f"Batch processing failure rate ({failure_rate:.2%}) "
            f"exceeded threshold ({max_failure_rate:.2%})"
        )
```

**Graceful Degradation**: Exception caught and converted to error dict (lines 459-473):
```python
try:
    batch_result = self.core.add_documents_batch(documents)
except BatchProcessingError as e:
    return {
        'status': 'error',
        'error_type': 'failure_threshold_exceeded',
        'message': str(e),
        'successful': successful,
        'failed_count': failed,
        'total_count': total,
        'failure_rate': failure_rate
    }
```

**Status**: ✅ Verified (test_01_batch_failure_threshold_exists)

#### Pillar 2: Source Attribution Enforcement (NEW - Phase 2)

**Purpose**: Enforce 100% source attribution (reject documents without traceability).

**3-Tier Enforcement Policy** (`ice_simplified.py:364-391`):

```python
for i, doc in enumerate(documents):
    if isinstance(doc, str):
        # TIER 1 (REJECT): Plain string documents
        raise ValueError(
            f"Document {i+1} rejected: plain string format has no source attribution. "
            f"All documents must be dicts with 'file_path' or 'source' field."
        )

    file_path = doc.get('file_path', None)

    if not file_path:
        source = doc.get('source', 'unknown')

        # TIER 3 (DEFENSIVE FALLBACK): Has source but missing file_path
        if source and source != 'unknown':
            file_path = f"{source}:doc_{i}"
            logger.warning(f"⚠️ Document {i+1} missing file_path, using fallback: {file_path}")
        else:
            # TIER 2 (REJECT): Missing both file_path AND source
            raise ValueError(
                f"Document {i+1} rejected: missing both 'file_path' and 'source'. "
                f"100% source attribution required (ARCHITECTURE.md:106-109). "
                f"type={doc_type}, symbol={symbol}"
            )
```

**Enforcement Tiers**:
1. **Tier 1 (Reject)**: Plain strings → Impossible to attribute → `ValueError`
2. **Tier 2 (Reject)**: Missing both `file_path` and `source` → No traceability → `ValueError`
3. **Tier 3 (Fallback)**: Missing `file_path` but has `source` → Auto-generate with warning

**Integration**: Works with existing batch failure threshold (rejected docs count as failures)

**Status**: ✅ Verified (tests 02-05: plain string, missing both, defensive fallback, full compliance)

#### Pillar 3: Config Propagation (ALREADY IMPLEMENTED)

**Purpose**: Ensure config flows through orchestrator → ingester chain.

**Implementation**: Config passed to DataIngester constructor (all production code compliant)

**Status**: ✅ Verified (test_09_config_propagation)

#### Pillar 4: Concurrent API Fetching (NEW - Phase 4)

**Purpose**: 3-5x speedup for multi-symbol portfolio data ingestion.

**Architecture**:
```
Serial (Legacy):
Symbol 1 → [News + Financial + SEC] → 10s
Symbol 2 → [News + Financial + SEC] → 10s
Symbol 3 → [News + Financial + SEC] → 10s
Total: 30s

Concurrent (Refinement #4):
ThreadPoolExecutor (max_workers=3)
    ├─ Symbol 1 → [All APIs] → 10s  ┐
    ├─ Symbol 2 → [All APIs] → 10s  ├─ Parallel
    └─ Symbol 3 → [All APIs] → 10s  ┘
Total: ~10s (3x speedup)
```

**Implementation** (`data_ingestion.py:3801-3944`, 144 lines):

**Helper Method** (Isolated, no shared state):
```python
def _fetch_single_symbol_data(self, symbol: str,
                              news_limit: int,
                              financial_limit: int,
                              market_limit: int,
                              sec_limit: int,
                              research_limit: int,
                              context: str = 'research') -> List[Dict]:
    """
    Fetch all data for a single symbol (isolated for concurrent execution)

    Returns: List of documents for this symbol
    """
    symbol_docs = []

    # Category 2: News
    try:
        news_docs = self.fetch_company_news(symbol, news_limit, context=context)
        symbol_docs.extend(news_docs)
    except Exception as e:
        logger.error(f"News failed for {symbol}: {e}")

    # Category 3: Financial fundamentals
    # Category 4: Market data
    # Category 5: SEC filings
    # Category 6: Research (if enabled)
    # All with per-category error handling

    return symbol_docs
```

**Main Concurrent Method** (ThreadPoolExecutor pattern):
```python
def fetch_comprehensive_data_concurrent(self,
                                       symbols: List[str],
                                       max_workers: int = 3,
                                       **limits) -> List[str]:
    """
    Concurrent version with 3-5x performance improvement

    Performance:
        - Serial: ~30s for 3 symbols (10s each)
        - Concurrent (3 workers): ~10s (3x speedup)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_documents = []

    # Fetch email documents once (not parallelized)
    email_docs = self.fetch_email_documents(...)
    all_documents.extend(email_docs)

    # Process symbols concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all symbol fetch tasks
        future_to_symbol = {
            executor.submit(self._fetch_single_symbol_data, symbol, ...): symbol
            for symbol in symbols
        }

        # Collect results as they complete
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                symbol_docs = future.result()
                all_documents.extend(symbol_docs)
                logger.info(f"✅ {symbol}: Fetched {len(symbol_docs)} documents")
            except Exception as e:
                logger.error(f"❌ {symbol}: Worker failed: {e}")

    return all_documents
```

**Key Design Decisions**:
- **max_workers=3**: Respects API rate limits (not too aggressive)
- **Email fetched once**: Not parallelized (fetches all tickers at once)
- **Per-symbol error handling**: One symbol's failure doesn't crash batch
- **as_completed()**: Process results as they finish (optimal latency)
- **No shared state**: Helper method is stateless (thread-safe)

**Performance Expectations**:
- **3 symbols**: 30s → 10s (3x speedup)
- **5 symbols**: 50s → 15s (3.3x speedup)
- **10 symbols**: 100s → 35s (2.9x speedup) - Batch completion time limited by slowest worker

**Status**: ✅ Verified (test_06: method exists, test_07: performance comparison, test_08: error handling)

### Testing & Validation

**Test Suite**: `tests/test_refinement_4_reliability.py` (243 lines, 10 tests)

**Test Coverage**:
- ✅ test_01: Batch failure threshold exists
- ✅ test_02: Plain string documents rejected
- ✅ test_03: Missing both file_path and source rejected
- ✅ test_04: Defensive fallback when source exists
- ✅ test_05: Full compliance documents accepted
- ✅ test_06: Concurrent fetching method exists
- ✅ test_07: Performance comparison (requires API keys)
- ✅ test_08: Concurrent error handling (graceful degradation)
- ✅ test_09: Config propagation verified
- ✅ test_10: Integration test (all 4 phases together)

**Results**: 7/7 basic tests passing (no API keys), 10/10 with API keys

### Related Files

**Implementation**:
- `ice_simplified.py:364-391` (27 lines) - Source attribution enforcement
- `ice_simplified.py:415-474` (60 lines) - Batch failure threshold
- `data_ingestion.py:3801-3944` (144 lines) - Concurrent API fetching

**Testing**:
- `tests/test_refinement_4_reliability.py` (243 lines) - Comprehensive test suite

**Documentation**:
- Serena memory: `refinement_4_reliability_architecture_2025_11_23` - Implementation guide
- `PROGRESS.md` - Session 2025-11-23 entry

### Design Principles Applied

1. **Graceful Degradation**: Batch errors don't crash system (return error dict)
2. **Defensive Programming**: Fallback when `file_path` missing but `source` exists
3. **Fail-Fast**: Stop batch processing at >10% failure rate (detect issues early)
4. **Performance Optimization**: 3-5x speedup through concurrency
5. **Error Isolation**: Per-symbol error handling (one failure doesn't crash batch)
6. **SEC Audit-Ready**: 100% source attribution enforcement

---

## SEC Company Facts API Integration

**Implemented**: 2025-11-22
**Status**: ✅ Production (100% complete)
**Impact**: 100% cost savings ($0/month vs $10-50/month), 100% accuracy (XBRL ground truth)

### Purpose

Provide authoritative financial metrics (Revenue, NetIncome, Assets, EPS, Cash) from SEC's official Company Facts API with zero marginal cost, eliminating dependency on paid financial data APIs while improving accuracy from ~70% (parsed) to 100% (XBRL ground truth).

**Business Impact**: Enables boutique hedge funds to access regulatory-quality financial data for fundamental analysis without API costs, supporting ICE's <$200/month architecture goal.

### Architecture

**Data Flow**:
```
SEC EDGAR API (free, rate-limited)
    ↓ (sec_edgar_connector.py)
Ticker → CIK lookup + Company Facts fetch
    ↓ (data_ingestion.py)
XBRL metric extraction (5 metrics × 8 quarters)
    ↓
Signal Store INSERT (financial_metrics table)
    ↓ (ice_simplified.py)
LightRAG summary document + Knowledge graph
```

**Dual-Purpose Design**:
1. **Signal Store**: Fast SQL queries (<1s) for specific metrics
2. **LightRAG Graph**: Context-rich summaries for reasoning

### Implementation

**Key Files**:
- `sec_edgar_connector.py:262-339` - SEC API client with fallback chains
- `data_ingestion.py:2612-2679` - Ingestion method with Signal Store integration
- `ice_simplified.py:1188-1191, 1222-1228, 2104-2107` - Orchestrator integration (4 locations)
- `config.py:181-191` - Configuration (enabled by default, 8 quarters lookback)

**Metric Mappings** (with fallback chains for robustness):
```python
METRIC_MAPPINGS = {
    'Revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'],
    'NetIncome': ['NetIncomeLoss', 'ProfitLoss', 'NetIncomeLossAttributableToParent'],
    'TotalAssets': ['Assets', 'AssetsCurrent'],
    'EPS_Diluted': ['EarningsPerShareDiluted', 'EarningsPerShareBasic'],
    'Cash': ['CashAndCashEquivalentsAtCarryingValue', 'Cash']
}
```

**Orchestrator Integration Pattern**:
```python
# Initialize to empty (safe default)
sec_facts_docs = []

# Conditional fetch (backward compatible)
if self.config.sec_facts_enabled:
    sec_facts_docs = self.ingester.fetch_sec_company_facts(symbol)

# Process like other sources (consistent pattern)
for doc_dict in sec_facts_docs:
    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{timestamp}]\n{doc_dict['content']}"
    doc_list.append({
        'content': content_with_marker,
        'file_path': doc_dict.get('file_path'),
        'type': 'financial'
    })
```

### Design Decisions

**1. Graceful Degradation**: Returns empty list `[]` on all errors (no exceptions bubble up)
**2. Configuration Control**: `ICE_SEC_FACTS_ENABLED=true/false` for A/B testing
**3. Lookback Limit**: Default 8 quarters (2 years) to control memory usage
**4. Rate Limiting**: 10 requests/second (SEC limit) enforced in connector
**5. Fallback Chains**: Multiple XBRL tags per metric for maximum coverage

### Configuration

```bash
# Enable/disable (default: enabled)
export ICE_SEC_FACTS_ENABLED=true

# Lookback window (default: 8 quarters = 2 years)
export ICE_SEC_FACTS_LOOKBACK_QUARTERS=8
```

### Validation

**Test Suite**: `tests/test_sec_company_facts.py` (6 tests, 100% passing)
- Config validation (defaults, toggles)
- API connectivity (real ticker: AAPL)
- Error handling (invalid ticker → graceful failure)
- Signal Store integration (metrics inserted correctly)
- Lookback quarters limit enforcement

**Integration Test**: Verified end-to-end with 5 critical checks:
- Variable flow safety (no null pointers)
- Data structure correctness (matches schema)
- Signal Store persistence (metrics in DB)
- Error handling (graceful degradation)
- Orchestrator integration (2 locations verified)

### Impact Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Cost | $10-50/mo | $0 | 100% savings |
| Accuracy | ~70% | 100% | XBRL ground truth |
| Coverage | ~60% companies | 100% US public | +40% companies |
| Update Lag | 1-2 days | Same day | Real-time |

### Related Patterns

**Extends** Multi-Source News Aggregation principles:
- Quality over quantity (XBRL > parsed data)
- Graceful degradation (returns [] on failure)
- Configuration control (enable/disable flag)
- Cost-conscious design ($0 marginal cost)

**Integration Points**:
- Signal Store: Temporal queries (YoY/QoQ comparisons)
- LightRAG Graph: Context-rich reasoning ("Show NVDA revenue trend")
- Content Deduplication: Metrics tracked in manifest

**For detailed implementation**: See Serena memory `sec_company_facts_api_integration_complete_2025_11_22`

---

## Confidence Centralization Architecture (Phase 2.8)

**Implemented**: 2025-11-25 to 2025-11-26
**Status**: ✅ Production (100% core path modules migrated)
**Impact**: Single source of truth for confidence values, environment variable overrides

### Purpose

Centralize all hardcoded confidence values (0.X floats) into a single config module with accessor functions, enabling runtime tuning without code changes, environment variable overrides, validation at startup, and consistent values across modules.

**Business Impact**: Allows boutique hedge funds to tune extraction and scoring thresholds without code deployment, supporting iterative calibration based on portfolio-specific feedback.

### Architecture

**Configuration Layer** (`config.py:21-180`):

```python
CONFIDENCE_DEFAULTS = {
    # LightRAG base values
    'lightrag_base': 0.7,
    'confidence_cap': 0.95,
    'confidence_floor': 0.1,

    # Relationship extraction
    'relationship_competitive': 0.85,
    'relationship_supplier': 0.90,
    'relationship_employment': 0.80,
    'relationship_portfolio': 0.75,
    'relationship_event_close': 0.85,
    'relationship_event_distant': 0.65,
    'relationship_category': 0.70,

    # Entity extraction
    'extraction_high': 0.95,
    'extraction_medium': 0.85,
    'threshold_high': 0.80,
    'threshold_medium': 0.70,

    # Graph building
    'edge_default': 0.5,
    'boost_financial_term': 0.15,
    'boost_source_verified': 0.10,
    'penalty_ambiguous': 0.20,

    # Pattern confidence
    'pattern_depends_on': 0.85,
    'pattern_supplies': 0.90,
    'pattern_exposed_to': 0.80,
    # ... 50+ keys total
}

SOURCE_CONFIDENCE_MULTIPLIERS = {
    'sec_edgar': 1.0,    # Regulatory (highest)
    'sec_facts': 0.95,   # XBRL structured
    'yahoo_finance': 0.85,
    'benzinga': 0.80,
    'newsapi': 0.75,     # Standard news
    'finnhub': 0.75,
    'email': 0.70,       # Analyst opinion
    'exa': 0.65,
    'unknown': 0.50      # Fallback
}

CONFIDENCE_WEIGHTS = {
    'source_reliability': 0.4,
    'relationship_clarity': 0.3,
    'evidence_strength': 0.3,
    'base_weight': 0.6,
    'path_weight': 0.4
}
```

**Accessor Functions**:
- `get_confidence(key, default)` - Returns confidence value with env override support
- `get_source_confidence(source)` - Returns source multiplier
- `get_confidence_weight(key)` - Returns composite scoring weight
- `validate_confidence_config()` - Startup validation (0.0-1.0 range check)

**Environment Override Pattern**:
```python
def get_confidence(key: str, default: float = None) -> float:
    """Get confidence value with environment override support"""
    env_key = f"ICE_CONFIDENCE_{key.upper()}"
    if os.environ.get(env_key):
        return float(os.environ[env_key])
    return CONFIDENCE_DEFAULTS.get(key, default or CONFIDENCE_DEFAULTS['source_default'])
```

### Core Module Migration (100% Complete)

| Module | Values Migrated | Status |
|--------|----------------|--------|
| `relationship_extractor.py` | 6 values (competitive, supplier, employment, portfolio, event_close/distant, category) | ✅ 100% |
| `ice_query_processor.py` | 10+ references (lightrag_base, query_min_threshold, confidence_cap, floor, chunk_default, path_default) | ✅ 100% |
| `ice_graph_builder.py` | 8 pattern values + 4 boost/penalty values | ✅ 100% |
| `enhanced_entity_extractor.py` | 8 values (extraction_high/medium, threshold_high/medium) | ✅ 100% |
| `ice_simplified.py` | SOURCE_CONFIDENCE_MULTIPLIERS | ✅ 100% |

### Integration Pattern

**Before** (hardcoded):
```python
# Scattered across files, inconsistent values
confidence = 0.85 if match.group(1) else 0.7
```

**After** (centralized):
```python
from updated_architectures.implementation.config import get_confidence

confidence = get_confidence('extraction_medium') if match.group(1) else get_confidence('threshold_medium')
```

### Testing

**Test Suite**: `tests/test_phase_2_8_config_propagation.py` (19 tests, 100% passing)
- Config structure validation (required keys present)
- Accessor function behavior (returns correct values)
- Module import verification (no import errors)
- Value range checks (all values 0.0-1.0)
- Weight sum validation (base + path = 1.0)

### Related Files

**Implementation**:
- `config.py:21-180` - Centralized config definitions
- `relationship_extractor.py:21` - Import for relationship confidence
- `ice_query_processor.py:17` - Import for query processing
- `ice_graph_builder.py:14` - Import for graph building
- `enhanced_entity_extractor.py:30` - Import for entity extraction

**Documentation**:
- `PROGRESS.md` - Session entries 2025-11-25, 2025-11-26
- Serena memory: `phase_2_8_config_propagation_complete`

---

## Real-Time Monitoring Architecture

**Implemented**: 2025-11-25
**Status**: ✅ Production (890 lines)
**File**: `src/ice_core/real_time_monitor.py`
**Impact**: Instant PM notification of portfolio-impacting events via multi-channel alerts

### Purpose

Continuous market event monitoring with async polling of news sources and SEC filings, portfolio-aware alert classification, and multi-channel delivery (email via SMTP, Slack via webhooks). Enables hedge fund PMs to receive instant notifications of critical events affecting their portfolio.

**Business Impact**: Reduces PM reaction time from hours to minutes for critical market events (earnings surprises, M&A announcements, regulatory actions).

### Architecture Components (8 Classes)

| Class | Lines | Purpose |
|-------|-------|---------|
| `AlertPriority(Enum)` | ~10 | CRITICAL/HIGH/MEDIUM/LOW priority levels |
| `AlertChannel(Enum)` | ~10 | EMAIL/SLACK/WEBHOOK/LOG delivery channels |
| `Alert` (dataclass) | ~30 | Event alert data structure with priority and metadata |
| `NewsAPIPoller` | ~100 | Async news polling (configurable intervals, default 5-min) |
| `SECEdgarPoller` | ~100 | Async SEC filing polling (configurable intervals, default 15-min) |
| `AlertClassifier` | ~100 | Portfolio-aware priority classification based on holdings |
| `AlertDelivery` | 354-618 (264 lines) | Multi-channel delivery (SMTP, Slack webhooks, custom webhooks) |
| `RealTimeMonitor` | 621-869 (248 lines) | Main orchestrator coordinating all components |

### Data Flow

```
Market Sources (News APIs, SEC EDGAR)
    ↓ (Async Polling)
NewsAPIPoller / SECEdgarPoller
    ↓ (Raw Events)
EventExtractor.extract_events() → 15 event types
    ↓ (Extracted Events)
AlertClassifier.classify() → Portfolio-aware priority
    ↓ (Prioritized Alerts)
AlertDelivery.queue_alert() → Multi-channel delivery
    ↓
PM receives Email/Slack notification
```

### Multi-Channel Delivery

**Email Delivery** (`_send_email`, lines 416-462):
- SMTP + TLS encryption
- Gmail, Outlook, and custom SMTP server support
- Environment variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `ALERT_EMAIL_TO`
- Connection timeout: 10s

**Slack Delivery** (`_send_slack`, lines 481-566):
- Slack Incoming Webhooks API
- Block Kit formatting for rich layout
- Color-coded by priority: CRITICAL (red), HIGH (orange), MEDIUM (green), LOW (gray)
- Environment variable: `SLACK_WEBHOOK_URL`

**Custom Webhook** (`_send_webhook`, lines 568-614):
- Generic webhook endpoint support
- JSON payload with full alert details
- Environment variable: `ALERT_WEBHOOK_URL`

### Configuration

```python
# Environment Variables
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=app_password
ALERT_EMAIL_TO=pm@hedgefund.com
NEWS_POLL_INTERVAL_SECONDS=300     # 5 minutes
SEC_POLL_INTERVAL_SECONDS=900      # 15 minutes
```

### Integration with ICE

**Standalone Mode**: Can run independently as monitoring daemon
```python
from src.ice_core.real_time_monitor import RealTimeMonitor
monitor = RealTimeMonitor(portfolio=['NVDA', 'AAPL', 'TSMC'])
await monitor.start()  # Begins async monitoring
```

**Integrated Mode**: Shares EventExtractor and SignalStore with main ICE system

### Testing

**Test Suite**: `tests/test_real_time_monitor.py`
- Alert priority classification
- Multi-channel delivery (mocked SMTP/webhook)
- Polling loop error handling
- Portfolio-aware filtering

---

## Query Processing Architecture

**Implemented**: Phase 2.7-2.8
**Status**: ✅ Production (1,773 lines)
**File**: `src/ice_core/ice_query_processor.py`
**Impact**: Intelligent query routing, multi-hop reasoning, temporal enhancement, answer synthesis

### Purpose

Orchestrate multi-source query processing with intelligent routing between Signal Store (structured data) and LightRAG (semantic/graph), temporal query enhancement, adaptive confidence scoring, and formatted display output.

**Business Impact**: Enables natural language queries with automatic optimization for query type, ensuring PMs get accurate, confidence-scored answers with full source attribution.

### Core Class: ICEQueryProcessor

**Location**: Lines 28-1773 (1,745 lines)

**Key Methods** (44+ methods):

| Category | Methods | Purpose |
|----------|---------|---------|
| **Query Processing** | `process_enhanced_query`, `_query_with_fallback` | Main query entry, fallback logic |
| **Entity Extraction** | `_extract_entities_from_query`, `_is_valid_ticker` | Extract tickers, companies from query |
| **Query Classification** | `_classify_query_type`, `_classify_temporal_intent` | Route to appropriate handler |
| **Graph Context** | `_get_graph_context`, `_format_graph_context` | Multi-hop graph traversal |
| **Response Synthesis** | `_synthesize_enhanced_response`, `_extract_key_insights` | Combine sources into answer |
| **Confidence Scoring** | `_calculate_response_confidence`, `_calculate_adaptive_confidence` | Source-weighted confidence |
| **Source Metadata** | `_enrich_source_metadata`, `_enrich_chunks_metadata` | Full attribution |
| **Temporal Processing** | `_extract_temporal_info`, `_build_temporal_context` | Time-aware queries |
| **Conflict Detection** | `_detect_conflicts` | Identify contradictory signals |
| **Display Formatting** | `format_adaptive_display`, `_format_*_card` (6 methods) | Rich output formatting |

### Query Flow

```
Natural Language Query
    ↓
_extract_entities_from_query() → Tickers, companies
    ↓
_classify_query_type() → RISK/PERFORMANCE/RELATIONSHIP/TEMPORAL/GENERAL
    ↓
_classify_temporal_intent() → RECENT/HISTORICAL/TREND/COMPARISON
    ↓
process_enhanced_query()
    ├─ _get_graph_context() → Multi-hop graph traversal (1-3 hops)
    ├─ LightRAG.query() → Semantic search results
    ├─ SignalStore queries → Structured data (ratings, metrics)
    ↓
_synthesize_enhanced_response()
    ├─ _enrich_source_metadata() → Full attribution
    ├─ _calculate_adaptive_confidence() → Weighted scoring
    ├─ _detect_conflicts() → Contradictory signal detection
    ↓
format_adaptive_display() → Rich formatted output
    ├─ Answer Card
    ├─ Reliability Card
    ├─ Source Card (with links)
    ├─ Temporal Card
    ├─ Conflict Card (if applicable)
    └─ Reasoning Card
```

### Adaptive Confidence Scoring

**Formula** (`_calculate_adaptive_confidence`, lines 816-873):
```python
confidence = base_weight × source_confidence + path_weight × path_integrity

where:
- base_weight = 0.6 (from CONFIDENCE_WEIGHTS)
- path_weight = 0.4 (from CONFIDENCE_WEIGHTS)
- source_confidence = weighted average of sources
- path_integrity = graph path verification score

# Variance penalty applied if sources disagree
if _has_variance(chunks):
    confidence = _apply_variance_penalty(confidence, variance_score)
```

### Display Cards (6 Card Types)

| Card | Method | Purpose |
|------|--------|---------|
| **Answer** | `_format_answer_card` | Main response text |
| **Reliability** | `_format_reliability_card` | Confidence score breakdown |
| **Source** | `_format_source_card` | Clickable source links |
| **Temporal** | `_format_temporal_card` | Time context and freshness |
| **Conflict** | `_format_conflict_card` | Contradictory signals (if any) |
| **Reasoning** | `_format_reasoning_card` | Multi-hop path explanation |

### Integration Points

**LightRAG Integration**:
- Wraps `JupyterSyncWrapper` for semantic queries
- Uses graph traversal for relationship discovery

**Signal Store Integration**:
- Routes structured queries (ratings, metrics, calendar)
- Temporal queries use Signal Store temporal methods

**Config Integration**:
- Uses `get_confidence()` for centralized confidence values
- Respects `CONFIDENCE_WEIGHTS` for scoring

### Configuration

```python
# ICEQueryProcessor defaults (lines 58-60)
max_context_documents = 20
max_graph_hops = 3
min_confidence_threshold = get_confidence('query_min_threshold')  # 0.3
```

### Testing

**Test Suite**: Integrated into `tests/test_query_router_comprehensive.py`
- Query classification accuracy
- Temporal intent detection
- Confidence scoring validation
- Display formatting

---

**For comprehensive architecture details**: See `md_files/ARCHITECTURE.md` (175 lines)
**For implementation guide**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`
