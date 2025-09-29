# docs/LIGHTRAG_SETUP.md
# Complete LightRAG setup and configuration guide for ICE Investment Context Engine
# Provides detailed financial domain optimizations and query parameter configurations
# Relevant files: ice_lightrag/ice_rag.py, setup/local_llm_setup.py, simple_demo.py, CLAUDE.md

# LightRAG Setup & Configuration Guide

This guide provides comprehensive LightRAG setup and configuration options for the ICE Investment Context Engine, including financial domain optimizations and cost optimization strategies.

## 🔧 LightRAG Best Practices for Financial Applications

### Document Preparation for Optimal Entity Extraction

```python
# Financial document preprocessing
def prepare_financial_doc(text):
    """Optimize financial documents for LightRAG entity extraction"""
    # Expand common financial abbreviations
    abbreviations = {
        "P/E": "price to earnings ratio",
        "EPS": "earnings per share",
        "ROE": "return on equity",
        "EBITDA": "earnings before interest taxes depreciation amortization",
        "FCF": "free cash flow"
    }

    for abbr, full in abbreviations.items():
        text = text.replace(abbr, f"{abbr} ({full})")

    # Add section headers for better chunking
    text = add_document_structure(text)
    return text
```

## LightRAG Configuration Options

### Option 1: Local Ollama LLM (Recommended for Cost & Privacy)

```python
from lightrag import LightRAG, QueryParam
import ollama

# Configure Ollama client for local LLM
def get_ollama_llm_func():
    """Create Ollama-compatible LLM function for LightRAG"""
    async def ollama_llm_func(prompt, **kwargs):
        response = ollama.chat(
            model='llama3.1:8b',  # or 'qwen2.5:7b' for better financial reasoning
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'temperature': kwargs.get('temperature', 0.1),
                'top_p': kwargs.get('top_p', 0.9),
                'num_ctx': kwargs.get('max_tokens', 4096)
            }
        )
        return response['message']['content']
    return ollama_llm_func

# Local LLM configuration for hedge fund workflows (Cost: $0/month)
financial_rag_local = LightRAG(
    working_dir="./financial_knowledge_graph",
    llm_model_func=get_ollama_llm_func(),  # Local Ollama LLM
    embedding_model_name="text-embedding-3-small",  # Cheaper OpenAI embeddings
    # Or use local embeddings: embedding_model_name="BAAI/bge-small-en-v1.5"

    # Financial domain optimizations
    chunk_token_size=800,  # Optimal for financial documents
    chunk_overlap_token_size=100,
    entity_extract_max_gleaning=2,  # Ensure complete entity coverage

    # Enhanced performance settings
    embedding_batch_size=32,

    # Storage backend selection
    vector_storage="nano-vector-db",  # For development/small datasets
)
```

### Option 2: Hybrid Local/Remote Setup (Balanced Cost & Performance)

```python
# Hybrid: Local LLM for entity extraction, OpenAI for complex reasoning
def get_hybrid_llm_func():
    """Use local for simple tasks, OpenAI for complex financial reasoning"""
    async def hybrid_llm_func(prompt, **kwargs):
        # Detect if this is entity extraction (simple) or reasoning (complex)
        if any(keyword in prompt.lower() for keyword in ['extract', 'entities', 'relationships']):
            # Use local Ollama for entity extraction
            response = ollama.chat(
                model='llama3.1:8b',
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.1, 'num_ctx': 4096}
            )
            return response['message']['content']
        else:
            # Use OpenAI for complex financial reasoning
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective for most tasks
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 2000)
            )
            return response.choices[0].message.content
    return hybrid_llm_func

financial_rag_hybrid = LightRAG(
    working_dir="./financial_knowledge_graph",
    llm_model_func=get_hybrid_llm_func(),  # Hybrid local/remote
    embedding_model_name="text-embedding-3-large",  # Best embeddings for finance
    # Estimated cost: ~$5-15/month depending on usage
)
```

### Option 3: Full OpenAI Setup (Maximum Performance)

```python
# Full OpenAI configuration - premium performance for production
financial_rag_openai = LightRAG(
    working_dir="./financial_knowledge_graph",
    llm_model_name="gpt-4o",  # Best for complex financial reasoning
    embedding_model_name="text-embedding-3-large",  # Superior financial semantics

    # Financial domain optimizations
    chunk_token_size=800,
    chunk_overlap_token_size=100,
    entity_extract_max_gleaning=2,

    # Enhanced performance settings
    embedding_batch_size=32,

    # Production storage
    vector_storage="qdrant",  # For production scale
)
# Estimated cost: $50-200/month for active hedge fund usage
```

## Investment Research Query Parameters

```python
# Optimized parameters for financial analysis
investment_param = QueryParam(
    mode="mix",  # Adaptive selection - recommended default
    top_k=25,    # More entities for comprehensive analysis
    chunk_top_k=15,  # Sufficient context without token overflow
    enable_rerank=True,  # Critical for financial relevance

    # Token management for financial complexity
    max_entity_tokens=4000,
    max_relation_tokens=3000,
    max_total_tokens=12000,
)
```

## Performance Optimization

### Batch Document Processing

```python
# Batch document processing for efficiency
async def bulk_ingest_financial_docs(rag, documents):
    """Efficiently process multiple financial documents"""
    for doc_batch in chunk_list(documents, batch_size=10):
        tasks = []
        for doc in doc_batch:
            prepared_doc = prepare_financial_doc(doc.content)
            tasks.append(rag.ainsert(prepared_doc, doc.metadata))
        await asyncio.gather(*tasks)
```

### Incremental Updates

```python
# Incremental updates for live data
def update_financial_knowledge(rag, new_earnings_call):
    """Add new earnings call without full reindex"""
    # LightRAG handles incremental updates automatically
    rag.insert(new_earnings_call, chunk_overlap_token_size=150)
```

## Cost Optimization Strategy

### LLM Cost Comparison (Monthly Estimates)

| Setup | Entity Extraction | Query Processing | Embeddings | Total Cost | Performance |
|-------|------------------|------------------|------------|------------|-------------|
| **Pure Local** | Ollama (Free) | Ollama (Free) | Local BGE (Free) | **$0/month** | Good |
| **Hybrid Recommended** | Ollama (Free) | GPT-4o-mini ($5) | OpenAI Small ($2) | **~$7/month** | Very Good |
| **Cost-Optimized Cloud** | GPT-4o-mini ($8) | GPT-4o-mini ($12) | OpenAI Small ($2) | **~$22/month** | Very Good |
| **Premium Performance** | GPT-4o ($25) | GPT-4o ($50) | OpenAI Large ($8) | **~$83/month** | Excellent |

*Estimates based on ~50 documents/month processing + 200 queries/month for small hedge fund*

### Recommended Setup by Use Case

```python
# Development/Learning (Pure Local - $0/month)
development_config = {
    "llm_model_func": get_ollama_llm_func(),
    "embedding_model_name": "BAAI/bge-small-en-v1.5",  # Local embeddings
    "vector_storage": "nano-vector-db"
}

# Small Fund/Personal Use (Hybrid - $5-15/month)
small_fund_config = {
    "llm_model_func": get_hybrid_llm_func(),  # Local extraction + Remote reasoning
    "embedding_model_name": "text-embedding-3-small",  # Cheap but good
    "vector_storage": "nano-vector-db"
}

# Production Fund (Cloud - $50-100/month)
production_config = {
    "llm_model_name": "gpt-4o",  # Best reasoning
    "embedding_model_name": "text-embedding-3-large",  # Best embeddings
    "vector_storage": "qdrant"  # Production storage
}
```

## Financial Domain Optimizations

### Entity Types for Financial Documents

```python
# Financial entity types to prioritize during extraction
FINANCIAL_ENTITY_TYPES = [
    "TICKER",           # Stock symbols (NVDA, TSMC, AAPL)
    "COMPANY",          # Company names
    "PERSON",           # CEOs, analysts, key personnel
    "FINANCIAL_METRIC", # P/E, EPS, Revenue, etc.
    "GEOGRAPHY",        # Markets, countries, regions
    "SECTOR",           # Technology, Healthcare, etc.
    "PRODUCT",          # Product names and categories
    "EVENT",            # Earnings calls, product launches
    "REGULATION",       # SEC rules, compliance requirements
    "CURRENCY",         # USD, EUR, etc.
    "DATE"              # Quarterly periods, fiscal years
]
```

### Relationship Types for Investment Context

```python
# Investment-specific relationship patterns
INVESTMENT_RELATIONSHIP_TYPES = [
    "DEPENDS_ON",       # Supply chain dependencies
    "EXPOSED_TO",       # Risk exposures and themes
    "DRIVES",           # KPI and performance drivers
    "COMPETES_WITH",    # Competitive relationships
    "CORRELATES_WITH",  # Statistical correlations
    "IMPACTS",          # Causal relationships
    "MENTIONS",         # Document co-occurrence
    "SUPPLIES_TO",      # Business relationships
    "REGULATES",        # Regulatory relationships
    "LOCATED_IN"        # Geographic relationships
]
```

### Storage Configuration Options

```python
# Vector storage backends for different scales
STORAGE_BACKENDS = {
    "nano-vector-db": {
        "description": "Lightweight local storage for development",
        "max_documents": 10000,
        "memory_usage": "Low",
        "setup_complexity": "Minimal"
    },
    "chroma": {
        "description": "Mid-scale local storage with persistence",
        "max_documents": 100000,
        "memory_usage": "Medium",
        "setup_complexity": "Easy"
    },
    "qdrant": {
        "description": "Production-scale distributed storage",
        "max_documents": "Unlimited",
        "memory_usage": "Configurable",
        "setup_complexity": "Advanced"
    }
}
```

## Integration with ICE Components

### Working with ICELightRAG Wrapper

```python
from ice_lightrag.ice_rag import ICELightRAG

# Initialize with custom configuration
ice_rag = ICELightRAG(
    working_dir="./ice_lightrag/storage",
    config_override={
        "chunk_token_size": 800,
        "entity_extract_max_gleaning": 2,
        "embedding_batch_size": 32
    }
)

# Process financial documents
result = ice_rag.query(
    query="What companies are exposed to China risk?",
    mode="hybrid",
    max_hops=3,
    confidence_threshold=0.7
)
```

### MCP Compatibility

```python
# Format outputs for MCP tool interoperability
def format_for_mcp(lightrag_result):
    """Convert LightRAG output to MCP-compatible JSON"""
    return {
        "answer": lightrag_result.get("answer", ""),
        "sources": lightrag_result.get("sources", []),
        "entities": lightrag_result.get("entities", []),
        "relationships": lightrag_result.get("relationships", []),
        "confidence_score": lightrag_result.get("confidence", 0.0),
        "query_mode": lightrag_result.get("mode", "unknown"),
        "processing_time_ms": lightrag_result.get("timing", 0)
    }
```

---

**Related Documentation:**
- [Local LLM Guide](LOCAL_LLM_GUIDE.md) - Ollama setup and hybrid configurations
- [Query Patterns](QUERY_PATTERNS.md) - Query mode selection and optimization
- [CLAUDE.md](../CLAUDE.md) - Main development guide
- [Project Structure](../PROJECT_STRUCTURE.md) - File organization and navigation