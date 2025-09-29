#!/usr/bin/env python3
"""
Test script to check if ICE data sources are working
"""
import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

DEMO_TICKER = "NVDA"

async def test_data_sources():
    print(f"🎯 Testing data sources with ticker: {DEMO_TICKER}")
    print(f"📅 Current time: {datetime.now()}")
    print("=" * 60)
    
    # Test 1: Yahoo Finance Fallback
    print("\n1. Testing Yahoo Finance Fallback...")
    try:
        from ice_data_ingestion import free_api_manager
        yahoo_data = await free_api_manager.fetch_stock_data(DEMO_TICKER)
        
        if "error" not in yahoo_data:
            print("✅ Yahoo Finance: SUCCESS")
            print(f"   Price: ${yahoo_data.get('price', 'N/A')}")
            print(f"   Change: {yahoo_data.get('change', 'N/A')} ({yahoo_data.get('change_percent', 'N/A')}%)")
        else:
            print(f"❌ Yahoo Finance: FAILED - {yahoo_data['error']}")
    except Exception as e:
        print(f"❌ Yahoo Finance: ERROR - {e}")
    
    # Test 2: Comprehensive Fallback
    print("\n2. Testing Comprehensive Fallback...")
    try:
        from ice_data_ingestion import get_fallback_data
        fallback_data = await get_fallback_data(DEMO_TICKER)
        
        if "error" not in fallback_data:
            print("✅ Comprehensive Fallback: SUCCESS")
            print(f"   Sources used: {fallback_data.get('sources_used', [])}")
            print(f"   News articles: {len(fallback_data.get('news', []))}")
        else:
            print(f"❌ Comprehensive Fallback: FAILED - {fallback_data['error']}")
    except Exception as e:
        print(f"❌ Comprehensive Fallback: ERROR - {e}")
    
    # Test 3: MCP Data Manager
    print("\n3. Testing MCP Data Manager...")
    try:
        from ice_data_ingestion import mcp_data_manager, DataType, FinancialDataQuery
        stock_query = FinancialDataQuery(data_type=DataType.STOCK_DATA, symbol=DEMO_TICKER)
        result = await mcp_data_manager.fetch_financial_data(stock_query)
        
        if result.success:
            print("✅ MCP Data Manager: SUCCESS")
            print(f"   Sources: {result.sources}")
            print(f"   Confidence: {result.confidence_score:.2f}")
        else:
            print("❌ MCP Data Manager: FAILED - No data returned")
    except Exception as e:
        print(f"❌ MCP Data Manager: ERROR - {e}")
    
    # Test 4: ICE Integration
    print("\n4. Testing ICE Integration...")
    try:
        from ice_data_ingestion import get_live_company_intelligence
        intelligence = await get_live_company_intelligence(DEMO_TICKER, include_in_kb=False)
        
        if intelligence.get("success"):
            print("✅ ICE Integration: SUCCESS")
            print(f"   Data sources: {intelligence.get('data_sources', [])}")
            print(f"   Key insights: {len(intelligence.get('key_insights', []))}")
        else:
            print(f"❌ ICE Integration: FAILED - {intelligence.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ ICE Integration: ERROR - {e}")
    
    # Test 5: Infrastructure Health
    print("\n5. Testing Infrastructure Health...")
    try:
        from ice_data_ingestion import mcp_infrastructure
        healthy_servers = mcp_infrastructure.get_healthy_servers()
        cost_summary = mcp_infrastructure.get_cost_summary()
        
        print(f"✅ Infrastructure Health: SUCCESS")
        print(f"   Healthy servers: {len(healthy_servers)} - {healthy_servers}")
        print(f"   Total cost: ${cost_summary['total_monthly_cost']}")
        print(f"   Free servers: {cost_summary['free_servers']}/{cost_summary['total_servers']}")
    except Exception as e:
        print(f"❌ Infrastructure Health: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Data source testing completed!")

if __name__ == "__main__":
    asyncio.run(test_data_sources())