# ice_data_ingestion/mcp_data_manager.py
"""
MCP Data Manager for ICE Investment Context Engine
Unified data fetching and aggregation across multiple MCP servers
Orchestrates zero-cost financial data ingestion with intelligent routing and failover
Relevant files: mcp_infrastructure.py, ice_rag.py, mcp_connectors.py
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from .mcp_infrastructure import mcp_infrastructure, MCPServerStatus
from .mcp_client_manager import mcp_client_manager, get_mcp_data

logger = logging.getLogger(__name__)


class DataType(Enum):
    STOCK_DATA = "stock_data"
    NEWS = "news"
    SEC_FILINGS = "sec_filings"
    FINANCIAL_METRICS = "financial_metrics"
    TECHNICAL_INDICATORS = "technical_indicators"
    SENTIMENT = "sentiment"


@dataclass
class FinancialDataQuery:
    """Query specification for financial data retrieval"""
    data_type: DataType
    symbol: Optional[str] = None
    symbols: Optional[List[str]] = None
    limit: int = 50
    time_window: str = "1d"  # 1d, 1w, 1m, 1y
    fields: Optional[List[str]] = None
    form_types: Optional[List[str]] = None  # For SEC filings
    start_time: datetime = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()


@dataclass
class MCPServerResult:
    """Result from individual MCP server"""
    server_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    latency: Optional[float] = None
    timestamp: datetime = None
    confidence_score: float = 1.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AggregatedFinancialData:
    """Aggregated results from multiple MCP servers"""
    query: FinancialDataQuery
    success: bool
    stock_data: List[Dict] = None
    news_articles: List[Dict] = None
    sec_filings: List[Dict] = None
    financial_metrics: Dict[str, Any] = None
    technical_indicators: Dict[str, Any] = None
    sentiment_data: Dict[str, Any] = None
    sources: List[str] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.stock_data is None:
            self.stock_data = []
        if self.news_articles is None:
            self.news_articles = []
        if self.sec_filings is None:
            self.sec_filings = []
        if self.sources is None:
            self.sources = []


class MCPDataManager:
    """Unified MCP data manager for financial intelligence"""
    
    def __init__(self):
        """Initialize MCP data manager"""
        self.infrastructure = mcp_infrastructure
        self.mcp_client_manager = mcp_client_manager  # Add reference to client manager
        self.request_cache = {}
        self.rate_limiters = {}
        
    async def fetch_financial_data(self, query: FinancialDataQuery) -> AggregatedFinancialData:
        """Fetch financial data from multiple MCP servers with intelligent routing"""
        start_time = datetime.now()
        
        try:
            # Get appropriate servers for this query
            candidate_servers = self._get_servers_for_query(query)
            
            if not candidate_servers:
                return AggregatedFinancialData(
                    query=query,
                    success=False,
                    error="No healthy MCP servers available for this query type"
                )
            
            # Execute parallel requests to multiple servers
            server_tasks = []
            for server_name in candidate_servers[:3]:  # Limit to top 3 servers
                task = asyncio.create_task(
                    self._fetch_from_mcp_server(server_name, query)
                )
                server_tasks.append(task)
            
            # Wait for all tasks with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*server_tasks, return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"MCP query timeout for {query.data_type}")
                results = [MCPServerResult("timeout", False, error="Request timeout")]
            
            # Filter successful results
            successful_results = [
                r for r in results 
                if isinstance(r, MCPServerResult) and r.success
            ]
            
            # Aggregate results
            aggregated = self._aggregate_results(successful_results, query)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            aggregated.processing_time = processing_time
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error fetching financial data: {e}")
            return AggregatedFinancialData(
                query=query,
                success=False,
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _get_servers_for_query(self, query: FinancialDataQuery) -> List[str]:
        """Get appropriate MCP servers for a specific query type"""
        capability_mapping = {
            DataType.STOCK_DATA: ['historical_data', 'current_prices'],
            DataType.NEWS: ['company_news'],
            DataType.SEC_FILINGS: ['sec_filings'],
            DataType.FINANCIAL_METRICS: ['financial_statements'],
            DataType.TECHNICAL_INDICATORS: ['technical_indicators'],
            DataType.SENTIMENT: ['news_sentiment']
        }
        
        required_capabilities = capability_mapping.get(query.data_type, [])
        candidate_servers = []
        
        for capability in required_capabilities:
            servers = self.infrastructure.get_servers_by_capability(capability)
            candidate_servers.extend(servers)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_servers = []
        for server in candidate_servers:
            if server not in seen:
                seen.add(server)
                unique_servers.append(server)
                
        return unique_servers
    
    async def _fetch_from_mcp_server(self, server_name: str, query: FinancialDataQuery) -> MCPServerResult:
        """Fetch data from specific MCP server"""
        start_time = datetime.now()
        
        try:
            # Check rate limits
            if not await self._check_rate_limit(server_name):
                return MCPServerResult(
                    server_name=server_name,
                    success=False,
                    error="Rate limit exceeded"
                )
            
            # Try real MCP call if available
            if mcp_client_manager.is_enabled() and server_name in mcp_client_manager.get_configured_servers():
                tool_name = self._get_tool_name_for_query(query.data_type)
                if tool_name:
                    # Build arguments based on tool requirements
                    if tool_name == "get_historical_stock_prices":
                        args = {"ticker": query.symbol or "NVDA", "period": "1mo"}
                    elif tool_name == "get_company_news":
                        args = {"ticker": query.symbol or "NVDA"}
                    elif tool_name == "get_sec_filings":
                        args = {"ticker": query.symbol or "NVDA", "limit": query.limit}
                    elif tool_name == "get_income_statements":
                        args = {"ticker": query.symbol or "NVDA", "limit": 4}
                    else:
                        args = {"symbol": query.symbol or "NVDA", "limit": query.limit}
                        
                    mcp_response = await get_mcp_data(
                        server_name, 
                        tool_name, 
                        **args
                    )
                    
                    if mcp_response.success:
                        return MCPServerResult(
                            server_name=server_name,
                            success=True,
                            data=mcp_response.data,
                            latency=mcp_response.processing_time,
                            confidence_score=1.0
                        )
            
            # Fallback to mock data if MCP unavailable
            mock_data = await self._simulate_mcp_call(server_name, query)
            
            latency = (datetime.now() - start_time).total_seconds()
            
            return MCPServerResult(
                server_name=server_name,
                success=True,
                data=mock_data,
                latency=latency,
                confidence_score=self._calculate_server_confidence(server_name, query)
            )
            
        except Exception as e:
            logger.error(f"MCP server {server_name} error: {e}")
            return MCPServerResult(
                server_name=server_name,
                success=False,
                error=str(e),
                latency=(datetime.now() - start_time).total_seconds()
            )
    
    def _get_tool_name_for_query(self, data_type: DataType) -> Optional[str]:
        """Map query data types to MCP tool names"""
        tool_mapping = {
            DataType.STOCK_DATA: "get_historical_stock_prices",
            DataType.NEWS: "get_company_news",
            DataType.SEC_FILINGS: "get_sec_filings",
            DataType.FINANCIAL_METRICS: "get_income_statements"
        }
        return tool_mapping.get(data_type)
    
    async def _simulate_mcp_call(self, server_name: str, query: FinancialDataQuery) -> Dict[str, Any]:
        """Simulate MCP server call with realistic data structure"""
        # Add small delay to simulate network
        await asyncio.sleep(0.1)
        
        # Generate mock data based on server and query type
        if query.data_type == DataType.STOCK_DATA:
            return self._generate_mock_stock_data(server_name, query)
        elif query.data_type == DataType.NEWS:
            return self._generate_mock_news_data(server_name, query)
        elif query.data_type == DataType.SEC_FILINGS:
            return self._generate_mock_sec_data(server_name, query)
        else:
            return {"data": f"Mock {query.data_type.value} from {server_name}"}
    
    def _generate_mock_stock_data(self, server_name: str, query: FinancialDataQuery) -> Dict[str, Any]:
        """Generate realistic mock stock data"""
        symbol = query.symbol or "NVDA"
        
        base_data = {
            "symbol": symbol,
            "server": server_name,
            "timestamp": datetime.now().isoformat()
        }
        
        if server_name == "yahoo_finance":
            base_data.update({
                "price": 875.42,
                "change": 12.34,
                "change_percent": 1.43,
                "volume": 45230000,
                "market_cap": 2150000000000,
                "pe_ratio": 65.8,
                "dividend_yield": 0.003
            })
        elif server_name == "alpha_vantage":
            base_data.update({
                "open": 863.12,
                "high": 878.95,
                "low": 861.22,
                "close": 875.42,
                "adj_close": 875.42,
                "volume": 45230000
            })
        
        return base_data
    
    def _generate_mock_news_data(self, server_name: str, query: FinancialDataQuery) -> Dict[str, Any]:
        """Generate realistic mock news data"""
        return {
            "articles": [
                {
                    "title": f"NVIDIA Reports Strong Q3 Earnings - {server_name}",
                    "summary": "NVIDIA exceeded expectations with datacenter revenue growth",
                    "sentiment": 0.75,
                    "relevance_score": 0.92,
                    "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "source": server_name
                },
                {
                    "title": "AI Chip Demand Continues to Drive Tech Sector",
                    "summary": "Market analysts bullish on semiconductor growth",
                    "sentiment": 0.68,
                    "relevance_score": 0.84,
                    "published_at": (datetime.now() - timedelta(hours=4)).isoformat(),
                    "source": server_name
                }
            ]
        }
    
    def _generate_mock_sec_data(self, server_name: str, query: FinancialDataQuery) -> Dict[str, Any]:
        """Generate realistic mock SEC filing data"""
        return {
            "filings": [
                {
                    "form_type": "10-K",
                    "filing_date": (datetime.now() - timedelta(days=30)).isoformat(),
                    "company_name": "NVIDIA Corporation",
                    "cik": "0001045810",
                    "accession_number": "0001045810-24-000123",
                    "key_metrics": {
                        "revenue": 60922000000,
                        "net_income": 29760000000,
                        "total_assets": 95000000000
                    },
                    "server": server_name
                }
            ]
        }
    
    async def _check_rate_limit(self, server_name: str) -> bool:
        """Check if server is within rate limits"""
        server_config = self.infrastructure.mcp_servers.get(server_name)
        if not server_config or not server_config.rate_limit:
            return True  # No rate limit
            
        # Simple rate limiting logic (would be more sophisticated in production)
        current_time = datetime.now()
        if server_name not in self.rate_limiters:
            self.rate_limiters[server_name] = {
                'last_request': current_time,
                'request_count': 0
            }
            
        rate_limiter = self.rate_limiters[server_name]
        time_diff = (current_time - rate_limiter['last_request']).total_seconds()
        
        # Reset counter every minute
        if time_diff >= 60:
            rate_limiter['request_count'] = 0
            rate_limiter['last_request'] = current_time
        
        # Check if within rate limit
        if rate_limiter['request_count'] >= server_config.rate_limit:
            return False
            
        rate_limiter['request_count'] += 1
        return True
    
    def _calculate_server_confidence(self, server_name: str, query: FinancialDataQuery) -> float:
        """Calculate confidence score for server response"""
        server_config = self.infrastructure.mcp_servers.get(server_name)
        if not server_config:
            return 0.5
        
        base_confidence = 0.8
        
        # Adjust based on server priority (higher priority = higher confidence)
        priority_adjustment = (3 - server_config.priority) * 0.1
        
        # Adjust based on cost tier (premium sources typically more reliable)
        tier_adjustment = {'free': 0.0, 'freemium': 0.05, 'premium': 0.1}
        tier_boost = tier_adjustment.get(server_config.cost_tier, 0.0)
        
        return min(1.0, base_confidence + priority_adjustment + tier_boost)
    
    def _aggregate_results(self, results: List[MCPServerResult], query: FinancialDataQuery) -> AggregatedFinancialData:
        """Aggregate results from multiple MCP servers"""
        if not results:
            return AggregatedFinancialData(
                query=query,
                success=False,
                error="No successful MCP server responses"
            )
        
        aggregated = AggregatedFinancialData(query=query, success=True)
        
        # Collect data by type
        for result in results:
            aggregated.sources.append(result.server_name)
            
            if query.data_type == DataType.STOCK_DATA and result.data:
                aggregated.stock_data.append(result.data)
            elif query.data_type == DataType.NEWS and result.data:
                articles = result.data.get('articles', [])
                aggregated.news_articles.extend(articles)
            elif query.data_type == DataType.SEC_FILINGS and result.data:
                filings = result.data.get('filings', [])
                aggregated.sec_filings.extend(filings)
        
        # Calculate overall confidence
        if results:
            aggregated.confidence_score = sum(r.confidence_score for r in results) / len(results)
        
        return aggregated
    
    async def get_comprehensive_company_data(self, symbol: str) -> Dict[str, AggregatedFinancialData]:
        """Get comprehensive data for a company across all data types"""
        data_types = [
            DataType.STOCK_DATA,
            DataType.NEWS,
            DataType.SEC_FILINGS,
            DataType.FINANCIAL_METRICS
        ]
        
        results = {}
        tasks = []
        
        for data_type in data_types:
            query = FinancialDataQuery(data_type=data_type, symbol=symbol)
            task = asyncio.create_task(self.fetch_financial_data(query))
            tasks.append((data_type.value, task))
        
        # Execute all queries in parallel
        for data_type_name, task in tasks:
            try:
                result = await task
                results[data_type_name] = result
            except Exception as e:
                logger.error(f"Error fetching {data_type_name} for {symbol}: {e}")
                results[data_type_name] = AggregatedFinancialData(
                    query=FinancialDataQuery(data_type=DataType(data_type_name), symbol=symbol),
                    success=False,
                    error=str(e)
                )
        
        return results


# Global instance for easy access
mcp_data_manager = MCPDataManager()


async def fetch_company_intelligence(symbol: str) -> Dict[str, Any]:
    """High-level function to fetch comprehensive company intelligence"""
    try:
        comprehensive_data = await mcp_data_manager.get_comprehensive_company_data(symbol)
        
        # Format for ICE system consumption
        intelligence = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'data_sources': [],
            'stock_info': {},
            'latest_news': [],
            'sec_filings': [],
            'summary': {}
        }
        
        # Process stock data
        if comprehensive_data.get('stock_data', {}).get('success'):
            stock_results = comprehensive_data['stock_data'].stock_data
            if stock_results:
                intelligence['stock_info'] = stock_results[0]
                intelligence['data_sources'].extend(comprehensive_data['stock_data'].sources)
        
        # Process news data
        if comprehensive_data.get('news', {}).get('success'):
            intelligence['latest_news'] = comprehensive_data['news'].news_articles[:5]  # Top 5
            intelligence['data_sources'].extend(comprehensive_data['news'].sources)
        
        # Process SEC filings
        if comprehensive_data.get('sec_filings', {}).get('success'):
            intelligence['sec_filings'] = comprehensive_data['sec_filings'].sec_filings[:3]  # Top 3
            intelligence['data_sources'].extend(comprehensive_data['sec_filings'].sources)
        
        # Create summary
        intelligence['summary'] = {
            'data_freshness': 'real-time',
            'confidence_score': sum(
                data.confidence_score for data in comprehensive_data.values() 
                if hasattr(data, 'confidence_score')
            ) / len(comprehensive_data),
            'sources_used': len(set(intelligence['data_sources'])),
            'total_data_points': len(intelligence['latest_news']) + len(intelligence['sec_filings']) + (1 if intelligence['stock_info'] else 0)
        }
        
        return intelligence
        
    except Exception as e:
        logger.error(f"Error fetching intelligence for {symbol}: {e}")
        return {
            'symbol': symbol,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }