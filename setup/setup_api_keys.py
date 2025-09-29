#!/usr/bin/env python3
"""
setup_api_keys.py - Interactive script to set up API keys for ICE project
Run this script to easily configure your free API keys for financial data sources
"""

import os
import re
from pathlib import Path

def setup_api_keys():
    """Interactive setup for API keys"""
    print("🚀 ICE API Keys Setup")
    print("=" * 50)
    print("This script will help you set up free API keys for enhanced data sources.")
    print("All these APIs offer free tiers that are perfect for development and testing.")
    print()
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current .env file
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    api_keys = {
        'MARKETAUX_API_KEY': {
            'name': 'Marketaux',
            'url': 'https://www.marketaux.com/account/dashboard',
            'description': 'Financial news with sentiment analysis (100 requests/month free)',
            'current': None
        },
        'FINNHUB_API_KEY': {
            'name': 'Finnhub',
            'url': 'https://finnhub.io/register',
            'description': 'Stock data and financial news (60 calls/minute free)',
            'current': None
        },
        'ALPHA_VANTAGE_API_KEY': {
            'name': 'Alpha Vantage',
            'url': 'https://www.alphavantage.co/support/#api-key',
            'description': 'Stock data and technical indicators (25 requests/day free)',
            'current': None
        }
    }
    
    # Extract current values
    for key in api_keys:
        match = re.search(f'{key}=(.*)$', env_content, re.MULTILINE)
        if match:
            current_value = match.group(1).strip()
            api_keys[key]['current'] = current_value if current_value else None
    
    # Interactive setup
    updated_keys = {}
    
    for key, info in api_keys.items():
        print(f"\n📡 {info['name']} API Key")
        print(f"   Description: {info['description']}")
        print(f"   Sign up at: {info['url']}")
        
        current = info['current']
        if current:
            print(f"   Current: {current[:8]}...{current[-4:]} (configured)")
            update = input(f"   Update {info['name']} key? (y/N): ").lower().strip()
            if update not in ['y', 'yes']:
                continue
        else:
            print(f"   Current: Not set")
        
        while True:
            new_key = input(f"   Enter {info['name']} API key (or 'skip'): ").strip()
            
            if new_key.lower() == 'skip':
                break
            elif new_key == '':
                print("   ⚠️  Empty key entered. Use 'skip' to skip this key.")
                continue
            elif len(new_key) < 10:
                print("   ⚠️  API key seems too short. Please double-check.")
                continue
            else:
                updated_keys[key] = new_key
                print(f"   ✅ {info['name']} key configured!")
                break
    
    # Update .env file
    if updated_keys:
        print(f"\n🔄 Updating .env file with {len(updated_keys)} new key(s)...")
        
        for key, value in updated_keys.items():
            # Replace the line in env_content
            pattern = f'{key}=.*$'
            replacement = f'{key}={value}'
            env_content = re.sub(pattern, replacement, env_content, flags=re.MULTILINE)
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ .env file updated successfully!")
        
        # Test the keys
        print(f"\n🧪 Testing API keys...")
        os.environ.update(updated_keys)
        
        # Quick validation
        for key, value in updated_keys.items():
            print(f"   {key}: {'✅ Set' if os.getenv(key) else '❌ Not set'}")
        
    else:
        print("\n⏭️  No keys updated.")
    
    print(f"\n📊 Final Status:")
    for key, info in api_keys.items():
        current = os.getenv(key) or info['current']
        status = "✅ Configured" if current else "❌ Missing"
        print(f"   {info['name']:.<15} {status}")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Run 'python python_notebook/test_data_sources.py' to test all sources")
    print(f"   2. The system will automatically use configured API keys")
    print(f"   3. Fallback to free sources works even without API keys")
    
    return len(updated_keys) > 0


if __name__ == "__main__":
    setup_api_keys()