# Finnhub API - Real-Time Financial News

**Provider**: Finnhub.io
**Tier**: 1 (Real-time)
**Cost**: Free tier available
**Status**: ✅ Active in ICE
**Priority**: #1 (Fetched first)

---

## Overview

Finnhub provides real-time financial news, market data, and fundamental data for stocks, forex, and cryptocurrencies. Their free tier offers **60 requests per minute**, making it the best free real-time news source for ICE.

### Key Strengths

- ✅ **Real-time delivery**: No delays, immediate news as it breaks
- ✅ **Best free tier**: 60 req/min is generous for small hedge funds
- ✅ **High quality sources**: Curated from professional financial news outlets
- ✅ **Comprehensive coverage**: Global stocks, including US, EU, Asia markets
- ✅ **Rich metadata**: Timestamps, categories, source attribution

### Limitations

- ⚠️ **Rate limits**: 60 req/min on free tier (300 req/min on paid)
- ⚠️ **Historical depth**: Free tier limited to recent news (30 days)
- ⚠️ **No sentiment scores**: Raw news only, no built-in sentiment analysis

---

## API Specifications

### Endpoint

```
GET https://finnhub.io/api/v1/company-news
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | Yes | Stock ticker symbol (e.g., "AAPL") |
| `from` | string | Yes | Start date (YYYY-MM-DD) |
| `to` | string | Yes | End date (YYYY-MM-DD) |
| `token` | string | Yes | API key |

### Rate Limits

| Tier | Requests/Minute | Requests/Month |
|------|-----------------|----------------|
| **Free** | 60 | ~2.6 million |
| Starter ($19.99/mo) | 300 | 12.9 million |
| Developer ($39.99/mo) | 300 | 12.9 million |

---

## Response Format

### Example Response

```json
[
  {
    "category": "company news",
    "datetime": 1605543726,
    "headline": "Apple Unveils New MacBook Pro with M1 Chip",
    "id": 85951641,
    "image": "https://image.finnhub.io/...",
    "related": "AAPL",
    "source": "SeekingAlpha",
    "summary": "Apple announced the new MacBook Pro featuring the M1 chip...",
    "url": "https://seekingalpha.com/..."
  },
  {
    "category": "company news",
    "datetime": 1605543726,
    "headline": "Apple's Services Revenue Hits Record High",
    "id": 85951642,
    "image": "https://image.finnhub.io/...",
    "related": "AAPL",
    "source": "Bloomberg",
    "summary": "Apple's services division posted record revenue...",
    "url": "https://bloomberg.com/..."
  }
]
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | News category (e.g., "company news", "top news") |
| `datetime` | integer | Unix timestamp (seconds since epoch) |
| `headline` | string | Article headline/title |
| `id` | integer | Unique article identifier |
| `image` | string | URL to article thumbnail image |
| `related` | string | Related ticker symbol |
| `source` | string | News source name (e.g., "Bloomberg", "Reuters") |
| `summary` | string | Article summary/description |
| `url` | string | Link to full article |

---

## ICE Integration

### Implementation Location

**File**: `updated_architectures/implementation/data_ingestion.py`
**Lines**: 872-888

### Fetch Logic

```python
# Finnhub - Real-time news (Priority #1)
if self.config.is_api_available('finnhub'):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        url = "https://finnhub.io/api/v1/company-news"
        params = {
            'symbol': symbol,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'token': self.config.api_keys['finnhub']
        }

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        for article in data[:limit]:
            # Create structured document with metadata
            doc = {
                'content': f"{article['headline']}\n\n{article['summary']}\n\nSource: {article['source']}",
                'source': 'finnhub',
                'file_path': f"finnhub:{symbol}_{article['id']}",
                'freshness': 'real-time',
                'tier': 1,  # Real-time tier
                'premium': False
            }
            documents.append(doc)
    except Exception as e:
        logger.warning(f"Finnhub failed: {e}")
```

### Metadata Schema

ICE enriches Finnhub articles with:

```python
{
    'content': str,              # "Headline\n\nSummary\n\nSource: SourceName"
    'source': 'finnhub',         # Always 'finnhub'
    'file_path': str,            # "finnhub:AAPL_85951641"
    'freshness': 'real-time',    # Always 'real-time'
    'tier': 1,                   # Always 1 (real-time)
    'relevance_score': float,    # 12.0 (base 10.0 × 1.2 source weight)
    'premium': False             # Always False (not premium)
}
```

---

## Configuration

### Enable in ICE

**File**: `ice_building_workflow.ipynb` Cell 14

```python
# News APIs (4 sources)
finnhub_enabled = True  # Enable Finnhub
```

### Set API Key

**File**: `.env`

```bash
FINNHUB_API_KEY=your_api_key_here
```

**Get API Key**: https://finnhub.io/register

---

## Usage Patterns

### 1. Live Trading Context

```python
# Real-time news for intraday monitoring
news = ingester.fetch_company_news('NVDA', limit=5, context='live')

# Finnhub prioritized (real-time)
# Result: Latest breaking news, high relevance scores
```

### 2. Portfolio Analysis Context

```python
# Daily portfolio review
news = ingester.fetch_company_news('AAPL', limit=10, context='portfolio')

# Finnhub included with high priority
# Result: Recent news with moderate relevance scores
```

### 3. Historical Research Context

```python
# Due diligence for new position
news = ingester.fetch_company_news('TSLA', limit=20, context='research')

# Finnhub included alongside all sources
# Result: Balanced mix of real-time and delayed sources
```

---

## Scoring & Prioritization

### Source Quality Weight

**Finnhub**: 1.2x (second highest after Benzinga)

### Example Scores

| Context | Base | Source Weight | Tier Penalty | Final Score |
|---------|------|---------------|--------------|-------------|
| Live | 10.0 | 1.2 | 1.0 | **12.0** |
| Portfolio | 10.0 | 1.2 | 1.0 | **12.0** |
| Research | 10.0 | 1.2 | 1.0 | **12.0** |
| Sentiment | 10.0 | 1.2 | 1.0 | **12.0** |

**Ranking**: 2nd (after Benzinga premium 19.5, before MarketAux 10.0, NewsAPI 3.5-7.0)

---

## Best Practices

### 1. Date Range Optimization

```python
# ✅ Good: 30-day window (balances coverage vs rate limits)
start_date = datetime.now() - timedelta(days=30)

# ❌ Avoid: 1-year window (wastes rate limit, exceeds free tier historical depth)
start_date = datetime.now() - timedelta(days=365)
```

### 2. Rate Limit Management

```python
# Monitor usage
# Free tier: 60 req/min
# Typical ICE usage: 1-3 req/run (portfolio of 1-10 stocks)
# Safe margin: Can handle 20+ stocks per minute
```

### 3. Error Handling

```python
# Graceful degradation (already implemented)
try:
    # Fetch Finnhub news
except Exception as e:
    logger.warning(f"Finnhub failed: {e}")
    # Continue with other sources (MarketAux, Benzinga, NewsAPI)
```

---

## Advantages in ICE Architecture

### vs NewsAPI.org
- ✅ **Real-time** (no 24hr delay)
- ✅ **Better quality** (curated financial sources)
- ✅ **Higher scoring** (1.2x vs 0.7x source weight)

### vs Benzinga
- ✅ **Free tier** (vs premium only)
- ✅ **Higher rate limit** (60 vs varies)
- ❌ **No sentiment** (Benzinga has built-in sentiment)

### vs MarketAux
- ✅ **Higher quality** (1.2x vs 1.0x source weight)
- ✅ **More reliable** (established provider)
- ❌ **Rate limited** (MarketAux unlimited free)

---

## Troubleshooting

### Issue: "401 Unauthorized"
**Cause**: Invalid or missing API key
**Fix**:
```bash
# Check .env file
echo $FINNHUB_API_KEY

# Verify key at https://finnhub.io/dashboard
```

### Issue: "429 Too Many Requests"
**Cause**: Exceeded 60 req/min rate limit
**Fix**:
```python
# Add delay between requests (already handled by ICE)
# Or upgrade to paid tier (300 req/min)
```

### Issue: "Empty response []"
**Cause**: No news in date range or invalid ticker
**Fix**:
```python
# Verify ticker symbol is valid
# Check date range (free tier: recent 30 days only)
# Verify stock has news coverage (small caps may have gaps)
```

---

## Additional Resources

- **Official Docs**: https://finnhub.io/docs/api/company-news
- **API Dashboard**: https://finnhub.io/dashboard
- **Pricing**: https://finnhub.io/pricing
- **Support**: support@finnhub.io

---

**Last Updated**: 2025-11-16
**ICE Integration**: ✅ Active (Priority #1)
**Recommendation**: ⭐⭐⭐⭐⭐ Best free real-time source
