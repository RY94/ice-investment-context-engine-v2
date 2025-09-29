# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/alpha_vantage_client.py
# Alpha Vantage API client implementation with news and sentiment data
# Provides integration with Alpha Vantage's financial news and sentiment analysis endpoints
# RELEVANT FILES: news_apis.py, __init__.py, fmp_client.py, marketaux_client.py

"""
Alpha Vantage News API Client

Alpha Vantage is the primary recommended provider with the most generous free tier:
- 500 requests per day (most generous among free providers)
- Real-time and historical stock data
- Market news with AI-powered sentiment scores
- Official NASDAQ vendor status

API Endpoints Used:
- NEWS_SENTIMENT: Financial news with sentiment analysis
- TIME_SERIES_DAILY: Stock price data for context
- MARKET_OVERVIEW: General market news

Sentiment Analysis:
- Alpha Vantage provides sentiment scores from -1 (bearish) to +1 (bullish)  
- Relevance scores from 0 to 1 for news-ticker relationship strength
- Both overall article sentiment and ticker-specific sentiment

Rate Limits:
- 500 requests per day on free tier
- 5 requests per minute
- Premium plans available for higher limits

Authentication:
- Requires API key (free registration)
- API key passed as 'apikey' parameter in requests
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode

from .news_apis import (
    NewsAPIClient, NewsAPIProvider, NewsArticle, SentimentScore,
    APIQuota, RateLimiter, NewsCache
)
from .smart_cache import SmartCache, AlphaVantageValidator, cached_api_call

logger = logging.getLogger(__name__)

class AlphaVantageClient(NewsAPIClient):
    """Alpha Vantage API client for financial news and sentiment"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: str, rate_limiter: Optional[RateLimiter] = None,
                 cache: Optional[NewsCache] = None, use_smart_cache: bool = True):
        # Alpha Vantage specific rate limiter (5 req/min, 500 req/day)
        if rate_limiter is None:
            rate_limiter = RateLimiter(requests_per_minute=5)

        super().__init__(api_key, NewsAPIProvider.ALPHA_VANTAGE, rate_limiter, cache)

        # Initialize smart cache for Alpha Vantage-specific endpoints
        self.use_smart_cache = use_smart_cache
        if use_smart_cache:
            self.smart_cache = SmartCache(
                cache_dir="user_data/alpha_vantage_cache",
                memory_size=50,
                default_ttl_hours=6,
                validator=AlphaVantageValidator()
            )
        
        # Set Alpha Vantage quota (500 requests per day)
        self.quota = APIQuota(provider=NewsAPIProvider.ALPHA_VANTAGE, requests_per_day=500)
        
        # News sentiment function parameters
        self.sentiment_functions = {
            'news': 'NEWS_SENTIMENT',
            'market_overview': 'MARKET_STATUS'  # For general market news
        }
    
    def _build_url(self, function: str, **params) -> str:
        """Build Alpha Vantage API URL with parameters"""
        base_params = {
            'function': function,
            'apikey': self.api_key
        }
        base_params.update(params)
        return f"{self.BASE_URL}?{urlencode(base_params)}"
    
    def _parse_sentiment_score(self, sentiment_str: str) -> Optional[float]:
        """Parse Alpha Vantage sentiment label to numeric score"""
        sentiment_mapping = {
            'Bearish': -0.8,
            'Somewhat-Bearish': -0.4,
            'Neutral': 0.0,
            'Somewhat-Bullish': 0.4, 
            'Bullish': 0.8
        }
        return sentiment_mapping.get(sentiment_str)
    
    def _parse_sentiment_enum(self, sentiment_score: float) -> SentimentScore:
        """Convert numeric sentiment to enum"""
        if sentiment_score <= -0.6:
            return SentimentScore.VERY_NEGATIVE
        elif sentiment_score <= -0.2:
            return SentimentScore.NEGATIVE
        elif sentiment_score >= 0.6:
            return SentimentScore.VERY_POSITIVE
        elif sentiment_score >= 0.2:
            return SentimentScore.POSITIVE
        else:
            return SentimentScore.NEUTRAL
    
    def _parse_news_article(self, article_data: Dict[str, Any], ticker: Optional[str] = None) -> Optional[NewsArticle]:
        """Parse Alpha Vantage news article data into standardized format"""
        try:
            # Extract basic article info
            title = article_data.get('title', '')
            content = article_data.get('summary', '')
            url = article_data.get('url', '')
            source = article_data.get('source', '')
            
            # Parse timestamp
            time_published = article_data.get('time_published', '')
            if time_published:
                # Alpha Vantage format: YYYYMMDDTHHMMSS
                published_at = datetime.strptime(time_published, '%Y%m%dT%H%M%S')
            else:
                published_at = datetime.now()
            
            # Extract sentiment data
            overall_sentiment_score = None
            overall_sentiment_label = None
            confidence = None
            
            # Overall sentiment
            if 'overall_sentiment_score' in article_data:
                overall_sentiment_score = float(article_data['overall_sentiment_score'])
                overall_sentiment_label = self._parse_sentiment_enum(overall_sentiment_score)
            
            # If specific ticker provided, look for ticker-specific sentiment
            ticker_sentiment_score = overall_sentiment_score
            ticker_relevance = None
            
            if ticker and 'ticker_sentiment' in article_data:
                for ticker_data in article_data['ticker_sentiment']:
                    if ticker_data.get('ticker') == ticker:
                        ticker_sentiment_score = float(ticker_data.get('sentiment_score', 0))
                        ticker_relevance = float(ticker_data.get('relevance_score', 0))
                        break
            
            # Extract keywords and entities
            keywords = []
            if 'topics' in article_data:
                for topic in article_data['topics']:
                    keywords.append(topic.get('topic', ''))
            
            # Build metadata
            metadata = {
                'source_domain': article_data.get('source_domain', ''),
                'authors': article_data.get('authors', []),
                'banner_image': article_data.get('banner_image', ''),
                'overall_sentiment_label': article_data.get('overall_sentiment_label', ''),
                'ticker_relevance': ticker_relevance,
                'topics': article_data.get('topics', [])
            }
            
            return NewsArticle(
                title=title,
                content=content,
                url=url,
                source=source,
                published_at=published_at,
                provider=NewsAPIProvider.ALPHA_VANTAGE,
                ticker=ticker,
                sentiment_score=ticker_sentiment_score,
                sentiment_label=overall_sentiment_label,
                confidence=ticker_relevance,  # Use relevance as confidence for ticker-specific news
                keywords=keywords,
                entities=[],  # Alpha Vantage doesn't provide entity extraction
                category=None,
                metadata=metadata
            )
            
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse Alpha Vantage article: {e}")
            return None
    
    def get_news(self, ticker: Optional[str] = None, limit: int = 20, 
                 hours_back: int = 24) -> List[NewsArticle]:
        """Get financial news from Alpha Vantage"""
        params = {
            'topics': 'financial_markets,earnings,ipo,mergers_and_acquisitions',
            'sort': 'LATEST',
            'limit': min(limit, 1000)  # Alpha Vantage max limit
        }
        
        # Add ticker-specific filtering if provided
        if ticker:
            params['tickers'] = ticker
        
        # Add time range filtering
        if hours_back < 24 * 30:  # Less than 30 days
            time_from = datetime.now() - timedelta(hours=hours_back)
            params['time_from'] = time_from.strftime('%Y%m%dT%H%M')
        
        url = self._build_url('NEWS_SENTIMENT', **params)
        
        response_data = self._make_request(url, {}, endpoint='news_sentiment')
        if not response_data:
            return []
        
        articles = []
        feed_data = response_data.get('feed', [])
        
        for article_data in feed_data[:limit]:
            article = self._parse_news_article(article_data, ticker)
            if article:
                articles.append(article)
        
        logger.info(f"Retrieved {len(articles)} articles from Alpha Vantage" + 
                   (f" for {ticker}" if ticker else ""))
        return articles
    
    def get_sentiment(self, ticker: str, hours_back: int = 24) -> Optional[float]:
        """Get aggregated sentiment score for a ticker from Alpha Vantage"""
        articles = self.get_news(ticker=ticker, limit=50, hours_back=hours_back)
        
        if not articles:
            return None
        
        # Calculate weighted average sentiment
        total_sentiment = 0
        total_weight = 0
        
        for article in articles:
            if article.sentiment_score is not None:
                # Weight by confidence (relevance) if available, otherwise equal weight
                weight = article.confidence if article.confidence else 1.0
                total_sentiment += article.sentiment_score * weight
                total_weight += weight
        
        if total_weight == 0:
            return None
        
        avg_sentiment = total_sentiment / total_weight
        logger.info(f"Alpha Vantage sentiment for {ticker}: {avg_sentiment:.3f} (from {len(articles)} articles)")
        
        return avg_sentiment
    
    def search_news(self, query: str, limit: int = 20) -> List[NewsArticle]:
        """Search news by keywords in Alpha Vantage"""
        # Alpha Vantage doesn't have a direct search endpoint
        # We'll get general market news and filter by keywords in the content
        params = {
            'topics': 'financial_markets,earnings,technology,economy',
            'sort': 'LATEST',
            'limit': min(limit * 2, 1000)  # Get more to filter
        }
        
        url = self._build_url('NEWS_SENTIMENT', **params)
        
        response_data = self._make_request(url, {}, endpoint='news_search')
        if not response_data:
            return []
        
        articles = []
        feed_data = response_data.get('feed', [])
        query_lower = query.lower()
        
        for article_data in feed_data:
            # Simple keyword matching in title and summary
            title = article_data.get('title', '').lower()
            summary = article_data.get('summary', '').lower()
            
            if query_lower in title or query_lower in summary:
                article = self._parse_news_article(article_data)
                if article:
                    articles.append(article)
                    if len(articles) >= limit:
                        break
        
        logger.info(f"Found {len(articles)} articles matching '{query}' in Alpha Vantage")
        return articles
    
    def get_market_status(self) -> Optional[Dict[str, Any]]:
        """Get current market status from Alpha Vantage"""
        url = self._build_url('MARKET_STATUS')
        
        response_data = self._make_request(url, {}, endpoint='market_status')
        if not response_data:
            return None
        
        return response_data
    
    def get_earnings_calendar(self, symbol: Optional[str] = None, horizon: str = '3month') -> Optional[Dict[str, Any]]:
        """Get earnings calendar data"""
        params = {'horizon': horizon}
        if symbol:
            params['symbol'] = symbol
            
        url = self._build_url('EARNINGS_CALENDAR', **params)
        
        response_data = self._make_request(url, {}, endpoint='earnings_calendar')
        return response_data
    
    def get_company_overview(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company fundamental data overview with smart caching and validation

        Uses smart cache to prevent corrupted data from rate limiting issues.
        Falls back to regular cache if smart cache is disabled.
        """
        # Try smart cache first if enabled
        if self.use_smart_cache:
            # Check smart cache
            cache_params = {"symbol": symbol}
            quota_usage = self.quota.requests_used / self.quota.requests_per_day

            cached_data = self.smart_cache.get(
                provider="alpha_vantage",
                endpoint="company_overview",
                params=cache_params,
                requested_symbol=symbol
            )

            if cached_data:
                logger.debug(f"Smart cache hit for {symbol} overview")
                return cached_data

            # Make API request
            url = self._build_url('OVERVIEW', symbol=symbol)
            response_data = self._make_request(url, {}, endpoint='company_overview')

            if response_data:
                # Validate and cache using smart cache
                success = self.smart_cache.set(
                    provider="alpha_vantage",
                    endpoint="company_overview",
                    params=cache_params,
                    data=response_data,
                    requested_symbol=symbol,
                    quota_usage=quota_usage
                )

                if not success:
                    logger.warning(f"Smart cache rejected corrupted data for {symbol}")
                    return None

            return response_data

        else:
            # Fall back to original implementation with basic validation
            url = self._build_url('OVERVIEW', symbol=symbol)
            response_data = self._make_request(url, {}, endpoint='company_overview')

            # Enhanced validation: Check if returned symbol matches requested symbol
            if response_data:
                returned_symbol = response_data.get('Symbol', '').upper()
                requested_symbol = symbol.upper()

                # If symbols don't match, it's likely cached/rate-limited data
                if returned_symbol and returned_symbol != requested_symbol:
                    logger.warning(f"Alpha Vantage returned {returned_symbol} data instead of {requested_symbol}. "
                                 f"This indicates rate limiting or cached response.")

                    # Return response with validation flag for caller to handle
                    response_data['_validation_warning'] = True
                    response_data['_requested_symbol'] = requested_symbol
                    response_data['_returned_symbol'] = returned_symbol

            return response_data

    def validate_symbol_response(self, response_data: Optional[Dict[str, Any]],
                                requested_symbol: str) -> bool:
        """
        Validate that Alpha Vantage response contains data for the correct symbol

        Returns:
            bool: True if validation passes or cannot be determined, False if clear mismatch
        """
        if not response_data:
            return False

        # Check for validation warning flag
        if response_data.get('_validation_warning', False):
            return False

        # Check symbol field
        returned_symbol = response_data.get('Symbol', '').upper()
        if returned_symbol and returned_symbol != requested_symbol.upper():
            return False

        return True