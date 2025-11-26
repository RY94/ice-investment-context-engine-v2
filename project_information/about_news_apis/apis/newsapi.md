# NewsAPI.org - Broad News Coverage (24hr Delay)

**Provider**: NewsAPI.org
**Tier**: 2 (Delayed)
**Cost**: Free tier available
**Status**: ✅ Active in ICE (context-restricted)
**Priority**: #4 (Fetched last, conditionally)

---

## Overview

NewsAPI.org aggregates news from 80,000+ sources worldwide, providing broad coverage of global news. **Critical limitation**: Free tier has **24-hour delay**, making it unsuitable for real-time trading but valuable for historical research and sentiment analysis.

### Key Strengths

- ✅ **Broad coverage**: 80,000+ news sources globally
- ✅ **High volume**: 1,000 requests/day on free tier
- ✅ **Easy integration**: Simple REST API
- ✅ **Multiple languages**: Support for 50+ languages
- ✅ **Source filtering**: Can filter by specific news sources

### Critical Limitations

- ❌ **24-hour delay**: Free tier news is delayed by 24 hours (MAJOR ISSUE for trading)
- ❌ **Limited historical**: Only 1 month of historical news on free tier
- ❌ **No sentiment**: Raw news only, no sentiment scores
- ❌ **Rate limits**: 1,000 req/day cap (vs Finnhub 60 req/min = 86,400/day)

---

## ⚠️ 24-Hour Delay Issue

### Problem

Free tier NewsAPI.org returns news that is **up to 24 hours old**, making it:

- ❌ **Unsuitable for intraday trading** (price may have moved 5-10% already)
- ❌ **Risky for daily analysis** (stale information for decision-making)
- ❌ **Poor for breaking news** (events already priced into market)

### ICE Solution

Smart context-based routing:

| Context | NewsAPI Included? | Penalty | Reason |
|---------|------------------|---------|--------|
| **Live** | ❌ NO | N/A (excluded) | 24hr delay unacceptable for live trading |
| **Portfolio** | ⚠️ YES | 5x penalty | Included but heavily de-prioritized |
| **Research** | ✅ YES | 1.3x penalty | Delay acceptable for historical research |
| **Sentiment** | ✅ YES | 1.6x penalty | Volume matters more than freshness |

---

## API Specifications

### Endpoint

```
GET https://newsapi.org/v2/everything
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query (ticker symbol or company name) |
| `apiKey` | string | Yes | API key |
| `pageSize` | integer | No | Number of results (max 100) |
| `sortBy` | string | No | Sort order: 'relevancy', 'popularity', 'publishedAt' |
| `from` | string | No | Start date (YYYY-MM-DD) |
| `to` | string | No | End date (YYYY-MM-DD) |

### Rate Limits

| Tier | Requests/Day | Requests/Minute | Historical Depth |
|------|--------------|-----------------|------------------|
| **Free** | 1,000 | 5 | 1 month |
| Developer ($450/mo) | 100,000 | 100 | 3 years |
| Business ($750/mo) | 250,000 | 250 | 3 years |

---

## Response Format

### Example Response

```json
{
  "status": "ok",
  "totalResults": 38,
  "articles": [
    {
      "source": {
        "id": "bloomberg",
        "name": "Bloomberg"
      },
      "author": "Sarah Chen",
      "title": "Apple Shares Rise on Strong iPhone Sales",
      "description": "Apple Inc. shares climbed after reporting stronger-than-expected iPhone sales...",
      "url": "https://www.bloomberg.com/...",
      "urlToImage": "https://assets.bwbx.io/...",
      "publishedAt": "2024-11-15T14:30:00Z",
      "content": "Apple Inc. shares climbed 2.3% after reporting stronger-than-expected iPhone sales for the quarter..."
    }
  ]
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `source.name` | string | News source name |
| `author` | string | Article author |
| `title` | string | Article title/headline |
| `description` | string | Article description/summary |
| `url` | string | Link to full article |
| `urlToImage` | string | Article image URL |
| `publishedAt` | string | Publication timestamp (ISO 8601) |
| `content` | string | Article content snippet (truncated) |

---

## ICE Integration

### Implementation Location

**File**: `updated_architectures/implementation/data_ingestion.py`
**Lines**: 931-953

### Fetch Logic

```python
# NewsAPI.org - Delayed news (Priority #4, conditional)
if include_delayed and self.config.is_api_available('newsapi'):
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': symbol,
            'apiKey': self.config.api_keys['newsapi'],
            'pageSize': limit,
            'sortBy': 'relevancy'
        }

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        for article in data.get('articles', []):
            # Create structured document with delay warning
            doc = {
                'content': f"⚠️ DELAYED DATA (up to 24 hours old)\n\n{article['title']}\n\n{article['description']}",
                'source': 'newsapi',
                'file_path': f"newsapi:{symbol}_{hash(article['url'])}",
                'freshness': 'delayed_24h',  # ⚠️ Critical metadata
                'tier': 2,                    # Tier 2 (delayed)
                'premium': False,
                'delay_warning': True         # Explicit warning flag
            }
            documents.append(doc)
    except Exception as e:
        logger.warning(f"NewsAPI failed: {e}")
else:
    if context == 'live':
        logger.info(f"Skipping NewsAPI (24hr delay, context='{context}' requires real-time)")
```

### Metadata Schema

ICE enriches NewsAPI articles with **delay warnings**:

```python
{
    'content': str,              # "⚠️ DELAYED DATA...\n\nHeadline\n\nDescription"
    'source': 'newsapi',         # Always 'newsapi'
    'file_path': str,            # "newsapi:AAPL_hash"
    'freshness': 'delayed_24h',  # ⚠️ Always 'delayed_24h'
    'tier': 2,                   # Always 2 (delayed tier)
    'relevance_score': float,    # 3.5-7.0 (context-dependent penalty)
    'premium': False,            # Always False
    'delay_warning': True        # ⚠️ Explicit warning flag
}
```

---

## Configuration

### Enable in ICE

**File**: `ice_building_workflow.ipynb` Cell 14

```python
# News APIs (4 sources)
newsapi_enabled = True  # Enable NewsAPI (with delay awareness)
```

### Set API Key

**File**: `.env`

```bash
NEWS_API_KEY=your_api_key_here
```

**Get API Key**: https://newsapi.org/register

---

## Usage Patterns

### 1. Live Trading Context (EXCLUDED)

```python
# Real-time news for intraday monitoring
news = ingester.fetch_company_news('NVDA', limit=5, context='live')

# NewsAPI EXCLUDED (24hr delay unacceptable)
# Log message: "Skipping NewsAPI (24hr delay, context='live' requires real-time)"
```

### 2. Portfolio Analysis Context (PENALIZED)

```python
# Daily portfolio review
news = ingester.fetch_company_news('AAPL', limit=10, context='portfolio')

# NewsAPI included but heavily de-prioritized
# Score: 3.5 (10.0 × 0.7 source weight × 0.5 tier penalty)
# Result: Appears at bottom of ranked list after real-time sources
```

### 3. Historical Research Context (INCLUDED)

```python
# Due diligence for new position
news = ingester.fetch_company_news('TSLA', limit=20, context='research')

# NewsAPI included with minimal penalty
# Score: 6.3 (10.0 × 0.7 source weight × 0.9 tier penalty)
# Result: Mixed with other sources for comprehensive coverage
```

---

## Scoring & Prioritization

### Source Quality Weight

**NewsAPI**: 0.7x (lowest among all sources due to delay)

### Context-Specific Scoring

| Context | Base | Source Weight | Tier Penalty | Final Score | Rank |
|---------|------|---------------|--------------|-------------|------|
| Live | 10.0 | 0.7 | N/A | **EXCLUDED** | N/A |
| Portfolio | 10.0 | 0.7 | 0.5 | **3.5** | 4th (last) |
| Research | 10.0 | 0.7 | 0.9 | **6.3** | 3rd-4th |
| Sentiment | 10.0 | 0.7 | 0.8 | **5.6** | 4th |

**Comparison** (Portfolio context):
- Benzinga premium: 19.5 (1st)
- Finnhub: 12.0 (2nd)
- MarketAux: 10.0 (3rd)
- **NewsAPI: 3.5 (4th - last)**

---

## Best Practices

### 1. Use for Historical Research Only

```python
# ✅ Good: Historical due diligence (delay acceptable)
news = ingester.fetch_company_news('TSLA', limit=20, context='research')

# ❌ Avoid: Live trading decisions (24hr delay unacceptable)
news = ingester.fetch_company_news('NVDA', limit=5, context='live')  # NewsAPI excluded
```

### 2. Combine with Real-Time Sources

```python
# ✅ Good: Use NewsAPI for volume/breadth, Finnhub for timeliness
# Portfolio context automatically balances both

# ❌ Avoid: Relying solely on NewsAPI for trading signals
```

### 3. Check Delay Warnings

```python
# ✅ Good: Check metadata before trading decisions
for article in news_docs:
    if article.get('delay_warning'):
        print(f"⚠️ WARNING: Article from {article['source']} is up to 24 hours old")
```

---

## Advantages vs Other Sources

### vs Finnhub
- ✅ **More sources** (80,000 vs curated list)
- ✅ **Higher request limit** (1,000/day vs 60/min throttling)
- ❌ **24hr delay** (Finnhub real-time)
- ❌ **Lower quality** (0.7x vs 1.2x source weight)

### vs MarketAux
- ✅ **More sources** (80,000 vs focused financial)
- ❌ **24hr delay** (MarketAux real-time)
- ❌ **Rate limited** (1,000/day vs unlimited)
- ❌ **No NLP** (MarketAux has entity extraction)

---

## Troubleshooting

### Issue: "426 Upgrade Required"
**Cause**: Exceeded 1,000 requests/day on free tier
**Fix**:
```bash
# Check current usage at https://newsapi.org/account
# Wait for daily reset (midnight UTC)
# Or upgrade to paid tier ($450/mo for 100,000/day)
```

### Issue: "Empty articles array"
**Cause**: No news matching query in last 24 hours (remember delay)
**Fix**:
```python
# Check if ticker/company name is correct
# Try broader search terms
# Check date range (free tier: 1 month max)
```

### Issue: "All articles show delay warnings"
**Cause**: Expected behavior on free tier (all news delayed 24hr)
**Fix**:
```python
# No fix needed - this is correct behavior
# Use Finnhub/MarketAux for real-time news
# Or upgrade to NewsAPI paid tier for real-time access
```

---

## Why NewsAPI Was Demoted

### Original Implementation (BROKEN)

```python
# OLD: NewsAPI fetched FIRST (before Finnhub)
sources = [newsapi, benzinga, finnhub, marketaux]
```

**Problems**:
- 24hr old news returned first
- Real-time sources (Finnhub) buried
- No transparency about data freshness
- Trading decisions based on stale information

### New Implementation (FIXED)

```python
# NEW: Real-time sources FIRST, NewsAPI last (conditionally)
sources = [finnhub, marketaux, benzinga, newsapi_if_context_allows]
```

**Improvements**:
- Real-time sources prioritized
- NewsAPI excluded from live context
- Clear delay warnings in metadata
- Lower relevance scores reflect lower quality

---

## Upgrade Path

### Free Tier → Developer ($450/mo)

**Benefits**:
- ✅ **Real-time access** (no 24hr delay)
- ✅ **100,000 requests/day** (vs 1,000)
- ✅ **3 years historical** (vs 1 month)
- ✅ **100 req/min** (vs 5)

**Recommendation**: Only upgrade if:
- Need more than 1,000 articles/day (unlikely for small hedge funds)
- Need real-time NewsAPI specifically (Finnhub better for this)
- Need deep historical analysis (3 years vs 1 month)

**Cost-Benefit Analysis**:
- **Finnhub free tier** covers most real-time needs
- **MarketAux free tier** provides unlimited volume
- **NewsAPI upgrade** only needed for specific historical research

---

## Additional Resources

- **Official Docs**: https://newsapi.org/docs/endpoints/everything
- **API Dashboard**: https://newsapi.org/account
- **Pricing**: https://newsapi.org/pricing
- **Sources List**: https://newsapi.org/sources
- **Support**: support@newsapi.org

---

**Last Updated**: 2025-11-16
**ICE Integration**: ✅ Active (Priority #4, context-restricted)
**Recommendation**: ⭐⭐ Use for research/sentiment only, not live trading
**Critical Warning**: ⚠️ 24-hour delay on free tier
