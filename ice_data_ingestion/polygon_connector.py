# ice_data_ingestion/polygon_connector.py
"""
Polygon.io API connector for ICE Investment Context Engine
Provides access to Polygon.io financial data including news, market data, and real-time quotes
Handles rate limiting, authentication, and unified response format
Relevant files: financial_news_connectors.py, openbb_connector.py, benzinga_connector.py
"""

import asyncio
import logging
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json
import os

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, environment variables should be set manually

# Import shared data structures from financial_news_connectors
try:
    from .financial_news_connectors import NewsArticle, NewsResponse
except ImportError:
    # Fallback if running standalone
    from financial_news_connectors import NewsArticle, NewsResponse

logger = logging.getLogger(__name__)


@dataclass
class PolygonStockData:
    """Polygon.io stock data structure"""
    symbol: str
    price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open_price: Optional[float] = None
    previous_close: Optional[float] = None
    timestamp: Optional[datetime] = None
    market_status: Optional[str] = None


@dataclass
class PolygonAggregateData:
    """Polygon.io aggregate (OHLCV) data structure"""
    symbol: str
    timestamp: datetime
    open_price: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None  # Volume Weighted Average Price
    transactions: Optional[int] = None


@dataclass
class PolygonResponse:
    """Standardized Polygon.io API response"""
    success: bool
    data: Optional[Any] = None
    source_name: str = "Polygon.io"
    symbol: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    rate_limit_remaining: Optional[int] = None
    next_url: Optional[str] = None  # For pagination


class PolygonConnector:
    """Polygon.io API connector for financial data and news"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Polygon.io connector"""
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        
        # Rate limiting - Polygon.io has different limits based on plan
        # Basic plan: 5 requests per minute, Premium plans much higher
        self.rate_limit = 12.0  # 12 seconds between requests for basic plan (5 per minute)
        self.last_request_time = 0
        
        # Headers for all requests
        self.headers = {
            "User-Agent": "ICE-Investment-Context-Engine/1.0",
            "Accept": "application/json"
        }
    
    async def _rate_limit_delay(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            delay = self.rate_limit - time_since_last
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> PolygonResponse:
        """Make API request with error handling"""
        start_time = time.time()
        
        if not self.api_key:
            return PolygonResponse(
                success=False,
                error="Polygon.io API key required"
            )
        
        try:
            await self._rate_limit_delay()
            
            # Add API key to params
            params["apikey"] = self.api_key
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for Polygon.io specific error in response
                if data.get("status") == "ERROR":
                    return PolygonResponse(
                        success=False,
                        error=data.get("error", "Unknown Polygon.io API error"),
                        processing_time=processing_time
                    )
                
                return PolygonResponse(
                    success=True,
                    data=data,
                    processing_time=processing_time,
                    rate_limit_remaining=response.headers.get("X-RateLimit-Remaining"),
                    next_url=data.get("next_url")
                )
            elif response.status_code == 401:
                return PolygonResponse(
                    success=False,
                    error="Invalid or expired Polygon.io API key",
                    processing_time=processing_time
                )
            elif response.status_code == 429:
                return PolygonResponse(
                    success=False,
                    error="Rate limit exceeded - upgrade plan or wait",
                    processing_time=processing_time
                )
            elif response.status_code == 403:
                return PolygonResponse(
                    success=False,
                    error="Access denied - check subscription plan permissions",
                    processing_time=processing_time
                )
            else:
                return PolygonResponse(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Polygon.io API error: {e}")
            return PolygonResponse(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_stock_quote(self, symbol: str) -> PolygonResponse:
        """Get real-time stock quote"""
        response = await self._make_request(f"v2/aggs/ticker/{symbol}/prev", {})
        
        if response.success and response.data:
            results = response.data.get("results", [])
            if results:
                result = results[0]
                stock_data = PolygonStockData(
                    symbol=symbol,
                    price=result.get("c", 0.0),  # close price
                    open_price=result.get("o"),
                    high=result.get("h"),
                    low=result.get("l"),
                    volume=result.get("v"),
                    previous_close=result.get("c"),  # For previous day data
                    timestamp=datetime.fromtimestamp(result.get("t", 0) / 1000) if result.get("t") else datetime.now(),
                    market_status="closed"  # Previous day data is always closed
                )
                response.data = stock_data
                response.symbol = symbol
        
        return response
    
    async def get_real_time_quote(self, symbol: str) -> PolygonResponse:
        """Get real-time quote (requires higher tier subscription)"""
        response = await self._make_request(f"v1/last_quote/stocks/{symbol}", {})
        
        if response.success and response.data:
            last_quote = response.data.get("last", {})
            if last_quote:
                stock_data = PolygonStockData(
                    symbol=symbol,
                    price=(last_quote.get("bid", 0) + last_quote.get("ask", 0)) / 2,  # Mid price
                    timestamp=datetime.fromtimestamp(last_quote.get("timestamp", 0) / 1000000000) if last_quote.get("timestamp") else datetime.now(),
                    market_status="open"
                )
                response.data = stock_data
                response.symbol = symbol
        
        return response
    
    async def get_company_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        """Get company-specific news from Polygon.io"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Polygon.io",
                symbol=symbol,
                error="Polygon.io API key required"
            )
        
        try:
            params = {
                "ticker": symbol,
                "limit": limit,
                "sort": "published_utc",
                "order": "desc"
            }
            
            response = await self._make_request("v2/reference/news", params)
            processing_time = time.time() - start_time
            
            if response.success and response.data:
                articles = []
                results = response.data.get("results", [])
                
                for item in results:
                    # Parse published date
                    published = datetime.now()
                    if item.get("published_utc"):
                        try:
                            published = datetime.fromisoformat(item["published_utc"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    # Extract tickers (Polygon.io provides multiple tickers per article)
                    tickers = item.get("tickers", [])
                    article_symbol = symbol if symbol in tickers else (tickers[0] if tickers else symbol)
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        summary=item.get("description", ""),
                        url=item.get("article_url", ""),
                        published=published,
                        source=item.get("publisher", {}).get("name", "Polygon.io"),
                        symbol=article_symbol,
                        sentiment=None,  # Polygon.io doesn't provide built-in sentiment
                        sentiment_score=None,
                        category=None,
                        image_url=item.get("image_url"),
                        author=item.get("author")
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="Polygon.io",
                    symbol=symbol,
                    total_articles=len(articles),
                    processing_time=processing_time,
                    rate_limit_remaining=response.rate_limit_remaining
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Polygon.io",
                    symbol=symbol,
                    error=response.error or "No news data available",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Polygon.io news API error for {symbol}: {e}")
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Polygon.io",
                symbol=symbol,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_market_news(self, limit: int = 20) -> NewsResponse:
        """Get general market news from Polygon.io"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Polygon.io",
                error="Polygon.io API key required"
            )
        
        try:
            params = {
                "limit": limit,
                "sort": "published_utc",
                "order": "desc"
            }
            
            response = await self._make_request("v2/reference/news", params)
            processing_time = time.time() - start_time
            
            if response.success and response.data:
                articles = []
                results = response.data.get("results", [])
                
                for item in results:
                    published = datetime.now()
                    if item.get("published_utc"):
                        try:
                            published = datetime.fromisoformat(item["published_utc"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    # Get primary ticker if available
                    tickers = item.get("tickers", [])
                    primary_ticker = tickers[0] if tickers else None
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        summary=item.get("description", ""),
                        url=item.get("article_url", ""),
                        published=published,
                        source=item.get("publisher", {}).get("name", "Polygon.io"),
                        symbol=primary_ticker,
                        sentiment=None,
                        sentiment_score=None,
                        image_url=item.get("image_url"),
                        author=item.get("author")
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="Polygon.io",
                    total_articles=len(articles),
                    processing_time=processing_time,
                    rate_limit_remaining=response.rate_limit_remaining
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Polygon.io",
                    error=response.error or "No market news available",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Polygon.io",
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_aggregates(self, symbol: str, multiplier: int = 1, timespan: str = "day", from_date: str = None, to_date: str = None, limit: int = 50) -> PolygonResponse:
        """Get aggregate bars (OHLCV data)"""
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        
        endpoint = f"v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {"limit": limit}
        
        response = await self._make_request(endpoint, params)
        
        if response.success and response.data:
            results = response.data.get("results", [])
            aggregates = []
            
            for result in results:
                aggregate = PolygonAggregateData(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(result.get("t", 0) / 1000),
                    open_price=result.get("o", 0.0),
                    high=result.get("h", 0.0),
                    low=result.get("l", 0.0),
                    close=result.get("c", 0.0),
                    volume=result.get("v", 0),
                    vwap=result.get("vw"),
                    transactions=result.get("n")
                )
                aggregates.append(aggregate)
            
            response.data = aggregates
            response.symbol = symbol
        
        return response
    
    async def get_company_details(self, symbol: str) -> PolygonResponse:
        """Get company details and fundamentals"""
        response = await self._make_request(f"v3/reference/tickers/{symbol}", {})
        response.symbol = symbol
        return response
    
    async def get_market_status(self) -> PolygonResponse:
        """Get current market status"""
        return await self._make_request("v1/marketstatus/now", {})
    
    async def get_dividends(self, symbol: str, limit: int = 10) -> PolygonResponse:
        """Get dividend information for a symbol"""
        params = {"limit": limit}
        response = await self._make_request(f"v3/reference/dividends", {"ticker": symbol, **params})
        response.symbol = symbol
        return response


# Global instance
polygon_connector = PolygonConnector()


async def test_polygon_connector(symbol: str = "AAPL") -> Dict[str, bool]:
    """Test Polygon.io connector functionality"""
    tests = {}
    
    # Test stock quote
    try:
        quote_response = await polygon_connector.get_stock_quote(symbol)
        tests["stock_quote"] = quote_response.success
    except Exception as e:
        logger.error(f"Polygon.io stock quote test failed: {e}")
        tests["stock_quote"] = False
    
    # Test company news
    try:
        news_response = await polygon_connector.get_company_news(symbol, 3)
        tests["company_news"] = news_response.success
    except Exception as e:
        logger.error(f"Polygon.io company news test failed: {e}")
        tests["company_news"] = False
    
    # Test market news
    try:
        market_response = await polygon_connector.get_market_news(5)
        tests["market_news"] = market_response.success
    except Exception as e:
        logger.error(f"Polygon.io market news test failed: {e}")
        tests["market_news"] = False
    
    # Test aggregates (historical data)
    try:
        agg_response = await polygon_connector.get_aggregates(symbol, limit=5)
        tests["aggregates"] = agg_response.success
    except Exception as e:
        logger.error(f"Polygon.io aggregates test failed: {e}")
        tests["aggregates"] = False
    
    # Test company details
    try:
        details_response = await polygon_connector.get_company_details(symbol)
        tests["company_details"] = details_response.success
    except Exception as e:
        logger.error(f"Polygon.io company details test failed: {e}")
        tests["company_details"] = False
    
    return tests


if __name__ == "__main__":
    # Test the connector
    async def main():
        print("Testing Polygon.io Connector...")
        results = await test_polygon_connector("BABA")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test}: {status}")
    
    asyncio.run(main())