# Smart News API Integration - Implementation Guide

**File**: `IMPLEMENTATION.md`
**Last Updated**: 2025-11-17
**Implementation Version**: 1.1 (Smart Integration + Graceful Degradation + Date Range Fix)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Source Prioritization Algorithm](#source-prioritization-algorithm)
3. [Context-Based Routing](#context-based-routing)
4. [Relevance Scoring System](#relevance-scoring-system)
5. [Metadata Schema](#metadata-schema)
6. [Code Organization](#code-organization)
7. [Data Flow](#data-flow)
8. [Error Handling](#error-handling)

---

## Architecture Overview

### Design Principles

```
┌─────────────────────────────────────────────────────────────────┐
│ SMART NEWS INTEGRATION ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Query → Context Selection → Source Routing → Fetching     │
│     ↓             ↓                   ↓              ↓           │
│  'NVDA'      'live'/'portfolio'   Priority List    API Calls    │
│                                                                  │
│     → Metadata Enhancement → Scoring → Ranking → Return         │
│           ↓                    ↓         ↓           ↓           │
│       freshness, tier       Calculate  Sort by    List[Dict]    │
│       source, file_path      score    relevance                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Main Entry Point** | `data_ingestion.py` | 914-1050 | `fetch_company_news()` |
| **Source Selection** | `data_ingestion.py` | 943-971 | Context-aware routing + graceful degradation |
| **Scoring Engine** | `data_ingestion.py` | 1052-1111 | `_score_and_rank_news()` |
| **NewsAPI Date Fix** | `data_ingestion.py` | 1189-1205 | Explicit date range (24hr delay handling) |
| **Integration Layer** | `ice_simplified.py` | 1138, 2036, 2289, 2530 | Callers with context |
| **Configuration** | `config.py` | Various | API keys, switches |

---

## Source Prioritization Algorithm

### Proportional Distribution Strategy

**Design Philosophy**: Maximize news coverage by distributing quota across ALL available sources, then deduplicate and rank by relevance.

```python
# Step 1: Determine active sources (availability + context filtering)
active_sources = []
real_time_sources = []  # NEW (2025-11-17): Track real-time availability

# Real-time sources (no delay)
if is_service_available('finnhub'):
    active_sources.append('finnhub')
    real_time_sources.append('finnhub')
if is_service_available('marketaux'):
    active_sources.append('marketaux')
    real_time_sources.append('marketaux')
if is_service_available('benzinga'):
    active_sources.append('benzinga')
    real_time_sources.append('benzinga')

# Context-based filtering + graceful degradation (2025-11-17)
include_delayed = context in ['research', 'sentiment']
newsapi_available = is_service_available('newsapi')

# NEW: Include NewsAPI if (1) appropriate context OR (2) no real-time sources (graceful degradation)
if newsapi_available and (include_delayed or not real_time_sources):
    active_sources.append('newsapi')
    if not real_time_sources:
        logger.warning(f"⚠️ Using NewsAPI despite context='{context}' (no real-time sources). Data will have 24hr delay.")

# Step 2: Calculate proportional quota with 20% dedup buffer
fetch_budget = int(limit * 1.2)  # Over-fetch to account for duplicates
base_quota = max(1, fetch_budget // len(active_sources))
remainder = fetch_budget % len(active_sources)

# Step 3: Distribute quota across sources
# Example: limit=5, sources=3 → fetch_budget=6, quotas=[2, 2, 2]
# Example: limit=5, sources=4 → fetch_budget=6, quotas=[2, 2, 1, 1]

# Step 4: Fetch from ALL sources (not sequential early-exit)
for idx, source in enumerate(active_sources):
    source_quota = base_quota + (1 if idx < remainder else 0)
    docs = fetch_from_source(source, symbol, source_quota)

    # Inline deduplication (normalized headline matching)
    for doc in docs:
        headline_key = normalize_headline(doc)
        if headline_key not in seen_headlines:
            seen_headlines.add(headline_key)
            all_articles.append(doc)

# Step 5: Score and rank all unique articles
all_articles = _score_and_rank_news(all_articles, symbol, context)

# Step 6: Return top N articles up to limit
return all_articles[:limit]
```

**Key Advantages:**
- **Coverage**: Captures unique content from all sources (~80% coverage vs ~20% with sequential)
- **Cost-Efficient**: Controlled over-fetch (20%) vs brute force (600%)
- **Robust**: Each source fails independently without breaking pipeline
- **Generalizable**: Math-based allocation works for 1-N sources

### Context-Based Inclusion Matrix

```
┌────────────┬──────────┬───────────┬──────────┬───────────┐
│  Source    │   Live   │ Portfolio │ Research │ Sentiment │
├────────────┼──────────┼───────────┼──────────┼───────────┤
│ Finnhub    │    ✅    │     ✅    │    ✅    │     ✅    │
│ MarketAux  │    ✅    │     ✅    │    ✅    │     ✅    │
│ Benzinga   │    ✅    │     ✅    │    ✅    │     ✅    │
│ NewsAPI    │    ❌    │     ✅    │    ✅    │     ✅    │
└────────────┴──────────┴───────────┴──────────┴───────────┘

✅ Included in active sources (proportional quota allocated)
❌ Excluded (24hr delay incompatible with real-time trading context)
```

### Source Priority Weights (for scoring, not fetching order)

```python
# Post-fetch scoring weights (affects ranking, not quota)
source_weights = {
    'benzinga': 1.5,   # Premium professional source
    'finnhub': 1.2,    # High-quality real-time
    'marketaux': 1.0,  # Baseline (good NLP coverage)
    'newsapi': 0.7     # Delayed but broad
}
```

---

## Context-Based Routing

### Implementation

```python
def fetch_company_news(
    self,
    symbol: str,
    limit: int = 5,
    context: str = 'portfolio'
) -> List[Dict[str, str]]:
    """
    Intelligently fetch company news with proportional multi-source distribution

    Strategy:
        - Distributes fetch quota proportionally across available sources
        - Applies simple headline-based deduplication (catches ~80% of duplicates)
        - Over-fetches by 20% to account for potential duplicates
        - Returns top-scored unique articles up to limit
    """
    import re

    # Step 1: Determine active sources based on availability and context
    active_sources = []
    if self.is_service_available('finnhub'):
        active_sources.append('finnhub')
    if self.is_service_available('marketaux'):
        active_sources.append('marketaux')
    if self.benzinga_client:
        active_sources.append('benzinga')

    # Context-based filtering (exclude NewsAPI in 'live' context)
    include_delayed = context in ['research', 'sentiment']
    if include_delayed and self.is_service_available('newsapi'):
        active_sources.append('newsapi')

    if not active_sources:
        logger.warning(f"⚠️ {symbol}: No news APIs available. Returning empty list.")
        return []

    # Step 2: Calculate proportional quota distribution with 20% dedup buffer
    fetch_budget = int(limit * 1.2)  # Over-fetch to account for duplicates
    base_quota = max(1, fetch_budget // len(active_sources))
    remainder = fetch_budget % len(active_sources)

    logger.info(f"📊 {symbol}: Distributing quota={fetch_budget} across {len(active_sources)} sources")

    # Step 3: Fetch from all active sources with proportional quotas
    all_articles = []
    seen_headlines = set()

    for idx, source in enumerate(active_sources):
        source_quota = base_quota + (1 if idx < remainder else 0)

        try:
            logger.info(f"📰 {symbol}: Fetching {source_quota} from {source}...")

            # Fetch from source-specific method
            if source == 'finnhub':
                raw_docs = self._fetch_finnhub_news(symbol, source_quota)
                freshness, tier = 'real-time', 1
            elif source == 'marketaux':
                raw_docs = self._fetch_marketaux_news(symbol, source_quota)
                freshness, tier = 'real-time', 1
            elif source == 'benzinga':
                raw_docs = self._fetch_benzinga_news(symbol, source_quota)
                freshness, tier = 'real-time', 1
            elif source == 'newsapi':
                raw_docs = self._fetch_newsapi(symbol, source_quota)
                freshness, tier = 'delayed_24h', 2

            # Process articles with inline deduplication
            added_count = 0
            for doc in raw_docs:
                # Normalize headline for deduplication
                headline = doc.split('\n')[0] if '\n' in doc else doc[:100]
                headline_key = re.sub(r'[^\w\s]', '', headline).lower()[:60]

                if headline_key in seen_headlines:
                    continue  # Skip duplicate

                seen_headlines.add(headline_key)
                doc_hash = hashlib.md5(doc[:200].encode()).hexdigest()[:8]

                article = {
                    'content': f"⚠️ DELAYED DATA (up to 24 hours old)\n\n{doc}" if source == 'newsapi' else doc,
                    'source': source,
                    'file_path': f"{source}:{symbol}_{doc_hash}",
                    'freshness': freshness,
                    'tier': tier
                }

                if source == 'benzinga':
                    article['premium'] = True
                if source == 'newsapi':
                    article['delay_warning'] = True

                all_articles.append(article)
                added_count += 1

            duplicates = len(raw_docs) - added_count
            logger.info(f"  ✅ {source}: {added_count} unique ({duplicates} duplicates removed)")

        except Exception as e:
            logger.warning(f"  ❌ {source} failed for {symbol}: {e}")
            continue  # Graceful degradation

    # Step 4: Score and rank all unique articles
    if all_articles:
        all_articles = self._score_and_rank_news(all_articles, symbol, context)

    # Step 5: Return top N articles up to limit
    final_articles = all_articles[:limit]
    logger.info(f"📊 {symbol}: Returning {len(final_articles)} unique articles from {len(set(a['source'] for a in final_articles))} sources")

    return final_articles
```

---

## Relevance Scoring System

### Scoring Formula

```
relevance_score = base × source_weight × tier_penalty × premium_boost
```

### Visual Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│ RELEVANCE SCORING ALGORITHM                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Base Score (10.0)                                              │
│       ↓                                                          │
│  × Source Weight                                                │
│    - Benzinga:  1.5x  (premium professional)                   │
│    - Finnhub:   1.2x  (high-quality real-time)                 │
│    - MarketAux: 1.0x  (baseline)                               │
│    - NewsAPI:   0.7x  (delayed)                                │
│       ↓                                                          │
│  × Tier Penalty (context-dependent)                            │
│    Context: Live                                                │
│      - Tier 1 (real-time): 1.0x                                │
│      - Tier 2 (delayed):   0.1x  (heavy penalty)               │
│    Context: Portfolio                                           │
│      - Tier 1: 1.0x                                             │
│      - Tier 2: 0.5x  (moderate penalty)                        │
│    Context: Research                                            │
│      - Tier 1: 1.0x                                             │
│      - Tier 2: 0.9x (minimal penalty)                          │
│       ↓                                                          │
│  × Premium Boost (if applicable)                               │
│    - Premium content: 1.3x                                      │
│    - Regular content: 1.0x                                      │
│       ↓                                                          │
│  = Final Relevance Score                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Score Examples

```
Example 1: Benzinga Premium (Portfolio Context)
  10.0 × 1.5 × 1.0 × 1.3 = 19.5 ⭐ HIGHEST

Example 2: Finnhub Real-time (Portfolio Context)
  10.0 × 1.2 × 1.0 × 1.0 = 12.0

Example 3: MarketAux Real-time (Portfolio Context)
  10.0 × 1.0 × 1.0 × 1.0 = 10.0

Example 4: NewsAPI Delayed (Portfolio Context)
  10.0 × 0.7 × 0.5 × 1.0 = 3.5

Example 5: NewsAPI Delayed (Live Context)
  EXCLUDED (not scored, filtered out before scoring)
```

### Implementation Code

```python
def _score_and_rank_news(
    self,
    documents: List[Dict],
    symbol: str,
    context: str
) -> List[Dict]:
    """
    Multi-factor relevance scoring
    """
    
    # Source credibility weights
    source_weights = {
        'benzinga': 1.5,   # Premium professional source
        'finnhub': 1.2,    # High-quality real-time
        'marketaux': 1.0,  # Good NLP coverage (baseline)
        'newsapi': 0.7     # Delayed but broad
    }
    
    # Context-specific tier penalties
    tier_penalties = {
        'live': {1: 1.0, 2: 0.1},        # Heavy penalty
        'portfolio': {1: 1.0, 2: 0.5},   # Moderate penalty
        'research': {1: 1.0, 2: 0.9},    # Minimal penalty
        'sentiment': {1: 1.0, 2: 0.8}    # Volume focus
    }
    
    # Calculate scores
    for doc in documents:
        base_score = 10.0
        
        # Source quality multiplier
        source = doc.get('source', 'unknown')
        source_mult = source_weights.get(source, 0.5)
        
        # Tier penalty (context-dependent)
        tier = doc.get('tier', 1)
        tier_mult = tier_penalties[context].get(tier, 1.0)
        
        # Premium boost
        premium_mult = 1.3 if doc.get('premium', False) else 1.0
        
        # Final score
        score = base_score * source_mult * tier_mult * premium_mult
        doc['relevance_score'] = round(score, 2)
    
    # Sort by relevance (highest first)
    documents.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    return documents
```

---

## Metadata Schema

### Complete Schema

```python
{
    # Core fields (required)
    'content': str,           # Article text
    'source': str,            # Source identifier
    'file_path': str,         # Unique document ID
    
    # Freshness metadata (required)
    'freshness': str,         # 'real-time' | 'delayed_24h' | 'on-demand'
    'tier': int,              # 1 (real-time) | 2 (delayed) | 3 (research)
    
    # Scoring metadata (required)
    'relevance_score': float, # Calculated score (0.0-20.0)
    
    # Optional metadata
    'premium': bool,          # Premium content flag (Benzinga)
    'delay_warning': bool,    # Delay warning flag (NewsAPI)
    'sentiment': str,         # Sentiment label (MarketAux, Benzinga)
    'channels': List[str],    # Event types (Benzinga)
    'semantic_score': float   # Semantic relevance (Exa)
}
```

### Field-by-Field Details

#### `content` (string, required)
```python
# Format: Headline + Body + Source attribution
content = f"""
{headline}

{description or summary}

{full_body (if available)}

Source: {source_name}
Published: {timestamp}
URL: {url}
"""
```

#### `source` (string, required)
```python
# One of: 'finnhub', 'marketaux', 'benzinga', 'newsapi', 'exa'
source = 'finnhub'
```

#### `file_path` (string, required)
```python
# Format: "{source}:{symbol}_{unique_id}"
# Purpose: Unique document identifier for deduplication
file_path = f"{source}:{symbol}_{article_id}"  # e.g., "finnhub:AAPL_85951641"
```

#### `freshness` (string, required)
```python
# Values:
freshness = 'real-time'    # Finnhub, MarketAux, Benzinga
freshness = 'delayed_24h'  # NewsAPI.org free tier
freshness = 'on-demand'    # Exa semantic search
```

#### `tier` (integer, required)
```python
# Values:
tier = 1  # Real-time sources (Finnhub, MarketAux, Benzinga)
tier = 2  # Delayed sources (NewsAPI)
tier = 3  # Research sources (Exa)
```

#### `relevance_score` (float, required)
```python
# Range: 0.0-20.0 (higher = more relevant)
# Calculation: base(10.0) × source_weight × tier_penalty × premium_boost
relevance_score = 19.5  # Benzinga premium (highest possible)
relevance_score = 12.0  # Finnhub
relevance_score = 10.0  # MarketAux
relevance_score = 3.5   # NewsAPI (portfolio context)
```

---

## Code Organization

### File Structure

```
ICE Project Root
├── updated_architectures/implementation/
│   ├── data_ingestion.py         # Main implementation
│   │   ├── fetch_company_news()  # Lines 826-960
│   │   └── _score_and_rank_news() # Lines 962-1021
│   │
│   ├── ice_simplified.py          # Integration layer
│   │   ├── Caller 1: Line 1129   # build_knowledge_graph
│   │   ├── Caller 2: Line 2027   # prefetch_knowledge_base
│   │   ├── Caller 3: Line 2280   # refresh_knowledge_graph
│   │   └── Caller 4: Line 2521   # handle_portfolio_changes
│   │
│   └── config.py                  # Configuration
│       └── API source switches
│
├── project_information/about_news_apis/
│   └── (This documentation directory)
│
└── tests/
    └── tmp_comprehensive_news_test.py  # Test suite (48 tests)
```

### Module Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│ DEPENDENCY GRAPH                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ice_simplified.py                                              │
│       ↓                                                          │
│  ProductionDataIngester (from data_ingestion.py)               │
│       ↓                                                          │
│  fetch_company_news(symbol, limit, context)                    │
│       ↓                                                          │
│  [Fetch from sources] → [Add metadata] → [Score & rank]        │
│       ↓                        ↓                ↓                │
│  finnhub/marketaux/        tier, freshness   _score_and_rank() │
│  benzinga/newsapi          source, premium                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### End-to-End Flow Diagram

```
USER REQUEST
     ↓
┌────────────────────────────────────────────────┐
│ ice_simplified.py:1129                         │
│ news_docs = self.ingester.fetch_company_news( │
│     symbol='NVDA',                             │
│     limit=5,                                   │
│     context='portfolio'  ← User-specified      │
│ )                                              │
└────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────┐
│ data_ingestion.py:826 (fetch_company_news)    │
│                                                │
│ Step 1: Determine active sources              │
│   active_sources = []                          │
│   if finnhub available: append('finnhub')      │
│   if marketaux available: append('marketaux')  │
│   if benzinga available: append('benzinga')    │
│   if newsapi AND context != 'live': append('newsapi') │
│                                                │
│ Step 2: Calculate proportional quotas         │
│   fetch_budget = limit * 1.2  (20% buffer)    │
│   base_quota = fetch_budget // num_sources    │
│   # Example: 5 docs, 3 sources → 6 budget,    │
│   #          quotas = [2, 2, 2]               │
│                                                │
│ Step 3: Fetch from ALL sources                │
│   all_articles = []                            │
│   seen_headlines = set()                       │
│   for each source:                             │
│     docs = fetch_from_api(source, quota)      │
│     for each doc:                              │
│       normalized = normalize_headline(doc)     │
│       if normalized not in seen_headlines:     │
│         add_metadata(doc, source, tier)        │
│         all_articles.append(doc)               │
│         seen_headlines.add(normalized)         │
│                                                │
│ Step 4: Score and rank all unique articles    │
│   all_articles = _score_and_rank_news(        │
│       all_articles, symbol, context            │
│   )                                            │
│                                                │
│ Step 5: Return top N                          │
│   return all_articles[:limit]                 │
└────────────────────────────────────────────────┘
     ↓
RETURNED TO CALLER
     ↓
┌────────────────────────────────────────────────┐
│ List[Dict] with metadata (multi-source)        │
│ [                                              │
│   {                                            │
│     'content': '...',                          │
│     'source': 'benzinga',  ← Premium source   │
│     'file_path': 'benzinga:NVDA_a7f3',        │
│     'freshness': 'real-time',                 │
│     'tier': 1,                                 │
│     'relevance_score': 19.5,  ← Highest       │
│     'premium': True                            │
│   },                                           │
│   {                                            │
│     'content': '...',                          │
│     'source': 'finnhub',   ← Real-time        │
│     'file_path': 'finnhub:NVDA_123',          │
│     'freshness': 'real-time',                 │
│     'tier': 1,                                 │
│     'relevance_score': 12.0                   │
│   },                                           │
│   {                                            │
│     'content': '...',                          │
│     'source': 'marketaux', ← NLP coverage     │
│     'file_path': 'marketaux:NVDA_xyz',        │
│     'freshness': 'real-time',                 │
│     'tier': 1,                                 │
│     'relevance_score': 10.0                   │
│   },                                           │
│   ...                                          │
│ ]                                              │
└────────────────────────────────────────────────┘
     ↓
USED IN KNOWLEDGE GRAPH BUILDING
```

### Context Flow Example

```
Context: 'live' (Real-time trading), limit=5
     ↓
┌────────────────────────────────────────────────┐
│ include_delayed = False                        │
│ active_sources = ['finnhub', 'marketaux', 'benzinga'] │
│ (NewsAPI excluded - 24hr delay incompatible)   │
└────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────┐
│ Proportional Quota Calculation:                │
│   fetch_budget = 5 * 1.2 = 6                   │
│   num_sources = 3                               │
│   base_quota = 6 // 3 = 2                      │
│   remainder = 6 % 3 = 0                        │
│   quotas = [2, 2, 2]                           │
└────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────┐
│ Fetch Execution:                                │
│ ✅ Finnhub:   Fetch 2 articles                 │
│ ✅ MarketAux: Fetch 2 articles                 │
│ ✅ Benzinga:  Fetch 2 articles                 │
│ Total fetched: 6 (before deduplication)        │
│                                                 │
│ Inline Deduplication:                           │
│   Article 1 (Finnhub):   "NVDA announces..."  │
│   Article 2 (MarketAux): "NVDA announces..." ← Duplicate (skipped) │
│   Article 3 (Benzinga):  "NVDA reveals..."    │
│   ...                                           │
│ Total unique: 5 articles                       │
└────────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────────┐
│ Score & Rank:                                   │
│   1. Benzinga premium (19.5)                   │
│   2. Finnhub real-time (12.0)                  │
│   3. MarketAux NLP (10.0)                      │
│   4. Finnhub article 2 (12.0)                  │
│   5. Benzinga article 2 (19.5)                 │
└────────────────────────────────────────────────┘
     ↓
Result: Top 5 diverse articles from 3 sources
```

---

## Error Handling

### Graceful Degradation Pattern

```python
# Each source fails independently
documents = []

# Try Finnhub
try:
    finnhub_docs = fetch_finnhub(symbol, limit)
    documents.extend(finnhub_docs)
except Exception as e:
    logger.warning(f"Finnhub failed: {e}")
    # Continue to next source (no crash)

# Try MarketAux
try:
    marketaux_docs = fetch_marketaux(symbol, limit)
    documents.extend(marketaux_docs)
except Exception as e:
    logger.warning(f"MarketAux failed: {e}")
    # Continue (still have Finnhub docs if successful)

# ... and so on

# Result: Partial success is acceptable
# Even if 3/4 sources fail, 1 working source provides value
```

### Error Recovery Strategy

```
┌────────────────────────────────────────────────┐
│ ERROR HANDLING STRATEGY                        │
├────────────────────────────────────────────────┤
│                                                │
│  Source A fails                                │
│      ↓                                          │
│  Log warning                                   │
│      ↓                                          │
│  Continue to Source B                          │
│      ↓                                          │
│  If ALL sources fail:                          │
│    - Return empty list []                      │
│    - Log error summary                         │
│    - Don't crash the system                    │
│      ↓                                          │
│  Caller handles empty result:                  │
│    - Skip news processing                      │
│    - Continue with other data (financials, SEC)│
│                                                │
└────────────────────────────────────────────────┘
```

---

## Performance Considerations

### Sequential vs Parallel Fetching

**Current**: Sequential (one at a time)
```python
# Current implementation
for source in [finnhub, marketaux, benzinga, newsapi]:
    docs = fetch(source)  # Waits for completion
    documents.extend(docs)

# Total time: 500ms + 800ms + 1200ms + 400ms = 2900ms
```

**Future**: Parallel (all at once)
```python
# Proposed enhancement
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(fetch, source): source
        for source in [finnhub, marketaux, benzinga, newsapi]
    }
    
    for future in concurrent.futures.as_completed(futures):
        docs = future.result()
        documents.extend(docs)

# Total time: max(500ms, 800ms, 1200ms, 400ms) = 1200ms
# Speedup: 2.4x
```

### Caching Strategy

```python
# Content-based deduplication (already implemented via manifest)
content_hash = hashlib.sha256(content.encode()).hexdigest()
doc_id = f"{source}:{symbol}_{content_hash[:8]}"

if manifest.is_document_ingested(doc_id):
    logger.info(f"Skipping duplicate: {doc_id}")
    continue  # Skip already-ingested documents
```

---

**Last Updated**: 2025-11-16
**Version**: 1.0
**Maintained By**: ICE Development Team
