#!/usr/bin/env python3
"""
Earnings Fetcher Module for ICE
Unified interface for fetching latest earnings reports from multiple sources
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import requests
import json

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not installed. Run: pip install yfinance")

try:
    import yahoo_fin.stock_info as si
    YAHOO_FIN_AVAILABLE = True
except ImportError:
    YAHOO_FIN_AVAILABLE = False
    logger.warning("yahoo_fin not installed. Run: pip install yahoo_fin")


class EarningsData:
    """Container for earnings report data"""
    
    def __init__(self, ticker: str, company_name: str = None):
        self.ticker = ticker.upper()
        self.company_name = company_name or ticker
        self.source = None
        self.last_updated = datetime.now()
        self.data = {}
        self.raw_text = ""
        self.error = None
    
    def to_document_text(self) -> str:
        """Convert earnings data to text format suitable for LightRAG"""
        if not self.raw_text and not self.data:
            return f"No earnings data available for {self.ticker}"
        
        if self.raw_text:
            return f"[EARNINGS_REPORT_{self.ticker}] {self.raw_text}"
        
        # Convert structured data to text
        text_parts = [f"EARNINGS REPORT - {self.company_name} ({self.ticker})"]
        text_parts.append(f"Data Source: {self.source}")
        text_parts.append(f"Last Updated: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if 'quarterly_earnings' in self.data:
            text_parts.append("\nQUARTERLY EARNINGS:")
            for quarter, earnings in self.data['quarterly_earnings'].items():
                text_parts.append(f"  {quarter}: {earnings}")
        
        if 'financials' in self.data:
            text_parts.append("\nFINANCIAL HIGHLIGHTS:")
            for key, value in self.data['financials'].items():
                text_parts.append(f"  {key}: {value}")
        
        if 'info' in self.data:
            text_parts.append("\nCOMPANY INFORMATION:")
            info = self.data['info']
            key_metrics = ['sector', 'industry', 'marketCap', 'peRatio', 'revenue', 'grossMargins']
            for key in key_metrics:
                if key in info:
                    text_parts.append(f"  {key}: {info[key]}")
        
        return "\n".join(text_parts)


class EarningsFetcher:
    """Unified earnings data fetcher with multiple data sources"""
    
    def __init__(self):
        self.sources = []
        if YFINANCE_AVAILABLE:
            self.sources.append("yfinance")
        if YAHOO_FIN_AVAILABLE:
            self.sources.append("yahoo_fin")
        
        logger.info(f"EarningsFetcher initialized with sources: {self.sources}")
    
    def validate_ticker(self, ticker: str) -> Optional[str]:
        """Validate and normalize ticker symbol"""
        if not ticker or not isinstance(ticker, str):
            return None
        
        # Clean ticker symbol
        ticker = re.sub(r'[^A-Za-z0-9.-]', '', ticker.strip().upper())
        
        # Basic validation - tickers are typically 1-5 characters
        if len(ticker) < 1 or len(ticker) > 8:
            return None
        
        return ticker
    
    def resolve_company_to_ticker(self, query: str) -> Optional[str]:
        """Attempt to resolve company name to ticker symbol"""
        if not query:
            return None
        
        query = query.strip().lower()
        
        # Common company name to ticker mappings
        company_mappings = {
            'nvidia': 'NVDA', 'nvidia corp': 'NVDA', 'nvidia corporation': 'NVDA',
            'apple': 'AAPL', 'apple inc': 'AAPL', 'apple corporation': 'AAPL',
            'microsoft': 'MSFT', 'microsoft corp': 'MSFT', 'microsoft corporation': 'MSFT',
            'google': 'GOOGL', 'alphabet': 'GOOGL', 'alphabet inc': 'GOOGL',
            'amazon': 'AMZN', 'amazon.com': 'AMZN', 'amazon inc': 'AMZN',
            'meta': 'META', 'facebook': 'META', 'meta platforms': 'META',
            'tesla': 'TSLA', 'tesla inc': 'TSLA', 'tesla motors': 'TSLA',
            'netflix': 'NFLX', 'netflix inc': 'NFLX',
            'disney': 'DIS', 'walt disney': 'DIS', 'the walt disney company': 'DIS',
        }
        
        # Check exact matches first
        if query in company_mappings:
            return company_mappings[query]
        
        # Check partial matches
        for company, ticker in company_mappings.items():
            if company in query or query in company:
                return ticker
        
        # If it looks like it might already be a ticker, validate it
        if len(query) <= 8 and query.replace('.', '').replace('-', '').isalnum():
            return self.validate_ticker(query)
        
        return None
    
    def fetch_yfinance_data(self, ticker: str) -> EarningsData:
        """Fetch earnings data using yfinance"""
        earnings_data = EarningsData(ticker)
        earnings_data.source = "yfinance"
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get company name
            earnings_data.company_name = info.get('longName', info.get('shortName', ticker))
            
            # Get financial data
            financials = {}
            
            # Basic info
            if 'marketCap' in info:
                financials['Market Cap'] = info['marketCap']
            if 'revenue' in info:
                financials['Revenue'] = info['revenue']
            if 'grossMargins' in info:
                financials['Gross Margins'] = f"{info['grossMargins']*100:.1f}%" if info['grossMargins'] else 'N/A'
            if 'peRatio' in info:
                financials['P/E Ratio'] = info['peRatio']
            
            # Try to get financial statements (quarterly earnings deprecated)
            quarterly_earnings = {}
            try:
                # Get income statement for recent quarters
                income_stmt = stock.quarterly_income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    # Get net income from most recent quarters
                    for i, col in enumerate(income_stmt.columns[:4]):  # Last 4 quarters
                        quarter_date = col.strftime('%Y-Q%s') if hasattr(col, 'strftime') else str(col)
                        
                        # Try to get net income
                        net_income = None
                        for index_name in ['Net Income', 'Net Income Common Stockholders', 'Net Income Applicable To Common Shares']:
                            if index_name in income_stmt.index:
                                net_income = income_stmt.loc[index_name, col]
                                break
                        
                        if net_income is not None:
                            # Format large numbers
                            if isinstance(net_income, (int, float)) and abs(net_income) > 1e6:
                                net_income = f"${net_income/1e9:.1f}B" if abs(net_income) > 1e9 else f"${net_income/1e6:.0f}M"
                            quarterly_earnings[quarter_date] = net_income
                        
            except Exception as e:
                logger.debug(f"Could not fetch quarterly financials for {ticker}: {e}")
                
                # Fallback: try to get earnings data from info
                try:
                    if 'earningsQuarterlyGrowth' in info:
                        quarterly_earnings['Recent Quarter Growth'] = f"{info['earningsQuarterlyGrowth']*100:.1f}%" if info['earningsQuarterlyGrowth'] else 'N/A'
                except Exception:
                    pass
            
            # Store data
            earnings_data.data = {
                'info': info,
                'financials': financials,
                'quarterly_earnings': quarterly_earnings
            }
            
            logger.info(f"Successfully fetched yfinance data for {ticker}")
            
        except Exception as e:
            logger.error(f"Failed to fetch yfinance data for {ticker}: {e}")
            earnings_data.error = str(e)
        
        return earnings_data
    
    def fetch_latest_earnings(self, query: str) -> EarningsData:
        """
        Fetch latest earnings data for a company
        
        Args:
            query: Ticker symbol or company name (e.g., "NVDA", "nvidia", "Apple Inc")
        
        Returns:
            EarningsData object with fetched information
        """
        
        # Try to resolve to ticker - first try company name resolution, then validate
        ticker = self.resolve_company_to_ticker(query)
        if not ticker:
            # If company resolution failed, try direct ticker validation
            ticker = self.validate_ticker(query)
        
        if not ticker:
            error_data = EarningsData(query or "UNKNOWN")
            error_data.error = f"Could not resolve '{query}' to a valid ticker symbol"
            return error_data
        
        # Try yfinance first
        if "yfinance" in self.sources:
            try:
                data = self.fetch_yfinance_data(ticker)
                if not data.error:
                    return data
            except Exception as e:
                logger.warning(f"yfinance failed for {ticker}: {e}")
        
        # If all sources fail, return error
        error_data = EarningsData(ticker)
        error_data.error = "All data sources failed to retrieve earnings information"
        return error_data
    
    def is_available(self) -> bool:
        """Check if any data sources are available"""
        return len(self.sources) > 0
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources"""
        return self.sources.copy()


# Global instance for easy access
earnings_fetcher = EarningsFetcher()


def fetch_company_earnings(query: str) -> Dict[str, Any]:
    """
    Convenience function to fetch earnings data
    
    Args:
        query: Company name or ticker symbol
    
    Returns:
        Dict with status, data, and text suitable for LightRAG
    """
    
    if not earnings_fetcher.is_available():
        return {
            "status": "error",
            "message": "No earnings data sources available. Install yfinance: pip install yfinance"
        }
    
    try:
        earnings_data = earnings_fetcher.fetch_latest_earnings(query)
        
        if earnings_data.error:
            return {
                "status": "error",
                "message": earnings_data.error
            }
        
        return {
            "status": "success",
            "ticker": earnings_data.ticker,
            "company_name": earnings_data.company_name,
            "source": earnings_data.source,
            "last_updated": earnings_data.last_updated.isoformat(),
            "document_text": earnings_data.to_document_text(),
            "raw_data": earnings_data.data
        }
    
    except Exception as e:
        logger.error(f"Error fetching earnings for {query}: {e}")
        return {
            "status": "error", 
            "message": f"Failed to fetch earnings data: {str(e)}"
        }


if __name__ == "__main__":
    # Test the earnings fetcher
    print("🧪 Testing Earnings Fetcher")
    print("=" * 40)
    
    test_queries = ["NVDA", "nvidia", "AAPL", "apple", "INVALID_TICKER"]
    
    for query in test_queries:
        print(f"\nTesting: {query}")
        result = fetch_company_earnings(query)
        print(f"Status: {result['status']}")
        
        if result['status'] == 'success':
            print(f"Ticker: {result['ticker']}")
            print(f"Company: {result['company_name']}")
            print(f"Source: {result['source']}")
            print(f"Document preview: {result['document_text'][:200]}...")
        else:
            print(f"Error: {result['message']}")