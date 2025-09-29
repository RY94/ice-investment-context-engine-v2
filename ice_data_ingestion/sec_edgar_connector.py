# ice_data_ingestion/sec_edgar_connector.py
"""
SEC EDGAR API Connector for ICE Investment Context Engine
Provides direct access to SEC EDGAR filing data via official SEC APIs
Handles ticker-to-CIK lookup and filing retrieval with proper rate limiting
Relevant files: free_api_connectors.py, mcp_client_manager.py
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import requests
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class SECFiling:
    """SEC filing data structure"""
    form: str
    filing_date: str
    accession_number: str
    file_number: str
    acceptance_datetime: str
    act: str
    size: int
    is_xbrl: bool
    is_inline_xbrl: bool
    primary_document: Optional[str] = None
    primary_doc_description: Optional[str] = None


@dataclass
class SECCompanyInfo:
    """SEC company information"""
    cik: str
    entity_type: str
    sic: str
    sic_description: str
    insider_transaction_for_owner_exists: bool
    insider_transaction_for_issuer_exists: bool
    name: str
    tickers: List[str]
    exchanges: List[str]
    ein: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    state_of_incorporation: Optional[str] = None
    state_of_incorporation_description: Optional[str] = None


class SECEdgarConnector:
    """Direct SEC EDGAR API connector"""
    
    def __init__(self, user_agent: str = "ICE System (email@example.com)"):
        """Initialize SEC EDGAR connector"""
        self.user_agent = user_agent
        self.base_url = "https://data.sec.gov"
        self.tickers_url = "https://www.sec.gov/files/company_tickers.json"
        
        # Rate limiting: SEC allows 10 requests/second
        self.rate_limit = 0.1  # 100ms between requests
        self.last_request_time = 0
        
        # Cache for ticker-to-CIK mapping
        self._ticker_cache = {}
        self._cache_loaded = False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get proper headers for SEC API requests"""
        return {
            'User-Agent': self.user_agent,
            'Accept-Encoding': 'gzip, deflate',
        }
    
    async def _rate_limit_delay(self) -> None:
        """Ensure we don't exceed SEC rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            delay = self.rate_limit - time_since_last
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def _load_ticker_cache(self) -> bool:
        """Load ticker-to-CIK mapping from SEC"""
        if self._cache_loaded:
            return True
            
        try:
            await self._rate_limit_delay()
            
            response = requests.get(
                self.tickers_url,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                tickers_data = response.json()
                
                # Build ticker-to-CIK mapping
                for entry in tickers_data.values():
                    ticker = entry.get('ticker', '').upper()
                    cik = str(entry.get('cik_str', ''))
                    if ticker and cik:
                        self._ticker_cache[ticker] = cik
                
                self._cache_loaded = True
                logger.info(f"Loaded {len(self._ticker_cache)} ticker-to-CIK mappings")
                return True
            else:
                logger.error(f"Failed to load ticker mappings: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading ticker cache: {e}")
            return False
    
    async def get_cik_by_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK by ticker symbol"""
        if not await self._load_ticker_cache():
            return None
        
        ticker_upper = ticker.upper()
        cik = self._ticker_cache.get(ticker_upper)
        
        if cik:
            # Ensure CIK is 10 digits with leading zeros
            return cik.zfill(10)
        return None
    
    async def get_company_info(self, ticker: str) -> Optional[SECCompanyInfo]:
        """Get company information from SEC EDGAR"""
        cik = await self.get_cik_by_ticker(ticker)
        if not cik:
            logger.warning(f"No CIK found for ticker {ticker}")
            return None
        
        try:
            await self._rate_limit_delay()
            
            url = f"{self.base_url}/submissions/CIK{cik}.json"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return SECCompanyInfo(
                    cik=data.get('cik', cik),
                    entity_type=data.get('entityType', ''),
                    sic=data.get('sic', ''),
                    sic_description=data.get('sicDescription', ''),
                    insider_transaction_for_owner_exists=data.get('insiderTransactionForOwnerExists', False),
                    insider_transaction_for_issuer_exists=data.get('insiderTransactionForIssuerExists', False),
                    name=data.get('name', ''),
                    tickers=data.get('tickers', []),
                    exchanges=data.get('exchanges', []),
                    ein=data.get('ein'),
                    description=data.get('description'),
                    website=data.get('website'),
                    category=data.get('category'),
                    fiscal_year_end=data.get('fiscalYearEnd'),
                    state_of_incorporation=data.get('stateOfIncorporation'),
                    state_of_incorporation_description=data.get('stateOfIncorporationDescription')
                )
            else:
                logger.error(f"Failed to get company info for {ticker}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting company info for {ticker}: {e}")
            return None
    
    async def get_recent_filings(self, ticker: str, limit: int = 10) -> List[SECFiling]:
        """Get recent SEC filings for a company"""
        cik = await self.get_cik_by_ticker(ticker)
        if not cik:
            logger.warning(f"No CIK found for ticker {ticker}")
            return []
        
        try:
            await self._rate_limit_delay()
            
            url = f"{self.base_url}/submissions/CIK{cik}.json"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                filings_data = data.get('filings', {}).get('recent', {})
                
                if not filings_data:
                    return []
                
                # Extract filing information
                forms = filings_data.get('form', [])
                filing_dates = filings_data.get('filingDate', [])
                accession_numbers = filings_data.get('accessionNumber', [])
                file_numbers = filings_data.get('fileNumber', [])
                acceptance_datetimes = filings_data.get('acceptanceDateTime', [])
                acts = filings_data.get('act', [])
                sizes = filings_data.get('size', [])
                is_xbrl = filings_data.get('isXBRL', [])
                is_inline_xbrl = filings_data.get('isInlineXBRL', [])
                primary_documents = filings_data.get('primaryDocument', [])
                primary_doc_descriptions = filings_data.get('primaryDocDescription', [])
                
                filings = []
                for i in range(min(len(forms), limit)):
                    filing = SECFiling(
                        form=forms[i] if i < len(forms) else '',
                        filing_date=filing_dates[i] if i < len(filing_dates) else '',
                        accession_number=accession_numbers[i] if i < len(accession_numbers) else '',
                        file_number=file_numbers[i] if i < len(file_numbers) else '',
                        acceptance_datetime=acceptance_datetimes[i] if i < len(acceptance_datetimes) else '',
                        act=acts[i] if i < len(acts) else '',
                        size=sizes[i] if i < len(sizes) else 0,
                        is_xbrl=is_xbrl[i] if i < len(is_xbrl) else False,
                        is_inline_xbrl=is_inline_xbrl[i] if i < len(is_inline_xbrl) else False,
                        primary_document=primary_documents[i] if i < len(primary_documents) else None,
                        primary_doc_description=primary_doc_descriptions[i] if i < len(primary_doc_descriptions) else None
                    )
                    filings.append(filing)
                
                return filings
            else:
                logger.error(f"Failed to get filings for {ticker}: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting filings for {ticker}: {e}")
            return []
    
    async def search_filings_by_form(self, ticker: str, form_types: List[str], limit: int = 10) -> List[SECFiling]:
        """Get filings filtered by form type"""
        all_filings = await self.get_recent_filings(ticker, limit * 3)  # Get more to filter
        
        # Filter by form types
        filtered_filings = []
        for filing in all_filings:
            if filing.form in form_types and len(filtered_filings) < limit:
                filtered_filings.append(filing)
        
        return filtered_filings


# Global instance for easy access
sec_edgar_connector = SECEdgarConnector()


async def get_company_filings(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """Convenience function to get company SEC filings"""
    try:
        company_info = await sec_edgar_connector.get_company_info(ticker)
        recent_filings = await sec_edgar_connector.get_recent_filings(ticker, limit)
        
        return {
            "success": True,
            "ticker": ticker,
            "company_info": company_info.__dict__ if company_info else None,
            "recent_filings": [filing.__dict__ for filing in recent_filings],
            "filings_count": len(recent_filings),
            "data_source": "SEC EDGAR API",
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in get_company_filings for {ticker}: {e}")
        return {
            "success": False,
            "ticker": ticker,
            "error": str(e),
            "data_source": "SEC EDGAR API",
            "last_updated": datetime.now().isoformat()
        }


async def test_sec_edgar_connection(ticker: str = "AAPL") -> bool:
    """Test SEC EDGAR API connection"""
    try:
        result = await get_company_filings(ticker, 3)
        return result.get("success", False)
    except Exception as e:
        logger.error(f"SEC EDGAR connection test failed: {e}")
        return False