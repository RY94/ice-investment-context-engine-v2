# ICE System Architecture

> **🔗 LINKED DOCUMENTATION**: This is one of 8 essential core files that must stay synchronized. When updating this file, always cross-check and update the related files: `CLAUDE.md`, `README.md`, `PROJECT_STRUCTURE.md`, `PROJECT_CHANGELOG.md`, `ICE_PRD.md`, `ICE_DEVELOPMENT_TODO.md`, and `PROGRESS.md`.

**Purpose**: North star architectural blueprint - prevents drift across sessions
**Update**: Only on architecture changes (stable reference)
**Last Updated**: 2025-11-05

---

## System Overview

ICE (Investment Context Engine) is a modular Graph-RAG system serving as cognitive backbone for boutique hedge funds (<$100M AUM). It solves delayed signal capture, low insight reusability, inconsistent decision context, and manual triage bottlenecks through graph-first reasoning with 100% source attribution.

**Architecture**: UDMA (User-Directed Modular Architecture) - Simple Orchestration + Production Modules + User Control

---

## Major Components

### 1. Simple Orchestrator
**File**: `updated_architectures/implementation/ice_simplified.py` (1,366 lines)
**Responsibility**: High-level workflow coordination
**Inputs**: User commands (ingest, query, analyze)
**Outputs**: Orchestrated results from production modules

### 2. Production Modules
**Location**: `ice_data_ingestion/` (17K lines), `imap_email_ingestion_pipeline/` (13K lines), `src/ice_core/` (4K lines)
**Responsibility**: Robust data ingestion, email processing, graph building
**Inputs**: API data, email files, SEC filings, URLs
**Outputs**: Validated entities, relationships, documents

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
**Enforcement**: All data structures include `source` field
**Violation**: Any data without source attribution is rejected

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

---

**For comprehensive architecture details**: See `md_files/ARCHITECTURE.md` (175 lines)
**For implementation guide**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`
