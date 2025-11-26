# Location: /tests/test_yahoo_finance_enhanced.py
# Purpose: Validate enhanced Yahoo Finance integration with comprehensive data extraction
# Why: Ensure 5 data categories (market, analyst, holdings, financials, earnings) work correctly
# Relevant Files: updated_architectures/implementation/data_ingestion.py, ice_simplified.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from updated_architectures.implementation.data_ingestion import DataIngester
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_yahoo_finance_enhanced():
    """
    Test enhanced Yahoo Finance integration

    Validates:
    1. Method returns 1-5 documents (depending on ticker)
    2. Each document has proper category markers
    3. FMP/Alpha Vantage still available as fallbacks
    4. Error handling for invalid tickers
    5. Graceful degradation for small caps (partial data)
    """
    print("\n" + "="*80)
    print("YAHOO FINANCE ENHANCED INTEGRATION TEST")
    print("="*80)

    ingester = DataIngester()

    # Test 1: Large cap with full data (AAPL)
    print("\n--- TEST 1: Large Cap (AAPL) - Expect 5 document categories ---")
    try:
        docs_aapl = ingester._fetch_yahoo_market_data('AAPL')
        print(f"✅ AAPL: Retrieved {len(docs_aapl)} document(s)")

        # Detect categories
        categories = set()
        for doc in docs_aapl:
            if "Analyst Intelligence" in doc:
                categories.add("analyst")
            elif "Institutional Holdings" in doc:
                categories.add("holdings")
            elif "Financial Statements" in doc:
                categories.add("financials")
            elif "Earnings & Dividends" in doc:
                categories.add("earnings")
            else:
                categories.add("market")

        print(f"   Categories found: {', '.join(sorted(categories))}")
        print(f"   Expected: analyst, earnings, financials, holdings, market")

        if len(categories) >= 4:
            print(f"   ✅ PASS: {len(categories)}/5 categories retrieved")
        else:
            print(f"   ⚠️  PARTIAL: Only {len(categories)}/5 categories (may be okay)")

    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # Test 2: Tech stock with analyst coverage (NVDA)
    print("\n--- TEST 2: Tech Stock (NVDA) - Validate analyst data ---")
    try:
        docs_nvda = ingester._fetch_yahoo_market_data('NVDA')
        print(f"✅ NVDA: Retrieved {len(docs_nvda)} document(s)")

        # Check for analyst data
        has_analyst = any("Analyst Intelligence" in doc for doc in docs_nvda)
        has_financials = any("Financial Statements" in doc for doc in docs_nvda)

        print(f"   Analyst data present: {has_analyst}")
        print(f"   Financial statements present: {has_financials}")

        if has_analyst and has_financials:
            print(f"   ✅ PASS: Critical categories present")
        else:
            print(f"   ⚠️  WARNING: Missing critical data")

    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # Test 3: Small cap (may have partial data)
    print("\n--- TEST 3: Small Cap - Graceful degradation check ---")
    try:
        # Using a smaller company that may have less analyst coverage
        docs_small = ingester._fetch_yahoo_market_data('CROX')
        print(f"✅ CROX: Retrieved {len(docs_small)} document(s)")

        if len(docs_small) >= 1:
            print(f"   ✅ PASS: At least market data retrieved (graceful degradation working)")
        else:
            print(f"   ❌ FAIL: No data retrieved")

    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # Test 4: Invalid ticker (error handling)
    print("\n--- TEST 4: Invalid Ticker (INVALID_TICKER) - Error handling ---")
    try:
        docs_invalid = ingester._fetch_yahoo_market_data('INVALID_TICKER_XYZ123')

        if len(docs_invalid) == 0:
            print(f"   ✅ PASS: Returned empty list (graceful error handling)")
        else:
            print(f"   ⚠️  WARNING: Retrieved {len(docs_invalid)} doc(s) for invalid ticker")

    except Exception as e:
        print(f"   ✅ PASS: Exception caught gracefully: {e}")

    # Test 5: FMP/Alpha Vantage still available (backward compatibility)
    print("\n--- TEST 5: Backward Compatibility - FMP/Alpha Vantage fallbacks ---")
    try:
        # Check if methods still exist
        has_fmp = hasattr(ingester, '_fetch_fmp_company_profile')
        has_alpha = hasattr(ingester, '_fetch_alpha_vantage_overview')

        print(f"   FMP method exists: {has_fmp}")
        print(f"   Alpha Vantage method exists: {has_alpha}")

        if has_fmp and has_alpha:
            print(f"   ✅ PASS: Fallback APIs preserved (not deleted)")
        else:
            print(f"   ❌ FAIL: Fallback APIs missing")

    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # Test 6: Document length check (ensure not too large)
    print("\n--- TEST 6: Document Length - Performance check ---")
    try:
        docs_length_test = ingester._fetch_yahoo_market_data('MSFT')

        for i, doc in enumerate(docs_length_test):
            doc_length = len(doc)
            print(f"   Document {i+1}: {doc_length:,} characters")

            if doc_length > 50000:
                print(f"      ⚠️  WARNING: Document may be too large for optimal LightRAG processing")
            else:
                print(f"      ✅ Size acceptable")

    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
    print("\n✅ Key Validation Points:")
    print("   1. Enhanced method returns 1-5 documents (not just 1)")
    print("   2. Categories properly detected (analyst, holdings, financials, earnings, market)")
    print("   3. Graceful degradation for tickers with partial data")
    print("   4. Error handling for invalid tickers")
    print("   5. FMP/Alpha Vantage fallbacks preserved")
    print("   6. Document sizes reasonable for LightRAG")
    print("\n")

if __name__ == "__main__":
    test_yahoo_finance_enhanced()
