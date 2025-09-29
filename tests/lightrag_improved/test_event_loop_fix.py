#!/usr/bin/env python3
"""
Test script to verify the event loop fix for multiple queries
Simulates the Streamlit scenario where multiple queries are made sequentially
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
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from pathlib import Path

# Add the current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ice_rag import SimpleICERAG

# Set up logging to see any errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_multiple_queries():
    """Test multiple sequential queries to reproduce and verify the fix"""
    
    print("🧪 Testing LightRAG Event Loop Fix")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please set it first:")
        print("export OPENAI_API_KEY='your-key-here'")
        return False
    
    try:
        # Initialize RAG (this should work)
        print("📊 Initializing SimpleICERAG...")
        rag = SimpleICERAG("storage/test_storage")
        
        if not rag.is_ready():
            print("❌ LightRAG not ready - check dependencies")
            return False
        
        print("✅ RAG initialized successfully")
        
        # Add sample document
        print("\n📄 Adding sample document...")
        sample_doc = """
        NVIDIA Corporation reported strong Q3 2024 results with revenue of $18.1 billion.
        Key risks include dependency on TSMC for chip manufacturing and China export restrictions.
        The company faces competition from AMD and Intel in the GPU market.
        Data center revenue was $14.5 billion, driven by AI chip demand.
        """
        
        result = rag.add_document(sample_doc, "earnings_report")
        if result["status"] != "success":
            print(f"❌ Failed to add document: {result['message']}")
            return False
        
        print("✅ Document added successfully")
        
        # Test multiple queries (this is where the error occurred before)
        queries = [
            "What are the risks to investing in NVIDIA?",
            "What was NVIDIA's revenue in Q3 2024?", 
            "Who are NVIDIA's main competitors?",
            "What drives NVIDIA's data center revenue?"
        ]
        
        print(f"\n🔍 Testing {len(queries)} sequential queries...")
        
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            
            try:
                result = rag.query(query, "hybrid")
                
                if result["status"] == "success":
                    print(f"✅ Query {i} successful")
                    print(f"Response preview: {result['result'][:100]}...")
                else:
                    print(f"❌ Query {i} failed: {result['message']}")
                    return False
                    
            except Exception as e:
                print(f"❌ Query {i} threw exception: {e}")
                return False
        
        print("\n🎉 All tests passed! Event loop fix is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_multiple_queries()
    sys.exit(0 if success else 1)