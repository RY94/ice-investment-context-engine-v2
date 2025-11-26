# Benzinga API - Premium Professional News & Sentiment

**Provider**: Benzinga.com
**Tier**: 1 (Real-time)
**Cost**: Premium only (no free tier)
**Status**: ⚠️ Configured but disabled (requires paid subscription)
**Priority**: #3 (Would fetch third if enabled)

---

## Overview

Benzinga provides professional-grade financial news, analyst ratings, and sentiment analysis. **Premium only** - no free tier available, but offers highest quality news with built-in sentiment scores and analyst ratings.

### Key Strengths

- ✅ **Professional quality**: Curated by financial journalists
- ✅ **Real-time delivery**: Breaking news as it happens
- ✅ **Analyst ratings**: Upgrade/downgrade signals with targets
- ✅ **Sentiment analysis**: Professional-grade sentiment scores
- ✅ **Comprehensive metadata**: Rich tagging (topics, sectors, events)
- ✅ **Exclusive content**: Original Benzinga research and analysis

### Limitations

- ❌ **No free tier**: Requires paid subscription ($varies/month)
- ❌ **Cost**: Premium pricing for boutique hedge funds
- ⚠️ **Rate limits**: Vary by subscription tier
- ⚠️ **Integration issues**: Current implementation not working

---

## API Specifications

### Endpoint

```
GET https://api.benzinga.com/api/v2/news
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | API key |
| `tickers` | string | No | Ticker symbols (comma-separated) |
| `pageSize` | integer | No | Number of results (default: 15, max: 100) |
| `date` | string | No | Specific date (YYYY-MM-DD) |
| `dateFrom` | string | No | Start date (YYYY-MM-DD) |
| `dateTo` | string | No | End date (YYYY-MM-DD) |
| `channels` | string | No | Filter by channel (news, analyst-ratings, etc.) |

### Rate Limits

| Tier | Requests/Month | Cost |
|------|----------------|------|
| Starter | Varies | Contact sales |
| Professional | Varies | Contact sales |
| Enterprise | Varies | Custom pricing |

**Pricing**: Contact Benzinga sales (typically $hundreds/month for hedge fund tier)

---

## Response Format

### Example Response

```json
[
  {
    "id": "27834567",
    "author": "Benzinga News Desk",
    "created": "2024-11-15T14:30:00Z",
    "updated": "2024-11-15T14:30:00Z",
    "title": "Apple Shares Surge On AI iPhone Announcement",
    "teaser": "Apple Inc. shares jumped 3% after unveiling new AI-powered iPhone features...",
    "body": "Full article content...",
    "url": "https://www.benzinga.com/...",
    "image": [
      {
        "size": "large",
        "url": "https://cdn.benzinga.com/..."
      }
    ],
    "channels": ["News", "Tech"],
    "stocks": ["AAPL"],
    "tags": ["Apple", "iPhone", "AI", "Technology"]
  }
]
```

### Analyst Ratings Example

```json
{
  "analyst_ratings": [
    {
      "id": "12345",
      "date": "2024-11-15",
      "time": "14:30:00",
      "ticker": "AAPL",
      "analyst": "Morgan Stanley",
      "analyst_name": "Katy Huberty",
      "rating_current": "Overweight",
      "rating_prior": "Equal-Weight",
      "action": "Upgrade",
      "pt_current": 200.00,
      "pt_prior": 175.00,
      "url": "https://www.benzinga.com/..."
    }
  ]
}
```

---

## ICE Integration

### Implementation Location

**File**: `updated_architectures/implementation/data_ingestion.py`
**Lines**: 909-927 (Configured but not active)

### Planned Fetch Logic

```python
# Benzinga - Premium professional news (Priority #3)
if self.config.is_api_available('benzinga'):
    try:
        url = "https://api.benzinga.com/api/v2/news"
        params = {
            'token': self.config.api_keys['benzinga'],
            'tickers': symbol,
            'pageSize': limit
        }

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        for article in data:
            # Create structured document with premium flag
            doc = {
                'content': f"{article['title']}\n\n{article['teaser']}\n\n{article.get('body', '')}\n\nSource: Benzinga",
                'source': 'benzinga',
                'file_path': f"benzinga:{symbol}_{article['id']}",
                'freshness': 'real-time',
                'tier': 1,  # Real-time tier
                'premium': True,  # Premium content flag
                'channels': article.get('channels', [])  # Extra metadata
            }
            documents.append(doc)
    except Exception as e:
        logger.warning(f"Benzinga failed: {e}")
```

### Metadata Schema (Planned)

```python
{
    'content': str,              # "Title\n\nTeaser\n\nBody\n\nSource: Benzinga"
    'source': 'benzinga',        # Always 'benzinga'
    'file_path': str,            # "benzinga:AAPL_27834567"
    'freshness': 'real-time',    # Always 'real-time'
    'tier': 1,                   # Always 1 (real-time)
    'relevance_score': float,    # 19.5 (10.0 × 1.5 × 1.0 × 1.3 premium boost)
    'premium': True,             # Always True (premium content)
    'channels': list             # ['News', 'Tech'] (BONUS)
}
```

---

## Configuration

### Enable in ICE

**File**: `ice_building_workflow.ipynb` Cell 14

```python
# News APIs (4 sources)
benzinga_enabled = False  # Disabled (requires premium subscription)
```

### Set API Key

**File**: `.env`

```bash
BENZINGA_API_KEY=your_api_key_here
```

**Get API Key**: Contact Benzinga sales at https://www.benzinga.com/apis

---

## Scoring & Prioritization

### Source Quality Weight

**Benzinga**: 1.5x (highest among all sources)

### Premium Boost

**Premium Content**: Additional 30% boost (+1.3x multiplier)

### Scores

| Context | Base | Source Weight | Tier Penalty | Premium Boost | Final Score | Rank |
|---------|------|---------------|--------------|---------------|-------------|------|
| Live | 10.0 | 1.5 | 1.0 | 1.3 | **19.5** | 1st |
| Portfolio | 10.0 | 1.5 | 1.0 | 1.3 | **19.5** | 1st |
| Research | 10.0 | 1.5 | 1.0 | 1.3 | **19.5** | 1st |
| Sentiment | 10.0 | 1.5 | 1.0 | 1.3 | **19.5** | 1st |

**Ranking** (if enabled):
- **Benzinga premium: 19.5 (1st - HIGHEST)**
- Finnhub: 12.0 (2nd)
- MarketAux: 10.0 (3rd)
- NewsAPI: 3.5-7.0 (4th)

---

## Unique Features

### 1. Analyst Ratings & Price Targets

```python
# Separate endpoint for analyst ratings
ratings = benzinga.analyst_ratings(ticker='AAPL')

# Extracts:
# - Upgrades/downgrades (Overweight → Outperform)
# - Price target changes ($175 → $200)
# - Analyst firm (Morgan Stanley, Goldman Sachs)
```

**Use Case**: Track consensus changes, identify inflection points

### 2. Professional Sentiment Scores

```python
# Built-in sentiment analysis by financial journalists
article['sentiment'] = {
    'score': 0.85,  # -1.0 to 1.0
    'label': 'positive'
}
```

**Use Case**: Sentiment trend analysis, contrarian signals

### 3. Event Categorization

```python
# Articles tagged by event type
article['channels'] = [
    'Earnings',       # Earnings announcements
    'M&A',            # Mergers & acquisitions
    'FDA',            # FDA approvals (biotech)
    'Analyst Ratings' # Analyst upgrades/downgrades
]
```

**Use Case**: Filter for material events only

---

## Business Value Proposition

### Cost-Benefit Analysis

**Cost**: ~$300-500/month (estimated for hedge fund tier)

**Benefits**:
- ✅ Highest quality news (1.5x source weight = 50% more relevant than baseline)
- ✅ Analyst ratings tracking (valuable for signal generation)
- ✅ Professional sentiment (more accurate than algorithmic sentiment)
- ✅ Exclusive content (competitive edge)

**Break-Even Analysis**:
```
Monthly cost: $400
Value of one good trade: $10,000+ (1% on $1M position)
Required: 1 good trade every 25 months to break even
Realistic: 1-2 trades/month benefit from exclusive insights
ROI: Positive if news contributes to 0.04% of monthly returns
```

**Recommendation**: Consider for funds >$10M AUM where $400/mo is <0.005% of AUM

---

## Integration Issues

### Current Status

⚠️ **Not Working** in ICE implementation

### Known Problems

1. **No API Key**: Free tier unavailable, paid tier not subscribed
2. **Authentication**: Requires valid Benzinga API token
3. **Endpoint Changes**: API may have updated since initial integration

### Resolution Path

1. **Evaluate necessity**: Compare Finnhub vs Benzinga for specific use case
2. **Cost analysis**: Calculate expected ROI from premium content
3. **Trial period**: Request trial access from Benzinga sales
4. **Integration testing**: Verify current API schema before subscribing

---

## Best Practices (If Enabled)

### 1. Prioritize Analyst Ratings

```python
# Fetch ratings separately
ratings = benzinga.analyst_ratings(
    tickers='AAPL',
    dateFrom='2024-11-01',
    dateTo='2024-11-15'
)

# Store in Signal Store for query routing
for rating in ratings:
    signal_store.insert_rating(
        ticker=rating['ticker'],
        analyst=rating['analyst'],
        rating=rating['rating_current'],
        price_target=rating['pt_current']
    )
```

### 2. Use Event Filters

```python
# Only fetch material events
news = benzinga.news(
    tickers='TSLA',
    channels='Earnings,M&A,Analyst Ratings'  # Skip general news
)
```

### 3. Combine with Free Sources

```python
# Use Benzinga for quality, Finnhub for volume
# ICE automatically combines both when both enabled
# Benzinga articles rank higher (19.5 vs 12.0 scores)
```

---

## Comparison with Competitors

### vs Finnhub
- ✅ **Higher quality** (1.5x vs 1.2x source weight)
- ✅ **Analyst ratings** (Finnhub no ratings)
- ✅ **Professional sentiment** (Finnhub no sentiment)
- ❌ **No free tier** (Finnhub 60 req/min free)
- ❌ **More expensive** ($400/mo vs $0)

### vs MarketAux
- ✅ **Higher quality** (1.5x vs 1.0x source weight)
- ✅ **Professional sentiment** (MarketAux algorithmic)
- ✅ **Analyst ratings** (MarketAux no ratings)
- ❌ **No free tier** (MarketAux unlimited free)
- ❌ **Much more expensive** ($400/mo vs $0)

### vs Bloomberg Terminal
- ✅ **Lower cost** ($400/mo vs $2,000/mo)
- ✅ **API access** (Bloomberg limited API)
- ❌ **Less comprehensive** (Bloomberg has everything)
- ❌ **Fewer features** (Bloomberg includes data, analytics, messaging)

---

## Troubleshooting

### Issue: "403 Forbidden"
**Cause**: Invalid API key or expired subscription
**Fix**: Contact Benzinga to verify subscription status

### Issue: "429 Too Many Requests"
**Cause**: Exceeded rate limit for subscription tier
**Fix**: Upgrade tier or reduce request frequency

### Issue: "Empty response array"
**Cause**: No news for ticker or date range out of subscription limits
**Fix**: Verify ticker coverage, check subscription tier's historical depth

---

## Future Enhancements

### Phase 1: Analyst Ratings Integration (HIGH Priority)

**Tasks**:
1. Add `fetch_analyst_ratings()` method
2. Store ratings in Signal Store
3. Create rating change signals (upgrade/downgrade)
4. Add to query router patterns

**Estimated Effort**: 3-4 hours
**Expected Value**: High (analyst ratings are alpha-generating signals)

### Phase 2: Sentiment Trend Tracking (MEDIUM Priority)

**Tasks**:
1. Extract sentiment scores from Benzinga articles
2. Calculate rolling sentiment averages
3. Detect sentiment inflection points
4. Build sentiment-based queries

**Estimated Effort**: 2-3 hours
**Expected Value**: Medium (sentiment trends complement technical analysis)

---

## Additional Resources

- **Official Docs**: https://www.benzinga.com/apis/docs
- **Pricing**: https://www.benzinga.com/apis/pricing
- **Sales Contact**: apisales@benzinga.com
- **Sample Data**: Request via sales team

---

**Last Updated**: 2025-11-16
**ICE Integration**: ⚠️ Configured but disabled (premium only)
**Recommendation**: ⭐⭐⭐⭐⭐ Best quality, evaluate ROI for fund size
**Action Required**: Cost-benefit analysis, consider for funds >$10M AUM
