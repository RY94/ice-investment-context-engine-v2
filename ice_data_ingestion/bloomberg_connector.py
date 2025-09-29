# ice_data_ingestion/bloomberg_connector.py
# Bloomberg Terminal API connector for ICE Investment Context Engine
# Fetches fundamental data (operating margins, financial ratios) and market data (price, volume)
# RELEVANT FILES: ice_data_ingestion/mcp_infrastructure.py, src/ice_lightrag/ice_rag.py, UI/ice_ui_v17.py, src/simple_demo.py

import blpapi
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import logging

class BloombergConnector:
    """
    Bloomberg Terminal API connector for fetching fundamental and market data.
    
    Supports:
    - Historical operating margins and financial ratios
    - Real-time and historical price/volume data
    - Bulk data requests for multiple securities
    - Error handling and session management
    """
    
    def __init__(self, host='localhost', port=8194):
        """
        Initialize Bloomberg API connection.
        
        Args:
            host: Bloomberg API host (default: localhost)
            port: Bloomberg API port (default: 8194)
        """
        self.host = host
        self.port = port
        self.session = None
        self.refdata_service = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """
        Establish connection to Bloomberg Terminal.
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Create session options
            session_options = blpapi.SessionOptions()
            session_options.setServerHost(self.host)
            session_options.setServerPort(self.port)
            
            # Create and start session
            self.session = blpapi.Session(session_options)
            
            if not self.session.start():
                self.logger.error("Failed to start Bloomberg session")
                return False
            
            # Open reference data service
            if not self.session.openService("//blp/refdata"):
                self.logger.error("Failed to open reference data service")
                return False
            
            self.refdata_service = self.session.getService("//blp/refdata")
            self.logger.info("Bloomberg API connection established")
            return True
            
        except Exception as e:
            self.logger.error(f"Bloomberg connection error: {e}")
            return False
    
    def disconnect(self):
        """Close Bloomberg API connection."""
        if self.session:
            self.session.stop()
            self.session = None
            self.refdata_service = None
            self.logger.info("Bloomberg API connection closed")
    
    def get_fundamental_data(self, 
                           tickers: Union[str, List[str]], 
                           fields: List[str], 
                           start_date: str = None,
                           end_date: str = None) -> pd.DataFrame:
        """
        Fetch fundamental data for given tickers.
        
        Args:
            tickers: Single ticker or list of tickers (e.g., 'AAPL US Equity')
            fields: Bloomberg fields (e.g., ['OPER_MARGIN', 'ROE', 'DEBT_TO_TOT_CAP'])
            start_date: Start date in YYYYMMDD format (optional for historical data)
            end_date: End date in YYYYMMDD format (optional for historical data)
        
        Returns:
            DataFrame with fundamental data
        """
        if not self.session or not self.refdata_service:
            raise ConnectionError("Bloomberg API not connected. Call connect() first.")
        
        # Ensure tickers is a list
        if isinstance(tickers, str):
            tickers = [tickers]
        
        # Choose request type based on date parameters
        if start_date and end_date:
            return self._get_historical_data(tickers, fields, start_date, end_date)
        else:
            return self._get_reference_data(tickers, fields)
    
    def get_market_data(self, 
                       tickers: Union[str, List[str]], 
                       start_date: str,
                       end_date: str,
                       fields: List[str] = None) -> pd.DataFrame:
        """
        Fetch historical market data (price, volume).
        
        Args:
            tickers: Single ticker or list of tickers
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format  
            fields: Market data fields (default: ['PX_LAST', 'VOLUME'])
        
        Returns:
            DataFrame with market data
        """
        if fields is None:
            fields = ['PX_LAST', 'VOLUME', 'PX_OPEN', 'PX_HIGH', 'PX_LOW']
        
        return self.get_fundamental_data(tickers, fields, start_date, end_date)
    
    def get_operating_margins_history(self, 
                                    tickers: Union[str, List[str]], 
                                    periods: int = 20) -> pd.DataFrame:
        """
        Fetch historical operating margins for specified periods.
        
        Args:
            tickers: Single ticker or list of tickers
            periods: Number of quarters to fetch (default: 20 = 5 years)
        
        Returns:
            DataFrame with operating margin history
        """
        # Calculate date range for specified periods (quarterly data)
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=periods * 90)).strftime('%Y%m%d')
        
        return self.get_fundamental_data(
            tickers, 
            ['OPER_MARGIN'], 
            start_date, 
            end_date
        )
    
    def _get_reference_data(self, tickers: List[str], fields: List[str]) -> pd.DataFrame:
        """
        Internal method to fetch current/latest reference data.
        """
        # Create reference data request
        request = self.refdata_service.createRequest("ReferenceDataRequest")
        
        # Add securities
        securities = request.getElement("securities")
        for ticker in tickers:
            securities.appendValue(ticker)
        
        # Add fields
        request_fields = request.getElement("fields")
        for field in fields:
            request_fields.appendValue(field)
        
        # Send request and process response
        cid = self.session.sendRequest(request)
        return self._process_reference_response(cid)
    
    def _get_historical_data(self, tickers: List[str], fields: List[str], 
                           start_date: str, end_date: str) -> pd.DataFrame:
        """
        Internal method to fetch historical data.
        """
        results = []
        
        # Bloomberg historical data API requires individual requests per security
        for ticker in tickers:
            request = self.refdata_service.createRequest("HistoricalDataRequest")
            request.getElement("securities").appendValue(ticker)
            
            # Add fields
            request_fields = request.getElement("fields")
            for field in fields:
                request_fields.appendValue(field)
            
            # Set date range
            request.set("startDate", start_date)
            request.set("endDate", end_date)
            request.set("periodicityAdjustment", "ACTUAL")
            request.set("periodicitySelection", "QUARTERLY")  # For fundamental data
            
            # Send request
            cid = self.session.sendRequest(request)
            ticker_data = self._process_historical_response(cid, ticker)
            results.append(ticker_data)
        
        # Combine results
        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def _process_reference_response(self, cid) -> pd.DataFrame:
        """Process Bloomberg reference data response."""
        data = []
        
        while True:
            event = self.session.nextEvent(500)
            
            if event.eventType() == blpapi.Event.RESPONSE:
                for msg in event:
                    security_data = msg.getElement("securityData")
                    
                    for i in range(security_data.numValues()):
                        security = security_data.getValue(i)
                        ticker = security.getElement("security").getValue()
                        
                        field_data = security.getElement("fieldData")
                        row = {"ticker": ticker}
                        
                        # Extract field values
                        for j in range(field_data.numElements()):
                            field = field_data.getElement(j)
                            field_name = field.name()
                            
                            try:
                                field_value = field.getValue()
                                row[field_name] = field_value
                            except:
                                row[field_name] = None
                        
                        data.append(row)
                break
        
        return pd.DataFrame(data)
    
    def _process_historical_response(self, cid, ticker: str) -> pd.DataFrame:
        """Process Bloomberg historical data response."""
        data = []
        
        while True:
            event = self.session.nextEvent(500)
            
            if event.eventType() == blpapi.Event.RESPONSE:
                for msg in event:
                    security_data = msg.getElement("securityData")
                    field_data = security_data.getElement("fieldData")
                    
                    for i in range(field_data.numValues()):
                        point = field_data.getValue(i)
                        row = {
                            "ticker": ticker,
                            "date": point.getElement("date").getValue()
                        }
                        
                        # Extract field values
                        for j in range(1, point.numElements()):  # Skip date element
                            field = point.getElement(j)
                            field_name = field.name()
                            
                            try:
                                field_value = field.getValue()
                                row[field_name] = field_value
                            except:
                                row[field_name] = None
                        
                        data.append(row)
                break
        
        return pd.DataFrame(data)
    
    def get_bulk_fundamental_data(self, tickers: List[str], 
                                periods: int = 20) -> Dict[str, pd.DataFrame]:
        """
        Fetch comprehensive fundamental data for multiple tickers.
        
        Args:
            tickers: List of tickers to fetch
            periods: Number of quarters of historical data
        
        Returns:
            Dictionary with ticker as key and DataFrame as value
        """
        # Key fundamental fields for ICE system
        fundamental_fields = [
            'OPER_MARGIN',           # Operating margin
            'NET_INCOME_MARGIN',     # Net income margin  
            'GROSS_MARGIN',          # Gross margin
            'ROE',                   # Return on equity
            'ROA',                   # Return on assets
            'DEBT_TO_TOT_CAP',       # Debt to total capital
            'CURRENT_RATIO',         # Current ratio
            'QUICK_RATIO',           # Quick ratio
            'TOTAL_REV',             # Total revenue
            'OPER_INC',              # Operating income
            'NET_INCOME',            # Net income
            'TOT_ASSETS',            # Total assets
            'TOT_DEBT',              # Total debt
        ]
        
        # Calculate date range
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=periods * 90)).strftime('%Y%m%d')
        
        results = {}
        
        for ticker in tickers:
            try:
                ticker_data = self.get_fundamental_data(
                    ticker, 
                    fundamental_fields, 
                    start_date, 
                    end_date
                )
                results[ticker] = ticker_data
                self.logger.info(f"Fetched fundamental data for {ticker}")
                
            except Exception as e:
                self.logger.error(f"Failed to fetch data for {ticker}: {e}")
                results[ticker] = pd.DataFrame()
        
        return results
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Example usage and testing functions
def test_bloomberg_connection():
    """Test Bloomberg API connection and basic functionality."""
    
    with BloombergConnector() as bbg:
        if not bbg.session:
            print("❌ Failed to connect to Bloomberg Terminal")
            print("Make sure Bloomberg Terminal is running and logged in")
            return False
        
        print("✅ Bloomberg API connection successful")
        
        # Test fundamental data
        try:
            test_tickers = ['AAPL US Equity', 'MSFT US Equity']
            
            # Test operating margins
            margins_data = bbg.get_operating_margins_history(test_tickers, periods=8)
            print(f"✅ Fetched operating margins: {len(margins_data)} records")
            print(margins_data.head())
            
            # Test market data
            market_data = bbg.get_market_data(
                test_tickers,
                start_date='20240101', 
                end_date='20241201'
            )
            print(f"✅ Fetched market data: {len(market_data)} records")
            print(market_data.head())
            
            return True
            
        except Exception as e:
            print(f"❌ Data fetch error: {e}")
            return False


if __name__ == "__main__":
    # Test the Bloomberg connector
    print("Testing Bloomberg API Connector...")
    test_bloomberg_connection()