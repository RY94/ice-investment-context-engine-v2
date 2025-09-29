# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/marketaux_client.py
# MarketAux API client for global financial news with comprehensive sentiment analysis
# Provides integration with MarketAux's financial news aggregation and AI-powered sentiment
# RELEVANT FILES: news_apis.py, alpha_vantage_client.py, fmp_client.py, __init__.py

"""
MarketAux API Client

MarketAux is a financial news aggregation service that provides:
- Global financial news from multiple sources
- Built-in AI-powered sentiment analysis
- Coverage of stocks, crypto, commodities, and forex
- Real-time and historical news data
- Entity recognition and tagging

API Features:
- Comprehensive news aggregation from 100+ sources
- Multi-language support
- Advanced filtering by symbols, entities, topics
- Sentiment analysis with confidence scores
- High-quality data deduplication
- Real-time and historical data access

Free Tier:
- Generous free tier with API access
- Good for development and small-scale applications
- Rate limits apply but reasonable for most use cases

Sentiment Analysis:
- AI-powered sentiment classification: negative, neutral, positive
- Confidence scores for sentiment predictions
- Entity-level sentiment analysis
- Time-series sentiment tracking

Authentication:
- Requires API token (free registration)
- Token passed as 'api_token' parameter
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode

from .news_apis import (
    NewsAPIClient, NewsAPIProvider, NewsArticle, SentimentScore,
    APIQuota, RateLimiter, NewsCache
)

logger = logging.getLogger(__name__)

class MarketAuxClient(NewsAPIClient):
    """MarketAux API client for financial news with sentiment analysis"""
    
    BASE_URL = "https://api.marketaux.com/v1"
    
    def __init__(self, api_token: str, rate_limiter: Optional[RateLimiter] = None,
                 cache: Optional[NewsCache] = None):
        # MarketAux rate limiter (conservative estimate)
        if rate_limiter is None:
            rate_limiter = RateLimiter(requests_per_minute=30)
            
        super().__init__(api_token, NewsAPIProvider.MARKETAUX, rate_limiter, cache)
        
        # Set MarketAux quota (estimate based on free tier)
        self.quota = APIQuota(provider=NewsAPIProvider.MARKETAUX, requests_per_day=1000)
        
        # Store token separately as MarketAux uses different parameter name
        self.api_token = api_token
    
    def _build_url(self, endpoint: str, **params) -> str:
        """Build MarketAux API URL with parameters"""
        base_params = {'api_token': self.api_token}
        base_params.update(params)
        
        url = f"{self.BASE_URL}/{endpoint}"
        if base_params:
            url += f"?{urlencode(base_params)}"
        
        return url
    
    def _parse_sentiment_score(self, sentiment_str: Optional[str]) -> Optional[float]:
        """Parse MarketAux sentiment label to numeric score"""
        if not sentiment_str:
            return None
            
        sentiment_mapping = {
            'negative': -0.7,
            'neutral': 0.0,
            'positive': 0.7,
            'very_negative': -1.0,
            'very_positive': 1.0,
            'bearish': -0.8,
            'bullish': 0.8
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
        """Parse MarketAux news article data into standardized format"""
        try:
            # Extract basic article info
            title = article_data.get('title', '')
            content = article_data.get('description', '') or article_data.get('snippet', '')
            url = article_data.get('url', '')
            source = article_data.get('source', '')
            
            # Parse timestamp
            published_at = datetime.now()
            date_str = article_data.get('published_at', '')
            
            if date_str:
                try:
                    # MarketAux format: 2024-01-15T10:30:00.000000Z
                    published_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        # Fallback format
                        published_at = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        logger.warning(f"Could not parse MarketAux date: {date_str}")
            
            # Extract sentiment data
            sentiment_score = None
            sentiment_label = None
            confidence = None
            
            # MarketAux provides sentiment object
            sentiment_data = article_data.get('sentiment', {})
            if sentiment_data:
                sentiment_str = sentiment_data.get('sentiment')
                confidence = sentiment_data.get('confidence')
                
                if sentiment_str:
                    sentiment_score = self._parse_sentiment_score(sentiment_str)
                    if sentiment_score is not None:
                        sentiment_label = self._parse_sentiment_enum(sentiment_score)
            
            # Extract entities and symbols
            entities = article_data.get('entities', [])
            symbols = []
            keywords = []
            
            for entity in entities:
                if entity.get('type') == 'equity':
                    symbols.append(entity.get('symbol', ''))
                elif entity.get('name'):
                    keywords.append(entity.get('name'))
            
            # Use provided ticker or first symbol found
            article_ticker = ticker or (symbols[0] if symbols else None)
            
            # Extract additional metadata
            image_url = article_data.get('image_url', '')
            language = article_data.get('language', 'en')
            
            # Build metadata
            metadata = {
                'uuid': article_data.get('uuid', ''),
                'entities': entities,
                'symbols': symbols,
                'image_url': image_url,
                'language': language,
                'source_url': article_data.get('source_url', ''),
                'original_sentiment': sentiment_data,
                'similar': article_data.get('similar', [])
            }
            
            return NewsArticle(
                title=title,
                content=content,
                url=url,
                source=source,
                published_at=published_at,
                provider=NewsAPIProvider.MARKETAUX,
                ticker=article_ticker,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=confidence,
                keywords=keywords,
                entities=[entity.get('name', '') for entity in entities if entity.get('name')],
                category=None,
                metadata=metadata
            )
            
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse MarketAux article: {e}")
            return None
    
    def get_news(self, ticker: Optional[str] = None, limit: int = 20,
                 hours_back: int = 24) -> List[NewsArticle]:
        """Get financial news from MarketAux"""
        params = {
            'limit': min(limit, 100),  # MarketAux max limit per request
            'sort': 'published_desc',
            'filter_entities': 'true',  # Include entity information
            'language': 'en'
        }
        
        # Add ticker-specific filtering if provided
        if ticker:
            params['symbols'] = ticker
        else:
            # Get general financial news
            params['entities'] = 'equity'
        
        # Add time range filtering
        if hours_back < 24 * 7:  # Less than a week
            published_after = datetime.now() - timedelta(hours=hours_back)
            params['published_after'] = published_after.strftime('%Y-%m-%dT%H:%M:%S')
        
        url = self._build_url('news/all', **params)
        
        response_data = self._make_request(url, {}, endpoint='news')
        if not response_data:
            return []
        
        articles = []
        news_data = response_data.get('data', [])
        
        for article_data in news_data:
            article = self._parse_news_article(article_data, ticker)
            if article:
                articles.append(article)
        
        logger.info(f"Retrieved {len(articles)} articles from MarketAux" + 
                   (f" for {ticker}" if ticker else ""))
        return articles[:limit]
    
    def get_sentiment(self, ticker: str, hours_back: int = 24) -> Optional[float]:
        """Get aggregated sentiment score for a ticker from MarketAux"""
        articles = self.get_news(ticker=ticker, limit=50, hours_back=hours_back)
        
        if not articles:
            return None
        
        # Calculate weighted average sentiment using confidence scores
        total_sentiment = 0
        total_weight = 0
        
        for article in articles:
            if article.sentiment_score is not None:
                # Weight by confidence if available, otherwise equal weight
                weight = article.confidence if article.confidence else 1.0
                total_sentiment += article.sentiment_score * weight
                total_weight += weight
        
        if total_weight == 0:
            return None
        
        avg_sentiment = total_sentiment / total_weight
        logger.info(f"MarketAux sentiment for {ticker}: {avg_sentiment:.3f} (from {len(articles)} articles)")
        
        return avg_sentiment
    
    def search_news(self, query: str, limit: int = 20) -> List[NewsArticle]:
        """Search news by keywords in MarketAux"""
        params = {
            'search': query,
            'limit': min(limit, 100),
            'sort': 'published_desc',
            'filter_entities': 'true',
            'language': 'en'
        }
        
        url = self._build_url('news/all', **params)
        
        response_data = self._make_request(url, {}, endpoint='search')
        if not response_data:
            return []
        
        articles = []
        news_data = response_data.get('data', [])
        
        for article_data in news_data:
            article = self._parse_news_article(article_data)
            if article:
                articles.append(article)
        
        logger.info(f"Found {len(articles)} articles matching '{query}' in MarketAux")
        return articles[:limit]
    
    def get_news_by_category(self, category: str, limit: int = 20) -> List[NewsArticle]:
        """Get news by category (e.g., 'general', 'forex', 'crypto', 'merger')"""
        params = {
            'categories': category,
            'limit': min(limit, 100),
            'sort': 'published_desc',
            'filter_entities': 'true',
            'language': 'en'
        }
        
        url = self._build_url('news/all', **params)
        
        response_data = self._make_request(url, {}, endpoint=f'news_{category}')
        if not response_data:
            return []
        
        articles = []
        news_data = response_data.get('data', [])
        
        for article_data in news_data:
            article = self._parse_news_article(article_data)
            if article:
                article.category = category
                articles.append(article)
        
        logger.info(f"Retrieved {len(articles)} {category} articles from MarketAux")
        return articles[:limit]
    
    def get_trending_news(self, limit: int = 20, hours_back: int = 6) -> List[NewsArticle]:
        """Get trending financial news"""
        params = {
            'limit': min(limit, 100),
            'sort': 'social_score_desc',  # Sort by social engagement
            'filter_entities': 'true',
            'language': 'en'
        }
        
        # Get recent trending news
        published_after = datetime.now() - timedelta(hours=hours_back)
        params['published_after'] = published_after.strftime('%Y-%m-%dT%H:%M:%S')
        
        url = self._build_url('news/all', **params)
        
        response_data = self._make_request(url, {}, endpoint='trending')
        if not response_data:
            return []
        
        articles = []
        news_data = response_data.get('data', [])
        
        for article_data in news_data:
            article = self._parse_news_article(article_data)
            if article:
                articles.append(article)
        
        logger.info(f"Retrieved {len(articles)} trending articles from MarketAux")
        return articles[:limit]
    
    def get_market_sentiment_summary(self, hours_back: int = 24) -> Optional[Dict[str, Any]]:
        """Get overall market sentiment summary"""
        # Get general market news
        articles = self.get_news(limit=100, hours_back=hours_back)
        
        if not articles:
            return None
        
        # Analyze sentiment distribution
        sentiments = [article.sentiment_score for article in articles if article.sentiment_score is not None]
        
        if not sentiments:
            return None
        
        # Calculate statistics
        positive_count = sum(1 for s in sentiments if s > 0.2)
        negative_count = sum(1 for s in sentiments if s < -0.2)
        neutral_count = len(sentiments) - positive_count - negative_count
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Get most mentioned entities
        all_entities = []
        for article in articles:
            all_entities.extend(article.entities)
        
        entity_counts = {}
        for entity in all_entities:
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
        
        top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'period_hours': hours_back,
            'total_articles': len(articles),
            'sentiment_distribution': {
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count
            },
            'average_sentiment': avg_sentiment,
            'sentiment_scores': sentiments,
            'top_entities': dict(top_entities),
            'timestamp': datetime.now().isoformat(),
            'provider': 'MarketAux'
        }