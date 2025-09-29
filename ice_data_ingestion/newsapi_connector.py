# ice_data_ingestion/newsapi_connector.py
"""
NewsAPI.org connector for ICE Investment Context Engine
Provides access to NewsAPI.org news articles from thousands of sources worldwide
Handles rate limiting, authentication, and unified response format
Relevant files: financial_news_connectors.py, polygon_connector.py, benzinga_connector.py
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
class NewsAPIResponse:
    """Standardized NewsAPI.org API response"""
    success: bool
    data: Optional[Any] = None
    source_name: str = "NewsAPI.org"
    symbol: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    rate_limit_remaining: Optional[int] = None
    total_results: Optional[int] = None


class NewsAPIConnector:
    """NewsAPI.org connector for financial news"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize NewsAPI connector"""
        self.api_key = api_key or os.getenv("NEWSAPI_API_KEY") or os.getenv("NEWS_API_KEY") or os.getenv("NEWSAPI_ORG_API_KEY")
        self.base_url = "https://newsapi.org/v2"
        
        # Rate limiting - NewsAPI has different limits based on plan
        # Free tier: 1000 requests per day, 100 per hour
        self.rate_limit = 36.0  # 36 seconds between requests for free tier (100/hour = ~36s)
        self.last_request_time = 0
        
        # Headers for all requests
        self.headers = {
            "User-Agent": "ICE-Investment-Context-Engine/1.0",
            "Accept": "application/json"
        }
        
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
    
    async def _rate_limit_delay(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            delay = self.rate_limit - time_since_last
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> NewsAPIResponse:
        """Make API request with error handling"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsAPIResponse(
                success=False,
                error="NewsAPI.org API key required"
            )
        
        try:
            await self._rate_limit_delay()
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for NewsAPI.org specific error in response
                if data.get("status") == "error":
                    return NewsAPIResponse(
                        success=False,
                        error=data.get("message", "Unknown NewsAPI.org error"),
                        processing_time=processing_time
                    )
                
                return NewsAPIResponse(
                    success=True,
                    data=data,
                    processing_time=processing_time,
                    rate_limit_remaining=response.headers.get("X-RateLimit-Remaining"),
                    total_results=data.get("totalResults")
                )
            elif response.status_code == 401:
                return NewsAPIResponse(
                    success=False,
                    error="Invalid or missing NewsAPI.org API key",
                    processing_time=processing_time
                )
            elif response.status_code == 429:
                return NewsAPIResponse(
                    success=False,
                    error="Rate limit exceeded - upgrade plan or wait",
                    processing_time=processing_time
                )
            elif response.status_code == 426:
                return NewsAPIResponse(
                    success=False,
                    error="Upgrade required - this endpoint requires a paid plan",
                    processing_time=processing_time
                )
            else:
                error_text = "Unknown error"
                try:
                    error_data = response.json()
                    error_text = error_data.get("message", error_text)
                except:
                    error_text = response.text[:200]
                    
                return NewsAPIResponse(
                    success=False,
                    error=f"HTTP {response.status_code}: {error_text}",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"NewsAPI.org API error: {e}")
            return NewsAPIResponse(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_company_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        """Get company-specific news from NewsAPI.org"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="NewsAPI.org",
                symbol=symbol,
                error="NewsAPI.org API key required"
            )
        
        try:
            # Calculate date range (last 30 days, NewsAPI free tier only allows last 30 days)
            date_to = datetime.now()
            date_from = date_to - timedelta(days=29)  # 29 days to be safe with free tier
            
            # Use company name or symbol in search query
            # Common company name mappings
            company_names = {
                "AAPL": "Apple",
                "GOOGL": "Google",
                "MSFT": "Microsoft",
                "AMZN": "Amazon",
                "TSLA": "Tesla",
                "META": "Meta",
                "NVDA": "Nvidia",
                "BABA": "Alibaba",
                "NFLX": "Netflix",
                "CRM": "Salesforce"
            }
            
            search_term = company_names.get(symbol.upper(), symbol)
            query = f'("{search_term}" OR "{symbol}") AND (stock OR shares OR earnings OR financial OR revenue)'
            
            params = {
                "q": query,
                "from": date_from.strftime("%Y-%m-%d"),
                "to": date_to.strftime("%Y-%m-%d"),
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": min(limit, 100)  # NewsAPI max is 100 per request
            }
            
            response = await self._make_request("everything", params)
            processing_time = time.time() - start_time
            
            if response.success and response.data:
                articles = []
                articles_data = response.data.get("articles", [])
                
                for item in articles_data:
                    # Skip removed articles
                    if item.get("title") == "[Removed]":
                        continue
                        
                    # Parse published date
                    published = datetime.now()
                    if item.get("publishedAt"):
                        try:
                            published = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    # Extract source name
                    source_name = "NewsAPI.org"
                    if item.get("source", {}).get("name"):
                        source_name = item["source"]["name"]
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        summary=item.get("description", ""),
                        url=item.get("url", ""),
                        published=published,
                        source=source_name,
                        symbol=symbol,
                        sentiment=None,  # NewsAPI doesn't provide sentiment
                        sentiment_score=None,
                        category=None,
                        image_url=item.get("urlToImage"),
                        author=item.get("author")
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="NewsAPI.org",
                    symbol=symbol,
                    total_articles=len(articles),
                    processing_time=processing_time,
                    rate_limit_remaining=response.rate_limit_remaining
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="NewsAPI.org",
                    symbol=symbol,
                    error=response.error or "No news data available",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"NewsAPI.org news API error for {symbol}: {e}")
            return NewsResponse(
                success=False,
                articles=[],
                source_name="NewsAPI.org",
                symbol=symbol,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_market_news(self, limit: int = 20) -> NewsResponse:
        """Get general market news from NewsAPI.org"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="NewsAPI.org",
                error="NewsAPI.org API key required"
            )
        
        try:
            # Get recent financial/business news
            date_to = datetime.now()
            date_from = date_to - timedelta(days=7)  # Last 7 days
            
            # Use business/finance focused query
            query = "(stock market OR Wall Street OR NYSE OR NASDAQ OR S&P 500 OR Dow Jones OR earnings OR IPO OR financial)"
            
            params = {
                "q": query,
                "from": date_from.strftime("%Y-%m-%d"),
                "to": date_to.strftime("%Y-%m-%d"),
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": min(limit, 100)
            }
            
            response = await self._make_request("everything", params)
            processing_time = time.time() - start_time
            
            if response.success and response.data:
                articles = []
                articles_data = response.data.get("articles", [])
                
                for item in articles_data:
                    # Skip removed articles
                    if item.get("title") == "[Removed]":
                        continue
                        
                    published = datetime.now()
                    if item.get("publishedAt"):
                        try:
                            published = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    # Extract source name
                    source_name = "NewsAPI.org"
                    if item.get("source", {}).get("name"):
                        source_name = item["source"]["name"]
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        summary=item.get("description", ""),
                        url=item.get("url", ""),
                        published=published,
                        source=source_name,
                        sentiment=None,
                        sentiment_score=None,
                        image_url=item.get("urlToImage"),
                        author=item.get("author")
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="NewsAPI.org",
                    total_articles=len(articles),
                    processing_time=processing_time,
                    rate_limit_remaining=response.rate_limit_remaining
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="NewsAPI.org",
                    error=response.error or "No market news available",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return NewsResponse(
                success=False,
                articles=[],
                source_name="NewsAPI.org",
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_headlines(self, category: str = "business", country: str = "us", limit: int = 20) -> NewsResponse:
        """Get top headlines from NewsAPI.org"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="NewsAPI.org",
                error="NewsAPI.org API key required"
            )
        
        try:
            params = {
                "category": category,
                "country": country,
                "pageSize": min(limit, 100)
            }
            
            response = await self._make_request("top-headlines", params)
            processing_time = time.time() - start_time
            
            if response.success and response.data:
                articles = []
                articles_data = response.data.get("articles", [])
                
                for item in articles_data:
                    if item.get("title") == "[Removed]":
                        continue
                        
                    published = datetime.now()
                    if item.get("publishedAt"):
                        try:
                            published = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    source_name = "NewsAPI.org"
                    if item.get("source", {}).get("name"):
                        source_name = item["source"]["name"]
                    
                    article = NewsArticle(
                        title=item.get("title", ""),
                        summary=item.get("description", ""),
                        url=item.get("url", ""),
                        published=published,
                        source=source_name,
                        sentiment=None,
                        sentiment_score=None,
                        image_url=item.get("urlToImage"),
                        author=item.get("author")
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="NewsAPI.org",
                    total_articles=len(articles),
                    processing_time=processing_time,
                    rate_limit_remaining=response.rate_limit_remaining
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="NewsAPI.org",
                    error=response.error or "No headlines available",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return NewsResponse(
                success=False,
                articles=[],
                source_name="NewsAPI.org",
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_sources(self, category: str = "business", language: str = "en", country: str = "us") -> NewsAPIResponse:
        """Get available news sources from NewsAPI.org"""
        params = {
            "category": category,
            "language": language,
            "country": country
        }
        
        response = await self._make_request("sources", params)
        return response


# Global instance
newsapi_connector = NewsAPIConnector()


async def test_newsapi_connector(symbol: str = "AAPL") -> Dict[str, bool]:
    """Test NewsAPI.org connector functionality"""
    tests = {}
    
    # Test company news
    try:
        news_response = await newsapi_connector.get_company_news(symbol, 5)
        tests["company_news"] = news_response.success
    except Exception as e:
        logger.error(f"NewsAPI.org company news test failed: {e}")
        tests["company_news"] = False
    
    # Test market news
    try:
        market_response = await newsapi_connector.get_market_news(5)
        tests["market_news"] = market_response.success
    except Exception as e:
        logger.error(f"NewsAPI.org market news test failed: {e}")
        tests["market_news"] = False
    
    # Test headlines
    try:
        headlines_response = await newsapi_connector.get_headlines("business", "us", 5)
        tests["headlines"] = headlines_response.success
    except Exception as e:
        logger.error(f"NewsAPI.org headlines test failed: {e}")
        tests["headlines"] = False
    
    return tests


if __name__ == "__main__":
    # Test the connector
    async def main():
        print("Testing NewsAPI.org Connector...")
        results = await test_newsapi_connector("BABA")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test}: {status}")
    
    asyncio.run(main())