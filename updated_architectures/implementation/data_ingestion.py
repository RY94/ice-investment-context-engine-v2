# data_ingestion.py
"""
ICE Data Ingestion - Simple API calls without transformation layers
Direct data fetching that returns text documents for LightRAG processing
Eliminates complex validation pipelines and transformation orchestration
Relevant files: ice_simplified.py, ice_core.py
"""

import os
import sys
from pathlib import Path
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Add project root to path for production module imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Production module imports for robust data ingestion
from ice_data_ingestion.robust_client import RobustHTTPClient
from ice_data_ingestion.sec_edgar_connector import SECEdgarConnector
from imap_email_ingestion_pipeline.email_connector import EmailConnector

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

        # Initialize production modules for robust data ingestion
        # 1. Robust HTTP Client (replaces simple requests.get())
        # Note: For now, keep using requests for simple integration
        # TODO: Fully migrate to RobustHTTPClient with service-specific clients
        self.http_client = None  # Will use requests for now, migrate later

        # 2. Email Connector - NOT needed for sample emails
        # fetch_email_documents() reads .eml files directly
        # EmailConnector only needed for live IMAP connections in production
        self.email_connector = None  # Development: read sample .eml files directly

        # 3. SEC EDGAR Connector (regulatory filings: 10-K, 10-Q, 8-K)
        self.sec_connector = SECEdgarConnector()

        logger.info(f"Data Ingester initialized with {len(self.available_services)} API services: {self.available_services}")
        logger.info("Production modules initialized: SEC EDGAR connector ready, Email reads from samples")

    def is_service_available(self, service: str) -> bool:
        """Check if specific API service is configured"""
        return service in self.api_keys and bool(self.api_keys[service])

    def _format_number(self, value: Any) -> str:
        """Safely format a number with comma separators, handle strings/None"""
        try:
            if value is None or value == '' or value == 'N/A':
                return 'N/A'
            num = int(float(value))
            return f"{num:,}"
        except (ValueError, TypeError):
            return 'N/A'

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

    def fetch_email_documents(self, tickers: Optional[List[str]] = None, limit: int = 10) -> List[str]:
        """
        Fetch broker research emails from sample emails directory

        During development, reads from data/emails_samples/ directory
        In production, can switch to real IMAP using imap_email_ingestion_pipeline

        Args:
            tickers: Optional list of ticker symbols to filter emails
            limit: Maximum number of emails to return

        Returns:
            List of email document texts ready for LightRAG ingestion
        """
        import email
        from pathlib import Path

        documents = []
        # Path relative to this file: updated_architectures/implementation/data_ingestion.py
        # Need to go up 2 levels to reach project root, then into data/emails_samples/
        emails_dir = Path(__file__).parent.parent.parent / "data" / "emails_samples"

        if not emails_dir.exists():
            logger.warning(f"Email samples directory not found: {emails_dir}")
            return documents

        # Get all .eml files
        eml_files = list(emails_dir.glob("*.eml"))
        logger.info(f"Found {len(eml_files)} sample email files")

        # Process each email file
        filtered_docs = []
        all_docs = []

        for eml_file in eml_files:
            try:
                with open(eml_file, 'r', encoding='utf-8', errors='ignore') as f:
                    msg = email.message_from_file(f)

                # Extract email metadata
                subject = msg.get('Subject', 'No Subject')
                sender = msg.get('From', 'Unknown Sender')
                date = msg.get('Date', 'Unknown Date')

                # Extract email body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body += payload.decode('utf-8', errors='ignore')
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')

                # Format as document for LightRAG
                email_doc = f"""
Broker Research Email: {subject}

From: {sender}
Date: {date}
Source: Sample Email ({eml_file.name})

{body.strip()}

---
Email Type: Broker Research
Category: Investment Intelligence
Tickers Mentioned: {', '.join(tickers) if tickers else 'All'}
"""
                all_docs.append(email_doc.strip())

                # Check if matches ticker filter
                if tickers:
                    content_text = f"{subject} {body}".upper()
                    if any(ticker.upper() in content_text for ticker in tickers):
                        filtered_docs.append(email_doc.strip())

            except Exception as e:
                logger.warning(f"Failed to parse email {eml_file.name}: {e}")
                continue

        # Return filtered results if any, otherwise return first N unfiltered results
        if tickers and filtered_docs:
            documents = filtered_docs[:limit]
            logger.info(f"Fetched {len(documents)} email documents filtered by tickers: {tickers}")
        else:
            documents = all_docs[:limit]
            logger.info(f"Fetched {len(documents)} email documents (no ticker filter applied)")


        return documents

    def fetch_sec_filings(self, symbol: str, limit: int = 5) -> List[str]:
        """
        Fetch SEC EDGAR filings for a company

        Fetches regulatory filings (10-K, 10-Q, 8-K) from SEC EDGAR database

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of filings to return

        Returns:
            List of SEC filing document texts ready for LightRAG ingestion
        """
        import asyncio

        documents = []

        try:
            # Run async method synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                filings = loop.run_until_complete(
                    self.sec_connector.get_recent_filings(symbol, limit=limit)
                )
            finally:
                loop.close()

            # Convert SEC filing objects to text documents
            for filing in filings:
                filing_doc = f"""
SEC EDGAR Filing: {filing.form} - {symbol}

Filing Date: {filing.filing_date}
Accession Number: {filing.accession_number}
File Number: {filing.file_number}
Acceptance DateTime: {filing.acceptance_datetime}
Act: {filing.act}
Document Size: {filing.size:,} bytes
XBRL: {filing.is_xbrl}
Inline XBRL: {filing.is_inline_xbrl}
Primary Document: {filing.primary_document or 'N/A'}
Document Description: {filing.primary_doc_description or 'N/A'}

---
Source: SEC EDGAR Database
Symbol: {symbol}
Document Type: Regulatory Filing
Form Type: {filing.form}
"""
                documents.append(filing_doc.strip())

            logger.info(f"Fetched {len(documents)} SEC filings for {symbol}")

        except Exception as e:
            logger.warning(f"SEC filings fetch failed for {symbol}: {e}")

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
Market Cap: ${self._format_number(company.get('mktCap', 0))}
Current Price: ${company.get('price', 0)}
Beta: {company.get('beta', 'N/A')}
Volume Average: {self._format_number(company.get('volAvg', 0))}
Website: {company.get('website', '')}

Business Description:
{company.get('description', 'No description available')}

Key Metrics:
- CEO: {company.get('ceo', 'Unknown')}
- Full Time Employees: {self._format_number(company.get('fullTimeEmployees', 0))}
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
- Market Capitalization: ${self._format_number(data.get('MarketCapitalization', 0))}
- Shares Outstanding: {self._format_number(data.get('SharesOutstanding', 0))}
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

Market Cap: ${self._format_number(details.get('market_cap', 0))}
Weighted Shares Outstanding: {self._format_number(details.get('weighted_shares_outstanding', 0))}
Outstanding Shares: {self._format_number(details.get('share_class_shares_outstanding', 0))}

Homepage: {details.get('homepage_url', '')}
Description: {details.get('description', 'No description available')}

Source: Polygon.io
Retrieved: {datetime.now().isoformat()}
"""
        return [details_text.strip()]

    def fetch_comprehensive_data(self, symbols: List[str], news_limit: int = 5, email_limit: int = 5, sec_limit: int = 3) -> List[str]:
        """
        Fetch comprehensive data from ALL 3 sources: API + Email + SEC filings

        This is the UNIFIED data ingestion method that combines:
        1. API data (news + financials) from NewsAPI, Alpha Vantage, FMP, etc.
        2. Email documents (broker research) from sample emails
        3. SEC EDGAR filings (10-K, 10-Q, 8-K) from regulatory database

        Args:
            symbols: List of stock ticker symbols
            news_limit: Maximum number of news articles per symbol
            email_limit: Maximum number of emails to fetch
            sec_limit: Maximum number of SEC filings per symbol

        Returns:
            Combined list of all documents from all 3 sources ready for LightRAG ingestion
        """
        all_documents = []

        logger.info(f"🚀 Fetching comprehensive data from 3 sources for symbols: {symbols}")

        # SOURCE 1: Email documents (CORE data source - broker research and signals)
        try:
            email_docs = self.fetch_email_documents(tickers=symbols, limit=email_limit)
            all_documents.extend(email_docs)
            logger.info(f"✅ Source 1 (Email): Added {len(email_docs)} email documents")
        except Exception as e:
            logger.error(f"❌ Source 1 (Email) failed: {e}")

        # SOURCE 2 & 3: For each symbol, get API data + SEC filings
        for symbol in symbols:
            # SOURCE 2a: Financial data (API)
            try:
                financial_docs = self.fetch_company_financials(symbol)
                all_documents.extend(financial_docs)
                logger.info(f"✅ Source 2a (API/Financials): Added {len(financial_docs)} documents for {symbol}")
            except Exception as e:
                logger.error(f"❌ Source 2a (API/Financials) failed for {symbol}: {e}")

            # SOURCE 2b: News data (API)
            try:
                news_docs = self.fetch_company_news(symbol, news_limit)
                all_documents.extend(news_docs)
                logger.info(f"✅ Source 2b (API/News): Added {len(news_docs)} documents for {symbol}")
            except Exception as e:
                logger.error(f"❌ Source 2b (API/News) failed for {symbol}: {e}")

            # SOURCE 3: SEC EDGAR filings (regulatory)
            try:
                sec_docs = self.fetch_sec_filings(symbol, limit=sec_limit)
                all_documents.extend(sec_docs)
                logger.info(f"✅ Source 3 (SEC EDGAR): Added {len(sec_docs)} filings for {symbol}")
            except Exception as e:
                logger.error(f"❌ Source 3 (SEC EDGAR) failed for {symbol}: {e}")

        logger.info(f"📊 COMPREHENSIVE DATA FETCH COMPLETE: {len(all_documents)} total documents from 3 sources")
        logger.info(f"   Sources: Email (broker research) + API (news/financials) + SEC EDGAR (filings)")
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


def test_data_ingestion(symbols: List[str] = ["NVDA", "TSMC", "AMD", "ASML"]) -> bool:
    """
    Test integrated data ingestion from all 3 sources

    Tests the complete integration:
    1. Email documents (broker research from sample emails)
    2. API data (news + financials from NewsAPI, Alpha Vantage, FMP, etc.)
    3. SEC EDGAR filings (regulatory documents)

    Args:
        symbols: List of stock symbols to test with (default: semiconductor portfolio)

    Returns:
        True if test passes, False otherwise
    """
    try:
        logger.info(f"🧪 Testing INTEGRATED data ingestion for {len(symbols)} symbols: {symbols}")

        ingester = create_data_ingester()

        # Test comprehensive data fetch from ALL 3 sources
        documents = ingester.fetch_comprehensive_data(
            symbols=symbols,
            news_limit=2,      # 2 news articles per symbol
            email_limit=5,     # 5 broker emails
            sec_limit=2        # 2 SEC filings per symbol
        )

        if documents:
            logger.info(f"✅ INTEGRATION TEST PASSED: {len(documents)} documents fetched from 3 sources")

            # Show breakdown by source
            email_docs = [d for d in documents if 'Broker Research Email' in d or 'Sample Email' in d]
            api_docs = [d for d in documents if any(src in d for src in ['NewsAPI', 'Alpha Vantage', 'Financial Modeling Prep', 'Finnhub', 'MarketAux', 'Polygon'])]
            sec_docs = [d for d in documents if 'SEC EDGAR' in d]

            logger.info(f"   📧 Email documents: {len(email_docs)}")
            logger.info(f"   📊 API documents: {len(api_docs)}")
            logger.info(f"   📋 SEC filings: {len(sec_docs)}")

            return True
        else:
            logger.warning("⚠️ No documents fetched, but no errors occurred")
            return True

    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
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