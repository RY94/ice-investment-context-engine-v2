# CLAUDE.md - ICE Development Guide

> **🔗 LINKED DOCUMENTATION**: This is one of 6 essential core files that must stay synchronized. When updating this file, always cross-check and update related files: `README.md`, `PROJECT_STRUCTURE.md`, `ICE_DEVELOPMENT_TODO.md`, `PROJECT_CHANGELOG.md`, and `ICE_PRD.md`.

**Location**: `/CLAUDE.md`
**Purpose**: Comprehensive development guidance for Claude Code instances working on ICE
**Last Updated**: 2025-10-24
**Target Audience**: Claude Code AI and human developers

---

## 1. 🚀 QUICK REFERENCE

### Current Project Status

**Phase**: UDMA Integration Complete (Week 6/6) ✅ | 57% (73/128 tasks)

> **📖 For sprint priorities and detailed status**: See `ICE_DEVELOPMENT_TODO.md:1-60`
> **📖 For week completion tracking**: See `PROJECT_CHANGELOG.md`

### Essential Commands

**Quick Start**
```bash
export OPENAI_API_KEY="sk-..." && cd updated_architectures/implementation
python config.py  # Test configuration
python ice_simplified.py  # Run complete system
```

**Development Workflows**
```bash
jupyter notebook ice_building_workflow.ipynb  # Knowledge graph building
jupyter notebook ice_query_workflow.ipynb  # Investment intelligence analysis
export ICE_DEBUG=1 && python src/simple_demo.py  # Debug mode
```

**Testing & Validation**
```bash
python src/ice_lightrag/test_basic.py && python test_api_key.py
python tests/test_imap_email_pipeline_comprehensive.py  # IMAP tests (21 tests, all passing)
jupyter notebook ice_query_workflow.ipynb  # Portfolio analysis (11 test datasets)
```

### Critical Files Quick Reference

| File | Purpose | See Also |
|------|---------|----------|
| `ice_simplified.py` | Main orchestrator (1,366 lines) | Section 3.2 |
| `ice_building_workflow.ipynb` | Knowledge graph construction | Section 3.3 |
| `ice_query_workflow.ipynb` | Investment analysis interface | Section 3.3 |
| `ICE_PRD.md` | Complete product requirements | - |
| `ICE_DEVELOPMENT_TODO.md` | Task tracking (128 tasks) | - |
| `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` | UDMA guide (Option 5) | Section 2 |
| `ICE_VALIDATION_FRAMEWORK.md` | PIVF (20 golden queries) | Section 3.5 |
| `PROJECT_STRUCTURE.md` | Directory organization | Section 5 |

> **📖 For complete file catalog with descriptions**: See `PROJECT_STRUCTURE.md:268-295`
> **📖 For portfolio test datasets (11 portfolios)**: See `PROJECT_STRUCTURE.md:103-122`

---

## 2. 📋 DEVELOPMENT CONTEXT

### What is ICE?

**Investment Context Engine (ICE)** is a modular AI system serving as the cognitive backbone for boutique hedge fund workflows, solving four critical pain points:
1. Delayed Signal Capture
2. Low Insight Reusability
3. Inconsistent Decision Context
4. Manual Triage Bottlenecks

> **📖 For complete product vision and user personas**: See `ICE_PRD.md:1-100`
> **📖 For detailed user personas**: See `project_information/user_research/ICE_USER_PERSONAS_DETAILED.md`

### Current Architecture

**UDMA (User-Directed Modular Architecture)** - Simple Orchestration + Production Modules

> **📖 For complete data flow diagram**: See `README.md:38-69`
> **📖 For storage architecture details**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` Section 9
> **📖 For complete UDMA implementation guide**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md`
> **📖 For architecture decision history (5 options analyzed)**: See `archive/strategic_analysis/README.md`

### Integration Status

> **📖 For UDMA implementation phases and 6-week integration timeline**: See `ICE_DEVELOPMENT_TODO.md:19-57`

### Docling Integration (Switchable Architecture)

**Docling** is IBM's open-source AI-powered document parser integrated into ICE for professional-grade table extraction (42% → 97.9% accuracy).

**Switchable Design**: Both original and docling implementations coexist. Toggle via `config.py`:

```bash
# Enable docling for SEC filings (default: true)
export USE_DOCLING_SEC=true

# Enable docling for email attachments (default: true)
export USE_DOCLING_EMAIL=true

# Disable to use original implementations
export USE_DOCLING_SEC=false
export USE_DOCLING_EMAIL=false
```

**Key Features**:
- SEC Filing Processor: Extracts financial tables from 10-K/10-Q (0% → 97.9% content extraction)
- Email Attachment Processor: Drop-in replacement for PyPDF2/openpyxl (42% → 97.9% table accuracy)
- EntityExtractor + GraphBuilder integration: Same pipeline as email workflow
- Production-grade: RobustHTTPClient, caching, clear error handling

> **📖 For testing procedures and toggle usage**: See `md_files/DOCLING_INTEGRATION_TESTING.md`
> **📖 For architecture patterns and design decisions**: See `md_files/DOCLING_INTEGRATION_ARCHITECTURE.md`
> **📖 For future integrations (uploads, archives, news)**: See `md_files/DOCLING_FUTURE_INTEGRATIONS.md`

### Design Philosophy

> **Strategic Positioning**: ICE delivers professional-grade investment intelligence for boutique hedge funds (<$100M AUM) at <$200/month through cost-conscious, relationship-focused architecture.

**Core Principles** (in priority order):

1. **Quality Within Resource Constraints**: Target 80-90% capability at <20% enterprise cost. Accept professional-grade over perfection. (F1≥0.85, <$200/month budget)

2. **Hidden Relationships Over Surface Facts**: Graph-first strategy for multi-hop reasoning (1-3 hops). Trust semantic search for relevance, not manual filtering.

3. **Fact-Grounded with Source Attribution**: 100% source traceability, confidence scores on all entities/relationships, complete audit trail.

4. **User-Directed Evolution**: Build for ACTUAL problems, not imagined ones. Test → Decide → Integrate. Evidence-driven, not speculative. (<10,000 line budget)

5. **Simple Orchestration + Battle-Tested Modules**: Delegate to production modules (34K+ lines), keep orchestrator simple (<2,000 lines). No reinventing wheels.

6. **Cost-Consciousness as Design Constraint**: 80% queries → local LLM, 20% → cloud. Semantic caching (70% hit rate). Free-tier APIs prioritized.

> **📖 For detailed philosophy**: See `project_information/development_plans/Development Brainstorm Plans (md files)/Lean_ICE_Architecture.md`

---

## 3. 🛠️ CORE DEVELOPMENT WORKFLOWS

### 3.1 Starting a New Development Session

1. **Read current status**: Check `ICE_DEVELOPMENT_TODO.md` for current sprint tasks
2. **Review recent changes**: Check `PROJECT_CHANGELOG.md` for latest updates
3. **Understand context**: Read relevant section in `ICE_PRD.md` for requirements
4. **Check file locations**: Use `PROJECT_STRUCTURE.md` to navigate codebase
5. **Set environment**: `export OPENAI_API_KEY="sk-..."` and any other required API keys

### 3.2 Common Development Tasks

**Adding New Data Sources**
```python
# DO: Use production robust client
from ice_data_ingestion.robust_client import RobustHTTPClient
client = RobustHTTPClient()
response = client.get(url)  # Circuit breaker + retry included
```

**Workflow**:
1. Check `ice_data_ingestion/` for existing connectors
2. Import and use in `data_ingestion.py` if exists
3. Create enhanced documents with inline metadata (see Email pipeline pattern)
4. Test with PIVF golden queries

**Modifying Orchestration**
```python
# DO: Delegate to production modules
from src.ice_core.ice_query_processor import ICEQueryProcessor

class ICESimplified:
    def __init__(self):
        self.query_processor = ICEQueryProcessor(self.core)
```

### 3.3 Notebook Development

**When to update notebooks**:
- Core data ingestion changes → Update `ice_building_workflow.ipynb`
- Query processing modifications → Update `ice_query_workflow.ipynb`

**Process**: Modify production code first → Update notebook cells → Run end-to-end validation

**Query Visualization Features** (Cells 31 & 32):
The `ice_building_workflow.ipynb` includes two complementary graph visualizations after each query:

**Cell 31 - Static Visualization** (matplotlib):
- Fixed PNG image for reports/presentations
- Shows entities mentioned in answer (red nodes) and 2-hop neighbors (teal nodes)
- Edge labels with relationship descriptions
- Good for: Final reports, PDFs, presentations

**Cell 32 - Interactive Visualization** (pyvis):
- Interactive HTML with click, drag, zoom, pan
- Click nodes to highlight 1st/2nd degree neighbors
- Hover for rich tooltips (entity type, confidence, description, source)
- Dark mode styling with colored nodes by entity type
- Good for: Exploration, analysis, understanding reasoning paths
- See Serena memory `interactive_graph_visualization_pyvis_2025_10_27` for details

**Cell 30.5 - Confidence-Based Entity Filtering** (NEW):
- Filters query results by entity confidence scores
- **High confidence (≥0.80)**: EntityExtractor + TickerValidator validated entities
- **Low confidence (<0.80)**: LightRAG automatic extraction (may include false positives)
- Shows breakdown of validated vs unvalidated entities per query
- **Use for**: Investment decisions requiring high-precision entity data
- See Serena memory `confidence_filtering_two_layer_2025_11_04` for two-layer extraction design

**Consolidated Control System** (Cell 26):
The notebook uses a single consolidated cell for all data source configuration:
- **Layer 1**: Source type switches (email_source_enabled, api_source_enabled, mcp_source_enabled)
- **Portfolio Selector**: 4 tiers (tiny/small/medium/full) with preset holdings + category limits
- **Email Selector**: 4 modes (all/crawl4ai_test/docling_test/custom) for targeted email processing
- **Layer 2**: Category limits (email_limit, news_limit, financial_limit, market_limit, sec_limit, research_limit)
- **Precedence**: Source switch → Category limit → Special selector (EMAIL_SELECTOR)

**Note**: Cells 24 & 25 are deprecated (commented out). All configuration now in Cell 26.

See Serena memory `notebook_cell_26_consolidation_2025_10_24` for architecture decision and validation.

### 3.4 TodoWrite Mandatory Practice ⚠️

**CRITICAL**: Every TodoWrite list MUST include these two todos as the FINAL items:

```
[ ] 📋 Review & update 6 core files + 2 notebooks if changes warrant synchronization
    - Core files: PROJECT_STRUCTURE.md, CLAUDE.md, README.md, PROJECT_CHANGELOG.md, ICE_DEVELOPMENT_TODO.md, ICE_PRD.md
    - Notebooks: ice_building_workflow.ipynb, ice_query_workflow.ipynb
    - Skip only if: bug fixes, minor code changes, temporary/test files

[ ] 🧠 Update Serena server memory if work warrants documentation
    - Use mcp__serena__write_memory for: architecture decisions, implementation patterns, debugging solutions
    - Memory names: Use descriptive names (e.g., 'week6_testing_patterns', 'email_integration_debugging')
    - Document: Key decisions, file locations, workflows, solutions to complex problems
    - Skip only if: Minor bug fixes, temporary code, work-in-progress, trivial changes
```

**Why**: Prevents documentation drift and preserves institutional knowledge across Claude Code sessions.

### 3.5 Testing and Validation

**Three-tier approach**:

1. **Unit Tests**: Component-level validation
   ```bash
   python tests/test_email_graph_integration.py
   python src/ice_lightrag/test_basic.py
   ```

2. **Integration Tests**: End-to-end workflow validation
   ```bash
   jupyter notebook ice_building_workflow.ipynb
   jupyter notebook ice_query_workflow.ipynb
   ```

3. **PIVF Validation**: Golden query benchmarking
   - Reference: `ICE_VALIDATION_FRAMEWORK.md`
   - 20 golden queries covering 1-3 hop reasoning
   - 9-dimensional scoring

### 3.6 Debugging Workflows

1. Check system health: `python check/health_checks.py`
2. Review logs: `logs/session_start.json`, `logs/pre_tool_use.json`
3. Validate data sources: `sandbox/python_notebook/ice_data_sources_demo_simple.ipynb`
4. **LightRAG storage**: `ice_lightrag/storage/` (vector DBs and graph data)
5. **Direct testing**: `python src/ice_lightrag/quick_test.py`

---

## 4. 📐 DEVELOPMENT STANDARDS

### 4.1 TodoWrite Requirements (MANDATORY) ⚠️

**CRITICAL**: Every TodoWrite list MUST include these two todos as the FINAL items:

```
[ ] 📋 Review & update 6 core files + 2 notebooks if changes warrant synchronization
[ ] 🧠 Update Serena server memory if work warrants documentation
```

See Section 3.4 for complete details.

### 4.2 File Header Requirements

**Every file must start with these 4 comment lines**:
```python
# Location: /path/to/file.py
# Purpose: Clear description of what this file does
# Why: Business purpose and role in ICE architecture
# Relevant Files: file1.py, file2.py, file3.py
```

### 4.3 Comment Principles

```python
# DON'T: Obvious syntax comments
x = x + 1  # Increment x

# DO: Explain thought process and business logic
# Confidence threshold set to 0.7 based on PIVF validation showing
# accuracy >95% at this level while minimizing false positives
confidence_threshold = 0.7
```

**NEVER delete explanatory comments** unless demonstrably wrong or obsolete.

### 4.4 ICE-Specific Patterns

**1. Source Attribution** - Every fact must trace to source
```python
edge_metadata = {
    "source_document_id": "email_12345",
    "confidence": 0.92,
    "timestamp": "2024-03-15T10:30:00Z"
}
```

**2. Confidence Scoring** - All entities/relationships include confidence
```python
"""
[TICKER:NVDA|confidence:0.95] [RATING:BUY|confidence:0.87]
Goldman Sachs raised price target to [PRICE_TARGET:500|confidence:0.92]
"""
```

**3. Multi-hop Reasoning** - Support 1-3 hop graph traversal
```python
query_1_hop = "Which suppliers does NVDA depend on?"
query_2_hop = "How does China risk impact NVDA through TSMC?"
query_3_hop = "What portfolios are exposed to AI regulation via chip suppliers?"
```

**4. MCP Compatibility** - Format outputs as structured JSON
```python
result = {
    "query": "...",
    "answer": "...",
    "sources": [...],
    "confidence": 0.85
}
```

**5. SOURCE Markers** - Document source attribution for statistics tracking
```python
# Data layer tags documents with source
{'content': '...', 'source': 'fmp'}

# Orchestrator embeds SOURCE markers in content (survives LightRAG storage)
content_with_marker = f"[SOURCE:FMP|SYMBOL:NVDA]\n{content}"

# Statistics layer parses markers for source breakdown
match = re.search(r'\[SOURCE:(\w+)\|', content)
if match:
    source = match.group(1).lower()  # 'fmp', 'newsapi', 'sec_edgar', etc.
```

**6. Crawl4AI Hybrid URL Fetching** - Smart routing for web scraping with 6-tier classification
```python
# Enable/disable Crawl4AI (follows Docling switchable pattern)
# In notebook Cell 1 or command line:
export USE_CRAWL4AI_LINKS=true   # Enable hybrid approach
export USE_CRAWL4AI_LINKS=false  # Disable (simple HTTP only, default)
export CRAWL4AI_TIMEOUT=60       # Timeout per page (seconds)
export CRAWL4AI_HEADLESS=true    # Run browser in background

# URL Rate Limiting (added 2025-11-05 for robustness)
export URL_RATE_LIMIT_DELAY=1.0      # Seconds between requests per domain (default: 1.0)
export URL_CONCURRENT_DOWNLOADS=3     # Max concurrent downloads (default: 3)

# Configuration in config.py
self.use_crawl4ai_links = os.getenv('USE_CRAWL4AI_LINKS', 'false').lower() == 'true'
self.crawl4ai_timeout = int(os.getenv('CRAWL4AI_TIMEOUT', '60'))
self.rate_limit_delay = float(os.getenv('URL_RATE_LIMIT_DELAY', '1.0'))
self.concurrent_downloads = int(os.getenv('URL_CONCURRENT_DOWNLOADS', '3'))

# 6-Tier URL Classification System in IntelligentLinkProcessor
# Tier 1-2: Simple HTTP (direct PDFs, token auth) - Always enabled
# Tier 3-5: Crawl4AI (JS sites, portals, paywalls) - Requires enablement
# Tier 6: Skip (social media, tracking) - Always skipped

# Smart routing logic
if tier in [1, 2]:
    content = await self._download_with_retry(session, url)  # DBS PDFs, SEC EDGAR
elif tier in [3, 4, 5] and self.use_crawl4ai:
    content = await self._fetch_with_crawl4ai(url)  # Goldman, Morgan Stanley, WSJ
else:
    # Graceful degradation: fallback to simple HTTP if Crawl4AI disabled/fails
    try:
        content = await self._download_with_retry(session, url)
    except:
        if self.use_crawl4ai:
            content = await self._fetch_with_crawl4ai(url)

# Success Criteria (4 Levels)
# Level 1: URLs extracted from email bodies ✅
# Level 2: Content downloaded via HTTP or Crawl4AI ⚠️ (needs enablement)
# Level 3: Text/tables extracted via Docling ✅
# Level 4: Entities/relationships ingested into LightRAG ✅

# Cache Management
# Clear cache for testing: rm -rf data/link_cache/*
```

**Integration:** 103 lines added to 3 files (config.py, intelligent_link_processor.py, ultra_refined_email_processor.py)
**Notebook Enablement:** `ice_building_workflow.ipynb` Cell 1 updated with Crawl4AI env vars (2025-11-04)
**Documentation:** `md_files/CRAWL4AI_INTEGRATION_PLAN.md` (comprehensive plan)
**Memory:** `crawl4ai_hybrid_integration_plan_2025_10_21`, `crawl4ai_enablement_notebook_2025_11_04` (Serena memory)

**7. Two-Layer Entity Extraction + Confidence Filtering** - Validated entities with quality scores
```python
# Layer 1: EntityExtractor + TickerValidator (HIGH confidence 0.85-0.95)
entities = extractor.extract_entities(text)
filtered_entities = validator.filter_tickers(entities)  # Removes false positives

# Layer 2: LightRAG automatic extraction (LOW confidence 0.50-0.65)
# Runs automatically during document ingestion

# Query-time filtering by confidence threshold
high_conf_entities = [e for e in entities if e['confidence'] >= 0.80]
```

**Integration:** TickerValidator filters false positive tickers (I, NOT, BUY, SELL, etc.) at 5 points in data_ingestion.py
**Files:** `imap_email_ingestion_pipeline/ticker_validator.py`, `tests/test_ticker_validator.py`
**Impact:** 70% noise reduction on URL PDF entity extraction
**Usage:** Cell 30.5 in `ice_building_workflow.ipynb` demonstrates confidence filtering
**Memory:** `ticker_validator_noise_reduction_2025_11_04`, `confidence_filtering_two_layer_2025_11_04` (Serena memory)

### 4.5 Code Organization Principles

1. **Modularity**: Build lightweight, maintainable components
2. **Simplicity**: Favor straightforward solutions over complex architectures
3. **Reusability**: Import from production modules, don't duplicate code
4. **Traceability**: Every fact must have source attribution
5. **Security**: Never expose API keys or credentials in code/commits

### 4.6 Protected Files - NEVER Delete or Move

- `CLAUDE.md` (this file)
- `README.md`
- `ICE_PRD.md`
- `ICE_DEVELOPMENT_TODO.md`
- `PROJECT_STRUCTURE.md`
- `PROJECT_CHANGELOG.md`
- `ice_building_workflow.ipynb`
- `ice_query_workflow.ipynb`

**Before modifying**: Create timestamped backup in `archive/backups/`

---

## 5. 🗂️ NAVIGATION & QUICK DECISIONS

### Documentation Quick Reference

| Document | When to Use | Key Content |
|----------|-------------|-------------|
| **ICE_PRD.md** | Starting new features, validating requirements | Product vision, user personas, success metrics |
| **ICE_DEVELOPMENT_TODO.md** | Planning sprints, tracking progress | 128 tasks across 5 phases with status |
| **PROJECT_STRUCTURE.md** | Finding files, understanding layout | Complete directory tree, file descriptions |
| **ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md** | Architecture decisions, UDMA planning | UDMA guide, implementation phases, build scripts |
| **ICE_VALIDATION_FRAMEWORK.md** | Testing changes, benchmarking | PIVF with 20 golden queries, 9D scoring |
| **PROJECT_CHANGELOG.md** | Understanding recent changes | Day-by-day change tracking |
| **CLAUDE.md** | Session start, learning workflows | Quick reference, standards, workflows |

> **📖 For complete file catalog**: See `PROJECT_STRUCTURE.md:268-295`

### Key Decision Trees

**Query Mode Selection**

> **📖 For complete query mode guide**: See `md_files/QUERY_PATTERNS.md:10-100`

| Mode | Use Case | Example |
|------|----------|---------|
| **local** | Entity lookup | "What is NVDA's market cap?" |
| **global** | High-level summaries | "Summarize AI chip market trends" |
| **hybrid** | Investment analysis (recommended) | "How does China risk impact NVDA?" |
| **mix** | Multi-aspect queries | "Portfolio exposure to AI regulation" |
| **naive** | Semantic search | "Find mentions of TSMC" |

**Data Source Prioritization**

| Priority For | Order |
|--------------|-------|
| Real-time signals | API/MCP → Email → SEC |
| Deep research | Email → SEC → API/MCP |
| Regulatory compliance | SEC → Email → API/MCP |

**IMAP Email Pipeline**

> **📖 For detailed IMAP integration reference**: See Serena memory `imap_integration_reference`

**Brief Overview**: 71 emails → EntityExtractor (668 lines) → GraphBuilder (680 lines) → Enhanced documents → LightRAG

**Working with Email Data**:
```python
ice.ingest_portfolio_data(['NVDA', 'AAPL'])  # Standard workflow
```

**Notebook vs Script Development**

| Use Notebooks | Use Scripts |
|---------------|-------------|
| Interactive testing | Production orchestration |
| End-to-end validation | Automated pipelines |
| Debugging | API integrations |

**Create vs Modify Files**

| Create New | Modify Existing |
|------------|-----------------|
| New data connector | Extending functionality |
| New validation framework | Bug fixes/optimizations |
| New architectural component | Adding features to existing |

**Before creating**: Check `PROJECT_STRUCTURE.md` for similar files

**Production Modules vs Simple Code**

| Use Production Modules | Use Simple Code |
|------------------------|-----------------|
| HTTP requests (`robust_client`) | Coordination/orchestration |
| API integrations | Workflow sequencing |
| Data validation | High-level business logic |
| Query processing (`ICEQueryProcessor`) | Main entry points |

**Development Workflow Strategies**

Two strategies for faster development iterations:

**Strategy A: Skip Graph Building** (RECOMMENDED for 90% of dev work)
```python
# ice_building_workflow.ipynb, Cell 22
REBUILD_GRAPH = False  # Use existing graph (instant!)
```
- ⚡ **Time**: Instant (0 minutes)
- ✅ **Coverage**: Full 178-doc graph, all 3 sources
- 📍 **Use for**: Query tuning, analysis features, validation testing

**Strategy B: Tiered Portfolio System** (For ingestion testing)
```python
# ice_building_workflow.ipynb, Portfolio Selector Cell
PORTFOLIO_SIZE = 'tiny'  # Options: tiny | small | medium | full
```
- ⏱️ **Time**: 10-102 minutes depending on tier
- ✅ **Coverage**: ALL 3 sources guaranteed in every tier
- 📍 **Use for**: Testing ingestion changes, data source modifications

**Portfolio Tiers** (all guarantee Email + API + SEC coverage):
- `tiny`: 2 tickers, 18 docs (~10 min) - Email(4) + News(4) + Financials(6) + SEC(4)
- `small`: 2 tickers, 41 docs (~25 min) - Email(25) + News(4) + Financials(6) + SEC(6)
- `medium`: 3 tickers, 80 docs (~48 min) - Email(50) + News(6) + Financials(9) + SEC(15)
- `full`: 4 tickers, 178 docs (~102 min) - Email(71) + News(8) + Financials(12) + SEC(16)

---

## 6. 🔧 TROUBLESHOOTING

> **📖 For comprehensive troubleshooting guide**: See Serena memory `troubleshooting_comprehensive_guide_2025_10_18`

### Top 5 Common Issues

**1. API Key Not Found**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
python test_api_key.py  # Verify
```

**2. LightRAG Import Error**
```bash
cd src/ice_lightrag && python setup.py && cd ../..
python src/ice_lightrag/test_basic.py  # Verify
```

**3. Module Import Failures**
```bash
export PYTHONPATH="${PYTHONPATH}:."
python -c "from ice_data_ingestion import robust_client; print('OK')"
```

**4. Jupyter Kernel Issues**
```bash
pip install ipykernel
python -m ipykernel install --user --name=ice_env
```

**5. LightRAG Storage Corruption**
```bash
rm -rf ice_lightrag/storage/*
jupyter notebook ice_building_workflow.ipynb  # Recreate graph
```

**6. Skip Graph Building (Use Existing Graph)**

When working iteratively on query analysis without needing to rebuild the knowledge graph:

```python
# In ice_building_workflow.ipynb Cell 22
REBUILD_GRAPH = False  # Skip 97+ minute graph building process
```

This workflow control:
- Skips data ingestion and graph construction
- Uses existing graph from `ice_lightrag/storage/`
- Creates mock `ingestion_result` for downstream cells
- Saves time when testing query workflows or analysis features

Set `REBUILD_GRAPH = True` to rebuild the graph with fresh data.

### Debug Commands Reference

```bash
python check/health_checks.py  # System health
python src/ice_lightrag/quick_test.py  # LightRAG test
export ICE_DEBUG=1 && python updated_architectures/implementation/ice_simplified.py  # Debug mode
cat logs/session_start.json | python -m json.tool  # Check logs
```

---

## 7. 📚 RESOURCES & DEEP DIVES

### Technical Guides
- **[LightRAG Setup & Configuration](md_files/LIGHTRAG_SETUP.md)** - Complete setup, financial optimizations
- **[Local LLM Guide](md_files/LOCAL_LLM_GUIDE.md)** - Ollama setup, hybrid configurations
- **[Ollama Test Results](md_files/OLLAMA_TEST_RESULTS.md)** - Integration validation
- **[Query Patterns](md_files/QUERY_PATTERNS.md)** - Query strategies, performance

### Architecture Documentation
- **[UDMA Implementation Plan](ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md)** - Complete guide
- **[Architecture Decision History](archive/strategic_analysis/README.md)** - 5 options analyzed
- **[Validation Framework](ICE_VALIDATION_FRAMEWORK.md)** - PIVF methodology

### LightRAG Workflow Guides
- **[Building Workflow](project_information/about_lightrag/lightrag_building_workflow.md)** - Document ingestion
- **[Query Workflow](project_information/about_lightrag/lightrag_query_workflow.md)** - Retrieval strategies

### Data Source Demonstrations
- **[IMAP Email Pipeline Demo](imap_email_ingestion_pipeline/investment_email_extractor_simple.ipynb)** - 25-cell comprehensive demo
  - Entity extraction (tickers, ratings, price targets)
  - BUY/SELL signal extraction with confidence scores
  - Enhanced document format with inline metadata
  - Referenced by ice_building_workflow.ipynb

### Serena Memories (Deep Dives)
- `imap_integration_reference` - Full IMAP pipeline integration details
- `troubleshooting_comprehensive_guide_2025_10_18` - Complete troubleshooting reference
- `comprehensive_email_extraction_2025_10_16` - Email extraction patterns
- `email_ingestion_trust_the_graph_strategy_2025_10_17` - Cross-company relationship discovery
- `phase_2_2_dual_layer_architecture_decision_2025_10_15` - Dual-layer architecture rationale

---

**Last Updated**: 2025-10-18
**Backup**: `archive/backups/CLAUDE_20251018_pre_refinement.md`
**Refinement**: Reduced from 991 lines to 550 lines (45% reduction) while preserving 100% of information via migrations
**Maintenance**: Update this file when major workflows, architecture, or standards change
