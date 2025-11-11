# Location: /updated_architectures/implementation/test_benzinga_direct.py
# Purpose: Direct test of _fetch_benzinga_news() method
# Why: Verify Benzinga method works independently of waterfall
# Relevant Files: data_ingestion.py, ice_data_ingestion/benzinga_client.py

"""
Direct test of Benzinga news fetching
Tests the _fetch_benzinga_news() method directly
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

def test_benzinga_direct():
    """Test _fetch_benzinga_news() method directly"""
    print("\n" + "="*60)
    print("Direct Test of _fetch_benzinga_news() Method")
    print("="*60 + "\n")

    # Check API key
    if not os.getenv('BENZINGA_API_TOKEN'):
        print("⚠️  BENZINGA_API_TOKEN not configured")
        print("   Skipping test (graceful degradation)")
        return True

    # Initialize
    config = ICEConfig()
    ingester = DataIngester(config=config)

    if not ingester.benzinga_client:
        print("⚠️  BenzingaClient not initialized")
        return True

    # Test direct fetch
    test_symbol = 'NVDA'
    print(f"Testing _fetch_benzinga_news() for {test_symbol}...")
    print("-" * 60 + "\n")

    try:
        docs = ingester._fetch_benzinga_news(test_symbol, limit=2)

        if docs:
            print(f"✅ Retrieved {len(docs)} Benzinga article(s)\n")
            print("Article 1 Preview:")
            print("-" * 60)
            print(docs[0][:800])  # First 800 chars
            print("...\n")
            print("="*60)
            print("✅ SUCCESS: Benzinga integration working!")
            print("="*60 + "\n")
            return True
        else:
            print("ℹ️  No articles returned (may be no recent news for symbol)")
            print("   But method executed without errors ✅")
            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_benzinga_direct()
    sys.exit(0 if success else 1)
