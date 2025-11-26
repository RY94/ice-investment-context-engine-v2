# NEWS API Key Setup Guide - Complete Instructions

**Created**: 2025-11-16
**Purpose**: Step-by-step guide to enable multi-source NEWS API coverage in ICE
**Status**: ✅ Production-ready instructions

---

## Overview

ICE integrates 4 NEWS APIs with smart proportional distribution. By default, only Finnhub is configured (free tier, no credit card required). This guide helps you add the other 3 APIs for maximum news coverage.

### Current Status (Default)
- ✅ **Finnhub**: Configured (free tier, 60 req/min)
- ❌ **NewsAPI.org**: Not configured (free tier available)
- ❌ **MarketAux**: Not configured (free tier: 100/month, paid: $29/month)
- ❌ **Benzinga**: Not configured (paid only: $99-500/month)

### Target Status (Full Coverage)
- ✅ **All 4 APIs** configured
- ✅ **Proportional distribution** across sources
- ✅ **Premium coverage** with professional-grade sources

---

## Quick Start

### Step 1: Check Current Configuration

```bash
cd "updated_architectures/implementation"
python config.py
```

**Expected output**:
```
✅ OPENAI_API_KEY configured
Available API services: 1
  - finnhub ✅
```

---

## API-by-API Setup Instructions

### 1. NewsAPI.org (FREE - Recommended First)

**Tier**: 2 (Delayed 24 hours)
**Cost**: FREE (1,000 requests/day)
**Best for**: Research context, historical analysis, broad coverage

#### Signup Process
1. Go to: https://newsapi.org/register
2. Fill in:
   - Email address
   - Password
   - First/Last name
3. Click "Submit"
4. Check email for API key

#### Add to .env
```bash
# Open .env file (create if doesn't exist)
nano .env

# Add this line:
NEWSAPI_ORG_API_KEY=your-actual-api-key-here
```

#### Verify
```bash
python config.py
# Should now show: finnhub, newsapi
```

**Source Weight**: 0.7x
**Expected Score** (research context): 6.3
**Articles per 10-limit**: ~2-3

---

### 2. MarketAux (FREE TIER AVAILABLE)

**Tier**: 1 (Real-time)
**Cost**:
- FREE: 100 requests/month
- PAID: $29/month for unlimited
**Best for**: NLP entity extraction, sentiment indicators

#### Signup Process
1. Go to: https://www.marketaux.com/account/signup
2. Fill in:
   - Email address
   - Password
   - Use case: "Personal research"
3. Verify email
4. Log in and navigate to: https://www.marketaux.com/account/api
5. Copy your API key

#### Free Tier Limits
- 100 API calls per month
- 3 news articles per call
- Full feature access

#### Paid Tier ($29/month)
- Unlimited API calls
- 100 articles per call
- Priority support

#### Add to .env
```bash
# Open .env file
nano .env

# Add this line:
MARKETAUX_API_KEY=your-actual-api-key-here
```

#### Verify
```bash
python config.py
# Should now show: finnhub, newsapi, marketaux
```

**Source Weight**: 1.0x (baseline)
**Expected Score**: 10.0
**Articles per 10-limit**: ~2-3
**Special Features**:
- NLP entity extraction
- Sentiment scores (-1.0 to 1.0)
- Topic categorization

---

### 3. Benzinga (PAID ONLY - Premium)

**Tier**: 1 (Real-time)
**Cost**: $99-500/month (varies by plan)
**Best for**: Professional trading, analyst ratings, sentiment analysis

⚠️ **Note**: Benzinga requires a paid subscription. Free tier not available.

#### Pricing Tiers

| Plan | Cost/Month | Features |
|------|------------|----------|
| **Newsfeed Lite** | $99 | Real-time news, basic sentiment |
| **Newsfeed Pro** | $249 | + Analyst ratings, price targets |
| **Newsfeed Premium** | $499 | + Calendar events, full API access |

#### Signup Process
1. Go to: https://www.benzinga.com/apis/en
2. Click "Get Started" or "Contact Sales"
3. Choose plan based on needs
4. Complete payment (credit card required)
5. Receive API token via email

#### Add to .env
```bash
# Open .env file
nano .env

# Add this line:
BENZINGA_API_TOKEN=your-actual-api-token-here
```

#### Verify
```bash
python config.py
# Should now show: finnhub, newsapi, marketaux, benzinga
```

**Source Weight**: 1.5x (highest quality)
**Expected Score**: 19.5 (with premium boost)
**Articles per 10-limit**: ~3-4
**Special Features**:
- Professional sentiment analysis
- Analyst ratings and price targets
- Event categorization (earnings, M&A, FDA, etc.)
- Premium content flag

---

## Configuration File (.env)

### Complete Example

```bash
# OpenAI (Required for LightRAG)
OPENAI_API_KEY=sk-your-openai-key-here

# NEWS APIs
FINNHUB_API_KEY=your-finnhub-key-here           # FREE (60 req/min)
NEWSAPI_ORG_API_KEY=your-newsapi-key-here       # FREE (1000/day)
MARKETAUX_API_KEY=your-marketaux-key-here       # FREE (100/month) or PAID ($29/mo)
BENZINGA_API_TOKEN=your-benzinga-token-here     # PAID ($99-500/mo)

# Other APIs (Optional)
ALPHA_VANTAGE_API_KEY=your-alphavantage-key-here
FMP_API_KEY=your-fmp-key-here
POLYGON_API_KEY=your-polygon-key-here
```

### Security Best Practices

1. **Never commit .env file to git**
   ```bash
   # .env is already in .gitignore, verify:
   cat .gitignore | grep .env
   # Should show: .env
   ```

2. **Use environment variables in production**
   ```bash
   export NEWSAPI_ORG_API_KEY="your-key"
   ```

3. **Rotate keys regularly**
   - Every 90 days for free tiers
   - Every 30 days for paid tiers

---

## Testing Your Setup

### Step 1: Verify Configuration

```bash
cd updated_architectures/implementation
python config.py
```

**Expected output** (with all 4 APIs):
```
✅ OPENAI_API_KEY configured
Available API services: 4
  - finnhub ✅
  - newsapi ✅
  - marketaux ✅
  - benzinga ✅
```

### Step 2: Test in Notebook

Open `ice_building_workflow.ipynb` and run Cell 15 (ingestion cell).

**Expected log output**:
```
📊 AAPL: Distributing quota=12 across 4 sources (base=3)
📰 AAPL: Fetching 3 from finnhub...
  ✅ finnhub: 3 unique (0 duplicates removed)
📰 AAPL: Fetching 3 from marketaux...
  ✅ marketaux: 3 unique (0 duplicates removed)
📰 AAPL: Fetching 3 from benzinga...
  ✅ benzinga: 3 unique (0 duplicates removed)
📰 AAPL: Fetching 3 from newsapi...
  ✅ newsapi: 2 unique (1 duplicates removed)
📊 AAPL: Returning 10 unique articles from 4 sources
```

### Step 3: Verify Article Distribution

**Expected metadata** (Cell 15 output):
```python
# Article 1
{'source': 'benzinga', 'tier': 1, 'relevance_score': 19.5, 'premium': True}

# Article 2
{'source': 'finnhub', 'tier': 1, 'relevance_score': 12.0}

# Article 3
{'source': 'marketaux', 'tier': 1, 'relevance_score': 10.0}

# Article 4
{'source': 'newsapi', 'tier': 2, 'relevance_score': 6.3, 'delay_warning': True}
```

---

## Cost Analysis

### Recommended Setup for Boutique Hedge Funds (<$100M AUM)

**Tier 1: Free (Minimal Coverage)**
- Finnhub: FREE (60 req/min)
- NewsAPI: FREE (1000/day)
- **Total**: $0/month
- **Coverage**: ~60% (2 sources, delayed data)

**Tier 2: Budget (Good Coverage)**
- Finnhub: FREE
- NewsAPI: FREE
- MarketAux: $29/month (unlimited)
- **Total**: $29/month
- **Coverage**: ~85% (3 sources, real-time + delayed)

**Tier 3: Professional (Maximum Coverage)**
- Finnhub: FREE
- NewsAPI: FREE
- MarketAux: $29/month
- Benzinga Lite: $99/month
- **Total**: $128/month
- **Coverage**: ~100% (4 sources, premium quality)

**Tier 4: Premium (Institutional Grade)**
- Finnhub: FREE
- NewsAPI: FREE
- MarketAux: $29/month
- Benzinga Pro: $249/month
- **Total**: $278/month
- **Coverage**: 100% + analyst ratings + price targets

### ROI Calculation

**For $10M AUM fund**:
- Professional tier: $128/month = $1,536/year
- As % of AUM: 0.015%
- **Conclusion**: Negligible cost for comprehensive market intelligence

**For $50M AUM fund**:
- Premium tier: $278/month = $3,336/year
- As % of AUM: 0.007%
- **Conclusion**: Highly cost-effective for institutional-grade data

---

## Troubleshooting

### Issue: "No news APIs available"

**Symptom**:
```
⚠️ AAPL: No news APIs available (limit=10). Returning empty list.
```

**Cause**: No API keys configured

**Fix**:
1. Check .env file exists: `ls .env`
2. Verify keys are set: `cat .env | grep API_KEY`
3. Run config test: `python config.py`

### Issue: "Only Finnhub returns articles"

**Symptom**:
```
📊 AAPL: Returning 10 unique articles from 1 sources
```

**Cause**: Other API keys missing or invalid

**Fix**:
1. Verify each API key individually:
   ```bash
   # Test MarketAux
   curl "https://api.marketaux.com/v1/news/all?api_token=YOUR_KEY&symbols=AAPL&limit=1"

   # Test NewsAPI
   curl "https://newsapi.org/v2/everything?q=AAPL&apiKey=YOUR_KEY&pageSize=1"

   # Test Benzinga (requires authentication header)
   curl -H "Authorization: Bearer YOUR_TOKEN" "https://api.benzinga.com/api/v2/news?tickers=AAPL&pageSize=1"
   ```

2. If API returns error, check:
   - Key is correct (no extra spaces)
   - Account is active
   - Free tier limits not exceeded

### Issue: "Articles all from delayed sources"

**Symptom**: All articles have `'tier': 2` and `'delay_warning': True`

**Cause**: Only NewsAPI is configured (24hr delay)

**Fix**: Add MarketAux (free, real-time) or Finnhub API keys

### Issue: "Duplicate articles across sources"

**Symptom**: Same headline appears multiple times

**Expected**: This is normal and handled by deduplication

**Verification**:
- Check log shows "X duplicates removed"
- Final count should be close to limit (e.g., 10)
- Different sources may have same news (expected)

---

## Best Practices

### 1. Start with Free Tiers
- Finnhub: Always use (generous free tier)
- NewsAPI: Add for research context (delayed OK)
- MarketAux: Start with 100 free requests/month
- Benzinga: Only if budget allows ($99+/month)

### 2. Monitor Usage
```bash
# Check API usage in logs
grep "📊.*sources" logs/*.json

# Track monthly costs
# MarketAux: 100 free calls = ~20 portfolio builds
# Benzinga: Unlimited for $99/month
```

### 3. Use Context Parameter Appropriately
```python
# Real-time trading (excludes delayed NewsAPI)
news = fetch_company_news('AAPL', limit=10, context='live')

# Daily analysis (penalizes delayed but includes)
news = fetch_company_news('AAPL', limit=10, context='portfolio')

# Research (treats delayed equally)
news = fetch_company_news('AAPL', limit=10, context='research')
```

### 4. Optimize for Your Use Case

**Intraday Trading**:
- Need: Real-time only
- Setup: Finnhub + MarketAux (+ Benzinga if budget allows)
- Context: `'live'`

**Portfolio Analysis**:
- Need: Recent news (24hr delay OK)
- Setup: All 4 APIs for maximum coverage
- Context: `'portfolio'` or `'research'`

**Due Diligence**:
- Need: Historical depth, broad sources
- Setup: All 4 APIs, prioritize NewsAPI for breadth
- Context: `'research'`

---

## Next Steps

1. ✅ Choose your tier based on budget and needs
2. ✅ Sign up for APIs (start with free tiers)
3. ✅ Add API keys to .env file
4. ✅ Test configuration with `python config.py`
5. ✅ Run notebook Cell 15 to verify multi-source fetching
6. ✅ Monitor usage and upgrade as needed

---

## Support Resources

### Official Documentation
- **Finnhub**: https://finnhub.io/docs/api
- **NewsAPI**: https://newsapi.org/docs
- **MarketAux**: https://www.marketaux.com/documentation
- **Benzinga**: https://docs.benzinga.io/benzinga/

### ICE Documentation
- **Main README**: `/project_information/about_news_apis/README.md`
- **Implementation Guide**: `/project_information/about_news_apis/IMPLEMENTATION.md`
- **Integration Guide**: `/project_information/about_news_apis/INTEGRATION.md`

### Contact
- **Finnhub Support**: support@finnhub.io
- **NewsAPI Support**: support@newsapi.org
- **MarketAux Support**: support@marketaux.com
- **Benzinga Support**: apisupport@benzinga.com

---

**Last Updated**: 2025-11-16
**Status**: ✅ Production-ready
**Maintained By**: ICE Development Team
