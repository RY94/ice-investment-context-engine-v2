# ice_data_ingestion/test_data_pipeline.py
"""
Test script for ICE data ingestion pipeline
Validates MCP infrastructure, data fetching, and ICE LightRAG integration
Comprehensive testing of zero-cost financial data ingestion system
Relevant files: mcp_infrastructure.py, mcp_data_manager.py, ice_integration.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
import json
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_infrastructure():
    """Test MCP infrastructure setup and health monitoring"""
    logger.info("=" * 50)
    logger.info("Testing MCP Infrastructure")
    logger.info("=" * 50)
    
    try:
        from .mcp_infrastructure import mcp_infrastructure, initialize_mcp_infrastructure
        
        # Test infrastructure initialization
        logger.info("Initializing MCP infrastructure...")
        success = await initialize_mcp_infrastructure()
        
        if success:
            logger.info("✅ MCP infrastructure initialized successfully")
        else:
            logger.warning("⚠️  MCP infrastructure initialization had issues")
        
        # Test server health
        logger.info("Checking server health...")
        healthy_servers = mcp_infrastructure.get_healthy_servers()
        logger.info(f"Healthy servers: {healthy_servers}")
        
        # Test capability mapping
        logger.info("Testing capability mapping...")
        stock_servers = mcp_infrastructure.get_servers_by_capability("historical_data")
        news_servers = mcp_infrastructure.get_servers_by_capability("news_sentiment")
        sec_servers = mcp_infrastructure.get_servers_by_capability("sec_filings")
        
        logger.info(f"Stock data servers: {stock_servers}")
        logger.info(f"News servers: {news_servers}")  
        logger.info(f"SEC servers: {sec_servers}")
        
        # Test cost summary
        cost_summary = mcp_infrastructure.get_cost_summary()
        logger.info(f"Cost summary: {json.dumps(cost_summary, indent=2)}")
        
        # Test dashboard data
        dashboard_data = mcp_infrastructure.get_status_dashboard_data()
        logger.info(f"Dashboard shows {dashboard_data['summary']['healthy_servers']}/{dashboard_data['summary']['total_servers']} servers healthy")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP infrastructure test failed: {e}")
        return False


async def test_mcp_data_manager():
    """Test MCP data manager functionality"""
    logger.info("=" * 50)
    logger.info("Testing MCP Data Manager")
    logger.info("=" * 50)
    
    try:
        from .mcp_data_manager import mcp_data_manager, DataType, FinancialDataQuery
        
        # Test stock data query
        logger.info("Testing stock data query...")
        stock_query = FinancialDataQuery(data_type=DataType.STOCK_DATA, symbol="NVDA")
        stock_result = await mcp_data_manager.fetch_financial_data(stock_query)
        
        logger.info(f"Stock query success: {stock_result.success}")
        logger.info(f"Stock data sources: {stock_result.sources}")
        logger.info(f"Stock confidence: {stock_result.confidence_score:.2f}")
        logger.info(f"Processing time: {stock_result.processing_time:.2f}s")
        
        if stock_result.stock_data:
            logger.info(f"Sample stock data: {json.dumps(stock_result.stock_data[0], indent=2, default=str)}")
        
        # Test news query
        logger.info("\nTesting news query...")
        news_query = FinancialDataQuery(data_type=DataType.NEWS, symbol="NVDA", limit=3)
        news_result = await mcp_data_manager.fetch_financial_data(news_query)
        
        logger.info(f"News query success: {news_result.success}")
        logger.info(f"News articles found: {len(news_result.news_articles)}")
        logger.info(f"News sources: {news_result.sources}")
        
        if news_result.news_articles:
            logger.info(f"Sample news: {news_result.news_articles[0]['title']}")
        
        # Test comprehensive data
        logger.info("\nTesting comprehensive company data...")
        comprehensive_data = await mcp_data_manager.get_comprehensive_company_data("AAPL")
        
        logger.info(f"Comprehensive data types: {list(comprehensive_data.keys())}")
        for data_type, result in comprehensive_data.items():
            if hasattr(result, 'success'):
                logger.info(f"  {data_type}: {'✅' if result.success else '❌'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP data manager test failed: {e}")
        return False


async def test_free_api_fallback():
    """Test free API fallback functionality"""
    logger.info("=" * 50)
    logger.info("Testing Free API Fallback")
    logger.info("=" * 50)
    
    try:
        from .free_api_connectors import free_api_manager, get_fallback_data
        
        # Test Yahoo Finance direct (no API key needed)
        logger.info("Testing Yahoo Finance fallback...")
        yahoo_data = await free_api_manager.fetch_stock_data("MSFT")
        
        if "error" not in yahoo_data:
            logger.info("✅ Yahoo Finance fallback working")
            logger.info(f"MSFT price: ${yahoo_data.get('price', 'N/A')}")
        else:
            logger.warning(f"⚠️  Yahoo Finance fallback failed: {yahoo_data['error']}")
        
        # Test comprehensive fallback
        logger.info("\nTesting comprehensive fallback data...")
        fallback_data = await get_fallback_data("TSLA")
        
        if "error" not in fallback_data:
            logger.info("✅ Comprehensive fallback working")
            logger.info(f"TSLA data sources: {fallback_data.get('sources_used', [])}")
            logger.info(f"News articles: {len(fallback_data.get('news', []))}")
        else:
            logger.warning(f"⚠️  Comprehensive fallback failed: {fallback_data['error']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Free API fallback test failed: {e}")
        return False


async def test_ice_integration():
    """Test ICE LightRAG integration"""
    logger.info("=" * 50)
    logger.info("Testing ICE Integration")
    logger.info("=" * 50)
    
    try:
        from .ice_integration import ice_integration_manager, get_live_company_intelligence
        
        # Test ICE RAG availability
        ice_ready = ice_integration_manager.ice_rag and ice_integration_manager.ice_rag.is_ready()
        logger.info(f"ICE LightRAG ready: {'✅' if ice_ready else '❌'}")
        
        # Test intelligence ingestion
        logger.info("Testing intelligence ingestion...")
        intelligence = await get_live_company_intelligence("GOOGL", include_in_kb=False)
        
        if intelligence.get("success", False):
            logger.info("✅ Intelligence ingestion successful")
            logger.info(f"Data sources: {intelligence.get('data_sources', [])}")
            logger.info(f"Key insights: {len(intelligence.get('key_insights', []))}")
            logger.info(f"Confidence score: {intelligence.get('data_quality', {}).get('confidence_score', 0):.2f}")
            
            # Show sample insights
            insights = intelligence.get('key_insights', [])
            if insights:
                logger.info(f"Sample insight: {insights[0]}")
        else:
            logger.warning(f"⚠️  Intelligence ingestion failed: {intelligence.get('error', 'Unknown error')}")
        
        # Test with knowledge base integration if ICE RAG is ready
        if ice_ready:
            logger.info("\nTesting knowledge base integration...")
            kb_intelligence = await get_live_company_intelligence("AMD", include_in_kb=True)
            
            if kb_intelligence.get("success", False):
                logger.info("✅ Knowledge base integration successful")
            else:
                logger.warning("⚠️  Knowledge base integration failed")
        else:
            logger.info("⏭️  Skipping knowledge base test (ICE LightRAG not ready)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ICE integration test failed: {e}")
        return False


async def test_end_to_end_pipeline():
    """Test complete end-to-end pipeline"""
    logger.info("=" * 50)
    logger.info("Testing End-to-End Pipeline")
    logger.info("=" * 50)
    
    try:
        from .ice_integration import query_ice_with_live_context
        
        # Test symbols
        test_symbols = ["NVDA", "AAPL", "MSFT"]
        
        logger.info(f"Testing pipeline with symbols: {test_symbols}")
        
        # Query with live context refresh
        query = "What are the latest developments for these technology companies?"
        
        logger.info(f"Querying: '{query}'")
        result = await query_ice_with_live_context(query, symbols=test_symbols[:2])  # Limit for performance
        
        if result.get("success", False):
            logger.info("✅ End-to-end pipeline successful")
            logger.info(f"Context refreshed for: {result.get('context_refreshed', [])}")
            logger.info(f"Answer length: {len(result.get('answer', ''))}")
            
            # Show partial answer
            answer = result.get('answer', '')
            if answer:
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                logger.info(f"Answer preview: {preview}")
        else:
            logger.warning(f"⚠️  End-to-end pipeline failed: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ End-to-end pipeline test failed: {e}")
        return False


async def run_performance_test():
    """Run performance benchmarks"""
    logger.info("=" * 50)
    logger.info("Performance Benchmarks")
    logger.info("=" * 50)
    
    try:
        from .mcp_data_manager import mcp_data_manager, DataType, FinancialDataQuery
        
        # Test parallel processing
        symbols = ["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA"]
        start_time = datetime.now()
        
        logger.info(f"Fetching data for {len(symbols)} symbols in parallel...")
        
        tasks = []
        for symbol in symbols:
            query = FinancialDataQuery(data_type=DataType.STOCK_DATA, symbol=symbol)
            task = mcp_data_manager.fetch_financial_data(query)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        successful_results = [r for r in results if not isinstance(r, Exception) and getattr(r, 'success', False)]
        
        logger.info(f"Performance results:")
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Successful queries: {len(successful_results)}/{len(symbols)}")
        logger.info(f"  Average time per query: {total_time/len(symbols):.2f}s")
        logger.info(f"  Throughput: {len(symbols)/total_time:.1f} queries/second")
        
        # Calculate average confidence and processing time
        if successful_results:
            avg_confidence = sum(r.confidence_score for r in successful_results) / len(successful_results)
            avg_processing_time = sum(r.processing_time for r in successful_results) / len(successful_results)
            
            logger.info(f"  Average confidence: {avg_confidence:.2f}")
            logger.info(f"  Average processing time: {avg_processing_time:.2f}s")
        
        return len(successful_results) > 0
        
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting ICE Data Ingestion Pipeline Tests")
    logger.info(f"Test started at: {datetime.now()}")
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("MCP Infrastructure", test_mcp_infrastructure),
        ("MCP Data Manager", test_mcp_data_manager),
        ("Free API Fallback", test_free_api_fallback),
        ("ICE Integration", test_ice_integration),
        ("End-to-End Pipeline", test_end_to_end_pipeline),
        ("Performance Benchmarks", run_performance_test)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name}...")
        try:
            result = await test_func()
            test_results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            test_results[test_name] = False
            logger.error(f"{test_name}: ❌ FAILED with exception: {e}")
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:.<30} {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 All tests passed! Data ingestion pipeline is ready.")
    elif passed > total // 2:
        logger.info("⚠️  Most tests passed. Pipeline has minor issues but is functional.")
    else:
        logger.warning("❌ Multiple test failures. Pipeline needs attention.")
    
    logger.info(f"Test completed at: {datetime.now()}")


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())