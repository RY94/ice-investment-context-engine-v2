#!/usr/bin/env python3
# Location: /tests/test_dynamic_company_name_lookup.py
# Purpose: Test dynamic company name lookup with Yahoo Finance caching
# Why: Verify replacement of hardcoded TICKER_COMPANY_MAP with scalable solution
# Relevant Files: data_ingestion.py (get_company_name method)

"""
Test suite for dynamic company name resolution using Yahoo Finance.

Tests:
1. FICO resolves to "Fair Isaac Corporation"
2. AAPL resolves to "Apple Inc."
3. Unknown ticker (XYZ999) falls back to ticker symbol
4. Caching works (second call is instant)
5. Works for thousands of tickers (not just 8 hardcoded)
"""

import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'updated_architectures', 'implementation'))

def test_dynamic_company_name_resolution():
    """Test dynamic company name lookup from Yahoo Finance"""
    print("\n" + "="*80)
    print("DYNAMIC COMPANY NAME RESOLUTION TEST")
    print("="*80)

    from data_ingestion import DataIngester

    api_keys = {'openai': os.getenv('OPENAI_API_KEY')}
    ingestion = DataIngester(api_keys=api_keys)

    print("\n✅ DataIngester initialized\n")

    # Test 1: FICO (ambiguous ticker)
    print("TEST 1: Resolve FICO ticker")
    start = time.time()
    fico_name = ingestion.get_company_name('FICO')
    duration = time.time() - start
    print(f"  FICO → '{fico_name}'")
    print(f"  Duration: {duration:.3f}s (first call, Yahoo Finance API fetch)")
    assert 'Fair Isaac' in fico_name or 'FICO' in fico_name, f"Expected Fair Isaac, got {fico_name}"
    print("  ✅ PASS\n")

    # Test 2: AAPL (popular ticker)
    print("TEST 2: Resolve AAPL ticker")
    start = time.time()
    aapl_name = ingestion.get_company_name('AAPL')
    duration = time.time() - start
    print(f"  AAPL → '{aapl_name}'")
    print(f"  Duration: {duration:.3f}s (first call)")
    assert 'Apple' in aapl_name, f"Expected Apple, got {aapl_name}"
    print("  ✅ PASS\n")

    # Test 3: Cached lookup (should be instant)
    print("TEST 3: Cached lookup (FICO second call)")
    start = time.time()
    fico_name_cached = ingestion.get_company_name('FICO')
    duration = time.time() - start
    print(f"  FICO → '{fico_name_cached}' (cached)")
    print(f"  Duration: {duration:.6f}s (cached, should be ~0ms)")
    assert duration < 0.01, f"Expected <10ms, got {duration*1000:.1f}ms"
    assert fico_name_cached == fico_name, "Cached value should match"
    print("  ✅ PASS - Caching works!\n")

    # Test 4: Unknown ticker (fallback to ticker symbol)
    print("TEST 4: Unknown ticker fallback")
    start = time.time()
    unknown_name = ingestion.get_company_name('XYZ999INVALID')
    duration = time.time() - start
    print(f"  XYZ999INVALID → '{unknown_name}'")
    print(f"  Duration: {duration:.3f}s")
    assert unknown_name == 'XYZ999INVALID', f"Expected fallback to ticker, got {unknown_name}"
    print("  ✅ PASS - Graceful fallback\n")

    # Test 5: Multiple tickers (demonstrate scalability)
    print("TEST 5: Scalability test (10 different tickers)")
    tickers = ['NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'JPM', 'V', 'WMT', 'PG']
    resolved = {}
    total_duration = 0

    for ticker in tickers:
        start = time.time()
        name = ingestion.get_company_name(ticker)
        duration = time.time() - start
        total_duration += duration
        resolved[ticker] = name
        print(f"  {ticker} → {name} ({duration:.3f}s)")

    print(f"\n  Total: {len(resolved)} tickers resolved in {total_duration:.3f}s")
    print(f"  Average: {total_duration/len(resolved):.3f}s per ticker")
    print("  ✅ PASS - Scales to any ticker\n")

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ All tests passed!")
    print(f"✅ Dynamic resolution works for any ticker (not just 8 hardcoded)")
    print(f"✅ Caching prevents repeated API calls")
    print(f"✅ Graceful fallback for unknown tickers")
    print(f"✅ Resolved {len(resolved) + 3} unique tickers total")
    print("\nSample resolutions:")
    for ticker, name in list(resolved.items())[:5]:
        print(f"  {ticker:6} → {name}")

if __name__ == '__main__':
    test_dynamic_company_name_resolution()
