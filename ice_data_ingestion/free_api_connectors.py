# ice_data_ingestion/free_api_connectors.py
"""
Free API connectors as fallback for MCP servers
Implements zero-cost alternatives using free financial APIs
Fallback system when MCP servers are unavailable
Relevant files: mcp_data_manager.py, mcp_infrastructure.py
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class APIConnectionConfig:
    """Configuration for free API connections"""
    name: str
    base_url: str
    api_key_required: bool
    rate_limit_per_minute: int
    daily_limit: Optional[int]
    capabilities: List[str]


class BaseAPIConnector(ABC):
    """Abstract base class for free API connectors"""
    
    def __init__(self, config: APIConnectionConfig, api_key: Optional[str] = None):
        self.config = config
        self.api_key = api_key
        self.session = None
        self.request_count = 0
        self.last_reset = datetime.now()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _check_rate_limit(self) -> bool:
        """Check if within rate limits"""
        now = datetime.now()
        time_diff = (now - self.last_reset).total_seconds()
        
        # Reset counter every minute
        if time_diff >= 60:
            self.request_count = 0
            self.last_reset = now
            
        if self.request_count >= self.config.rate_limit_per_minute:
            return False
            
        self.request_count += 1
        return True
    
    @abstractmethod
    async def fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock data for given symbol"""
        pass
    
    @abstractmethod
    async def fetch_news(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """Fetch news for given symbol"""
        pass


class AlphaVantageConnector(BaseAPIConnector):
    """Alpha Vantage free API connector (500 requests/day)"""
    
    def __init__(self, api_key: Optional[str] = None):
        config = APIConnectionConfig(
            name="alpha_vantage",
            base_url="https://www.alphavantage.co/query",
            api_key_required=True,
            rate_limit_per_minute=5,
            daily_limit=500,
            capabilities=["stock_data", "news", "technical_indicators"]
        )
        super().__init__(config, api_key)
    
    async def fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock data from Alpha Vantage"""
        if not self.api_key:
            return {"error": "API key required for Alpha Vantage"}
            
        if not await self._check_rate_limit():
            return {"error": "Rate limit exceeded"}
            
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            async with self.session.get(self.config.base_url, params=params) as response:
                data = await response.json()
                
                # Alpha Vantage returns nested structure
                if "Global Quote" in data:
                    quote = data["Global Quote"]
                    return {
                        "symbol": symbol,
                        "price": float(quote.get("05. price", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
                        "volume": int(quote.get("06. volume", 0)),
                        "timestamp": datetime.now().isoformat(),
                        "source": "alpha_vantage"
                    }
                else:
                    return {"error": "Invalid response format", "raw_data": data}
                    
        except Exception as e:
            logger.error(f"Alpha Vantage API error: {e}")
            return {"error": str(e)}
    
    async def fetch_news(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """Fetch news from Alpha Vantage"""
        if not self.api_key:
            return {"error": "API key required"}
            
        if not await self._check_rate_limit():
            return {"error": "Rate limit exceeded"}
            
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "apikey": self.api_key,
            "limit": min(limit, 50)
        }
        
        try:
            async with self.session.get(self.config.base_url, params=params) as response:
                data = await response.json()
                
                if "feed" in data:
                    articles = []
                    for item in data["feed"][:limit]:
                        articles.append({
                            "title": item.get("title", ""),
                            "summary": item.get("summary", ""),
                            "url": item.get("url", ""),
                            "published_at": item.get("time_published", ""),
                            "sentiment": float(item.get("overall_sentiment_score", 0)),
                            "source": "alpha_vantage"
                        })
                    
                    return {"articles": articles}
                else:
                    return {"error": "No news data available", "raw_data": data}
                    
        except Exception as e:
            logger.error(f"Alpha Vantage news API error: {e}")
            return {"error": str(e)}


class FinnhubConnector(BaseAPIConnector):
    """Finnhub free API connector (60 requests/minute)"""
    
    def __init__(self, api_key: Optional[str] = None):
        config = APIConnectionConfig(
            name="finnhub",
            base_url="https://finnhub.io/api/v1",
            api_key_required=True,
            rate_limit_per_minute=60,
            daily_limit=None,
            capabilities=["stock_data", "news"]
        )
        super().__init__(config, api_key)
    
    async def fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock data from Finnhub"""
        if not self.api_key:
            return {"error": "API key required for Finnhub"}
            
        if not await self._check_rate_limit():
            return {"error": "Rate limit exceeded"}
            
        try:
            # Fetch quote data
            quote_params = {"symbol": symbol, "token": self.api_key}
            async with self.session.get(f"{self.config.base_url}/quote", params=quote_params) as response:
                quote_data = await response.json()
                
            if "error" in quote_data:
                return {"error": quote_data["error"]}
                
            return {
                "symbol": symbol,
                "price": quote_data.get("c", 0),  # Current price
                "change": quote_data.get("d", 0),  # Change
                "change_percent": quote_data.get("dp", 0),  # Change percent
                "high": quote_data.get("h", 0),  # High
                "low": quote_data.get("l", 0),  # Low
                "open": quote_data.get("o", 0),  # Open
                "previous_close": quote_data.get("pc", 0),  # Previous close
                "timestamp": datetime.now().isoformat(),
                "source": "finnhub"
            }
            
        except Exception as e:
            logger.error(f"Finnhub API error: {e}")
            return {"error": str(e)}
    
    async def fetch_news(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """Fetch news from Finnhub"""
        if not self.api_key:
            return {"error": "API key required"}
            
        if not await self._check_rate_limit():
            return {"error": "Rate limit exceeded"}
            
        # Get news from last week
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date,
            "token": self.api_key
        }
        
        try:
            async with self.session.get(f"{self.config.base_url}/company-news", params=params) as response:
                data = await response.json()
                
                if isinstance(data, list):
                    articles = []
                    for item in data[:limit]:
                        articles.append({
                            "title": item.get("headline", ""),
                            "summary": item.get("summary", ""),
                            "url": item.get("url", ""),
                            "published_at": datetime.fromtimestamp(item.get("datetime", 0)).isoformat(),
                            "source": item.get("source", "finnhub")
                        })
                    
                    return {"articles": articles}
                else:
                    return {"error": "Unexpected response format", "raw_data": data}
                    
        except Exception as e:
            logger.error(f"Finnhub news API error: {e}")
            return {"error": str(e)}


class YahooFinanceConnector(BaseAPIConnector):
    """Yahoo Finance connector using yfinance library (no API key needed)"""
    
    def __init__(self):
        config = APIConnectionConfig(
            name="yahoo_finance_direct",
            base_url="",  # Using yfinance library
            api_key_required=False,
            rate_limit_per_minute=60,
            daily_limit=None,
            capabilities=["stock_data", "financial_metrics"]
        )
        super().__init__(config)
    
    async def fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock data using yfinance"""
        try:
            # Import yfinance dynamically
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "price": info.get("currentPrice", 0),
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
                "volume": info.get("regularMarketVolume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "52_week_high": info.get("fiftyTwoWeekHigh", 0),
                "52_week_low": info.get("fiftyTwoWeekLow", 0),
                "timestamp": datetime.now().isoformat(),
                "source": "yahoo_finance_direct"
            }
            
        except ImportError:
            return {"error": "yfinance library not installed"}
        except Exception as e:
            logger.error(f"Yahoo Finance error: {e}")
            return {"error": str(e)}
    
    async def fetch_news(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """Fetch news using yfinance"""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            articles = []
            for item in news[:limit]:
                articles.append({
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "url": item.get("link", ""),
                    "published_at": datetime.fromtimestamp(item.get("providerPublishTime", 0)).isoformat(),
                    "publisher": item.get("publisher", ""),
                    "source": "yahoo_finance_direct"
                })
            
            return {"articles": articles}
            
        except ImportError:
            return {"error": "yfinance library not installed"}
        except Exception as e:
            logger.error(f"Yahoo Finance news error: {e}")
            return {"error": str(e)}


class FreeAPIManager:
    """Manager for free API connectors with failover logic"""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """Initialize with optional API keys"""
        api_keys = api_keys or {}
        
        self.connectors = {
            "yahoo_finance": YahooFinanceConnector(),
            "alpha_vantage": AlphaVantageConnector(api_keys.get("alpha_vantage")),
            "finnhub": FinnhubConnector(api_keys.get("finnhub"))
        }
        
        # Priority order for different data types
        self.priority_order = {
            "stock_data": ["yahoo_finance", "alpha_vantage", "finnhub"],
            "news": ["alpha_vantage", "finnhub", "yahoo_finance"]
        }
    
    async def fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock data with automatic failover"""
        for connector_name in self.priority_order["stock_data"]:
            connector = self.connectors[connector_name]
            
            async with connector:
                result = await connector.fetch_stock_data(symbol)
                
                if "error" not in result:
                    return result
                else:
                    logger.warning(f"{connector_name} failed: {result['error']}")
        
        return {"error": "All free API connectors failed"}
    
    async def fetch_news(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """Fetch news with automatic failover"""
        all_articles = []
        
        for connector_name in self.priority_order["news"]:
            connector = self.connectors[connector_name]
            
            async with connector:
                result = await connector.fetch_news(symbol, limit)
                
                if "error" not in result and "articles" in result:
                    all_articles.extend(result["articles"])
                    if len(all_articles) >= limit:
                        break
                else:
                    logger.warning(f"{connector_name} news failed: {result.get('error', 'Unknown error')}")
        
        if all_articles:
            return {"articles": all_articles[:limit]}
        else:
            return {"error": "No news data available from free APIs"}
    
    async def get_comprehensive_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive data using free APIs"""
        results = await asyncio.gather(
            self.fetch_stock_data(symbol),
            self.fetch_news(symbol, 5),
            return_exceptions=True
        )
        
        stock_data, news_data = results[0], results[1]
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "stock_data": stock_data if "error" not in stock_data else None,
            "news": news_data.get("articles", []) if "articles" in news_data else [],
            "sources_used": [
                stock_data.get("source") for stock_data in [stock_data] if "source" in stock_data
            ] + [
                "news_apis" if news_data.get("articles") else None
            ],
            "fallback_mode": True
        }


# Global instance for easy access
free_api_manager = FreeAPIManager()


async def get_fallback_data(symbol: str) -> Dict[str, Any]:
    """High-level function to get data from free APIs when MCP servers fail"""
    try:
        return await free_api_manager.get_comprehensive_data(symbol)
    except Exception as e:
        logger.error(f"Free API fallback failed: {e}")
        return {
            "symbol": symbol,
            "error": f"All data sources failed: {e}",
            "timestamp": datetime.now().isoformat(),
            "fallback_mode": True
        }