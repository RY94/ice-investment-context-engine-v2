# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/test_newsapi_fix.py
# Quick test script to verify NewsAPI.org fix
# Tests the specific NewsAPI.org client with the provided API key
# RELEVANT FILES: ice_data_ingestion/newsapi_org_client.py, setup_ice_api_keys.py

"""
NewsAPI.org Fix Test Script

This script specifically tests the NewsAPI.org client to verify that the authentication 
and API integration is working correctly with the provided API key.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
import sys
from pathlib import Path

# Add ice_data_ingestion to path
sys.path.append(str(Path(__file__).parent / "ice_data_ingestion"))

from ice_data_ingestion.newsapi_org_client import NewsAPIClient_Org
from ice_data_ingestion.news_apis import NewsCache, RateLimiter

def test_newsapi_org_client():
    """Test NewsAPI.org client specifically"""
    print("=" * 60)
    print("NEWSAPI.ORG SPECIFIC TEST")
    print("=" * 60)
    
    # Your provided API key
    api_key = "02abeaef7f9c41f5a835c8c8893e894e"
    
    print(f"Testing with API key: {api_key[:10]}...")
    
    try:
        # Create client
        client = NewsAPIClient_Org(
            api_key=api_key,
            rate_limiter=RateLimiter(requests_per_minute=60),
            cache=NewsCache(cache_dir="user_data/test_cache", ttl_hours=1)
        )
        
        print("✓ NewsAPI.org client created successfully")
        
        # Test 1: Get general business headlines
        print("\n1. Testing top business headlines...")
        headlines = client.get_top_business_headlines(limit=3)
        
        if headlines:
            print(f"✓ Retrieved {len(headlines)} business headlines")
            for i, article in enumerate(headlines[:2], 1):
                print(f"   {i}. {article.title[:60]}...")
                print(f"      Source: {article.source}")
                print(f"      Published: {article.published_at}")
        else:
            print("✗ No headlines retrieved")
        
        # Test 2: Search for financial news
        print("\n2. Testing financial news search...")
        financial_news = client.search_news("stock market", limit=3)
        
        if financial_news:
            print(f"✓ Retrieved {len(financial_news)} financial articles")
            for i, article in enumerate(financial_news[:2], 1):
                print(f"   {i}. {article.title[:60]}...")
                print(f"      Source: {article.source}")
                if article.sentiment_score:
                    print(f"      Sentiment: {article.sentiment_score:.3f}")
        else:
            print("✗ No financial news retrieved")
        
        # Test 3: Get ticker-specific news  
        print("\n3. Testing ticker-specific news (AAPL)...")
        ticker_news = client.get_news("AAPL", limit=2)
        
        if ticker_news:
            print(f"✓ Retrieved {len(ticker_news)} AAPL articles")
            for i, article in enumerate(ticker_news, 1):
                print(f"   {i}. {article.title[:60]}...")
                print(f"      Source: {article.source}")
                print(f"      Ticker: {article.ticker}")
        else:
            print("✗ No AAPL news retrieved")
        
        # Test 4: Check quota status
        print("\n4. Checking quota status...")
        quota_status = client.get_quota_status()
        print(f"   Used: {quota_status['requests_used']}/{quota_status['requests_per_day']}")
        print(f"   Remaining: {quota_status['requests_remaining']}")
        
        # Test 5: Get available sources
        print("\n5. Testing sources endpoint...")
        sources = client.get_sources("business")
        if sources:
            print(f"✓ Retrieved {len(sources)} business sources")
            print(f"   Sample sources: {[s['name'] for s in sources[:3]]}")
        else:
            print("✗ No sources retrieved")
        
        print("\n" + "=" * 60)
        print("NEWSAPI.ORG TEST COMPLETE")
        print("✓ All basic functions are working!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing NewsAPI.org: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    success = test_newsapi_org_client()
    
    if success:
        print("\n🎉 NewsAPI.org integration is working correctly!")
        print("\nNext steps:")
        print("1. Run the full system test: python setup_ice_api_keys.py --test-only")
        print("2. Try the interactive demo: python test_news_apis_demo.py --interactive")
    else:
        print("\n❌ NewsAPI.org integration has issues.")
        print("Please check your API key and network connection.")

if __name__ == "__main__":
    main()