# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/__init__.py
# ICE Data Ingestion module initialization
# Provides centralized data ingestion capabilities for financial news, market data, and sentiment analysis
# RELEVANT FILES: news_apis.py, alpha_vantage_client.py, fmp_client.py, marketaux_client.py

"""
ICE Data Ingestion Module

This module provides comprehensive data ingestion capabilities for the Investment Context Engine (ICE).
It supports multiple financial data sources including news APIs, market data providers, and sentiment analysis services.

Key Features:
- Multi-source news aggregation
- Sentiment analysis integration
- Rate limiting and caching
- Graph-ready data processing
- Source attribution and traceability

Supported APIs:
- Alpha Vantage (primary recommendation - 500 req/day)
- Financial Modeling Prep (FMP)
- MarketAux
- Polygon.io
- Finnhub

Usage:
    from ice_data_ingestion import NewsAPIManager, AlphaVantageClient
    
    manager = NewsAPIManager()
    news_data = manager.get_financial_news("NVDA", limit=10)
"""

from .news_apis import NewsAPIClient, NewsAPIManager
from .news_processor import NewsProcessor
from .mcp_data_manager import DataType, FinancialDataQuery, mcp_data_manager
from .mcp_infrastructure import mcp_infrastructure
from .mcp_client_manager import get_mcp_data
from .ice_integration import ICEDataIntegrationManager
from .sec_edgar_connector import sec_edgar_connector
from .financial_news_connectors import get_aggregated_news

# Create integration manager instance for easy access
ice_integration_manager = ICEDataIntegrationManager()

__version__ = "0.1.0"
__all__ = [
    "NewsAPIClient", 
    "NewsAPIManager", 
    "NewsProcessor",
    "DataType",
    "FinancialDataQuery", 
    "mcp_data_manager",
    "mcp_infrastructure",
    "get_mcp_data",
    "ice_integration_manager",
    "sec_edgar_connector",
    "get_aggregated_news"
]