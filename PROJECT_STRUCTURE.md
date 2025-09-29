# ICE Project Structure Guide

> **🔗 LINKED DOCUMENTATION**: This is one of 5 essential core files that must stay synchronized. When updating this file, always cross-check and update the related files (if applicable): `CLAUDE.md`, `README.md`, `ICE_DEVELOPMENT_TODO.md`, and `PROJECT_CHANGELOG.md` to maintain consistency across project documentation.

**Location**: `/PROJECT_STRUCTURE.md`
**Purpose**: Comprehensive directory structure guide for Claude Code navigation and understanding
**Business Value**: Enables efficient AI-assisted development by providing clear project organization context
**Relevant Files**: `README.md`, `CLAUDE.md`, `docs/plans/ICE_DEVELOPMENT_PLAN.md`

---

> **🔄 SELF-MAINTAINING**: When adding/removing directories, moving files, or changing project organization, update the directory tree below and file location references throughout this document.

## 📁 CURRENT PROJECT STRUCTURE (Post-Organization)

```
ICE-Investment-Context-Engine/
├── 📄 Core Project Files
│   ├── README.md                           # Project overview & getting started guide
│   ├── CLAUDE.md                          # Claude Code development guidance & power user docs
│   ├── PROJECT_STRUCTURE.md               # This file - comprehensive directory guide
│   ├── PROJECT_CHANGELOG.md               # 🆕 Complete implementation changelog and task tracking
│   ├── dual_notebooks_designs_to_do.md    # 🆕 Dual notebook evaluation & integration checklist
│   ├── ice_building_workflow_design.md    # 🆕 Design specification for building workflow notebook
│   ├── ice_query_workflow_design.md       # 🆕 Design specification for query workflow notebook
│   ├── ice_building_workflow.ipynb        # 🆕 Knowledge graph building workflow notebook
│   ├── ice_query_workflow.ipynb           # 🆕 Investment intelligence analysis workflow notebook
│   ├── simple_demo.py                     # Standalone LightRAG demo script
│   ├── ice_main_notebook.ipynb            # ⭐ PRIMARY DEVELOPMENT INTERFACE (New simplified design)
│   └── ice_main_notebook_20250917.ipynb   # 📋 Original notebook (backed up)
│
├── 🆕 Simplified Architecture (Production Ready)
│   ├── updated_architectures/             # ⭐ NEW SIMPLIFIED SYSTEM (2,515 lines)
│   │   ├── README.md                      # Architecture overview & deployment guide
│   │   ├── implementation/                # Complete working system
│   │   │   ├── ice_simplified.py         # Main interface (677 lines)
│   │   │   ├── ice_core.py               # Direct LightRAG wrapper (374 lines)
│   │   │   ├── data_ingestion.py         # 8 API services (510 lines)
│   │   │   ├── query_engine.py           # Portfolio analysis (534 lines)
│   │   │   └── config.py                 # Environment config (420 lines)
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
│   ├── streamlit_integration.py           # Streamlit UI components for RAG
│   ├── setup.py                           # Automated dependency installer
│   ├── test_basic.py                      # Basic functionality tests
│   ├── earnings_fetcher.py                # Yahoo Finance earnings data fetcher
│   ├── quick_test.py                      # Quick LightRAG testing utility
│   └── storage/                           # LightRAG knowledge graph storage
│       ├── entities_vdb/                  # Entity vector database
│       ├── relationships_vdb/             # Relationship vector database
│       └── chunks_vdb/                    # Document chunk vector database
│
├── 📊 Data Infrastructure
│   ├── ice_data_ingestion/                # 15+ API clients for financial data
│   │   ├── 🔐 Security & Configuration
│   │   │   ├── secure_config.py            # 🆕 Encrypted API key management with rotation
│   │   │   ├── robust_client.py            # 🆕 HTTP client with retry/circuit breaker
│   │   │   └── config.py                   # Base configuration management
│   │   ├── 🧪 Testing & Validation
│   │   │   ├── test_scenarios.py           # 🆕 Comprehensive test scenarios (5 suites)
│   │   │   ├── data_validator.py           # 🆕 Multi-level data validation framework
│   │   │   ├── test_data_pipeline.py       # Pipeline integration tests
│   │   │   └── tests/                      # Unit tests directory
│   │   ├── 📡 Data Connectors
│   │   │   ├── bloomberg_connector.py      # Bloomberg API integration
│   │   │   ├── exa_mcp_connector.py       # Exa search MCP integration
│   │   │   ├── financial_news_connectors.py # Multi-source news aggregation
│   │   │   ├── sec_edgar_connector.py      # SEC filing data connector
│   │   │   ├── polygon_connector.py        # Polygon.io market data
│   │   │   └── mcp_client_manager.py       # MCP client orchestration
│   │
│   ├── data/                              # Data storage and samples
│   │   ├── sample_data.py                # Sample financial data for development
│   │   ├── data_loader.py                # Data loading utilities
│   │   ├── emails_samples/               # Sample financial emails
│   │   └── user_profiles/               # User portfolios and preferences
│   │   └── portfolio_holdings.xlsx       # Sample portfolio data
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
│   └── md_files/                        # Organized project documentation
│       ├── LIGHTRAG_SETUP.md           # ⭐ Complete LightRAG configuration guide
│       ├── LOCAL_LLM_GUIDE.md          # ⭐ Ollama setup and cost optimization
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
├── 🏗️ Infrastructure & Integration
│   ├── ice_core/                        # Core system management
│   │   ├── ice_unified_rag.py           # Unified RAG engine implementation
│   │   ├── ice_error_handling.py        # Error handling utilities
│   │   ├── ice_system_manager.py        # System orchestration
│   │   └── ice_data_manager.py          # Data management coordination
│   │
│   ├── mcp_servers/                     # MCP server integrations
│   │   ├── financial-datasets-mcp/      # Financial data MCP server
│   │   └── yahoo-finance-mcp/           # Yahoo Finance MCP server
│   │
│   ├── imap_email_ingestion_pipeline/   # Email processing and analysis
│   ├── project_information/             # Project documentation consolidation
│   │   ├── about_lightrag/             # 🆕 LightRAG focused documentation
│   │   │   ├── LightRAG_notes.md       # Technical implementation notes
│   │   │   ├── lightrag_building_workflow.md  # Document ingestion pipeline guide
│   │   │   └── lightrag_query_workflow.md     # Query processing pipeline guide
│   │   ├── about_graphrag/             # 🆕 GraphRAG focused documentation
│   │   │   └── GraphRAG_notes.md       # Comprehensive GraphRAG research and analysis notes
│   │   ├── proposals/                   # Capstone proposals and variations
│   │   ├── research_papers/            # Academic research and analysis
│   │   ├── development_plans/          # Development planning documents (moved from root)
│   │   │   ├── ICE_DEVELOPMENT_PLANS/  # Detailed implementation strategies
│   │   │   └── Development Brainstorm Plans (md files)/  # Strategy brainstorms
│   │   ├── Critical Analysis of the ICE AI System Proposal.docx
│   │   └── README.md                  # Project information overview
│   └── logs/                           # Application and system logs
│
├── 🗂️ Archive & Legacy
│   ├── archive/                         # Organized archived files
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
- **Development Guide**: `CLAUDE.md` - Essential Claude Code power user guide
- **Project Structure**: `PROJECT_STRUCTURE.md` - Complete directory organization
- **Notebook Design**: `ICE_MAIN_NOTEBOOK_DESIGN_V2.md` - 🆕 Refined main notebook with LightRAG workflows
- **LightRAG Workflows**: `project_information/about_lightrag/lightrag_building_workflow.md` & `lightrag_query_workflow.md` - 🆕 Detailed pipeline guides
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

### **Data & Storage**
- **LightRAG Storage**: `ice_lightrag/storage/` - Knowledge graph persistence
- **Cache Storage**: `storage/cache/` - Centralized cache for all data ingestion APIs
- **Test Data**: `storage/test_storage/main/` - Consolidated test LightRAG data and fixtures

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