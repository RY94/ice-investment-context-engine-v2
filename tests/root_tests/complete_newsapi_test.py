#!/usr/bin/env python3
"""
Complete test of ICE system with all 7 news sources including NewsAPI.org
Demonstrates the comprehensive news coverage now available
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set your working API keys
os.environ["POLYGON_API_KEY"] = "O0tzmNdJl9VZ2w7AOaJ2KqZ1Ek0FFSJQ"
os.environ["BENZINGA_API_KEY"] = "bz.S6QL6ERDXWMVZXW6CEAPV4DUTLNTG6GC"
# NewsAPI key would go here: os.environ["NEWSAPI_API_KEY"] = "your-newsapi-key"

async def main():
    print("🎉 ICE Complete News Ecosystem Test")
    print("=" * 50)
    print(f"Test started: {datetime.now()}")
    print(f"Testing all 7 news sources for BABA")
    print()

    # Test aggregated news from all sources
    from ice_data_ingestion.financial_news_connectors import get_aggregated_news
    
    print("📰 TESTING ALL 7 NEWS SOURCES")
    print("-" * 40)
    
    results = await get_aggregated_news("BABA", 3)
    
    # Categorize sources by type
    financial_focused = ["Finnhub", "Marketaux", "Polygon.io", "Benzinga"]
    broad_coverage = ["NewsAPI.org"]
    real_time = ["Yahoo RSS"] 
    professional = ["OpenBB"]
    
    total_articles = 0
    working_sources = 0
    
    print(f"🔍 Results from {len(results)} integrated sources:")
    print()
    
    for source_name, result in results.items():
        status_icon = "✅" if result.success else "❌"
        article_count = result.total_articles if result.success else 0
        total_articles += article_count
        if result.success:
            working_sources += 1
        
        # Show category
        category = ""
        if source_name in financial_focused:
            category = "📊 Financial"
        elif source_name in broad_coverage:
            category = "🌍 Global"
        elif source_name in real_time:
            category = "⚡ Real-time"  
        elif source_name in professional:
            category = "💼 Professional"
            
        print(f"{status_icon} {source_name:<15} {category:<12} ({article_count} articles)")
        
        if result.success and result.articles:
            # Show sample article
            sample = result.articles[0]
            print(f"   📝 Sample: {sample.title[:60]}...")
            print(f"   📅 Published: {sample.published.strftime('%Y-%m-%d %H:%M')}")
            if hasattr(result, 'processing_time'):
                print(f"   ⏱️  Response time: {result.processing_time:.2f}s")
        elif not result.success:
            print(f"   ❌ Error: {result.error}")
        print()
    
    print("📊 COMPREHENSIVE SUMMARY")
    print("-" * 40)
    print(f"🎯 Total Sources Available: 7")
    print(f"✅ Working Sources: {working_sources}")
    print(f"📰 Total Articles Retrieved: {total_articles}")
    print(f"📈 Success Rate: {working_sources/7*100:.1f}%")
    print()
    
    # Show ecosystem breakdown
    print("🌟 NEWS ECOSYSTEM BREAKDOWN")
    print("-" * 40)
    
    financial_working = sum(1 for name, result in results.items() if name in financial_focused and result.success)
    print(f"📊 Financial-Focused Sources: {financial_working}/4 working")
    print(f"   • Specialized financial news and data")
    print(f"   • Market analysis and earnings coverage")
    print(f"   • Analyst ratings and sentiment analysis")
    print()
    
    global_working = sum(1 for name, result in results.items() if name in broad_coverage and result.success) 
    newsapi_status = "working" if results.get("NewsAPI.org", {}).success else "needs API key"
    print(f"🌍 Global News Coverage: {global_working}/1 ({newsapi_status})")
    print(f"   • 70,000+ sources worldwide when enabled")
    print(f"   • Business headlines and breaking news")
    print(f"   • International market perspectives")
    print()
    
    realtime_working = sum(1 for name, result in results.items() if name in real_time and result.success)
    print(f"⚡ Real-time Sources: {realtime_working}/1 working")
    print(f"   • Live RSS feeds")
    print(f"   • No API key required")
    print(f"   • Immediate news updates")
    print()
    
    professional_working = sum(1 for name, result in results.items() if name in professional and result.success)
    openbb_status = "working" if results.get("OpenBB", {}).success else "needs API key"
    print(f"💼 Professional Terminal Data: {professional_working}/1 ({openbb_status})")
    print(f"   • Bloomberg Terminal-grade data when enabled")
    print(f"   • Institutional-quality news feeds")
    print(f"   • Professional market analysis")
    print()
    
    print("🚀 NEXT STEPS")
    print("-" * 40)
    if working_sources < 7:
        missing = 7 - working_sources
        print(f"💡 Add {missing} more API key(s) to unlock full potential:")
        for name, result in results.items():
            if not result.success and "API key" in str(result.error):
                if name == "NewsAPI.org":
                    print(f"   • {name}: Get free key at https://newsapi.org/register")
                elif name == "OpenBB":
                    print(f"   • {name}: Get key at https://openbb.co/")
        print()
    
    print(f"🎉 ICE now has {working_sources} working news sources!")
    print("✨ Your investment research is powered by comprehensive")
    print("   global news coverage across multiple specialized sources")

if __name__ == "__main__":
    asyncio.run(main())