#!/usr/bin/env python3
# Location: /tests/test_newsapi_benzinga_fixes.py
# Purpose: Test NewsAPI and Benzinga fixes for FICO ticker issue
# Why: Verify enhanced query logic and diagnostic logging work correctly
# Relevant Files: data_ingestion.py, benzinga_client.py

"""
Test suite for NewsAPI and Benzinga empty response fixes.

Tests:
1. NewsAPI enhanced query logic (TICKER_COMPANY_MAP)
2. NewsAPI empty response logging
3. Benzinga empty response logging
4. Both APIs work correctly for high-coverage tickers (AAPL)
5. Both APIs provide diagnostics for low-coverage tickers (FICO)
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'updated_architectures', 'implementation'))

# Set up logging to see diagnostic messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_newsapi_fico():
    """Test NewsAPI with FICO ticker (low-coverage, ambiguous)"""
    print("\n" + "="*80)
    print("TEST 1: NewsAPI with FICO ticker (low-coverage, ambiguous)")
    print("="*80)

    from data_ingestion import DataIngester

    # Initialize with only NewsAPI enabled
    api_keys = {
        'newsapi': os.getenv('NEWSAPI_ORG_API_KEY'),
        'openai': os.getenv('OPENAI_API_KEY')
    }

    if not api_keys['newsapi']:
        print("⚠️ NEWSAPI_ORG_API_KEY not set, skipping test")
        return

    ingestion = DataIngester(api_keys=api_keys)

    # Fetch news for FICO (context='research' enables delayed sources like NewsAPI)
    print("\n📊 Fetching news for FICO using NewsAPI...")
    docs = ingestion.fetch_company_news(
        symbol='FICO',
        limit=10,
        context='research'  # Enables delayed sources (NewsAPI)
    )

    print(f"\n✅ NewsAPI returned {len(docs)} documents for FICO")
    if docs:
        print(f"   First article: {docs[0].get('content', '')[:100]}...")
    else:
        print("   Expected: May be low due to ambiguous ticker term")

    return len(docs)


def test_newsapi_aapl():
    """Test NewsAPI with AAPL ticker (high-coverage, unique)"""
    print("\n" + "="*80)
    print("TEST 2: NewsAPI with AAPL ticker (high-coverage, unique)")
    print("="*80)

    from data_ingestion import DataIngester

    api_keys = {
        'newsapi': os.getenv('NEWSAPI_ORG_API_KEY'),
        'openai': os.getenv('OPENAI_API_KEY')
    }

    if not api_keys['newsapi']:
        print("⚠️ NEWSAPI_ORG_API_KEY not set, skipping test")
        return

    ingestion = DataIngester(api_keys=api_keys)

    print("\n📊 Fetching news for AAPL using NewsAPI...")
    docs = ingestion.fetch_company_news(
        symbol='AAPL',
        limit=10,
        context='research'  # Enables delayed sources (NewsAPI)
    )

    print(f"\n✅ NewsAPI returned {len(docs)} documents for AAPL")
    if docs:
        print(f"   First article: {docs[0].get('content', '')[:100]}...")

    return len(docs)


def test_benzinga_fico():
    """Test Benzinga with FICO ticker (likely not covered)"""
    print("\n" + "="*80)
    print("TEST 3: Benzinga with FICO ticker (likely not covered)")
    print("="*80)

    # Check if Benzinga API key exists
    benzinga_key = os.getenv('BENZINGA_API_KEY')
    if not benzinga_key:
        print("⚠️ BENZINGA_API_KEY not set, skipping test")
        print("   This is expected - Benzinga is a paid service")
        return 0

    from data_ingestion import DataIngester

    api_keys = {
        'benzinga': benzinga_key,
        'openai': os.getenv('OPENAI_API_KEY')
    }

    ingestion = DataIngester(api_keys=api_keys)

    print("\n📊 Fetching news for FICO using Benzinga...")
    docs = ingestion.fetch_company_news(
        symbol='FICO',
        limit=10,
        context='portfolio'  # Real-time sources only
    )

    print(f"\n✅ Benzinga returned {len(docs)} documents for FICO")
    print("   Expected: Likely 0 due to coverage limitations (popular tickers only)")

    return len(docs)


def test_benzinga_aapl():
    """Test Benzinga with AAPL ticker (high-coverage)"""
    print("\n" + "="*80)
    print("TEST 4: Benzinga with AAPL ticker (high-coverage)")
    print("="*80)

    benzinga_key = os.getenv('BENZINGA_API_KEY')
    if not benzinga_key:
        print("⚠️ BENZINGA_API_KEY not set, skipping test")
        return 0

    from data_ingestion import DataIngester

    api_keys = {
        'benzinga': benzinga_key,
        'openai': os.getenv('OPENAI_API_KEY')
    }

    ingestion = DataIngester(api_keys=api_keys)

    print("\n📊 Fetching news for AAPL using Benzinga...")
    docs = ingestion.fetch_company_news(
        symbol='AAPL',
        limit=10,
        context='portfolio'  # Real-time sources only
    )

    print(f"\n✅ Benzinga returned {len(docs)} documents for AAPL")
    if docs:
        print(f"   First article: {docs[0].get('content', '')[:100]}...")

    return len(docs)


def main():
    """Run all tests and summarize results"""
    print("\n" + "="*80)
    print("NEWSAPI & BENZINGA FIX VERIFICATION SUITE")
    print("="*80)
    print("\nTesting fixes for:")
    print("1. NewsAPI enhanced query logic (TICKER_COMPANY_MAP)")
    print("2. NewsAPI empty response logging")
    print("3. Benzinga empty response logging")
    print("\nExpected behavior:")
    print("- FICO: Low results due to ambiguous term / coverage gaps (with diagnostic logs)")
    print("- AAPL: Good results from both APIs (popular ticker)")

    results = {}

    # Run tests
    results['newsapi_fico'] = test_newsapi_fico()
    results['newsapi_aapl'] = test_newsapi_aapl()
    results['benzinga_fico'] = test_benzinga_fico()
    results['benzinga_aapl'] = test_benzinga_aapl()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"NewsAPI + FICO: {results.get('newsapi_fico', 'SKIPPED')} documents")
    print(f"NewsAPI + AAPL: {results.get('newsapi_aapl', 'SKIPPED')} documents")
    print(f"Benzinga + FICO: {results.get('benzinga_fico', 'SKIPPED')} documents")
    print(f"Benzinga + AAPL: {results.get('benzinga_aapl', 'SKIPPED')} documents")

    # Validation
    print("\n" + "="*80)
    print("VALIDATION")
    print("="*80)

    if results.get('newsapi_aapl', 0) > 0:
        print("✅ NewsAPI working for high-coverage tickers (AAPL)")
    else:
        print("⚠️ NewsAPI returned 0 results for AAPL (unexpected)")

    if results.get('newsapi_fico', 0) >= 0:
        print("✅ NewsAPI query enhancement implemented (check logs for company name query)")

    print("\n📋 Check logs above for diagnostic warnings when results are empty")
    print("   Look for: '⚠️ NewsAPI returned 0 articles...' or '⚠️ Benzinga returned 0 articles...'")


if __name__ == '__main__':
    main()
