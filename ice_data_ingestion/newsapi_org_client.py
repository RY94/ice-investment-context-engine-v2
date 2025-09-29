# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/newsapi_org_client.py
# NewsAPI.org client implementation for general and financial news
# Provides integration with NewsAPI.org's comprehensive news aggregation service
# RELEVANT FILES: news_apis.py, alpha_vantage_client.py, benzinga_client.py, polygon_client.py

"""
NewsAPI.org Client

NewsAPI.org is a comprehensive news aggregation service that provides:
- News from 150,000+ sources worldwide
- General news, business news, and financial coverage
- Search capabilities across historical articles
- Category filtering and source selection
- Real-time and historical data access

API Features:
- Everything endpoint: Search across all articles
- Top headlines: Latest breaking news
- Sources endpoint: Available news sources
- Category filtering: business, technology, general
- Language and country filtering
- Keyword search with complex queries

Free Tier Limitations:
- 100 requests per day (very limited)
- Articles delayed by 24 hours
- No commercial usage on free tier
- Rate limit: 1 request per second

Paid Plans:
- Developer: $449/month, 10K requests/day
- Business: $899/month, 100K requests/day
- Enterprise: Custom pricing

Authentication:
- Requires API key
- API key passed as 'X-API-Key' header
- Register at: https://newsapi.org/register

Note: Due to the restrictive free tier (100 req/day, 24h delay),
this client is primarily useful for demonstration or when combined
with paid plans for production usage.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import re
import json
import requests
from urllib.parse import urlencode

from .news_apis import (
    NewsAPIClient, NewsAPIProvider, NewsArticle, SentimentScore,
    APIQuota, RateLimiter, NewsCache
)

logger = logging.getLogger(__name__)

class NewsAPIClient_Org(NewsAPIClient):
    """NewsAPI.org client for general and financial news"""
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: str, rate_limiter: Optional[RateLimiter] = None,
                 cache: Optional[NewsCache] = None):
        # NewsAPI.org specific rate limiter (1 req/sec, 100 req/day)
        if rate_limiter is None:
            rate_limiter = RateLimiter(requests_per_minute=60)  # Max 1 per second
            
        super().__init__(api_key, NewsAPIProvider.NEWSAPI_ORG, rate_limiter, cache)
        
        # Set NewsAPI.org quota (100 requests per day for free tier)
        self.quota = APIQuota(provider=NewsAPIProvider.NEWSAPI_ORG, requests_per_day=100)
        
        # Update session headers for NewsAPI.org authentication
        self.session.headers.update({'X-API-Key': self.api_key})
        
        # Financial keywords for better filtering
        self.financial_keywords = [
            'stock', 'shares', 'market', 'trading', 'investor', 'earnings', 'revenue',
            'financial', 'economy', 'nasdaq', 'nyse', 'dow', 'sp500', 'portfolio',
            'dividend', 'acquisition', 'merger', 'ipo', 'cryptocurrency', 'bitcoin'
        ]
    
    def _build_url(self, endpoint: str, **params) -> str:
        """Build NewsAPI.org URL with parameters"""
        url = f"{self.BASE_URL}/{endpoint}"
        if params:
            url += f"?{urlencode(params)}"
        return url
    
    def _make_request(self, url: str, params: Dict[str, Any], endpoint: str = "") -> Optional[Dict[str, Any]]:
        """Override to handle NewsAPI.org specific authentication and response format"""
        # Check cache first
        cached_response = self.cache.get(self.provider, endpoint, params)
        if cached_response:
            logger.debug(f"Cache hit for {self.provider.value} {endpoint}")
            return cached_response
        
        # Check quota
        if not self.quota.can_make_request():
            logger.warning(f"API quota exceeded for {self.provider.value}. Used {self.quota.requests_used}/{self.quota.requests_per_day}")
            return None
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            logger.info(f"Making API request to {self.provider.value}: {url}")
            
            # NewsAPI.org uses headers for authentication, not URL params
            headers = {
                'X-API-Key': self.api_key,
                'User-Agent': 'ICE-Investment-Context-Engine/1.0'
            }
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check NewsAPI.org specific error format
            if data.get('status') != 'ok':
                error_code = data.get('code', 'unknown')
                error_message = data.get('message', 'Unknown error')
                logger.error(f"NewsAPI.org error: {error_code} - {error_message}")
                return None
            
            # Record successful request
            self.quota.record_request()
            
            # Cache response
            self.cache.set(self.provider, endpoint, params, data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {self.provider.value}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from {self.provider.value}: {e}")
            return None
    
    def _estimate_sentiment(self, title: str, description: str) -> Tuple[Optional[float], Optional[SentimentScore]]:
        """Estimate sentiment from article content (NewsAPI.org doesn't provide sentiment)"""
        content = f"{title} {description}".lower()
        
        # Simple keyword-based sentiment analysis
        positive_words = [
            'surge', 'soar', 'rally', 'gain', 'rise', 'up', 'growth', 'profit', 'success',
            'breakthrough', 'improve', 'strong', 'beat', 'exceed', 'boost', 'advance',
            'positive', 'optimistic', 'bullish', 'upgrade', 'outperform'
        ]
        
        negative_words = [
            'fall', 'drop', 'decline', 'loss', 'down', 'crash', 'plunge', 'slide',
            'concern', 'worry', 'risk', 'threat', 'challenge', 'pressure', 'weak',
            'negative', 'pessimistic', 'bearish', 'downgrade', 'underperform', 'cut'
        ]
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count > negative_count:
            sentiment_score = min(0.8, 0.1 + (positive_count * 0.1))
            sentiment_label = SentimentScore.POSITIVE
        elif negative_count > positive_count:
            sentiment_score = max(-0.8, -0.1 - (negative_count * 0.1))
            sentiment_label = SentimentScore.NEGATIVE
        else:
            sentiment_score = 0.0
            sentiment_label = SentimentScore.NEUTRAL
        
        return sentiment_score, sentiment_label
    
    def _extract_tickers_from_content(self, title: str, description: str) -> List[str]:
        """Extract potential ticker symbols from article content"""
        content = f"{title} {description}"
        
        # Look for ticker patterns (2-5 uppercase letters)
        ticker_pattern = re.compile(r'\b[A-Z]{2,5}\b')
        potential_tickers = ticker_pattern.findall(content)
        
        # Filter out common false positives
        excluded_words = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 
            'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 
            'ITS', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID', 'USE', 
            'WAY', 'SHE', 'MAY', 'SAY', 'CEO', 'CFO', 'CTO', 'USA', 'USD', 'EUR',
            'API', 'GDP', 'IPO', 'ETF', 'SEC', 'FDA', 'FTC', 'DOJ'
        }
        
        return [ticker for ticker in potential_tickers if ticker not in excluded_words]
    
    def _parse_news_article(self, article_data: Dict[str, Any], ticker: Optional[str] = None) -> Optional[NewsArticle]:
        """Parse NewsAPI.org article data into standardized format"""
        try:
            # Extract basic article info
            title = article_data.get('title', '')
            description = article_data.get('description', '') or ''
            content = article_data.get('content', '') or description
            url = article_data.get('url', '')
            
            # Source information
            source_info = article_data.get('source', {})
            source = source_info.get('name', '') if source_info else ''
            
            # Parse timestamp
            published_at = datetime.now()
            date_str = article_data.get('publishedAt', '')
            
            if date_str:
                try:
                    # NewsAPI format: 2024-01-15T10:30:00Z
                    published_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    # Remove timezone info for consistency
                    published_at = published_at.replace(tzinfo=None)
                except ValueError:
                    logger.warning(f"Could not parse NewsAPI date: {date_str}")
            
            # Estimate sentiment (NewsAPI doesn't provide it)
            sentiment_score, sentiment_label = self._estimate_sentiment(title, description)
            
            # Extract potential tickers
            extracted_tickers = self._extract_tickers_from_content(title, description)
            article_ticker = ticker or (extracted_tickers[0] if extracted_tickers else None)
            
            # Extract author
            author = article_data.get('author', '')
            
            # Extract image URL
            image_url = article_data.get('urlToImage', '')
            
            # Create keywords from title and description
            keywords = []
            for keyword in self.financial_keywords:
                if keyword.lower() in f"{title} {description}".lower():
                    keywords.append(keyword)
            
            # Build metadata
            metadata = {
                'source_id': source_info.get('id', '') if source_info else '',
                'author': author,
                'image_url': image_url,
                'extracted_tickers': extracted_tickers,
                'estimated_sentiment': True,  # Flag indicating sentiment was estimated
                'content_preview': content[:100] + '...' if len(content) > 100 else content
            }
            
            return NewsArticle(
                title=title,
                content=content,
                url=url,
                source=source,
                published_at=published_at,
                provider=NewsAPIProvider.NEWSAPI_ORG,
                ticker=article_ticker,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=0.3,  # Lower confidence since sentiment is estimated
                keywords=keywords,
                entities=extracted_tickers,
                category='business' if any(kw in keywords for kw in ['stock', 'market', 'financial']) else None,
                metadata=metadata
            )
            
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse NewsAPI.org article: {e}")
            return None
    
    def get_news(self, ticker: Optional[str] = None, limit: int = 20,
                 hours_back: int = 24) -> List[NewsArticle]:
        """Get financial news from NewsAPI.org"""
        articles = []
        
        # Build search query
        if ticker:
            # Search for ticker-specific news
            query = f'("{ticker}" OR "{ticker} stock" OR "{ticker} shares") AND (earnings OR revenue OR financial OR market)'
        else:
            # General financial news query
            query = '(stock market OR financial OR earnings OR economy OR nasdaq OR trading)'
        
        # Calculate date range (limited to 1 month for free tier)
        from_date = datetime.now() - timedelta(hours=min(hours_back, 24*30))
        
        params = {
            'q': query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': min(limit, 100),  # NewsAPI max per request
            'from': from_date.strftime('%Y-%m-%d')
        }
        
        # Use 'everything' endpoint for search
        url = self._build_url('everything', **params)
        
        response_data = self._make_request(url, {}, endpoint='everything')
        if not response_data:
            return []
        
        # Parse articles
        news_articles = response_data.get('articles', [])
        
        for article_data in news_articles[:limit]:
            article = self._parse_news_article(article_data, ticker)
            if article:
                # Additional filtering for financial relevance
                if self._is_financially_relevant(article):
                    articles.append(article)
        
        logger.info(f"Retrieved {len(articles)} financially relevant articles from NewsAPI.org" + 
                   (f" for {ticker}" if ticker else ""))
        return articles
    
    def _is_financially_relevant(self, article: NewsArticle) -> bool:
        """Check if article is financially relevant"""
        content = f"{article.title} {article.content}".lower()
        
        # Must contain at least one financial keyword
        financial_terms = [
            'stock', 'share', 'market', 'trading', 'investor', 'earnings', 'revenue',
            'financial', 'nasdaq', 'nyse', 'portfolio', 'dividend', 'merger',
            'acquisition', 'ipo', 'cryptocurrency', 'economy', 'federal reserve'
        ]
        
        return any(term in content for term in financial_terms)
    
    def get_sentiment(self, ticker: str, hours_back: int = 24) -> Optional[float]:
        """Get aggregated sentiment score for a ticker from NewsAPI.org"""
        articles = self.get_news(ticker=ticker, limit=30, hours_back=hours_back)
        
        if not articles:
            return None
        
        # Calculate average sentiment
        sentiments = [article.sentiment_score for article in articles if article.sentiment_score is not None]
        
        if not sentiments:
            return None
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        logger.info(f"NewsAPI.org estimated sentiment for {ticker}: {avg_sentiment:.3f} (from {len(sentiments)} articles)")
        
        return avg_sentiment
    
    def search_news(self, query: str, limit: int = 20) -> List[NewsArticle]:
        """Search news by keywords in NewsAPI.org"""
        # Enhance query for financial context
        enhanced_query = f'"{query}" AND (financial OR market OR stock OR economy)'
        
        params = {
            'q': enhanced_query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': min(limit, 100)
        }
        
        url = self._build_url('everything', **params)
        
        response_data = self._make_request(url, {}, endpoint='search')
        if not response_data:
            return []
        
        articles = []
        news_articles = response_data.get('articles', [])
        
        for article_data in news_articles[:limit]:
            article = self._parse_news_article(article_data)
            if article and self._is_financially_relevant(article):
                articles.append(article)
        
        logger.info(f"Found {len(articles)} articles matching '{query}' in NewsAPI.org")
        return articles
    
    def get_top_business_headlines(self, limit: int = 20) -> List[NewsArticle]:
        """Get top business headlines from NewsAPI.org"""
        params = {
            'category': 'business',
            'language': 'en',
            'pageSize': min(limit, 100),
            'country': 'us'  # Focus on US business news
        }
        
        url = self._build_url('top-headlines', **params)
        
        response_data = self._make_request(url, {}, endpoint='top_headlines')
        if not response_data:
            return []
        
        articles = []
        news_articles = response_data.get('articles', [])
        
        for article_data in news_articles:
            article = self._parse_news_article(article_data)
            if article:
                articles.append(article)
        
        logger.info(f"Retrieved {len(articles)} top business headlines from NewsAPI.org")
        return articles
    
    def get_sources(self, category: str = 'business') -> List[Dict[str, Any]]:
        """Get available news sources from NewsAPI.org"""
        params = {
            'category': category,
            'language': 'en',
            'country': 'us'
        }
        
        url = self._build_url('sources', **params)
        
        response_data = self._make_request(url, {}, endpoint='sources')
        if not response_data:
            return []
        
        sources = response_data.get('sources', [])
        logger.info(f"Retrieved {len(sources)} {category} sources from NewsAPI.org")
        
        return sources