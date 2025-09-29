# ice_data_ingestion/openbb_connector.py
"""
OpenBB API connector for ICE Investment Context Engine
Provides access to OpenBB financial data including news, equity data, and market information
Handles rate limiting, authentication, and unified response format
Relevant files: financial_news_connectors.py, free_api_connectors.py, sec_edgar_connector.py
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
class OpenBBStockData:
    """OpenBB stock data structure"""
    symbol: str
    price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    timestamp: Optional[datetime] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None


@dataclass
class OpenBBResponse:
    """Standardized OpenBB API response"""
    success: bool
    data: Optional[Any] = None
    source_name: str = "OpenBB"
    symbol: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    rate_limit_remaining: Optional[int] = None


class OpenBBConnector:
    """OpenBB API connector for financial data and news"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenBB connector"""
        self.api_key = api_key or os.getenv("OPENBB_API_KEY")
        self.base_url = "https://api.openbb.co"
        
        # Rate limiting - OpenBB has different limits based on plan
        # Free tier: 100 requests per day, paid plans higher
        self.rate_limit = 2.0  # 2 seconds between requests to be conservative
        self.last_request_time = 0
        
        # Headers for all requests
        self.headers = {
            "User-Agent": "ICE-Investment-Context-Engine/1.0",
            "Accept": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def _rate_limit_delay(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            delay = self.rate_limit - time_since_last
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> OpenBBResponse:
        """Make API request with error handling"""
        start_time = time.time()
        
        if not self.api_key:
            return OpenBBResponse(
                success=False,
                error="OpenBB API key required"
            )
        
        try:
            await self._rate_limit_delay()
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return OpenBBResponse(
                    success=True,
                    data=data,
                    processing_time=processing_time,
                    rate_limit_remaining=response.headers.get("X-RateLimit-Remaining")
                )
            elif response.status_code == 401:
                return OpenBBResponse(
                    success=False,
                    error="Invalid or expired API key",
                    processing_time=processing_time
                )
            elif response.status_code == 429:
                return OpenBBResponse(
                    success=False,
                    error="Rate limit exceeded",
                    processing_time=processing_time
                )
            else:
                return OpenBBResponse(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"OpenBB API error: {e}")
            return OpenBBResponse(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_stock_quote(self, symbol: str) -> OpenBBResponse:
        """Get real-time stock quote"""
        params = {"symbol": symbol}
        response = await self._make_request("equity/price/quote", params)
        
        if response.success and response.data:
            # Transform data to standardized format
            raw_data = response.data
            stock_data = OpenBBStockData(
                symbol=symbol,
                price=raw_data.get("price", 0.0),
                change=raw_data.get("change"),
                change_percent=raw_data.get("change_percent"),
                volume=raw_data.get("volume"),
                market_cap=raw_data.get("market_cap"),
                pe_ratio=raw_data.get("pe_ratio"),
                timestamp=datetime.now(),
                currency=raw_data.get("currency", "USD"),
                exchange=raw_data.get("exchange")
            )
            response.data = stock_data
            response.symbol = symbol
        
        return response
    
    async def get_company_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        """Get company-specific news from OpenBB"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="OpenBB",
                symbol=symbol,
                error="OpenBB API key required"
            )
        
        try:
            params = {
                "symbol": symbol,
                "limit": limit,
                "sort": "published_utc",
                "order": "desc"
            }
            
            response = await self._make_request("equity/news", params)
            processing_time = time.time() - start_time
            
            if response.success and response.data:
                articles = []
                news_data = response.data.get("results", []) if isinstance(response.data, dict) else response.data
                
                for item in news_data:
                    # Parse published date
                    published = datetime.now()
                    if item.get("published_utc"):
                        try:
                            published = datetime.fromisoformat(item["published_utc"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        summary=item.get("description", ""),
                        url=item.get("article_url", ""),
                        published=published,
                        source=item.get("publisher", {}).get("name", "OpenBB"),
                        symbol=symbol,
                        sentiment=None,  # OpenBB might not provide sentiment
                        sentiment_score=None,
                        category=None,
                        image_url=item.get("image_url"),
                        author=item.get("author")
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="OpenBB",
                    symbol=symbol,
                    total_articles=len(articles),
                    processing_time=processing_time,
                    rate_limit_remaining=response.rate_limit_remaining
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="OpenBB",
                    symbol=symbol,
                    error=response.error or "No news data available",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"OpenBB news API error for {symbol}: {e}")
            return NewsResponse(
                success=False,
                articles=[],
                source_name="OpenBB",
                symbol=symbol,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_market_news(self, limit: int = 20) -> NewsResponse:
        """Get general market news from OpenBB"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="OpenBB",
                error="OpenBB API key required"
            )
        
        try:
            params = {
                "limit": limit,
                "sort": "published_utc",
                "order": "desc"
            }
            
            response = await self._make_request("news", params)
            processing_time = time.time() - start_time
            
            if response.success and response.data:
                articles = []
                news_data = response.data.get("results", []) if isinstance(response.data, dict) else response.data
                
                for item in news_data:
                    published = datetime.now()
                    if item.get("published_utc"):
                        try:
                            published = datetime.fromisoformat(item["published_utc"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        summary=item.get("description", ""),
                        url=item.get("article_url", ""),
                        published=published,
                        source=item.get("publisher", {}).get("name", "OpenBB"),
                        sentiment=None,
                        sentiment_score=None,
                        image_url=item.get("image_url"),
                        author=item.get("author")
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="OpenBB",
                    total_articles=len(articles),
                    processing_time=processing_time,
                    rate_limit_remaining=response.rate_limit_remaining
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="OpenBB",
                    error=response.error or "No market news available",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return NewsResponse(
                success=False,
                articles=[],
                source_name="OpenBB",
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_company_fundamentals(self, symbol: str) -> OpenBBResponse:
        """Get company fundamental data"""
        params = {"symbol": symbol}
        response = await self._make_request("equity/fundamental/overview", params)
        response.symbol = symbol
        return response
    
    async def get_earnings_calendar(self, date: Optional[str] = None) -> OpenBBResponse:
        """Get earnings calendar"""
        params = {}
        if date:
            params["date"] = date
        
        return await self._make_request("equity/calendar/earnings", params)
    
    async def get_economic_calendar(self, date: Optional[str] = None) -> OpenBBResponse:
        """Get economic calendar"""
        params = {}
        if date:
            params["date"] = date
            
        return await self._make_request("economy/calendar", params)


# Global instance
openbb_connector = OpenBBConnector()


async def test_openbb_connector(symbol: str = "AAPL") -> Dict[str, bool]:
    """Test OpenBB connector functionality"""
    tests = {}
    
    # Test stock quote
    try:
        quote_response = await openbb_connector.get_stock_quote(symbol)
        tests["stock_quote"] = quote_response.success
    except Exception as e:
        logger.error(f"OpenBB stock quote test failed: {e}")
        tests["stock_quote"] = False
    
    # Test company news
    try:
        news_response = await openbb_connector.get_company_news(symbol, 3)
        tests["company_news"] = news_response.success
    except Exception as e:
        logger.error(f"OpenBB company news test failed: {e}")
        tests["company_news"] = False
    
    # Test market news
    try:
        market_response = await openbb_connector.get_market_news(5)
        tests["market_news"] = market_response.success
    except Exception as e:
        logger.error(f"OpenBB market news test failed: {e}")
        tests["market_news"] = False
    
    return tests


if __name__ == "__main__":
    # Test the connector
    async def main():
        print("Testing OpenBB Connector...")
        results = await test_openbb_connector("BABA")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test}: {status}")
    
    asyncio.run(main())