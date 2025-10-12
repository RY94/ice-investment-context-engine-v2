# ICE Codebase Structure (Updated: 2025-01-22)

## Architecture Integration Philosophy

**Current Strategy**: Simple Orchestration + Production Modules = Best of Both Worlds
- Keep simple, understandable orchestration layer
- Import and use robust production modules (34K+ lines)
- Avoid code duplication, leverage existing capabilities
- Integration roadmap: `ARCHITECTURE_INTEGRATION_PLAN.md` (6-week plan)

## Root Directory Organization

### Core Implementation Files
- **`ARCHITECTURE_INTEGRATION_PLAN.md`** - 6-week integration roadmap (Week 1 COMPLETE)
- **`ICE_VALIDATION_FRAMEWORK.md`** - PIVF with 20 golden queries, 9-dimensional scoring
- **`ice_building_workflow.ipynb`** - Knowledge graph building workflow notebook (PRIMARY INTERFACE)
- **`ice_query_workflow.ipynb`** - Investment intelligence analysis workflow notebook (PRIMARY INTERFACE)
- **`README.md`** - Project overview and documentation entry point
- **`CLAUDE.md`** - Essential development guidance and power user commands
- **`PROJECT_STRUCTURE.md`** - Complete directory organization reference
- **`ICE_DEVELOPMENT_TODO.md`** - 115-task comprehensive roadmap (39% complete)
- **`PROJECT_CHANGELOG.md`** - Detailed development change log with dated entries
- **`requirements.txt`** - Core dependency specification

### Main Directories

#### `updated_architectures/implementation/` - Simple Orchestrator (INTEGRATION IN PROGRESS)
**Status**: Week 1 Complete - Data ingestion integrated (API + Email + SEC → LightRAG)
**Next**: Week 2-6 will integrate remaining production modules

**Current Files**:
- **`ice_simplified.py`** - Simple orchestrator (currently self-contained, will import from production modules)
- **`config.py`** - Environment config (will upgrade to SecureConfig in Week 3)
- **`data_ingestion.py`** - Data APIs (✅ Week 1: integrated robust_client, email, SEC sources)
- **`query_engine.py`** - Portfolio analysis (Week 4: will use ICEQueryProcessor with fallbacks)
- **`ice_core.py`** - Direct LightRAG wrapper (374 lines)
- **`tests/`** - Structure + functional tests

**Week 1 Achievements** ✅:
- Integrated robust HTTP client with circuit breaker + retry logic
- Email pipeline feeding 74 sample emails to LightRAG (enhanced documents)
- SEC EDGAR async connector for regulatory filings
- 26 documents successfully ingested (3 email + 9 API + 6 SEC + 8 news)

#### `ice_data_ingestion/` - 🏭 PRODUCTION DATA FRAMEWORK (17,256 lines, 38 files)
**Status**: Week 1 INTEGRATED with simplified architecture
**Integration Method**: Import robust_client, validators, SEC connector

**Key Components**:
- **`robust_client.py`** - ✅ INTEGRATED: HTTP client with circuit breaker, retry logic, connection pooling
- **`secure_config.py`** - Week 3: Encrypted API key management with rotation (to be integrated)
- **`data_validator.py`** - Multi-level validation framework
- **`test_scenarios.py`** - Comprehensive test coverage (5 suites)
- **`sec_edgar_connector.py`** - ✅ INTEGRATED: SEC filing data connector (async)
- **API Clients**: NewsAPI, Alpha Vantage, Finnhub, FMP, Bloomberg, Polygon
- **MCP Infrastructure**: Advanced protocol for data ingestion

#### `imap_email_ingestion_pipeline/` - 🏭 PRODUCTION EMAIL PIPELINE (12,810 lines, 31 files)
**Status**: ✅ PHASE 1 COMPLETE (2025-01-22) - Week 1 INTEGRATED
**Integration Method**: Enhanced document generation → LightRAG (single graph approach)

**Key Components**:
- **`email_connector.py`** - Email data source for broker research and analyst reports
- **`contextual_signal_extractor.py`** - BUY/SELL/HOLD signal extraction from emails
- **`intelligent_link_processor.py`** - PDF downloads from email links
- **`attachment_processor.py`** - OCR and document processing from attachments
- **`enhanced_doc_creator.py`** - ✅ NEW: Creates enhanced documents with inline metadata
  - Ticker/rating/price target markup: `[TICKER:NVDA|confidence:0.95]`
  - Source attribution: `[SOURCE_EMAIL:12345|sender:analyst@firm.com|date:2024-03-15]`
  - Confidence preservation throughout LightRAG pipeline
  - 27/27 unit tests passing
- **`ice_integrator.py`** - ✅ UPDATED: Uses enhanced documents (use_enhanced=True default)
- **`tests/test_email_graph_integration.py`** - ✅ NEW: Phase 1 validation tests (all passing)

**Phase 1 Validation Results** ✅:
- Ticker extraction accuracy: >95% (PASSED)
- Confidence preservation: Inline markup validated (PASSED)
- Structured query performance: <2s (PASSED)
- Source attribution: Traceable (PASSED)
- Cost optimization: No duplicate LLM calls (PASSED)

**Decision**: Phase 2 (dual-layer graph) NOT NEEDED - Single LightRAG graph sufficient

#### `src/` - Core System Components

##### `src/ice_lightrag/` - LightRAG Integration
- **`ice_rag.py`** - Main LightRAG wrapper (used by simplified)
- **`ice_rag_fixed.py`** - JupyterSyncWrapper (imported by simplified)
- **`setup.py`** - Dependencies installation
- **`test_basic.py`** - Core functionality tests
- **`storage/`** - LightRAG knowledge graph persistence

##### `src/ice_core/` - 🏭 PRODUCTION ORCHESTRATION (3,955 lines, 9 files)
**Status**: Week 2 (to be integrated with simplified architecture)

**Key Components**:
- **`ice_system_manager.py`** - System orchestration with health monitoring (Week 2 integration)
- **`ice_query_processor.py`** - Query processing with fallbacks (Week 4 integration)
- **`ice_graph_builder.py`** - Graph construction utilities
- **`ice_unified_rag.py`** - Unified RAG engine implementation
- **`ice_error_handling.py`** - Error handling utilities
- **`ice_data_manager.py`** - Data management coordination

#### `data/` - Data Storage and Samples
- **`sample_data.py`** - Sample financial data for development
- **`data_loader.py`** - Data loading utilities
- **`emails_samples/`** - 74 sample financial emails (✅ integrated Week 1)
- **`user_profiles/`** - User portfolios and preferences
- **`portfolio_holdings.xlsx`** - Sample portfolio data

#### `tests/` - Testing Infrastructure
- **`test_runner.py`** - Comprehensive test execution
- **`test_dual_notebook_integration.py`** - Dual workflow validation (10 tests, 100% pass)
- **`test_email_graph_integration.py`** - ✅ NEW: Email Phase 1 validation (5 tests, all passing)
- **`conftest.py`** - Pytest configuration
- Multiple test subdirectories for different components

#### Other Key Directories
- **`setup/`** - Environment configuration and local LLM setup
  - `local_llm_setup.py` - Ollama integration framework
  - `local_llm_adapter.py` - Local LLM adapter
  - `setup_ice_api_keys.py` - API key configuration
- **`mcp_servers/`** - MCP server integrations
  - `financial-datasets-mcp/` - Financial data MCP server
  - `yahoo-finance-mcp/` - Yahoo Finance MCP server
- **`project_information/`** - Project documentation
  - `about_lightrag/` - LightRAG workflow documentation (building + query guides)
  - `about_graphrag/` - GraphRAG research notes
  - `development_plans/` - Development roadmaps and notebook designs
- **`archive/`** - Organized backups and legacy files
  - `backups/data_ingestion_pre_integration_2025-01-22.py` - Pre-integration backup
  - `completed_todos/` - Archived completed task documentation
- **`sandbox/`** - Development experiments and prototypes
- **`UI/`** - Streamlit interface (SHELVED until Phase 5 - post 90% AI completion)

## Data Flow Architecture (Integrated - Week 1 Complete)

```
ICE Simplified (Orchestrator)
         ↓
✅ Production Data Sources (ALL feed LightRAG - Week 1 COMPLETE):
  1. API/MCP (ice_data_ingestion/)
     - NewsAPI, Finnhub, Alpha Vantage, FMP
     - MCP infrastructure
     - SEC EDGAR connector (async)
     - Circuit breaker + retry logic
  
  2. Email (imap_email_ingestion_pipeline/)
     - Broker research emails (74 samples)
     - Enhanced documents with inline metadata
     - Analyst reports (PDF downloads)
     - BUY/SELL/HOLD signal extraction
     - EntityExtractor enrichment (no duplicate LLM calls)
  
  3. Robust Framework (INTEGRATED)
     - Circuit breaker + retry (robust_client)
     - Connection pooling
     - Multi-level validation
         ↓
LightRAG Knowledge Graph (Single Unified Graph)
  - Entity extraction
  - Relationship building
  - Vector + Graph + Full-text storage
  - Enhanced document metadata preserved
         ↓
Query Processing (Week 4 - to be enhanced)
  - 6 LightRAG modes (local, global, hybrid, mix, naive, kg)
  - Portfolio analysis
  - ICEQueryProcessor integration (Week 4)
```

## Integration Roadmap Status (6 Weeks)

- ✅ **Week 1 COMPLETE**: Data Ingestion (robust_client + email + SEC sources) - 26 docs in LightRAG
- **Week 2 (NEXT)**: Core Orchestration (integrate ICESystemManager with health monitoring)
- **Week 3**: Configuration (upgrade to SecureConfig for encrypted API keys)
- **Week 4**: Query Enhancement (integrate ICEQueryProcessor with fallback logic)
- **Week 5**: Workflow Notebooks (demonstrate integrated features in dual workflow)
- **Week 6**: Testing & Validation (end-to-end integration tests)

## Critical File Protection
Never delete or rename without explicit permission:
- `ARCHITECTURE_INTEGRATION_PLAN.md`
- `ICE_VALIDATION_FRAMEWORK.md`
- `ICE_DEVELOPMENT_TODO.md`
- `ice_building_workflow.ipynb`
- `ice_query_workflow.ipynb`
- `PROJECT_STRUCTURE.md`
- `PROJECT_CHANGELOG.md`
- `README.md`
- `CLAUDE.md`