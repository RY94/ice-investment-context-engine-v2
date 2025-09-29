#!/usr/bin/env python3
"""
Test the complete earnings integration with ICE
Tests the full workflow: fetch earnings -> add to knowledge base -> query
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import sys
from pathlib import Path
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging

# Add the current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ice_rag import SimpleICERAG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_earnings_integration():
    """Test the complete earnings integration workflow"""
    
    print("🧪 Testing Complete Earnings Integration")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please set it first:")
        print("export OPENAI_API_KEY='your-key-here'")
        return False
    
    try:
        # Initialize ICE RAG
        print("📊 Initializing ICE with earnings support...")
        rag = SimpleICERAG("./test_earnings_storage")
        
        if not rag.is_ready():
            print("❌ LightRAG not ready - check dependencies")
            return False
        
        print(f"✅ RAG initialized. Earnings available: {rag.earnings_available}")
        
        if not rag.earnings_available:
            print("❌ Earnings fetching not available")
            return False
        
        # Test 1: Fetch and add earnings for NVIDIA
        print("\n📈 Test 1: Fetching NVIDIA earnings...")
        result = rag.fetch_and_add_earnings("nvidia")
        
        if result["status"] != "success":
            print(f"❌ Failed to fetch NVIDIA earnings: {result['message']}")
            return False
        
        print(f"✅ Successfully fetched earnings for {result['company_name']} ({result['ticker']})")
        print(f"   Source: {result['source']}")
        
        # Test 2: Query about NVIDIA earnings
        print("\n🤖 Test 2: Querying about NVIDIA earnings...")
        query_result = rag.query("What are NVIDIA's latest quarterly earnings?", "hybrid")
        
        if query_result["status"] != "success":
            print(f"❌ Query failed: {query_result['message']}")
            return False
        
        print("✅ Query successful!")
        print("Response preview:")
        print("-" * 40)
        print(query_result["result"][:500] + "..." if len(query_result["result"]) > 500 else query_result["result"])
        print("-" * 40)
        
        # Test 3: Test query_with_earnings for Apple
        print("\n🍎 Test 3: Query with automatic earnings fetch for Apple...")
        combined_result = rag.query_with_earnings(
            "What are Apple's financial highlights and risks?", 
            "apple", 
            "hybrid"
        )
        
        if combined_result["status"] != "success":
            print(f"❌ Combined query failed: {combined_result['message']}")
            return False
        
        print(f"✅ Combined query successful!")
        if combined_result.get("earnings_fetched"):
            earnings_info = combined_result.get("earnings_info", {})
            print(f"   📊 Auto-fetched earnings for {earnings_info.get('company_name', 'Apple')}")
        
        print("Response preview:")
        print("-" * 40) 
        print(combined_result["result"][:400] + "..." if len(combined_result["result"]) > 400 else combined_result["result"])
        print("-" * 40)
        
        # Test 4: Test with invalid company
        print("\n❓ Test 4: Testing with invalid company...")
        invalid_result = rag.fetch_and_add_earnings("INVALID_COMPANY_XYZ")
        
        if invalid_result["status"] == "success":
            print("❌ Should have failed for invalid company")
            return False
        
        print(f"✅ Correctly handled invalid company: {invalid_result['message']}")
        
        print("\n🎉 All earnings integration tests passed!")
        print("✅ Earnings fetching, knowledge base integration, and querying all working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_earnings_integration()
    sys.exit(0 if success else 1)