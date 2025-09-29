# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/benzinga_client.py
# Benzinga API client implementation for premium financial news and data
# Provides integration with Benzinga's professional-grade financial news and analytics
# RELEVANT FILES: news_apis.py, polygon_client.py, alpha_vantage_client.py, newsapi_org_client.py

"""
Benzinga API Client

Benzinga is a premium financial news and data provider offering:
- Real-time financial news and market data
- Professional-grade analyst ratings and price targets
- Earnings data, calendars, and conference calls
- FDA calendar and regulatory events
- Insider trading data and SEC filings
- Options flow and unusual activity
- Cannabis industry coverage

API Features:
- News API: Real-time financial news with structured data
- Calendar API: Earnings, dividends, splits, FDA events
- Analyst API: Ratings, price targets, analyst insights
- Newsfeed API: Structured news data with metadata
- Real-time data feeds

Pricing Tiers:
- Basic: $25/month - 1000 API calls/month
- Professional: $250/month - 25K API calls/month  
- Enterprise: Custom pricing - Unlimited calls

API Key Format: bz.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

Benzinga-Polygon Partnership:
- Benzinga's news is now available through Polygon.io
- Enhanced news data with better structured metadata
- Combined market data and news in single API

Authentication:
- Requires API token
- Token passed as 'token' parameter in requests
- Register at: https://www.benzinga.com/apis/

Rate Limits:
- Varies by plan (typically 10 requests/minute for basic)
- Higher limits for paid plans
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

class BenzingaClient(NewsAPIClient):
    """Benzinga API client for premium financial news and data"""
    
    BASE_URL = "https://api.benzinga.com/api/v2"
    
    def __init__(self, api_token: str, rate_limiter: Optional[RateLimiter] = None,
                 cache: Optional[NewsCache] = None):
        # Benzinga specific rate limiter (conservative for basic plan)
        if rate_limiter is None:
            rate_limiter = RateLimiter(requests_per_minute=10)
            
        super().__init__(api_token, NewsAPIProvider.BENZINGA, rate_limiter, cache)
        
        # Set Benzinga quota (1000 requests per month for basic plan)
        self.quota = APIQuota(provider=NewsAPIProvider.BENZINGA, requests_per_day=33)  # ~1000/month
        
        # Store token for Benzinga
        self.api_token = api_token
    
    def _build_url(self, endpoint: str, **params) -> str:
        """Build Benzinga API URL with parameters"""
        base_params = {'token': self.api_token}
        base_params.update(params)
        
        url = f"{self.BASE_URL}/{endpoint}"
        if base_params:
            url += f"?{urlencode(base_params)}"
        
        return url
    
    def _parse_sentiment_score(self, sentiment_str: Optional[str]) -> Optional[float]:
        """Parse Benzinga sentiment to numeric score"""
        if not sentiment_str:
            return None
            
        sentiment_mapping = {
            'positive': 0.7,
            'negative': -0.7,
            'neutral': 0.0,
            'bullish': 0.8,
            'bearish': -0.8,
            'optimistic': 0.6,
            'pessimistic': -0.6
        }
        
        return sentiment_mapping.get(sentiment_str.lower())
    
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
        """Parse Benzinga news article data into standardized format"""
        try:
            # Extract basic article info
            title = article_data.get('title', '')
            content = article_data.get('body', '') or article_data.get('content', '')
            url = article_data.get('url', '')
            
            # Source information
            source = 'Benzinga'
            if 'author' in article_data:
                source = f"Benzinga ({article_data['author']})"
            
            # Parse timestamp
            published_at = datetime.now()
            date_str = article_data.get('created', '') or article_data.get('published', '')
            
            if date_str:
                try:
                    # Benzinga format: 2024-01-15T10:30:00Z
                    published_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    published_at = published_at.replace(tzinfo=None)
                except ValueError:
                    logger.warning(f"Could not parse Benzinga date: {date_str}")
            
            # Extract sentiment data (Benzinga may provide sentiment)
            sentiment_score = None
            sentiment_label = None
            
            if 'sentiment' in article_data:
                sentiment_score = self._parse_sentiment_score(article_data['sentiment'])
                if sentiment_score is not None:
                    sentiment_label = self._parse_sentiment_enum(sentiment_score)
            
            # Extract tickers/symbols
            symbols = []
            if 'tickers' in article_data:
                if isinstance(article_data['tickers'], list):
                    symbols = article_data['tickers']
                elif isinstance(article_data['tickers'], str):
                    symbols = [article_data['tickers']]
            
            # Also check 'symbols' field
            if 'symbols' in article_data:
                additional_symbols = article_data['symbols']
                if isinstance(additional_symbols, list):
                    symbols.extend(additional_symbols)
                elif isinstance(additional_symbols, str):
                    symbols.append(additional_symbols)
            
            # Remove duplicates and clean symbols
            symbols = list(set(symbol.upper() for symbol in symbols if symbol))
            
            # Use provided ticker or first symbol found
            article_ticker = ticker or (symbols[0] if symbols else None)
            
            # Extract categories/tags
            categories = article_data.get('categories', [])
            if isinstance(categories, str):
                categories = [categories]
            
            # Extract keywords from categories and content
            keywords = list(categories) if categories else []
            
            # Extract image URL
            image_url = article_data.get('image', '') or article_data.get('images', [{}])[0].get('url', '') if article_data.get('images') else ''
            
            # Build metadata with Benzinga-specific fields
            metadata = {
                'benzinga_id': article_data.get('id', ''),
                'author': article_data.get('author', ''),
                'teaser': article_data.get('teaser', ''),
                'image_url': image_url,
                'categories': categories,
                'symbols': symbols,
                'revision': article_data.get('revision', 0),
                'channels': article_data.get('channels', []),
                'tags': article_data.get('tags', []),
                'stocks': article_data.get('stocks', [])
            }
            
            return NewsArticle(
                title=title,
                content=content,
                url=url,
                source=source,
                published_at=published_at,
                provider=NewsAPIProvider.BENZINGA,
                ticker=article_ticker,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=0.9,  # High confidence for professional source
                keywords=keywords,
                entities=symbols,
                category=categories[0] if categories else None,
                metadata=metadata
            )
            
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse Benzinga article: {e}")
            return None
    
    def get_news(self, ticker: Optional[str] = None, limit: int = 20,
                 hours_back: int = 24) -> List[NewsArticle]:
        """Get financial news from Benzinga"""
        params = {
            'pageSize': min(limit, 100),
            'displayOutput': 'full'
        }
        
        # Add ticker-specific filtering
        if ticker:
            params['tickers'] = ticker
        
        # Add time range filtering
        date_from = datetime.now() - timedelta(hours=hours_back)
        params['dateFrom'] = date_from.strftime('%Y-%m-%d')
        params['dateTo'] = datetime.now().strftime('%Y-%m-%d')
        
        url = self._build_url('news', **params)
        
        response_data = self._make_request(url, {}, endpoint='news')
        if not response_data:
            return []
        
        articles = []
        
        # Benzinga response can be a list or have a 'data' field
        news_data = response_data
        if isinstance(response_data, dict):
            news_data = response_data.get('data', response_data.get('news', []))
        
        for article_data in news_data[:limit]:
            article = self._parse_news_article(article_data, ticker)
            if article:
                articles.append(article)
        
        logger.info(f"Retrieved {len(articles)} articles from Benzinga" + 
                   (f" for {ticker}" if ticker else ""))
        return articles
    
    def get_sentiment(self, ticker: str, hours_back: int = 24) -> Optional[float]:
        """Get aggregated sentiment score for a ticker from Benzinga"""
        articles = self.get_news(ticker=ticker, limit=50, hours_back=hours_back)
        
        if not articles:
            return None
        
        # Calculate average sentiment
        sentiments = [article.sentiment_score for article in articles if article.sentiment_score is not None]
        
        if not sentiments:
            return None
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        logger.info(f"Benzinga sentiment for {ticker}: {avg_sentiment:.3f} (from {len(sentiments)} articles)")
        
        return avg_sentiment
    
    def search_news(self, query: str, limit: int = 20) -> List[NewsArticle]:
        """Search news by keywords in Benzinga"""
        params = {
            'q': query,
            'pageSize': min(limit, 100),
            'displayOutput': 'full'
        }
        
        url = self._build_url('news', **params)
        
        response_data = self._make_request(url, {}, endpoint='search')
        if not response_data:
            return []
        
        articles = []
        news_data = response_data
        if isinstance(response_data, dict):
            news_data = response_data.get('data', response_data.get('news', []))
        
        for article_data in news_data[:limit]:
            article = self._parse_news_article(article_data)
            if article:
                articles.append(article)
        
        logger.info(f"Found {len(articles)} articles matching '{query}' in Benzinga")
        return articles
    
    def get_analyst_ratings(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get analyst ratings for a ticker"""
        params = {
            'tickers': ticker,
            'pageSize': min(limit, 100)
        }
        
        url = self._build_url('analyst-ratings', **params)
        
        response_data = self._make_request(url, {}, endpoint='analyst_ratings')
        if not response_data:
            return []
        
        ratings = response_data if isinstance(response_data, list) else response_data.get('analyst-ratings', [])
        logger.info(f"Retrieved {len(ratings)} analyst ratings for {ticker} from Benzinga")
        
        return ratings
    
    def get_earnings_calendar(self, date_from: Optional[str] = None, date_to: Optional[str] = None,
                             ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get earnings calendar data"""
        params = {}
        
        if date_from:
            params['dateFrom'] = date_from
        if date_to:
            params['dateTo'] = date_to
        if ticker:
            params['tickers'] = ticker
        
        url = self._build_url('calendar/earnings', **params)
        
        response_data = self._make_request(url, {}, endpoint='earnings_calendar')
        if not response_data:
            return []
        
        earnings = response_data if isinstance(response_data, list) else response_data.get('earnings', [])
        logger.info(f"Retrieved {len(earnings)} earnings events from Benzinga")
        
        return earnings
    
    def get_dividends_calendar(self, date_from: Optional[str] = None, date_to: Optional[str] = None,
                              ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get dividends calendar data"""
        params = {}
        
        if date_from:
            params['dateFrom'] = date_from
        if date_to:
            params['dateTo'] = date_to
        if ticker:
            params['tickers'] = ticker
        
        url = self._build_url('calendar/dividends', **params)
        
        response_data = self._make_request(url, {}, endpoint='dividends_calendar')
        if not response_data:
            return []
        
        dividends = response_data if isinstance(response_data, list) else response_data.get('dividends', [])
        logger.info(f"Retrieved {len(dividends)} dividend events from Benzinga")
        
        return dividends
    
    def get_price_targets(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get price targets for a ticker"""
        params = {
            'tickers': ticker,
            'pageSize': min(limit, 100)
        }
        
        url = self._build_url('analyst-ratings', **params)  # Same endpoint as ratings
        
        response_data = self._make_request(url, {}, endpoint='price_targets')
        if not response_data:
            return []
        
        # Filter for entries with price targets
        ratings = response_data if isinstance(response_data, list) else response_data.get('analyst-ratings', [])
        price_targets = [rating for rating in ratings if rating.get('pt_current') or rating.get('pt_prior')]
        
        logger.info(f"Retrieved {len(price_targets)} price targets for {ticker} from Benzinga")
        return price_targets
    
    def get_movers(self, session: str = 'regular') -> List[Dict[str, Any]]:
        """Get market movers data"""
        params = {
            'session': session  # 'regular' or 'pre' or 'after'
        }
        
        url = self._build_url('movers', **params)
        
        response_data = self._make_request(url, {}, endpoint='movers')
        if not response_data:
            return []
        
        movers = response_data if isinstance(response_data, list) else response_data.get('movers', [])
        logger.info(f"Retrieved {len(movers)} market movers from Benzinga")
        
        return movers