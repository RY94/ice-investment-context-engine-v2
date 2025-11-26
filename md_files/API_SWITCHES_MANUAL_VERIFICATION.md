# API Source Switches - Manual Verification Guide

**Location**: `/md_files/API_SWITCHES_MANUAL_VERIFICATION.md`
**Purpose**: Step-by-step manual verification of granular API switches implementation
**Date**: 2025-11-11
**Implementation**: Phase 1 Feature - Granular API Controls

---

## Overview

This guide helps verify the granular API source switches implementation through notebook testing.

**Implementation Summary**:
- ✅ **Cell 14** updated with 8 individual API switches + master switch
- ✅ **ice_simplified.py** updated to pass `api_source_config` to DataIngester
- ✅ **data_ingestion.py** updated with 3-layer precedence, caching, and early exit logic
- ✅ **Tests**: 16 unit tests + 6 integration tests = 22 tests passing

---

## Test Results Summary

### Unit Tests (16/16 passing)
```bash
python tests/test_api_source_switches.py
```

**Coverage**:
- ✅ Configuration setting (3 tests)
- ✅ 3-layer precedence hierarchy (4 tests)
- ✅ Caching performance (2 tests)
- ✅ Early exit logic (4 tests)
- ✅ Backward compatibility (1 test)
- ✅ Edge cases (2 tests)

### Integration Tests (6/6 passing)
```bash
python tests/test_api_switches_integration.py
```

**Coverage**:
- ✅ Config bundle flow from Cell 14
- ✅ Master switch disables all APIs
- ✅ Selective API enabling
- ✅ Fetch methods respect configuration
- ✅ Cache performance with multiple tickers
- ✅ Config update invalidates cache

---

## Manual Verification in Notebook

### Prerequisite
Open `ice_building_workflow.ipynb` and ensure you have API keys configured in environment variables.

### Test 1: Master Switch OFF (Layer 0)

**Cell 14 Configuration**:
```python
api_source_enabled = False  # Master switch OFF
newsapi_enabled = True      # Individual switches don't matter
benzinga_enabled = True
# ... rest can be any value
```

**Expected Behavior**:
- ⚠️ Logs show: "🔒 API sources: Master switch OFF (all APIs disabled)"
- All news/financial/market API calls should be skipped
- Only emails should be ingested

**Run**: Execute Cell 14 → Cell 15 (ingestion)

**Verification**:
```python
# In next cell, check:
ice_system.ingester.is_service_available('newsapi')  # Should return False
ice_system.ingester.is_service_available('fmp')     # Should return False
```

---

### Test 2: Selective News API Only

**Cell 14 Configuration**:
```python
api_source_enabled = True
newsapi_enabled = True       # Only NewsAPI
benzinga_enabled = False
finnhub_enabled = False
marketaux_enabled = False
fmp_enabled = False
alpha_vantage_enabled = False
polygon_enabled = False
sec_edgar_enabled = False
```

**Expected Behavior**:
- ✅ Logs show: "✅ API configuration applied: 1 APIs enabled: newsapi"
- Only NewsAPI fetches should occur
- Financial/market/SEC calls should be skipped with warning logs

**Verification**:
```python
# Check availability
ice_system.ingester.is_service_available('newsapi')  # True
ice_system.ingester.is_service_available('fmp')      # False

# Check fetch behavior
news = ice_system.ingester.fetch_company_news('AAPL', limit=5)
# Should return news articles

financials = ice_system.ingester.fetch_financial_fundamentals('AAPL', limit=2)
# Should return [] with warning log
```

---

### Test 3: News + Financial APIs Only

**Cell 14 Configuration**:
```python
api_source_enabled = True
newsapi_enabled = True
benzinga_enabled = True
finnhub_enabled = True
marketaux_enabled = True
fmp_enabled = True
alpha_vantage_enabled = True
polygon_enabled = False       # Market data OFF
sec_edgar_enabled = False     # SEC filings OFF
```

**Expected Behavior**:
- ✅ 6 APIs enabled (4 news + 2 financial)
- News and financial fundamentals fetched
- Market data and SEC filings skipped

**Verification**: Check logs for:
- "✅ API configuration applied: 6 APIs enabled"
- "⚠️ AAPL: Polygon (market data API) disabled"
- "⚠️ AAPL: SEC EDGAR disabled"

---

### Test 4: Cache Performance Test

**Objective**: Verify caching prevents redundant API availability checks

**Configuration**:
```python
api_source_enabled = True
newsapi_enabled = True
fmp_enabled = True
# ... others as needed
```

**Test Code** (in new cell after ingestion):
```python
# Clear cache first
ice_system.ingester._api_availability_cache.clear()

# Check cache population
import time

# First check (populates cache)
start = time.time()
result1 = ice_system.ingester.is_service_available('newsapi')
time1 = time.time() - start

# Second check (uses cache)
start = time.time()
result2 = ice_system.ingester.is_service_available('newsapi')
time2 = time.time() - start

print(f"First check: {time1*1000:.2f}ms (no cache)")
print(f"Second check: {time2*1000:.2f}ms (cached)")
print(f"Cache size: {len(ice_system.ingester._api_availability_cache)}")
print(f"Speedup: {time1/time2:.1f}x")
```

**Expected**:
- Cache size > 0
- Second check significantly faster (cached lookup)

---

### Test 5: Configuration Update Invalidates Cache

**Test Code**:
```python
# Initial config
config1 = {
    'api_source_enabled': True,
    'newsapi_enabled': True
}
ice_system.ingester.set_api_source_config(config1)

# Populate cache
ice_system.ingester.is_service_available('newsapi')  # True
print(f"Cache after config1: {len(ice_system.ingester._api_availability_cache)}")

# Update config (should clear cache)
config2 = {
    'api_source_enabled': True,
    'newsapi_enabled': False
}
ice_system.ingester.set_api_source_config(config2)

print(f"Cache after config2: {len(ice_system.ingester._api_availability_cache)}")  # Should be 0
print(f"NewsAPI available: {ice_system.ingester.is_service_available('newsapi')}")  # Should be False
```

**Expected**:
- Cache size is 0 after config update
- NewsAPI returns False after disabling

---

### Test 6: Early Exit Prevents Wasted Work

**Configuration** (disable all news APIs but set limit > 0):
```python
api_source_enabled = True
newsapi_enabled = False
benzinga_enabled = False
finnhub_enabled = False
marketaux_enabled = False
news_limit = 5  # Requesting news despite all APIs disabled
```

**Expected Behavior**:
- Warning log: "⚠️ AAPL: All news APIs disabled (limit=5). Returning empty list."
- No attempted API calls (saves time and avoids errors)
- Empty list returned immediately

**Verification**: Check logs for early exit warning

---

## Expected Log Patterns

### Successful Configuration Application
```
✅ API configuration applied: 6 APIs enabled: newsapi, benzinga, finnhub, marketaux, fmp, alpha_vantage
```

### Master Switch OFF
```
🔒 API sources: Master switch OFF (all APIs disabled)
```

### Individual API Disabled
```
⚠️ AAPL: All news APIs disabled (limit=5). Returning empty list.
⚠️ AAPL: Polygon (market data API) disabled (limit=1). Returning empty list.
⚠️ AAPL: SEC EDGAR disabled (limit=2). Returning empty list.
```

---

## Performance Benchmarks

With granular switches and caching:

| Scenario | Without Cache | With Cache | Speedup |
|----------|---------------|------------|---------|
| 50 tickers × 4 APIs | 200+ checks | 4 checks | 50x |
| Single ticker | 4 checks | 4 checks (1st run) | 1x |
| Re-run same ticker | 4 checks | 0 checks (cached) | ∞ |

**Cache Invalidation**: Occurs only on `set_api_source_config()` call

---

## Troubleshooting

### Issue: Configuration not applied

**Symptom**: API switches have no effect
**Check**:
1. Verify `api_source_config` bundle is passed to `ingest_historical_data()` or `ingest_with_manifest()`
2. Check logs for "✅ API configuration applied"
3. Verify `set_api_source_config()` exists in `data_ingestion.py`

**Fix**: Re-run Cell 14 and ensure api_source_config is passed correctly

### Issue: All APIs disabled despite switches ON

**Symptom**: No API calls happening
**Check**:
1. Verify `api_source_enabled = True` (master switch)
2. Check individual switches are `True`
3. Verify API keys are set in environment

**Fix**: Set master switch to True and check API key env vars

### Issue: Cache not working

**Symptom**: Repeated checks don't use cache
**Check**:
1. Verify `_api_availability_cache` exists in `self.ingester`
2. Check if cache is being cleared unexpectedly

**Fix**: Ensure `set_api_source_config()` is called only when config changes

---

## Validation Checklist

- [ ] Unit tests pass (16/16)
- [ ] Integration tests pass (6/6)
- [ ] Master switch OFF disables all APIs
- [ ] Individual switches control specific APIs
- [ ] Cache improves performance for multiple tickers
- [ ] Cache invalidates on config update
- [ ] Early exit prevents wasted API calls
- [ ] Configuration flows from Cell 14 → ice_simplified → data_ingestion
- [ ] Backward compatible (old notebooks work without changes)
- [ ] Log messages are clear and informative

---

## Success Criteria

✅ **All 22 tests passing**
✅ **3-layer precedence working** (Master → Individual → API Key)
✅ **Caching prevents redundant checks** (50x speedup for 50 tickers)
✅ **Early exit saves time** (empty list returned immediately if all disabled)
✅ **Clear logging** (user knows what's enabled/disabled)
✅ **Backward compatible** (existing code works without api_source_config)

---

**Verification Status**: ⏳ Pending manual notebook testing
**Next Steps**: Run verification tests in notebook, document any issues
**Owner**: Development team
**Last Updated**: 2025-11-11
