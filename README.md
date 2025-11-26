# Investment Context Engine (ICE)

> **🔗 LINKED DOCUMENTATION**: This is one of 8 essential core files that must stay synchronized. When updating this file, always cross-check and update the related files: `ARCHITECTURE.md`, `CLAUDE.md`, `PROJECT_STRUCTURE.md`, `ICE_DEVELOPMENT_TODO.md`, `PROJECT_CHANGELOG.md`, `ICE_PRD.md`, and `PROGRESS.md` to maintain consistency across project documentation.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)

> **ICE** is a modular, lightweight AI system designed as the cognitive backbone for hedge fund core workflows—spanning idea generation, equity research, portfolio monitoring, risk management, and investor communications.

**DBA5102 Business Analytics Capstone Project**  
**Author**: Roy Yeo Fu Qiang (A0280541L)  
**Institution**: National University of Singapore

## 🚀 What is ICE?

ICE addresses critical pain points faced by lean boutique hedge funds through an AI-powered **Investment Knowledge Graph** that continuously learns and evolves:

### Core Problems Solved
- 📊 **Delayed Signal Capture**: Missing soft signals buried in transcripts, filings, or news flows
- 🔄 **Low Insight Reusability**: Investment theses remaining siloed in decks, chats, or emails  
- 🧩 **Inconsistent Decision Context**: Fragmented understanding leading to uncoordinated decisions
- ⏱️ **Manual Triage Bottlenecks**: Fully manual context stitching limiting speed and scale

### Key Value Propositions
- **Multi-hop Reasoning**: Connect dots across 1-3 relationship hops with universal cross-company relationship extraction
  - **7 relationship types**: RELATED_TO, HOLDS, EMPLOYED_BY, SUBSIDIARY, PARTNER, IMPACTS, MENTIONED_WITH
  - **Source confidence weighting**: SEC filings (1.0x), news (0.75x), email (0.70x) for reliability scoring
  - **Example**: "How does Taiwan tension on TSMC impact data center REITs?" → TSMC → NVDA → Hyperscalers → REITs
  - **Business value**: Uncover cascading risks that require dedicated research teams at larger funds
- **Graph-RAG Intelligence**: Hybrid retrieval combining semantic search, keyword search, and graph traversal
- **End-to-end Traceability**: Every fact and inference traces back to verifiable source documents
- **Temporal Intelligence**: Time-aware analysis separating when events happened from when they were ingested
  - **Recency-aware ranking**: Prioritize fresh signals with exponential decay weighting (30-day half-life)
  - **Event-driven queries**: Retrieve signals around specific dates (earnings, regulatory events)
  - **Temporal comparisons**: Year-over-year (YoY), quarter-over-quarter (QoQ), CAGR calculations
  - **Trend detection**: Statistical significance testing for metric evolution over time
  - **Prevents blind spots**: Late-filed SEC documents correctly tagged to original quarter, not ingestion date
  - **Business value**: Accurate portfolio risk assessment considering signal recency and relevance

## 🏗️ Architecture Overview

### 🆕 **Integrated Architecture (Simple Orchestration + Production Modules)**

**Current Version**: ICE 2.0 - Simple orchestrator using robust production modules
**Philosophy**: Keep simple, understandable orchestration while leveraging 34K+ lines of production-ready code

```
┌─────────────────────────────────────────┐
│     ICE Simplified (Orchestrator)       │
│           (ice_simplified.py)           │
│   Simple coordination - imports from:   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Production Data Sources            │
│  (All feed into LightRAG Knowledge Graph)│
│                                         │
│  1. API/MCP (ice_data_ingestion/)      │
│     ├── NewsAPI, Finnhub, Alpha Vantage│
│     ├── MCP infrastructure             │
│     ├── SEC EDGAR connector (+ docling)│
│     └── SEC Company Facts (XBRL metrics)│
│                                         │
│  2. Email (imap_email_ingestion/)      │
│     ├── Broker research emails         │
│     ├── Analyst reports (PDFs)         │
│     ├── BUY/SELL signal extraction     │
│     └── Docling processor (97.9% tables)│
│                                         │
│  3. Robust Framework                    │
│     ├── Circuit breaker + retry logic  │
│     ├── SecureConfig (Week 3: AES-256) │
│     └── Multi-level validation         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│     LightRAG Knowledge Graph            │
│   (Vector + Graph + Entity storage)     │
└─────────────────────────────────────────┘
```

**Architecture**: User-Directed Modular Architecture (UDMA) - Option 5 from strategic analysis

**Integration Benefits:**
- ✅ **Simple orchestration** - Easy to understand and maintain
- ✅ **Production modules** - Circuit breaker, retry, validation (34K+ lines)
- ✅ **3 data sources** - API/MCP + Email + SEC filings → unified graph
- ✅ **Robust features** - Health monitoring, graceful degradation, encrypted config
- ✅ **No code duplication** - Import from existing production modules
- ✅ **User control** - Manual testing decides what gets integrated (not automated thresholds)

**Implementation Guide**: See `ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md` (UDMA complete guide)
**Decision History**: See `archive/strategic_analysis/README.md` (all 5 options analyzed)
**Location**: `updated_architectures/implementation/`

**Docling Integration** (Switchable): Professional-grade document parsing for SEC filings (0% → 97.9% table extraction) and email attachments (42% → 97.9% accuracy). Toggle via `config.py` environment variables. See `md_files/DOCLING_INTEGRATION_TESTING.md` for usage.

**Crawl4AI Integration** (Switchable): Hybrid URL fetching with smart routing for email links. Simple HTTP (fast, free) for direct downloads. Browser automation for complex sites (premium portals, JS-heavy IR pages). Toggle via `USE_CRAWL4AI_LINKS` environment variable. See `md_files/CRAWL4AI_INTEGRATION_PLAN.md` for strategy.

**Documentation**:
- 📖 **LightRAG Building Workflow**: `project_information/about_lightrag/lightrag_building_workflow.md` - Complete document ingestion pipeline
- 📖 **LightRAG Query Workflow**: `project_information/about_lightrag/lightrag_query_workflow.md` - Query processing and retrieval strategies
- 📓 **Notebook Design**: `ICE_MAIN_NOTEBOOK_DESIGN_V2.md` - Refined main notebook with workflow integration

### Storage Architecture

**Single Source of Truth**: All documents stored in `data/attachments/` with unified hierarchical structure

```
data/attachments/
├── {email_uid}/                    # Email identifier for isolation
│   ├── {file_hash}/                # SHA-256 hash for deduplication
│   │   ├── original/               # Original files
│   │   │   └── {filename}          # PDF, Excel, images, etc.
│   │   ├── extracted.txt           # Extracted text content
│   │   └── metadata.json           # Source tracking & processing info
```

**Two Processing Flows**:
1. **AttachmentProcessor** - Email attachments (images, PDFs, Excel, Word, PowerPoint)
2. **IntelligentLinkProcessor** - URL PDFs from research links in emails

**Source Distinction**: `metadata.json` contains `source_type` field:
- `"email_attachment"` - File attached to email
- `"url_pdf"` - PDF downloaded from URL in email body

**Text Extraction**: Switchable between Docling (97.9% table accuracy) and PyPDF2/pdfplumber (42% accuracy)

**Current Size**: ~686 files (212 documents × ~3 files each)

### Core Technical Components

1. **🧠 Lazy Graph-RAG**: Dynamic subgraph retrieval using sparse, high-signal edge types
2. **🔍 Hybrid RAG Architecture**: Semantic vector search + keyword search + graph traversal + HyDE
3. **⚡ LightRAG Integration**: AI-powered document analysis and entity extraction
4. **📊 Streamlit Interface**: Interactive web interface for investment analysis
5. **🔗 MCP Compatibility**: JSON-formatted outputs for tool interoperability

## 🚀 Quick Start

> **🔄 SELF-MAINTAINING**: When changing installation procedures, environment setup, or dependencies, update the commands below and the Prerequisites section.

### **🆕 Simplified Architecture (Recommended)**

**Production-ready system with 83% code reduction:**

```bash
# 1. Set environment variables
export OPENAI_API_KEY="sk-your-openai-api-key"
export NEWSAPI_ORG_API_KEY="your-newsapi-key"  # Optional
export ALPHA_VANTAGE_API_KEY="your-alpha-key"  # Optional

# 2. Run the simplified system
cd updated_architectures/implementation

# Test configuration
python config.py

# Run basic demo
python ice_simplified.py
```

### **Enabling Crawl4AI for Advanced URL Fetching** ⚙️

**Purpose**: Browser automation for JavaScript-heavy sites and login-protected research portals

ICE uses a hybrid URL fetching strategy:
- **Simple HTTP** (default): Fast, free - works for direct downloads (PDFs, Excel) and token-authenticated URLs (DBS research)
- **Crawl4AI** (optional): Browser automation - handles complex sites (Goldman Sachs, Morgan Stanley portals, JS-heavy IR pages)

**Enable Crawl4AI**:
```bash
# Set environment variable before starting ICE
export USE_CRAWL4AI_LINKS=true

# Optional: Configure timeout and browser mode
export CRAWL4AI_TIMEOUT=60        # Default: 60 seconds
export CRAWL4AI_HEADLESS=true      # Default: true (no browser window)

# Run ICE with Crawl4AI enabled
cd updated_architectures/implementation
python ice_simplified.py

# Or in Jupyter notebooks (already enabled in Cell 1 as of 2025-11-04)
# Cell 1 includes: os.environ['USE_CRAWL4AI_LINKS'] = 'true'
jupyter notebook ice_building_workflow.ipynb
```

**Disable Crawl4AI** (revert to simple HTTP only):
```bash
export USE_CRAWL4AI_LINKS=false
python ice_simplified.py
```

**Verify Crawl4AI Status**:
- Check notebook Cell 27 output for "Using Crawl4AI for Tier X: [URL]" messages
- Check Cell 28 for Crawl4AI configuration status
- Look for browser automation activity in logs

**When to Enable**:
- Processing broker research portals (Goldman, Morgan Stanley, JP Morgan)
- Extracting from JavaScript-heavy investor relations pages (NVIDIA, AMD)
- Handling multi-step link chains (Email → Portal landing → Report download)
- Bypassing simple paywalls (Bloomberg, Reuters)

**Impact**: Enabling Crawl4AI improves URL download success rate from ~30-40% → ~60-80% for complex sites, capturing 70-90% more premium broker research content.

**See Also**: `md_files/CRAWL4AI_INTEGRATION_PLAN.md` for complete strategy and technical details.

**Example Python usage:**
```python
from ice_simplified import create_ice_system

# Create ICE system
ice = create_ice_system()

# Analyze portfolio
holdings = ['NVDA', 'TSMC', 'AMD']
analysis = ice.analyze_portfolio(holdings)
print(f"Analysis: {analysis['summary']['analysis_completion_rate']:.1f}% complete")
```

### **Graph Analysis & Categorization**

ICE includes pattern-based categorization for entities and relationships in the knowledge graph:

```python
from src.ice_lightrag.graph_categorization import categorize_entities, categorize_relationships

# Categorize entities (9 categories: Company, Financial Metric, Technology/Product, etc.)
entity_stats = categorize_entities(entities_data)
# Returns: {'Company': 15, 'Financial Metric': 45, ...}

# Categorize relationships (10 categories: Financial, Product/Tech, Corporate, etc.)
rel_stats = categorize_relationships(relationships_data)
# Returns: {'Financial': 40, 'Product/Tech': 25, ...}
```

**Two-Phase Pattern Matching** (Enhanced 2025-10-13, Critical Fixes Applied):
- **Phase 1**: Match against entity_name only (high precision, prevents content contamination)
- **Phase 2**: Match against entity_name + entity_content (broader context fallback, confidence reduced by 0.10)
- **Critical Fixes**: Added missing Technology/Product patterns (INTEL, CORE, ULTRA), enhanced LLM prompt with entity_content, fixed health check exact matching
- **Target Accuracy**: ~100% for financial entities (companies, metrics, tech) - validation pending
- **Previous Impact**: 70% error reduction from baseline (58% → ~15-20%) with two-phase approach alone

**Patterns Configuration**:
- `src/ice_lightrag/entity_categories.py` - Entity categorization patterns (9 categories)
- `src/ice_lightrag/relationship_categories.py` - Relationship categorization patterns (10 categories)
- `src/ice_lightrag/graph_categorization.py` - Categorization logic with two-phase matching

**📧 Production Entity Extraction** (Phase 2.6.1 Complete - 2025-10-15):
- ✅ **EntityExtractor Integration**: Email ingestion now uses production `EntityExtractor` (668 lines) from `imap_email_ingestion_pipeline/`
- ✅ **Enhanced Documents**: Inline markup format `[TICKER:NVDA|confidence:0.95]` improves LightRAG precision
- ✅ **Structured Data**: Class attributes (`last_extracted_entities`, `last_graph_data`) prepare for Phase 2.6.2 Signal Store
- ✅ **F1 Score Improvement**: Expected 0.733 → ≥0.85 (17% gain, production-grade extraction with confidence scoring)
- ✅ **UDMA Compliance**: Simple integration (~60 lines), imports production modules, zero code duplication, graceful fallback
- 📧 **Demo**: See `imap_email_ingestion_pipeline/investment_email_extractor_simple.ipynb` for 25-cell comprehensive demonstration

### **Legacy Complex Architecture**

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd capstone-project
   ```

2. **Set up environment**
   ```bash
   # Set your OpenAI API key
   export OPENAI_API_KEY="your-openai-api-key"
   
   # Install LightRAG dependencies
   cd src/ice_lightrag
   python setup.py

   # Create user data directory
   mkdir -p ../../user_data
   ```

3. **Test the setup**
   ```bash
   # Test basic functionality
   python test_basic.py

   # Test API connection
   cd ../..
   python test_api_key.py
   ```

4. **Launch the application**
   ```bash
   # Run the main Streamlit interface
   streamlit run UI/ice_ui_v17.py

   # Or run the simple demo
   python src/simple_demo.py
   ```

## ⚙️ Environment Variables

Control API data lookback periods to manage costs:

```bash
# News APIs (NewsAPI, Finnhub, Benzinga) - Default: 7 days
export ICE_NEWS_LOOKBACK_DAYS=7

# Financial APIs (Yahoo Finance, SEC Edgar) - Default: 90 days
export ICE_FINANCIAL_LOOKBACK_DAYS=90
```

**Cost Optimization**: Reduce lookback periods for significant API call savings:
- `ICE_NEWS_LOOKBACK_DAYS=3` → 57% reduction in news API calls
- `ICE_FINANCIAL_LOOKBACK_DAYS=30` → 66% reduction in financial API calls
- **Combined**: 60-70% total API call reduction

**Temperature Configuration** (optional):
```bash
# Entity extraction (default: 0.3, recommended: ≤0.2 for reproducibility)
export ICE_LLM_TEMPERATURE_ENTITY_EXTRACTION=0.3

# Query answering (default: 0.5, range: 0.0-1.0)
export ICE_LLM_TEMPERATURE_QUERY_ANSWERING=0.5
```

## 💡 Usage Examples

### Basic Query Interface
```python
from src.ice_lightrag.ice_rag import ICELightRAG

# Initialize ICE
ice_rag = ICELightRAG(working_dir="./src/ice_lightrag/storage")

# Ask investment questions
result = ice_rag.query(
    query="What companies are exposed to China risk?",
    mode="hybrid",  # Uses semantic + keyword + graph + HyDE
    max_hops=3,
    confidence_threshold=0.7
)

print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")
```

### Graph-RAG Query Patterns
```python
# 1-hop: Direct relationships
"Which suppliers does NVDA depend on?"

# 2-hop: Causal chains  
"How does China risk impact NVDA through TSMC?"

# 3-hop: Multi-step reasoning
"What portfolio names are exposed to AI regulation via chip suppliers?"
```

### Streamlit Integration
```python
import streamlit as st
from src.ice_lightrag.streamlit_integration import render_rag_interface

st.title("Investment Analysis Dashboard")

# Add AI analysis capabilities
with st.expander("🤖 AI Analysis", expanded=True):
    render_rag_interface()
```

## 📁 Project Structure

> **📁 COMPLETE STRUCTURE GUIDE**: See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for comprehensive directory organization and navigation

### **Key Directories (Organized Structure)**
```
ICE-Investment-Context-Engine/
├── 📄 Core Files                   # README.md, CLAUDE.md, main notebooks
├── 📁 src/                        # Core application code
│   ├── 🧠 ice_lightrag/           # LightRAG Integration Module (Core AI Engine)
│   ├── 🏗️ ice_core/              # Core system management and orchestration
│   └── 📄 simple_demo.py          # Standalone demo script
├── 📊 ice_data_ingestion/          # 15+ API clients for financial data
├── 📊 data/                       # Data utilities, samples, and portfolio data
├── 🧪 tests/                      # Comprehensive test suite with runner
├── 📁 sandbox/                    # Development experiments and prototypes
├── 📋 md_files/                   # Documentation (plans, specs, analysis)
├── ⚙️ setup/                      # Environment & configuration setup
├── 🎨 UI/                         # User interface components and mockups
├── 🗂️ archive/                    # Organized backups, exports, legacy files
└── 🏗️ Infrastructure/             # Core systems, MCP servers, email pipeline
```

### **Primary Development Files**
- **Dual Workflow Notebooks**: 🆕 `ice_building_workflow.ipynb` (knowledge graph construction) & `ice_query_workflow.ipynb` (investment analysis)
- **Main Interface**: `ice_main_notebook.ipynb` - Primary AI solution development
- **Core Engine**: `src/ice_lightrag/ice_rag.py` - LightRAG wrapper
- **Demo & Testing**: `src/simple_demo.py`, `tests/test_runner.py`
- **Enhanced Testing Framework**: `sandbox/python_notebook/ice_data_sources_demo_v2.ipynb` - 🆕 Production-grade validation
- **Week 6 Test Suite**: 🎉 **UDMA Integration Complete (6/6 weeks)**
  - `tests/test_integration.py` - 5 integration tests (251 lines) ✅ ALL PASSING
  - `tests/test_pivf_queries.py` - 20 golden queries with 9-dimensional scoring (424 lines)
  - `tests/benchmark_performance.py` - 4 performance metrics (418 lines)
  - `tests/test_imap_email_pipeline_comprehensive.py` - 21 comprehensive IMAP pipeline tests (496 lines) ✅ ALL PASSING
- **Development Guide**: `CLAUDE.md` - Claude Code instructions
- **Project Changelog**: `PROJECT_CHANGELOG.md` - 🆕 Complete implementation tracking

## 🎯 Current MVP Features

### Module 1: Ask ICE a Question
- Natural language investment queries
- Multi-hop reasoning with confidence scoring
- Source citations and evidence grounding
- Structured, explainable answers

### Module 2: Per-Ticker Intelligence Panel
- TL;DR summaries and alert priorities
- KPI drivers with causal reasoning chains
- Thematic exposures and soft signals
- "What Changed" tracker for evidence shifts

### Module 3: Mini Subgraph Viewer
- Interactive 1-3 hop relationship visualization
- Filters: hop depth, recency, edge type, confidence
- Intuitive network mapping of investment relationships

### Module 4: Daily Portfolio/Watchlist Briefs
- High-signal emerging risks and opportunities
- Material changes across portfolio holdings
- Automated briefing generation

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Core Language** | Python 3.8+ | Primary development language |
| **Web Framework** | Streamlit | Interactive web interface |
| **Graph Engine** | NetworkX | Lightweight graph operations |
| **Vector Database** | ChromaDB/Qdrant | Semantic search and embeddings |
| **LLM Integration** | OpenAI GPT-4 | Natural language processing |
| **Visualization** | pyvis | Interactive network displays |
| **Data Format** | MCP-compatible JSON | Tool interoperability |

## 🚧 Development Roadmap

### Phase 1: Basic RAG + Simple Graph ✅ (Current MVP)
- Core LightRAG integration
- Simple graph construction
- Basic Streamlit interface

### Phase 2: Hybrid Retrieval + Edge Expansion 🚧 (In Progress)
- Multi-strategy retrieval orchestration
- Graph-aware query processing
- Confidence scoring and source attribution

### Phase 3: Full Graph-RAG + Multi-hop Reasoning
- Advanced graph traversal algorithms
- Complex causal reasoning chains
- Temporal relationship tracking

### Phase 4: Advanced Features + Web Search Integration
- Real-time data integration
- Proactive alerts and monitoring
- Advanced portfolio optimization

### Phase 5: Production Scaling + Enterprise Features
- Performance optimization
- Enterprise security features
- API and webhook integrations

## 📊 Success Metrics

| Metric | Target | Current Status |
|--------|--------|----------------|
| **Query Response Time** | < 5 seconds for 3-hop reasoning | 🟨 In Development |
| **Answer Faithfulness** | >85% to source documents | 🟨 In Development |
| **Query Coverage** | >90% of analyst queries within 3 hops | 🟨 In Development |
| **Team Adoption** | 100% daily active usage | 🟨 MVP Testing |

## 🤝 Integration Opportunities

- **Bloomberg Terminal**: Data feed integration and API connectivity
- **Portfolio Management Systems**: Holdings and performance data sync
- **Research Management**: Integration with existing note-taking systems
- **Compliance Systems**: Audit trail and regulatory reporting
- **MCP Ecosystem**: Compatible with Model Context Protocol tools

## 📚 Documentation

### Core Development Guides
- **[ICE_PRD.md](ICE_PRD.md)**: 🆕 Product Requirements Document - Unified requirements specification for Claude Code instances (product vision, user personas, functional/non-functional requirements, success metrics)
- **[CLAUDE.md](CLAUDE.md)**: Essential guidance for Claude Code power users
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**: Complete directory organization and file navigation
- **[ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md](ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md)**: 🆕 UDMA implementation guide (User-Directed Modular Architecture, Option 5)
- **[ICE_DEVELOPMENT_PLAN_v3.md](ICE_DEVELOPMENT_PLAN_v3.md)**: Comprehensive activation-focused development roadmap
- **[ICE_VALIDATION_FRAMEWORK.md](ICE_VALIDATION_FRAMEWORK.md)**: 🆕 PIVF - Comprehensive validation framework (20 golden queries, 9-dimensional scoring)
- **[archive/strategic_analysis/README.md](archive/strategic_analysis/README.md)**: 🆕 Quick reference for all 5 architectural options analyzed

### Technical Setup Guides
- **[md_files/LIGHTRAG_SETUP.md](md_files/LIGHTRAG_SETUP.md)**: Complete LightRAG configuration and financial optimizations
- **[md_files/LOCAL_LLM_GUIDE.md](md_files/LOCAL_LLM_GUIDE.md)**: Ollama setup, hybrid configurations, and cost optimization
- **[md_files/QUERY_PATTERNS.md](md_files/QUERY_PATTERNS.md)**: Query mode selection and performance optimization

### Project Documentation
- **[project_information/development_plans/](project_information/development_plans/)**: Development planning documents and implementation strategies

## 🔍 Research Context

This project represents cutting-edge research in:
- **Graph-RAG architectures** for financial intelligence
- **Hybrid retrieval systems** combining multiple search strategies  
- **Temporal knowledge graphs** with investment domain expertise
- **AI-powered portfolio management** and risk assessment

**Academic Supervisor**: [To be specified]  
**Industry Partners**: [To be specified]  
**Publication Pipeline**: Research findings will be submitted to relevant AI/Finance conferences

## 🛟 Support & Troubleshooting

### Common Issues
- **API Key Error**: Ensure `OPENAI_API_KEY` is set in your environment
- **Import Errors**: Run `python ice_lightrag/setup.py` to install dependencies
- **Port Conflicts**: Use `streamlit run --server.port 8502 ui_mockups/ice_ui_v17.py`
- **Performance Issues**: Set `export NUMEXPR_MAX_THREADS=14` for CPU optimization

### Getting Help
1. Check the [CLAUDE.md](CLAUDE.md) for detailed development guidance
2. Review existing [issues and solutions](ice_lightrag/test_basic.py) in test files
3. Contact: Roy Yeo Fu Qiang (A0280541L) - [Contact details]
