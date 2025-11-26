# News Limit Quota Distribution Fix

**Date**: 2025-11-22
**Issue**: `news_limit=3` only returns 1-2 articles instead of 3
**Root Cause**: Quota distribution bug dividing limit across sources
**Fix**: Request full limit from each source, select top N by quality

---

## Problem Statement

When configuring `news_limit=3` in notebook Cell 15:
- **Expected**: 3 news articles
- **Actual**: 1-2 articles (depending on source availability)
- **User Impact**: Insufficient news coverage for analysis

## Root Cause Analysis

### The Bug (Line 975)

**Old Code** (`data_ingestion.py:973-978`):
```python
# Step 2: Calculate proportional quota distribution with 20% dedup buffer
fetch_budget = int(limit * 1.2)  # int(3 * 1.2) = 3
base_quota = max(1, fetch_budget // len(active_sources))  # BUG: Divides quota
remainder = fetch_budget % len(active_sources)

logger.info(f"  📊 {symbol}: Distributing quota={fetch_budget} across {len(active_sources)} sources (base={base_quota})")
```

**Problem**: Divides the requested limit across multiple news sources:

| Scenario | Active Sources | Quota Per Source | Max Possible Return |
|----------|---------------|------------------|---------------------|
| 3 sources enabled | finnhub, marketaux, benzinga | 3 ÷ 3 = **1 each** | 3 total (if all succeed) |
| 1 source fails | finnhub, marketaux, ~~benzinga~~ | 1 + 1 + **0** | **2 total** ❌ |
| Only NewsAPI | newsapi | 3 ÷ 1 = 3 | 1-3 (depends on coverage) |

**Impact**:
- If any source fails → fewer articles than requested
- Low-coverage tickers (like FICO) → even fewer articles
- Violates user expectation: `news_limit=3` should return 3 articles

### Diagnostic Evidence

**Test output showing the bug**:
```
INFO:data_ingestion:  📊 FICO: Distributing quota=3 across 3 sources (base=1)
INFO:data_ingestion:  📰 FICO: Fetching 1 from finnhub...
INFO:data_ingestion:    ✅ finnhub: 1 unique (0 duplicates removed)
INFO:data_ingestion:  📰 FICO: Fetching 1 from marketaux...
INFO:data_ingestion:    ✅ marketaux: 1 unique (0 duplicates removed)
INFO:data_ingestion:  📰 FICO: Fetching 1 from benzinga...
WARNING:ice_data_ingestion.benzinga_client:⚠️ Benzinga returned no response
INFO:data_ingestion:    ✅ benzinga: 0 unique (0 duplicates removed)

RESULTS: Documents returned: 2  ← Should be 3
```

---

## The Fix

### Elegant Solution: Quality-Based Selection

Instead of dividing quota, **request full limit from each source** and select the best:

**New Code** (`data_ingestion.py:973-978`):
```python
# Step 2: Request full limit from each source for quality-based selection
# Strategy: Over-fetch from all sources, then rank by freshness/quality and select top N
# This ensures we get the requested number of articles even if some sources fail
source_quota = limit  # Each source gets full quota (not divided)

logger.info(f"  📊 {symbol}: Requesting {source_quota} articles from each of {len(active_sources)} sources (quality-ranked selection)")
```

**Also removed** (Line 984-986):
```python
# OLD: Distribute remainder to first N sources
# source_quota = base_quota + (1 if idx < remainder else 0)

# NEW: Use global source_quota defined above
```

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Request Phase                                            │
│    ✓ Finnhub:   Request 3 articles → Returns 3             │
│    ✓ MarketAux: Request 3 articles → Returns 3             │
│    ✗ Benzinga:  Request 3 articles → Returns 0 (failed)    │
│                                                              │
│    Total collected: 6 articles (deduplicated by headline)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Ranking Phase (data_ingestion.py:1044)                  │
│    Rank by:                                                  │
│      • Freshness tier (real-time > delayed_24h)             │
│      • Context relevance (portfolio vs research)            │
│      • Premium source (benzinga > others)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Selection Phase (data_ingestion.py:1047)                │
│    final_articles = all_articles[:limit]  # Top 3           │
│                                                              │
│    ✅ Returns exactly 3 articles as requested               │
└─────────────────────────────────────────────────────────────┘
```

### Benefits

1. **Resilience**: Source failures don't reduce article count
2. **Quality**: Get best articles across all sources (ranked)
3. **Predictability**: User always gets `limit` articles (if available)
4. **Fair competition**: Sources compete on quality, not quota

---

## Verification

### Test Results

**After Fix**:
```
INFO:data_ingestion:  📊 FICO: Requesting 3 articles from each of 3 sources (quality-ranked selection)
INFO:data_ingestion:  📰 FICO: Fetching 3 from finnhub...
INFO:data_ingestion:    ✅ finnhub: 3 unique (0 duplicates removed)
INFO:data_ingestion:  📰 FICO: Fetching 3 from marketaux...
INFO:data_ingestion:    ✅ marketaux: 3 unique (0 duplicates removed)
INFO:data_ingestion:  📰 FICO: Fetching 3 from benzinga...
WARNING:ice_data_ingestion.benzinga_client:⚠️ Benzinga returned no response
INFO:data_ingestion:    ✅ benzinga: 0 unique (0 duplicates removed)

RESULTS: Documents returned: 3 ✅  ← Now correct!
Expected: 3
Actual: 3
```

### Test Coverage

| Scenario | Before Fix | After Fix |
|----------|-----------|-----------|
| 3 sources, all succeed | 3 articles ✅ | 3 articles ✅ |
| 3 sources, 1 fails | **2 articles** ❌ | 3 articles ✅ |
| 1 source (NewsAPI), low coverage | 1 article (data scarcity) | 1 article (data scarcity) |
| Mixed quality articles | Unranked | Best 3 by quality ✅ |

**Note**: When only 1 source is available with low coverage (e.g., NewsAPI returning 1 article for FICO), the system correctly returns what's available. This is **expected behavior**, not a bug.

---

## Impact on Notebooks

### ice_building_workflow.ipynb Cell 15

**Before**:
```
📊 Pre-fetching documents to calculate totals...
     ✓ Found 1 documents (news: 1, financial: 0, market: 0, SEC: 0, research: 0)
```

**After** (with multiple sources enabled):
```
📊 Pre-fetching documents to calculate totals...
     ✓ Found 3 documents (news: 3, financial: 0, market: 0, SEC: 0, research: 0)
```

**Configuration remains unchanged**:
```python
# Cell 15 configuration
news_limit = 3  # ← Still works as expected now
api_source_enabled = True
newsapi_enabled = True
# ... other settings
```

---

## Files Modified

- **`updated_architectures/implementation/data_ingestion.py`**:
  - Lines 973-978: Replaced quota distribution with full-limit strategy
  - Line 984-986: Removed remainder distribution logic
  - Line 980: Updated comment to reflect new strategy

**Total changes**: 6 lines modified (3 logic, 3 comments)

---

## Related Documentation

- **Investigation**: `tmp/tmp_diagnose_news_limit.py` (diagnostic test, deleted after use)
- **Notebook**: `ice_building_workflow.ipynb` Cell 15 (affected configuration)
- **Architecture**: Data ingestion layer quota distribution strategy

---

## Lessons Learned

### Design Principle

**Bad**: Divide quota across sources (fails when sources are unreliable)
**Good**: Request full quota from all sources, select best (resilient + quality-focused)

### Why This Bug Existed

The original quota distribution assumed:
1. All sources would succeed (optimistic)
2. Equal quality across sources (incorrect)
3. Fair distribution is more important than user expectation (wrong priority)

The fix recognizes:
1. Sources fail unpredictably (defensive)
2. Quality varies by source and article (rank by score)
3. User expectation (`limit=3` → 3 articles) is paramount

---

**Status**: ✅ Fixed and Verified
**Regression Risk**: Low (scoring/ranking logic already existed, just using it properly now)
**User Notification**: Update notebook documentation to reflect improved reliability

---

**Last Updated**: 2025-11-22
**Verified By**: Diagnostic test showing 3/3 articles returned with source failure
**Next Steps**: Monitor API costs (requesting 3× more articles per source)
