# lightrag/test_basic.py
"""
Basic test for ICE LightRAG integration
Simple test to verify everything works
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ice_lightrag.ice_rag import SimpleICERAG


def test_basic_functionality():
    """Test basic LightRAG functionality"""
    print("🧪 Testing ICE LightRAG integration...")
    
    # Initialize system
    rag = SimpleICERAG()
    
    if not rag.is_ready():
        print("❌ LightRAG not ready. Check installation and API key.")
        return False
    
    print("✅ LightRAG system initialized")
    
    # Test document processing
    sample_doc = """
    Apple Inc. (AAPL) reported strong Q4 2023 results with iPhone revenue of $43.8 billion.
    The company faces challenges in China market due to increased competition.
    Services revenue grew to $22.3 billion, showing strong recurring revenue growth.
    """
    
    print("📄 Testing document processing...")
    result = rag.add_document(sample_doc, "earnings_report")
    
    if result["status"] != "success":
        print(f"❌ Document processing failed: {result['message']}")
        return False
    
    print("✅ Document processed successfully")
    
    # Test querying
    print("❓ Testing query functionality...")
    result = rag.query("What challenges does Apple face in China?")
    
    if result["status"] != "success":
        print(f"❌ Query failed: {result['message']}")
        return False
    
    print("✅ Query successful")
    print(f"📝 Answer: {result['result'][:200]}...")
    
    return True


def main():
    """Main test function"""
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Run tests
    if test_basic_functionality():
        print("\n🎉 All tests passed! LightRAG is ready for use.")
    else:
        print("\n❌ Tests failed. Check the errors above.")


if __name__ == "__main__":
    main()
