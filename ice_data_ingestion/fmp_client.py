# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/fmp_client.py
# Financial Modeling Prep (FMP) API client for comprehensive financial data and news
# Provides integration with FMP's financial statements, stock data, and news endpoints
# RELEVANT FILES: news_apis.py, alpha_vantage_client.py, marketaux_client.py, __init__.py

"""
Financial Modeling Prep (FMP) API Client

FMP is a comprehensive financial data provider that offers:
- Free tier with basic stock data and financial statements
- Real-time and historical prices
- Fundamental financial data
- RSS news feeds with sentiment analysis
- Social sentiment tracking
- Earnings data and financial ratios

API Endpoints Used:
- /v3/stock_news: General stock market news
- /v4/general_news: Broader financial news coverage  
- /v4/social-sentiment: Social media sentiment analysis
- /v3/historical-social-sentiment: Historical sentiment data
- /v3/rss_feed: RSS feed with sentiment scores

Free Tier Limits:
- 250 requests per day on free tier
- No real-time data on free tier (15-minute delay)
- Limited to basic endpoints

Sentiment Analysis:
- Provides sentiment scores and labels
- Social sentiment from multiple platforms
- Historical sentiment tracking
- RSS feed includes sentiment analysis per article

Authentication:
- Requires API key (free registration available)
- API key passed as query parameter 'apikey'
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode, quote
import re

from .news_apis import (
    NewsAPIClient, NewsAPIProvider, NewsArticle, SentimentScore,
    APIQuota, RateLimiter, NewsCache
)

logger = logging.getLogger(__name__)

class FMPClient(NewsAPIClient):
    """Financial Modeling Prep API client for financial news and sentiment"""
    
    BASE_URL = "https://financialmodelingprep.com/api"
    
    def __init__(self, api_key: str, rate_limiter: Optional[RateLimiter] = None,
                 cache: Optional[NewsCache] = None):
        # FMP specific rate limiter (conservative for free tier)
        if rate_limiter is None:
            rate_limiter = RateLimiter(requests_per_minute=10)
            
        super().__init__(api_key, NewsAPIProvider.FINANCIAL_MODELING_PREP, rate_limiter, cache)
        
        # Set FMP quota (250 requests per day for free tier)
        self.quota = APIQuota(provider=NewsAPIProvider.FINANCIAL_MODELING_PREP, requests_per_day=250)
    
    def _build_url(self, endpoint: str, version: str = "v3", **params) -> str:
        """Build FMP API URL with parameters"""
        base_params = {'apikey': self.api_key}
        base_params.update(params)
        
        url = f"{self.BASE_URL}/{version}/{endpoint}"
        if base_params:
            url += f"?{urlencode(base_params)}"
        
        return url
    
    def _parse_sentiment_score(self, sentiment_str: Optional[str]) -> Optional[float]:
        """Parse FMP sentiment label to numeric score"""
        if not sentiment_str:
            return None
            
        sentiment_mapping = {
            'Bearish': -0.8,
            'Somewhat-Bearish': -0.4,
            'Neutral': 0.0,
            'Somewhat-Bullish': 0.4,
            'Bullish': 0.8,
            'Very Bearish': -1.0,
            'Very Bullish': 1.0,
            'negative': -0.6,
            'positive': 0.6,
            'neutral': 0.0
        }
        
        # Handle various formats
        sentiment_clean = sentiment_str.strip().replace('_', ' ').title()
        return sentiment_mapping.get(sentiment_clean)
    
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
    
    def _clean_content(self, content: str) -> str:
        """Clean HTML tags and formatting from content"""
        if not content:
            return ""
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        # Remove extra whitespace
        content = ' '.join(content.split())
        
        return content
    
    def _parse_news_article(self, article_data: Dict[str, Any], ticker: Optional[str] = None) -> Optional[NewsArticle]:
        """Parse FMP news article data into standardized format"""
        try:
            # Extract basic article info
            title = article_data.get('title', '')
            content = self._clean_content(article_data.get('text', '') or article_data.get('content', ''))
            url = article_data.get('url', '')
            source = article_data.get('site', '') or article_data.get('source', '')
            
            # Parse timestamp
            published_at = datetime.now()
            date_str = article_data.get('publishedDate', '') or article_data.get('date', '')
            
            if date_str:
                try:
                    # Try different date formats
                    if 'T' in date_str:
                        # ISO format: 2024-01-15T10:30:00.000Z
                        published_at = datetime.fromisoformat(date_str.replace('Z', '+00:00').split('.')[0])
                    else:
                        # Date only: 2024-01-15
                        published_at = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Could not parse date: {date_str}")
            
            # Extract sentiment data
            sentiment_score = None
            sentiment_label = None
            
            # Check various sentiment fields
            if 'sentiment' in article_data:
                sentiment_score = self._parse_sentiment_score(article_data['sentiment'])
            elif 'sentimentScore' in article_data:
                sentiment_score = float(article_data['sentimentScore'])
            
            if sentiment_score is not None:
                sentiment_label = self._parse_sentiment_enum(sentiment_score)
            
            # Extract symbols/tickers mentioned
            symbols = article_data.get('symbols', []) or article_data.get('symbol', [])
            if isinstance(symbols, str):
                symbols = [symbols]
            
            # Use provided ticker or first symbol found
            article_ticker = ticker or (symbols[0] if symbols else None)
            
            # Extract image
            image_url = article_data.get('image', '')
            
            # Build metadata
            metadata = {
                'symbols': symbols,
                'image': image_url,
                'site': source,
                'original_sentiment': article_data.get('sentiment', ''),
                'tags': article_data.get('tags', []),
                'author': article_data.get('author', '')
            }
            
            return NewsArticle(
                title=title,
                content=content,
                url=url,
                source=source,
                published_at=published_at,
                provider=NewsAPIProvider.FINANCIAL_MODELING_PREP,
                ticker=article_ticker,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=None,  # FMP doesn't provide confidence scores
                keywords=[],  # Extract from symbols
                entities=symbols,
                category=None,
                metadata=metadata
            )
            
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse FMP article: {e}")
            return None
    
    def get_news(self, ticker: Optional[str] = None, limit: int = 20,
                 hours_back: int = 24) -> List[NewsArticle]:
        """Get financial news from FMP"""
        articles = []
        
        # Try multiple endpoints for better coverage
        endpoints_to_try = [
            ('v3/stock_news', {}),
            ('v4/general_news', {}),
        ]
        
        # Add ticker-specific endpoint if ticker provided
        if ticker:
            endpoints_to_try.insert(0, ('v3/stock_news', {'tickers': ticker}))
        
        for endpoint, params in endpoints_to_try:
            if len(articles) >= limit:
                break
                
            try:
                # Add pagination and limit
                params.update({
                    'limit': min(limit - len(articles), 100),
                    'page': 0
                })
                
                url = self._build_url(endpoint, **params)
                response_data = self._make_request(url, {}, endpoint=endpoint)
                
                if not response_data:
                    continue
                
                # Handle different response formats
                news_items = response_data
                if isinstance(response_data, dict):
                    news_items = response_data.get('content', response_data.get('data', []))
                
                for article_data in news_items:
                    if len(articles) >= limit:
                        break
                        
                    article = self._parse_news_article(article_data, ticker)
                    if article:
                        # Filter by time range
                        time_diff = datetime.now() - article.published_at
                        if time_diff.total_seconds() / 3600 <= hours_back:
                            articles.append(article)
                            
            except Exception as e:
                logger.warning(f"Failed to fetch from FMP endpoint {endpoint}: {e}")
                continue
        
        logger.info(f"Retrieved {len(articles)} articles from FMP" + 
                   (f" for {ticker}" if ticker else ""))
        return articles[:limit]
    
    def get_sentiment(self, ticker: str, hours_back: int = 24) -> Optional[float]:
        """Get aggregated sentiment score for a ticker from FMP"""
        # Try social sentiment endpoint first
        try:
            url = self._build_url(f'v4/social-sentiment', symbol=ticker)
            response_data = self._make_request(url, {}, endpoint='social_sentiment')
            
            if response_data and len(response_data) > 0:
                # Get latest sentiment data
                latest_sentiment = response_data[0]
                sentiment_score = latest_sentiment.get('sentiment', 0)
                
                logger.info(f"FMP social sentiment for {ticker}: {sentiment_score}")
                return float(sentiment_score)
                
        except Exception as e:
            logger.warning(f"Failed to get FMP social sentiment: {e}")
        
        # Fallback to news-based sentiment analysis
        articles = self.get_news(ticker=ticker, limit=30, hours_back=hours_back)
        
        if not articles:
            return None
        
        # Calculate average sentiment from news articles
        sentiments = [article.sentiment_score for article in articles if article.sentiment_score is not None]
        
        if not sentiments:
            return None
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        logger.info(f"FMP news sentiment for {ticker}: {avg_sentiment:.3f} (from {len(sentiments)} articles)")
        
        return avg_sentiment
    
    def search_news(self, query: str, limit: int = 20) -> List[NewsArticle]:
        """Search news by keywords in FMP"""
        # FMP doesn't have a direct search endpoint, so we'll get general news and filter
        try:
            url = self._build_url('v4/general_news', limit=min(limit * 2, 100))
            response_data = self._make_request(url, {}, endpoint='search_news')
            
            if not response_data:
                return []
            
            articles = []
            query_lower = query.lower()
            
            news_items = response_data
            if isinstance(response_data, dict):
                news_items = response_data.get('content', response_data.get('data', []))
            
            for article_data in news_items:
                # Simple keyword matching
                title = article_data.get('title', '').lower()
                content = article_data.get('text', '').lower()
                
                if query_lower in title or query_lower in content:
                    article = self._parse_news_article(article_data)
                    if article:
                        articles.append(article)
                        if len(articles) >= limit:
                            break
            
            logger.info(f"Found {len(articles)} articles matching '{query}' in FMP")
            return articles
            
        except Exception as e:
            logger.warning(f"FMP search failed: {e}")
            return []
    
    def get_social_sentiment_historical(self, symbol: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get historical social sentiment data"""
        try:
            url = self._build_url('v3/historical-social-sentiment', version='v3', symbol=symbol)
            response_data = self._make_request(url, {}, endpoint='historical_sentiment')
            
            if response_data:
                # Filter by date range
                cutoff_date = datetime.now() - timedelta(days=days)
                filtered_data = []
                
                for item in response_data:
                    date_str = item.get('date', '')
                    if date_str:
                        try:
                            item_date = datetime.strptime(date_str, '%Y-%m-%d')
                            if item_date >= cutoff_date:
                                filtered_data.append(item)
                        except ValueError:
                            continue
                
                return {
                    'symbol': symbol,
                    'data': filtered_data,
                    'period': f"{days} days",
                    'count': len(filtered_data)
                }
                
        except Exception as e:
            logger.warning(f"Failed to get FMP historical sentiment: {e}")
            
        return None
    
    def get_rss_feed(self, limit: int = 50) -> List[NewsArticle]:
        """Get RSS feed with sentiment analysis"""
        try:
            url = self._build_url('v3/rss_feed', limit=min(limit, 100))
            response_data = self._make_request(url, {}, endpoint='rss_feed')
            
            if not response_data:
                return []
            
            articles = []
            for article_data in response_data:
                article = self._parse_news_article(article_data)
                if article:
                    articles.append(article)
            
            logger.info(f"Retrieved {len(articles)} articles from FMP RSS feed")
            return articles
            
        except Exception as e:
            logger.warning(f"Failed to get FMP RSS feed: {e}")
            return []
    
    def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company profile data"""
        try:
            url = self._build_url('v3/profile', symbol=symbol)
            response_data = self._make_request(url, {}, endpoint='company_profile')
            
            if response_data and len(response_data) > 0:
                return response_data[0]
                
        except Exception as e:
            logger.warning(f"Failed to get FMP company profile: {e}")
            
        return None