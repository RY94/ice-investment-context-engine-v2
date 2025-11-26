# MarketAux API - Real-Time News with NLP Enhancement

**Provider**: MarketAux.com
**Tier**: 1 (Real-time)
**Cost**: Free tier available
**Status**: ⚠️ Configured but not working (API issues)
**Priority**: #2 (Would fetch second if working)

---

## Overview

MarketAux provides real-time financial news enhanced with NLP entity extraction and sentiment indicators. Their free tier offers **unlimited requests**, making it theoretically the best free option. However, current integration has technical issues.

### Key Strengths

- ✅ **Unlimited free tier**: No rate limits on free plan (unique advantage)
- ✅ **Real-time delivery**: No delays, immediate news
- ✅ **NLP entity extraction**: Automatic extraction of tickers, companies, people
- ✅ **Sentiment indicators**: Basic sentiment scores (positive/negative/neutral)
- ✅ **Multiple filters**: Filter by entity type, sentiment, country, language

### Current Limitations

- ❌ **Integration issues**: Not currently working in ICE implementation
- ⚠️ **Free tier restrictions**: Max 100 articles per request
- ⚠️ **Smaller coverage**: Fewer sources than NewsAPI or Finnhub
- ⚠️ **Documentation gaps**: API docs less comprehensive than competitors

---

## API Specifications

### Endpoint

```
GET https://api.marketaux.com/v1/news/all
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbols` | string | No | Ticker symbols (comma-separated, e.g., "AAPL,TSLA") |
| `entity_types` | string | No | Filter by entity type: "equity", "index", "commodity" |
| `sentiment` | string | No | Filter by sentiment: "positive", "negative", "neutral" |
| `api_token` | string | Yes | API key |
| `limit` | integer | No | Number of results (default: 10, max: 100) |
| `published_after` | string | No | Start date (ISO 8601) |
| `published_before` | string | No | End date (ISO 8601) |

### Rate Limits

| Tier | Requests/Month | Articles/Request | Historical Depth | Cost |
|------|----------------|------------------|------------------|------|
| **Free** | Unlimited | 100 | 7 days | $0 |
| Starter | 1,000 | 1,000 | 30 days | $19/mo |
| Professional | 10,000 | 10,000 | 90 days | $49/mo |

---

## Response Format

### Example Response

```json
{
  "meta": {
    "found": 125,
    "returned": 10,
    "limit": 10,
    "page": 1
  },
  "data": [
    {
      "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "Apple Unveils New iPhone with Advanced AI Features",
      "description": "Apple Inc. announced its latest iPhone model featuring enhanced AI capabilities...",
      "keywords": "Apple, iPhone, AI, technology",
      "snippet": "Apple Inc. announced its latest iPhone model...",
      "url": "https://www.reuters.com/...",
      "image_url": "https://images.reuters.com/...",
      "published_at": "2024-11-15T14:30:00.000Z",
      "source": "Reuters",
      "entities": [
        {
          "symbol": "AAPL",
          "name": "Apple Inc.",
          "exchange": "NASDAQ",
          "type": "equity",
          "industry": "Technology"
        }
      ],
      "sentiment": {
        "polarity": 0.75,
        "label": "positive"
      }
    }
  ]
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `uuid` | string | Unique article identifier |
| `title` | string | Article headline |
| `description` | string | Article description/summary |
| `keywords` | string | Comma-separated keywords |
| `snippet` | string | Article excerpt |
| `url` | string | Link to full article |
| `image_url` | string | Article image URL |
| `published_at` | string | Publication timestamp (ISO 8601) |
| `source` | string | News source name |
| `entities` | array | NLP-extracted entities (companies, people, etc.) |
| `sentiment.polarity` | float | Sentiment score (-1.0 to 1.0) |
| `sentiment.label` | string | Sentiment label ("positive", "negative", "neutral") |

---

## ICE Integration

### Implementation Location

**File**: `updated_architectures/implementation/data_ingestion.py`
**Lines**: 890-907 (Configured but not active)

### Planned Fetch Logic

```python
# MarketAux - Real-time news with NLP (Priority #2)
if self.config.is_api_available('marketaux'):
    try:
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            'symbols': symbol,
            'api_token': self.config.api_keys['marketaux'],
            'limit': limit,
            'entity_types': 'equity'  # Focus on stocks
        }

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        for article in data.get('data', []):
            # Create structured document with NLP metadata
            doc = {
                'content': f"{article['title']}\n\n{article['description']}\n\nSource: {article['source']}",
                'source': 'marketaux',
                'file_path': f"marketaux:{symbol}_{article['uuid']}",
                'freshness': 'real-time',
                'tier': 1,  # Real-time tier
                'premium': False,
                'sentiment': article.get('sentiment', {}).get('label', 'neutral')  # Extra metadata
            }
            documents.append(doc)
    except Exception as e:
        logger.warning(f"MarketAux failed: {e}")
```

### Metadata Schema (Planned)

```python
{
    'content': str,              # "Title\n\nDescription\n\nSource: SourceName"
    'source': 'marketaux',       # Always 'marketaux'
    'file_path': str,            # "marketaux:AAPL_uuid"
    'freshness': 'real-time',    # Always 'real-time'
    'tier': 1,                   # Always 1 (real-time)
    'relevance_score': float,    # 10.0 (base 10.0 × 1.0 source weight)
    'premium': False,            # Always False
    'sentiment': str             # 'positive', 'negative', 'neutral' (BONUS)
}
```

---

## Configuration

### Enable in ICE

**File**: `ice_building_workflow.ipynb` Cell 14

```python
# News APIs (4 sources)
marketaux_enabled = False  # Currently disabled (integration issues)
```

### Set API Key

**File**: `.env`

```bash
MARKETAUX_API_KEY=your_api_key_here
```

**Get API Key**: https://www.marketaux.com/account/signup

---

## Scoring & Prioritization

### Source Quality Weight

**MarketAux**: 1.0x (baseline)

### Planned Scores

| Context | Base | Source Weight | Tier Penalty | Final Score | Rank |
|---------|------|---------------|--------------|-------------|------|
| Live | 10.0 | 1.0 | 1.0 | **10.0** | 3rd |
| Portfolio | 10.0 | 1.0 | 1.0 | **10.0** | 3rd |
| Research | 10.0 | 1.0 | 1.0 | **10.0** | 3rd |
| Sentiment | 10.0 | 1.0 | 1.0 | **10.0** | 3rd |

**Planned Ranking** (if working):
- Benzinga premium: 19.5 (1st)
- Finnhub: 12.0 (2nd)
- **MarketAux: 10.0 (3rd)**
- NewsAPI: 3.5-7.0 (4th)

---

## Unique Advantages

### 1. NLP Entity Extraction

```json
// Automatic extraction of mentioned entities
"entities": [
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    "type": "equity"
  },
  {
    "symbol": "MSFT",
    "name": "Microsoft Corporation",
    "exchange": "NASDAQ",
    "type": "equity"
  }
]
```

**Use Case**: Discover related companies mentioned in news (e.g., Apple article mentions supplier TSMC)

### 2. Built-In Sentiment Scores

```json
// Sentiment analysis included
"sentiment": {
  "polarity": 0.75,   // -1.0 (very negative) to 1.0 (very positive)
  "label": "positive"
}
```

**Use Case**: Filter for positive/negative news, sentiment trend analysis

### 3. Unlimited Free Tier

**MarketAux**: Unlimited requests (vs Finnhub 60/min, NewsAPI 1000/day)

**Use Case**: High-volume analysis, multiple portfolio scans, historical backtesting

---

## Integration Issues

### Current Status

⚠️ **Not Working** in ICE implementation

### Known Problems

1. **API Response Format**: Response structure may have changed since initial integration
2. **Authentication**: API key validation issues
3. **Rate Limiting**: Possible undocumented throttling despite "unlimited" claim

### Debugging Steps

```python
# Test MarketAux API directly
import requests

url = "https://api.marketaux.com/v1/news/all"
params = {
    'symbols': 'AAPL',
    'api_token': 'YOUR_API_KEY',
    'limit': 10
}

response = requests.get(url, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

**Expected Issues**:
- 401 Unauthorized (API key problem)
- 429 Too Many Requests (rate limiting)
- Empty response (no articles for ticker)

---

## Best Practices (When Working)

### 1. Leverage NLP Entities

```python
# Find articles mentioning multiple tickers
params = {
    'symbols': 'AAPL,TSMC,NVDA',  # Comma-separated
    'entity_types': 'equity'
}
```

### 2. Filter by Sentiment

```python
# Only positive news
params = {
    'symbols': 'TSLA',
    'sentiment': 'positive'
}

# Only negative news (for risk monitoring)
params = {
    'symbols': 'NVDA',
    'sentiment': 'negative'
}
```

### 3. Combine with Finnhub

```python
# Use MarketAux for volume/sentiment, Finnhub for quality
# ICE automatically combines both if both enabled
```

---

## Future Enhancements

### Phase 1: Fix Integration (Priority: HIGH)

**Tasks**:
1. Debug API response parsing
2. Verify API key configuration
3. Test with current API version
4. Update integration code if schema changed

**Estimated Effort**: 1-2 hours

### Phase 2: Sentiment Integration (Priority: MEDIUM)

**Tasks**:
1. Extract sentiment scores from MarketAux responses
2. Store sentiment in Signal Store
3. Create sentiment trend indicators
4. Add sentiment-based query routing

**Estimated Effort**: 2-3 hours

### Phase 3: Entity Graph Enhancement (Priority: LOW)

**Tasks**:
1. Use MarketAux entities to discover related companies
2. Build entity relationship graph
3. Enhance LightRAG with co-mention signals

**Estimated Effort**: 4-6 hours

---

## Comparison with Competitors

### vs Finnhub
- ✅ **Unlimited requests** (Finnhub 60/min)
- ✅ **Built-in NLP** (Finnhub raw news only)
- ✅ **Sentiment scores** (Finnhub no sentiment)
- ❌ **Lower quality** (1.0x vs 1.2x source weight)
- ❌ **Integration issues** (Finnhub works reliably)

### vs Benzinga
- ✅ **Free tier** (Benzinga premium only)
- ✅ **Unlimited requests** (Benzinga varies)
- ❌ **No professional-grade sentiment** (Benzinga has analyst ratings)
- ❌ **Smaller source coverage** (Benzinga broader financial sources)

### vs NewsAPI.org
- ✅ **Real-time** (NewsAPI 24hr delay)
- ✅ **NLP extraction** (NewsAPI raw aggregation)
- ✅ **Sentiment scores** (NewsAPI no sentiment)
- ❌ **Smaller coverage** (NewsAPI 80,000 sources)

---

## Troubleshooting

### Issue: "401 Unauthorized"
**Possible Causes**:
- Invalid or expired API key
- API key not activated
- Free tier disabled for new accounts

**Fix**:
```bash
# Verify API key at https://www.marketaux.com/account
# Check account status (free tier active?)
# Generate new API key if needed
```

### Issue: "Empty 'data' array"
**Possible Causes**:
- No news for ticker in last 7 days (free tier limit)
- Invalid ticker symbol
- Ticker not covered by MarketAux

**Fix**:
```python
# Try well-known ticker (AAPL, TSLA, NVDA)
# Check published_after/published_before dates
# Verify ticker symbol spelling
```

### Issue: "Integration not working"
**Possible Causes**:
- API schema changed (response format different)
- Code bug in integration layer
- Network/timeout issues

**Fix**:
```python
# Test API directly (curl or requests)
# Check ICE logs for specific error messages
# Compare current response vs expected schema
```

---

## Additional Resources

- **Official Docs**: https://www.marketaux.com/documentation
- **API Dashboard**: https://www.marketaux.com/account
- **Pricing**: https://www.marketaux.com/pricing
- **Support**: support@marketaux.com

---

**Last Updated**: 2025-11-16
**ICE Integration**: ⚠️ Configured but not working
**Recommendation**: ⭐⭐⭐⭐ High potential once integration fixed
**Action Required**: Debug and fix integration issues
