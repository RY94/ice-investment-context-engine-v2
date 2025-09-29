#!/usr/bin/env python3
"""
Quick test to verify if notebook workflow will work successfully
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

DEMO_TICKER = "BABA"

async def test_notebook_workflow():
    """Test all the key components that the notebook uses"""
    print(f"🎯 Testing notebook workflow with {DEMO_TICKER}")
    
    results = {}
    
    # Test 1: MCP Data Manager
    try:
        from ice_data_ingestion import mcp_data_manager, DataType, FinancialDataQuery
        stock_query = FinancialDataQuery(data_type=DataType.STOCK_DATA, symbol=DEMO_TICKER)
        result = await mcp_data_manager.fetch_financial_data(stock_query)
        results["MCP Data Manager"] = result.success
        print(f"✅ MCP Data Manager: {result.success} (Sources: {result.sources})")
    except Exception as e:
        results["MCP Data Manager"] = False
        print(f"❌ MCP Data Manager: Failed - {e}")
    
    # Test 2: Free API Manager
    try:
        from ice_data_ingestion import free_api_manager
        yahoo_data = await free_api_manager.fetch_stock_data(DEMO_TICKER)
        success = "error" not in yahoo_data
        results["Free API Manager"] = success
        if success:
            print(f"✅ Free API Manager: SUCCESS (Price: ${yahoo_data.get('price', 'N/A')})")
        else:
            print(f"❌ Free API Manager: Failed - {yahoo_data.get('error', 'Unknown error')}")
    except Exception as e:
        results["Free API Manager"] = False
        print(f"❌ Free API Manager: Failed - {e}")
    
    # Test 3: Comprehensive Fallback
    try:
        from ice_data_ingestion import get_fallback_data
        fallback_data = await get_fallback_data(DEMO_TICKER)
        success = "error" not in fallback_data
        results["Comprehensive Fallback"] = success
        if success:
            print(f"✅ Comprehensive Fallback: SUCCESS (Sources: {fallback_data.get('sources_used', [])})")
        else:
            print(f"❌ Comprehensive Fallback: Failed - {fallback_data.get('error', 'Unknown error')}")
    except Exception as e:
        results["Comprehensive Fallback"] = False
        print(f"❌ Comprehensive Fallback: Failed - {e}")
    
    # Test 4: ICE Integration
    try:
        from ice_data_ingestion import get_live_company_intelligence
        intelligence = await get_live_company_intelligence(DEMO_TICKER, include_in_kb=False)
        success = intelligence.get("success", False)
        results["ICE Integration"] = success
        if success:
            insights = len(intelligence.get('key_insights', []))
            print(f"✅ ICE Integration: SUCCESS ({insights} insights generated)")
        else:
            print(f"❌ ICE Integration: Failed - {intelligence.get('error', 'Unknown error')}")
    except Exception as e:
        results["ICE Integration"] = False
        print(f"❌ ICE Integration: Failed - {e}")
    
    # Test 5: Infrastructure Health
    try:
        from ice_data_ingestion import mcp_infrastructure
        healthy_servers = mcp_infrastructure.get_healthy_servers()
        cost_summary = mcp_infrastructure.get_cost_summary()
        results["Infrastructure"] = True
        print(f"✅ Infrastructure: SUCCESS (Healthy: {len(healthy_servers)}, Cost: ${cost_summary['total_monthly_cost']})")
    except Exception as e:
        results["Infrastructure"] = False
        print(f"❌ Infrastructure: Failed - {e}")
    
    # Summary
    print("\n" + "="*50)
    print("NOTEBOOK READINESS SUMMARY")
    print("="*50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for component, success in results.items():
        status = "✅ READY" if success else "❌ NEEDS ATTENTION"
        print(f"{component:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} components ready ({passed/total*100:.1f}%)")
    
    if passed >= 3:  # At least 3/5 working
        print("🎉 Notebook should run successfully with working fallback!")
        return True
    else:
        print("⚠️ Notebook may have issues. Multiple components need attention.")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_notebook_workflow())