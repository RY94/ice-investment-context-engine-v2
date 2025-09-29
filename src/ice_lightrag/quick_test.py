#!/usr/bin/env python3
"""Quick test to verify SimpleICERAG initialization and basic functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ice_rag import SimpleICERAG

def quick_test():
    print("🧪 Quick Event Loop Test")
    print("=" * 30)
    
    try:
        # Test initialization 
        print("📊 Creating SimpleICERAG instance...")
        rag = SimpleICERAG("./quick_test_storage")
        print("✅ Instance created successfully")
        
        # Test is_ready
        print("🔍 Checking if ready...")
        ready = rag.is_ready()
        print(f"✅ Ready status: {ready}")
        
        # Test multiple calls to is_ready (simulates multiple UI interactions)
        print("🔄 Testing multiple ready checks...")
        for i in range(3):
            ready = rag.is_ready()
            print(f"  Check {i+1}: {ready}")
        
        print("\n🎉 Basic functionality test passed!")
        print("✅ No PriorityQueue binding errors occurred")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)