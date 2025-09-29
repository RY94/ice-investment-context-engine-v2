# ICE Architecture Documentation

**Location**: `/docs/ARCHITECTURE.md`
**Purpose**: Comprehensive architectural overview of the Investment Context Engine
**Business Value**: Technical design reference for development and integration decisions
**Relevant Files**: `README.md`, `PROJECT_STRUCTURE.md`, `src/`, `docs/specifications/`

---

## 🏗️ System Architecture Overview

ICE (Investment Context Engine) is built as a modular, Graph-RAG based AI system designed for investment intelligence and portfolio analysis.

## 🧱 Core Components

### 📊 Data Layer
```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│   SEC Filings   │   Earnings      │   News & Research       │
│   • 10-K/10-Q   │   • Transcripts │   • Financial News      │
│   • 8-K Forms   │   • Guidance    │   • Analyst Reports     │
│   • Proxy       │   • Metrics     │   • Market Data         │
└─────────────────┴─────────────────┴─────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Data Ingestion Pipeline                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│  API Connectors │  MCP Integration│  Document Processing    │
│  • Bloomberg    │  • Yahoo Finance│  • PDF/HTML Parsing    │
│  • Exa Search   │  • News APIs    │  • Email Processing     │
│  • Custom APIs  │  • Real-time    │  • OCR & Extraction     │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 🧠 AI Processing Layer
```
┌─────────────────────────────────────────────────────────────┐
│                   LightRAG Core Engine                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Entity Extract  │ Relationship    │ Document Processing     │
│ • Companies     │ • Supply Chain  │ • Chunking Strategy     │
│ • People        │ • Ownership     │ • Semantic Analysis     │
│ • Locations     │ • Competition   │ • Sentiment Detection   │
│ • Events        │ • Correlation   │ • Topic Classification  │
└─────────────────┴─────────────────┴─────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Knowledge Graph Storage                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Entities      │  Relationships  │   Document Chunks       │
│   • Vector DB   │  • Graph Store  │   • Vector Embeddings   │
│   • Metadata    │  • Temporal     │   • Source Attribution  │
│   • Confidence  │  • Confidence   │   • Timestamp Tracking  │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 🔍 Query Processing Layer
```
┌─────────────────────────────────────────────────────────────┐
│                 Hybrid Query Engine                         │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Semantic Search │ Graph Traversal │ Keyword Matching       │
│ • Vector Sim    │ • 1-3 Hop       │ • Exact Terms          │
│ • Embeddings    │ • Path Finding  │ • Boolean Logic        │
│ • Similarity    │ • Relationship  │ • Fuzzy Matching       │
└─────────────────┴─────────────────┴─────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Query Mode Selection                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│     Naive       │     Local       │      Global             │
│ • Basic RAG     │ • Entity Focus  │ • Full Graph Scan      │
│ • Simple        │ • Local Context │ • Comprehensive         │
│                 │                 │                         │
├─────────────────┼─────────────────┼─────────────────────────┤
│     Hybrid      │    Naive+HT     │     Local+HT            │
│ • Multi-mode    │ • HyDE Enhanced │ • Enhanced Local        │
│ • Best of all   │ • Hypothetical  │ • Hypothesis + Local    │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 🎯 Application Layer

### 📓 Primary Interfaces
- **Jupyter Notebook**: `ice_main_notebook.ipynb` - Main development interface
- **Streamlit UI**: `UI/ice_ui_v17.py` - Interactive web dashboard
- **Demo Script**: `src/simple_demo.py` - Standalone testing

### 🔧 Core Modules (in `/src/`)
```
src/
├── ice_lightrag/          # LightRAG integration
│   ├── ice_rag.py         # Main wrapper class
│   ├── query_optimization.py
│   └── streamlit_integration.py
├── ice_core/              # System management
│   ├── ice_system_manager.py
│   ├── ice_unified_rag.py
│   └── ice_error_handling.py
└── simple_demo.py         # Standalone demo
```

## 🔄 Data Flow Architecture

```
User Query → Query Processor → Mode Selection → Graph Traversal
                                     ↓
Source Attribution ← Answer Assembly ← Context Retrieval ← Hybrid Search
                                     ↓
                          Response with Evidence Chain
```

## 🏛️ Design Principles

### 🎯 Core Principles
1. **Modularity**: Loosely coupled, highly cohesive components
2. **Traceability**: Every fact traces to verifiable source documents
3. **Scalability**: Designed for single developer maintainability
4. **Evidence-First**: All claims backed by source attribution
5. **Temporal Awareness**: Time-sensitive relationship tracking

### 🔐 Security Considerations
- API key management via environment variables
- No hardcoded credentials in codebase
- Secure document processing pipelines
- Data anonymization for sensitive information

### ⚡ Performance Considerations
- Lazy graph expansion for memory efficiency
- Caching strategies for frequently accessed data
- Async processing for I/O bound operations
- Local LLM support for cost optimization

## 🔌 Integration Points

### External Systems
- **Bloomberg Terminal**: Data feed integration
- **Portfolio Management**: Holdings sync
- **Research Platforms**: Note integration
- **MCP Ecosystem**: Tool interoperability

### Internal Interfaces
- **Python Package**: Clean `/src/` structure
- **REST APIs**: Future web service endpoints
- **Event Streaming**: Real-time data updates
- **Batch Processing**: Bulk document ingestion

---

## 🚀 Future Architecture Evolution

### Phase 3: Advanced Graph-RAG
- Multi-layer graph representations
- Advanced reasoning algorithms
- Temporal relationship modeling

### Phase 4: Real-time Intelligence
- Streaming data integration
- Live market monitoring
- Proactive alert systems

### Phase 5: Enterprise Scale
- Distributed processing
- Multi-tenant architecture
- Advanced security features

---

**Last Updated**: September 13, 2024
**Architecture Version**: 2.0
**Next Review**: End of Phase 2