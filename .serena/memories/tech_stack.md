# ICE Technology Stack

## Core Technologies
- **Language**: Python 3.x
- **AI Engine**: LightRAG (knowledge graph + vector search)
- **Vector DB**: ChromaDB/Qdrant for semantic search
- **Graph Engine**: NetworkX for lightweight graph operations
- **Web Framework**: Streamlit for interactive interface
- **Visualization**: pyvis for interactive network displays

## Key Dependencies
- **Core AI**: 
  - `lightrag>=0.1.0` - Core knowledge graph engine
  - `openai>=1.0.0` - OpenAI API client
- **Data Processing**:
  - `pandas>=2.0.0` - Data manipulation
  - `numpy>=1.24.0` - Numerical computing
- **Web Interface**:
  - `streamlit>=1.28.0` - Interactive web apps
- **API Clients**: Multiple financial data connectors (Alpha Vantage, NewsAPI, etc.)

## Architecture Pattern
- **Modular Design**: Separate components for data ingestion, core engine, and query processing
- **MCP Compatibility**: JSON output format for tool interoperability
- **Local LLM Support**: Ollama integration for cost efficiency
- **Lazy Loading**: Build knowledge graph on-demand

## Development Environment
- **Platform**: Darwin (macOS)
- **Python**: 3.x with virtual environment recommended
- **IDE**: Jupyter notebooks for primary development interface