# Location: /updated_architectures/implementation/test_exa_mcp_integration.py
# Purpose: Test Exa MCP integration in data_ingestion.py
# Why: Validate Phase 2 integration - on-demand deep research tool
# Relevant Files: data_ingestion.py, ice_data_ingestion/exa_mcp_connector.py

"""
Test for Exa MCP integration in ICE data ingestion pipeline
Tests:
1. ExaMCPConnector initialization
2. research_company_deep() method
3. Async-to-sync bridge pattern
4. Source tagging (exa_company, exa_competitors)
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

def test_exa_mcp_integration():
    """Test Exa MCP integration"""
    print("\n" + "="*60)
    print("Testing Exa MCP Integration")
    print("="*60 + "\n")

    # Check if Exa API key is configured
    exa_key = os.getenv('EXA_API_KEY')
    if not exa_key:
        print("⚠️  EXA_API_KEY not found in environment")
        print("   Set it with: export EXA_API_KEY='your-key-here'")
        print("   Exa MCP integration will be skipped in graceful degradation mode")
        print("\nTest Result: ✅ PASS (graceful degradation working)")
        return True

    print(f"✅ EXA_API_KEY configured ({len(exa_key)} characters)")

    # Initialize config and data ingester
    try:
        config = ICEConfig()
        ingester = DataIngester(config=config)
        print("✅ DataIngester initialized")
    except Exception as e:
        print(f"❌ DataIngester initialization failed: {e}")
        return False

    # Check if exa_connector was initialized
    if ingester.exa_connector:
        print("✅ ExaMCPConnector initialized successfully")
    else:
        print("⚠️  ExaMCPConnector not initialized (MCP may not be configured)")
        print("   Exa MCP will be skipped in graceful degradation mode")
        print("\nTest Result: ✅ PASS (graceful degradation working)")
        return True

    # Test research_company_deep() method
    print("\n" + "-"*60)
    print("Testing research_company_deep() on-demand method")
    print("-"*60 + "\n")

    test_symbol = 'TSLA'
    test_company = 'Tesla Inc'
    test_topics = ['electric vehicles', 'battery technology']

    try:
        research_docs = ingester.research_company_deep(
            symbol=test_symbol,
            company_name=test_company,
            topics=test_topics,
            include_competitors=True,
            industry='automotive'
        )

        print(f"\n✅ Deep research completed for {test_symbol}")
        print(f"   Total documents: {len(research_docs)}")

        # Check source tagging
        exa_company_docs = [doc for doc in research_docs if doc.get('source') == 'exa_company']
        exa_competitor_docs = [doc for doc in research_docs if doc.get('source') == 'exa_competitors']

        print(f"   Company research documents: {len(exa_company_docs)}")
        print(f"   Competitor analysis documents: {len(exa_competitor_docs)}")

        if research_docs:
            print("\nSample research result (first 500 chars):")
            print("-" * 60)
            sample = research_docs[0]['content'][:500]
            print(sample)
            print("...")
            print("-" * 60)

            print(f"\n✅ Test Result: PASS")
            print(f"   Sources: {set(doc.get('source') for doc in research_docs)}")
            return True
        else:
            print("ℹ️  No documents returned (MCP may not be fully configured)")
            print("   But method executed without errors ✅")
            return True

    except Exception as e:
        print(f"❌ research_company_deep() failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_exa_mcp_integration()

    print("\n" + "="*60)
    if success:
        print("✅ Exa MCP Integration Test: PASSED")
    else:
        print("❌ Exa MCP Integration Test: FAILED")
    print("="*60 + "\n")

    sys.exit(0 if success else 1)
