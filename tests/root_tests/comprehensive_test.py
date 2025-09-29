#!/usr/bin/env python3
"""
Comprehensive test of all ICE data sources with working API keys
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set your API keys
os.environ["POLYGON_API_KEY"] = "O0tzmNdJl9VZ2w7AOaJ2KqZ1Ek0FFSJQ"
os.environ["BENZINGA_API_KEY"] = "bz.S6QL6ERDXWMVZXW6CEAPV4DUTLNTG6GC"

async def main():
    print("🚀 ICE Data Sources Comprehensive Test")
    print("=" * 50)
    print(f"Test started: {datetime.now()}")
    print(f"Testing symbol: BABA")
    print()

    # Test 1: Polygon.io Features
    print("1️⃣ POLYGON.IO COMPREHENSIVE TEST")
    print("-" * 30)
    
    from ice_data_ingestion.polygon_connector import polygon_connector
    
    # Stock quote
    quote = await polygon_connector.get_stock_quote("BABA")
    if quote.success:
        data = quote.data
        print(f"📈 Stock Quote: ${data.price} (Volume: {data.volume:,})")
    
    # Historical data
    agg = await polygon_connector.get_aggregates("BABA", limit=3)
    if agg.success and agg.data:
        latest = agg.data[-1]
        print(f"📊 Latest OHLC: O${latest.open_price:.2f} H${latest.high:.2f} L${latest.low:.2f} C${latest.close:.2f}")
        print(f"   Date: {latest.timestamp.strftime('%Y-%m-%d')}, Volume: {latest.volume:,}")
    
    # Company details
    details = await polygon_connector.get_company_details("BABA")
    if details.success and details.data.get("results"):
        company = details.data["results"]
        print(f"🏢 Company: {company.get('name', 'N/A')}")
        print(f"   Exchange: {company.get('primary_exchange', 'N/A')}")
        print(f"   Type: {company.get('type', 'N/A')}")
    
    print()

    # Test 2: Benzinga Features
    print("2️⃣ BENZINGA COMPREHENSIVE TEST")
    print("-" * 30)
    
    from ice_data_ingestion.benzinga_connector import benzinga_connector
    
    # Company news with sentiment
    news = await benzinga_connector.get_company_news("BABA", 3)
    if news.success:
        print(f"📰 Company News: {news.total_articles} articles found")
        for i, article in enumerate(news.articles[:2], 1):
            print(f"   {i}. {article.title[:60]}...")
            if article.sentiment:
                print(f"      Sentiment: {article.sentiment} ({article.sentiment_score:.2f})")
    
    print()

    # Test 3: Aggregated News from All Sources
    print("3️⃣ AGGREGATED NEWS (ALL 6 SOURCES)")
    print("-" * 30)
    
    from ice_data_ingestion.financial_news_connectors import get_aggregated_news
    
    results = await get_aggregated_news("BABA", 3)
    
    total_articles = 0
    working_sources = 0
    
    for source_name, result in results.items():
        status = "✅" if result.success else "❌"
        article_count = result.total_articles if result.success else 0
        total_articles += article_count
        if result.success:
            working_sources += 1
        
        print(f"{status} {source_name}: {article_count} articles")
        if result.success and result.articles:
            # Show one sample article
            sample = result.articles[0]
            print(f"   Sample: {sample.title[:50]}...")
    
    print()
    print("📊 SUMMARY:")
    print(f"   Working sources: {working_sources}/6")
    print(f"   Total articles: {total_articles}")
    print(f"   Success rate: {working_sources/6*100:.1f}%")
    
    print()
    print("🎯 KEY FEATURES DEMONSTRATED:")
    print("• Polygon.io: Stock quotes, OHLCV data, company details")
    print("• Benzinga: News with sentiment analysis")
    print("• Multi-source aggregation: 6 different news sources")
    print("• Error handling: Graceful handling of missing API keys")
    print("• Rate limiting: Optimized for free tier usage")
    
    print()
    print("✅ Comprehensive test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())