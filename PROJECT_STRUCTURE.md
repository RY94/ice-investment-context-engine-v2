# ICE Project Structure Guide

> **🔗 LINKED DOCUMENTATION**: This is one of 8 essential core files that must stay synchronized. When updating this file, always cross-check and update the related files (if applicable): `ARCHITECTURE.md`, `CLAUDE.md`, `README.md`, `ICE_DEVELOPMENT_TODO.md`, `PROJECT_CHANGELOG.md`, `ICE_PRD.md`, and `PROGRESS.md` to maintain consistency across project documentation.

**Location**: `/PROJECT_STRUCTURE.md`
**Purpose**: Comprehensive directory structure guide for Claude Code navigation and understanding
**Business Value**: Enables efficient AI-assisted development by providing clear project organization context
**Relevant Files**: `README.md`, `CLAUDE.md`, `docs/plans/ICE_DEVELOPMENT_PLAN.md`

---

> **🔄 SELF-MAINTAINING**: When adding/removing directories, moving files, or changing project organization, update the directory tree below and file location references throughout this document.

## 🔧 CONTEXT OPTIMIZATION (2025-11-05)

**Purpose**: Reduce Claude Code baseline context by ~743MB through intelligent directory exclusion

**Implementation**: 3-layer protection strategy
1. **Serena MCP** (`.serena/project.yml`): Excludes from indexing but allows access when needed
2. **Claude Settings** (`.claude/settings.local.json`): Hard deny for archive/* (historical files only)
3. **Gitignore** (`.gitignore`): Standard exclusions for build artifacts

**Excluded Directories** (automatically excluded from context but preserved on disk):
- `archive/**` (438MB) - Historical files, fully blocked
- `tmp/**` (299MB) - Old temp files excluded, new temp files still writable per CLAUDE.md workflow
- `logs/**` (3.8MB) - Excluded from indexing but readable for debugging
- `.claude/data/sessions/**` (1.9MB) - Old session data
- `mcp_servers/**` - Embedded git repos
- `data/attachments/**` - Large email attachments
- Build artifacts: `__pycache__/`, `.ipynb_checkpoints/`, `*.pyc`, `.venv/`, `node_modules/`

**Total Context Saved**: ~743MB

**Verification**:
- tmp/ workflow tested: ✅ Write, Execute, Delete working
- logs/ access tested: ✅ Readable for debugging
- Settings backed up to: `.serena/project.yml.backup_20251105_192728`, `.claude/settings.local.json.backup_20251105_192728`

**See Also**: CLAUDE.md Section 6 (Temp files workflow)

---

## 📁 CURRENT PROJECT STRUCTURE (Post-Organization)

```
ICE-Investment-Context-Engine/
├── 📄 Core Project Files
│   ├── README.md                           # Project overview & getting started guide
│   ├── ARCHITECTURE.md                    # 🆕 North star architectural blueprint (invariants, interfaces, design rules)
│   ├── CLAUDE.md                          # 🆕 Claude Code quick reference (293 lines, streamlined 2025-11-05)
│   ├── CLAUDE_PATTERNS.md                 # 🆕 ICE coding patterns with examples (~400 lines)
│   ├── CLAUDE_INTEGRATIONS.md             # 🆕 Docling & Crawl4AI integration guide (~450 lines)
│   ├── CLAUDE_TROUBLESHOOTING.md          # 🆕 Complete troubleshooting reference (~350 lines)
│   ├── ICE_PRD.md                         # 🆕 Product Requirements Document - Unified requirements for Claude Code instances
│   ├── PROJECT_STRUCTURE.md               # This file - comprehensive directory guide
│   ├── PROJECT_CHANGELOG.md               # 🆕 Detailed dev log (day-by-day changes, see also: md_files/CHANGELOG.md for versions)
│   ├── PROGRESS.md                        # 🆕 Session-level state tracker (updated every session, ~50 lines)
│   ├── ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md  # 🆕 UDMA implementation guide (User-Directed Modular Architecture)
│   ├── ICE_VALIDATION_FRAMEWORK.md        # 🆕 PIVF - Comprehensive validation framework (20 golden queries, 9 dimensions)
│   ├── ice_building_workflow.ipynb        # 🆕 Knowledge graph building workflow notebook (Cell 26: Two-layer control system)
│   ├── ice_query_workflow.ipynb           # 🆕 Investment intelligence analysis workflow notebook
│   ├── test_queries.csv                   # 🆕 Test query dataset for validation (12 queries, 3 personas, 5 modes)
│   ├── simple_demo.py                     # Standalone LightRAG demo script
│   ├── ice_main_notebook.ipynb            # ⭐ PRIMARY DEVELOPMENT INTERFACE (New simplified design)
│   └── ice_main_notebook_20250917.ipynb   # 📋 Original notebook (backed up)
│
├── 🆕 Simplified Architecture (Integrated with Production Modules)
│   ├── updated_architectures/             # ⭐ SIMPLE ORCHESTRATOR using production modules
│   │   ├── README.md                      # Architecture overview & deployment guide
│   │   ├── implementation/                # Simple orchestration layer (Week 1-4 INTEGRATED)
│   │   │   ├── ice_simplified.py         # Main interface (Week 4: ICEQueryProcessor enabled)
│   │   │   ├── ice_core.py               # Direct LightRAG wrapper (374 lines)
│   │   │   ├── data_ingestion.py         # Data sources with 6-category control (Email + News + Financial + Market + SEC + Research)
│   │   │   ├── query_engine.py           # Portfolio analysis (Week 4: Uses ICEQueryProcessor via delegation)
│   │   │   ├── config.py                 # Basic environment config
│   │   │   ├── test_secure_config.py     # ✅ Week 3: SecureConfig validation suite (145 lines)
│   │   │   ├── rotate_credentials.py     # ✅ Week 3: Credential rotation utility (236 lines)
│   │   │   ├── test_week4.py             # ✅ Week 4: Query enhancement validation (240 lines)
│   │   │   ├── test_integration.py       # ✅ Week 6: Integration test suite - 5 tests (251 lines)
│   │   │   ├── test_pivf_queries.py      # ✅ Week 6: PIVF golden query validation - 20 queries (424 lines)
│   │   │   └── benchmark_performance.py  # ✅ Week 6: Performance benchmarking - 4 metrics (418 lines)
│   │   ├── tests/                        # Comprehensive testing
│   │   │   ├── test_architecture_structure.py  # Structure validation
│   │   │   └── test_simplified_architecture.py # Functional tests
│   │   ├── documentation/                # Technical documentation
│   │   │   ├── ICE_MIGRATION_GUIDE.md   # Migration from complex to simplified
│   │   │   └── ICE_SIMPLIFIED_ARCHITECTURE_SUMMARY.md
│   │   ├── business/                     # Business documentation
│   │   │   ├── ICE_SIMPLIFIED_TECHNICAL_DESIGN.md
│   │   │   └── ICE_BUSINESS_USE_CASES.md
│   │   └── INTEGRATION_EVALUATION.md    # Integration analysis & recommendations
│
├── 🧠 Core AI Engine (ice_lightrag/)
│   ├── ice_rag.py                         # Core ICELightRAG wrapper class
│   ├── ice_rag_fixed.py                   # ✅ Week 3: JupyterSyncWrapper with SecureConfig integration
│   ├── model_provider.py                  # 🆕 Model provider factory (OpenAI/Ollama/Hybrid selection)
│   ├── 🏷️ Graph Analysis & Categorization # Pattern-based entity/relationship classification
│   │   ├── entity_categories.py           # Entity categorization patterns (9 categories)
│   │   ├── relationship_categories.py     # Relationship categorization patterns (10 categories)
│   │   └── graph_categorization.py        # Helper functions for graph analysis
│   ├── streamlit_integration.py           # Streamlit UI components for RAG
│   ├── setup.py                           # Automated dependency installer
│   ├── test_basic.py                      # Basic functionality tests (includes provider tests)
│   ├── earnings_fetcher.py                # Yahoo Finance earnings data fetcher
│   ├── quick_test.py                      # Quick LightRAG testing utility
│   └── storage/                           # LightRAG knowledge graph storage
│       ├── entities_vdb/                  # Entity vector database
│       ├── relationships_vdb/             # Relationship vector database
│       └── chunks_vdb/                    # Document chunk vector database
│
├── 📊 Data Infrastructure (Production Modules - WEEK 1-3 INTEGRATED)
│   ├── ice_data_ingestion/                # 🏭 PRODUCTION DATA FRAMEWORK (17,256 lines, 38 files)
│   │   ├── 🔐 Security & Configuration    # ✅ Week 3: Integrated into ice_simplified.py
│   │   │   ├── secure_config.py            # ✅ Week 3: Encrypted API key management (AES-256, rotation, audit)
│   │   │   ├── robust_client.py            # ✅ Week 1: HTTP client with retry/circuit breaker
│   │   │   └── config.py                   # Base configuration management
│   │   ├── 🧪 Testing & Validation        # Production-grade validation
│   │   │   ├── test_scenarios.py           # 🆕 Comprehensive test scenarios (5 suites)
│   │   │   ├── data_validator.py           # 🆕 Multi-level data validation framework
│   │   │   ├── test_data_pipeline.py       # Pipeline integration tests
│   │   │   └── tests/                      # Unit tests directory
│   │   ├── 📡 Data Connectors             # 7+ API integrations + MCP + SEC EDGAR
│   │   │   ├── bloomberg_connector.py      # Bloomberg API integration
│   │   │   ├── exa_mcp_connector.py       # Exa search MCP integration
│   │   │   ├── financial_news_connectors.py # Multi-source news aggregation
│   │   │   ├── sec_edgar_connector.py      # SEC filing data connector (to be added to simplified)
│   │   │   ├── polygon_connector.py        # Polygon.io market data
│   │   │   └── mcp_client_manager.py       # MCP client orchestration
│   │
│   ├── data/                              # Data storage and samples
│   │   ├── sample_data.py                # Sample financial data for development
│   │   ├── data_loader.py                # Data loading utilities
│   │   ├── emails_samples/               # Sample financial emails
│   │   ├── user_profiles/               # User portfolios and preferences
│   │   ├── portfolio_holdings.xlsx       # Sample portfolio data (original)
│   │   ├── portfolio_holdings.csv        # Sample portfolio data (CSV format)
│   │   └── portfolio_holdings_folder/    # 🆕 Test portfolio datasets (11 diverse portfolios)
│   │       ├── portfolio_holdings_1_tech_growth.csv           # Tech growth stocks (10 stocks)
│   │       ├── portfolio_holdings_2_dividend_blue_chip.csv    # Dividend aristocrats (15 stocks)
│   │       ├── portfolio_holdings_3_small_cap_growth.csv      # Small cap growth (15 stocks)
│   │       ├── portfolio_holdings_4_balanced_diversified.csv  # Balanced mix (15 stocks)
│   │       ├── portfolio_holdings_5_energy_materials.csv      # Energy & materials (14 stocks)
│   │       ├── portfolio_holdings_6_healthcare_biotech.csv    # Healthcare & biotech (15 stocks)
│   │       ├── portfolio_holdings_7_financial_services.csv    # Financial services (15 stocks)
│   │       ├── portfolio_holdings_8_consumer_discretionary.csv # Consumer discretionary (15 stocks)
│   │       ├── portfolio_holdings_9_ai_semiconductor.csv      # AI & semiconductor (15 stocks)
│   │       ├── portfolio_holdings_10_defensive_value.csv      # Defensive value (15 stocks)
│   │       └── portfolio_holdings_diversified_10.csv          # Multi-sector diversified (10 stocks, 4 sectors)
│   │
│   │   **Testing Use Cases**: These 11 diverse portfolios enable comprehensive validation
│   │   - Sector concentration analysis (single vs multi-sector)
│   │   - Risk profile validation (growth vs defensive vs balanced)
│   │   - Portfolio size impact (10 vs 15 stocks)
│   │   - Investment strategy assessment
│   │   - Multi-hop reasoning (e.g., "How does China risk impact AI semiconductor portfolio?")
│   │
│   └── storage/                          # Organized storage systems
│       ├── cache/                        # Centralized cache for all APIs
│       │   ├── alpha_vantage_cache/      # Alpha Vantage API cache
│       │   ├── news_cache/               # News API cache
│       │   ├── test_cache/               # Test data cache
│       │   └── processed_documents.json # Document processing cache
│       ├── document_storage/             # Document processing storage
│       ├── notebook_storage/             # Notebook execution storage
│       ├── test_storage/                 # Consolidated test data storage
│       │   └── main/                     # Main test LightRAG data and artifacts
│       └── unified_storage/              # Unified RAG storage
│
├── 🧪 Testing & Quality Assurance
│   ├── tests/                            # Comprehensive test suite
│   │   ├── test_runner.py               # Main test execution runner
│   │   ├── test_lightrag.py             # LightRAG integration tests
│   │   ├── test_unified_rag.py          # Unified RAG system tests
│   │   ├── test_imap_email_pipeline_comprehensive.py  # 🆕 IMAP pipeline comprehensive test (496 lines, 21 tests)
│   │   ├── test_temporal_features_comprehensive.py    # ✅ Week 6: Temporal architecture tests (450+ lines, 30+ tests)
│   │   ├── ice_data_tests/              # Data ingestion tests
│   │   ├── ice_lightrag_tests/          # Core AI engine tests
│   │   └── mock_data/                   # Test data fixtures
│   │
│   └── check/                           # System health checks and validation
│       └── health_checks.py             # Production health monitoring
│
├── 🔧 Development Tools & Scripts
│   ├── scripts/                         # Organized utility scripts
│   │   ├── fixes/                       # Notebook and system fix scripts
│   │   ├── utilities/                   # General development utilities
│   │   └── deployment/                  # Deployment and production scripts
│   │
│   ├── setup/                           # Environment and configuration setup
│   │   ├── local_llm_setup.py          # Ollama LLM integration setup
│   │   ├── local_llm_adapter.py        # Local LLM adapter implementation
│   │   └── setup_ice_api_keys.py       # API key configuration utility
│   │
│   └── dev_experiments/                 # Experimental development code
│       ├── ice_lazyrag/                 # LazyRAG experimental implementation
│       ├── lightrag/                    # LightRAG experiments and tests
│       └── python_notebook/             # Python notebook experiments
│
├── 📋 Documentation & Planning
│   ├── project_information/development_plans/
│   │   ├── notebook_designs/            # 🆕 Notebook design specifications
│   │   │   ├── ice_building_workflow_design.md    # Building workflow design spec
│   │   │   ├── ice_query_workflow_design.md       # Query workflow design spec
│   │   │   └── dual_notebooks_designs_to_do.md    # Dual notebook evaluation checklist
│   │   └── ICE_DEVELOPMENT_PLANS/       # Development roadmaps
│   └── md_files/                        # Organized project documentation
│       ├── CHANGELOG.md                 # Version milestones & releases (see also: PROJECT_CHANGELOG.md at root)
│       ├── LIGHTRAG_SETUP.md           # ⭐ Complete LightRAG configuration guide
│       ├── LOCAL_LLM_GUIDE.md          # ⭐ Ollama setup and cost optimization
│       ├── OLLAMA_TEST_RESULTS.md      # 🆕 Comprehensive Ollama integration test results (hybrid mode validated)
│       ├── QUERY_PATTERNS.md           # ⭐ Query strategies and optimization
│       ├── plans/                       # Development plans and roadmaps
│       │   └── ICE_DEVELOPMENT_PLAN.md  # ⭐ MAIN 75-TASK ROADMAP
│       ├── specifications/              # Technical specifications
│       │   ├── data_pipeline_architecture.md
│       │   ├── data_sources_specification.md
│       │   └── ice_notebook_architecture.md
│       └── analysis/                    # Analysis reports and findings
│           ├── ICE_NOTEBOOK_FIX_REPORT.md
│           └── about_LightRAG.md
│
├── 🎨 User Interface (SHELVED until 90% AI completion)
│   └── ui_mockups/                      # Streamlit application iterations
│       ├── ice_ui_v17.py               # Latest/main Streamlit application
│       └── ice_ui_v1.py-v16.py         # Previous development iterations
│
├── 🏗️ Infrastructure & Integration (Production Modules - WEEK 2-4 INTEGRATED)
│   ├── src/ice_core/                    # 🏭 PRODUCTION ORCHESTRATION (4,505 lines, 11 files)
│   │   ├── ice_unified_rag.py           # Unified RAG engine implementation
│   │   ├── ice_error_handling.py        # Error handling utilities
│   │   ├── ice_system_manager.py        # ✅ Week 2: System orchestration (used by ice_simplified.py)
│   │   ├── ice_query_processor.py       # ✅ Week 4: Enhanced query processing with fallback logic (enabled via use_graph_context=True)
│   │   ├── ice_graph_builder.py         # Graph construction utilities
│   │   ├── ice_data_manager.py          # Data management coordination
│   │   ├── temporal_analyzer.py         # ✅ Week 6: Trend detection and temporal analysis (350 lines)
│   │   ├── period_utils.py              # ✅ Week 6: Period arithmetic utilities (200 lines)
│   │   ├── temporal_enhancer.py         # Temporal enhancement utilities
│   │   ├── enhanced_entity_adapter.py   # Entity extraction adapter
│   │   └── enhanced_entity_extractor.py # Enhanced entity extraction
│   │
│   ├── src/ice_docling/                 # 🏭 DOCLING INTEGRATION (568 lines, 4 files)
│   │   │                                # Switchable architecture: Toggle via config.py
│   │   ├── __init__.py                  # Package initialization
│   │   ├── sec_filing_processor.py      # SEC filing content extraction (280 lines)
│   │   │                                # EXTENSION pattern: 0% → 97.9% table extraction
│   │   ├── docling_processor.py         # Email attachment processing (150 lines)
│   │   │                                # REPLACEMENT pattern: 42% → 97.9% table accuracy
│   │   └── scripts/download_docling_models.py  # Model pre-loader (106 lines)
│   │   └── Documentation:
│   │       ├── md_files/DOCLING_INTEGRATION_TESTING.md      # Testing guide (267 lines)
│   │       ├── md_files/DOCLING_INTEGRATION_ARCHITECTURE.md # Architecture (241 lines)
│   │       └── md_files/DOCLING_FUTURE_INTEGRATIONS.md      # Future features (190 lines)
│   │
│   ├── mcp_servers/                     # MCP server integrations
│   │   ├── financial-datasets-mcp/      # Financial data MCP server
│   │   └── yahoo-finance-mcp/           # Yahoo Finance MCP server
│   │
│   ├── imap_email_ingestion_pipeline/   # 🏭 PRODUCTION EMAIL PIPELINE (12,810 lines, 31 files)
│   │   │                                # CORE DATA SOURCE (to be integrated with simplified)
│   │   ├── Core Modules:
│   │   │   ├── email_connector.py           # Email data source connector
│   │   │   ├── entity_extractor.py          # High-precision entity extraction (668 lines)
│   │   │   ├── graph_builder.py             # Graph relationship construction (680 lines)
│   │   │   ├── ice_integrator.py            # IMAP pipeline coordinator (587 lines)
│   │   │   ├── enhanced_doc_creator.py      # Inline metadata markup (355 lines)
│   │   │   ├── contextual_signal_extractor.py # BUY/SELL/HOLD signal extraction
│   │   │   ├── intelligent_link_processor.py # PDF downloads from emails
│   │   │   └── attachment_processor.py      # OCR and document processing
│   │   └── Validation Notebooks:
│   │       ├── investment_email_extractor_simple.ipynb  # 📧 PRIMARY DEMO (25 cells)
│   │       │                                # Entity extraction, BUY/SELL signals, enhanced documents
│   │       │                                # Referenced by ice_building_workflow.ipynb Cells 21-22
│   │       ├── pipeline_demo_notebook.ipynb # Full pipeline integration demo
│   │       ├── imap_mailbox_connector_python.ipynb # IMAP connection testing
│   │       └── read_msg_files_python.ipynb  # .msg file parsing utilities
│   ├── project_information/             # Project documentation consolidation
│   │   ├── about_lightrag/             # 🆕 LightRAG focused documentation
│   │   │   ├── LightRAG_notes.md       # Technical implementation notes
│   │   │   ├── lightrag_building_workflow.md  # Document ingestion pipeline guide
│   │   │   └── lightrag_query_workflow.md     # Query processing pipeline guide
│   │   ├── about_graphrag/             # 🆕 GraphRAG focused documentation
│   │   │   └── GraphRAG_notes.md       # Comprehensive GraphRAG research and analysis notes
│   │   ├── about_news_apis/            # 🆕 News API integration documentation (100% complete)
│   │   │   ├── README.md               # Overview and quick reference (313 lines)
│   │   │   ├── DOCUMENTATION_STATUS.md # Status tracker and index (213 lines)
│   │   │   ├── IMPLEMENTATION.md       # Technical deep-dive with ASCII diagrams (602 lines)
│   │   │   ├── INTEGRATION.md          # ICE system integration with visual flows (491 lines)
│   │   │   └── apis/                   # Individual API documentation (5 files, 2,122 lines)
│   │   │       ├── finnhub.md         # Priority #1: Real-time, 60 req/min free (336 lines)
│   │   │       ├── newsapi.md         # Priority #4: 24hr delay warning (413 lines)
│   │   │       ├── marketaux.md       # Unlimited free, NLP features (454 lines)
│   │   │       ├── benzinga.md        # Premium quality (434 lines)
│   │   │       └── exa.md             # On-demand semantic search (485 lines)
│   │   ├── proposals/                   # Capstone proposals and variations
│   │   ├── research_papers/            # Academic research and analysis
│   │   ├── development_plans/          # Development planning documents (moved from root)
│   │   │   ├── ICE_DEVELOPMENT_PLANS/  # Detailed implementation strategies
│   │   │   └── Development Brainstorm Plans (md files)/  # Strategy brainstorms
│   │   ├── user_research/               # 🆕 User research and persona documentation
│   │   │   └── ICE_USER_PERSONAS_DETAILED.md  # Complete user persona profiles
│   │   ├── other_resources/            # Other supporting resources and documentation
│   │   ├── Critical Analysis of the ICE AI System Proposal.docx
│   │   └── README.md                  # Project information overview
│   └── logs/                           # Application and system logs
│
├── 🗂️ Archive & Legacy
│   ├── archive/                         # Organized archived files
│   │   ├── strategic_analysis/          # 🆕 Architecture decision history (5-option analysis)
│   │   │   ├── README.md               # 🆕 Quick reference: All 5 architectural options compared
│   │   │   ├── ICE_ARCHITECTURE_STRATEGIC_ANALYSIS.md  # 🆕 Complete 5-option comparison & decision framework
│   │   │   ├── MODIFIED_OPTION_4_ANALYSIS.md  # 🆕 Deep analysis: Why Option 4 rejected, UDMA philosophy
│   │   │   ├── ARCHITECTURE_INTEGRATION_PLAN.md  # 🆕 Original 6-week roadmap (superseded by UDMA)
│   │   │   ├── implementation_qa_20250106.md     # 🆕 ARCHIVED: Implementation Q&A questions (future-state design)
│   │   │   └── implementation_qa_answers_v2_20250106.md  # 🆕 ARCHIVED: Q&A with answers (500-stock production spec)
│   │   ├── backups/                    # Notebook and code backups
│   │   │   └── notebooks/              # Consolidated notebook backups
│   │   ├── deprecated_designs/          # 🆕 Deprecated design files with timestamps
│   │   │   └── ICE_MAIN_NOTEBOOK_DESIGN_V2_20250920.md  # Archived notebook design V2
│   │   ├── development/                # Archived development files
│   │   ├── ui_versions/                # Archived UI mockup versions (v1-v16)
│   │   ├── exports/                    # Data exports and reports
│   │   ├── legacy_projects/            # Previous project versions
│   │   ├── misc_files/                 # Miscellaneous archived files
│   │   ├── temp_files/                 # Temporary files archive
│   │   └── implementation_q&a_questions (V1).md  # Archived implementation questions document
│   │
│   └── notebook_outputs/               # Notebook execution outputs
│
├── 🧪 Development Sandbox & Testing
│   └── sandbox/                         # Development experiments and testing
│       └── python_notebook/             # Notebook testing environment
│           ├── ice_data_sources_demo_simple.ipynb  # ✅ Simple data source validation
│           ├── bloomberg_demo.ipynb             # Bloomberg API testing notebook
│           ├── test_v4_unified.py               # V4.0 unified notebook component tests
│           └── ice_data_ingestion_demo (backups)/ # Backup folder for old notebooks
│
├── ⚙️ Configuration & Environment
│   ├── .env                            # Environment variables (API keys)
│   ├── .gitignore                      # Git ignore patterns
│   ├── .claude/                        # Claude Code configuration
│   ├── storage/                        # Organized storage and cache systems
│   └── project_information/            # Project documentation (proposals, research, analysis)
│
└── 📦 External Dependencies
    ├── .git/                           # Git version control
    └── __pycache__/                    # Python bytecode cache
```

---

## 🎯 KEY FILE LOCATIONS FOR CLAUDE CODE

### **🆕 Simplified Architecture (Recommended)**
- **Main Interface**: `updated_architectures/implementation/ice_simplified.py` - Complete system in 677 lines
- **Configuration**: `updated_architectures/implementation/config.py` - Environment setup with validation
- **Data Ingestion**: `updated_architectures/implementation/data_ingestion.py` - 8 financial APIs
- **Query Engine**: `updated_architectures/implementation/query_engine.py` - Portfolio analysis workflows
- **Core Engine**: `updated_architectures/implementation/ice_core.py` - Direct LightRAG wrapper

### **Legacy Complex Architecture**
- **Main Interface**: `ice_main_notebook.ipynb` - Primary AI solution development
- **Core Engine**: `ice_lightrag/ice_rag.py` - LightRAG wrapper implementation
- **Demo Script**: `simple_demo.py` - Standalone testing and demonstration
- **Data Utilities**: `data/sample_data.py`, `data/data_loader.py` - Core data management

### **Critical Configuration**
- **Development Guide**: `CLAUDE.md` - Quick reference for Claude Code (293 lines, streamlined 2025-11-05)
- **Coding Patterns**: `CLAUDE_PATTERNS.md` - All 7 ICE patterns with examples (~400 lines)
- **Integration Guide**: `CLAUDE_INTEGRATIONS.md` - Docling & Crawl4AI details (~450 lines)
- **Troubleshooting**: `CLAUDE_TROUBLESHOOTING.md` - Complete debug reference (~350 lines)
- **Project Structure**: `PROJECT_STRUCTURE.md` - Complete directory organization
- **Architecture Plan**: `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` - 🆕 UDMA implementation guide (User-Directed Modular Architecture, aka Option 5)
- **Validation Framework**: `ICE_VALIDATION_FRAMEWORK.md` - 🆕 PIVF comprehensive testing framework (20 golden queries, 9-dimensional scoring)
- **Architecture History**: `archive/strategic_analysis/README.md` - 🆕 Quick reference for all 5 architectural options analyzed
- **Notebook Design**: `ICE_MAIN_NOTEBOOK_DESIGN_V2.md` - 🆕 Refined main notebook with LightRAG workflows
- **LightRAG Workflows**: `project_information/about_lightrag/lightrag_building_workflow.md` & `lightrag_query_workflow.md` - 🆕 Detailed pipeline guides
- **User Personas**: `project_information/user_research/ICE_USER_PERSONAS_DETAILED.md` - 🆕 Detailed user persona profiles for product planning
- **Project Roadmap**: `md_files/plans/ICE_DEVELOPMENT_PLAN.md` - 75-task development plan
- **LightRAG Setup**: `md_files/LIGHTRAG_SETUP.md` - Complete configuration guide
- **Local LLM Guide**: `md_files/LOCAL_LLM_GUIDE.md` - Ollama setup and cost optimization
- **Query Patterns**: `md_files/QUERY_PATTERNS.md` - Query strategies and optimization
- **API Setup**: `setup/setup_ice_api_keys.py` - Environment configuration

### **Testing & Validation**
- **Data Sources Demo**: `sandbox/python_notebook/ice_data_sources_demo_simple.ipynb` - ✅ Simple data ingestion validation
- **Test Scenarios**: `ice_data_ingestion/test_scenarios.py` - 🆕 Comprehensive test scenario generator (5 suites)
- **Data Validation**: `ice_data_ingestion/data_validator.py` - 🆕 Multi-level validation framework
- **Secure Config**: `ice_data_ingestion/secure_config.py` - 🆕 Encrypted API key management
- **Robust Client**: `ice_data_ingestion/robust_client.py` - 🆕 HTTP client with retry/circuit breaker
- **Test Runner**: `tests/test_runner.py` - Comprehensive test execution
- **Dual Notebook Integration Tests**: `tests/test_dual_notebook_integration.py` - 🆕 Complete workflow validation
- **Basic Tests**: `ice_lightrag/test_basic.py` - Core functionality validation
- **Health Checks**: `check/health_checks.py` - System monitoring
- **Integration Tests**: `tests/test_integration.py` - 🆕 Week 6: 5 integration tests (251 lines) ✅ ALL PASSING
- **PIVF Validation**: `tests/test_pivf_queries.py` - 🆕 Week 6: 20 golden queries with 9-dimensional scoring (424 lines)
- **Performance Benchmarks**: `tests/benchmark_performance.py` - 🆕 Week 6: 4 performance metrics (418 lines)
- **IMAP Pipeline Tests**: `tests/test_imap_email_pipeline_comprehensive.py` - 🆕 Entry #59: Comprehensive IMAP email pipeline test (496 lines, 21 tests) ✅ ALL PASSING
- **Entity Extraction Tests**: `tests/test_entity_extraction.py` - 🆕 Phase 2.6.1: EntityExtractor integration validation (182 lines)
- **Quick Entity Test**: `tests/quick_entity_test.py` - 🆕 Phase 2.6.1: Fast validation script (42 lines)
- **API Switches Unit Tests**: `tests/test_api_source_switches.py` - 🆕 Entry #127: Granular API switches validation (16 tests covering precedence, caching, early exit) ✅ ALL PASSING
- **API Switches Integration Tests**: `tests/test_api_switches_integration.py` - 🆕 Entry #127: Config flow validation (6 tests for multi-ticker scenarios) ✅ ALL PASSING
- **API Switches E2E Tests**: `tests/test_sec_only_config.py` - 🆕 Entry #127: End-to-end validation (2 tests for SEC-only and master switch) ✅ ALL PASSING
- **Relationship Extraction Tests**: `tests/test_relationship_extraction.py` - 🆕 Refinement #3: Universal cross-company relationship extraction (15 tests, 14/15 passing)
- **Event Extraction Tests**: `tests/test_option1_integration.py` - 🆕 Entry #149: EventExtractor integration & webhook delivery (10 tests) ✅ ALL PASSING (100%)
- **Relationship Production Tests**: `tests/test_relationship_production.py` - 🆕 Entry #150: RelationshipExtractor production validation (10 tests) ✅ ALL PASSING (100%)

### **Data & Storage**
- **Document Storage**: `data/attachments/` - **SINGLE SOURCE OF TRUTH** for all documents
  - **Architecture**: Unified hierarchical storage for email attachments and URL PDFs
  - **Pattern**: `data/attachments/{email_uid}/{file_hash}/`
    - `original/{filename}` - Original file (PDF, Excel, images, etc.)
    - `extracted.txt` - Extracted text content
    - `metadata.json` - Source tracking and processing metadata
  - **Source Types**: Distinguished by `metadata.json` field
    - `source_type: "email_attachment"` - Written by AttachmentProcessor
    - `source_type: "url_pdf"` - Written by IntelligentLinkProcessor
  - **Processing**: AttachmentProcessor (email attachments) + IntelligentLinkProcessor (URL PDFs)
  - **Extraction**: Docling (97.9% table accuracy) or PyPDF2/pdfplumber (42% accuracy)
  - **Size**: ~686 files (212 documents × ~3 files each)
- **LightRAG Storage**: `ice_lightrag/storage/` - Knowledge graph persistence
  - **Architecture**: 2 storage types (Vector + Graph), 4 components
  - **Vector Stores** (3): `chunks_vdb`, `entities_vdb`, `relationships_vdb` (NanoVectorDBStorage)
  - **Graph Store** (1): `graph_chunk_entity_relation.graphml` (NetworkXStorage)
  - **Purpose**: Dual-level retrieval (entities + relationships) for LightRAG queries
  - **Production Path**: Upgrade to QdrantVectorDBStorage + Neo4JStorage for scale
- **Cache Storage**: `storage/cache/` - Centralized cache for all data ingestion APIs
- **Test Data**: `storage/test_storage/main/` - Consolidated test LightRAG data and fixtures

---

## 🔄 INTEGRATION STATUS & DATA FLOW

### **Current Architecture Strategy (January 2025)**
**Architecture**: User-Directed Modular Architecture (UDMA) - Option 5 from strategic analysis
**Philosophy**: Simple Orchestration + Production Modules = Best of Both Worlds

**Implementation Plan** (see ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md):
- ✅ **Keep**: Simple, understandable orchestration (`ice_simplified.py` - 879 lines)
- ✅ **Use**: Production-ready modules (34K+ lines of robust code)
- ✅ **Integrate**: All data sources → LightRAG → Query Processing
- ✅ **Control**: User-directed enhancement (manual testing decides integration)

**For decision history**: See `archive/strategic_analysis/README.md` for all 5 options analyzed

### **Data Flow (Integrated Architecture)**
```
┌─────────────────────────────────────────────────────────┐
│  ICE Simplified (Simple Orchestrator)                   │
│  └── Uses: ICESystemManager, DataIngester (integrated)  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Data Sources (All feed into LightRAG)                  │
│  ├── 1. API/MCP (ice_data_ingestion/)                  │
│  │    ├── NewsAPI, Finnhub, Alpha Vantage, FMP        │
│  │    ├── MCP infrastructure                           │
│  │    └── SEC EDGAR connector                          │
│  ├── 2. Email (imap_email_ingestion_pipeline/)        │
│  │    ├── Broker research emails                      │
│  │    ├── Analyst reports (PDF downloads)             │
│  │    └── Signal extraction (BUY/SELL/HOLD)           │
│  └── 3. All use robust_client (circuit breaker)       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  LightRAG Knowledge Graph                               │
│  ├── JupyterSyncWrapper (src/ice_lightrag/)           │
│  └── Vector + Graph storage                            │
└─────────────────────────────────────────────────────────┘
```

### **Integration Phases** (6-week roadmap)
1. ✅ **Week 1 COMPLETE**: Data Ingestion Integration (robust_client, email + SEC sources)
2. ✅ **Week 2 COMPLETE**: Core Orchestration (ICESystemManager with health monitoring)
3. ✅ **Week 3 COMPLETE**: Configuration & Security (SecureConfig with AES-256 encryption)
4. ✅ **Week 4 COMPLETE**: Query Enhancement (ICEQueryProcessor with mix→hybrid→local fallback)
5. ⏳ **Week 5 NEXT**: Workflow Notebook Updates (demonstrate integrated features)
6. **Week 6**: Testing & Validation (end-to-end integration tests)

---

## 🗂️ ORGANIZATION PRINCIPLES

### **Post-Reorganization Structure (September 2024)**
This structure reflects the major reorganization completed to improve navigation and maintainability:

1. **Root Level**: Core project files and primary development interface
2. **Functional Grouping**: Related files organized into logical directories
3. **Archive Separation**: Legacy and backup files moved to `archive/`
4. **Documentation Centralization**: All docs organized under `md_files/`
5. **Script Organization**: Utilities categorized by purpose in `scripts/`
6. **Storage Consolidation**: All storage systems organized under `storage/`
7. **Integration Strategy**: Simple orchestration using production modules (not code duplication)

### **Navigation Guidelines**
- **Start Here**: `README.md` for project overview
- **Development Work**: `CLAUDE.md` for detailed development guidance
- **Task Planning**: `md_files/plans/ICE_DEVELOPMENT_PLAN.md` for roadmap
- **Code Development**: `ice_main_notebook.ipynb` for AI solution work
- **Testing**: `tests/test_runner.py` for validation
- **Configuration**: `setup/` directory for environment setup

### **Maintenance Notes**
- **UI Development**: Deferred to Phase 5 (post-90% AI completion)
- **Archive Policy**: Old files moved to `archive/` with organized subdirectories
- **Test Organization**: Comprehensive test suite with multiple execution modes
- **Storage Management**: Centralized storage systems with clear separation

---

## 📊 DEVELOPMENT PHASE MAPPING

### **Current Focus Areas (Phase 2)**
- `ice_main_notebook.ipynb` - Primary development interface
- `ice_lightrag/` - Core AI engine optimization
- `setup/local_llm_setup.py` - Cost optimization deployment
- `tests/` - System validation and testing

### **Ready for Activation**
- `ice_data_ingestion/` - 15+ API clients for real data
- `check/health_checks.py` - Production monitoring
- `mcp_servers/` - Financial data integration
- `ice_data_ingestion/bloomberg_api_pipeline_kiv_to_integrate/` - Professional data feeds (KIV)

### **Future Development**
- `ui_mockups/ice_ui_v17.py` - User interface (Phase 5)
- `dev_experiments/` - Advanced feature research

---

**Last Updated**: January 2025 (Enhanced Data Ingestion Framework v2.0)
**Recent Updates**: Added robust testing framework, secure API management, comprehensive validation
**Maintenance**: Update this file when major structural changes occur
**Reference**: Cross-check with `README.md` and `CLAUDE.md` for consistency