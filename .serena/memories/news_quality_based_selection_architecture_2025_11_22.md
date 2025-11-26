# News Quality-Based Selection Architecture

**Date**: 2025-11-22  
**Type**: Core Architecture Pattern (Production)  
**Status**: ✅ Active (replaces proportional quota distribution)  
**Key Change**: Nov 22 fix - "Request Full, Select Best" strategy

---

## Executive Summary

**Strategy**: Request full limit from ALL sources → Deduplicate → Rank by quality → Select top N  
**Benefit**: Resilient to source failures + Quality-focused + Predictable output  
**Key Files**: `data_ingestion.py:914-1108`

---

## Core Design Philosophy

### Principle 1: Request Full, Not Divide

**OLD (Before Nov 22)**:
```python
# ❌ BUG: Divide quota across sources
fetch_budget = limit * 1.2
base_quota = max(1, fetch_budget // len(active_sources))
# If limit=3, sources=3 → Each gets 1 article
# If 1 source fails → Only 2 articles returned ❌
```

**NEW (After Nov 22)**:
```python
# ✅ FIX: Each source gets full quota
source_quota = limit  # 3 articles from EACH source
# If limit=3, sources=3 → Request 3 from each
# If 1 source fails → Still get 3 from others ✅
```

**Why This Matters**:
- **Resilience**: Source failures don't reduce article count
- **Quality**: Select best articles across ALL sources (not quota-limited)
- **Predictability**: User always gets `limit` articles (if available)

---

### Principle 2: Context-Aware Source Activation

**Logic** (`data_ingestion.py:943-967`):

```python
# Phase 1: Identify available real-time sources
real_time_sources = []
if is_service_available('finnhub'):    real_time_sources.append('finnhub')
if is_service_available('marketaux'):  real_time_sources.append('marketaux')
if is_service_available('benzinga'):   real_time_sources.append('benzinga')

# Phase 2: Smart delayed source inclusion
include_delayed = context in ['research', 'sentiment']
newsapi_available = is_service_available('newsapi')

# Activate NewsAPI if:
# 1. Context explicitly requests delayed sources (research/sentiment) OR
# 2. No real-time sources available (graceful degradation)
if newsapi_available and (include_delayed or not real_time_sources):
    active_sources.append('newsapi')
    if not real_time_sources:
        logger.warning("⚠️ Graceful degradation: Using NewsAPI despite context")
```

**Activation Matrix**:

| Context     | Real-Time Sources | NewsAPI Included? | Rationale                          |
|-------------|-------------------|-------------------|------------------------------------|
| `live`      | ✅ Yes            | ❌ No             | 24hr delay useless for live trading|
| `portfolio` | ✅ Yes            | ❌ No             | Prefer real-time for portfolio mgmt|
| `research`  | ✅ Yes            | ✅ Yes            | Volume > freshness (historical OK) |
| `sentiment` | ✅ Yes            | ✅ Yes            | Aggregate signals need volume      |
| `portfolio` | ❌ No (fallback)  | ✅ Yes (warning)  | Better delayed than nothing        |

---

### Principle 3: Quality-Based Ranking

**Scoring Formula** (`data_ingestion.py:1082-1097`):

```
relevance_score = base_score × source_weight × tier_penalty × premium_boost

where:
- base_score = 10.0
- source_weight ∈ [0.7, 1.5]
- tier_penalty ∈ [0.1, 1.0] (context-dependent)
- premium_boost = 1.3 if Benzinga, else 1.0
```

#### Source Credibility Weights

```python
source_weights = {
    'benzinga': 1.5,   # Premium professional (paid subscription)
                       # - Verified analyst coverage
                       # - Breaking news alerts
                       # - SEC filing analysis
    
    'finnhub': 1.2,    # High-quality real-time (free tier)
                       # - Real-time aggregation
                       # - Good global coverage
                       # - API reliability
    
    'marketaux': 1.0,  # Good NLP coverage (baseline)
                       # - Advanced NLP entity extraction
                       # - Sentiment scores included
    
    'newsapi': 0.7     # Delayed but broad (24hr delay)
                       # - 24-hour delay on free tier
                       # - 80,000+ source coverage
                       # - Historical research value
}
```

**Rationale**:
- **1.5× Benzinga**: Premium source justifies higher trust + paid subscription cost
- **1.2× Finnhub**: Proven reliability in real-time delivery
- **1.0× MarketAux**: Baseline - good quality, no standout features
- **0.7× NewsAPI**: Delay penalty + less financial-specific

#### Context-Specific Tier Penalties

**Tier Classification**:
- **Tier 1**: Real-time sources (0 delay)
- **Tier 2**: Delayed sources (24hr delay)

**Penalty Matrix**:

```python
tier_penalties = {
    #           Tier 1    Tier 2
    #         (real-time) (delayed)
    'live':      1.0       0.1      # 90% penalty: Delayed = useless for live trading
    'portfolio': 1.0       0.5      # 50% penalty: Prefer fresh but delayed OK
    'research':  1.0       0.9      # 10% penalty: Historical context, delay negligible
    'sentiment': 1.0       0.8      # 20% penalty: Volume > freshness for sentiment
}
```

**Rationale by Context**:

1. **`live` (0.1 penalty)**:
   - Use case: Intraday trading decisions
   - 24hr delay = completely stale for live trading
   - Example: Day trader needs real-time breaking news
   - 90% penalty reflects near-worthlessness

2. **`portfolio` (0.5 penalty)**:
   - Use case: Portfolio management (days-weeks horizon)
   - 24hr delay = somewhat relevant but less trustworthy
   - Example: PM analyzing position changes
   - 50% penalty = still useful but lower priority

3. **`research` (0.9 penalty)**:
   - Use case: Historical analysis, backtesting
   - 24hr delay = negligible (analyzing weeks/months)
   - Example: Analyst studying Q2 earnings sentiment
   - 10% penalty = essentially equal priority

4. **`sentiment` (0.8 penalty)**:
   - Use case: Aggregate sentiment signals
   - 24hr delay = acceptable (need volume > freshness)
   - Example: Measuring sentiment across 100 articles
   - 20% penalty = volume matters more

#### Premium Content Boost

```python
if doc.get('premium'):  # Benzinga articles
    score *= 1.3        # 30% boost
```

**Rationale**:
- Benzinga includes analyst ratings, price targets, insider trades
- Higher signal-to-noise ratio (curated vs aggregated)
- Justifies paid subscription cost
- Differential ensures Benzinga wins ties

---

## Concrete Scoring Examples

### Example 1: Portfolio Context (Default)

**Articles Available**:
```
A: Benzinga, Tier 1 (real-time), Premium=True
B: Finnhub, Tier 1 (real-time), Premium=False
C: MarketAux, Tier 1 (real-time), Premium=False  
D: NewsAPI, Tier 2 (delayed), Premium=False
```

**Scores**:
```
A: 10.0 × 1.5 × 1.0 × 1.3 = 19.5 ✅ #1
B: 10.0 × 1.2 × 1.0 × 1.0 = 12.0 ✅ #2
C: 10.0 × 1.0 × 1.0 × 1.0 = 10.0 ✅ #3
D: 10.0 × 0.7 × 0.5 × 1.0 = 3.5  ⚠️ #4 (much lower)
```

**If limit=3**: Returns A, B, C (NewsAPI excluded)

---

### Example 2: Live Trading Context

**Same articles, context='live'**:

```
A: 10.0 × 1.5 × 1.0 × 1.3 = 19.5 ✅ #1
B: 10.0 × 1.2 × 1.0 × 1.0 = 12.0 ✅ #2
C: 10.0 × 1.0 × 1.0 × 1.0 = 10.0 ✅ #3
D: 10.0 × 0.7 × 0.1 × 1.0 = 0.7  ❌ Essentially filtered out
```

**Impact**: NewsAPI essentially excluded (90% penalty)

---

### Example 3: Research Context

**Same articles, context='research'**:

```
A: 10.0 × 1.5 × 1.0 × 1.3 = 19.5 ✅ #1
B: 10.0 × 1.2 × 1.0 × 1.0 = 12.0 ✅ #2
C: 10.0 × 1.0 × 1.0 × 1.0 = 10.0 ✅ #3
D: 10.0 × 0.7 × 0.9 × 1.0 = 6.3  ✅ Much closer (viable)
```

**Impact**: NewsAPI becomes competitive (only 10% penalty, broad coverage valued)

---

## Complete Fetching Flow

### 4-Phase Process (Per Ticker)

```
INPUT: fetch_company_news('NVDA', limit=3, context='portfolio')

┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Source Activation (context-aware)                 │
│                                                              │
│  Active sources: ['finnhub', 'marketaux', 'benzinga']      │
│  NewsAPI: EXCLUDED (portfolio + real-time available)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Request Full Limit (resilience strategy)          │
│                                                              │
│  source_quota = 3  (each source gets FULL limit)           │
│                                                              │
│  Finnhub:   Request 3 → Returns 3 articles                 │
│  MarketAux: Request 3 → Returns 3 articles                 │
│  Benzinga:  Request 3 → Returns 0 (failed) ⚠️              │
│                                                              │
│  Total collected: 6 articles                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Deduplication (headline-based)                    │
│                                                              │
│  • Normalize headlines (lowercase, remove punct)            │
│  • Compare first 60 chars                                   │
│  • Remove exact duplicates                                  │
│                                                              │
│  Result: 6 unique articles (0 duplicates)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Quality Ranking & Selection                       │
│                                                              │
│  Ranked by score:                                           │
│    1. Finnhub #1  (score: 12.0)                            │
│    2. Finnhub #2  (score: 12.0)                            │
│    3. Finnhub #3  (score: 12.0)                            │
│    4. MarketAux #1 (score: 10.0)                           │
│    5. MarketAux #2 (score: 10.0)                           │
│    6. MarketAux #3 (score: 10.0)                           │
│                                                              │
│  Select top 3: Returns articles 1-3                         │
│                                                              │
│  ✅ Result: 3 articles (exactly as requested)              │
└─────────────────────────────────────────────────────────────┘

OUTPUT: [
  {content: "...", source: "finnhub", tier: 1, score: 12.0},
  {content: "...", source: "finnhub", tier: 1, score: 12.0},
  {content: "...", source: "finnhub", tier: 1, score: 12.0}
]
```

**Key Benefit**: Benzinga failure didn't reduce output (still got 3 articles)

---

## Portfolio-Level Scaling

### Tiny Portfolio (1 ticker)

```
Portfolio: ['FICO']
news_limit: 3

Per-ticker process:
  FICO → Request 3 from each of 3 sources
       → Collect 6-9 articles
       → Deduplicate
       → Return top 3

Total: 3 documents
API calls: 3 (1 per source)
```

---

### All Portfolio (30 tickers)

```
Portfolio: 30 tickers
news_limit: 3 per ticker

Per-ticker process:
  For each of 30 tickers:
    → Request 3 from each of 3 sources
    → Collect 6-9 articles
    → Deduplicate
    → Return top 3

Total: ~90 documents (30 × 3)
API calls: 90 (30 tickers × 3 sources)
Deduplication rate: ~5-10% (cross-source)
Final documents: ~85 news articles
```

**Cost per ingestion run**: ~$0.10-0.30 (depends on API pricing)  
**Daily cost** (1 run/day): ~$3-9/month

---

## Design Principles Summary

### 1. Quality Hierarchy
```
Premium professional (Benzinga 1.5×)
  > Free real-time (Finnhub 1.2×)
  > Baseline real-time (MarketAux 1.0×)
  > Delayed broad (NewsAPI 0.7×)
```

### 2. Context-Driven Behavior
```
live       → Real-time only (no delay tolerance)
portfolio  → Real-time preferred (50% delay penalty)
research   → All sources welcome (10% delay penalty)
sentiment  → Volume matters (20% delay penalty)
```

### 3. Resilience Through Redundancy
```
Request full limit from ALL sources
  ↓ Deduplicate by headline
  ↓ Rank by quality/context/tier
  ↓ Return top N
```

### 4. Cost-Conscious Activation
```
Portfolio/live:  Skip NewsAPI if real-time available (save API calls)
Research:        Include NewsAPI (volume > cost)
Sentiment:       Include NewsAPI (aggregate signals)
```

---

## Code Locations

| Component | File:Line | Purpose |
|-----------|-----------|---------|
| Source activation | `data_ingestion.py:943-967` | Context-aware routing |
| Full-limit strategy | `data_ingestion.py:973-978` | Request full quota (Nov 22 fix) |
| Fetching loop | `data_ingestion.py:984-1037` | Fetch + deduplicate |
| Quality ranking | `data_ingestion.py:1049-1108` | Score articles |
| Portfolio orchestration | `ice_simplified.py:2081-2110` | Loop through tickers |

---

## Related Documentation

- `NEWS_LIMIT_QUOTA_FIX_2025_11_22.md` - Nov 22 bug fix details
- `multi_source_news_api_complete_strategy_2025_11_17.md` - Original strategy (outdated quota logic)
- `ARCHITECTURE.md` - Overall system architecture

---

## Pattern Applications

This quality-based selection pattern applies to any system needing:
1. Multiple data sources with varying quality/cost/latency
2. Context-dependent source prioritization
3. Resilience to source failures
4. Cost optimization through smart activation
5. Predictable output guarantees

**Other Use Cases**:
- Price data (real-time vs delayed vs historical)
- Weather APIs (live vs forecast vs satellite)
- Search results (premium vs free vs cached)

---

**Last Updated**: 2025-11-22  
**Status**: Production (Nov 22 quota fix deployed)  
**Replaces**: Proportional quota distribution (buggy)
