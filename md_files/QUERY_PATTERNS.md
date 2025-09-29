# docs/QUERY_PATTERNS.md
# Comprehensive guide to LightRAG query modes, selection strategies, and financial use case patterns
# Provides query optimization techniques and performance monitoring for investment analysis
# Relevant files: ice_lightrag/ice_rag.py, ice_main_notebook.ipynb, simple_demo.py, LIGHTRAG_SETUP.md

# Query Patterns & Optimization Guide

This guide provides comprehensive strategies for LightRAG query mode selection, performance optimization, and financial use case patterns for the ICE Investment Context Engine.

## 🎯 Query Mode Selection Strategy

LightRAG provides six query modes, each optimized for different types of investment analysis tasks.

### LOCAL Mode - Entity-Focused Analysis

**Best for:**
- Ticker-specific analysis
- Company fundamentals research
- Management commentary analysis
- Single-entity deep dives

**Example Queries:**
```python
# Company-specific analysis
"What are NVDA's key business risks?"
"What drives TSMC's revenue growth?"
"Who are Apple's main suppliers?"
"What is Microsoft's competitive moat?"

# Financial metrics analysis
"What are Tesla's key performance indicators?"
"How has Amazon's margin structure evolved?"
"What are Google's main revenue streams?"
```

**Query Parameters:**
```python
local_param = QueryParam(
    mode="local",
    top_k=20,           # Focus on most relevant entities
    enable_rerank=True, # Critical for financial relevance
    max_entity_tokens=3000,
    max_relation_tokens=2000
)
```

### GLOBAL Mode - Market-Wide Themes

**Best for:**
- Sector and thematic analysis
- Market-wide events and trends
- Macro economic analysis
- Cross-sector impact assessment

**Example Queries:**
```python
# Sector analysis
"How is AI regulation affecting tech stocks?"
"What sectors benefit from rising interest rates?"
"Which industries are most exposed to inflation?"
"How does geopolitical tension affect energy markets?"

# Market themes
"What are the emerging trends in renewable energy?"
"How is supply chain disruption affecting different sectors?"
"What are the key drivers of semiconductor demand?"
```

**Query Parameters:**
```python
global_param = QueryParam(
    mode="global",
    top_k=15,
    chunk_top_k=10,     # Broader context for themes
    enable_rerank=True,
    max_entity_tokens=2500,
    max_relation_tokens=3500
)
```

### HYBRID Mode - Comprehensive Research

**Best for:**
- Multi-company comparative analysis
- Supply chain investigations
- Comprehensive investment thesis development
- Cross-entity relationship analysis

**Example Queries:**
```python
# Multi-company analysis
"How does China risk affect US semiconductor companies?"
"Which portfolio companies depend on Taiwan suppliers?"
"How do tech giants compare on AI investments?"
"What are the competitive dynamics in cloud computing?"

# Supply chain analysis
"Which companies are most exposed to rare earth metal prices?"
"How does automotive electrification affect different suppliers?"
"What are the downstream effects of chip shortages?"
```

**Query Parameters:**
```python
hybrid_param = QueryParam(
    mode="hybrid",
    top_k=25,           # More comprehensive entity coverage
    chunk_top_k=15,
    enable_rerank=True,
    max_entity_tokens=4000,
    max_relation_tokens=3000,
    max_total_tokens=12000
)
```

### MIX Mode - Adaptive Selection (Recommended Default)

**Best for:**
- General investment research queries
- Exploratory analysis
- When unsure of optimal approach
- Multi-turn conversation contexts

**Example Queries:**
```python
# General investment queries
"What portfolio names are exposed to AI regulation?"
"How might Fed policy changes affect our holdings?"
"What are the key risks in our energy allocation?"
"Which stocks benefit from infrastructure spending?"

# Exploratory analysis
"What's happening with Chinese ADRs lately?"
"Are there any emerging ESG risks in our portfolio?"
"What are analysts saying about semiconductor outlook?"
```

**Query Parameters:**
```python
mix_param = QueryParam(
    mode="mix",         # Automatically selects best approach
    top_k=20,
    enable_rerank=True,
    max_entity_tokens=3500,
    max_relation_tokens=2500,
    max_total_tokens=10000
)
```

### NAIVE Mode - Traditional Vector Search

**Best for:**
- Baseline performance comparison
- Simple document retrieval
- When graph relationships are not needed
- Performance benchmarking

**Example Queries:**
```python
# Simple document search
"Find earnings call transcripts mentioning margin pressure"
"Search for research notes on ESG investing"
"Retrieve documents about cryptocurrency regulation"
```

**Query Parameters:**
```python
naive_param = QueryParam(
    mode="naive",
    chunk_top_k=15,     # Standard vector retrieval
    enable_rerank=True
)
```

### BYPASS Mode - Direct LLM Response

**Best for:**
- General knowledge questions
- When no retrieval is needed
- Quick fact checking
- Testing LLM capabilities

**Example Queries:**
```python
# General financial knowledge
"What is the difference between EBITDA and net income?"
"How do stock buybacks affect EPS?"
"What are the main valuation methodologies?"
```

## 📊 Financial Use Case Patterns

### Portfolio Risk Assessment

```python
# Multi-hop risk analysis
risk_queries = [
    "What are the concentration risks in our tech allocation?",
    "How exposed are we to interest rate sensitivity?",
    "Which holdings have significant China exposure?",
    "What regulatory risks affect our healthcare positions?"
]

# Use HYBRID mode for comprehensive risk mapping
for query in risk_queries:
    result = ice_rag.query(query, mode="hybrid", max_hops=2)
```

### Earnings Season Analysis

```python
# Company-specific earnings preparation
earnings_queries = [
    "What are the key metrics to watch in NVDA's next earnings?",
    "What guidance updates should we expect from Apple?",
    "How has Tesla's delivery guidance evolved recently?"
]

# Use LOCAL mode for entity-focused analysis
for query in earnings_queries:
    result = ice_rag.query(query, mode="local", top_k=25)
```

### Sector Rotation Research

```python
# Thematic sector analysis
sector_queries = [
    "Which sectors typically outperform during rate hikes?",
    "How do defensive sectors perform in recession fears?",
    "What are the rotation patterns from growth to value?"
]

# Use GLOBAL mode for broad thematic analysis
for query in sector_queries:
    result = ice_rag.query(query, mode="global", chunk_top_k=12)
```

### Supply Chain Intelligence

```python
# Multi-hop supply chain analysis
supply_chain_queries = [
    "How does Taiwan semiconductor capacity affect our tech holdings?",
    "Which companies are most vulnerable to logistics disruption?",
    "What alternative suppliers exist for critical components?"
]

# Use HYBRID mode for complex relationship mapping
for query in supply_chain_queries:
    result = ice_rag.query(query, mode="hybrid", max_hops=3)
```

## ⚡ Performance Optimization

### Query Parameter Tuning

```python
# Performance-optimized parameters for different scenarios
PERFORMANCE_CONFIGS = {
    "fast_exploration": {
        "top_k": 10,
        "chunk_top_k": 8,
        "max_entity_tokens": 2000,
        "max_relation_tokens": 1500,
        "enable_rerank": False  # Skip for speed
    },
    "balanced_analysis": {
        "top_k": 20,
        "chunk_top_k": 12,
        "max_entity_tokens": 3500,
        "max_relation_tokens": 2500,
        "enable_rerank": True
    },
    "comprehensive_research": {
        "top_k": 30,
        "chunk_top_k": 20,
        "max_entity_tokens": 5000,
        "max_relation_tokens": 4000,
        "enable_rerank": True
    }
}
```

### Batch Query Processing

```python
async def batch_process_queries(queries: List[str], mode: str = "mix") -> List[Dict]:
    """Process multiple queries efficiently"""
    tasks = []
    for query in queries:
        task = ice_rag.aquery(
            query=query,
            mode=mode,
            **PERFORMANCE_CONFIGS["balanced_analysis"]
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

### Query Caching Strategy

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_query(query_hash: str, mode: str, **kwargs):
    """Cache frequent queries to improve response time"""
    return ice_rag.query(query, mode=mode, **kwargs)

def get_query_hash(query: str, mode: str, **kwargs) -> str:
    """Generate hash for query caching"""
    query_string = f"{query}_{mode}_{sorted(kwargs.items())}"
    return hashlib.md5(query_string.encode()).hexdigest()

# Usage
query = "What are NVDA's key risks?"
query_hash = get_query_hash(query, "local")
result = cached_query(query_hash, "local", top_k=20)
```

## 📈 Query Performance Monitoring

### Response Time Tracking

```python
import time
from typing import Dict, Any

def monitor_query_performance(query: str, mode: str, **kwargs) -> Dict[str, Any]:
    """Monitor and log query performance metrics"""
    start_time = time.time()

    try:
        result = ice_rag.query(query, mode=mode, **kwargs)
        end_time = time.time()

        performance_metrics = {
            "query": query[:100] + "..." if len(query) > 100 else query,
            "mode": mode,
            "response_time_ms": int((end_time - start_time) * 1000),
            "success": True,
            "entity_count": len(result.get("entities", [])),
            "source_count": len(result.get("sources", [])),
            "answer_length": len(result.get("answer", "")),
            "timestamp": time.time()
        }

        # Log performance metrics
        log_performance_metrics(performance_metrics)
        return result

    except Exception as e:
        end_time = time.time()
        error_metrics = {
            "query": query[:100] + "..." if len(query) > 100 else query,
            "mode": mode,
            "response_time_ms": int((end_time - start_time) * 1000),
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }
        log_performance_metrics(error_metrics)
        raise
```

### Performance Benchmarking

```python
def benchmark_query_modes(test_queries: List[str]) -> Dict[str, Dict]:
    """Benchmark different query modes for performance comparison"""
    modes = ["local", "global", "hybrid", "mix", "naive"]
    results = {}

    for mode in modes:
        mode_results = {
            "total_queries": 0,
            "successful_queries": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "min_response_time": float('inf'),
            "errors": []
        }

        response_times = []

        for query in test_queries:
            try:
                start_time = time.time()
                ice_rag.query(query, mode=mode)
                response_time = (time.time() - start_time) * 1000

                response_times.append(response_time)
                mode_results["successful_queries"] += 1

            except Exception as e:
                mode_results["errors"].append(str(e))

            mode_results["total_queries"] += 1

        if response_times:
            mode_results["avg_response_time"] = sum(response_times) / len(response_times)
            mode_results["max_response_time"] = max(response_times)
            mode_results["min_response_time"] = min(response_times)

        results[mode] = mode_results

    return results
```

## 🔍 Advanced Query Techniques

### Multi-Hop Reasoning Patterns

```python
# 1-hop: Direct relationships
one_hop_queries = [
    "Which suppliers does NVDA depend on?",
    "What are Tesla's main competitors?",
    "Who are Apple's key customers?"
]

# 2-hop: Causal chains
two_hop_queries = [
    "How does China risk impact NVDA through TSMC?",
    "How do rising rates affect REITs through borrowing costs?",
    "How does oil price volatility impact airlines through fuel costs?"
]

# 3-hop: Multi-step reasoning
three_hop_queries = [
    "What portfolio names are exposed to AI regulation via chip suppliers?",
    "How might Fed policy affect our tech holdings through dollar strength?",
    "What defensive positions benefit from rate hikes through sector rotation?"
]

# Configure for multi-hop analysis
multi_hop_param = QueryParam(
    mode="hybrid",
    top_k=30,
    enable_rerank=True,
    max_hops=3,  # Enable multi-hop traversal
    confidence_threshold=0.6
)
```

### Temporal Query Patterns

```python
# Time-sensitive investment queries
temporal_queries = [
    "What has changed in the semiconductor outlook over the past quarter?",
    "How have analyst ratings evolved for our energy holdings?",
    "What are the recent developments in AI regulation?"
]

# Configure for temporal analysis
temporal_param = QueryParam(
    mode="hybrid",
    top_k=25,
    enable_rerank=True,
    temporal_weight=0.8,  # Prioritize recent information
    recency_bias=True
)
```

### Confidence-Based Filtering

```python
def confidence_filtered_query(query: str, min_confidence: float = 0.7) -> Dict:
    """Filter results by confidence threshold for high-precision analysis"""
    result = ice_rag.query(
        query,
        mode="hybrid",
        confidence_threshold=min_confidence,
        enable_rerank=True
    )

    # Additional confidence filtering
    if "entities" in result:
        result["entities"] = [
            entity for entity in result["entities"]
            if entity.get("confidence", 0) >= min_confidence
        ]

    return result

# Usage for high-precision research
high_precision_result = confidence_filtered_query(
    "What are the confirmed risks for semiconductor companies?",
    min_confidence=0.8
)
```

## 🎯 Query Optimization Best Practices

### 1. Query Specificity

```python
# Poor: Too vague
"What's happening with tech stocks?"

# Better: More specific
"What are the key risks affecting mega-cap tech stocks in Q4 2024?"

# Best: Highly specific with context
"How are rising interest rates and AI regulation affecting the valuations of Apple, Microsoft, and Google?"
```

### 2. Context Injection

```python
# Add context for better results
contextual_query = f"""
Given our portfolio focus on US large-cap growth stocks with emphasis on technology and healthcare sectors:

{user_query}

Please consider our investment horizon of 3-5 years and focus on fundamental analysis over technical indicators.
"""
```

### 3. Multi-Part Query Decomposition

```python
def decompose_complex_query(complex_query: str) -> List[str]:
    """Break down complex queries into simpler components"""
    # Example: "How do geopolitical tensions affect our portfolio?"
    decomposed = [
        "What geopolitical risks are currently elevated?",
        "Which sectors are most sensitive to geopolitical events?",
        "What are our portfolio's exposures to international markets?",
        "How have similar events affected these holdings historically?"
    ]
    return decomposed

# Process each component and synthesize results
def process_decomposed_query(complex_query: str) -> Dict:
    subqueries = decompose_complex_query(complex_query)
    subresults = []

    for subquery in subqueries:
        result = ice_rag.query(subquery, mode="mix")
        subresults.append(result)

    # Synthesize results (implementation depends on use case)
    return synthesize_results(subresults, complex_query)
```

---

**Related Documentation:**
- [LightRAG Setup](LIGHTRAG_SETUP.md) - Complete configuration guide
- [Local LLM Guide](LOCAL_LLM_GUIDE.md) - Cost optimization strategies
- [CLAUDE.md](../CLAUDE.md) - Main development guide
- [ICE Development Plan](plans/ICE_DEVELOPMENT_PLAN.md) - Implementation roadmap