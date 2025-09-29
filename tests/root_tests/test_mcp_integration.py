#!/usr/bin/env python3
"""
Test script for MCP integration with ICE data ingestion system
Tests real MCP server connections and data retrieval
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

DEMO_TICKER = "NVDA"

async def test_mcp_client_manager():
    """Test MCP Client Manager functionality"""
    print("=" * 60)
    print("🔧 Testing MCP Client Manager")
    print("=" * 60)
    
    try:
        from ice_data_ingestion.mcp_client_manager import mcp_client_manager
        
        # Check if MCP is enabled
        print(f"MCP enabled: {mcp_client_manager.is_enabled()}")
        
        # Get configured servers
        servers = mcp_client_manager.get_configured_servers()
        print(f"Configured servers: {servers}")
        
        # Get server status
        for server_name in servers:
            status = await mcp_client_manager.get_server_status(server_name)
            print(f"Server {server_name}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Client Manager test failed: {e}")
        return False

async def test_mcp_data_manager():
    """Test MCP Data Manager with real MCP calls"""
    print("\n" + "=" * 60)
    print("📊 Testing MCP Data Manager")
    print("=" * 60)
    
    try:
        from ice_data_ingestion import mcp_data_manager, DataType, FinancialDataQuery
        
        # Enable MCP for testing using new reload method
        print("🔄 Enabling MCP for testing...")
        mcp_data_manager.mcp_client_manager.reload_config(enabled=True)
        print("✅ MCP enabled for testing")
        
        # Test stock data query
        print(f"\n🔍 Testing stock data query for {DEMO_TICKER}...")
        stock_query = FinancialDataQuery(data_type=DataType.STOCK_DATA, symbol=DEMO_TICKER)
        result = await mcp_data_manager.fetch_financial_data(stock_query)
        
        print(f"Success: {result.success}")
        print(f"Sources: {result.sources}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        if result.stock_data:
            sample_data = result.stock_data[0]
            print(f"\n📊 {DEMO_TICKER} Stock Data:")
            print(json.dumps(sample_data, indent=2, default=str))
        
        # Test comprehensive data
        print(f"\n🏢 Testing comprehensive data for {DEMO_TICKER}...")
        comprehensive_data = await mcp_data_manager.get_comprehensive_company_data(DEMO_TICKER)
        
        print(f"Data types available: {list(comprehensive_data.keys())}")
        for data_type, data_result in comprehensive_data.items():
            if hasattr(data_result, 'success'):
                status = "✅ Success" if data_result.success else "❌ Failed"
                confidence = f"({data_result.confidence_score:.2f})" if hasattr(data_result, 'confidence_score') else ""
                print(f"  {data_type:.<20} {status} {confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Data Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_yahoo_finance_mcp():
    """Test direct connection to Yahoo Finance MCP server"""
    print("\n" + "=" * 60)
    print("🔗 Testing Direct Yahoo Finance MCP Connection")
    print("=" * 60)
    
    try:
        from ice_data_ingestion.mcp_client_manager import get_mcp_data
        
        # Test direct MCP call
        print(f"Calling Yahoo Finance MCP for {DEMO_TICKER}...")
        
        response = await get_mcp_data(
            "yahoo_finance", 
            "get_stock_info", 
            ticker=DEMO_TICKER
        )
        
        print(f"Success: {response.success}")
        print(f"Server: {response.server_name}")
        print(f"Tool: {response.tool_name}")
        print(f"Processing time: {response.processing_time:.2f}s")
        
        if response.success:
            print(f"\n📈 MCP Response Data:")
            print(json.dumps(response.data, indent=2, default=str))
        else:
            print(f"❌ Error: {response.error}")
        
        return response.success
        
    except Exception as e:
        print(f"❌ Direct MCP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_infrastructure_integration():
    """Test integration with infrastructure manager"""
    print("\n" + "=" * 60)
    print("🏗️ Testing Infrastructure Integration")
    print("=" * 60)
    
    try:
        from ice_data_ingestion import mcp_infrastructure
        
        # Get healthy servers
        healthy_servers = mcp_infrastructure.get_healthy_servers()
        print(f"Healthy servers: {healthy_servers}")
        
        # Get server capabilities
        stock_servers = mcp_infrastructure.get_servers_by_capability("historical_data")
        print(f"Stock data servers: {stock_servers}")
        
        # Get cost summary
        cost_summary = mcp_infrastructure.get_cost_summary()
        print(f"Cost summary: {json.dumps(cost_summary, indent=2)}")
        
        # Test health monitoring
        print("\nTesting health monitoring...")
        for server_name in ["yahoo_finance", "sec_edgar", "alpha_vantage"]:
            try:
                # This will use real MCP client now
                status = await mcp_infrastructure._check_server_health(server_name)
                print(f"  {server_name}: {status.status.value} ({status.response_time_ms}ms)")
                if status.error_message:
                    print(f"    Error: {status.error_message}")
            except Exception as e:
                print(f"  {server_name}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Infrastructure integration test failed: {e}")
        return False

async def test_fallback_behavior():
    """Test fallback to direct APIs when MCP unavailable"""
    print("\n" + "=" * 60)
    print("🔄 Testing Fallback Behavior")
    print("=" * 60)
    
    try:
        from ice_data_ingestion.ice_integration import get_live_company_intelligence
        
        # Test intelligence with MCP potentially unavailable
        print(f"Testing intelligence for {DEMO_TICKER} with fallback...")
        
        intelligence = await get_live_company_intelligence(DEMO_TICKER, include_in_kb=False)
        
        if intelligence.get("success"):
            print("✅ Intelligence fetch successful")
            print(f"Data sources: {intelligence.get('data_sources', [])}")
            print(f"Confidence: {intelligence.get('data_quality', {}).get('confidence_score', 0):.2f}")
            
            insights = intelligence.get('key_insights', [])
            print(f"\n💡 Key Insights ({len(insights)} found):")
            for i, insight in enumerate(insights, 1):
                print(f"  {i}. {insight}")
                
        else:
            print(f"❌ Intelligence fetch failed: {intelligence.get('error', 'Unknown error')}")
            
        return intelligence.get("success", False)
        
    except Exception as e:
        print(f"❌ Fallback behavior test failed: {e}")
        return False

async def cleanup_test_config():
    """Reset MCP state after testing"""
    try:
        from ice_data_ingestion import mcp_data_manager
        
        # Reset MCP to disabled state
        mcp_data_manager.mcp_client_manager.set_enabled(False)
        print("🔄 MCP reset to disabled state")
    except Exception as e:
        print(f"⚠️ Could not reset MCP state: {e}")

async def main():
    """Run all MCP integration tests"""
    print("🚀 Starting MCP Integration Tests")
    print(f"Test started at: {datetime.now()}")
    print(f"🎯 Demo ticker: {DEMO_TICKER}")
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("MCP Client Manager", test_mcp_client_manager),
        ("MCP Data Manager", test_mcp_data_manager),
        ("Yahoo Finance MCP", test_yahoo_finance_mcp),
        ("Infrastructure Integration", test_infrastructure_integration),
        ("Fallback Behavior", test_fallback_behavior)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = await test_func()
            test_results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
        except Exception as e:
            test_results[test_name] = False
            print(f"{test_name}: ❌ FAILED with exception: {e}")
    
    # Cleanup
    await cleanup_test_config()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<35} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All MCP integration tests passed!")
    elif passed > total // 2:
        print("⚠️ Most tests passed. Some MCP features may have issues.")
    else:
        print("❌ Multiple test failures. MCP integration needs attention.")
    
    print(f"Test completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())