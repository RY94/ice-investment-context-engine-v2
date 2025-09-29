#!/usr/bin/env python3
"""
Test script for Polygon.io and Benzinga API integrations
Run this to verify both API keys work correctly
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
import os
from datetime import datetime

# Set API keys directly for testing
os.environ["POLYGON_API_KEY"] = "O0tzmNdJl9VZ2w7AOaJ2KqZ1Ek0FFSJQ"
os.environ["BENZINGA_API_KEY"] = "bz.S6QL6ERDXWMVZXW6CEAPV4DUTLNTG6GC"

from ice_data_ingestion.polygon_connector import polygon_connector
from ice_data_ingestion.benzinga_connector import benzinga_connector
from ice_data_ingestion.financial_news_connectors import get_aggregated_news

async def test_polygon_api():
    """Test Polygon.io API with real API key"""
    print("🔍 Testing Polygon.io API with provided key...")
    
    # Test stock quote
    print("\n📈 Testing stock quote...")
    quote_response = await polygon_connector.get_stock_quote("BABA")
    if quote_response.success:
        stock_data = quote_response.data
        print(f"✅ Stock Quote Success:")
        print(f"   Symbol: {stock_data.symbol}")
        print(f"   Price: ${stock_data.price}")
        print(f"   Volume: {stock_data.volume:,}" if stock_data.volume else "   Volume: N/A")
        print(f"   Date: {stock_data.timestamp.strftime('%Y-%m-%d')}")
    else:
        print(f"❌ Stock Quote Failed: {quote_response.error}")
    
    # Test company news
    print("\n📰 Testing company news...")
    news_response = await polygon_connector.get_company_news("BABA", 3)
    if news_response.success:
        print(f"✅ Company News Success: {news_response.total_articles} articles")
        for i, article in enumerate(news_response.articles[:2], 1):
            print(f"   {i}. {article.title[:60]}...")
            print(f"      Source: {article.source}")
    else:
        print(f"❌ Company News Failed: {news_response.error}")
    
    # Test market news
    print("\n🌍 Testing market news...")
    market_response = await polygon_connector.get_market_news(3)
    if market_response.success:
        print(f"✅ Market News Success: {market_response.total_articles} articles")
        for i, article in enumerate(market_response.articles[:2], 1):
            print(f"   {i}. {article.title[:60]}...")
    else:
        print(f"❌ Market News Failed: {market_response.error}")

async def test_benzinga_api():
    """Test Benzinga API with real API key"""
    print("\n🔍 Testing Benzinga API with provided key...")
    
    # Test company news
    print("\n📰 Testing company news...")
    news_response = await benzinga_connector.get_company_news("BABA", 3)
    if news_response.success:
        print(f"✅ Company News Success: {news_response.total_articles} articles")
        for i, article in enumerate(news_response.articles[:2], 1):
            print(f"   {i}. {article.title[:60]}...")
            if article.sentiment:
                print(f"      Sentiment: {article.sentiment} ({article.sentiment_score:.2f})")
    else:
        print(f"❌ Company News Failed: {news_response.error}")
    
    # Test analyst ratings
    print("\n⭐ Testing analyst ratings...")
    ratings_response = await benzinga_connector.get_analyst_ratings("BABA", 3)
    if ratings_response.success and ratings_response.data:
        ratings = ratings_response.data
        print(f"✅ Analyst Ratings Success: {len(ratings)} ratings")
        for i, rating in enumerate(ratings[:2], 1):
            print(f"   {i}. {rating.analyst_firm}: {rating.rating}")
            if rating.price_target:
                print(f"      Price Target: ${rating.price_target}")
    else:
        print(f"❌ Analyst Ratings Failed: {ratings_response.error}")

async def test_aggregated_news():
    """Test aggregated news with all sources"""
    print("\n🔍 Testing aggregated news with all 6 sources...")
    
    results = await get_aggregated_news("BABA", 2)
    
    print(f"\n📈 Results from {len(results)} sources:")
    total_articles = 0
    working_sources = 0
    
    for source_name, result in results.items():
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        article_count = result.total_articles if result.success else 0
        total_articles += article_count
        if result.success:
            working_sources += 1
        
        print(f"  {source_name:.<15} {status} ({article_count} articles)")
        if not result.success and result.error:
            print(f"    Error: {result.error}")
    
    print(f"\n📊 Summary:")
    print(f"  Working sources: {working_sources}/6")
    print(f"  Total articles: {total_articles}")
    print(f"  Success rate: {working_sources/6*100:.1f}%")

async def main():
    print(f"🧪 API Testing Started at {datetime.now()}")
    print("="*60)
    
    try:
        await test_polygon_api()
        await test_benzinga_api()
        await test_aggregated_news()
        
        print("\n" + "="*60)
        print("✅ API testing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())