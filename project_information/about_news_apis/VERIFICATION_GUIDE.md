# NEWS API Verification & Testing Guide

**Created**: 2025-11-16
**Last Updated**: 2025-11-17
**Purpose**: Quick commands to verify multi-source NEWS API setup
**Status**: ✅ Production-ready

---

## Quick Verification Commands

### Step 1: Check Configuration

```bash
cd updated_architectures/implementation
python config.py
```

**Expected output** (with all APIs configured):
```
✅ OPENAI_API_KEY is set
API services configured: 4
Available services: finnhub, newsapi, marketaux, benzinga
```

**Troubleshooting**:
- If shows 1 service → Only Finnhub configured (add other API keys to .env)
- If shows 0 services → Check .env file exists and has valid keys

---

### Step 2: Test Individual APIs

#### Test Finnhub
```bash
# Replace YOUR_KEY with actual key from .env
curl "https://finnhub.io/api/v1/company-news?symbol=AAPL&from=2025-10-01&to=2025-11-16&token=YOUR_KEY"
```

**Expected**: JSON array with news articles

**If fails**: Check key is correct, no extra spaces, account is active

#### Test NewsAPI
```bash
curl "https://newsapi.org/v2/everything?q=Apple&apiKey=YOUR_KEY&pageSize=5"
```

**Expected**: JSON with `"status": "ok"` and articles array

**If fails**: Free tier has 24hr delay, check error message for details

#### Test MarketAux
```bash
curl "https://api.marketaux.com/v1/news/all?api_token=YOUR_KEY&symbols=AAPL&limit=5"
```

**Expected**: JSON with `"data"` array

**If fails**: Check free tier limits (100 requests/month)

#### Test Benzinga
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "https://api.benzinga.com/api/v2/news?tickers=AAPL&pageSize=5"
```

**Expected**: JSON array with premium news articles

**If fails**: Requires paid subscription, check account status

---

### Step 3: Test in Notebook

Open `ice_building_workflow.ipynb` and run **Cell 15** (ingestion cell).

#### Expected Log Output (Multi-Source)

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
✅ Category 2 (News): Added 10 documents for AAPL
```

#### Expected Log Output (Finnhub + NewsAPI Only)

```
📊 AAPL: Distributing quota=12 across 2 sources (base=6)
  📰 AAPL: Fetching 6 from finnhub...
    ✅ finnhub: 6 unique (0 duplicates removed)
  📰 AAPL: Fetching 6 from newsapi...
    ✅ newsapi: 5 unique (1 duplicates removed)
📊 AAPL: Returning 10 unique articles from 2 sources
✅ Category 2 (News): Added 10 documents for AAPL
```

#### Expected Log Output (Finnhub Only - Current Default)

```
⚠️ AAPL: No news APIs available besides Finnhub
📊 AAPL: Distributing quota=12 across 1 sources (base=12)
  📰 AAPL: Fetching 12 from finnhub...
    ✅ finnhub: 10 unique (0 duplicates removed)
📊 AAPL: Returning 10 unique articles from 1 sources
✅ Category 2 (News): Added 10 documents for AAPL
```

---

### Step 4: Verify Article Metadata

Check Cell 15 output for article metadata:

```python
# Example article metadata (inspect first article)
print(news_docs[0])
```

**Expected fields**:
```python
{
    'content': 'Apple Announces New Product...',  # Full article text
    'source': 'finnhub',  # or 'newsapi', 'marketaux', 'benzinga'
    'file_path': 'finnhub:AAPL_a1b2c3d4',  # Unique ID
    'freshness': 'real-time',  # or 'delayed_24h'
    'tier': 1,  # 1=real-time, 2=delayed
    'relevance_score': 12.0,  # Scoring: 0.0-20.0
    'premium': False  # True only for Benzinga
}
```

---

## Troubleshooting Common Issues

### Issue: Only 4 articles despite limit=10

**Possible Causes**:
1. **Low news volume ticker** (e.g., FICO, small-cap stocks)
   - **Solution**: Test with high-volume ticker (AAPL, NVDA, TSLA)
   - **Expected**: More articles for popular stocks

2. **Only 1 API configured** (Finnhub only)
   - **Solution**: Add NewsAPI key (free) for broader coverage
   - **Expected**: 2 sources instead of 1

3. **Context='portfolio' with NewsAPI as only source**
   - **Solution**: Graceful degradation - NewsAPI will be used even for 'portfolio' if it's the only available source (with 24hr delay warning)
   - **Expected**: NewsAPI included with warning message about 24hr delay

### Issue: All articles from same source

**Symptom**:
```
📊 AAPL: Returning 10 unique articles from 1 sources
```

**Diagnosis**:
```bash
python config.py
# If shows "1 service" → Missing API keys
```

**Fix**:
1. Add at least NewsAPI key to .env (free):
   ```bash
   NEWSAPI_ORG_API_KEY=your-key-here
   ```
2. Restart kernel in notebook
3. Re-run Cell 15

**Expected after fix**:
```
📊 AAPL: Returning 10 unique articles from 2 sources
```

### Issue: "No news APIs available"

**Symptom**:
```
⚠️ AAPL: No news APIs available (limit=10). Returning empty list.
```

**Cause**: No API keys configured at all

**Fix**:
1. Check .env file exists: `ls .env`
2. If doesn't exist, create from sample:
   ```bash
   cp .env.sample .env
   ```
3. Add at minimum Finnhub key:
   ```bash
   FINNHUB_API_KEY=your-key-here
   ```
4. Verify: `python config.py`

### Issue: API returns error 401/403

**Symptom**: API test curl command returns authentication error

**Possible Causes**:
1. Invalid API key (typo, extra spaces)
2. Account suspended/expired
3. Free tier limit exceeded

**Fix**:
1. Copy key directly from API provider dashboard
2. Check account status on provider website
3. For free tiers, wait for monthly reset

---

## Testing Different Scenarios

### Scenario 1: High-Volume Ticker (AAPL, NVDA, TSLA)

**Expected**: ~10 articles easily available from each source

```python
# In Cell 15
holdings = ['AAPL']
news_limit = 10
```

**Result**: Should get exactly 10 articles (or close) from multiple sources

### Scenario 2: Low-Volume Ticker (FICO, Small-Cap)

**Expected**: May get <10 articles even with multiple sources

```python
# In Cell 15
holdings = ['FICO']
news_limit = 10
```

**Result**: Total articles limited by actual market availability (e.g., 4-6 articles)

### Scenario 3: Multiple Tickers

**Expected**: Articles distributed across all tickers

```python
# In Cell 15
holdings = ['AAPL', 'NVDA', 'TSLA']
news_limit = 5  # Per ticker
```

**Result**: ~15 total articles (5 per ticker × 3 tickers)

---

## Performance Benchmarks

### Expected Fetch Times (per ticker)

| Sources | Articles | Time | Notes |
|---------|----------|------|-------|
| 1 (Finnhub only) | 10 | ~0.5s | Fast, single API call |
| 2 (Finnhub + NewsAPI) | 10 | ~1.0s | Sequential fetching |
| 3 (+ MarketAux) | 10 | ~1.5s | Sequential fetching |
| 4 (All APIs) | 10 | ~2.0s | Sequential fetching |

**Note**: Times are for sequential fetching. Parallel fetching (future enhancement) could reduce to max(API times) ≈ 0.8s.

---

## Expected Article Distribution

### With All 4 APIs Configured

**For limit=10, high-volume ticker**:

| Source | Quota | Typical Yield | Final Count |
|--------|-------|---------------|-------------|
| Benzinga | 3 | 3 unique | 3 articles |
| Finnhub | 3 | 3 unique | 3 articles |
| MarketAux | 2 | 2 unique | 2 articles |
| NewsAPI | 2 | 1-2 unique | 2 articles |
| **Total** | **10** | **9-10 unique** | **10 articles** |

**Deduplication**: ~10-20% duplicates removed (same story from multiple sources)

### With Finnhub + NewsAPI Only

**For limit=10**:

| Source | Quota | Typical Yield | Final Count |
|--------|-------|---------------|-------------|
| Finnhub | 6 | 6 unique | 6 articles |
| NewsAPI | 6 | 4-5 unique | 4 articles |
| **Total** | **12** | **10 unique** | **10 articles** |

**Deduplication**: ~15% duplicates removed

---

## Quality Checks

### Check 1: Source Diversity

```python
# After Cell 15, inspect sources
sources = [doc['source'] for doc in news_docs]
print(f"Sources: {set(sources)}")
print(f"Distribution: {dict(Counter(sources))}")
```

**Expected** (4 APIs):
```
Sources: {'finnhub', 'newsapi', 'marketaux', 'benzinga'}
Distribution: {'benzinga': 3, 'finnhub': 3, 'marketaux': 2, 'newsapi': 2}
```

### Check 2: Relevance Scores

```python
# Check scoring is working
scores = [doc['relevance_score'] for doc in news_docs]
print(f"Score range: {min(scores):.1f} - {max(scores):.1f}")
```

**Expected**:
```
Score range: 6.3 - 19.5
# Benzinga (19.5) ranked first, NewsAPI (6.3) ranked last
```

### Check 3: Freshness Tags

```python
# Check freshness metadata
for doc in news_docs:
    print(f"{doc['source']}: tier={doc['tier']}, freshness={doc['freshness']}")
```

**Expected**:
```
benzinga: tier=1, freshness=real-time
finnhub: tier=1, freshness=real-time
marketaux: tier=1, freshness=real-time
newsapi: tier=2, freshness=delayed_24h
```

---

## NewsAPI.org Specific Troubleshooting

### Common NewsAPI Issues

#### Issue: NewsAPI Returns 0 Articles (Authentication)

**Symptom**:
```
❌ NewsAPI AUTHENTICATION FAILED for FICO: Invalid or expired API key (HTTP 401)
   API Response: Your API key is invalid or incorrect
```

**Root Cause**: API key is invalid, expired, or incorrectly formatted

**Diagnostic Steps**:
1. **Check if key exists**:
   ```bash
   echo $NEWSAPI_ORG_API_KEY
   # Should show 32-character alphanumeric string
   ```

2. **Test key directly**:
   ```bash
   curl "https://newsapi.org/v2/top-headlines?country=us&pageSize=1&apiKey=$NEWSAPI_ORG_API_KEY"
   ```

   **Success Response**:
   ```json
   {"status": "ok", "totalResults": 37, "articles": [...]}
   ```

   **Failure Response**:
   ```json
   {"status": "error", "code": "apiKeyInvalid", "message": "Your API key is invalid"}
   ```

3. **Fix invalid key**:
   - Get new key at: https://newsapi.org/register
   - Update `.env` file:
     ```bash
     NEWSAPI_ORG_API_KEY=your-new-32-char-key
     ```
   - Restart notebook kernel
   - Re-run ingestion

#### Issue: NewsAPI Returns 0 Articles (Query Too Restrictive)

**Symptom**:
```
📰 NewsAPI query 1/2 for FICO (Complex query): ("Fair Isaac Corporation" AND (stock OR shares OR earnings OR market))
   Query 1 returned 0 results, trying next strategy...
📰 NewsAPI query 2/2 for FICO (Simple fallback): "FICO stock"
✅ NewsAPI query 2 succeeded: 4 articles found
```

**Root Cause**: Complex query works for popular stocks (AAPL) but filters out all results for low-coverage stocks (FICO)

**What Happens**:
- **Query 1** (Complex): Full company name + stock terms
  - Works for AAPL: `("Apple Inc." AND (stock OR shares...))` → 24 results ✅
  - Fails for FICO: `("Fair Isaac Corporation" AND (stock OR shares...))` → 0 results ❌
- **Query 2** (Fallback): Simple ticker + "stock"
  - Works for FICO: `"FICO stock"` → 4 results ✅

**This is expected behavior** - ICE automatically tries fallback queries.

**Verification**:
```python
# Test complex query manually
import requests
response = requests.get(
    'https://newsapi.org/v2/everything',
    params={
        'q': '("Fair Isaac Corporation" AND (stock OR shares OR earnings OR market))',
        'apiKey': 'YOUR_KEY',
        'pageSize': 10
    }
)
print(f"Complex query: {response.json().get('totalResults', 0)} results")

# Test simple fallback
response2 = requests.get(
    'https://newsapi.org/v2/everything',
    params={
        'q': '"FICO stock"',
        'apiKey': 'YOUR_KEY',
        'pageSize': 10
    }
)
print(f"Simple query: {response2.json().get('totalResults', 0)} results")
```

**Expected Output**:
```
Complex query: 0 results
Simple query: 4 results
✅ Fallback strategy working correctly
```

**No action needed** - This is how ICE handles low-coverage stocks.

#### Issue: NewsAPI Returns 0 Articles (Low Coverage Stock)

**Symptom**:
```
⚠️ NewsAPI returned 0 articles for FICO after trying 2 query strategies.
Possible causes: (1) Low media coverage for this ticker,
(2) Ticker not newsworthy in past 7 days, (3) Ambiguous ticker term.
Consider using Finnhub/MarketAux for broader small-cap coverage.
```

**Root Cause**: Stock genuinely has no recent news in NewsAPI's database

**Diagnosis**:
1. **Verify this is a coverage issue, not API key issue**:
   - Test with known popular ticker (AAPL)
   - If AAPL works → Coverage issue
   - If AAPL fails → API key issue (see above)

2. **Test query variations**:
   ```bash
   # Test 1: Just ticker
   curl "https://newsapi.org/v2/everything?q=FICO&apiKey=YOUR_KEY&pageSize=5"

   # Test 2: Ticker + stock
   curl "https://newsapi.org/v2/everything?q=FICO+stock&apiKey=YOUR_KEY&pageSize=5"

   # Test 3: Company name
   curl "https://newsapi.org/v2/everything?q=Fair+Isaac+Corporation&apiKey=YOUR_KEY&pageSize=5"
   ```

3. **Expected behavior for low-coverage stocks**:
   - FICO (mid-cap): 0-4 results (depends on query)
   - AAPL (mega-cap): 20+ results (abundant coverage)
   - Small-cap (<$2B): Often 0 results

**Solution**: Use alternative APIs with better small-cap coverage:
```python
# Finnhub has broader coverage
finnhub_docs = ingester._fetch_finnhub_news('FICO', limit=10)
# Typically returns 5-10 articles even for small-cap

# MarketAux also covers small-cap well
marketaux_docs = ingester._fetch_marketaux('FICO', limit=10)
```

#### Issue: NewsAPI 24-Hour Delay Warning

**Symptom**:
```
⚠️ NewsAPI.org DEPRECATED: 24-hour delay on free tier. Use Finnhub for real-time news
```

**Root Cause**: NewsAPI free tier has inherent 24-hour data delay

**Impact**:
- ✅ **Research context**: Acceptable (historical analysis)
- ⚠️ **Portfolio context**: Delayed news penalized in ranking (but included via graceful degradation if only source)
- ⚠️ **Live context**: Excluded when real-time sources available (but included via graceful degradation if only source)

**This is a design limitation** of NewsAPI's free tier, not a bug.

**Recommendations**:
1. **For live trading**: Disable NewsAPI, use only Finnhub/MarketAux
2. **For portfolio analysis**: Keep enabled, but understand news is 24hr old
3. **For research**: NewsAPI works fine (delay doesn't matter)

**Configuration**:
```python
# In ice_building_workflow.ipynb Cell 14
finnhub_enabled = True        # ✅ Real-time
marketaux_enabled = True      # ✅ Real-time
newsapi_enabled = True        # ⚠️ 24hr delay (research only)
```

### NewsAPI vs Finnhub Coverage Comparison

| Stock Type | NewsAPI Results | Finnhub Results | Recommendation |
|------------|-----------------|-----------------|----------------|
| Mega-cap (AAPL) | 20+ articles | 15+ articles | Use both |
| Large-cap (NVDA) | 10-20 articles | 10-15 articles | Use both |
| Mid-cap (FICO) | 0-4 articles | 5-10 articles | **Prefer Finnhub** |
| Small-cap (<$2B) | 0-2 articles | 3-8 articles | **Prefer Finnhub** |

**Key Insight**: Finnhub has better small/mid-cap coverage than NewsAPI.

### Progressive Fallback Query Strategy (Since 2025-11-17)

ICE now automatically tries multiple query strategies for NewsAPI:

**Strategy 1 (Primary)**: Complex query with full company name
- Example: `("Fair Isaac Corporation" AND (stock OR shares OR earnings OR market))`
- Best for: Popular stocks with abundant news
- Precision: High (few false positives)
- Coverage: May miss results for low-coverage stocks

**Strategy 2 (Fallback)**: Simple query with ticker + "stock"
- Example: `"FICO stock"`
- Best for: Low-coverage stocks
- Precision: Lower (may include unrelated "FICO" mentions)
- Coverage: Better for sparse news environments

**How it works**:
1. Try Strategy 1 (complex query)
2. If 0 results → Automatically try Strategy 2 (simple fallback)
3. Return whichever strategy succeeded
4. If both fail → Return empty list with diagnostic logging

**Expected Log Output**:
```
📰 NewsAPI query 1/2 for FICO (Complex query): ("Fair Isaac Corporation" AND (stock OR shares OR earnings OR market))
   Query 1 returned 0 results, trying next strategy...
📰 NewsAPI query 2/2 for FICO (Simple fallback): "FICO stock"
✅ NewsAPI query 2 succeeded: 4 articles found
```

**No user action needed** - This happens automatically.

### When to Use NewsAPI vs Alternatives

| Use Case | Recommended API | Reason |
|----------|----------------|--------|
| **Live trading** | Finnhub, MarketAux | Real-time data required |
| **Intraday monitoring** | Finnhub, MarketAux | NewsAPI has 24hr delay |
| **Portfolio analysis** | All sources | Diversified coverage |
| **Historical research** | All sources | Delay doesn't matter |
| **Small-cap stocks** | Finnhub, MarketAux | Better coverage |
| **Mega-cap stocks** | All sources | NewsAPI works well |
| **Breaking news** | Finnhub, MarketAux | Real-time only |
| **Sentiment tracking** | Benzinga (premium) | Analyst sentiment data |

---

## Next Steps After Verification

### ✅ If All Tests Pass
1. Proceed with normal knowledge graph building
2. Monitor API usage (especially free tier limits)
3. Consider upgrading to paid tiers for professional coverage

### ⚠️ If Tests Fail
1. Review error messages carefully
2. Check API_KEY_SETUP_GUIDE.md for detailed troubleshooting
3. Verify API keys in .env are correct (no spaces, quotes)
4. Test individual APIs with curl commands above

### 📊 For Production Use
1. Set up monitoring for API failures
2. Track monthly API costs vs budget
3. Evaluate ROI of paid tiers vs free tiers
4. Consider parallel fetching for better performance (future enhancement)

---

**Last Updated**: 2025-11-17
**Status**: ✅ Production-ready (with graceful degradation)
**Maintained By**: ICE Development Team

**Recent Updates**:
- 2025-11-17: Added graceful degradation support - NewsAPI used as fallback when it's the only available source
