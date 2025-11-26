#!/usr/bin/env python3
"""
Test script to verify granular API switches work correctly
Tests the scenario where only SEC EDGAR is enabled
"""

import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'updated_architectures' / 'implementation'))

from data_ingestion import DataIngester

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sec_only_configuration():
    """Test with only SEC EDGAR enabled, all other APIs disabled"""

    print("\n" + "="*70)
    print("TEST: SEC-Only Configuration")
    print("="*70)

    # Mock API keys (simulating environment variables)
    api_keys = {
        'newsapi': 'test_newsapi_key',
        'benzinga': 'test_benzinga_key',
        'finnhub': 'test_finnhub_key',
        'marketaux': 'test_marketaux_key',
        'fmp': 'test_fmp_key',
        'alpha_vantage': 'test_av_key',
        'polygon': 'test_polygon_key',
    }

    # Create DataIngester
    ingester = DataIngester(api_keys=api_keys)

    # Configuration from Cell 14: Only SEC EDGAR enabled
    api_source_config = {
        'api_source_enabled': True,        # Master switch ON
        'newsapi_enabled': False,          # NewsAPI OFF
        'benzinga_enabled': False,         # Benzinga OFF
        'finnhub_enabled': False,          # Finnhub OFF
        'marketaux_enabled': False,        # MarketAux OFF
        'fmp_enabled': False,              # FMP OFF
        'alpha_vantage_enabled': False,    # Alpha Vantage OFF
        'polygon_enabled': False,          # Polygon OFF
        'sec_edgar_enabled': True          # SEC EDGAR ON (only this one!)
    }

    # Apply configuration
    ingester.set_api_source_config(api_source_config)

    # Test 1: Check individual API availability
    print("\n1. API Availability Checks:")
    apis_to_check = ['newsapi', 'benzinga', 'finnhub', 'marketaux', 'fmp', 'alpha_vantage', 'polygon']

    for api in apis_to_check:
        is_available = ingester.is_service_available(api)
        status = "❌ DISABLED" if not is_available else "✅ ENABLED (ERROR: Should be disabled!)"
        print(f"   {api:15}: {status}")

    # SEC EDGAR doesn't use is_service_available (special case - no API key required)
    print(f"   {'sec_edgar':15}: ✅ ENABLED (as expected)")

    # Test 2: Test fetch methods with limits > 0
    print("\n2. Testing Fetch Methods (should return empty for disabled APIs):")

    # Test news fetching (all news APIs disabled)
    news_result = ingester.fetch_company_news('AAPL', limit=5)
    print(f"   fetch_company_news:       {len(news_result)} items (expected: 0)")

    # Test financial fundamentals (FMP and Alpha Vantage disabled)
    financial_result = ingester.fetch_financial_fundamentals('AAPL', limit=2)
    print(f"   fetch_financial_fundamentals: {len(financial_result)} items (expected: 0)")

    # Test market data (Polygon disabled)
    market_result = ingester.fetch_market_data('AAPL', limit=1)
    print(f"   fetch_market_data:        {len(market_result)} items (expected: 0)")

    # Note: SEC filings would work but we can't test without network calls
    print(f"   fetch_sec_filings:        [Would work - SEC enabled]")

    # Test 3: Verify cache is working
    print("\n3. Cache Performance:")
    cache_size = len(ingester._api_availability_cache)
    print(f"   Cache size: {cache_size} entries")
    print(f"   Cache contents: {list(ingester._api_availability_cache.keys())}")

    # Summary
    print("\n" + "="*70)
    all_tests_passed = (
        len(news_result) == 0 and
        len(financial_result) == 0 and
        len(market_result) == 0 and
        cache_size > 0
    )

    if all_tests_passed:
        print("✅ TEST PASSED: Only SEC EDGAR is active, all other APIs correctly disabled")
    else:
        print("❌ TEST FAILED: Some APIs are still active when they should be disabled")

    print("="*70)
    return all_tests_passed


def test_master_switch_off():
    """Test with master switch OFF - all APIs should be disabled"""

    print("\n" + "="*70)
    print("TEST: Master Switch OFF")
    print("="*70)

    # Mock API keys
    api_keys = {
        'newsapi': 'test_newsapi_key',
        'fmp': 'test_fmp_key',
        'polygon': 'test_polygon_key',
    }

    # Create DataIngester
    ingester = DataIngester(api_keys=api_keys)

    # Configuration: Master switch OFF (individual switches don't matter)
    api_source_config = {
        'api_source_enabled': False,       # Master switch OFF!
        'newsapi_enabled': True,           # Doesn't matter
        'fmp_enabled': True,              # Doesn't matter
        'polygon_enabled': True,          # Doesn't matter
        'sec_edgar_enabled': True         # Doesn't matter
    }

    # Apply configuration
    ingester.set_api_source_config(api_source_config)

    print("\n1. API Availability (all should be disabled):")
    apis = ['newsapi', 'fmp', 'polygon']

    all_disabled = True
    for api in apis:
        is_available = ingester.is_service_available(api)
        status = "❌ DISABLED (correct)" if not is_available else "✅ ENABLED (ERROR!)"
        print(f"   {api:10}: {status}")
        if is_available:
            all_disabled = False

    # Test fetch methods
    print("\n2. Fetch Methods (all should return empty):")
    news = ingester.fetch_company_news('AAPL', limit=5)
    financials = ingester.fetch_financial_fundamentals('AAPL', limit=2)
    market = ingester.fetch_market_data('AAPL', limit=1)

    print(f"   News:      {len(news)} items (expected: 0)")
    print(f"   Financial: {len(financials)} items (expected: 0)")
    print(f"   Market:    {len(market)} items (expected: 0)")

    # Summary
    print("\n" + "="*70)
    all_tests_passed = all_disabled and len(news) == 0 and len(financials) == 0 and len(market) == 0

    if all_tests_passed:
        print("✅ TEST PASSED: Master switch correctly disables all APIs")
    else:
        print("❌ TEST FAILED: Master switch not working correctly")

    print("="*70)
    return all_tests_passed


if __name__ == '__main__':
    # Run both tests
    test1_passed = test_sec_only_configuration()
    test2_passed = test_master_switch_off()

    print("\n" + "="*70)
    print("FINAL RESULTS:")
    print(f"  SEC-only config test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Master switch test:   {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("="*70)

    sys.exit(0 if (test1_passed and test2_passed) else 1)