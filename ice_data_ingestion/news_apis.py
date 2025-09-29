# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/news_apis.py
# Base classes and interfaces for financial news API integration
# Provides abstract base classes and unified interface for multiple news data sources
# RELEVANT FILES: __init__.py, alpha_vantage_client.py, fmp_client.py, marketaux_client.py

"""
News API Base Classes and Manager

This module provides the foundational classes for integrating multiple financial news APIs
into the ICE system. It includes abstract base classes, rate limiting, caching, and 
a unified manager interface for coordinating multiple data sources.

Key Components:
- NewsAPIClient: Abstract base class for all news API implementations
- NewsAPIManager: Coordinates multiple APIs with fallback logic
- RateLimiter: Handles API rate limiting and quota management
- NewsCache: Caches API responses to minimize redundant requests

Design Patterns:
- Strategy Pattern: Different API implementations behind common interface
- Facade Pattern: NewsAPIManager provides unified interface
- Decorator Pattern: Rate limiting and caching as decorators
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import json
import hashlib
import logging
from enum import Enum
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAPIProvider(Enum):
    """Enumeration of supported news API providers"""
    ALPHA_VANTAGE = "alpha_vantage"
    FINANCIAL_MODELING_PREP = "fmp" 
    MARKETAUX = "marketaux"
    POLYGON = "polygon"
    FINNHUB = "finnhub"
    NEWSAPI_ORG = "newsapi_org"
    BENZINGA = "benzinga"

class SentimentScore(Enum):
    """Standardized sentiment classification"""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2

@dataclass
class NewsArticle:
    """Standardized news article data structure"""
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    provider: NewsAPIProvider
    ticker: Optional[str] = None
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    sentiment_label: Optional[SentimentScore] = None
    confidence: Optional[float] = None  # 0.0 to 1.0
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    category: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert article to dictionary for JSON serialization"""
        return {
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'source': self.source,
            'published_at': self.published_at.isoformat(),
            'provider': self.provider.value,
            'ticker': self.ticker,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label.value if self.sentiment_label else None,
            'confidence': self.confidence,
            'keywords': self.keywords,
            'entities': self.entities,
            'category': self.category,
            'metadata': self.metadata
        }

@dataclass
class APIQuota:
    """API usage quota tracking"""
    provider: NewsAPIProvider
    requests_per_day: int
    requests_used: int = 0
    last_reset: datetime = field(default_factory=datetime.now)
    
    def can_make_request(self) -> bool:
        """Check if we can make another API request within quota"""
        # Reset quota if it's a new day
        if datetime.now().date() > self.last_reset.date():
            self.requests_used = 0
            self.last_reset = datetime.now()
        
        return self.requests_used < self.requests_per_day
    
    def record_request(self):
        """Record a successful API request"""
        self.requests_used += 1

class RateLimiter:
    """Rate limiting mechanism for API requests"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[datetime] = []
    
    def wait_if_needed(self):
        """Wait if we're hitting rate limits"""
        now = datetime.now()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < timedelta(minutes=1)]
        
        if len(self.request_times) >= self.requests_per_minute:
            # Calculate wait time until oldest request is 1 minute old
            oldest_request = min(self.request_times)
            wait_time = 61 - (now - oldest_request).seconds
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
        
        self.request_times.append(now)

class NewsCache:
    """Simple file-based cache for news API responses"""
    
    def __init__(self, cache_dir: str = "user_data/news_cache", ttl_hours: int = 6):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    
    def _get_cache_key(self, provider: NewsAPIProvider, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate unique cache key from API call parameters"""
        key_data = f"{provider.value}_{endpoint}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, provider: NewsAPIProvider, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve cached response if available and not expired"""
        cache_key = self._get_cache_key(provider, endpoint, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                cache_file.unlink()  # Remove expired cache
                return None
            
            return cached_data['data']
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Invalid cache file {cache_file}: {e}")
            cache_file.unlink()  # Remove corrupted cache
            return None
    
    def set(self, provider: NewsAPIProvider, endpoint: str, params: Dict[str, Any], data: Dict[str, Any]):
        """Cache API response"""
        cache_key = self._get_cache_key(provider, endpoint, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")

class NewsAPIClient(ABC):
    """Abstract base class for news API clients"""
    
    def __init__(self, api_key: str, provider: NewsAPIProvider, rate_limiter: Optional[RateLimiter] = None, 
                 cache: Optional[NewsCache] = None):
        self.api_key = api_key
        self.provider = provider
        self.rate_limiter = rate_limiter or RateLimiter()
        self.cache = cache or NewsCache()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ICE-Investment-Context-Engine/1.0'})
        
        # Initialize quota tracking (to be overridden by subclasses)
        self.quota = APIQuota(provider=provider, requests_per_day=100)  # Conservative default
    
    def _make_request(self, url: str, params: Dict[str, Any], endpoint: str = "") -> Optional[Dict[str, Any]]:
        """Make rate-limited, cached API request"""
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
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
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
    
    @abstractmethod
    def get_news(self, ticker: Optional[str] = None, limit: int = 20, 
                 hours_back: int = 24) -> List[NewsArticle]:
        """Get news articles for a specific ticker or general market news"""
        pass
    
    @abstractmethod
    def get_sentiment(self, ticker: str, hours_back: int = 24) -> Optional[float]:
        """Get aggregated sentiment score for a ticker"""
        pass
    
    @abstractmethod
    def search_news(self, query: str, limit: int = 20) -> List[NewsArticle]:
        """Search for news articles by query"""
        pass
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current API quota usage status"""
        return {
            'provider': self.provider.value,
            'requests_used': self.quota.requests_used,
            'requests_per_day': self.quota.requests_per_day,
            'requests_remaining': self.quota.requests_per_day - self.quota.requests_used,
            'last_reset': self.quota.last_reset.isoformat()
        }

class NewsAPIManager:
    """Manager class to coordinate multiple news API clients"""
    
    def __init__(self, cache: Optional[NewsCache] = None):
        self.clients: Dict[NewsAPIProvider, NewsAPIClient] = {}
        self.cache = cache or NewsCache()
        self.primary_provider = NewsAPIProvider.ALPHA_VANTAGE  # Default primary
    
    def register_client(self, client: NewsAPIClient, set_as_primary: bool = False):
        """Register a news API client"""
        self.clients[client.provider] = client
        if set_as_primary:
            self.primary_provider = client.provider
        logger.info(f"Registered {client.provider.value} client")
    
    def set_primary_provider(self, provider: NewsAPIProvider):
        """Set the primary news provider"""
        if provider in self.clients:
            self.primary_provider = provider
            logger.info(f"Set primary provider to {provider.value}")
        else:
            logger.warning(f"Provider {provider.value} not registered")
    
    def get_financial_news(self, ticker: Optional[str] = None, limit: int = 20, 
                          hours_back: int = 24, fallback: bool = True) -> List[NewsArticle]:
        """Get financial news with automatic fallback between providers"""
        articles = []
        
        # Try primary provider first
        if self.primary_provider in self.clients:
            try:
                articles = self.clients[self.primary_provider].get_news(ticker, limit, hours_back)
                if articles:
                    logger.info(f"Retrieved {len(articles)} articles from primary provider {self.primary_provider.value}")
                    return articles
            except Exception as e:
                logger.warning(f"Primary provider {self.primary_provider.value} failed: {e}")
        
        # Fallback to other providers if enabled
        if fallback and not articles:
            for provider, client in self.clients.items():
                if provider == self.primary_provider:
                    continue  # Already tried
                try:
                    articles = client.get_news(ticker, limit, hours_back)
                    if articles:
                        logger.info(f"Fallback successful: Retrieved {len(articles)} articles from {provider.value}")
                        return articles
                except Exception as e:
                    logger.warning(f"Fallback provider {provider.value} failed: {e}")
        
        logger.warning("No articles retrieved from any provider")
        return articles
    
    def get_aggregated_sentiment(self, ticker: str, hours_back: int = 24) -> Optional[Dict[str, Any]]:
        """Get sentiment scores from all available providers"""
        sentiment_data = {}
        
        for provider, client in self.clients.items():
            try:
                sentiment = client.get_sentiment(ticker, hours_back)
                if sentiment is not None:
                    sentiment_data[provider.value] = sentiment
            except Exception as e:
                logger.warning(f"Failed to get sentiment from {provider.value}: {e}")
        
        if not sentiment_data:
            return None
        
        # Calculate aggregate metrics
        scores = list(sentiment_data.values())
        return {
            'individual_scores': sentiment_data,
            'average': sum(scores) / len(scores),
            'min': min(scores),
            'max': max(scores),
            'count': len(scores),
            'ticker': ticker,
            'hours_back': hours_back,
            'timestamp': datetime.now().isoformat()
        }
    
    def search_news(self, query: str, limit: int = 20, provider: Optional[NewsAPIProvider] = None) -> List[NewsArticle]:
        """Search news across providers"""
        if provider and provider in self.clients:
            return self.clients[provider].search_news(query, limit)
        
        # Search across all providers
        all_articles = []
        for client in self.clients.values():
            try:
                articles = client.search_news(query, limit)
                all_articles.extend(articles)
            except Exception as e:
                logger.warning(f"Search failed for {client.provider.value}: {e}")
        
        # Remove duplicates based on URL and sort by recency
        seen_urls = set()
        unique_articles = []
        for article in sorted(all_articles, key=lambda x: x.published_at, reverse=True):
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        return unique_articles[:limit]
    
    def get_all_quota_status(self) -> Dict[str, Dict[str, Any]]:
        """Get quota status for all registered providers"""
        return {provider.value: client.get_quota_status() 
                for provider, client in self.clients.items()}
    
    def get_available_providers(self) -> List[NewsAPIProvider]:
        """Get list of registered providers"""
        return list(self.clients.keys())