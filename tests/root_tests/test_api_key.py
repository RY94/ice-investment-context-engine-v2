# test_api_key.py
"""
Quick test to verify the API key is properly loaded from .env file
"""

import os
from dotenv import load_dotenv

def test_api_key_loading():
    """Test if API key is properly loaded from .env file"""
    print("🔧 Testing API key loading...")
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ No API key found in environment")
        print("Make sure .env file exists and contains OPENAI_API_KEY")
        return False
    
    if api_key.startswith("sk-proj-"):
        print("✅ OpenAI API key loaded successfully!")
        print(f"📝 Key format: {api_key[:15]}...{api_key[-10:]}")
        print("🔐 API key is ready for LightRAG")
        return True
    else:
        print("⚠️  API key found but format looks unusual")
        print(f"Expected to start with 'sk-proj-', got: {api_key[:10]}...")
        return False

if __name__ == "__main__":
    test_api_key_loading()
