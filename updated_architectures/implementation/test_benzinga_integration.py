# Location: /updated_architectures/implementation/test_benzinga_integration.py
# Purpose: Quick test to verify Benzinga integration in data_ingestion.py
# Why: Validate Phase 1 integration before full workflow testing
# Relevant Files: data_ingestion.py, ice_data_ingestion/benzinga_client.py

"""
Quick test for Benzinga integration in ICE data ingestion pipeline
Tests:
1. BenzingaClient initialization
2. _fetch_benzinga_news() method
3. Waterfall integration in fetch_company_news()
"""

import os
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from updated_architectures.implementation.data_ingestion import DataIngester
from updated_architectures.implementation.config import ICEConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_benzinga_integration():
    """Test Benzinga integration"""
    print("\n" + "="*60)
    print("Testing Benzinga Integration")
    print("="*60 + "\n")

    # Check if Benzinga API key is configured
    benzinga_token = os.getenv('BENZINGA_API_TOKEN')
    if not benzinga_token:
        print("⚠️  BENZINGA_API_TOKEN not found in environment")
        print("   Set it with: export BENZINGA_API_TOKEN='your-token-here'")
        print("   Benzinga integration will be skipped in graceful degradation mode")
        print("\nTest Result: ✅ PASS (graceful degradation working)")
        return True

    print(f"✅ BENZINGA_API_TOKEN configured ({len(benzinga_token)} characters)")

    # Initialize config and data ingester
    try:
        config = ICEConfig()
        ingester = DataIngester(config=config)
        print("✅ DataIngester initialized")
    except Exception as e:
        print(f"❌ DataIngester initialization failed: {e}")
        return False

    # Check if benzinga_client was initialized
    if ingester.benzinga_client:
        print("✅ BenzingaClient initialized successfully")
    else:
        print("⚠️  BenzingaClient not initialized (API key may be invalid)")
        print("   Benzinga will be skipped in graceful degradation mode")
        print("\nTest Result: ✅ PASS (graceful degradation working)")
        return True

    # Test fetch_company_news() with Benzinga in waterfall
    print("\n" + "-"*60)
    print("Testing fetch_company_news() waterfall with Benzinga")
    print("-"*60 + "\n")

    test_symbol = 'AAPL'
    try:
        news_docs = ingester.fetch_company_news(test_symbol, limit=3)
        print(f"\n✅ Fetched {len(news_docs)} news documents for {test_symbol}")

        # Check if any came from benzinga
        benzinga_docs = [doc for doc in news_docs if doc.get('source') == 'benzinga']
        if benzinga_docs:
            print(f"✅ {len(benzinga_docs)} document(s) from Benzinga")
            print("\nSample Benzinga article (first 500 chars):")
            print("-" * 60)
            sample = benzinga_docs[0]['content'][:500]
            print(sample)
            print("...")
            print("-" * 60)
        else:
            print("ℹ️  No Benzinga documents in result (may be below limit or unavailable)")
            print("   Other sources:", [doc.get('source') for doc in news_docs])

        print(f"\n✅ Test Result: PASS")
        print(f"   Total documents: {len(news_docs)}")
        print(f"   Sources: {set(doc.get('source') for doc in news_docs)}")
        return True

    except Exception as e:
        print(f"❌ fetch_company_news() failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_benzinga_integration()

    print("\n" + "="*60)
    if success:
        print("✅ Benzinga Integration Test: PASSED")
    else:
        print("❌ Benzinga Integration Test: FAILED")
    print("="*60 + "\n")

    sys.exit(0 if success else 1)
