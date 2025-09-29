# ice_data_ingestion/financial_news_connectors.py
"""
Financial News API Connectors for ICE Investment Context Engine
Provides direct access to multiple financial news sources including Finnhub, Marketaux, and Yahoo RSS
Handles rate limiting, data parsing, and unified response format
Relevant files: free_api_connectors.py, sec_edgar_connector.py
"""

import asyncio
import logging
import time
import requests
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, environment variables should be set manually
from dataclasses import dataclass
import json
import re
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Standardized news article data structure"""
    title: str
    summary: str
    url: str
    published: datetime
    source: str
    symbol: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    author: Optional[str] = None


@dataclass
class NewsResponse:
    """Standardized news response"""
    success: bool
    articles: List[NewsArticle]
    source_name: str
    symbol: Optional[str] = None
    total_articles: int = 0
    error: Optional[str] = None
    processing_time: float = 0.0
    rate_limit_remaining: Optional[int] = None


class FinnhubNewsConnector:
    """Finnhub.io news API connector"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Finnhub connector"""
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        
        # Rate limiting: 60 requests/minute on free tier
        self.rate_limit = 1.0  # 1 second between requests to be safe
        self.last_request_time = 0
    
    async def _rate_limit_delay(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            delay = self.rate_limit - time_since_last
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def get_company_news(self, symbol: str, days_back: int = 7) -> NewsResponse:
        """Get company-specific news with improved error handling and retry logic"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Finnhub",
                symbol=symbol,
                error="API key required for Finnhub"
            )
        
        # Retry logic for connection issues
        max_retries = 3
        retry_delay = 2.0  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                await self._rate_limit_delay()
                
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                params = {
                    'symbol': symbol,
                    'from': start_date.strftime('%Y-%m-%d'),
                    'to': end_date.strftime('%Y-%m-%d'),
                    'token': self.api_key
                }
                
                url = f"{self.base_url}/company-news"
                
                # Enhanced request with better session handling and headers
                headers = {
                    'User-Agent': 'ICE-Investment-Engine/1.0',
                    'Accept': 'application/json',
                    'Connection': 'close'  # Force connection close to avoid keep-alive issues
                }
                
                # Use a fresh session for each request to avoid connection pooling issues
                with requests.Session() as session:
                    session.headers.update(headers)
                    response = session.get(
                        url, 
                        params=params, 
                        timeout=20,  # Increased timeout
                        verify=True  # Explicitly verify SSL
                    )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    articles = []
                    for item in data:
                        article = NewsArticle(
                            title=item.get('headline', ''),
                            summary=item.get('summary', ''),
                            url=item.get('url', ''),
                            published=datetime.fromtimestamp(item.get('datetime', 0)),
                            source=item.get('source', 'Finnhub'),
                            symbol=symbol,
                            category=item.get('category', ''),
                            image_url=item.get('image', ''),
                            sentiment=None,
                            sentiment_score=None
                        )
                        articles.append(article)
                    
                    return NewsResponse(
                        success=True,
                        articles=articles,
                        source_name="Finnhub",
                        symbol=symbol,
                        total_articles=len(articles),
                        processing_time=processing_time
                    )
                else:
                    error_msg = f"HTTP {response.status_code}"
                    if response.status_code == 429:
                        error_msg = "Rate limit exceeded"
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * 2)  # Longer delay for rate limits
                            continue
                    elif response.status_code == 401:
                        error_msg = "Invalid API key"
                    
                    return NewsResponse(
                        success=False,
                        articles=[],
                        source_name="Finnhub",
                        symbol=symbol,
                        error=error_msg,
                        processing_time=processing_time
                    )
                    
            except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                # Handle connection-specific errors with retries
                if attempt < max_retries - 1:
                    logger.warning(f"Finnhub connection error for {symbol} (attempt {attempt + 1}): {e}. Retrying...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
                else:
                    processing_time = time.time() - start_time
                    logger.error(f"Finnhub API connection failed after {max_retries} attempts for {symbol}: {e}")
                    return NewsResponse(
                        success=False,
                        articles=[],
                        source_name="Finnhub",
                        symbol=symbol,
                        error=f"Connection failed after {max_retries} attempts: {str(e)}",
                        processing_time=processing_time
                    )
                    
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Finnhub timeout for {symbol} (attempt {attempt + 1}): {e}. Retrying...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                else:
                    processing_time = time.time() - start_time
                    return NewsResponse(
                        success=False,
                        articles=[],
                        source_name="Finnhub",
                        symbol=symbol,
                        error=f"Timeout after {max_retries} attempts",
                        processing_time=processing_time
                    )
                    
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"Finnhub API error for {symbol}: {e}")
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Finnhub",
                    symbol=symbol,
                    error=str(e),
                    processing_time=processing_time
                )
    
    async def get_market_news(self, category: str = "general", limit: int = 20) -> NewsResponse:
        """Get general market news with improved error handling"""
        start_time = time.time()
        
        if not self.api_key:
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Finnhub",
                error="API key required for Finnhub"
            )
        
        # Retry logic for connection issues
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                await self._rate_limit_delay()
                
                params = {
                    'category': category,
                    'token': self.api_key
                }
                
                url = f"{self.base_url}/news"
                
                # Enhanced request with better session handling
                headers = {
                    'User-Agent': 'ICE-Investment-Engine/1.0',
                    'Accept': 'application/json',
                    'Connection': 'close'
                }
                
                with requests.Session() as session:
                    session.headers.update(headers)
                    response = session.get(
                        url, 
                        params=params, 
                        timeout=20,
                        verify=True
                    )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    articles = []
                    for item in data[:limit]:
                        article = NewsArticle(
                            title=item.get('headline', ''),
                            summary=item.get('summary', ''),
                            url=item.get('url', ''),
                            published=datetime.fromtimestamp(item.get('datetime', 0)),
                            source=item.get('source', 'Finnhub'),
                            category=category,
                            image_url=item.get('image', ''),
                            sentiment=None,
                            sentiment_score=None
                        )
                        articles.append(article)
                    
                    return NewsResponse(
                        success=True,
                        articles=articles,
                        source_name="Finnhub",
                        total_articles=len(articles),
                        processing_time=processing_time
                    )
                else:
                    error_msg = f"HTTP {response.status_code}"
                    if response.status_code == 429 and attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * 2)
                        continue
                    
                    return NewsResponse(
                        success=False,
                        articles=[],
                        source_name="Finnhub",
                        error=error_msg,
                        processing_time=processing_time
                    )
                    
            except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Finnhub market news connection error (attempt {attempt + 1}): {e}. Retrying...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                else:
                    processing_time = time.time() - start_time
                    return NewsResponse(
                        success=False,
                        articles=[],
                        source_name="Finnhub",
                        error=f"Connection failed after {max_retries} attempts: {str(e)}",
                        processing_time=processing_time
                    )
                    
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                else:
                    processing_time = time.time() - start_time
                    return NewsResponse(
                        success=False,
                        articles=[],
                        source_name="Finnhub",
                        error=f"Timeout after {max_retries} attempts",
                        processing_time=processing_time
                    )
                    
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"Finnhub market news error: {e}")
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Finnhub",
                    error=str(e),
                    processing_time=processing_time
                )


class MarketauxNewsConnector:
    """Marketaux news API connector"""
    
    def __init__(self, api_token: Optional[str] = None):
        """Initialize Marketaux connector"""
        self.api_token = api_token
        self.base_url = "https://api.marketaux.com/v1"
        
        # Rate limiting for free tier (be conservative)
        self.rate_limit = 2.0  # 2 seconds between requests
        self.last_request_time = 0
    
    async def _rate_limit_delay(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            delay = self.rate_limit - time_since_last
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def get_company_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        """Get company-specific news"""
        start_time = time.time()
        
        try:
            await self._rate_limit_delay()
            
            params = {
                'symbols': symbol,
                'filter_entities': 'true',
                'limit': limit,
                'sort': 'published_desc'
            }
            
            if self.api_token:
                params['api_token'] = self.api_token
            
            url = f"{self.base_url}/news/all"
            response = requests.get(url, params=params, timeout=15)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                articles = []
                for item in data.get('data', []):
                    # Parse sentiment if available
                    sentiment_score = None
                    sentiment = None
                    
                    entities = item.get('entities', [])
                    for entity in entities:
                        if entity.get('symbol') == symbol:
                            sentiment_score = entity.get('sentiment_score')
                            if sentiment_score is not None:
                                sentiment = "positive" if sentiment_score > 0 else "negative" if sentiment_score < 0 else "neutral"
                    
                    article = NewsArticle(
                        title=item.get('title', ''),
                        summary=item.get('description', ''),
                        url=item.get('url', ''),
                        published=datetime.fromisoformat(item.get('published_at', '').replace('Z', '+00:00')),
                        source=item.get('source', 'Marketaux'),
                        symbol=symbol,
                        sentiment=sentiment,
                        sentiment_score=sentiment_score,
                        image_url=item.get('image_url', ''),
                        author=None
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="Marketaux",
                    symbol=symbol,
                    total_articles=len(articles),
                    processing_time=processing_time
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Marketaux",
                    symbol=symbol,
                    error=f"HTTP {response.status_code}",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Marketaux API error for {symbol}: {e}")
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Marketaux",
                symbol=symbol,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_market_news(self, limit: int = 20) -> NewsResponse:
        """Get general market news"""
        start_time = time.time()
        
        try:
            await self._rate_limit_delay()
            
            params = {
                'countries': 'us',
                'filter_entities': 'true',
                'limit': limit,
                'published_after': (datetime.now() - timedelta(days=1)).isoformat(),
                'sort': 'published_desc'
            }
            
            if self.api_token:
                params['api_token'] = self.api_token
            
            url = f"{self.base_url}/news/all"
            response = requests.get(url, params=params, timeout=15)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                articles = []
                for item in data.get('data', []):
                    article = NewsArticle(
                        title=item.get('title', ''),
                        summary=item.get('description', ''),
                        url=item.get('url', ''),
                        published=datetime.fromisoformat(item.get('published_at', '').replace('Z', '+00:00')),
                        source=item.get('source', 'Marketaux'),
                        image_url=item.get('image_url', ''),
                        sentiment=None,
                        sentiment_score=None
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="Marketaux",
                    total_articles=len(articles),
                    processing_time=processing_time
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Marketaux",
                    error=f"HTTP {response.status_code}",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Marketaux",
                error=str(e),
                processing_time=processing_time
            )


class YahooRSSNewsConnector:
    """Yahoo Finance RSS news connector (no API key required)"""
    
    def __init__(self):
        """Initialize Yahoo RSS connector"""
        self.base_url = "https://feeds.finance.yahoo.com/rss/2.0"
        
        # Rate limiting to be respectful
        self.rate_limit = 1.0  # 1 second between requests
        self.last_request_time = 0
    
    async def _rate_limit_delay(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            delay = self.rate_limit - time_since_last
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def get_company_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        """Get company-specific news from Yahoo RSS"""
        start_time = time.time()
        
        try:
            await self._rate_limit_delay()
            
            # Yahoo RSS URL for specific symbol
            url = f"{self.base_url}/headline?s={symbol}&region=US&lang=en-US"
            
            # Parse RSS feed
            feed = feedparser.parse(url)
            
            processing_time = time.time() - start_time
            
            if feed.bozo == 0 or len(feed.entries) > 0:  # Valid feed or has entries
                articles = []
                
                for entry in feed.entries[:limit]:
                    # Parse published date
                    published = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])
                    
                    # Clean summary (remove HTML tags)
                    summary = entry.get('summary', '')
                    if summary:
                        summary = re.sub(r'<[^>]+>', '', summary).strip()
                    
                    article = NewsArticle(
                        title=entry.get('title', ''),
                        summary=summary,
                        url=entry.get('link', ''),
                        published=published,
                        source='Yahoo Finance RSS',
                        symbol=symbol,
                        sentiment=None,
                        sentiment_score=None
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="Yahoo RSS",
                    symbol=symbol,
                    total_articles=len(articles),
                    processing_time=processing_time
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Yahoo RSS",
                    symbol=symbol,
                    error="Invalid RSS feed or no entries",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Yahoo RSS error for {symbol}: {e}")
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Yahoo RSS",
                symbol=symbol,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_market_news(self, limit: int = 20) -> NewsResponse:
        """Get general market news from Yahoo RSS"""
        start_time = time.time()
        
        try:
            await self._rate_limit_delay()
            
            # Yahoo RSS URL for general market news
            url = f"{self.base_url}/topstories?region=US&lang=en-US"
            
            # Parse RSS feed
            feed = feedparser.parse(url)
            
            processing_time = time.time() - start_time
            
            if feed.bozo == 0 or len(feed.entries) > 0:
                articles = []
                
                for entry in feed.entries[:limit]:
                    # Parse published date
                    published = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])
                    
                    # Clean summary
                    summary = entry.get('summary', '')
                    if summary:
                        summary = re.sub(r'<[^>]+>', '', summary).strip()
                    
                    article = NewsArticle(
                        title=entry.get('title', ''),
                        summary=summary,
                        url=entry.get('link', ''),
                        published=published,
                        source='Yahoo Finance RSS',
                        sentiment=None,
                        sentiment_score=None
                    )
                    articles.append(article)
                
                return NewsResponse(
                    success=True,
                    articles=articles,
                    source_name="Yahoo RSS",
                    total_articles=len(articles),
                    processing_time=processing_time
                )
            else:
                return NewsResponse(
                    success=False,
                    articles=[],
                    source_name="Yahoo RSS",
                    error="Invalid RSS feed or no entries",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return NewsResponse(
                success=False,
                articles=[],
                source_name="Yahoo RSS",
                error=str(e),
                processing_time=processing_time
            )


# Import new connectors
try:
    from .openbb_connector import openbb_connector
    from .benzinga_connector import benzinga_connector
    from .polygon_connector import polygon_connector
    from .newsapi_connector import newsapi_connector
except ImportError:
    # Fallback for standalone usage
    try:
        from openbb_connector import openbb_connector
        from benzinga_connector import benzinga_connector
        from polygon_connector import polygon_connector
        from newsapi_connector import newsapi_connector
    except ImportError:
        openbb_connector = None
        benzinga_connector = None
        polygon_connector = None
        newsapi_connector = None

# Global instances
import os  # Add back the os import for getenv calls

finnhub_connector = FinnhubNewsConnector(api_key=os.getenv("FINNHUB_API_KEY"))
marketaux_connector = MarketauxNewsConnector(api_token=os.getenv("MARKETAUX_API_KEY"))
yahoo_rss_connector = YahooRSSNewsConnector()


async def get_aggregated_news(symbol: str, limit_per_source: int = 5) -> Dict[str, NewsResponse]:
    """Get news from all sources for a symbol"""
    results = {}
    
    # Prepare all available sources
    tasks = [
        ("Finnhub", finnhub_connector.get_company_news(symbol, days_back=7)),
        ("Marketaux", marketaux_connector.get_company_news(symbol, limit_per_source)),
        ("Yahoo RSS", yahoo_rss_connector.get_company_news(symbol, limit_per_source))
    ]
    
    # Add new sources if available
    if openbb_connector:
        tasks.append(("OpenBB", openbb_connector.get_company_news(symbol, limit_per_source)))
    
    if benzinga_connector:
        tasks.append(("Benzinga", benzinga_connector.get_company_news(symbol, limit_per_source)))
    
    if polygon_connector:
        tasks.append(("Polygon.io", polygon_connector.get_company_news(symbol, limit_per_source)))
    
    if newsapi_connector:
        tasks.append(("NewsAPI.org", newsapi_connector.get_company_news(symbol, limit_per_source)))
    
    # Execute all requests concurrently
    for name, task in tasks:
        try:
            result = await task
            results[name] = result
        except Exception as e:
            logger.error(f"Error fetching news from {name}: {e}")
            results[name] = NewsResponse(
                success=False,
                articles=[],
                source_name=name,
                symbol=symbol,
                error=str(e)
            )
    
    return results


async def test_all_news_sources(symbol: str = "AAPL") -> Dict[str, bool]:
    """Test all news sources and return status"""
    results = await get_aggregated_news(symbol, 3)
    status_results = {name: result.success for name, result in results.items()}
    
    # Log which sources are available
    available_sources = []
    if finnhub_connector.api_key:
        available_sources.append("Finnhub")
    if marketaux_connector.api_token:
        available_sources.append("Marketaux")
    available_sources.append("Yahoo RSS")  # Always available
    if openbb_connector and openbb_connector.api_key:
        available_sources.append("OpenBB")
    if benzinga_connector and benzinga_connector.api_key:
        available_sources.append("Benzinga")
    if polygon_connector and polygon_connector.api_key:
        available_sources.append("Polygon.io")
    if newsapi_connector and newsapi_connector.api_key:
        available_sources.append("NewsAPI.org")
    
    logger.info(f"Available news sources: {', '.join(available_sources)}")
    return status_results