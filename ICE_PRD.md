# Investment Context Engine (ICE) - Product Requirements Document

> **🔗 LINKED DOCUMENTATION**: This is one of 6 essential core files that must stay synchronized. When updating this file, always cross-check and update the related files: `CLAUDE.md`, `README.md`, `PROJECT_STRUCTURE.md`, `ICE_DEVELOPMENT_TODO.md`, and `PROJECT_CHANGELOG.md` to maintain consistency across project documentation.

> **Location**: `/ICE_PRD.md`
> **Purpose**: Unified requirements specification for Claude Code development instances
> **Last Updated**: 2025-01-22
> **Status**: Living document - updated with each major milestone

---

## Document Purpose & Usage

**For**: Claude Code AI instances and development team
**When to Read**: At the start of every development session
**How to Use**:
- Quick scan Executive Summary for current priorities
- Reference specific sections as needed during development
- Use Decision Framework for architectural choices
- Cross-reference detailed documentation for deep dives

**Cross-References**:
- **Detailed Roadmap**: `ICE_DEVELOPMENT_TODO.md` (115 tasks, 39% complete)
- **Validation Framework**: `ICE_VALIDATION_FRAMEWORK.md` (PIVF with 20 golden queries)
- **Architecture Plan**: `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` (UDMA implementation guide)
- **Architecture History**: `archive/strategic_analysis/README.md` (all 5 options analyzed)
- **Developer Guide**: `CLAUDE.md` (commands, workflows, standards)
- **User Documentation**: `README.md` (product overview, quick start)

---

## 1. Executive Summary

### TL;DR (Quick Scan)
- **Current Phase**: Week 2/6 integration - ICESystemManager orchestration with health monitoring
- **Completion**: 39% (45/115 tasks) - Email Phase 1 validated ✅, Week 1 integration complete ✅
- **Architecture**: Simple orchestrator (879 lines) + production modules (34K+ lines)
- **Validation**: PIVF framework with 20 golden queries, target >7.5/10 overall score
- **Next Milestone**: Orchestration integration → Query enhancement → End-to-end validation

### Current Status (2025-01-22)

**Project Phase**: Phase 2 - Architecture Integration (Week 1 Complete ✅, Week 2 Starting)
**Completion**: 39% (45/115 tasks)
**Primary Interfaces**: Dual workflow notebooks (building + query)
**Architecture Strategy**: Simple Orchestration + Production Modules (34K+ lines)

### Recent Milestones ✅

1. **Email Pipeline Phase 1 Complete** (2025-01-22)
   - Enhanced document generation with inline metadata
   - 27/27 unit tests passing
   - Ticker extraction >95% accuracy
   - Single LightRAG graph approach validated

2. **Week 1 Integration Complete** (2025-01-22)
   - 3 data sources → LightRAG (API/MCP + Email + SEC)
   - 26 documents successfully ingested
   - Robust HTTP client integrated (circuit breaker + retry)

3. **Dual Workflow Notebooks Complete** (2025-01)
   - `ice_building_workflow.ipynb` - Knowledge graph construction
   - `ice_query_workflow.ipynb` - Investment intelligence analysis
   - 10 integration tests, 100% pass rate

### Immediate Priorities 🔴

**Next 2 Weeks (Week 2-3):**
1. Integrate `ICESystemManager` for orchestration with health monitoring
2. Upgrade to `SecureConfig` for encrypted API key management
3. Begin query enhancement with `ICEQueryProcessor` fallback logic
4. Continue validation against PIVF golden queries

**Week 2 Integration Checklist (Current Focus):**
- [ ] **File**: `updated_architectures/implementation/ice_simplified.py` - Import `ICESystemManager` from `src/ice_core/`
- [ ] **File**: `updated_architectures/implementation/ice_simplified.py` - Replace manual orchestration with `ICESystemManager.coordinate()`
- [ ] **File**: `updated_architectures/implementation/ice_simplified.py` - Add health monitoring method calls (check component status)
- [ ] **File**: `src/ice_core/ice_system_manager.py` - Verify integration points and method interfaces
- [ ] **File**: `check/health_checks.py` - Test graceful degradation scenarios (email source fails, API rate limit, etc.)
- [ ] **Testing**: Run integration tests to verify orchestration working with all 3 data sources

**Critical Path**: Complete 6-week integration roadmap → End-to-end validation → Local LLM deployment

---

## 2. Product Vision

### What is ICE?

**ICE (Investment Context Engine)** is a modular, lightweight AI system designed as the **cognitive backbone for boutique hedge fund workflows**—spanning idea generation, equity research, portfolio monitoring, risk management, and investor communications.

**DBA5102 Business Analytics Capstone Project**
**Author**: Roy Yeo Fu Qiang (A0280541L)
**Institution**: National University of Singapore

### Core Problems Solved

Boutique hedge funds face critical pain points that ICE addresses:

1. **📊 Delayed Signal Capture**
   - Problem: Soft signals buried in earnings transcripts, SEC filings, or news flows
   - ICE Solution: AI-powered entity extraction and relationship discovery across all sources

2. **🔄 Low Insight Reusability**
   - Problem: Investment theses siloed in decks, chats, or emails
   - ICE Solution: Persistent knowledge graph that continuously learns and evolves

3. **🧩 Inconsistent Decision Context**
   - Problem: Fragmented understanding leading to uncoordinated decisions
   - ICE Solution: Unified context assembly combining short-term + long-term memory

4. **⏱️ Manual Triage Bottlenecks**
   - Problem: Fully manual context stitching limiting speed and scale
   - ICE Solution: Automated multi-hop reasoning with source attribution

### Key Value Propositions

- **Multi-hop Reasoning**: Connect dots across 1-3 relationship hops (e.g., "How does China risk impact NVDA through TSMC?")
- **Graph-RAG Intelligence**: Hybrid retrieval combining semantic search + keyword search + graph traversal
- **End-to-end Traceability**: Every fact and inference traces back to verifiable source documents
- **Real-time Context**: Continuously updated investment knowledge graph with temporal awareness
- **Cost Optimization**: Local LLM support reducing operational costs from $500+/month to <$50/month

### Target Users

**Primary**: Lean boutique hedge funds (1-10 person teams)
**Secondary**: Independent investment professionals and research analysts

---

## 3. User Personas & Use Cases

> **For detailed persona profiles**: See `project_information/user_research/ICE_USER_PERSONAS_DETAILED.md` for complete backgrounds, goals, pain points, and workflows. This section provides concise summaries focused on AI development requirements.

### Persona 1: Portfolio Manager (Primary Decision Maker)

**Portfolio Manager Sarah** leads a boutique long/short equity fund ($100M AUM, 25-40 positions, 2-analyst team). **Primary ICE use cases**: Portfolio risk analysis ("What are the top 3 risks across my current portfolio?"), opportunity identification ("Find companies with improving margins in my coverage universe"), thesis validation ("What signals support or contradict my NVDA bull thesis?"), correlation discovery ("How does China regulatory risk impact my tech holdings?"). **Key pain points**: Information overload from fragmented sources, missed signals, time-consuming manual research synthesis. **Success metrics**: 60% reduction in research synthesis time, <30min portfolio review (vs 2+ hours), identify 2-3 non-obvious insights weekly. **Scale**: Manages 25-40 positions, needs multi-hop reasoning across portfolio holdings.

### Persona 2: Research Analyst (Research & Deep Analysis)

**Senior Research Analyst David** conducts deep research on technology/industrial sectors, covering 15-20 companies. **Primary ICE use cases**: Company deep-dive ("Summarize TSMC's customer concentration risk over last 2 years"), sector analysis ("How are semiconductor supply chain dynamics evolving?"), relationship mapping ("What companies are exposed to NVDA's success?"), thesis building ("Build investment thesis for company X based on all available data"). **Key pain points**: Time-consuming transcript/filing analysis, difficulty connecting dots across company relationships, repetitive data extraction. **Success metrics**: Complete company deep-dive in 2 hours (vs 8 hours), identify 3-5 relationship insights not obvious from single sources, track 20+ companies without missing critical developments. **Scale**: 15-20 company coverage universe, needs 2-3 hop relationship traversal.

### Persona 3: Junior Analyst (Data Triage & Monitoring)

**Junior Analyst Alex** handles initial research, data gathering, and news monitoring for the team (2 years experience). **Primary ICE use cases**: News monitoring ("What are the top 5 most important developments today?"), signal extraction ("Are there any BUY/SELL recommendations for our portfolio?"), preliminary research ("Quick summary of company X's latest earnings call"), learning/understanding ("Show me how this news about China impacts our holdings"). **Key pain points**: Overwhelming news volume (100+ daily articles), unclear signal vs noise, difficulty understanding second-order implications, time pressure. **Success metrics**: Triage 100+ daily items in <30 minutes, 90%+ accuracy flagging important signals for senior review, deliver preliminary research 3x faster than manual. **Scale**: 100+ daily news articles, needs efficient entity extraction and confidence scoring.

---

## 4. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           ICE SYSTEM ARCHITECTURE (Integrated)                  │
│         Simple Orchestration + Production Modules               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 PRIMARY INTERFACES                              │
├─────────────────────────────────────────────────────────────────┤
│  ice_building_workflow.ipynb  │  ice_query_workflow.ipynb      │
│  Knowledge graph construction │  Investment intelligence       │
│  Document ingestion pipeline  │  Portfolio analysis           │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              SIMPLE ORCHESTRATOR (ice_simplified.py)            │
│  Coordinates: Config → Data Ingestion → Core Engine → Query    │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              PRODUCTION DATA SOURCES (ALL → LightRAG)           │
│                                                                 │
│  1. API/MCP (ice_data_ingestion/ - 17,256 lines)               │
│     ├── NewsAPI, Finnhub, Alpha Vantage, FMP                   │
│     ├── SEC EDGAR connector (async)                            │
│     ├── Robust HTTP client (circuit breaker + retry)           │
│     └── Multi-level data validation                            │
│                                                                 │
│  2. Email (imap_email_ingestion_pipeline/ - 12,810 lines)      │
│     ├── Broker research emails (74 samples)                    │
│     ├── Enhanced documents (inline metadata)                   │
│     ├── EntityExtractor (>95% precision)                       │
│     └── BUY/SELL/HOLD signal extraction                        │
│                                                                 │
│  3. Robust Framework                                            │
│     ├── Connection pooling                                     │
│     ├── Encrypted config (SecureConfig)                        │
│     └── Health monitoring                                      │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              LIGHTRAG KNOWLEDGE GRAPH (Single Unified)          │
│  ├── Vector Storage (semantic search)                          │
│  ├── Graph Storage (entity relationships)                      │
│  ├── Full-text Storage (keyword search)                        │
│  └── Enhanced metadata (confidence scores, sources)            │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              QUERY PROCESSING (6 LightRAG Modes)                │
│  ├── Hybrid: Semantic + Graph (default for portfolio analysis) │
│  ├── Local: Document-focused retrieval                         │
│  ├── Global: Entity-level graph traversal                      │
│  ├── Mix: Adaptive mode selection                              │
│  ├── Naive: Simple vector search                               │
│  └── KG: Pure knowledge graph                                  │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUT (MCP-Compatible JSON)                       │
│  ├── Investment insights with confidence scores                │
│  ├── Source attribution (every fact traceable)                 │
│  ├── Relationship visualizations                               │
│  └── Portfolio risk analysis                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

**1. Data Ingestion Layer**
- Production module: `ice_data_ingestion/` (17,256 lines)
- Email pipeline: `imap_email_ingestion_pipeline/` (12,810 lines)
- Integration: Week 1 complete ✅ (3 sources → LightRAG)

**2. AI Engine**
- LightRAG wrapper: `src/ice_lightrag/ice_rag.py`
- Jupyter sync: `src/ice_lightrag/ice_rag_fixed.py`
- Storage: `src/ice_lightrag/storage/` (persistent knowledge graph)

**3. Orchestration**
- Simple: `ice_simplified.py` (self-contained orchestrator)
- Production: `src/ice_core/` (3,955 lines) - Week 2 integration
- System manager, query processor, graph builder

**4. Configuration**
- Current: `config.py` (environment variables)
- Target: `SecureConfig` with encrypted API keys (Week 3)

### Data Flow

1. **Ingestion**: External sources → Enhanced documents → LightRAG
2. **Processing**: LightRAG entity extraction + relationship building
3. **Storage**: Vector DB + Graph DB + Full-text index (single unified graph)
4. **Querying**: User query → Mode selection → Retrieval → LLM synthesis
5. **Output**: Source-attributed insights with confidence scores

---

## 5. Functional Requirements

### Phase 1: MVP Foundation ✅ COMPLETE (35/35 tasks)

#### 1.1 LightRAG Integration
- ✅ Core LightRAG wrapper implementation
- ✅ Document processing with entity extraction
- ✅ Natural language query interface
- ✅ Storage management and persistence
- ✅ 6 query modes (local, global, hybrid, mix, naive, kg)

**Acceptance Criteria**:
- All 6 query modes return coherent results
- Documents persist across sessions
- Entity extraction precision >90%

#### 1.2 Dual Workflow Notebooks
- ✅ Building workflow (`ice_building_workflow.ipynb`)
- ✅ Query workflow (`ice_query_workflow.ipynb`)
- ✅ 10 integration tests, 100% pass rate
- ✅ Complete LightRAG lifecycle (setup, ingest, query, export)

**Acceptance Criteria**:
- All notebook sections execute without errors
- Knowledge graph builds successfully from sample data
- All 6 query modes functional in notebooks

#### 1.3 Graph Data Structure
- ✅ NetworkX integration for lightweight operations
- ✅ Typed edge definitions (depends_on, exposed_to, drives, etc.)
- ✅ Temporal relationships with timestamps
- ✅ Source attribution for all edges
- ✅ Bidirectional graph traversal

**Acceptance Criteria**:
- Graph supports 1-3 hop traversal
- Every edge traceable to source document
- Temporal queries work correctly

---

### Phase 2: Architecture Integration 🔄 IN PROGRESS (10/80 tasks)

#### 2.1 Data Ingestion Integration ✅ COMPLETE (Week 1)
- ✅ Refactor `data_ingestion.py` to import from production modules
- ✅ Integrate email pipeline (74 sample emails with enhanced documents)
- ✅ Add SEC EDGAR connector (async filing retrieval)
- ✅ Test 3 data sources → LightRAG (26 documents ingested)

**Acceptance Criteria**:
- All 3 data sources feeding LightRAG successfully
- Circuit breaker + retry logic working
- Enhanced documents preserve confidence scores
- No duplicate LLM calls from email processing

#### 2.2 Email Graph Integration ✅ PHASE 1 COMPLETE
- ✅ Enhanced document creator (`enhanced_doc_creator.py`)
- ✅ Inline metadata markup: `[TICKER:NVDA|confidence:0.95]`
- ✅ Source attribution: `[SOURCE_EMAIL:uid|sender|date]`
- ✅ 27/27 unit tests passing
- ✅ Validation tests: Ticker extraction >95%, query <2s, traceable

**Decision Gate**: Phase 1 metrics PASSED ✅ → Continue single LightRAG graph, Phase 2 NOT needed

**Acceptance Criteria**:
- Ticker extraction accuracy >95% ✅
- Confidence preservation in queries ✅
- Structured query performance <2s ✅
- Source attribution reliability 100% ✅

#### 2.3 Core Orchestration Integration ⏳ WEEK 2 (Starting)
- [ ] Integrate `ICESystemManager` from `src/ice_core/`
- [ ] Add health monitoring and graceful degradation
- [ ] Implement session management
- [ ] Component coordination with fallbacks

**Acceptance Criteria**:
- Health checks report component status
- System degrades gracefully if email source fails
- Session state persists across notebook runs

#### 2.4 Configuration Integration ⏳ WEEK 3
- [ ] Upgrade to `SecureConfig` from `ice_data_ingestion/`
- [ ] Implement encrypted API key storage
- [ ] Add credential rotation support
- [ ] Environment variable fallback

**Acceptance Criteria**:
- API keys encrypted at rest
- No secrets in git repository
- Credential rotation works without code changes

#### 2.5 Query Enhancement ⏳ WEEK 4
- [ ] Integrate `ICEQueryProcessor` with fallback logic
- [ ] Implement query mode auto-selection
- [ ] Add confidence-based filtering
- [ ] Enhanced result formatting

**Acceptance Criteria**:
- Query mode auto-selection accuracy >80%
- Fallback to simpler modes if complex fails
- Confidence scores in all results

---

### Phase 3: Production Optimization (0/20 tasks planned)

**Focus**: Local LLM deployment, cost optimization, performance tuning

#### 3.1 Local LLM Integration
- [ ] Complete Ollama setup with llama3.1:8b
- [ ] Hybrid cloud/local routing logic
- [ ] Cost tracking per query
- [ ] Quality comparison (local vs GPT-4)

#### 3.2 Performance Optimization
- [ ] Query latency optimization (<2s target)
- [ ] Batch ingestion improvements
- [ ] Graph traversal optimization
- [ ] Memory usage reduction

---

### Phase 4: Validation & Testing (0/20 tasks planned)

**Focus**: PIVF validation, regression testing, quality assurance

#### 4.1 PIVF Validation
- [ ] Implement 20 golden queries
- [ ] 9-dimensional scoring automation
- [ ] Snapshot-based regression testing
- [ ] Modified Option 4 decision gates

#### 4.2 Integration Testing
- [ ] End-to-end workflow tests
- [ ] Data source failure scenarios
- [ ] Query mode performance benchmarks
- [ ] Cost-to-quality ratio measurement

---

### Phase 5: Production Deployment (0/20 tasks planned)

**Focus**: Streamlit UI (SHELVED until 90% AI completion), documentation, final polish

---

## 6. Non-Functional Requirements

### Performance Requirements

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Query Latency (Structured) | <2 seconds | PIVF test suite |
| Query Latency (Complex Multi-hop) | <5 seconds | PIVF test suite |
| Document Ingestion Rate | 100+ docs/hour | Batch processing tests |
| Knowledge Graph Size Support | 1,000-10,000 entities | Boutique fund scale |
| Concurrent Users | 1 (single user focus) | N/A |
| Session Persistence | Indefinite | Storage validation |

### Cost Requirements

| Component | Target Budget | Baseline (Without ICE) |
|-----------|--------------|----------------------|
| LLM Costs (monthly) | <$50 | $50-200 (GPT-4 only) |
| API Costs (monthly) | <$100 | $100-200 (manual subscriptions) |
| Total Operational Cost | <$200/month | $500+/month |
| Cost per Query | <$0.10 | $0.50-1.00 (manual research) |

**Cost Optimization Strategy**:
- Hybrid deployment: Critical queries → GPT-4, routine → local LLM
- Email processing: Deterministic extraction (no duplicate LLM calls)
- Batch API requests: Reduce per-request overhead
- Local LLM: llama3.1:8b for 80% of queries

### Quality Requirements

| Metric | Target | Validation Method |
|--------|--------|------------------|
| Entity Extraction Precision | >95% | PIVF golden queries Q011-Q015 |
| Entity Extraction Recall | >90% | PIVF golden queries Q011-Q015 |
| Structured Query Accuracy | >90% | PIVF golden queries Q001-Q010 |
| Source Attribution | 100% | Every fact must trace to source |
| F1 Score (Key Tasks) | >0.85 | Modified Option 4 decision gate |
| Overall PIVF Score | >7.5/10 | 9-dimensional scoring average |

### Security Requirements

| Requirement | Implementation | Validation |
|-------------|---------------|------------|
| API Key Encryption | SecureConfig (Week 3) | Keys encrypted at rest |
| No Secrets in Git | .gitignore configured | Pre-commit checks |
| Credential Rotation | SecureConfig support | Manual rotation test |
| Local LLM Option | Ollama integration | Sensitive data never sent to cloud |
| Data Privacy | All processing local | No external data sharing |

### Scalability Constraints

**Design Constraints** (Intentional Limitations):
- **Single User**: System designed for 1 boutique fund PM, not multi-tenant
- **Portfolio Size**: 10-50 holdings (not hundreds)
- **Historical Data**: 2-3 years (not decades)
- **Graph Size**: 1K-10K entities (boutique fund scale)
- **Real-time**: Batch ingestion (not streaming)

**Rationale**: Solo developer, capstone timeline, boutique fund focus

---

## 7. Success Metrics & Validation

### PIVF (Portfolio Intelligence Validation Framework)

**Reference**: See `ICE_VALIDATION_FRAMEWORK.md` for complete specification

#### 7.1 Golden Test Set (20 Queries)

**Query Categories**:
1. **Portfolio Risk Analysis** (Q001-Q005): Cross-holdings risk identification
2. **Opportunity Discovery** (Q006-Q010): Non-obvious investment insights
3. **Entity Extraction** (Q011-Q015): Ticker/rating/price target precision
4. **Multi-hop Reasoning** (Q016-Q020): 2-3 hop relationship traversal

**Example Golden Queries**:
- Q001: "What are the top 3 risks across my current portfolio?"
- Q006: "Find companies with improving margins in semiconductor sector"
- Q011: "Extract all BUY ratings from emails in last 7 days"
- Q016: "How does China regulatory risk impact NVDA through TSMC?"

#### 7.2 Nine-Dimensional Scoring

**Technical Quality (5 dimensions)**:
1. **Relevance** (0-10): Answer addresses user query
2. **Completeness** (0-10): All key aspects covered
3. **Accuracy** (0-10): Facts are correct and current
4. **Traceability** (0-10): Sources clearly cited
5. **Coherence** (0-10): Response is well-structured

**Business Quality (4 dimensions)**:
6. **Actionability** (0-10): Insights support decisions
7. **Novelty** (0-10): Non-obvious insights surfaced
8. **Timeliness** (0-10): Information is up-to-date
9. **Cost-Effectiveness** (0-10): Value per query cost

**Overall Score**: Average of 9 dimensions
**Target**: >7.5/10 overall (demo-ready quality)

#### 7.3 Modified Option 4 Decision Framework

**Phase 0: Baseline Validation** (3 days)
```
Run PIVF Core Validation (20 queries)
Calculate Entity Extraction F1 Score (Q011-Q015)

Decision Gate:
├── F1 ≥ 0.85 → Baseline sufficient ✅
├── F1 < 0.85 → Try targeted fix (Phase 2)
└── F1 < 0.70 → Consider enhanced docs (Phase 3)
```

**Current Status**: Email Phase 1 F1 >0.95 ✅ → Baseline sufficient, Phase 2 NOT needed

#### 7.4 Progressive Validation Workflow

1. **Smoke Test** (5 minutes): 5 queries, quick sanity check
2. **Core Validation** (30 minutes): 20 golden queries, full scoring
3. **Deep Validation** (2 hours): 20 queries + edge cases + regression

**Frequency**:
- Smoke: Every major change
- Core: Weekly during active development
- Deep: Before demo, before phase completion

---

## 8. Development Phases & Roadmap

### Phase Overview

| Phase | Status | Tasks | Focus |
|-------|--------|-------|-------|
| Phase 1: MVP Foundation | ✅ COMPLETE | 35/35 | LightRAG, notebooks, graph structure |
| Phase 2: Architecture Integration | 🔄 IN PROGRESS | 10/80 | Production modules, 6-week plan |
| Phase 3: Production Optimization | ⏳ PLANNED | 0/20 | Local LLM, performance, cost |
| Phase 4: Validation & Testing | ⏳ PLANNED | 0/20 | PIVF, regression, quality |
| Phase 5: Production Deployment | ⏳ SHELVED | 0/20 | UI (post-90% AI), final polish |

**Total Progress**: 45/115 tasks (39% complete)

### UDMA Implementation Roadmap (Phase 2 Detail)

**Architecture**: User-Directed Modular Architecture (UDMA) - Option 5 from strategic analysis
**Reference**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` for complete UDMA specification
**Decision History**: See `archive/strategic_analysis/README.md` for all 5 options analyzed

#### Week 1: Data Ingestion Integration ✅ COMPLETE
- ✅ Refactor `data_ingestion.py` → import from `ice_data_ingestion/`
- ✅ Integrate email pipeline (74 sample .eml files)
- ✅ Add SEC EDGAR connector (async)
- ✅ Test 3 sources → LightRAG (26 documents)

**Achievements**:
- Robust HTTP client (circuit breaker + retry)
- Enhanced documents (inline metadata)
- No duplicate LLM calls from email processing
- All validation metrics passed

#### Week 2: Core Orchestration ⏳ CURRENT WEEK
- [ ] Integrate `ICESystemManager` from `src/ice_core/`
- [ ] Add health monitoring + graceful degradation
- [ ] Implement session management
- [ ] Component coordination with fallbacks

**Success Criteria**:
- Health checks operational
- System degrades gracefully if sources fail
- Session state persists

#### Week 3: Configuration
- [ ] Upgrade to `SecureConfig` (encrypted API keys)
- [ ] Implement credential rotation
- [ ] Environment variable fallback
- [ ] Remove hardcoded secrets

**Success Criteria**:
- API keys encrypted at rest
- No secrets in git
- Rotation works seamlessly

#### Week 4: Query Enhancement
- [ ] Integrate `ICEQueryProcessor` with fallbacks
- [ ] Query mode auto-selection
- [ ] Confidence-based filtering
- [ ] Enhanced result formatting

**Success Criteria**:
- Auto-selection accuracy >80%
- Fallback logic works
- Confidence scores in all results

#### Week 5: Workflow Notebooks
- [ ] Update `ice_building_workflow.ipynb` with integrated features
- [ ] Update `ice_query_workflow.ipynb` with enhanced querying
- [ ] Add examples using all 3 data sources
- [ ] Document integration benefits

**Success Criteria**:
- Notebooks demonstrate all integrated features
- All data sources used in examples
- Documentation up-to-date

#### Week 6: Testing & Validation
- [x] End-to-end integration tests
- [x] Data source failure scenarios
- [x] PIVF Core Validation (20 queries)
- [x] Performance benchmarking

**Success Criteria**:
- All integration tests pass
- Graceful handling of source failures
- PIVF score >7.5/10
- Query latency targets met

---

## 9. Scope & Constraints

### In Scope ✅

**Core Features**:
- Investment knowledge graph construction
- Multi-hop reasoning (1-3 hops)
- Data ingestion from APIs, emails, SEC filings
- 6 LightRAG query modes
- Portfolio risk analysis
- Source-attributed insights
- Local LLM support (cost optimization)
- Single-user boutique fund workflows
- Notebook-first development interface
- MCP-compatible JSON outputs

**Data Sources**:
- Financial news APIs (NewsAPI, Finnhub, etc.)
- Market data APIs (Alpha Vantage, FMP)
- Email (broker research, analyst reports)
- SEC EDGAR filings (10-K, 10-Q, 8-K)
- Earnings call transcripts

> **For complete API/MCP inventory**: See `ice_data_ingestion/data_sources_specification.md` for detailed specifications of all 26 data sources (4 MCP servers + 22 direct APIs), including implementation patterns, data models, error handling, and cost management strategies.

**Query Capabilities**:
- Natural language queries
- Portfolio-level risk analysis
- Company-level deep dives
- Relationship discovery
- Signal extraction (BUY/SELL/HOLD)
- Confidence-scored insights

### Out of Scope ❌

**Explicitly NOT Building**:
- Multi-user/multi-tenant support
- Real-time trading execution
- Proprietary trading strategies
- Large institutional fund workflows (100+ holdings)
- Mobile applications
- Advanced NLP model training
- Custom LLM fine-tuning
- Multi-language support (English only)
- Regulatory compliance automation
- Full Streamlit UI (shelved until Phase 5, post-90% AI completion)
- Live market data streaming (batch ingestion only)
- Automated portfolio rebalancing
- Client reporting/communication tools
- Social media sentiment analysis
- Alternative data sources (satellite imagery, credit card data, etc.)

### Constraints & Limitations

**Development Constraints**:
- **Solo developer**: Not designed for team collaboration
- **Capstone timeline**: 6-month MVP (January-June 2025)
- **Platform**: macOS development environment only
- **Language**: Python 3.8+ (no multi-language support)

**Scale Constraints**:
- **Portfolio size**: 10-50 holdings (boutique fund scale)
- **Graph size**: 1K-10K entities (not enterprise scale)
- **Concurrent users**: 1 (single user system)
- **Historical data**: 2-3 years (not decades)

**Cost Constraints**:
- **Total operational cost**: <$200/month target
- **LLM costs**: Prioritize local LLM over cloud
- **API costs**: Free/low-cost tiers preferred

**Technical Constraints**:
- **Real-time**: Batch ingestion only (not streaming)
- **Latency**: Best-effort (not guaranteed <1s)
- **Availability**: Single machine (no high availability)

---

## 10. Decision Framework

### When to Use Each LightRAG Query Mode

| Query Mode | Use When | Example Query | Performance |
|------------|----------|---------------|-------------|
| **Hybrid** | Portfolio analysis, multi-aspect queries (DEFAULT) | "What are top 3 portfolio risks?" | Medium (2-5s) |
| **Local** | Document-focused, specific company research | "Summarize NVDA's latest earnings" | Fast (<2s) |
| **Global** | Entity-level, relationship discovery | "What companies are NVDA suppliers?" | Medium (2-4s) |
| **Mix** | Complex queries needing adaptive approach | "How does China risk impact tech holdings?" | Slow (3-6s) |
| **Naive** | Simple keyword search, known fact lookup | "What is NVDA's ticker symbol?" | Very fast (<1s) |
| **KG** | Pure graph traversal, relationship chains | "Show NVDA → TSMC → Apple path" | Fast (1-3s) |

**Decision Logic**:
1. Default to **Hybrid** for portfolio analysis
2. Use **Local** if query mentions specific company/document
3. Use **Global** if query asks about relationships/connections
4. Use **Naive** for simple factual lookups
5. Use **Mix** only for highly complex multi-aspect queries

### When to Add Email Phase 2 (Dual-layer Graph)

**Current State**: Phase 1 (Enhanced Documents) ✅ COMPLETE

**Decision Gate**: Add Phase 2 ONLY IF these conditions occur:
- Ticker extraction accuracy drops <95% (currently >95% ✅)
- Structured query performance >2s for simple filters (currently <2s ✅)
- Source attribution fails regulatory requirements (currently 100% ✅)
- Confidence-based filtering not working from LightRAG queries

**Recommendation**: Continue with Phase 1 (single LightRAG graph) ✅

### When to Use Cloud vs Local LLM

| Scenario | LLM Choice | Rationale |
|----------|------------|-----------|
| Production demos | GPT-4 (cloud) | Highest quality for stakeholders |
| Critical investment decisions | GPT-4 (cloud) | Accuracy > cost |
| Complex multi-hop reasoning | GPT-4 (cloud) | Superior reasoning capability |
| Routine portfolio monitoring | llama3.1:8b (local) | Cost efficiency |
| Development/testing | llama3.1:8b (local) | Fast iteration, no API costs |
| Sensitive proprietary data | llama3.1:8b (local) | Data privacy (never leaves machine) |

**Cost Optimization**:
- Route 20% queries → GPT-4 (critical decisions)
- Route 80% queries → local LLM (routine monitoring)
- Target: <$50/month total LLM costs

### When to Prioritize Data Sources

**Equal Priority** (All 3 sources feed LightRAG):
1. **API/MCP**: Real-time market data, news (always enabled)
2. **Email**: Broker research, analyst reports (CORE source, equal weight)
3. **SEC Filings**: Regulatory documents (quarterly focus, always enabled)

**Rationale**: Single unified LightRAG graph approach means all sources equally important

### When to Integrate Production Modules

**Integration Philosophy**: Simple orchestration + production modules

**Always Integrate** (Don't Duplicate Code):
- Robust HTTP client (circuit breaker + retry logic)
- SecureConfig (encrypted API keys)
- ICESystemManager (health monitoring + graceful degradation)
- ICEQueryProcessor (query fallback logic)
- Data validators (multi-level validation)

**Keep Simple** (Don't Over-Engineer):
- `ice_simplified.py` orchestration (stay understandable)
- Configuration loading (clear environment variables)
- Query interface (straightforward API)

### Code Pattern Examples

**Example 1: HTTP Requests (Always Use Production Client)**

```python
# DON'T: Simple implementation without error handling
response = requests.get(url, timeout=30)
data = response.json()

# DO: Use production robust client
from ice_data_ingestion.robust_client import RobustHTTPClient
client = RobustHTTPClient()
response = client.get(url)  # Circuit breaker + retry + connection pooling
```

**Example 2: Query Processing (Delegate to Production Modules)**

```python
# DON'T: Manual mode selection in orchestrator
if "portfolio" in query:
    mode = "hybrid"
else:
    mode = "local"

# DO: Use production query processor
from src.ice_core.ice_query_processor import ICEQueryProcessor
processor = ICEQueryProcessor(self.core)
result = processor.process_query(query)  # Auto mode selection + fallbacks
```

**Example 3: Configuration (Encrypted Credentials)**

```python
# DON'T: Hardcoded API keys
api_key = "sk-1234567890abcdef"

# DO: Use SecureConfig
from ice_data_ingestion.secure_config import SecureConfig
config = SecureConfig()
api_key = config.get_credential("openai_api_key")  # Encrypted at rest
```

---

## 11. Critical Files & Dependencies

### Files That Must NOT Be Deleted/Renamed

**Without Explicit User Permission**:

1. **`CLAUDE.md`** - Development guidance, commands, workflows
2. **`README.md`** - Project overview, quick start, architecture
3. **`ICE_PRD.md`** - This file (unified requirements)
4. **`ICE_DEVELOPMENT_TODO.md`** - 115-task roadmap, progress tracking
5. **`ICE_VALIDATION_FRAMEWORK.md`** - PIVF (20 golden queries, scoring)
6. **`ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`** - UDMA implementation guide (Option 5)
7. **`PROJECT_STRUCTURE.md`** - Directory organization, navigation
8. **`PROJECT_CHANGELOG.md`** - Change history, dated entries
9. **`archive/strategic_analysis/README.md`** - Architecture decision history (all 5 options)
10. **`ice_building_workflow.ipynb`** - Knowledge graph construction workflow
11. **`ice_query_workflow.ipynb`** - Investment intelligence analysis workflow
12. **`requirements.txt`** - Core dependencies

**Rationale**: These files are cross-referenced throughout documentation and workflows. Deletion breaks project navigation.

### 5-File Synchronization Workflow

**CRITICAL RULE**: When creating/modifying core project files, update ALL 5 linked core documentation files:

1. **PROJECT_STRUCTURE.md** - Add file to directory structure section
2. **CLAUDE.md** - Add file reference to relevant technical section
3. **README.md** - Add file to user-facing documentation guides
4. **PROJECT_CHANGELOG.md** - Add dated entry documenting change
5. **ICE_DEVELOPMENT_TODO.md** - Add/update tasks if new file creates work

**When This Rule Applies**:
- ✅ Creating new documentation files (*.md)
- ✅ Creating new core configuration files
- ✅ Adding new architectural components
- ✅ Creating new validation frameworks or test suites
- ❌ NOT for temporary/test files in `sandbox/`
- ❌ NOT for backup/archive files

**Example**: Creating this PRD file triggered updates to all 5 files + Serena memory

### Critical Dependencies

**Production Modules** (34K+ lines):
- `ice_data_ingestion/` (17,256 lines) - API clients, robust framework, SEC connector
- `imap_email_ingestion_pipeline/` (12,810 lines) - Email intelligence, enhanced documents
- `src/ice_core/` (3,955 lines) - System orchestration, query processing

**Python Libraries**:
- `lightrag>=0.1.0` - Core knowledge graph engine
- `openai>=1.0.0` - OpenAI API client (GPT-4)
- `pandas>=2.0.0` - Data manipulation
- `networkx>=3.0` - Graph operations
- `streamlit>=1.28.0` - UI (shelved until Phase 5)

**External Services**:
- OpenAI API (GPT-4) - Cloud LLM
- Ollama (llama3.1:8b) - Local LLM
- NewsAPI, Finnhub, Alpha Vantage, FMP - Financial data
- SEC EDGAR - Regulatory filings

---

## 12. Appendix: Quick Reference

### Key Metrics at a Glance

| Metric | Current Status | Target |
|--------|----------------|--------|
| **Project Completion** | 39% (45/115 tasks) | 100% |
| **Current Phase** | Phase 2 Week 2 | Phase 5 |
| **Email Phase 1** | ✅ Complete | ✅ Complete |
| **Data Sources** | 3 (API + Email + SEC) | 3 |
| **Documents Ingested** | 26 | 1,000+ |
| **Entity Extraction F1** | >0.95 | >0.85 |
| **Query Latency** | <2s (structured) | <2s |
| **PIVF Score** | TBD | >7.5/10 |
| **LLM Cost (monthly)** | TBD | <$50 |

### Development Quick Links

- **Primary Interfaces**: `ice_building_workflow.ipynb`, `ice_query_workflow.ipynb`
- **Orchestrator**: `updated_architectures/implementation/ice_simplified.py`
- **Architecture Plan**: `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` (UDMA implementation guide)
- **Architecture History**: `archive/strategic_analysis/README.md` (all 5 options analyzed)
- **Validation Framework**: `ICE_VALIDATION_FRAMEWORK.md`
- **Task Tracking**: `ICE_DEVELOPMENT_TODO.md`
- **Developer Guide**: `CLAUDE.md`

### Contact & Contribution

**Author**: Roy Yeo Fu Qiang (A0280541L)
**Institution**: National University of Singapore
**Project**: DBA5102 Business Analytics Capstone

---

**Document Version**: 1.0
**Last Updated**: 2025-01-22
**Next Review**: After Week 2 integration completion
