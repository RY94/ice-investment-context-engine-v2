# ICE Technology Stack (Updated: 2025-01-22)

## Core Technologies
- **Language**: Python 3.8+
- **AI Engine**: LightRAG (hybrid knowledge graph + vector search + full-text)
- **Vector DB**: ChromaDB/Qdrant for semantic search
- **Graph Engine**: NetworkX for lightweight graph operations
- **Web Framework**: Streamlit for interactive interface (shelved until Phase 5)
- **Visualization**: pyvis for interactive network displays
- **Data Format**: MCP-compatible JSON for tool interoperability

## Key Dependencies

### Core AI & LLM
- **`lightrag>=0.1.0`** - Core knowledge graph engine with entity extraction
- **`openai>=1.0.0`** - OpenAI API client (GPT-4 for production)
- **Local LLM Support**: Ollama integration (llama3.1:8b) for cost optimization ($0-7/month vs $50-200/month)

### Data Processing
- **`pandas>=2.0.0`** - Data manipulation and analysis
- **`numpy>=1.24.0`** - Numerical computing
- **`networkx>=3.0`** - Graph data structure and algorithms

### Web & Visualization
- **`streamlit>=1.28.0`** - Interactive web apps (shelved until Phase 5)
- **`pyvis>=0.3.0`** - Interactive network visualization

### Data Ingestion (34K+ lines production modules)
- **HTTP Client**: Custom `robust_client.py` with circuit breaker, retry logic, connection pooling
- **API Integrations**:
  - NewsAPI - Financial news aggregation
  - Alpha Vantage - Stock market data
  - Finnhub - Real-time market data
  - FMP (Financial Modeling Prep) - Financial statements
  - SEC EDGAR - Regulatory filings (async connector)
  - Bloomberg Terminal - Professional market data
  - Polygon.io - Market data and analytics

### Email Intelligence (12,810 lines production module)
- **Email Connector**: IMAP-based broker research ingestion
- **EntityExtractor**: High-precision ticker/rating/price target extraction
- **Enhanced Documents**: Inline metadata markup for LightRAG
- **PDF Processing**: Intelligent link processor + attachment OCR
- **Signal Extraction**: BUY/SELL/HOLD recommendation parsing

### Testing & Validation
- **`pytest>=7.0.0`** - Testing framework
- **Custom Test Suites**:
  - Dual notebook integration tests (10 tests, 100% pass rate)
  - Email graph integration tests (5 tests, Phase 1 validation)
  - Data source validation tests
  - LightRAG functionality tests

## Architecture Patterns

### Integrated Architecture (Current)
- **Simple Orchestration**: `ice_simplified.py` (self-contained orchestrator)
- **Production Modules**: Import from 34K+ lines of robust code
  - `ice_data_ingestion/` (17,256 lines) - API clients, robust framework
  - `imap_email_ingestion_pipeline/` (12,810 lines) - Email intelligence
  - `src/ice_core/` (3,955 lines) - System orchestration, query processing

### Design Principles
- **Modular Design**: Separate components for data ingestion, core engine, query processing
- **MCP Compatibility**: JSON output format for tool interoperability
- **Lazy Loading**: Build knowledge graph on-demand rather than pre-materializing
- **Evidence Grounding**: Every claim traces back to verifiable source documents
- **Source Attribution**: All edges timestamped and attributed to source documents
- **Confidence Scoring**: All extracted entities include confidence scores (0.0-1.0)

### Query Modes (6 LightRAG Modes)
1. **Local** - Document-focused retrieval
2. **Global** - Graph-based entity retrieval
3. **Hybrid** - Combined semantic + graph traversal
4. **Mix** - Adaptive mode selection
5. **Naive** - Simple vector search
6. **KG** - Pure knowledge graph traversal

## Data Flow Architecture

```
External Data Sources
├── API/MCP (ice_data_ingestion/)
│   ├── NewsAPI, Finnhub, Alpha Vantage, FMP
│   ├── SEC EDGAR (async connector)
│   └── Circuit breaker + retry logic
├── Email (imap_email_ingestion_pipeline/)
│   ├── 74 sample broker research emails
│   ├── Enhanced documents (inline metadata)
│   └── EntityExtractor enrichment
└── Robust Framework
    ├── Connection pooling
    └── Multi-level validation
         ↓
LightRAG Knowledge Graph (Single Unified Graph)
├── Vector storage (semantic search)
├── Graph storage (entity relationships)
└── Full-text storage (keyword search)
         ↓
Query Processing
├── 6 query modes (local, global, hybrid, mix, naive, kg)
├── Portfolio risk analysis
└── Investment intelligence generation
```

## Development Environment
- **Platform**: Darwin (macOS)
- **Python**: 3.8+ with virtual environment recommended
- **Primary Interface**: Jupyter notebooks (dual workflow approach)
  - `ice_building_workflow.ipynb` - Knowledge graph construction
  - `ice_query_workflow.ipynb` - Investment intelligence analysis
- **IDE Support**: VS Code, PyCharm, JupyterLab

## Cost Optimization
- **Cloud LLM**: GPT-4 via OpenAI API ($50-200/month baseline)
- **Local LLM**: Ollama llama3.1:8b ($0-7/month)
- **Hybrid Deployment**: Critical queries → GPT-4, routine → local LLM
- **Email Processing**: Deterministic extraction (no duplicate LLM calls)

## Security & Configuration
- **API Key Management**: SecureConfig with encrypted storage (Week 3 integration)
- **Environment Variables**: `.env` file support (never committed to git)
- **Secrets Protection**: `.gitignore` configured for sensitive files

## Performance Characteristics
- **Document Ingestion**: Batch processing with configurable sizes
- **Query Latency**: <2s for structured queries, <5s for complex multi-hop
- **Graph Size**: Optimized for single-user boutique fund (1K-10K entities)
- **Concurrent Users**: Single developer (not designed for multi-tenancy)