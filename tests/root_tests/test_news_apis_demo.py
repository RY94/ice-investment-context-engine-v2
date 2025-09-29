# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/test_news_apis_demo.py
# Demo script for testing ICE news API integration
# Provides interactive testing of news API clients with real or mock data
# RELEVANT FILES: ice_data_ingestion/config.py, ice_data_ingestion/news_apis.py, ice_ui_v17.py

"""
ICE News API Demo and Testing Script

This script provides an interactive way to test the ICE news API integration system.
It can work with real API keys or demonstrate functionality with mock data.

Features:
- Configuration validation and setup
- Interactive API key configuration
- Real API testing with rate limiting
- Mock data demonstration
- Graph data processing demo
- Performance benchmarking

Usage:
    # Interactive demo
    python test_news_apis_demo.py
    
    # Quick test with specific ticker
    python test_news_apis_demo.py --ticker NVDA --limit 5
    
    # Test configuration only
    python test_news_apis_demo.py --config-only
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

# Add ice_data_ingestion to path
sys.path.append(str(Path(__file__).parent / "ice_data_ingestion"))

from ice_data_ingestion.config import ICEConfig, setup_api_keys_interactive
from ice_data_ingestion.news_apis import NewsAPIManager, NewsArticle, NewsAPIProvider, SentimentScore
from ice_data_ingestion.news_processor import NewsProcessor

def print_banner():
    """Print demo banner"""
    print("=" * 60)
    print("ICE NEWS API INTEGRATION DEMO")
    print("Investment Context Engine - Financial News System")
    print("=" * 60)

def print_section(title: str):
    """Print section header"""
    print(f"\n{'-' * 50}")
    print(f" {title}")
    print(f"{'-' * 50}")

def test_configuration():
    """Test and display configuration status"""
    print_section("CONFIGURATION TEST")
    
    config = ICEConfig()
    validation = config.validate_configuration()
    
    print(f"Configuration file: {config.config_file}")
    print(f"Cache directory: {config.config.cache_directory}")
    print(f"Configuration valid: {'✓' if validation['valid'] else '✗'}")
    
    if validation['errors']:
        print(f"Errors: {', '.join(validation['errors'])}")
    
    if validation['warnings']:
        print(f"Warnings: {', '.join(validation['warnings'])}")
    
    print(f"Enabled APIs: {', '.join(validation['enabled_apis']) if validation['enabled_apis'] else 'None'}")
    print(f"Primary API: {validation['primary_api'] or 'None'}")
    
    # Display API status
    api_status = config.get_api_status()
    print("\nAPI Status:")
    for api_name, status in api_status.items():
        status_icon = "✓" if status['enabled'] and status['has_key'] else "✗"
        primary_icon = " (PRIMARY)" if status['is_primary'] else ""
        print(f"  {status_icon} {api_name.upper()}: {'Enabled' if status['enabled'] else 'Disabled'}"
              f"{' - Missing API Key' if status['enabled'] and not status['has_key'] else ''}{primary_icon}")
    
    return config, validation

def create_mock_articles(count: int = 5) -> list[NewsArticle]:
    """Create mock news articles for demonstration"""
    mock_articles = []
    
    companies = ["NVDA", "TSMC", "AMD", "INTC", "AAPL"]
    news_templates = [
        "announces breakthrough AI chip technology",
        "reports strong quarterly earnings",
        "faces supply chain challenges in China",
        "expands manufacturing capabilities", 
        "partners with major cloud providers"
    ]
    
    for i in range(count):
        ticker = companies[i % len(companies)]
        template = news_templates[i % len(news_templates)]
        sentiment = 0.8 if "breakthrough" in template or "strong" in template else (-0.3 if "challenges" in template else 0.1)
        
        article = NewsArticle(
            title=f"Breaking: {ticker} {template}",
            content=f"{ticker} has made significant developments in their operations. "
                   f"The company's latest {template.split()[-1]} could impact their market position. "
                   f"Analysts are watching closely for effects on supply chain dependencies and competitive positioning.",
            url=f"https://example.com/news/{ticker.lower()}-{template.replace(' ', '-')}",
            source="Financial Demo News",
            published_at=datetime.now() - timedelta(hours=i*2),
            provider=NewsAPIProvider.ALPHA_VANTAGE,
            ticker=ticker,
            sentiment_score=sentiment,
            sentiment_label=SentimentScore.POSITIVE if sentiment > 0.2 else (SentimentScore.NEGATIVE if sentiment < -0.2 else SentimentScore.NEUTRAL),
            confidence=0.8,
            keywords=["technology", "earnings", "AI", "manufacturing"],
            entities=[ticker, "supply chain", "AI technology"],
            category="technology",
            metadata={"demo": True, "mock_data": True}
        )
        
        mock_articles.append(article)
    
    return mock_articles

def test_news_manager(config: ICEConfig, ticker: str = "NVDA", limit: int = 10):
    """Test news manager functionality"""
    print_section(f"NEWS MANAGER TEST - {ticker}")
    
    try:
        manager = config.create_news_manager()
        print(f"NewsAPIManager created successfully")
        
        # Check available providers
        providers = manager.get_available_providers()
        print(f"Available providers: {[p.value for p in providers]}")
        
        if not providers:
            print("No providers available, using mock data...")
            articles = create_mock_articles(limit)
        else:
            print(f"Fetching {limit} articles for {ticker}...")
            start_time = time.time()
            articles = manager.get_financial_news(ticker=ticker, limit=limit, hours_back=48)
            fetch_time = time.time() - start_time
            
            print(f"Fetched {len(articles)} articles in {fetch_time:.2f} seconds")
        
        if articles:
            print("\nSample Articles:")
            for i, article in enumerate(articles[:3]):  # Show first 3
                print(f"\n  Article {i+1}:")
                print(f"    Title: {article.title[:80]}...")
                print(f"    Source: {article.source} ({article.provider.value})")
                print(f"    Published: {article.published_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"    Sentiment: {article.sentiment_score} ({article.sentiment_label.name if article.sentiment_label else 'N/A'})")
                print(f"    Ticker: {article.ticker}")
                print(f"    URL: {article.url[:60]}...")
        
        # Test sentiment aggregation if providers available
        if providers:
            print(f"\nTesting sentiment aggregation for {ticker}...")
            sentiment_data = manager.get_aggregated_sentiment(ticker)
            if sentiment_data:
                print(f"Average sentiment: {sentiment_data['average']:.3f}")
                print(f"Sentiment range: {sentiment_data['min']:.3f} to {sentiment_data['max']:.3f}")
                print(f"Based on {sentiment_data['count']} articles")
        
        return articles
        
    except Exception as e:
        print(f"Error in news manager test: {e}")
        print("Falling back to mock data...")
        return create_mock_articles(limit)

def test_news_processor(articles: list[NewsArticle]):
    """Test news processor functionality"""
    print_section("NEWS PROCESSOR TEST")
    
    try:
        processor = NewsProcessor(cache_dir="user_data/news_processing_demo")
        
        print(f"Processing {len(articles)} articles...")
        start_time = time.time()
        entities, edges = processor.process_articles(articles)
        process_time = time.time() - start_time
        
        print(f"Processed in {process_time:.2f} seconds")
        print(f"Extracted {len(entities)} entities and {len(edges)} edges")
        
        # Show entity statistics
        entity_stats = processor.get_entity_statistics()
        print(f"\nEntity Statistics:")
        print(f"  Total entities: {entity_stats['total_entities']}")
        for entity_type, count in entity_stats['entity_types'].items():
            print(f"  {entity_type}: {count}")
        
        # Show sample edges
        print(f"\nSample Edges:")
        for i, edge in enumerate(edges[:5]):  # Show first 5 edges
            print(f"  {i+1}. {edge.source_entity} --[{edge.relationship_type}]--> {edge.target_entity}")
            print(f"     Weight: {edge.weight:.3f}, Confidence: {edge.confidence_score:.3f}")
        
        # Test LightRAG export
        print(f"\nTesting LightRAG export...")
        lightrag_content = processor.export_to_lightrag_format(articles)
        content_length = len(lightrag_content)
        print(f"Generated LightRAG document: {content_length} characters")
        
        # Save sample export
        export_file = Path("user_data/sample_lightrag_export.txt")
        export_file.parent.mkdir(parents=True, exist_ok=True)
        with open(export_file, 'w') as f:
            f.write(lightrag_content)
        print(f"Sample export saved to: {export_file}")
        
        return entities, edges
        
    except Exception as e:
        print(f"Error in news processor test: {e}")
        return [], []

def test_quota_status(config: ICEConfig):
    """Test and display API quota status"""
    print_section("API QUOTA STATUS")
    
    try:
        manager = config.create_news_manager()
        quota_status = manager.get_all_quota_status()
        
        if not quota_status:
            print("No API quota information available")
            return
        
        print("Current API Usage:")
        for provider, status in quota_status.items():
            print(f"\n  {provider.upper()}:")
            print(f"    Used: {status['requests_used']}/{status['requests_per_day']}")
            remaining = status['requests_per_day'] - status['requests_used']
            print(f"    Remaining: {remaining}")
            usage_pct = (status['requests_used'] / status['requests_per_day']) * 100
            print(f"    Usage: {usage_pct:.1f}%")
            print(f"    Last reset: {status['last_reset']}")
        
    except Exception as e:
        print(f"Error checking quota status: {e}")

def interactive_demo():
    """Run interactive demo"""
    print_banner()
    
    while True:
        print("\nICE News API Demo Menu:")
        print("1. Test Configuration")
        print("2. Setup API Keys")
        print("3. Test News Fetching")
        print("4. Test Data Processing")
        print("5. Full Workflow Demo")
        print("6. Check API Quotas")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            config, validation = test_configuration()
        
        elif choice == '2':
            print("\nStarting interactive API key setup...")
            config = setup_api_keys_interactive()
        
        elif choice == '3':
            config = ICEConfig()
            ticker = input("Enter ticker symbol (default: NVDA): ").strip() or "NVDA"
            limit = int(input("Number of articles (default: 10): ").strip() or "10")
            articles = test_news_manager(config, ticker, limit)
        
        elif choice == '4':
            print("Using sample articles for processing demo...")
            articles = create_mock_articles(8)
            entities, edges = test_news_processor(articles)
        
        elif choice == '5':
            print_section("FULL WORKFLOW DEMO")
            config = ICEConfig()
            ticker = input("Enter ticker symbol (default: AAPL): ").strip() or "AAPL"
            
            # Step 1: Fetch news
            articles = test_news_manager(config, ticker, 10)
            
            # Step 2: Process for graph
            if articles:
                entities, edges = test_news_processor(articles)
                print(f"\n✓ Complete workflow executed successfully!")
                print(f"  - Fetched {len(articles)} articles")
                print(f"  - Extracted {len(entities)} entities")
                print(f"  - Created {len(edges)} relationships")
        
        elif choice == '6':
            config = ICEConfig()
            test_quota_status(config)
        
        elif choice == '7':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please select 1-7.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='ICE News API Demo')
    parser.add_argument('--ticker', default='NVDA', help='Ticker symbol to test')
    parser.add_argument('--limit', type=int, default=10, help='Number of articles to fetch')
    parser.add_argument('--config-only', action='store_true', help='Test configuration only')
    parser.add_argument('--interactive', action='store_true', help='Run interactive demo')
    
    args = parser.parse_args()
    
    if args.interactive or len(sys.argv) == 1:
        interactive_demo()
    else:
        print_banner()
        
        # Test configuration
        config, validation = test_configuration()
        
        if args.config_only:
            return
        
        if validation['valid'] or not validation['enabled_apis']:
            # Test news fetching
            articles = test_news_manager(config, args.ticker, args.limit)
            
            # Test processing
            if articles:
                entities, edges = test_news_processor(articles)
                
                print_section("SUMMARY")
                print(f"✓ Successfully tested ICE news system")
                print(f"  - Configuration: {'Valid' if validation['valid'] else 'Using mock data'}")
                print(f"  - Articles fetched: {len(articles)}")
                print(f"  - Entities extracted: {len(entities) if 'entities' in locals() else 0}")
                print(f"  - Edges created: {len(edges) if 'edges' in locals() else 0}")

if __name__ == "__main__":
    main()