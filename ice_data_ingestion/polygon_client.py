# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/polygon_client.py
# Polygon.io API client implementation for real-time market data and news
# Provides integration with Polygon's comprehensive financial market data and news services
# RELEVANT FILES: news_apis.py, benzinga_client.py, alpha_vantage_client.py, newsapi_org_client.py

"""
Polygon.io API Client

Polygon.io is a comprehensive financial market data provider offering:
- Real-time and historical stock market data
- Financial news with Benzinga partnership
- Options, forex, and crypto data
- Company fundamentals and financial statements
- Market holidays and status information
- WebSocket feeds for real-time data

API Features:
- REST API for historical and snapshot data
- WebSocket API for real-time streaming
- News API with Benzinga integration
- Reference data (tickers, exchanges, market status)
- Aggregates (OHLC) data with various timeframes
- Technical indicators

Benzinga Partnership:
- Polygon now includes Benzinga's structured news data
- Enhanced news metadata with analyst ratings
- Corporate actions and earnings data
- Real-time news feed with sentiment analysis

Free Tier:
- 5 API calls per minute
- 2 years of historical data
- Delayed data (15+ minutes)
- Basic endpoints only

Paid Plans:
- Starter: $99/month - 100 requests/minute
- Developer: $199/month - 1000 requests/minute
- Advanced: $399/month - Unlimited requests

Authentication:
- Requires API key
- API key passed as 'apikey' query parameter
- Register at: https://polygon.io/

Rate Limits:
- Free: 5 requests per minute
- Paid plans: Much higher limits
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode

from .news_apis import (
    NewsAPIClient, NewsAPIProvider, NewsArticle, SentimentScore,
    APIQuota, RateLimiter, NewsCache
)

logger = logging.getLogger(__name__)

class PolygonClient(NewsAPIClient):
    """Polygon.io API client for market data and news"""
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: str, rate_limiter: Optional[RateLimiter] = None,
                 cache: Optional[NewsCache] = None):
        # Polygon.io specific rate limiter (5 req/min for free tier)
        if rate_limiter is None:
            rate_limiter = RateLimiter(requests_per_minute=5)
            
        super().__init__(api_key, NewsAPIProvider.POLYGON, rate_limiter, cache)
        
        # Set Polygon quota (5 requests per minute = ~7200 per day theoretical max)
        # But practically limited by business hours usage
        self.quota = APIQuota(provider=NewsAPIProvider.POLYGON, requests_per_day=1000)  # Conservative estimate
    
    def _build_url(self, endpoint: str, version: str = "v2", **params) -> str:
        """Build Polygon.io API URL with parameters"""
        base_params = {'apikey': self.api_key}
        base_params.update(params)
        
        url = f"{self.BASE_URL}/{version}/{endpoint}"
        if base_params:
            url += f"?{urlencode(base_params)}"
        
        return url
    
    def _parse_sentiment_from_keywords(self, keywords: List[str]) -> Tuple[Optional[float], Optional[SentimentScore]]:
        """Estimate sentiment from article keywords"""
        if not keywords:
            return None, None
        
        positive_keywords = [
            'bullish', 'positive', 'growth', 'gain', 'up', 'surge', 'rally',
            'beat', 'outperform', 'strong', 'upgrade', 'buy', 'optimistic'
        ]
        
        negative_keywords = [
            'bearish', 'negative', 'decline', 'loss', 'down', 'drop', 'fall',
            'miss', 'underperform', 'weak', 'downgrade', 'sell', 'pessimistic'
        ]
        
        keywords_lower = [k.lower() for k in keywords]
        positive_count = sum(1 for k in keywords_lower if any(pos in k for pos in positive_keywords))
        negative_count = sum(1 for k in keywords_lower if any(neg in k for neg in negative_keywords))
        
        if positive_count > negative_count:
            sentiment_score = min(0.7, 0.2 + (positive_count * 0.1))
            sentiment_label = SentimentScore.POSITIVE
        elif negative_count > positive_count:
            sentiment_score = max(-0.7, -0.2 - (negative_count * 0.1))
            sentiment_label = SentimentScore.NEGATIVE
        else:
            sentiment_score = 0.0
            sentiment_label = SentimentScore.NEUTRAL
        
        return sentiment_score, sentiment_label
    
    def _parse_news_article(self, article_data: Dict[str, Any], ticker: Optional[str] = None) -> Optional[NewsArticle]:
        """Parse Polygon.io news article data into standardized format"""
        try:
            # Extract basic article info
            title = article_data.get('title', '')
            description = article_data.get('description', '') or article_data.get('summary', '')
            content = description  # Polygon typically provides descriptions/summaries
            url = article_data.get('article_url', '') or article_data.get('url', '')
            
            # Source information
            publisher = article_data.get('publisher', {})
            source = publisher.get('name', 'Unknown') if publisher else 'Polygon.io'
            
            # Parse timestamp
            published_at = datetime.now()
            timestamp = article_data.get('published_utc', '')
            
            if timestamp:
                try:
                    # Polygon format: 2024-01-15T10:30:00.000Z
                    published_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    published_at = published_at.replace(tzinfo=None)
                except ValueError:
                    logger.warning(f"Could not parse Polygon date: {timestamp}")
            
            # Extract tickers from the article
            tickers = article_data.get('tickers', [])
            if isinstance(tickers, str):
                tickers = [tickers]
            
            # Clean ticker symbols
            clean_tickers = []
            for t in tickers:
                if isinstance(t, dict):
                    clean_tickers.append(t.get('ticker', ''))
                else:
                    clean_tickers.append(str(t))
            
            tickers = [t.upper() for t in clean_tickers if t]
            
            # Use provided ticker or first found ticker
            article_ticker = ticker or (tickers[0] if tickers else None)
            
            # Extract keywords for sentiment analysis
            keywords = article_data.get('keywords', [])
            if isinstance(keywords, str):
                keywords = keywords.split(',')
            
            # Estimate sentiment from keywords and content
            sentiment_score, sentiment_label = self._parse_sentiment_from_keywords(keywords)
            
            # Extract image URL
            image_url = article_data.get('image_url', '')
            
            # Extract author information
            author = article_data.get('author', '')
            if not author and publisher:
                author = publisher.get('homepage_url', '')
            
            # Build metadata with Polygon-specific fields
            metadata = {
                'polygon_id': article_data.get('id', ''),
                'amp_url': article_data.get('amp_url', ''),
                'image_url': image_url,
                'author': author,
                'publisher': publisher,
                'tickers': tickers,
                'keywords': keywords,
                'insights': article_data.get('insights', [])
            }
            
            return NewsArticle(
                title=title,
                content=content,
                url=url,
                source=source,
                published_at=published_at,
                provider=NewsAPIProvider.POLYGON,
                ticker=article_ticker,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=0.6,  # Medium confidence for keyword-based sentiment
                keywords=keywords,
                entities=tickers,
                category='financial',
                metadata=metadata
            )
            
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse Polygon article: {e}")
            return None
    
    def get_news(self, ticker: Optional[str] = None, limit: int = 20,
                 hours_back: int = 24) -> List[NewsArticle]:
        """Get financial news from Polygon.io"""
        params = {
            'limit': min(limit, 1000)  # Polygon max limit
        }
        
        # Add ticker filtering if provided
        if ticker:
            params['ticker'] = ticker
        
        # Add date filtering
        published_gte = datetime.now() - timedelta(hours=hours_back)
        params['published.gte'] = published_gte.strftime('%Y-%m-%d')
        
        # Sort by publication date (newest first)
        params['order'] = 'desc'
        
        url = self._build_url('reference/news', **params)
        
        response_data = self._make_request(url, {}, endpoint='news')
        if not response_data:
            return []
        
        articles = []
        
        # Polygon response structure
        results = response_data.get('results', [])
        
        for article_data in results[:limit]:
            article = self._parse_news_article(article_data, ticker)
            if article:
                articles.append(article)
        
        logger.info(f"Retrieved {len(articles)} articles from Polygon.io" + 
                   (f" for {ticker}" if ticker else ""))
        return articles
    
    def get_sentiment(self, ticker: str, hours_back: int = 24) -> Optional[float]:
        """Get aggregated sentiment score for a ticker from Polygon.io"""
        articles = self.get_news(ticker=ticker, limit=50, hours_back=hours_back)
        
        if not articles:
            return None
        
        # Calculate average sentiment
        sentiments = [article.sentiment_score for article in articles if article.sentiment_score is not None]
        
        if not sentiments:
            return None
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        logger.info(f"Polygon.io sentiment for {ticker}: {avg_sentiment:.3f} (from {len(sentiments)} articles)")
        
        return avg_sentiment
    
    def search_news(self, query: str, limit: int = 20) -> List[NewsArticle]:
        """Search news by keywords in Polygon.io"""
        # Polygon doesn't have direct text search, but we can filter by keywords
        params = {
            'limit': min(limit * 2, 1000),  # Get more to filter
            'order': 'desc'
        }
        
        # Add recent date filter for relevance
        published_gte = datetime.now() - timedelta(days=7)
        params['published.gte'] = published_gte.strftime('%Y-%m-%d')
        
        url = self._build_url('reference/news', **params)
        
        response_data = self._make_request(url, {}, endpoint='search')
        if not response_data:
            return []
        
        articles = []
        results = response_data.get('results', [])
        query_lower = query.lower()
        
        for article_data in results:
            # Filter by title and description content
            title = article_data.get('title', '').lower()
            description = article_data.get('description', '').lower()
            keywords = article_data.get('keywords', [])
            keywords_str = ' '.join(keywords).lower() if keywords else ''
            
            if (query_lower in title or 
                query_lower in description or 
                query_lower in keywords_str):
                
                article = self._parse_news_article(article_data)
                if article:
                    articles.append(article)
                    if len(articles) >= limit:
                        break
        
        logger.info(f"Found {len(articles)} articles matching '{query}' in Polygon.io")
        return articles
    
    def get_market_status(self) -> Optional[Dict[str, Any]]:
        """Get current market status from Polygon.io"""
        url = self._build_url('reference/market-status', version='v1')
        
        response_data = self._make_request(url, {}, endpoint='market_status')
        return response_data
    
    def get_stock_splits(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get stock splits data for a ticker"""
        params = {
            'limit': min(limit, 1000)
        }
        
        url = self._build_url(f'reference/splits/{ticker}', version='v3', **params)
        
        response_data = self._make_request(url, {}, endpoint='stock_splits')
        if not response_data:
            return []
        
        splits = response_data.get('results', [])
        logger.info(f"Retrieved {len(splits)} stock splits for {ticker} from Polygon.io")
        
        return splits
    
    def get_dividends(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get dividend data for a ticker"""
        params = {
            'limit': min(limit, 1000)
        }
        
        url = self._build_url(f'reference/dividends/{ticker}', version='v3', **params)
        
        response_data = self._make_request(url, {}, endpoint='dividends')
        if not response_data:
            return []
        
        dividends = response_data.get('results', [])
        logger.info(f"Retrieved {len(dividends)} dividends for {ticker} from Polygon.io")
        
        return dividends
    
    def get_ticker_details(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a ticker"""
        url = self._build_url(f'reference/tickers/{ticker}', version='v3')
        
        response_data = self._make_request(url, {}, endpoint='ticker_details')
        if not response_data:
            return None
        
        return response_data.get('results')
    
    def get_market_holidays(self) -> List[Dict[str, Any]]:
        """Get market holidays from Polygon.io"""
        url = self._build_url('reference/market-holidays', version='v1')
        
        response_data = self._make_request(url, {}, endpoint='market_holidays')
        if not response_data:
            return []
        
        holidays = response_data if isinstance(response_data, list) else response_data.get('results', [])
        logger.info(f"Retrieved {len(holidays)} market holidays from Polygon.io")
        
        return holidays
    
    def get_exchanges(self) -> List[Dict[str, Any]]:
        """Get list of exchanges from Polygon.io"""
        url = self._build_url('reference/exchanges', version='v3')
        
        response_data = self._make_request(url, {}, endpoint='exchanges')
        if not response_data:
            return []
        
        exchanges = response_data.get('results', [])
        logger.info(f"Retrieved {len(exchanges)} exchanges from Polygon.io")
        
        return exchanges