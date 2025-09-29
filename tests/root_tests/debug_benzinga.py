#!/usr/bin/env python3
"""
Debug script for Benzinga API to see actual response format
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
import os

# Set API key
os.environ["BENZINGA_API_KEY"] = "bz.S6QL6ERDXWMVZXW6CEAPV4DUTLNTG6GC"

from ice_data_ingestion.benzinga_connector import benzinga_connector

async def debug_benzinga():
    """Debug Benzinga API response format"""
    print("🔍 Debugging Benzinga API...")
    
    # Test the raw API call
    from datetime import datetime, timedelta
    
    date_to = datetime.now()
    date_from = date_to - timedelta(days=30)
    
    params = {
        "tickers": "BABA",
        "pageSize": 3,
        "displayOutput": "full",
        "dateFrom": date_from.strftime("%Y-%m-%d"),
        "dateTo": date_to.strftime("%Y-%m-%d"),
        "sort": "created:desc"
    }
    
    print("Making raw API request...")
    response = await benzinga_connector._make_request("news", params)
    
    print(f"Success: {response.success}")
    print(f"Error: {response.error}")
    print(f"Data type: {type(response.data)}")
    
    if response.data:
        if isinstance(response.data, list):
            print(f"Data is list with {len(response.data)} items")
            if response.data:
                print(f"First item type: {type(response.data[0])}")
                if isinstance(response.data[0], dict):
                    print(f"First item keys: {list(response.data[0].keys())}")
                else:
                    print(f"First item value: {response.data[0]}")
        elif isinstance(response.data, dict):
            print(f"Data is dict with keys: {list(response.data.keys())}")
        else:
            print(f"Data content: {response.data}")

if __name__ == "__main__":
    asyncio.run(debug_benzinga())