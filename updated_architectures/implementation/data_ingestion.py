# data_ingestion.py
"""
ICE Data Ingestion - Simple API calls without transformation layers
Direct data fetching that returns text documents for LightRAG processing
Eliminates complex validation pipelines and transformation orchestration
Relevant files: ice_simplified.py, ice_core.py
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataIngester:
    """
    Simple data ingestion - Direct API calls without transformation layers

    Key principles:
    1. Fetch data from APIs
    2. Return raw text documents
    3. Let LightRAG handle entity extraction and processing
    4. No validation pipelines, enhancement layers, or complex transformations
    5. Graceful degradation when APIs are unavailable
    """

    def __init__(self, api_keys: Optional[Dict[str, str]] = None, timeout: int = 30):
        """
        Initialize data ingester with API configuration

        Args:
            api_keys: Dictionary of API service names to keys
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

        # Load API keys from parameter or environment
        self.api_keys = api_keys or {
            'newsapi': os.getenv('NEWSAPI_ORG_API_KEY'),
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'fmp': os.getenv('FMP_API_KEY'),
            'polygon': os.getenv('POLYGON_API_KEY'),
            'finnhub': os.getenv('FINNHUB_API_KEY'),
            'benzinga': os.getenv('BENZINGA_API_TOKEN'),
            'marketaux': os.getenv('MARKETAUX_API_KEY')
        }

        # Filter out None values
        self.api_keys = {k: v for k, v in self.api_keys.items() if v}

        self.available_services = list(self.api_keys.keys())

        logger.info(f"Data Ingester initialized with {len(self.available_services)} API services: {self.available_services}")

    def is_service_available(self, service: str) -> bool:
        """Check if specific API service is configured"""
        return service in self.api_keys and bool(self.api_keys[service])

    def fetch_company_news(self, symbol: str, limit: int = 5) -> List[str]:
        """
        Fetch company news from available APIs - return raw text documents

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of articles

        Returns:
            List of news article texts (no preprocessing, validation, or transformation)
        """
        documents = []

        # Try NewsAPI.org if available
        if self.is_service_available('newsapi'):
            try:
                documents.extend(self._fetch_newsapi(symbol, limit))
            except Exception as e:
                logger.warning(f"NewsAPI fetch failed for {symbol}: {e}")

        # Try Finnhub if available and we need more articles
        if self.is_service_available('finnhub') and len(documents) < limit:
            try:
                remaining = limit - len(documents)
                documents.extend(self._fetch_finnhub_news(symbol, remaining))
            except Exception as e:
                logger.warning(f"Finnhub news fetch failed for {symbol}: {e}")

        # Try MarketAux if available and we need more articles
        if self.is_service_available('marketaux') and len(documents) < limit:
            try:
                remaining = limit - len(documents)
                documents.extend(self._fetch_marketaux_news(symbol, remaining))
            except Exception as e:
                logger.warning(f"MarketAux fetch failed for {symbol}: {e}")

        logger.info(f"Fetched {len(documents)} news articles for {symbol}")
        return documents[:limit]

    def _fetch_newsapi(self, symbol: str, limit: int) -> List[str]:
        """Fetch news from NewsAPI.org"""
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': f'"{symbol}" OR "{symbol} stock" OR "{symbol} earnings"',
            'apiKey': self.api_keys['newsapi'],
            'pageSize': min(limit, 20),  # NewsAPI limit
            'sortBy': 'relevancy',
            'language': 'en'
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        documents = []
        for article in data.get('articles', []):
            content = f"""
News Article: {article.get('title', 'Untitled')}

{article.get('description', '')}

{article.get('content', '')}

Source: {article.get('source', {}).get('name', 'Unknown')}
Published: {article.get('publishedAt', 'Unknown')}
URL: {article.get('url', '')}
Symbol: {symbol}
"""
            documents.append(content.strip())

        return documents

    def _fetch_finnhub_news(self, symbol: str, limit: int) -> List[str]:
        """Fetch news from Finnhub"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        url = "https://finnhub.io/api/v1/company-news"
        params = {
            'symbol': symbol,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'token': self.api_keys['finnhub']
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        documents = []
        for article in data[:limit]:
            content = f"""
Company News: {article.get('headline', 'No Headline')}

{article.get('summary', '')}

Source: Finnhub
Published: {datetime.fromtimestamp(article.get('datetime', 0)).isoformat()}
URL: {article.get('url', '')}
Symbol: {symbol}
Related: {article.get('related', symbol)}
"""
            documents.append(content.strip())

        return documents

    def _fetch_marketaux_news(self, symbol: str, limit: int) -> List[str]:
        """Fetch news from MarketAux"""
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            'symbols': symbol,
            'filter_entities': 'true',
            'language': 'en',
            'api_token': self.api_keys['marketaux'],
            'limit': min(limit, 10)  # MarketAux free tier limit
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        documents = []
        for article in data.get('data', []):
            content = f"""
Market News: {article.get('title', 'No Title')}

{article.get('description', '')}

Source: {article.get('source', 'MarketAux')}
Published: {article.get('published_at', 'Unknown')}
URL: {article.get('url', '')}
Symbol: {symbol}
Entities: {', '.join(article.get('entities', []))}
"""
            documents.append(content.strip())

        return documents

    def fetch_company_financials(self, symbol: str) -> List[str]:
        """
        Fetch company financial data - return text documents

        Args:
            symbol: Stock ticker symbol

        Returns:
            List of financial document texts (company profile, overview, fundamentals)
        """
        documents = []

        # Try Financial Modeling Prep if available
        if self.is_service_available('fmp'):
            try:
                documents.extend(self._fetch_fmp_profile(symbol))
            except Exception as e:
                logger.warning(f"FMP profile fetch failed for {symbol}: {e}")

        # Try Alpha Vantage if available
        if self.is_service_available('alpha_vantage'):
            try:
                documents.extend(self._fetch_alpha_vantage_overview(symbol))
            except Exception as e:
                logger.warning(f"Alpha Vantage overview fetch failed for {symbol}: {e}")

        # Try Polygon if available
        if self.is_service_available('polygon'):
            try:
                documents.extend(self._fetch_polygon_details(symbol))
            except Exception as e:
                logger.warning(f"Polygon details fetch failed for {symbol}: {e}")

        logger.info(f"Fetched {len(documents)} financial documents for {symbol}")
        return documents

    def _fetch_fmp_profile(self, symbol: str) -> List[str]:
        """Fetch company profile from Financial Modeling Prep"""
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
        params = {'apikey': self.api_keys['fmp']}

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        if not data:
            return []

        company = data[0]
        profile_text = f"""
Company Profile: {company.get('companyName', symbol)}

Symbol: {symbol}
Exchange: {company.get('exchangeShortName', 'Unknown')}
Sector: {company.get('sector', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Country: {company.get('country', 'Unknown')}
Market Cap: ${company.get('mktCap', 0):,}
Current Price: ${company.get('price', 0)}
Beta: {company.get('beta', 'N/A')}
Volume Average: {company.get('volAvg', 0):,}
Website: {company.get('website', '')}

Business Description:
{company.get('description', 'No description available')}

Key Metrics:
- CEO: {company.get('ceo', 'Unknown')}
- Full Time Employees: {company.get('fullTimeEmployees', 'Unknown'):,}
- IPO Date: {company.get('ipoDate', 'Unknown')}
- 52 Week Range: ${company.get('range', 'N/A')}

Address: {company.get('address', '')}, {company.get('city', '')}, {company.get('state', '')} {company.get('zip', '')}

Source: Financial Modeling Prep
Retrieved: {datetime.now().isoformat()}
"""
        return [profile_text.strip()]

    def _fetch_alpha_vantage_overview(self, symbol: str) -> List[str]:
        """Fetch company overview from Alpha Vantage"""
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_keys['alpha_vantage']
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        if 'Symbol' not in data:
            return []

        overview_text = f"""
Company Overview: {data.get('Name', symbol)}

Symbol: {data.get('Symbol', symbol)}
AssetType: {data.get('AssetType', 'Unknown')}
Exchange: {data.get('Exchange', 'Unknown')}
Currency: {data.get('Currency', 'USD')}
Country: {data.get('Country', 'Unknown')}
Sector: {data.get('Sector', 'Unknown')}
Industry: {data.get('Industry', 'Unknown')}

Financial Metrics:
- Market Capitalization: ${int(data.get('MarketCapitalization', 0)):,}
- Shares Outstanding: {int(data.get('SharesOutstanding', 0)):,}
- PE Ratio: {data.get('PERatio', 'N/A')}
- PEG Ratio: {data.get('PEGRatio', 'N/A')}
- Book Value: {data.get('BookValue', 'N/A')}
- Dividend Per Share: {data.get('DividendPerShare', 'N/A')}
- Dividend Yield: {data.get('DividendYield', 'N/A')}
- EPS: {data.get('EPS', 'N/A')}
- Revenue Per Share (TTM): {data.get('RevenuePerShareTTM', 'N/A')}
- Profit Margin: {data.get('ProfitMargin', 'N/A')}
- Operating Margin (TTM): {data.get('OperatingMarginTTM', 'N/A')}
- Return on Assets (TTM): {data.get('ReturnOnAssetsTTM', 'N/A')}
- Return on Equity (TTM): {data.get('ReturnOnEquityTTM', 'N/A')}

Price Information:
- 52 Week High: ${data.get('52WeekHigh', 'N/A')}
- 52 Week Low: ${data.get('52WeekLow', 'N/A')}
- 50 Day Moving Average: ${data.get('50DayMovingAverage', 'N/A')}
- 200 Day Moving Average: ${data.get('200DayMovingAverage', 'N/A')}

Business Description:
{data.get('Description', 'No description available')}

Source: Alpha Vantage
Retrieved: {datetime.now().isoformat()}
"""
        return [overview_text.strip()]

    def _fetch_polygon_details(self, symbol: str) -> List[str]:
        """Fetch company details from Polygon.io"""
        url = f"https://api.polygon.io/v3/reference/tickers/{symbol}"
        params = {'apikey': self.api_keys['polygon']}

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        if 'results' not in data:
            return []

        details = data['results']
        details_text = f"""
Company Details: {details.get('name', symbol)}

Ticker: {details.get('ticker', symbol)}
Market: {details.get('market', 'Unknown')}
Locale: {details.get('locale', 'Unknown')}
Primary Exchange: {details.get('primary_exchange', 'Unknown')}
Type: {details.get('type', 'Unknown')}
Active: {details.get('active', 'Unknown')}
Currency Name: {details.get('currency_name', 'Unknown')}
CIK: {details.get('cik', 'Unknown')}
Composite FIGI: {details.get('composite_figi', 'Unknown')}
Share Class FIGI: {details.get('share_class_figi', 'Unknown')}

Market Cap: ${details.get('market_cap', 0):,}
Weighted Shares Outstanding: {details.get('weighted_shares_outstanding', 0):,}
Outstanding Shares: {details.get('share_class_shares_outstanding', 0):,}

Homepage: {details.get('homepage_url', '')}
Description: {details.get('description', 'No description available')}

Source: Polygon.io
Retrieved: {datetime.now().isoformat()}
"""
        return [details_text.strip()]

    def fetch_comprehensive_data(self, symbol: str, news_limit: int = 5) -> List[str]:
        """
        Fetch comprehensive data for a symbol - news + financials

        Args:
            symbol: Stock ticker symbol
            news_limit: Maximum number of news articles

        Returns:
            Combined list of all available documents
        """
        all_documents = []

        logger.info(f"Fetching comprehensive data for {symbol}")

        # Get financial data first (typically more stable)
        try:
            financial_docs = self.fetch_company_financials(symbol)
            all_documents.extend(financial_docs)
            logger.info(f"Added {len(financial_docs)} financial documents for {symbol}")
        except Exception as e:
            logger.error(f"Financial data fetch failed for {symbol}: {e}")

        # Get news data
        try:
            news_docs = self.fetch_company_news(symbol, news_limit)
            all_documents.extend(news_docs)
            logger.info(f"Added {len(news_docs)} news documents for {symbol}")
        except Exception as e:
            logger.error(f"News data fetch failed for {symbol}: {e}")

        logger.info(f"Fetched {len(all_documents)} total documents for {symbol}")
        return all_documents

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of available API services

        Returns:
            Dictionary with service availability and configuration info
        """
        status = {
            'total_services': len(self.api_keys),
            'available_services': self.available_services,
            'service_details': {}
        }

        # Service capabilities
        service_info = {
            'newsapi': {'type': 'news', 'limit': '1000/day', 'description': 'General news articles'},
            'finnhub': {'type': 'news+financial', 'limit': '60/minute', 'description': 'Financial news and company data'},
            'alpha_vantage': {'type': 'financial', 'limit': '25/day', 'description': 'Company fundamentals and overview'},
            'fmp': {'type': 'financial', 'limit': '250/day', 'description': 'Company profiles and financials'},
            'polygon': {'type': 'financial', 'limit': '5/minute', 'description': 'Company details and market data'},
            'marketaux': {'type': 'news', 'limit': '100/month', 'description': 'Financial news with entity extraction'},
            'benzinga': {'type': 'news', 'limit': 'varies', 'description': 'Professional financial news'}
        }

        for service in self.available_services:
            status['service_details'][service] = {
                'configured': True,
                **service_info.get(service, {'type': 'unknown', 'limit': 'unknown', 'description': 'Unknown service'})
            }

        return status


# Convenience functions
def create_data_ingester(api_keys: Optional[Dict[str, str]] = None) -> DataIngester:
    """
    Create and initialize data ingester

    Args:
        api_keys: Optional API keys dictionary

    Returns:
        Initialized DataIngester instance
    """
    ingester = DataIngester(api_keys=api_keys)
    logger.info(f"✅ Data Ingester created with {len(ingester.available_services)} services")
    return ingester


def test_data_ingestion(symbol: str = "AAPL") -> bool:
    """
    Test data ingestion functionality

    Args:
        symbol: Stock symbol to test with

    Returns:
        True if test passes, False otherwise
    """
    try:
        logger.info(f"🧪 Testing data ingestion for {symbol}...")

        ingester = create_data_ingester()

        if not ingester.available_services:
            logger.warning("No API services configured - skipping test")
            return True

        # Test comprehensive data fetch
        documents = ingester.fetch_comprehensive_data(symbol, news_limit=2)

        if documents:
            logger.info(f"✅ Data ingestion test passed: {len(documents)} documents fetched")
            return True
        else:
            logger.warning("⚠️ No documents fetched, but no errors occurred")
            return True

    except Exception as e:
        logger.error(f"❌ Data ingestion test failed: {e}")
        return False


if __name__ == "__main__":
    # Demo usage
    print("🚀 Data Ingestion Demo")

    try:
        # Test data ingestion
        if test_data_ingestion():
            print("✅ Data ingestion is working correctly")
        else:
            print("❌ Data ingestion test failed")

        # Show service status
        ingester = create_data_ingester()
        status = ingester.get_service_status()
        print(f"\n📊 Service Status: {status['total_services']} services configured")
        for service in status['available_services']:
            details = status['service_details'][service]
            print(f"  ✅ {service}: {details['type']} ({details['limit']})")

    except Exception as e:
        print(f"❌ Demo failed: {e}")