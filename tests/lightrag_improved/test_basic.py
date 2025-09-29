# lightrag/test_basic.py
"""
Basic test for ICE LightRAG integration
Simple test to verify everything works
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
from ice_rag import SimpleICERAG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_functionality() -> bool:
    """Test basic LightRAG functionality"""
    logger.info("🧪 Testing ICE LightRAG integration...")
    
    try:
        rag = SimpleICERAG()
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        return False
    
    if not rag.is_ready():
        logger.error("LightRAG not ready")
        return False
    
    logger.info("✅ LightRAG system initialized")
    
    sample_doc = """Apple Inc. (AAPL) reported strong Q4 2023 results with iPhone revenue of $43.8 billion.
    The company faces challenges in China market due to increased competition.
    Services revenue grew to $22.3 billion, showing strong recurring revenue growth."""
    
    logger.info("📄 Testing document processing...")
    result = rag.add_document(sample_doc, "earnings_report")
    
    if result["status"] != "success":
        logger.error(f"Document processing failed: {result['message']}")
        return False
    
    logger.info("✅ Document processed successfully")
    
    logger.info("❓ Testing query functionality...")
    test_queries = [
        ("What challenges does Apple face in China?", "hybrid"),
        ("What is Apple's iPhone revenue?", "local")
    ]
    
    for question, mode in test_queries:
        result = rag.query(question, mode)
        if result["status"] != "success":
            logger.error(f"Query failed: {result['message']}")
            return False
        logger.info(f"✅ Query successful (mode={mode})")
    
    return True


def main() -> int:
    """Main test function"""
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set")
        logger.info("Set it with: export OPENAI_API_KEY='your-key-here'")
        return 1
    
    try:
        if test_basic_functionality():
            logger.info("\n🎉 All tests passed!")
            return 0
        else:
            logger.error("\n❌ Tests failed")
            return 1
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
