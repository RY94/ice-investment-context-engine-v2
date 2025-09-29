# simple_demo.py
"""
Simple LightRAG demo for ICE Investment Context Engine
Direct implementation without complex imports
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_lightrag_directly():
    """Test LightRAG directly without our wrapper"""
    print("🚀 Testing LightRAG directly...")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No API key found. Make sure .env file contains OPENAI_API_KEY")
        return False
    
    print(f"✅ API key found: {api_key[:15]}...")
    
    try:
        # Import LightRAG components
        from lightrag import LightRAG, QueryParam
        from lightrag.llm import gpt_4o_mini_complete
        print("✅ LightRAG imported successfully")
        
        # Create working directory
        working_dir = "./storage"
        Path(working_dir).mkdir(exist_ok=True)
        
        # Initialize LightRAG
        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=gpt_4o_mini_complete
        )
        print("✅ LightRAG initialized")
        
        # Test document processing
        sample_doc = """
        NVIDIA Corporation (NVDA) reported strong Q3 2024 results with data center revenue 
        growing 206% year-over-year to $14.5 billion. The company's dependency on TSMC 
        for advanced chip manufacturing remains a key risk factor, especially given 
        geopolitical tensions between the US and China. Export controls on advanced 
        semiconductors continue to impact NVIDIA's ability to serve Chinese markets.
        """
        
        print("📄 Processing sample financial document...")
        
        async def process_and_query():
            # Insert document
            await rag.ainsert(sample_doc)
            print("✅ Document processed successfully")
            
            # Query the system
            query = "What are NVIDIA's main business risks?"
            print(f"❓ Querying: {query}")
            
            result = await rag.aquery(query, param=QueryParam(mode="hybrid"))
            print("✅ Query successful!")
            print(f"📝 Answer: {result}")
            
            return True
        
        # Run async operations
        return asyncio.run(process_and_query())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Try: pip install lightrag")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if test_lightrag_directly():
        print("\n🎉 LightRAG is working! Ready for ICE integration.")
    else:
        print("\n❌ LightRAG test failed. Check the errors above.")

