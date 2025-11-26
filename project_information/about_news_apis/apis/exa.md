# Exa API - Semantic Search for Deep Research

**Provider**: Exa.ai
**Tier**: Special (On-demand research)
**Cost**: Premium (pay-as-you-go)
**Status**: 🔬 Research-only (not integrated in automatic news fetching)
**Priority**: N/A (On-demand, not in automatic pipeline)

---

## Overview

Exa provides neural search capabilities for discovering relevant web content using semantic understanding rather than keyword matching. In ICE, Exa is used **on-demand for deep research**, not for automatic news fetching.

### Key Strengths

- ✅ **Semantic understanding**: Finds conceptually similar content, not just keyword matches
- ✅ **Web-scale discovery**: Access to billions of pages beyond traditional news APIs
- ✅ **Research depth**: Discovers niche sources, academic papers, company blogs
- ✅ **Query flexibility**: Natural language queries ("Find bullish takes on NVDA AI")
- ✅ **Content extraction**: Automatic extraction and cleaning of web page content

### Limitations

- ❌ **Not real-time news**: Not designed for breaking news monitoring
- ❌ **Pay-per-use**: Costs add up with high volume usage
- ⚠️ **Slower**: Semantic search takes longer than traditional keyword search
- ⚠️ **Quality variance**: Web content varies widely in reliability

---

## Use Case in ICE

### Automatic News Fetching vs On-Demand Research

```
┌─────────────────────────────────────────────────────────────┐
│ NEWS API INTEGRATION (Automatic, High Frequency)            │
├─────────────────────────────────────────────────────────────┤
│ Finnhub    → Real-time company news (60/min free)          │
│ MarketAux  → Real-time with NLP (unlimited free)           │
│ Benzinga   → Premium professional (paid)                   │
│ NewsAPI    → Delayed aggregation (1000/day free)           │
├─────────────────────────────────────────────────────────────┤
│ Used for: Portfolio building, daily updates, monitoring     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ EXA INTEGRATION (On-Demand, Deep Research)                  │
├─────────────────────────────────────────────────────────────┤
│ Exa        → Semantic web search (pay-per-use)             │
├─────────────────────────────────────────────────────────────┤
│ Used for: Due diligence, competitor analysis, niche topics  │
└─────────────────────────────────────────────────────────────┘
```

### When to Use Exa

**✅ Use Exa for**:
- Due diligence on potential investments
- Competitor analysis and industry research
- Discovering emerging trends or technologies
- Finding expert opinions and analysis pieces
- Researching niche sectors or small-cap companies

**❌ Don't use Exa for**:
- Daily portfolio monitoring (too slow, too expensive)
- Breaking news alerts (not designed for real-time)
- High-frequency updates (pay-per-use costs add up)

---

## API Specifications

### Endpoint (via MCP Server)

```
MCP Server: exa
Tool: search
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Natural language search query |
| `num_results` | integer | No | Number of results (default: 10, max: 100) |
| `type` | string | No | Search type: 'neural' (semantic) or 'keyword' |
| `use_autoprompt` | boolean | No | Let Exa optimize your query (recommended) |
| `category` | string | No | Filter by category: 'company', 'research paper', etc. |
| `start_published_date` | string | No | Filter by publish date (ISO 8601) |

### Pricing (Approximate)

| Tier | Searches/Month | Cost |
|------|----------------|------|
| Free Trial | 1,000 | $0 |
| Starter | 10,000 | $20/mo |
| Professional | 100,000 | $100/mo |
| Enterprise | Custom | Custom |

**Cost per search**: ~$0.002-0.01 depending on tier and complexity

---

## Response Format

### Example Response

```json
{
  "results": [
    {
      "title": "Why NVIDIA's AI Chips Will Dominate the Next Decade",
      "url": "https://example.com/nvidia-ai-analysis",
      "published_date": "2024-11-10",
      "author": "Jane Smith",
      "score": 0.87,
      "text": "Full extracted content of the article...",
      "highlights": [
        "NVIDIA's CUDA ecosystem creates a moat that competitors can't easily replicate...",
        "The company's data center revenue grew 200% YoY..."
      ]
    }
  ],
  "autoprompt_string": "Optimized query: bullish investment thesis NVIDIA artificial intelligence semiconductor dominance"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Page title or article headline |
| `url` | string | URL of the source |
| `published_date` | string | Publication date (if available) |
| `author` | string | Author name (if available) |
| `score` | float | Relevance score (0.0-1.0, higher = more relevant) |
| `text` | string | Extracted full text content |
| `highlights` | array | Key excerpts matching query intent |
| `autoprompt_string` | string | Exa's optimized version of your query |

---

## ICE Integration

### Implementation Location

**File**: `updated_architectures/implementation/data_ingestion.py`
**Method**: `research_company_deep()` (lines ~1400-1500)

### Usage Pattern

```python
# On-demand research (not automatic)
def research_company_deep(
    self,
    ticker: str,
    query_context: str,
    topics: Optional[List[str]] = None,
    include_competitors: bool = False
) -> List[Dict[str, str]]:
    """
    Deep research using Exa semantic search

    Args:
        ticker: Stock symbol
        query_context: What you're researching (e.g., "growth strategy", "competitive position")
        topics: Specific topics to focus on
        include_competitors: Whether to research competitors too

    Returns:
        List of research documents with semantic relevance
    """

    # Build semantic query
    query = f"{ticker} {query_context}"
    if topics:
        query += f" {' '.join(topics)}"

    # Call Exa via MCP
    try:
        results = mcp_client.call_tool(
            server='exa',
            tool='search',
            arguments={
                'query': query,
                'num_results': 10,
                'type': 'neural',  # Semantic search
                'use_autoprompt': True
            }
        )

        # Convert to ICE document format
        documents = []
        for result in results['results']:
            doc = {
                'content': f"{result['title']}\n\n{result['text']}\n\nSource: {result['url']}",
                'source': 'exa',
                'file_path': f"exa:{ticker}_{hash(result['url'])}",
                'freshness': 'on-demand',  # Not real-time news
                'tier': 3,  # Research tier (not news tier 1/2)
                'premium': True,  # Pay-per-use
                'semantic_score': result['score']
            }
            documents.append(doc)

        return documents

    except Exception as e:
        logger.warning(f"Exa research failed: {e}")
        return []
```

### Metadata Schema

```python
{
    'content': str,              # "Title\n\nExtracted text\n\nSource: URL"
    'source': 'exa',             # Always 'exa'
    'file_path': str,            # "exa:AAPL_hash"
    'freshness': 'on-demand',    # Not 'real-time' or 'delayed_24h'
    'tier': 3,                   # Research tier (separate from news tiers 1/2)
    'premium': True,             # Pay-per-use service
    'semantic_score': float,     # 0.0-1.0 (Exa's relevance score)
    'url': str                   # Original source URL (BONUS)
}
```

---

## Configuration

### Enable via MCP

**File**: ICE configuration

```python
# MCP source enabled for research
mcp_source_enabled = True  # Enables Exa and other MCP tools

# Research limits (per stock, on-demand only)
research_limit = 0  # Default: disabled for automatic ingestion
```

### Trigger Research Manually

```python
# In notebook or via query
research_docs = ice.ingester.research_company_deep(
    ticker='NVDA',
    query_context='AI chip competitive advantages',
    topics=['CUDA ecosystem', 'data center growth'],
    include_competitors=True
)
```

---

## Usage Examples

### Example 1: Due Diligence Research

```python
# Researching potential investment
research = ice.ingester.research_company_deep(
    ticker='PLTR',
    query_context='government contracts and AI platform strategy',
    topics=['Palantir Gotham', 'commercial growth', 'competitive moat']
)

# Results:
# - Semantic search finds in-depth analysis pieces
# - Discovers niche blogs, Substack posts, expert opinions
# - Goes beyond traditional news sources
```

### Example 2: Competitor Analysis

```python
# Understanding competitive landscape
research = ice.ingester.research_company_deep(
    ticker='NVDA',
    query_context='competitive threats in AI chips',
    topics=['AMD MI300', 'Intel Gaudi', 'custom AI chips'],
    include_competitors=True
)

# Results:
# - Finds technical comparisons
# - Discovers emerging competitors
# - Identifies potential disruption risks
```

### Example 3: Emerging Trend Discovery

```python
# Researching new technology trend
research = ice.ingester.research_company_deep(
    ticker='TSLA',
    query_context='autonomous driving regulatory landscape',
    topics=['FSD approval', 'robotaxi regulations', 'safety standards']
)

# Results:
# - Finds regulatory analysis
# - Discovers policy papers
# - Identifies jurisdiction-specific rules
```

---

## Scoring (If Used in News Context)

### Hypothetical Scores

If Exa results were scored like news (they're not currently):

| Context | Base | Source Weight | Tier Penalty | Final Score | Rank |
|---------|------|---------------|--------------|-------------|------|
| Research | 10.0 | 1.1 | 0.8 (tier 3) | **8.8** | 5th |

**Note**: Exa is **not scored** with news APIs - it's on-demand research, not automatic news.

---

## Best Practices

### 1. Use Natural Language Queries

```python
# ✅ Good: Natural language, specific intent
query = "bullish investment thesis for NVIDIA's data center AI chips"

# ❌ Avoid: Keyword stuffing (Exa is semantic, not keyword-based)
query = "NVDA AI chips data center bullish thesis investment"
```

### 2. Leverage Autoprompt

```python
# ✅ Recommended: Let Exa optimize your query
arguments = {
    'query': 'TSLA competitive advantages',
    'use_autoprompt': True  # Exa enhances query
}

# Result: "Tesla competitive advantages electric vehicle battery technology vertical integration manufacturing"
```

### 3. Filter by Date for Freshness

```python
# Research recent developments only
arguments = {
    'query': 'Apple Vision Pro market reception',
    'start_published_date': '2024-10-01'  # Last month only
}
```

### 4. Cost Management

```python
# ✅ Good: Use for high-value research only
if position_size > $1_000_000:
    research = exa.search(ticker, query)

# ❌ Avoid: Running Exa on every portfolio stock daily
for ticker in all_holdings:  # $2-10 per day!
    research = exa.search(ticker, generic_query)
```

---

## Comparison with News APIs

### Exa vs Finnhub/NewsAPI

| Feature | Exa | News APIs |
|---------|-----|-----------|
| **Content Type** | Web pages, blogs, analysis | News articles |
| **Search Method** | Semantic (meaning-based) | Keyword (exact match) |
| **Depth** | Deep (niche sources) | Broad (major outlets) |
| **Speed** | Slower (1-3 seconds) | Fast (<500ms) |
| **Cost** | Pay-per-use ($0.002-0.01/search) | Free tiers available |
| **Use Case** | Research, due diligence | Monitoring, updates |
| **Frequency** | On-demand | Automatic/scheduled |

### When to Use Each

```
Exa:        "What are experts saying about NVDA's AI moat?"
Finnhub:    "What's the latest news on NVDA?"

Exa:        "Find analysis of TSLA's manufacturing efficiency"
NewsAPI:    "Get all news articles mentioning TSLA today"

Exa:        "Discover emerging competitors in quantum computing"
MarketAux:  "Get real-time news on quantum computing stocks"
```

---

## Troubleshooting

### Issue: "Irrelevant results"
**Cause**: Query too broad or ambiguous
**Fix**:
```python
# ❌ Too broad
query = "Tesla"

# ✅ Specific intent
query = "Tesla's advantages in battery manufacturing cost efficiency"
```

### Issue: "High costs accumulating"
**Cause**: Running Exa too frequently
**Fix**:
```python
# Limit Exa to high-value research
# Use free news APIs for daily monitoring
# Reserve Exa for:
# - New position research (>$100k)
# - Quarterly deep dives
# - Competitive threat analysis
```

### Issue: "Outdated content"
**Cause**: No date filter applied
**Fix**:
```python
# Filter to recent content only
arguments = {
    'query': query,
    'start_published_date': '2024-11-01'  # Recent content
}
```

---

## Future Enhancements

### Phase 1: Automated Trigger Logic

**Tasks**:
1. Detect when Exa research would be valuable (e.g., unusual price movement)
2. Auto-trigger research with pre-defined queries
3. Store results separately in "research" category

**Estimated Effort**: 2-3 hours

### Phase 2: Research Cache

**Tasks**:
1. Cache Exa results to avoid duplicate searches
2. Set TTL based on content type (news: 1 day, analysis: 7 days)
3. Reduce costs by 50-70%

**Estimated Effort**: 2 hours

### Phase 3: Competitor Graph

**Tasks**:
1. Use Exa to discover competitors mentioned with target company
2. Build competitor relationship graph
3. Enable queries like "Who are NVDA's emerging threats?"

**Estimated Effort**: 4-5 hours

---

## Additional Resources

- **Official Docs**: https://docs.exa.ai
- **Pricing**: https://exa.ai/pricing
- **API Playground**: https://app.exa.ai
- **Support**: support@exa.ai

---

**Last Updated**: 2025-11-16
**ICE Integration**: 🔬 On-demand research only (not automatic news)
**Recommendation**: ⭐⭐⭐⭐ Excellent for deep research, use sparingly
**Cost Awareness**: ~$0.002-0.01 per search, budget accordingly
