# ice_data_ingestion/benzinga_connector.py
"""
Benzinga API connector for ICE Investment Context Engine
Provides access to Benzinga financial news, market data, and analyst insights
Handles rate limiting, authentication, and unified response format
Relevant files: financial_news_connectors.py, openbb_connector.py, free_api_connectors.py
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
class BenzingaRating:
    """Benzinga analyst rating data structure"""
    symbol: str
    analyst_firm: str
    rating: str  # Buy, Hold, Sell, etc.
    price_target: Optional[float] = None
    previous_rating: Optional[str] = None
    date: Optional[datetime] = None
    analyst_name: Optional[str] = None
    url: Optional[str] = None


@dataclass
class BenzingaEarnings:
    """Benzinga earnings data structure"""
    symbol: str
    date: datetime
    time: Optional[str] = None  # BMO, AMC, etc.
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_estimate: Optional[float] = None
    revenue_actual: Optional[float] = None
    importance: Optional[int] = None  # 0-5 scale


@dataclass
class BenzingaResponse:
    """Standardized Benzinga API response"""
    success: bool
    data: Optional[Any] = None
    source_name: str = "Benzinga"
    symbol: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    rate_limit_remaining: Optional[int] = None


class BenzingaConnector:
    """Benzinga API connector for financial data and news"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Benzinga connector"""
        self.api_key = api_key or os.getenv("BENZINGA_API_KEY") or os.getenv("BENZINGA_API_TOKEN")
        self.base_url = "https://api.benzinga.com/api/v2"
        
        # Rate limiting - Benzinga has strict limits
        # Basic plan: 1000 requests/month, Pro plans higher
        self.rate_limit = 3.0  # 3 seconds between requests to be conservative
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
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> BenzingaResponse:
        """Make API request with error handling"""
        start_time = time.time()
        
        if not self.api_key:
            return BenzingaResponse(
                success=False,
                error="Benzinga API key required"
            )
        
        try:
            await self._rate_limit_delay()
            
            # Add API key to params
            params["token"] = self.api_key
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return BenzingaResponse(
                    success=True,
                    data=data,
                    processing_time=processing_time,
                    rate_limit_remaining=response.headers.get("X-RateLimit-Remaining")
                )
            elif response.status_code == 401:
                return BenzingaResponse(
                    success=False,
                    error="Invalid or expired Benzinga API key",
                    processing_time=processing_time
                )
            elif response.status_code == 429:
                return BenzingaResponse(
                    success=False,
                    error="Rate limit exceeded",
                    processing_time=processing_time
                )
            elif response.status_code == 403:
                return BenzingaResponse(
                    success=False,
                    error="Access denied - check subscription plan",
                    processing_time=processing_time
                )
            else:
                return BenzingaResponse(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Benzinga API error: {e}")
            return BenzingaResponse(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_company_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        """Get company-specific news from Benzinga"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Benzinga",
                symbol=symbol,
                error="Benzinga API key required"
            )
        
        try:
            # Calculate date range (last 30 days)
            date_to = datetime.now()
            date_from = date_to - timedelta(days=30)
            
            params = {
                "tickers": symbol,
                "pageSize": limit,
                "displayOutput": "full",
                "dateFrom": date_from.strftime("%Y-%m-%d"),
                "dateTo": date_to.strftime("%Y-%m-%d"),
                "sort": "created:desc"
            }
            
            response = await self._make_request("news", params)
            processing_time = time.time() - start_time
            
            if response.success and response.data:
                articles = []
                
                # Handle different response formats from Benzinga API
                data_items = response.data
                if isinstance(response.data, dict) and "data" in response.data:
                    data_items = response.data["data"]
                elif isinstance(response.data, dict) and "results" in response.data:
                    data_items = response.data["results"]
                elif not isinstance(response.data, list):
                    # If it's not a list or dict with expected keys, skip processing
                    return NewsResponse(
                        success=False,
                        articles=[],
                        source_name="Benzinga",
                        symbol=symbol,
                        error="Unexpected API response format",
                        processing_time=processing_time
                    )
                
                for item in data_items:
                    # Skip non-dict items
                    if not isinstance(item, dict):
                        continue
                    # Parse published date
                    published = datetime.now()
                    if item.get("created"):
                        try:
                            published = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    elif item.get("updated"):
                        try:
                            published = datetime.fromisoformat(item["updated"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    # Extract sentiment if available
                    sentiment = None
                    sentiment_score = None
                    if "sentiment" in item:
                        sentiment_data = item["sentiment"]
                        if isinstance(sentiment_data, dict):
                            sentiment = sentiment_data.get("sentiment")
                            sentiment_score = sentiment_data.get("score")
                    
                    # Handle image URL extraction
                    image_url = None
                    if item.get("image"):
                        if isinstance(item["image"], dict):
                            image_url = item["image"].get("size", {}).get("large") if item["image"].get("size") else item["image"].get("url")
                        elif isinstance(item["image"], str):
                            image_url = item["image"]
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        summary=item.get("teaser", ""),
                        url=item.get("url", ""),
                        published=published,
                        source="Benzinga",
                        symbol=symbol,
                        sentiment=sentiment,
                        sentiment_score=sentiment_score,
                        category=None,
                        image_url=image_url,
                        author=item.get("author")
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="Benzinga",
                    symbol=symbol,
                    total_articles=len(articles),
                    processing_time=processing_time,
                    rate_limit_remaining=response.rate_limit_remaining
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Benzinga",
                    symbol=symbol,
                    error=response.error or "No news data available",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Benzinga news API error for {symbol}: {e}")
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Benzinga",
                symbol=symbol,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_market_news(self, limit: int = 20) -> NewsResponse:
        """Get general market news from Benzinga"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Benzinga",
                error="Benzinga API key required"
            )
        
        try:
            # Get recent market news
            date_to = datetime.now()
            date_from = date_to - timedelta(days=7)
            
            params = {
                "pageSize": limit,
                "displayOutput": "full",
                "dateFrom": date_from.strftime("%Y-%m-%d"),
                "dateTo": date_to.strftime("%Y-%m-%d"),
                "sort": "created:desc"
            }
            
            response = await self._make_request("news", params)
            processing_time = time.time() - start_time
            
            if response.success and response.data:
                articles = []
                
                # Handle different response formats from Benzinga API
                data_items = response.data
                if isinstance(response.data, dict) and "data" in response.data:
                    data_items = response.data["data"]
                elif isinstance(response.data, dict) and "results" in response.data:
                    data_items = response.data["results"]
                elif not isinstance(response.data, list):
                    # If it's not a list, skip processing
                    return NewsResponse(
                        success=False,
                        articles=[],
                        source_name="Benzinga",
                        error="Unexpected API response format",
                        processing_time=processing_time
                    )
                
                for item in data_items:
                    # Skip non-dict items
                    if not isinstance(item, dict):
                        continue
                    published = datetime.now()
                    if item.get("created"):
                        try:
                            published = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    # Extract sentiment if available
                    sentiment = None
                    sentiment_score = None
                    if "sentiment" in item:
                        sentiment_data = item["sentiment"]
                        if isinstance(sentiment_data, dict):
                            sentiment = sentiment_data.get("sentiment")
                            sentiment_score = sentiment_data.get("score")
                    
                    # Handle image URL extraction
                    image_url = None
                    if item.get("image"):
                        if isinstance(item["image"], dict):
                            image_url = item["image"].get("size", {}).get("large") if item["image"].get("size") else item["image"].get("url")
                        elif isinstance(item["image"], str):
                            image_url = item["image"]
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        summary=item.get("teaser", ""),
                        url=item.get("url", ""),
                        published=published,
                        source="Benzinga",
                        sentiment=sentiment,
                        sentiment_score=sentiment_score,
                        image_url=image_url,
                        author=item.get("author")
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="Benzinga",
                    total_articles=len(articles),
                    processing_time=processing_time,
                    rate_limit_remaining=response.rate_limit_remaining
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Benzinga",
                    error=response.error or "No market news available",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Benzinga",
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_analyst_ratings(self, symbol: str, limit: int = 10) -> BenzingaResponse:
        """Get analyst ratings for a symbol"""
        params = {
            "tickers": symbol,
            "pageSize": limit,
            "sort": "date:desc"
        }
        
        response = await self._make_request("calendar/ratings", params)
        
        if response.success and response.data:
            ratings = []
            
            # Handle different response formats from Benzinga API
            data_items = response.data
            if isinstance(response.data, dict) and "data" in response.data:
                data_items = response.data["data"]
            elif isinstance(response.data, dict) and "results" in response.data:
                data_items = response.data["results"]
            elif not isinstance(response.data, list):
                # If it's not a list, return empty ratings
                response.data = []
                return response
            
            for item in data_items:
                # Skip non-dict items
                if not isinstance(item, dict):
                    continue
                    
                rating_date = None
                if item.get("date"):
                    try:
                        rating_date = datetime.strptime(item["date"], "%Y-%m-%d")
                    except ValueError:
                        pass
                
                rating = BenzingaRating(
                    symbol=symbol,
                    analyst_firm=item.get("analyst", ""),
                    rating=item.get("rating_current", ""),
                    price_target=item.get("pt_current"),
                    previous_rating=item.get("rating_prior"),
                    date=rating_date,
                    analyst_name=item.get("analyst_name"),
                    url=item.get("url")
                )
                ratings.append(rating)
            
            response.data = ratings
            response.symbol = symbol
        
        return response
    
    async def get_earnings_calendar(self, symbol: str) -> BenzingaResponse:
        """Get earnings calendar for a symbol"""
        params = {
            "tickers": symbol,
            "sort": "date:desc"
        }
        
        response = await self._make_request("calendar/earnings", params)
        
        if response.success and response.data:
            earnings = []
            
            # Handle different response formats from Benzinga API
            data_items = response.data
            if isinstance(response.data, dict) and "data" in response.data:
                data_items = response.data["data"]
            elif isinstance(response.data, dict) and "results" in response.data:
                data_items = response.data["results"]
            elif not isinstance(response.data, list):
                # If it's not a list, return empty earnings
                response.data = []
                return response
            
            for item in data_items:
                # Skip non-dict items
                if not isinstance(item, dict):
                    continue
                    
                earnings_date = None
                if item.get("date"):
                    try:
                        earnings_date = datetime.strptime(item["date"], "%Y-%m-%d")
                    except ValueError:
                        pass
                
                earning = BenzingaEarnings(
                    symbol=symbol,
                    date=earnings_date,
                    time=item.get("time"),
                    eps_estimate=item.get("eps_est"),
                    eps_actual=item.get("eps"),
                    revenue_estimate=item.get("revenue_est"),
                    revenue_actual=item.get("revenue"),
                    importance=item.get("importance")
                )
                earnings.append(earning)
            
            response.data = earnings
            response.symbol = symbol
        
        return response
    
    async def get_dividends(self, symbol: str) -> BenzingaResponse:
        """Get dividend information for a symbol"""
        params = {
            "tickers": symbol,
            "sort": "ex:desc"
        }
        
        response = await self._make_request("calendar/dividends", params)
        response.symbol = symbol
        return response
    
    async def get_splits(self, symbol: str) -> BenzingaResponse:
        """Get stock split information for a symbol"""
        params = {
            "tickers": symbol,
            "sort": "ex:desc"
        }
        
        response = await self._make_request("calendar/splits", params)
        response.symbol = symbol
        return response


# Global instance
benzinga_connector = BenzingaConnector()


async def test_benzinga_connector(symbol: str = "AAPL") -> Dict[str, bool]:
    """Test Benzinga connector functionality"""
    tests = {}
    
    # Test company news
    try:
        news_response = await benzinga_connector.get_company_news(symbol, 3)
        tests["company_news"] = news_response.success
    except Exception as e:
        logger.error(f"Benzinga company news test failed: {e}")
        tests["company_news"] = False
    
    # Test market news
    try:
        market_response = await benzinga_connector.get_market_news(5)
        tests["market_news"] = market_response.success
    except Exception as e:
        logger.error(f"Benzinga market news test failed: {e}")
        tests["market_news"] = False
    
    # Test analyst ratings
    try:
        ratings_response = await benzinga_connector.get_analyst_ratings(symbol, 3)
        tests["analyst_ratings"] = ratings_response.success
    except Exception as e:
        logger.error(f"Benzinga analyst ratings test failed: {e}")
        tests["analyst_ratings"] = False
    
    # Test earnings calendar
    try:
        earnings_response = await benzinga_connector.get_earnings_calendar(symbol)
        tests["earnings_calendar"] = earnings_response.success
    except Exception as e:
        logger.error(f"Benzinga earnings calendar test failed: {e}")
        tests["earnings_calendar"] = False
    
    return tests


if __name__ == "__main__":
    # Test the connector
    async def main():
        print("Testing Benzinga Connector...")
        results = await test_benzinga_connector("BABA")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test}: {status}")
    
    asyncio.run(main())