# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/setup_ice_api_keys.py
# Interactive setup script for ICE news API keys
# Automatically configures all available news API providers with provided keys
# RELEVANT FILES: ice_data_ingestion/config.py, test_news_apis_demo.py, .env

"""
ICE News API Keys Setup Script

This script helps you quickly set up all available news API providers for the ICE system.
It reads your API keys from environment variables and configures the system properly.

The script will:
1. Set up environment variables from .env file
2. Create configuration file
3. Test API connections
4. Display quota information
5. Run a sample news fetch demo

Usage:
    python setup_ice_api_keys.py
    python setup_ice_api_keys.py --auto  # Skip prompts, use existing .env keys
    python setup_ice_api_keys.py --test-only  # Only test existing setup
    
Prerequisites:
    Create a .env file with your API keys:
    ALPHA_VANTAGE_API_KEY=your_key_here
    FMP_API_KEY=your_key_here
    NEWSAPI_ORG_API_KEY=your_key_here
    BENZINGA_API_TOKEN=your_key_here
    POLYGON_API_KEY=your_key_here
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import json

# Add ice_data_ingestion to path
sys.path.append(str(Path(__file__).parent / "ice_data_ingestion"))

from ice_data_ingestion.config import ICEConfig

def print_banner():
    """Print setup banner"""
    print("=" * 70)
    print("ICE NEWS API KEYS SETUP")
    print("Investment Context Engine - Multi-Provider News Integration")
    print("=" * 70)

def print_section(title: str):
    """Print section header"""
    print(f"\n{'-' * 60}")
    print(f" {title}")
    print(f"{'-' * 60}")

def get_provided_keys() -> Dict[str, str]:
    """Return the API keys from environment variables"""
    # Load .env file if it exists
    from pathlib import Path
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    # Get API keys from environment variables
    keys = {}
    env_keys = [
        'ALPHA_VANTAGE_API_KEY',
        'FMP_API_KEY', 
        'NEWSAPI_ORG_API_KEY',
        'BENZINGA_API_TOKEN',
        'POLYGON_API_KEY'
    ]
    
    for key in env_keys:
        value = os.getenv(key)
        if value:
            keys[key] = value
    
    return keys

def display_api_info():
    """Display information about each API provider"""
    print("\nAPI Provider Information:")
    print("=" * 50)
    
    providers = [
        {
            'name': 'Alpha Vantage',
            'tier': 'FREE (500 req/day)',
            'strengths': ['Real-time stock data', 'AI-powered sentiment', 'Official NASDAQ vendor'],
            'priority': 1
        },
        {
            'name': 'Financial Modeling Prep',
            'tier': 'FREE (250 req/day)',
            'strengths': ['Comprehensive financials', 'Social sentiment', 'RSS feeds'],
            'priority': 2
        },
        {
            'name': 'MarketAux',
            'tier': 'FREE (1000 req/day)',
            'strengths': ['Global news aggregation', 'AI sentiment', 'Multi-source'],
            'priority': 3
        },
        {
            'name': 'Polygon.io',
            'tier': 'FREE (5 req/min)',
            'strengths': ['Real-time market data', 'Benzinga partnership', 'Comprehensive'],
            'priority': 4
        },
        {
            'name': 'Benzinga',
            'tier': 'PAID (1000 req/month)',
            'strengths': ['Premium financial news', 'Analyst ratings', 'Professional grade'],
            'priority': 5
        },
        {
            'name': 'NewsAPI.org',
            'tier': 'FREE (100 req/day, 24h delay)',
            'strengths': ['150k+ sources', 'General news', 'Search capability'],
            'priority': 6
        }
    ]
    
    for provider in providers:
        print(f"\n{provider['priority']}. {provider['name']} - {provider['tier']}")
        print(f"   Strengths: {', '.join(provider['strengths'])}")

def setup_environment_variables(keys: Dict[str, str], interactive: bool = True) -> bool:
    """Set up environment variables for API keys"""
    print_section("ENVIRONMENT VARIABLES SETUP")
    
    # Create .env file
    env_file = Path('.env')
    env_content = []
    
    if env_file.exists():
        # Read existing .env file
        with open(env_file, 'r') as f:
            existing_lines = f.readlines()
        
        # Keep non-API key lines
        for line in existing_lines:
            if not any(key in line for key in keys.keys()):
                env_content.append(line.strip())
    
    # Add API keys
    env_content.append("# ICE News API Keys")
    for key, value in keys.items():
        env_content.append(f"{key}={value}")
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write('\n'.join(env_content))
    
    print(f"✓ Created/updated .env file with {len(keys)} API keys")
    
    # Set in current environment for immediate use
    for key, value in keys.items():
        os.environ[key] = value
    
    print("✓ Set environment variables for current session")
    return True

def create_config_file(interactive: bool = True) -> ICEConfig:
    """Create ICE configuration file"""
    print_section("CONFIGURATION FILE SETUP")
    
    # Create config with provided keys
    config = ICEConfig()
    
    # Save configuration
    config.save_configuration()
    
    # Validate configuration
    validation = config.validate_configuration()
    
    print(f"✓ Configuration file created: ice_config.json")
    print(f"✓ Configuration valid: {'Yes' if validation['valid'] else 'No'}")
    
    if validation['errors']:
        print(f"✗ Errors: {', '.join(validation['errors'])}")
    
    if validation['warnings']:
        print(f"⚠ Warnings: {', '.join(validation['warnings'])}")
    
    print(f"✓ Enabled APIs: {', '.join(validation['enabled_apis'])}")
    print(f"✓ Primary API: {validation['primary_api']}")
    
    return config

def test_api_connections(config: ICEConfig) -> Dict[str, bool]:
    """Test connections to all configured APIs"""
    print_section("API CONNECTION TESTING")
    
    manager = config.create_news_manager()
    results = {}
    
    # Test each provider
    providers = manager.get_available_providers()
    print(f"Testing {len(providers)} API providers...")
    
    for provider in providers:
        provider_name = provider.value
        print(f"\nTesting {provider_name.upper()}...")
        
        try:
            # Try to fetch a small number of articles
            articles = manager.get_financial_news("AAPL", limit=2, hours_back=48)
            
            if articles:
                results[provider_name] = True
                print(f"✓ {provider_name}: SUCCESS - Retrieved {len(articles)} articles")
                
                # Show sample article
                sample = articles[0]
                print(f"   Sample: {sample.title[:60]}...")
                print(f"   Source: {sample.source}")
                print(f"   Published: {sample.published_at.strftime('%Y-%m-%d %H:%M')}")
            else:
                results[provider_name] = False
                print(f"✗ {provider_name}: No articles returned")
                
        except Exception as e:
            results[provider_name] = False
            print(f"✗ {provider_name}: ERROR - {str(e)[:80]}...")
    
    # Summary
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f"CONNECTION TEST RESULTS: {successful}/{total} providers working")
    print(f"{'='*50}")
    
    return results

def display_quota_status(config: ICEConfig):
    """Display API quota information"""
    print_section("API QUOTA STATUS")
    
    manager = config.create_news_manager()
    quota_status = manager.get_all_quota_status()
    
    if not quota_status:
        print("No quota information available")
        return
    
    print("Current API Usage:")
    for provider, status in quota_status.items():
        print(f"\n{provider.upper()}:")
        print(f"  Used: {status['requests_used']}/{status['requests_per_day']}")
        remaining = status['requests_per_day'] - status['requests_used']
        print(f"  Remaining: {remaining}")
        usage_pct = (status['requests_used'] / status['requests_per_day']) * 100
        print(f"  Usage: {usage_pct:.1f}%")

def run_sample_demo(config: ICEConfig):
    """Run a sample news fetching demo"""
    print_section("SAMPLE NEWS DEMO")
    
    ticker = "NVDA"
    print(f"Fetching latest news for {ticker}...")
    
    manager = config.create_news_manager()
    
    # Fetch news
    articles = manager.get_financial_news(ticker, limit=5, hours_back=24)
    
    if articles:
        print(f"\n✓ Retrieved {len(articles)} articles for {ticker}")
        print("\nSample Articles:")
        
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article.title}")
            print(f"   Source: {article.source} ({article.provider.value})")
            print(f"   Published: {article.published_at.strftime('%Y-%m-%d %H:%M')}")
            if article.sentiment_score:
                sentiment = "Positive" if article.sentiment_score > 0.2 else ("Negative" if article.sentiment_score < -0.2 else "Neutral")
                print(f"   Sentiment: {sentiment} ({article.sentiment_score:.3f})")
            print(f"   URL: {article.url}")
        
        # Test sentiment aggregation
        sentiment_data = manager.get_aggregated_sentiment(ticker)
        if sentiment_data:
            print(f"\n📊 Aggregated Sentiment for {ticker}:")
            print(f"   Average: {sentiment_data['average']:.3f}")
            print(f"   Range: {sentiment_data['min']:.3f} to {sentiment_data['max']:.3f}")
            print(f"   Based on {sentiment_data['count']} articles")
    else:
        print(f"✗ No articles retrieved for {ticker}")

def print_next_steps():
    """Print next steps for the user"""
    print_section("NEXT STEPS")
    
    print("Your ICE news system is now configured! Here's what you can do:")
    print("\n1. Test the interactive demo:")
    print("   python test_news_apis_demo.py --interactive")
    
    print("\n2. Fetch news for a specific ticker:")
    print("   python test_news_apis_demo.py --ticker TSLA --limit 10")
    
    print("\n3. Use in your Python code:")
    print("   from ice_data_ingestion import ICEConfig")
    print("   config = ICEConfig()")
    print("   manager = config.create_news_manager()")
    print("   articles = manager.get_financial_news('AAPL', limit=20)")
    
    print("\n4. Integrate with Streamlit UI:")
    print("   # Add to UI/ice_ui_v17.py")
    print("   from ice_data_ingestion import ICEConfig")
    
    print("\n5. Monitor API usage:")
    print("   # Check quota status regularly to avoid hitting limits")
    print("   # Free tiers have daily/monthly limits")
    
    print("\n📁 Files created/updated:")
    print("   ✓ .env - Environment variables")
    print("   ✓ ice_config.json - Configuration file")
    print("   ✓ user_data/ - Cache directory")

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='ICE News API Keys Setup')
    parser.add_argument('--auto', action='store_true', help='Auto-setup with provided keys')
    parser.add_argument('--test-only', action='store_true', help='Only test existing setup')
    parser.add_argument('--no-demo', action='store_true', help='Skip the sample demo')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.test_only:
        print("Testing existing configuration...")
        config = ICEConfig()
        test_api_connections(config)
        display_quota_status(config)
        return
    
    # Display API information
    display_api_info()
    
    if not args.auto:
        print("\nThis script will set up your ICE news API integration with the provided keys.")
        proceed = input("\nProceed with setup? (y/N): ").strip().lower()
        if proceed != 'y':
            print("Setup cancelled.")
            return
    
    # Get API keys
    keys = get_provided_keys()
    
    # Setup environment variables
    if setup_environment_variables(keys, interactive=not args.auto):
        print("✓ Environment variables configured successfully")
    else:
        print("✗ Failed to configure environment variables")
        return
    
    # Create configuration file
    try:
        config = create_config_file(interactive=not args.auto)
        print("✓ Configuration file created successfully")
    except Exception as e:
        print(f"✗ Failed to create configuration: {e}")
        return
    
    # Test API connections
    try:
        connection_results = test_api_connections(config)
        working_count = sum(1 for success in connection_results.values() if success)
        
        if working_count == 0:
            print("⚠ Warning: No API connections are working. Check your keys and network.")
        elif working_count < len(connection_results):
            print(f"⚠ Warning: Only {working_count}/{len(connection_results)} APIs are working.")
        else:
            print("✓ All API connections are working!")
    except Exception as e:
        print(f"✗ Failed to test connections: {e}")
    
    # Display quota status
    try:
        display_quota_status(config)
    except Exception as e:
        print(f"⚠ Could not retrieve quota status: {e}")
    
    # Run sample demo
    if not args.no_demo:
        try:
            run_sample_demo(config)
        except Exception as e:
            print(f"⚠ Sample demo failed: {e}")
    
    # Print next steps
    print_next_steps()
    
    print(f"\n{'='*70}")
    print("ICE NEWS API SETUP COMPLETE! 🚀")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()