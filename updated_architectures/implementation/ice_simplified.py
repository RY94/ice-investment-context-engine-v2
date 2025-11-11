# Location: /updated_architectures/implementation/ice_simplified.py
# Purpose: ICE Investment Context Engine - Simplified orchestration using production modules
# Why: Week 4 UDMA integration - Enable ICEQueryProcessor with query fallback logic
# Relevant Files: src/ice_core/ice_system_manager.py, src/ice_core/ice_query_processor.py, ice_data_ingestion/secure_config.py

"""
ICE Investment Context Engine - Simplified Architecture with Production Orchestration

Week 4 Integration: ICEQueryProcessor enabled for enhanced graph-based context and query fallbacks
Week 3 Integration: SecureConfig for encrypted API key management and credential rotation
Week 2 Integration: ICESystemManager for health monitoring and graceful degradation
Maintains simple coordination while using robust production modules (34K+ lines)
Architecture: User-Directed Modular Architecture (UDMA) - Option 5

Relevant files:
- ice_data_ingestion/secure_config.py - Encrypted API key management
- src/ice_core/ice_system_manager.py - Production orchestration with health monitoring
- src/ice_core/ice_query_processor.py - Enhanced query processing with fallback logic
- src/ice_lightrag/ice_rag_fixed.py - LightRAG wrapper
- data_ingestion.py - Data fetching from API/MCP/Email/SEC sources
- query_engine.py - Query processing and analysis
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import SecureConfig for encrypted API key management (Week 3 integration)
from ice_data_ingestion.secure_config import get_secure_config

# Import production DataIngester with email pipeline (Phase 2.6.1)
from updated_architectures.implementation.data_ingestion import DataIngester as ProductionDataIngester

# Import ICEConfig with docling toggles
from updated_architectures.implementation.config import ICEConfig

# Import ingestion manifest for deduplication
from src.ice_core.ingestion_manifest import IngestionManifest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ICECore:
    """
    Core ICE engine - Uses ICESystemManager for production orchestration

    Week 2 Integration: ICESystemManager provides:
    - Health monitoring via get_system_status()
    - Graceful degradation if components fail
    - Session management for UI and notebooks
    - Production error handling patterns

    Key principle: Simple coordination, delegate complexity to production modules
    """

    def __init__(self, config: Optional[ICEConfig] = None):
        """Initialize ICE core with production orchestration"""
        self.config = config or ICEConfig()
        self._system_manager = None
        self._initialized = False

        logger.info("ICE Core initializing with ICESystemManager orchestration")

        # Import and initialize ICESystemManager from production modules
        try:
            from src.ice_core.ice_system_manager import ICESystemManager

            # ICESystemManager handles all component initialization with graceful degradation
            self._system_manager = ICESystemManager(working_dir=self.config.working_dir)
            self._initialized = True
            logger.info("✅ ICESystemManager initialized successfully")

            # Note: System status check is lazy-loaded, happens on first use
            # This allows graceful degradation if some components aren't available

        except ImportError as e:
            logger.error(f"Failed to import ICESystemManager: {e}")
            logger.error("Ensure src/ice_core/ is in Python path")
            raise RuntimeError("Cannot initialize ICE without production modules")
        except Exception as e:
            logger.error(f"ICESystemManager initialization failed: {e}")
            # Graceful degradation: still create object but mark as not ready
            self._initialized = False

    def is_ready(self) -> bool:
        """Check if ICE is ready for operations with production health checks"""
        if not self._initialized or not self._system_manager:
            return False

        try:
            # Use production health check from ICESystemManager
            return self._system_manager.is_ready()
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status for monitoring and debugging

        Returns:
            Dict with component statuses, errors, and performance metrics
        """
        if not self._system_manager:
            return {
                "ready": False,
                "error": "System manager not initialized",
                "components": {},
                "metrics": {}
            }

        try:
            return self._system_manager.get_system_status()
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "ready": False,
                "error": str(e),
                "components": {},
                "metrics": {}
            }

    def add_document(self, text: str, doc_type: str = "financial") -> Dict[str, Any]:
        """
        Add document to knowledge base via ICESystemManager

        Args:
            text: Document content (will be passed to LightRAG)
            doc_type: Document type for context (optional metadata)

        Returns:
            Result dictionary from LightRAG processing with error handling
        """
        if not self.is_ready():
            status = self.get_system_status()
            return {
                "status": "error",
                "message": "ICE not ready - check system status",
                "system_status": status
            }

        try:
            # Delegate to ICESystemManager which handles graceful degradation
            result = self._system_manager.add_document(text, doc_type=doc_type)
            logger.info(f"Document added successfully: {len(text)} chars, type: {doc_type}")
            return result
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {"status": "error", "message": str(e)}

    def _extract_document_title(self, doc_content: str, source_type: str) -> str:
        """Extract document title based on source type using pattern matching"""
        import re

        patterns = {
            "Email": r"Subject:\s*(.+)",
            "SEC Filing": r"Form Type:\s*(.+)",
            "News": r"News Article:\s*(.+)",
            "Financial API": r"Company Profile:\s*(.+)"
        }

        pattern = patterns.get(source_type)
        if pattern:
            match = re.search(pattern, doc_content, re.MULTILINE)
            if match:
                return match.group(1).strip()[:70]

        # Fallback: first non-empty line
        for line in doc_content.split('\n')[:5]:
            line = line.strip()
            if line and not line.startswith('[') and not line.startswith('Symbol:'):
                return line[:70]

        return "Untitled"

    def _print_document_progress(self, doc_index: int, total_docs: int, doc_content: str, symbol: str = ""):
        """
        Print visually distinct progress for each document being processed

        Args:
            doc_index: Current document index (1-based)
            total_docs: Total number of documents
            doc_content: Document content string
            symbol: Ticker symbol being processed
        """
        # Extract source type from content
        source_type = "Unknown"
        source_icon = "📄"

        if "[SOURCE_EMAIL:" in doc_content:
            source_type = "Email"
            source_icon = "📧"
        elif "SEC EDGAR Filing" in doc_content or "[SOURCE_SEC" in doc_content:
            source_type = "SEC Filing"
            source_icon = "📑"
        elif "News Article:" in doc_content or "[SOURCE_NEWS" in doc_content:
            source_type = "News"
            source_icon = "📰"
        elif "Company Profile:" in doc_content or "Company Overview:" in doc_content or "Company Details:" in doc_content:
            source_type = "Financial API"
            source_icon = "💹"

        # Extract title using helper method
        title = self._extract_document_title(doc_content, source_type)

        # Visual box formatting
        box_width = 80
        print(f"\n{'┏' + '━' * (box_width - 2) + '┓'}")
        print(f"┃ {source_icon} DOCUMENT {doc_index}/{total_docs}{' ' * (box_width - len(f'DOCUMENT {doc_index}/{total_docs}') - 6)}┃")
        print(f"┃ Source: {source_type:<{box_width - 11}}┃")
        if symbol:
            print(f"┃ Symbol: {symbol:<{box_width - 11}}┃")
        if title:
            print(f"┃ Title: {title:<{box_width - 11}}┃")
        print(f"{'┗' + '━' * (box_width - 2) + '┛'}")

    def add_documents_batch(self, documents: List[Union[str, Dict[str, str]]]) -> Dict[str, Any]:
        """
        Batch document processing via ICESystemManager

        Args:
            documents: List of document strings OR {"content": str, "type": str} dictionaries

        Returns:
            Batch processing results with graceful degradation
        """
        if not self.is_ready():
            status = self.get_system_status()
            return {
                "status": "error",
                "message": "ICE not ready - check system status",
                "system_status": status
            }

        try:
            # Process documents one at a time using ICESystemManager
            # This provides better error handling than batch processing
            results = []
            errors = []
            total_docs = len(documents)  # Cache count before loop to prevent inconsistency

            for i, doc in enumerate(documents):
                try:
                    # Handle both string documents and dict documents
                    if isinstance(doc, str):
                        content = doc
                        doc_type = 'financial'
                        symbol = ''
                        file_path = None  # No file_path for plain strings
                    else:
                        content = doc.get('content', '')
                        doc_type = doc.get('type', 'financial')
                        symbol = doc.get('symbol', '')
                        file_path = doc.get('file_path', None)  # Extract file_path for traceability

                    # Progress indicator: REMOVED to fix duplicate display bug
                    # Progress is now shown at ingestion level (ingest_historical_data)
                    # before calling this batch function, to avoid showing each doc 2-3 times
                    # self._print_document_progress(
                    #     doc_index=i+1,
                    #     total_docs=total_docs,
                    #     doc_content=content,
                    #     symbol=symbol
                    # )

                    result = self._system_manager.add_document(content, doc_type=doc_type, file_path=file_path)

                    if result.get('status') == 'success':
                        results.append({
                            'index': i,
                            'status': 'success',
                            'doc_type': doc_type
                        })
                    else:
                        errors.append({
                            'index': i,
                            'error': result.get('message', 'Unknown error')
                        })

                except Exception as e:
                    errors.append({
                        'index': i,
                        'error': str(e)
                    })

            logger.info(f"Batch processing completed: {len(results)} successful, {len(errors)} failed")

            return {
                'status': 'success' if len(results) > 0 else 'error',
                'successful': len(results),
                'failed': len(errors),
                'total': len(documents),
                'results': results,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {"status": "error", "message": str(e)}

    def query(self, question: str, mode: str = 'hybrid') -> Dict[str, Any]:
        """
        Query the knowledge base via ICESystemManager

        Args:
            question: Investment question to analyze
            mode: LightRAG query mode (naive, local, global, hybrid, mix, kg)

        Returns:
            Query results with answer and metadata, includes graceful degradation
        """
        if not self.is_ready():
            status = self.get_system_status()
            return {
                "status": "error",
                "message": "ICE not ready - check system status",
                "system_status": status
            }

        try:
            # Delegate to ICESystemManager which uses query_ice() method
            # Week 2: ICEQueryProcessor is Week 3+ feature, disable for now
            result = self._system_manager.query_ice(question, mode=mode, use_graph_context=False)
            logger.info(f"Query completed: {len(question)} chars, mode: {mode}")
            return result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            # Return error in consistent format
            return {
                "status": "error",
                "message": str(e),
                "question": question,
                "mode": mode
            }

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get LightRAG storage statistics for notebook monitoring

        Returns:
            Dict with storage component status and sizes
        """
        if not self._system_manager:
            return {"error": "System manager not initialized", "storage_exists": False}

        try:
            # Access LightRAG storage through working directory
            working_dir = Path(self.config.working_dir)

            # Define expected LightRAG storage components
            components = {
                "chunks_vdb": {
                    "exists": (working_dir / "vdb_chunks.json").exists(),
                    "file": "vdb_chunks.json",
                    "description": "Vector database for document chunks",
                    "size_bytes": (working_dir / "vdb_chunks.json").stat().st_size if (working_dir / "vdb_chunks.json").exists() else 0
                },
                "entities_vdb": {
                    "exists": (working_dir / "vdb_entities.json").exists(),
                    "file": "vdb_entities.json",
                    "description": "Vector database for extracted entities",
                    "size_bytes": (working_dir / "vdb_entities.json").stat().st_size if (working_dir / "vdb_entities.json").exists() else 0
                },
                "relationships_vdb": {
                    "exists": (working_dir / "vdb_relationships.json").exists(),
                    "file": "vdb_relationships.json",
                    "description": "Vector database for entity relationships",
                    "size_bytes": (working_dir / "vdb_relationships.json").stat().st_size if (working_dir / "vdb_relationships.json").exists() else 0
                },
                "graph": {
                    "exists": (working_dir / "graph_chunk_entity_relation.graphml").exists(),
                    "file": "graph_chunk_entity_relation.graphml",
                    "description": "NetworkX graph structure",
                    "size_bytes": (working_dir / "graph_chunk_entity_relation.graphml").stat().st_size if (working_dir / "graph_chunk_entity_relation.graphml").exists() else 0
                }
            }

            # Calculate total storage
            total_size = sum(f.stat().st_size for f in working_dir.rglob('*') if f.is_file()) if working_dir.exists() else 0

            return {
                "working_dir": str(working_dir),
                "storage_exists": working_dir.exists(),
                "is_initialized": self._initialized,
                "components": components,
                "total_storage_bytes": total_size
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e), "storage_exists": False}

    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get knowledge graph statistics for monitoring

        Returns:
            Dict with graph readiness and component indicators (file sizes in MB)
        """
        storage_stats = self.get_storage_stats()
        components = storage_stats.get("components", {})

        return {
            "is_ready": self.is_ready(),
            "storage_indicators": {
                "all_components_present": all(c.get("exists", False) for c in components.values()),
                "chunks_file_size": components.get("chunks_vdb", {}).get("size_bytes", 0) / (1024 * 1024),
                "entities_file_size": components.get("entities_vdb", {}).get("size_bytes", 0) / (1024 * 1024),
                "relationships_file_size": components.get("relationships_vdb", {}).get("size_bytes", 0) / (1024 * 1024),
                "graph_file_size": components.get("graph", {}).get("size_bytes", 0) / (1024 * 1024)
            }
        }

    def get_query_modes(self) -> List[str]:
        """
        Get available LightRAG query modes

        Returns:
            List of supported query mode names
        """
        return ['naive', 'local', 'global', 'hybrid', 'mix', 'bypass']

    def build_knowledge_graph_from_scratch(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Build knowledge graph from scratch (initial build mode)

        Args:
            documents: List of document dicts with 'content' and 'type' keys

        Returns:
            Building result with status and metrics
        """
        start_time = datetime.now()

        result = self.add_documents_batch(documents)

        if result.get('status') == 'success':
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                'status': 'success',
                'mode': 'initial',
                'total_documents': result.get('total', len(documents)),
                'metrics': {
                    'building_time': processing_time,
                    'graph_initialized': True
                }
            }
        else:
            return {
                'status': 'error',
                'mode': 'initial',
                'message': result.get('message', 'Building failed'),
                'total_documents': len(documents)
            }

    def add_documents_to_existing_graph(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Add documents to existing graph (incremental update mode)

        Args:
            documents: List of document dicts with 'content' and 'type' keys

        Returns:
            Update result with status and metrics
        """
        start_time = datetime.now()

        result = self.add_documents_batch(documents)

        if result.get('status') == 'success':
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                'status': 'success',
                'mode': 'incremental',
                'total_documents': result.get('total', len(documents)),
                'metrics': {
                    'update_time': processing_time,
                    'existing_graph_preserved': True
                }
            }
        else:
            return {
                'status': 'partial_failure' if result.get('successful', 0) > 0 else 'error',
                'mode': 'incremental',
                'message': result.get('message', 'Update failed'),
                'total_documents': len(documents)
            }


class DataIngester:
    """
    Simple data ingestion - Direct API calls without transformation layers

    Key principle: Fetch data, return text, let LightRAG handle the rest
    No validation pipelines, no entity enhancement, no complex transformations
    """

    def __init__(self, config: Optional[ICEConfig] = None):
        """Initialize data ingester with API configuration"""
        self.config = config or ICEConfig()
        self.available_services = self.config.get_available_services()

        logger.info(f"Data Ingester initialized with {len(self.available_services)} API services")

    def fetch_company_news(self, symbol: str, limit: int = 5) -> List[str]:
        """
        Fetch company news from available APIs - return raw text documents

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of articles

        Returns:
            List of news article texts (no preprocessing)
        """
        documents = []

        # Try NewsAPI if available
        if self.config.is_api_available('newsapi'):
            try:
                import requests
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': symbol,
                    'apiKey': self.config.api_keys['newsapi'],
                    'pageSize': limit,
                    'sortBy': 'relevancy'
                }

                response = requests.get(url, params=params, timeout=self.config.timeout)
                data = response.json()

                for article in data.get('articles', []):
                    content = f"""
{article.get('title', '')}

{article.get('description', '')}

{article.get('content', '')}

Source: {article.get('source', {}).get('name', 'Unknown')}
Published: {article.get('publishedAt', 'Unknown')}
URL: {article.get('url', '')}
"""
                    documents.append(content.strip())

                logger.info(f"Fetched {len(documents)} news articles for {symbol} from NewsAPI")

            except Exception as e:
                logger.warning(f"NewsAPI fetch failed for {symbol}: {e}")

        # Try Finnhub if available and we need more articles
        if self.config.is_api_available('finnhub') and len(documents) < limit:
            try:
                import requests
                from datetime import timedelta

                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)

                url = "https://finnhub.io/api/v1/company-news"
                params = {
                    'symbol': symbol,
                    'from': start_date.strftime('%Y-%m-%d'),
                    'to': end_date.strftime('%Y-%m-%d'),
                    'token': self.config.api_keys['finnhub']
                }

                response = requests.get(url, params=params, timeout=self.config.timeout)
                data = response.json()

                for article in data[:limit - len(documents)]:
                    content = f"""
{article.get('headline', '')}

{article.get('summary', '')}

Source: {article.get('source', 'Finnhub')}
Published: {datetime.fromtimestamp(article.get('datetime', 0)).isoformat()}
URL: {article.get('url', '')}
"""
                    documents.append(content.strip())

                logger.info(f"Fetched {len(data[:limit - len(documents)])} additional articles for {symbol} from Finnhub")

            except Exception as e:
                logger.warning(f"Finnhub fetch failed for {symbol}: {e}")

        return documents[:limit]

    def fetch_company_financials(self, symbol: str) -> List[str]:
        """
        Fetch company financial data - return text documents

        Args:
            symbol: Stock ticker symbol

        Returns:
            List of financial document texts
        """
        documents = []

        # Try Financial Modeling Prep if available
        if self.config.is_api_available('fmp'):
            try:
                import requests

                # Company profile
                profile_url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
                params = {'apikey': self.config.api_keys['fmp']}

                response = requests.get(profile_url, params=params, timeout=self.config.timeout)
                data = response.json()

                if data:
                    company = data[0]
                    profile_text = f"""
Company Profile: {company.get('companyName', symbol)}

Sector: {company.get('sector', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Market Cap: ${company.get('mktCap', 0):,}
Price: ${company.get('price', 0)}
Beta: {company.get('beta', 'N/A')}
Volume Average: {company.get('volAvg', 0):,}
Exchange: {company.get('exchange', 'Unknown')}
Website: {company.get('website', '')}

Description: {company.get('description', '')}

CEO: {company.get('ceo', 'Unknown')}
Employees: {company.get('fullTimeEmployees', 'Unknown')}
Address: {company.get('address', '')}, {company.get('city', '')}, {company.get('state', '')} {company.get('zip', '')}
"""
                    documents.append(profile_text.strip())
                    logger.info(f"Fetched company profile for {symbol} from FMP")

            except Exception as e:
                logger.warning(f"FMP profile fetch failed for {symbol}: {e}")

        # Try Alpha Vantage if available
        if self.config.is_api_available('alpha_vantage'):
            try:
                import requests

                overview_url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': self.config.api_keys['alpha_vantage']
                }

                response = requests.get(overview_url, params=params, timeout=self.config.timeout)
                data = response.json()

                if 'Symbol' in data:
                    overview_text = f"""
Company Overview: {data.get('Name', symbol)}

Symbol: {data.get('Symbol', symbol)}
Exchange: {data.get('Exchange', 'Unknown')}
Currency: {data.get('Currency', 'USD')}
Country: {data.get('Country', 'Unknown')}
Sector: {data.get('Sector', 'Unknown')}
Industry: {data.get('Industry', 'Unknown')}

Market Capitalization: ${int(data.get('MarketCapitalization', 0)):,}
Shares Outstanding: {int(data.get('SharesOutstanding', 0)):,}
PE Ratio: {data.get('PERatio', 'N/A')}
PEG Ratio: {data.get('PEGRatio', 'N/A')}
Book Value: {data.get('BookValue', 'N/A')}
Dividend Per Share: {data.get('DividendPerShare', 'N/A')}
Dividend Yield: {data.get('DividendYield', 'N/A')}
EPS: {data.get('EPS', 'N/A')}
Revenue Per Share: {data.get('RevenuePerShareTTM', 'N/A')}
Profit Margin: {data.get('ProfitMargin', 'N/A')}
Operating Margin: {data.get('OperatingMarginTTM', 'N/A')}
Return on Assets: {data.get('ReturnOnAssetsTTM', 'N/A')}
Return on Equity: {data.get('ReturnOnEquityTTM', 'N/A')}

52 Week High: ${data.get('52WeekHigh', 'N/A')}
52 Week Low: ${data.get('52WeekLow', 'N/A')}
50 Day Moving Average: ${data.get('50DayMovingAverage', 'N/A')}
200 Day Moving Average: ${data.get('200DayMovingAverage', 'N/A')}

Description: {data.get('Description', '')}
"""
                    documents.append(overview_text.strip())
                    logger.info(f"Fetched company overview for {symbol} from Alpha Vantage")

            except Exception as e:
                logger.warning(f"Alpha Vantage overview fetch failed for {symbol}: {e}")

        return documents

    def fetch_comprehensive_data(self, symbol: str) -> List[str]:
        """
        Fetch comprehensive data for a symbol - news + financials

        Args:
            symbol: Stock ticker symbol

        Returns:
            Combined list of all available documents
        """
        all_documents = []

        # Get financial data first
        financial_docs = self.fetch_company_financials(symbol)
        all_documents.extend(financial_docs)

        # Get news data
        news_docs = self.fetch_company_news(symbol)
        all_documents.extend(news_docs)

        logger.info(f"Fetched {len(all_documents)} total documents for {symbol}")
        return all_documents


class QueryEngine:
    """
    Thin wrapper for portfolio analysis queries

    Key principle: Simple query patterns, no complex planning or optimization
    Let LightRAG's built-in modes handle the complexity
    """

    def __init__(self, ice_core: ICECore):
        """Initialize query engine with ICE core"""
        self.ice = ice_core
        logger.info("Query Engine initialized")

    def analyze_portfolio_risks(self, holdings: List[str]) -> Dict[str, Any]:
        """
        Analyze risks for portfolio holdings

        Args:
            holdings: List of ticker symbols

        Returns:
            Dictionary mapping symbols to risk analysis
        """
        results = {}

        for symbol in holdings:
            logger.info(f"Analyzing risks for {symbol}")

            query = f"What are the main business and market risks facing {symbol}? Include supply chain, regulatory, competitive, and financial risks."

            result = self.ice.query(query, mode='hybrid')

            if result.get('status') == 'success':
                results[symbol] = {
                    'status': 'success',
                    'risk_analysis': result.get('answer', ''),
                    'query_mode': 'hybrid'
                }
            else:
                results[symbol] = {
                    'status': 'error',
                    'error': result.get('message', 'Unknown error')
                }

        logger.info(f"Portfolio risk analysis completed for {len(holdings)} holdings")
        return results

    def analyze_portfolio_opportunities(self, holdings: List[str]) -> Dict[str, Any]:
        """
        Analyze opportunities for portfolio holdings

        Args:
            holdings: List of ticker symbols

        Returns:
            Dictionary mapping symbols to opportunity analysis
        """
        results = {}

        for symbol in holdings:
            logger.info(f"Analyzing opportunities for {symbol}")

            query = f"What are the main growth opportunities and market advantages for {symbol}? Include technology trends, market expansion, and competitive positioning."

            result = self.ice.query(query, mode='hybrid')

            if result.get('status') == 'success':
                results[symbol] = {
                    'status': 'success',
                    'opportunity_analysis': result.get('answer', ''),
                    'query_mode': 'hybrid'
                }
            else:
                results[symbol] = {
                    'status': 'error',
                    'error': result.get('message', 'Unknown error')
                }

        logger.info(f"Portfolio opportunity analysis completed for {len(holdings)} holdings")
        return results

    def analyze_market_relationships(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Analyze relationships and dependencies between symbols

        Args:
            symbols: List of ticker symbols to analyze relationships

        Returns:
            Analysis of inter-company relationships and dependencies
        """
        symbols_str = ", ".join(symbols)
        query = f"What are the key business relationships, dependencies, and competitive dynamics between {symbols_str}? How do these companies affect each other?"

        result = self.ice.query(query, mode='global')

        if result.get('status') == 'success':
            return {
                'status': 'success',
                'relationship_analysis': result.get('answer', ''),
                'symbols_analyzed': symbols,
                'query_mode': 'global'
            }
        else:
            return {
                'status': 'error',
                'error': result.get('message', 'Unknown error'),
                'symbols_analyzed': symbols
            }


class ICESimplified:
    """
    Main ICE simplified interface - orchestrates core, ingestion, and query components

    This replaces 15,000 lines of complex orchestration with simple, direct coordination
    """

    def __init__(self, config: Optional[ICEConfig] = None):
        """Initialize ICE simplified system"""
        self.config = config or ICEConfig()

        # Initialize components
        self.core = ICECore(self.config)
        # Use production DataIngester with email pipeline (Phase 2.6.1)
        # Pass config for docling feature flags (USE_DOCLING_SEC, USE_DOCLING_EMAIL, etc.)
        self.ingester = ProductionDataIngester(config=self.config)
        self.query_engine = QueryEngine(self.core)

        # Phase 2: Initialize query router for dual-layer architecture
        # Router decides when to use Signal Store (<1s) vs LightRAG (~12s)
        if self.config.use_signal_store and self.ingester.signal_store:
            from updated_architectures.implementation.query_router import QueryRouter
            self.query_router = QueryRouter(signal_store=self.ingester.signal_store)
            logger.info("✅ Query router initialized for dual-layer architecture")
        else:
            self.query_router = None
            logger.info("Signal Store disabled, using LightRAG only")

        # Initialize ingestion manifest for incremental updates
        manifest_dir = Path(self.config.working_dir) / 'storage'
        self.manifest = IngestionManifest(manifest_dir)
        logger.info(f"✅ Ingestion manifest initialized ({len(self.manifest.manifest['documents'])} documents tracked)")

        logger.info("✅ ICE Simplified system initialized successfully")

        # Log initial system health status
        self._log_system_health()

    def is_ready(self) -> bool:
        """Check if system is ready for operations"""
        return self.core.is_ready()

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status

        Week 2 Integration: Exposes ICESystemManager health monitoring

        Returns:
            Dict with component statuses, errors, and performance metrics
        """
        return self.core.get_system_status()

    def _log_system_health(self) -> None:
        """Log system health status for monitoring"""
        try:
            status = self.get_system_status()
            logger.info(f"System health: ready={status.get('ready', False)}")
            logger.info(f"Components: {status.get('components', {})}")

            if status.get('errors'):
                logger.warning(f"Component errors: {status.get('errors')}")
        except Exception as e:
            logger.warning(f"Failed to log system health: {e}")

    def _aggregate_investment_signals(self, entities: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate investment signals from extracted entity data

        Processes EntityExtractor output to calculate investment intelligence metrics:
        - Email count and ticker coverage
        - BUY/SELL rating distribution
        - Average confidence scores

        Args:
            entities: List of entity dicts from EntityExtractor

        Returns:
            Dict with aggregated investment signal metrics
        """
        if not entities:
            return {
                'email_count': 0,
                'tickers_covered': 0,
                'buy_ratings': 0,
                'sell_ratings': 0,
                'avg_confidence': 0.0
            }

        tickers = set()
        buy_ratings = 0
        sell_ratings = 0
        confidences = []

        for ent in entities:
            # Aggregate tickers (handle both dict format from EntityExtractor and string format)
            ticker_list = ent.get('tickers', [])
            for ticker_obj in ticker_list:
                if isinstance(ticker_obj, dict):
                    # EntityExtractor format: {'ticker': 'NVDA', 'confidence': 0.95}
                    if 'ticker' in ticker_obj:
                        tickers.add(ticker_obj['ticker'])
                elif isinstance(ticker_obj, str):
                    # Simple string format
                    tickers.add(ticker_obj)

            # Count BUY/SELL ratings (handle both dict and string formats)
            ratings = ent.get('ratings', [])
            for rating_obj in ratings:
                if isinstance(rating_obj, dict):
                    # EntityExtractor format: {'rating': 'buy', 'confidence': 0.85}
                    rating_str = str(rating_obj.get('rating', '')).upper()
                elif isinstance(rating_obj, str):
                    rating_str = rating_obj.upper()
                else:
                    rating_str = str(rating_obj).upper()

                if 'BUY' in rating_str:
                    buy_ratings += 1
                if 'SELL' in rating_str:
                    sell_ratings += 1

            # Collect confidence scores
            if ent.get('confidence'):
                confidences.append(ent['confidence'])

        return {
            'email_count': len(entities),
            'tickers_covered': len(tickers),
            'buy_ratings': buy_ratings,
            'sell_ratings': sell_ratings,
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0.0
        }

    def ingest_portfolio_data(self, holdings: List[str], email_limit: int = 71, news_limit: int = 5, sec_limit: int = 3) -> Dict[str, Any]:
        """
        Ingest data for portfolio holdings and add to knowledge base with metrics

        Args:
            holdings: List of ticker symbols
            email_limit: Maximum number of emails to fetch (default: 71 - all samples)
            news_limit: Maximum number of news articles per symbol (default: 5)
            sec_limit: Maximum number of SEC filings per symbol (default: 3)

        Returns:
            Ingestion results summary with detailed metrics
        """
        from datetime import datetime

        start_time = datetime.now()
        results = {
            'successful': [],
            'failed': [],
            'email_documents': 0,        # Portfolio-wide email count
            'ticker_documents': 0,       # Ticker-specific docs count
            'total_documents': 0,
            'documents': [],
            'metrics': {
                'ingestion_time': 0.0,
                'email_processing_time': 0.0,
                'documents_per_symbol': {},
                'data_sources_used': [],
                'processing_time_per_symbol': {}
            }
        }

        # STEP 1: Fetch portfolio-wide emails ONCE (before symbol loop)
        # Rationale: Emails are broker research covering multiple tickers, not ticker-specific
        # "Trust the Graph" strategy - emails fetched unfiltered for relationship discovery
        email_start_time = datetime.now()
        try:
            email_docs = self.ingester.fetch_email_documents(tickers=None, limit=email_limit)
            if email_docs:
                # email_docs now returns List[Dict] with format: {'content': str, 'file_path': 'email:filename.eml', 'type': 'financial'}
                # Extract content and preserve file_path for LightRAG traceability
                email_doc_list = [
                    {
                        'content': doc['content'],  # Extract content from dict
                        'file_path': doc.get('file_path'),  # Pass through file_path for traceability
                        'type': 'email',
                        'symbol': 'PORTFOLIO'
                    }
                    for doc in email_docs
                ]

                email_result = self.core.add_documents_batch(email_doc_list)

                if email_result.get('status') == 'success':
                    results['email_documents'] = len(email_docs)
                    results['total_documents'] += len(email_docs)
                    results['documents'].extend(email_doc_list)
                    email_time = (datetime.now() - email_start_time).total_seconds()
                    results['metrics']['email_processing_time'] = email_time
                    logger.info(f"✅ Successfully ingested {len(email_docs)} portfolio-wide emails in {email_time:.2f}s")
                else:
                    logger.warning(f"⚠️ Email batch processing had issues: {email_result.get('message')}")
        except Exception as e:
            logger.warning(f"⚠️ Email ingestion failed (non-fatal): {e}")

        # STEP 2: Loop through holdings for ticker-specific data (API + SEC)
        for symbol in holdings:
            symbol_start_time = datetime.now()
            logger.info(f"Ingesting ticker-specific data for {symbol}")

            try:
                # Fetch ticker-specific data using individual methods (not fetch_comprehensive_data)
                # This prevents duplicate email fetching
                logger.info(f"💰 {symbol}: Fetching data from APIs...")
                financial_docs = self.ingester.fetch_company_financials(symbol, limit=news_limit)  # Returns List[Dict]
                news_docs = self.ingester.fetch_company_news(symbol, news_limit)  # Returns List[Dict]
                sec_docs = self.ingester.fetch_sec_filings(symbol, limit=sec_limit)  # Returns List[Dict]

                # Build document list with SOURCE markers for post-processing statistics
                # Phase 1: Enhanced SOURCE markers with timestamps (retrieval time)
                retrieval_timestamp = datetime.now().isoformat()

                doc_list = []
                for doc_dict in financial_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                for doc_dict in news_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                for doc_dict in sec_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                if doc_list:
                    # Add ticker-specific documents to knowledge base
                    batch_result = self.core.add_documents_batch(doc_list)

                    if batch_result.get('status') == 'success':
                        results['successful'].append(symbol)
                        results['ticker_documents'] += len(doc_list)
                        results['total_documents'] += len(doc_list)
                        results['documents'].extend(doc_list)
                        results['metrics']['documents_per_symbol'][symbol] = len(doc_list)

                        symbol_time = (datetime.now() - symbol_start_time).total_seconds()
                        results['metrics']['processing_time_per_symbol'][symbol] = symbol_time

                        logger.info(f"✅ {symbol}: {len(doc_list)} documents ingested in {symbol_time:.2f}s")
                    else:
                        results['failed'].append({
                            'symbol': symbol,
                            'error': batch_result.get('message', 'Batch processing failed')
                        })
                        logger.error(f"❌ Batch processing failed for {symbol}")
                else:
                    results['failed'].append({
                        'symbol': symbol,
                        'error': 'No ticker-specific documents fetched'
                    })
                    logger.warning(f"⚠️ No ticker-specific documents fetched for {symbol}")

            except Exception as e:
                results['failed'].append({
                    'symbol': symbol,
                    'error': str(e)
                })
                logger.error(f"❌ Ticker-specific ingestion failed for {symbol}: {e}")

        # Calculate final metrics
        total_time = (datetime.now() - start_time).total_seconds()
        results['metrics']['ingestion_time'] = total_time
        results['metrics']['data_sources_used'] = self.ingester.available_services
        results['metrics']['success_rate'] = len(results['successful']) / len(holdings) if holdings else 0.0
        results['metrics']['avg_documents_per_symbol'] = results['total_documents'] / len(holdings) if holdings else 0.0

        logger.info(f"Portfolio ingestion completed: {len(results['successful'])} successful, {len(results['failed'])} failed in {total_time:.2f}s")
        return results

    def analyze_portfolio(self, holdings: List[str], include_opportunities: bool = True) -> Dict[str, Any]:
        """
        Complete portfolio analysis - risks, opportunities, and relationships

        Args:
            holdings: List of ticker symbols
            include_opportunities: Whether to include opportunity analysis

        Returns:
            Comprehensive portfolio analysis
        """
        analysis = {
            'holdings': holdings,
            'timestamp': datetime.now().isoformat(),
            'risk_analysis': {},
            'opportunity_analysis': {},
            'relationship_analysis': {},
            'summary': {}
        }

        # Analyze risks
        logger.info("Analyzing portfolio risks...")
        analysis['risk_analysis'] = self.query_engine.analyze_portfolio_risks(holdings)

        # Analyze opportunities if requested
        if include_opportunities:
            logger.info("Analyzing portfolio opportunities...")
            analysis['opportunity_analysis'] = self.query_engine.analyze_portfolio_opportunities(holdings)

        # Analyze relationships between holdings
        if len(holdings) > 1:
            logger.info("Analyzing market relationships...")
            analysis['relationship_analysis'] = self.query_engine.analyze_market_relationships(holdings)

        # Generate summary
        successful_risks = len([r for r in analysis['risk_analysis'].values() if r.get('status') == 'success'])
        successful_opps = len([r for r in analysis['opportunity_analysis'].values() if r.get('status') == 'success'])

        analysis['summary'] = {
            'total_holdings': len(holdings),
            'successful_risk_analyses': successful_risks,
            'successful_opportunity_analyses': successful_opps,
            'relationship_analysis_status': analysis['relationship_analysis'].get('status', 'not_performed'),
            'analysis_completion_rate': (successful_risks / len(holdings)) * 100 if holdings else 0
        }

        logger.info(f"Portfolio analysis completed: {successful_risks}/{len(holdings)} risk analyses successful")
        return analysis

    def query_rating(self, ticker: str) -> Dict[str, Any]:
        """
        Query latest analyst rating for a ticker using dual-layer architecture.

        Routes to Signal Store (<1s) if available, otherwise falls back to LightRAG (~12s).

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')

        Returns:
            Dict with rating data:
            {
                'ticker': 'NVDA',
                'rating': 'BUY',
                'firm': 'Goldman Sachs',
                'analyst': 'John Doe',
                'confidence': 0.87,
                'timestamp': '2024-03-15T10:30:00Z',
                'source': 'signal_store' | 'lightrag',
                'latency_ms': 45
            }

        Examples:
            >>> ice.query_rating('NVDA')
            {'ticker': 'NVDA', 'rating': 'BUY', 'source': 'signal_store', 'latency_ms': 45}
        """
        import time
        start_time = time.time()

        ticker = ticker.upper()

        # Try Signal Store first (if enabled)
        if self.query_router and self.ingester.signal_store:
            try:
                rating_data = self.ingester.signal_store.get_latest_rating(ticker)
                latency_ms = int((time.time() - start_time) * 1000)

                if rating_data:
                    rating_data['source'] = 'signal_store'
                    rating_data['latency_ms'] = latency_ms
                    logger.info(f"✅ Signal Store rating query: {ticker} → {rating_data['rating']} ({latency_ms}ms)")
                    return rating_data

                logger.debug(f"No Signal Store data for {ticker}, falling back to LightRAG")

            except Exception as e:
                logger.warning(f"Signal Store query failed: {e}, falling back to LightRAG")

        # Fallback: Query LightRAG for semantic rating extraction
        try:
            query = f"What is the latest analyst rating or recommendation for {ticker}?"
            lightrag_result = self.core.query(query, mode='hybrid')

            latency_ms = int((time.time() - start_time) * 1000)

            # Parse LightRAG response for rating information
            # (This is a simplified parser - real implementation would use LLM extraction)
            rating_info = {
                'ticker': ticker,
                'rating': 'UNKNOWN',  # Would extract from lightrag_result
                'source': 'lightrag',
                'latency_ms': latency_ms,
                'raw_response': lightrag_result
            }

            logger.info(f"LightRAG rating query: {ticker} ({latency_ms}ms)")
            return rating_info

        except Exception as e:
            logger.error(f"Rating query failed for {ticker}: {e}")
            return {
                'ticker': ticker,
                'rating': 'ERROR',
                'error': str(e),
                'source': 'none',
                'latency_ms': int((time.time() - start_time) * 1000)
            }

    def query_metric(
        self,
        ticker: str,
        metric_type: str,
        period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query financial metric for a ticker using dual-layer architecture.

        Routes to Signal Store (<1s) if available, otherwise falls back to LightRAG (~12s).

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            metric_type: Type of financial metric (e.g., 'Operating Margin', 'Revenue', 'EPS')
            period: Optional time period filter (e.g., 'Q2 2024', 'FY2024', 'TTM')

        Returns:
            Dict with metric data:
            {
                'ticker': 'NVDA',
                'metric_type': 'Operating Margin',
                'metric_value': '62.3%',
                'period': 'Q2 2024',
                'confidence': 0.95,
                'source': 'signal_store' | 'lightrag',
                'latency_ms': 35
            }

        Examples:
            >>> ice.query_metric('NVDA', 'Operating Margin')
            {'ticker': 'NVDA', 'metric_type': 'Operating Margin', 'metric_value': '62.3%', ...}

            >>> ice.query_metric('NVDA', 'Revenue', period='Q2 2024')
            {'ticker': 'NVDA', 'metric_type': 'Revenue', 'metric_value': '$26.97B', ...}
        """
        import time
        start_time = time.time()

        ticker = ticker.upper()

        # Try Signal Store first (if enabled)
        if self.query_router and self.ingester.signal_store:
            try:
                metric_data = self.ingester.signal_store.get_metric(
                    ticker=ticker,
                    metric_type=metric_type,
                    period=period
                )
                latency_ms = int((time.time() - start_time) * 1000)

                if metric_data:
                    metric_data['source'] = 'signal_store'
                    metric_data['latency_ms'] = latency_ms
                    logger.info(f"✅ Signal Store metric query: {ticker} {metric_type} → {metric_data['metric_value']} ({latency_ms}ms)")
                    return metric_data

                logger.debug(f"No Signal Store data for {ticker} {metric_type}, falling back to LightRAG")

            except Exception as e:
                logger.warning(f"Signal Store metric query failed: {e}, falling back to LightRAG")

        # Fallback: Query LightRAG for semantic metric extraction
        try:
            period_str = f" for {period}" if period else ""
            query = f"What is the {metric_type} for {ticker}{period_str}?"
            lightrag_result = self.core.query(query, mode='hybrid')

            latency_ms = int((time.time() - start_time) * 1000)

            # Parse LightRAG response for metric information
            # (This is a simplified parser - real implementation would use LLM extraction)
            metric_info = {
                'ticker': ticker,
                'metric_type': metric_type,
                'metric_value': 'UNKNOWN',  # Would extract from lightrag_result
                'period': period,
                'source': 'lightrag',
                'latency_ms': latency_ms,
                'raw_response': lightrag_result
            }

            logger.info(f"LightRAG metric query: {ticker} {metric_type} ({latency_ms}ms)")
            return metric_info

        except Exception as e:
            logger.error(f"Metric query failed for {ticker} {metric_type}: {e}")
            return {
                'ticker': ticker,
                'metric_type': metric_type,
                'metric_value': 'ERROR',
                'error': str(e),
                'source': 'none',
                'latency_ms': int((time.time() - start_time) * 1000)
            }

    def query_with_router(self, query: str, mode: str = 'hybrid') -> Dict[str, Any]:
        """
        Execute query using intelligent routing (Signal Store vs LightRAG).

        Uses QueryRouter to classify query intent and route to optimal layer:
        - Structured queries (What/Which/Show) → Signal Store (<1s)
        - Semantic queries (Why/How/Explain) → LightRAG (~12s)
        - Hybrid queries → Both layers, combined result

        Args:
            query: User query string
            mode: LightRAG query mode if routing to LightRAG ('local', 'global', 'hybrid', 'naive')

        Returns:
            Dict with query result:
            {
                'query': original query,
                'answer': response text,
                'query_type': 'structured_rating' | 'semantic_why' | etc.,
                'source': 'signal_store' | 'lightrag' | 'hybrid',
                'confidence': 0.90,
                'latency_ms': 850
            }

        Examples:
            >>> ice.query_with_router("What's NVDA's latest rating?")
            {'answer': 'BUY', 'source': 'signal_store', 'latency_ms': 45}

            >>> ice.query_with_router("Why did Goldman upgrade NVDA?")
            {'answer': '...reasoning...', 'source': 'lightrag', 'latency_ms': 12000}
        """
        import time
        start_time = time.time()

        # Route query to optimal layer
        if self.query_router:
            from updated_architectures.implementation.query_router import QueryType

            query_type, confidence = self.query_router.route_query(query)
            logger.info(f"Query routed: {query_type.value} (confidence: {confidence:.2f})")

            # Handle structured rating queries
            if query_type == QueryType.STRUCTURED_RATING:
                ticker = self.query_router.extract_ticker(query)
                if ticker:
                    rating_data = self.query_rating(ticker)
                    formatted_answer = self.query_router.format_signal_store_result(rating_data, query)

                    return {
                        'query': query,
                        'answer': formatted_answer,
                        'query_type': query_type.value,
                        'source': 'signal_store',
                        'confidence': confidence,
                        'latency_ms': int((time.time() - start_time) * 1000),
                        'raw_data': rating_data
                    }

            # Handle structured metric queries
            elif query_type == QueryType.STRUCTURED_METRIC:
                ticker = self.query_router.extract_ticker(query)
                metric_type, period = self.query_router.extract_metric_info(query)

                if ticker and metric_type:
                    metric_data = self.query_metric(ticker, metric_type, period)
                    formatted_answer = self.query_router.format_signal_store_result(metric_data, query)

                    return {
                        'query': query,
                        'answer': formatted_answer,
                        'query_type': query_type.value,
                        'source': 'signal_store',
                        'confidence': confidence,
                        'latency_ms': int((time.time() - start_time) * 1000),
                        'raw_data': metric_data
                    }

            # Handle semantic queries (route to LightRAG)
            elif query_type in (QueryType.SEMANTIC_WHY, QueryType.SEMANTIC_HOW, QueryType.SEMANTIC_EXPLAIN):
                lightrag_result = self.core.query(query, mode=mode)

                return {
                    'query': query,
                    'answer': lightrag_result,
                    'query_type': query_type.value,
                    'source': 'lightrag',
                    'confidence': confidence,
                    'latency_ms': int((time.time() - start_time) * 1000)
                }

            # Handle hybrid queries (both layers)
            elif query_type == QueryType.HYBRID:
                # Get structured data from Signal Store (try ratings and metrics)
                ticker = self.query_router.extract_ticker(query)
                signal_store_data = None

                if ticker:
                    # Try rating query first
                    rating_data = self.query_rating(ticker)
                    if rating_data and rating_data.get('rating') != 'UNKNOWN':
                        signal_store_data = rating_data

                    # Also try metric query
                    metric_type, period = self.query_router.extract_metric_info(query)
                    if metric_type:
                        metric_data = self.query_metric(ticker, metric_type, period)
                        if metric_data and metric_data.get('metric_value') != 'UNKNOWN':
                            # If we have both, combine them
                            if signal_store_data:
                                signal_store_data = {
                                    'rating': rating_data,
                                    'metric': metric_data
                                }
                            else:
                                signal_store_data = metric_data

                # Get semantic context from LightRAG
                lightrag_result = self.core.query(query, mode=mode)

                # Combine results
                combined_answer = f"**Structured Data:**\n"
                if signal_store_data:
                    # Handle combined rating + metric response
                    if isinstance(signal_store_data, dict) and 'rating' in signal_store_data and 'metric' in signal_store_data:
                        combined_answer += self.query_router.format_signal_store_result(signal_store_data['rating'], query)
                        combined_answer += "\n\n"
                        combined_answer += self.query_router.format_signal_store_result(signal_store_data['metric'], query)
                    else:
                        combined_answer += self.query_router.format_signal_store_result(signal_store_data, query)
                else:
                    combined_answer += "No structured data found"

                combined_answer += f"\n\n**Semantic Analysis:**\n{lightrag_result}"

                return {
                    'query': query,
                    'answer': combined_answer,
                    'query_type': query_type.value,
                    'source': 'hybrid',
                    'confidence': confidence,
                    'latency_ms': int((time.time() - start_time) * 1000),
                    'signal_store_data': signal_store_data
                }

        # Fallback: No router available, use LightRAG only
        logger.debug("Query router not available, using LightRAG only")
        lightrag_result = self.core.query(query, mode=mode)

        return {
            'query': query,
            'answer': lightrag_result,
            'query_type': 'semantic_explain',
            'source': 'lightrag',
            'confidence': 0.50,
            'latency_ms': int((time.time() - start_time) * 1000)
        }

    def ingest_historical_data(self, holdings: List[str], years: int = 2,
                                email_limit: int = 71,
                                news_limit: int = 2,
                                financial_limit: int = 2,
                                market_limit: int = 1,
                                sec_limit: int = 2,
                                research_limit: int = 0,
                                email_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Ingest historical data for portfolio holdings (building workflow method)

        Args:
            holdings: List of ticker symbols
            years: Number of years of historical data to fetch (default: 2)
            email_limit: Maximum number of emails to fetch (default: 71)
            news_limit: Maximum number of news articles per symbol (default: 2)
            financial_limit: Maximum number of financial fundamental documents per symbol (default: 2)
            market_limit: Maximum number of market data documents per symbol (default: 1)
            sec_limit: Maximum number of SEC filings per symbol (default: 2)
            research_limit: Maximum number of research documents per symbol (default: 0 - on-demand)
            email_files: Optional list of specific .eml filenames to process (e.g., ['email1.eml'])
                        If provided, only these files are processed. If None, all files are processed.

        Returns:
            Historical ingestion results with metrics
        """
        from datetime import datetime, timedelta

        start_time = datetime.now()
        results = {
            'status': 'success',
            'holdings_processed': [],
            'total_documents': 0,
            'time_period': f"{years} years",
            'start_date': (datetime.now() - timedelta(days=years*365)).isoformat(),
            'end_date': datetime.now().isoformat(),
            'failed_holdings': [],
            'metrics': {
                'processing_time': 0.0,
                'documents_per_holding': {},
                'data_sources_used': []
            }
        }

        logger.info(f"Starting historical data ingestion for {len(holdings)} holdings ({years} years)")
        print(f"🚀 Starting ingestion for {len(holdings)} holdings ({years} years)...")

        # Initialize entity aggregation for Phase 2.6.1
        all_entities = []

        # Track cumulative document count for progress display
        cumulative_doc_count = 0

        # PRE-FETCH PHASE: Calculate total documents for accurate progress display (Fix for "Document 12/7" bug)
        logger.info("📊 Pre-fetching documents to calculate totals...")
        print("\n📊 Pre-fetching documents to calculate totals...")
        total_all_docs = 0
        prefetched_data = {'emails': [], 'tickers': {}}

        # Pre-fetch emails
        try:
            print("  ⏳ Fetching emails...")
            email_docs = self.ingester.fetch_email_documents(tickers=None, limit=email_limit, email_files=email_files)
            if email_docs:
                prefetched_data['emails'] = email_docs
                total_all_docs += len(email_docs)
                print(f"     ✓ Found {len(email_docs)} emails")
        except Exception as e:
            logger.warning(f"⚠️ Email pre-fetch failed: {e}")
            print(f"     ⚠️ Email fetch failed: {e}")

        # Pre-fetch ticker documents (6 categories)
        for symbol in holdings:
            try:
                print(f"  ⏳ Fetching {symbol} data...")
                news_docs = self.ingester.fetch_company_news(symbol, news_limit)
                financial_docs = self.ingester.fetch_financial_fundamentals(symbol, financial_limit)
                market_docs = self.ingester.fetch_market_data(symbol, market_limit)
                sec_docs = self.ingester.fetch_sec_filings(symbol, limit=sec_limit)
                research_docs = []  # Research is on-demand, not auto-fetched
                if research_limit > 0:
                    try:
                        research_docs = self.ingester.research_company_deep(symbol, symbol, topics=None, include_competitors=False)[:research_limit]
                    except:
                        pass  # Research failures are non-critical

                prefetched_data['tickers'][symbol] = {
                    'news': news_docs,
                    'financial': financial_docs,
                    'market': market_docs,
                    'sec': sec_docs,
                    'research': research_docs
                }
                ticker_total = len(news_docs) + len(financial_docs) + len(market_docs) + len(sec_docs) + len(research_docs)
                total_all_docs += ticker_total
                print(f"     ✓ Found {ticker_total} documents (news: {len(news_docs)}, financial: {len(financial_docs)}, market: {len(market_docs)}, SEC: {len(sec_docs)}, research: {len(research_docs)})")
            except Exception as e:
                logger.warning(f"⚠️ {symbol} pre-fetch failed: {e}")
                print(f"     ⚠️ {symbol} fetch failed: {e}")
                prefetched_data['tickers'][symbol] = {'news': [], 'financial': [], 'market': [], 'sec': [], 'research': []}

        logger.info(f"📊 Total documents to process: {total_all_docs}")
        print(f"\n📊 Total documents to process: {total_all_docs}")
        print("━" * 50)

        # STEP 1: Process portfolio-wide emails
        try:
            email_docs = prefetched_data['emails']
            if email_docs:
                # Capture entities from emails
                if hasattr(self.ingester, 'last_extracted_entities'):
                    all_entities.extend(self.ingester.last_extracted_entities)

                # email_docs now returns List[Dict] with format: {'content': str, 'file_path': 'email:filename.eml', 'type': 'financial'}
                # Extract content and preserve file_path for LightRAG traceability
                email_doc_list = [
                    {
                        'content': doc['content'],  # Extract content from dict
                        'file_path': doc.get('file_path'),  # Pass through file_path for traceability
                        'type': 'email_historical',
                        'symbol': 'PORTFOLIO',
                        'ingestion_mode': 'historical'
                    }
                    for doc in email_docs
                ]

                # Print progress for emails (using total_all_docs for accurate count)
                for idx, doc_dict in enumerate(email_doc_list, start=1):
                    cumulative_doc_count += 1
                    self.core._print_document_progress(
                        doc_index=cumulative_doc_count,
                        total_docs=total_all_docs,  # Fixed: use total across all sources
                        doc_content=doc_dict['content'],
                        symbol='PORTFOLIO'
                    )

                email_result = self.core.add_documents_batch(email_doc_list)
                if email_result.get('status') == 'success':
                    results['total_documents'] += len(email_docs)
                    logger.info(f"✅ Historical emails ingested: {len(email_docs)} documents")
        except Exception as e:
            logger.warning(f"⚠️ Historical email ingestion failed (non-fatal): {e}")

        # STEP 2: Loop through holdings for ticker-specific historical data (6 categories)
        for symbol in holdings:
            try:
                # Use prefetched ticker-specific data
                logger.info(f"💰 {symbol}: Processing {years} years of historical data...")
                ticker_data = prefetched_data['tickers'].get(symbol, {})
                news_docs = ticker_data.get('news', [])
                financial_docs = ticker_data.get('financial', [])
                market_docs = ticker_data.get('market', [])
                sec_docs = ticker_data.get('sec', [])
                research_docs = ticker_data.get('research', [])

                # Email entities already captured in STEP 1
                # Ticker-specific sources (news/financials/market/SEC/research) don't extract entities
                # So no new entities to capture here

                # Build document list with SOURCE markers (all 5 ticker categories)
                # Phase 1: Enhanced SOURCE markers with timestamps (retrieval time)
                retrieval_timestamp = datetime.now().isoformat()

                doc_list = []

                # Category 2: News
                for doc_dict in news_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                # Category 3: Financial fundamentals
                for doc_dict in financial_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                # Category 4: Market data
                for doc_dict in market_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                # Category 5: SEC filings
                for doc_dict in sec_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                # Category 6: Research (if any)
                for doc_dict in research_docs:
                    if isinstance(doc_dict, dict) and 'source' in doc_dict:
                        content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                        doc_list.append({'content': content_with_marker})

                if doc_list:
                    # Print progress for each document (using total_all_docs for accurate count)
                    for idx, doc_dict in enumerate(doc_list, start=1):
                        cumulative_doc_count += 1
                        self.core._print_document_progress(
                            doc_index=cumulative_doc_count,
                            total_docs=total_all_docs,  # Fixed: use total across all sources
                            doc_content=doc_dict['content'],
                            symbol=symbol
                        )

                    batch_result = self.core.add_documents_batch(doc_list)

                    if batch_result.get('status') == 'success':
                        results['holdings_processed'].append(symbol)
                        results['total_documents'] += len(doc_list)
                        results['metrics']['documents_per_holding'][symbol] = len(doc_list)
                        logger.info(f"✅ {symbol}: {len(doc_list)} historical documents ingested")
                    else:
                        results['failed_holdings'].append({
                            'symbol': symbol,
                            'error': batch_result.get('message', 'Unknown error')
                        })
                else:
                    results['failed_holdings'].append({
                        'symbol': symbol,
                        'error': 'No historical ticker data available'
                    })

            except Exception as e:
                logger.error(f"❌ Error processing historical ticker data for {symbol}: {str(e)}")
                results['failed_holdings'].append({
                    'symbol': symbol,
                    'error': str(e)
                })

        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results['metrics']['processing_time'] = processing_time
        results['metrics']['data_sources_used'] = self.ingester.available_services

        # Aggregate investment signals from Phase 2.6.1 EntityExtractor
        results['metrics']['investment_signals'] = self._aggregate_investment_signals(all_entities)

        # Set status based on success rate
        success_rate = len(results['holdings_processed']) / len(holdings) if holdings else 0
        if success_rate < 0.5:
            results['status'] = 'partial_failure'
        elif len(results['failed_holdings']) > 0:
            results['status'] = 'partial_success'

        logger.info(f"Historical data ingestion completed: {len(results['holdings_processed'])}/{len(holdings)} successful")
        return results

    def ingest_incremental_data(self, holdings: List[str], days: int = 7) -> Dict[str, Any]:
        """
        Ingest incremental/recent data for portfolio holdings (update workflow method)

        Args:
            holdings: List of ticker symbols
            days: Number of recent days to fetch (default: 7)

        Returns:
            Incremental ingestion results with metrics
        """
        from datetime import datetime, timedelta

        start_time = datetime.now()
        results = {
            'status': 'success',
            'holdings_updated': [],
            'total_new_documents': 0,
            'time_period': f"last {days} days",
            'start_date': (datetime.now() - timedelta(days=days)).isoformat(),
            'end_date': datetime.now().isoformat(),
            'failed_holdings': [],
            'metrics': {
                'processing_time': 0.0,
                'new_documents_per_holding': {},
                'update_sources_used': []
            }
        }

        logger.info(f"Starting incremental data ingestion for {len(holdings)} holdings (last {days} days)")

        # STEP 1: Fetch new portfolio-wide emails (if any)
        # For incremental updates, this fetches recent emails (could be filtered by date in future enhancement)
        try:
            email_docs = self.ingester.fetch_email_documents(tickers=None, limit=20)  # Reduced limit for incremental
            if email_docs:
                # email_docs now returns List[Dict] with format: {'content': str, 'file_path': 'email:filename.eml', 'type': 'financial'}
                # Extract content and preserve file_path for LightRAG traceability
                email_doc_list = [
                    {
                        'content': doc['content'],  # Extract content from dict
                        'file_path': doc.get('file_path'),  # Pass through file_path for traceability
                        'type': 'email_incremental',
                        'symbol': 'PORTFOLIO',
                        'ingestion_mode': 'incremental',
                        'update_date': datetime.now().isoformat()
                    }
                    for doc in email_docs
                ]

                email_result = self.core.add_documents_to_existing_graph(email_doc_list)
                if email_result.get('status') == 'success':
                    results['total_new_documents'] += len(email_docs)
                    logger.info(f"✅ Incremental emails added: {len(email_docs)} new documents")
        except Exception as e:
            logger.warning(f"⚠️ Incremental email fetch failed (non-fatal): {e}")

        # STEP 2: Loop through holdings for ticker-specific incremental data
        for symbol in holdings:
            try:
                # Fetch ticker-specific data (not emails, to prevent duplication)
                logger.info(f"💰 {symbol}: Fetching recent data (last {days} days)...")
                financial_docs = self.ingester.fetch_company_financials(symbol, limit=5)  # Returns List[Dict]
                news_docs = self.ingester.fetch_company_news(symbol, limit=5)  # Returns List[Dict]
                sec_docs = self.ingester.fetch_sec_filings(symbol, limit=2)  # Returns List[Dict]

                # Build document list with SOURCE markers
                # Phase 1: Enhanced SOURCE markers with timestamps (retrieval time)
                retrieval_timestamp = datetime.now().isoformat()

                doc_list = []
                for doc_dict in financial_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                for doc_dict in news_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                for doc_dict in sec_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({'content': content_with_marker})

                if doc_list:
                    batch_result = self.core.add_documents_to_existing_graph(doc_list)

                    if batch_result.get('status') == 'success':
                        results['holdings_updated'].append(symbol)
                        results['total_new_documents'] += len(doc_list)
                        results['metrics']['new_documents_per_holding'][symbol] = len(doc_list)
                        logger.info(f"✅ {symbol}: {len(doc_list)} new documents added")
                    else:
                        results['failed_holdings'].append({
                            'symbol': symbol,
                            'error': batch_result.get('message', 'Unknown error')
                        })
                else:
                    # No new data is OK for incremental updates
                    results['holdings_updated'].append(symbol)
                    results['metrics']['new_documents_per_holding'][symbol] = 0
                    logger.info(f"ℹ️ No new ticker data for {symbol} (up to date)")

            except Exception as e:
                logger.error(f"❌ Error processing incremental ticker data for {symbol}: {str(e)}")
                results['failed_holdings'].append({
                    'symbol': symbol,
                    'error': str(e)
                })

        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results['metrics']['processing_time'] = processing_time
        results['metrics']['update_sources_used'] = self.ingester.available_services

        # Status determination for incremental updates (more lenient)
        if len(results['failed_holdings']) == len(holdings):
            results['status'] = 'failure'
        elif len(results['failed_holdings']) > 0:
            results['status'] = 'partial_success'

        logger.info(f"Incremental data ingestion completed: {len(results['holdings_updated'])}/{len(holdings)} updated")
        return results

    def ingest_with_manifest(self, holdings: List[str],
                            email_limit: int = 71,
                            news_limit: int = 2,
                            financial_limit: int = 2,
                            market_limit: int = 1,
                            sec_limit: int = 2,
                            research_limit: int = 0,
                            email_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Intelligent incremental ingestion using manifest to prevent duplicates.

        This method uses the IngestionManifest to:
        1. Track which documents have been ingested
        2. Detect portfolio changes (new tickers added/removed)
        3. Only fetch and process genuinely new documents
        4. Update portfolio relevance scores for existing entities

        Args:
            holdings: Current portfolio holdings
            email_limit: Max emails to process
            news_limit: News articles per ticker
            financial_limit: Financial docs per ticker
            market_limit: Market data per ticker
            sec_limit: SEC filings per ticker
            research_limit: Research docs per ticker
            email_files: Specific email files to process

        Returns:
            Ingestion results with deduplication metrics
        """
        from datetime import datetime, timedelta

        start_time = datetime.now()

        # Calculate portfolio delta
        portfolio_delta = self.manifest.get_portfolio_delta(holdings)

        results = {
            'status': 'success',
            'portfolio_delta': portfolio_delta,
            'new_documents': 0,
            'skipped_duplicates': 0,
            'updated_documents': 0,
            'new_tickers_data': {},
            'metrics': {
                'processing_time': 0.0,
                'manifest_entries': len(self.manifest.manifest['documents']),
                'deduplication_rate': 0.0
            }
        }

        logger.info(f"🔄 Incremental ingestion with manifest")
        logger.info(f"   Portfolio delta: +{portfolio_delta['added']} -{portfolio_delta['removed']}")

        # Track cumulative counts for progress display
        all_new_docs = []
        skipped_count = 0

        # STEP 1: Process emails (check for new ones)
        try:
            logger.info("📧 Checking for new emails...")

            # Fetch available emails
            available_emails = self.ingester.fetch_email_documents(
                tickers=None,  # Universal ingestion
                limit=email_limit,
                email_files=email_files
            )

            # Filter to only genuinely new emails using manifest
            new_emails = []
            for email_doc in available_emails:
                # Generate document ID
                file_path = email_doc.get('file_path', '')
                doc_id = self.manifest.get_document_id('email', file_path.replace('email:', ''))

                # Check if already ingested
                if not self.manifest.is_document_ingested(doc_id):
                    # Also check content hash for duplicates with different names
                    if not self.manifest.is_content_duplicate(email_doc['content']):
                        new_emails.append(email_doc)

                        # Add to manifest
                        self.manifest.add_document(
                            doc_id=doc_id,
                            content=email_doc['content'],
                            metadata={
                                'source_type': 'email',
                                'file_path': file_path,
                                'portfolio_relevance': self._calculate_relevance(email_doc['content'], holdings)
                            }
                        )
                    else:
                        logger.debug(f"Skipping duplicate content: {doc_id}")
                        skipped_count += 1
                else:
                    logger.debug(f"Skipping already ingested: {doc_id}")
                    skipped_count += 1

            # Ingest only new emails
            if new_emails:
                logger.info(f"✅ Found {len(new_emails)} new emails (skipped {skipped_count} duplicates)")

                # Prepare documents for LightRAG
                email_doc_list = [
                    {
                        'content': doc['content'],
                        'file_path': doc.get('file_path'),
                        'type': 'email',
                        'symbol': 'PORTFOLIO',
                        'ingestion_mode': 'incremental_manifest'
                    }
                    for doc in new_emails
                ]

                # Add to existing graph
                email_result = self.core.add_documents_to_existing_graph(email_doc_list)

                if email_result.get('status') == 'success':
                    all_new_docs.extend(email_doc_list)
                    results['new_documents'] += len(new_emails)
            else:
                logger.info(f"ℹ️ No new emails to process ({skipped_count} already in graph)")

        except Exception as e:
            logger.error(f"Email processing failed: {e}")
            results['status'] = 'partial'

        # STEP 2: Process new tickers only (from portfolio delta)
        if portfolio_delta['added']:
            logger.info(f"📊 Fetching data for {len(portfolio_delta['added'])} new tickers: {portfolio_delta['added']}")

            for ticker in portfolio_delta['added']:
                ticker_docs = []

                try:
                    # Fetch all data types for new ticker
                    if news_limit > 0:
                        news_docs = self.ingester.fetch_company_news(ticker, news_limit)
                        for doc in news_docs:
                            doc_id = self.manifest.get_document_id('api_news', f"{ticker}_{len(ticker_docs)}")
                            if not self.manifest.is_document_ingested(doc_id):
                                ticker_docs.append(doc)
                                self.manifest.add_document(doc_id, doc.get('content', str(doc)), {
                                    'source_type': 'api_news',
                                    'ticker': ticker
                                })

                    if financial_limit > 0:
                        financial_docs = self.ingester.fetch_financial_fundamentals(ticker, financial_limit)
                        for doc in financial_docs:
                            doc_id = self.manifest.get_document_id('api_financial', f"{ticker}_{len(ticker_docs)}")
                            if not self.manifest.is_document_ingested(doc_id):
                                ticker_docs.append(doc)
                                self.manifest.add_document(doc_id, doc.get('content', str(doc)), {
                                    'source_type': 'api_financial',
                                    'ticker': ticker
                                })

                    if sec_limit > 0:
                        sec_docs = self.ingester.fetch_sec_filings(ticker, limit=sec_limit)
                        for doc in sec_docs:
                            doc_id = self.manifest.get_document_id('sec', f"{ticker}_{len(ticker_docs)}")
                            if not self.manifest.is_document_ingested(doc_id):
                                ticker_docs.append(doc)
                                self.manifest.add_document(doc_id, doc.get('content', str(doc)), {
                                    'source_type': 'sec',
                                    'ticker': ticker
                                })

                    # Add ticker docs to graph
                    if ticker_docs:
                        ticker_result = self.core.add_documents_to_existing_graph(ticker_docs)
                        if ticker_result.get('status') == 'success':
                            results['new_tickers_data'][ticker] = len(ticker_docs)
                            results['new_documents'] += len(ticker_docs)
                            all_new_docs.extend(ticker_docs)
                            logger.info(f"✅ {ticker}: Added {len(ticker_docs)} documents")

                    # Update API coverage in manifest
                    self.manifest.update_api_coverage(ticker, {
                        'news': min(news_limit, len([d for d in ticker_docs if isinstance(d, str) and 'news' in d.lower()])),
                        'financial': min(financial_limit, len([d for d in ticker_docs if isinstance(d, str) and 'financial' in d.lower()])),
                        'sec': min(sec_limit, len([d for d in ticker_docs if isinstance(d, str) and 'sec' in d.lower()]))
                    })

                except Exception as e:
                    logger.error(f"Failed to fetch data for {ticker}: {e}")
                    results['status'] = 'partial'

        # STEP 3: Update portfolio in manifest
        self.manifest.update_portfolio(holdings)

        # STEP 4: Save manifest
        self.manifest.save()

        # Calculate final metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results['metrics']['processing_time'] = processing_time
        results['skipped_duplicates'] = skipped_count

        # Calculate deduplication rate
        total_checked = results['new_documents'] + skipped_count
        if total_checked > 0:
            results['metrics']['deduplication_rate'] = (skipped_count / total_checked) * 100

        # Log summary
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 INCREMENTAL INGESTION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"✅ New documents: {results['new_documents']}")
        logger.info(f"⏭️ Skipped duplicates: {results['skipped_duplicates']}")
        logger.info(f"📈 Deduplication rate: {results['metrics']['deduplication_rate']:.1f}%")
        logger.info(f"⏱️ Processing time: {processing_time:.1f}s")
        logger.info(f"📁 Manifest entries: {results['metrics']['manifest_entries']}")

        if portfolio_delta['added']:
            logger.info(f"🆕 New tickers processed: {portfolio_delta['added']}")
        if portfolio_delta['removed']:
            logger.info(f"🗑️ Removed from portfolio: {portfolio_delta['removed']}")

        return results

    def _calculate_relevance(self, content: str, holdings: List[str]) -> float:
        """
        Calculate document relevance to portfolio.

        Score 0.0-1.0 based on:
        - Direct ticker mentions (primary)
        - Competitor/supply chain mentions (secondary)
        - Sector relevance (tertiary)
        """
        content_upper = content.upper()

        # Check primary holdings
        primary_count = sum(1 for ticker in holdings if ticker.upper() in content_upper)
        if primary_count > 0:
            return min(1.0, 0.8 + (primary_count * 0.1))  # 0.8-1.0 for primary

        # Check ecosystem (simplified - in production, would use graph traversal)
        ecosystem_keywords = ['semiconductor', 'supply chain', 'competitor', 'customer']
        ecosystem_count = sum(1 for keyword in ecosystem_keywords if keyword.upper() in content_upper)
        if ecosystem_count > 0:
            return min(0.7, 0.4 + (ecosystem_count * 0.1))  # 0.4-0.7 for ecosystem

        # Default low relevance
        return 0.2

    def _format_progress_bar(self, count: int, total: int, width: int = 30) -> str:
        """
        Format visual progress bar for statistics display

        Args:
            count: Number of items in category
            total: Total number of items
            width: Character width of progress bar (default: 30)

        Returns:
            Formatted string with bar, count, and percentage

        Example:
            >>> ice._format_progress_bar(50, 100)
            '███████████████░░░░░░░░░░░░░░░  50 ( 50.0%)'
        """
        if total == 0:
            return '░' * width + '   0 (  0.0%)'

        filled = int(width * count / total)
        bar = '█' * filled + '░' * (width - filled)
        pct = f"{count/total*100:5.1f}%"
        return f"{bar} {count:3d} ({pct})"

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Generate comprehensive 3-tier knowledge graph statistics

        Tier 1: Document source breakdown (email, newsapi, fmp, etc.)
        Tier 2: Graph structure (entities, relationships, connectivity)
        Tier 3: Investment intelligence (signals, ticker coverage)

        Returns:
            Dict with tier1, tier2, tier3 statistics
        """
        import json
        import re
        from pathlib import Path
        from collections import Counter

        stats = {
            'tier1': {},
            'tier2': {},
            'tier3': {}
        }

        storage_path = Path(self.config.working_dir)

        # TIER 1: Document Source Breakdown
        stats['tier1'] = self._get_document_stats(storage_path)

        # TIER 2: Graph Structure Statistics
        stats['tier2'] = self._get_graph_structure_stats(storage_path)

        # TIER 3: Investment Intelligence Metrics
        stats['tier3'] = self._get_investment_intelligence_stats(storage_path)

        # Validate source marker coverage and log recommendations
        diversity = stats['tier1'].get('source_diversity', {})
        coverage = diversity.get('coverage_percentage', 0.0)
        status = diversity.get('status', 'unknown')
        total_docs = stats['tier1'].get('total', 0)
        docs_with_markers = diversity.get('documents_with_markers', 0)

        if coverage < 80.0:
            logger.warning(f"⚠️  SOURCE marker coverage: {coverage:.1f}% ({docs_with_markers}/{total_docs} documents)")
            logger.warning(f"   Only {diversity.get('unique_sources', 0)} unique source(s) detected")
            logger.warning(f"   Recommendation: Set REBUILD_GRAPH=True in ice_building_workflow.ipynb Cell 22")
            logger.warning(f"   This will rebuild the graph with correct SOURCE markers for accurate statistics")
        elif coverage < 100.0:
            logger.info(f"ℹ️  SOURCE marker coverage: {coverage:.1f}% ({docs_with_markers}/{total_docs} documents) - {status}")
        else:
            logger.info(f"✅ SOURCE marker coverage: 100% - All {total_docs} documents properly tagged")

        return stats

    def _get_document_stats(self, storage_path: Path) -> Dict[str, Any]:
        """Parse SOURCE markers from stored documents for Tier 1 statistics"""
        import json
        import re
        from collections import Counter

        doc_status_file = storage_path / 'kv_store_doc_status.json'
        if not doc_status_file.exists():
            return {'total': 0, 'by_source': {}, 'email': 0, 'api_total': 0, 'sec_total': 0}

        docs = json.load(open(doc_status_file))
        source_counts = Counter()

        # Parse SOURCE markers from content
        for doc in docs.values():
            content = doc.get('content_summary', '')

            # Match [SOURCE:NEWSAPI|SYMBOL:NVDA] pattern
            match = re.search(r'\[SOURCE:(\w+)\|', content)
            if match:
                source = match.group(1).lower()
                source_counts[source] += 1
            elif 'SOURCE_EMAIL' in content or '[TICKER:' in content:
                # Email documents use different markup pattern
                source_counts['email'] += 1

        # Calculate totals
        api_sources = {'newsapi', 'finnhub', 'marketaux', 'fmp', 'alpha_vantage', 'polygon', 'benzinga'}
        api_total = sum(source_counts[s] for s in api_sources)
        sec_total = source_counts.get('sec_edgar', 0)
        exa_total = source_counts.get('exa_company', 0) + source_counts.get('exa_competitors', 0)

        # Calculate source diversity metrics
        total_with_markers = sum(source_counts.values())
        total_without_markers = len(docs) - total_with_markers
        unique_sources = len([v for v in source_counts.values() if v > 0])
        coverage_percentage = (total_with_markers / len(docs) * 100) if len(docs) > 0 else 0.0

        # Determine completeness status
        has_email = source_counts.get('email', 0) > 0
        has_api = api_total > 0
        has_sec = sec_total > 0
        expected_sources_present = sum([has_email, has_api, has_sec])

        if expected_sources_present == 3 and coverage_percentage >= 95:
            status = 'complete'
        elif expected_sources_present >= 2 or coverage_percentage >= 50:
            status = 'partial'
        else:
            status = 'incomplete'

        return {
            'total': len(docs),
            'by_source': dict(source_counts),
            'email': source_counts.get('email', 0),
            'api_total': api_total,
            'sec_total': sec_total,
            'exa_total': exa_total,
            **{k: source_counts.get(k, 0) for k in ['newsapi', 'finnhub', 'marketaux', 'benzinga', 'fmp', 'alpha_vantage', 'polygon', 'sec_edgar', 'exa_company', 'exa_competitors']},
            'source_diversity': {
                'unique_sources': unique_sources,
                'expected_sources': 3,  # Email, API, SEC
                'expected_sources_present': expected_sources_present,
                'coverage_percentage': coverage_percentage,
                'documents_with_markers': total_with_markers,
                'documents_without_markers': total_without_markers,
                'status': status
            }
        }

    def _get_graph_structure_stats(self, storage_path: Path) -> Dict[str, Any]:
        """Read VDB files for Tier 2 graph structure statistics"""
        import json

        stats = {
            'total_entities': 0,
            'total_relationships': 0,
            'avg_connections': 0.0
        }

        # Parse entities
        entities_file = storage_path / 'vdb_entities.json'
        if entities_file.exists():
            data = json.load(open(entities_file))
            stats['total_entities'] = len(data.get('data', []))

        # Parse relationships
        rels_file = storage_path / 'vdb_relationships.json'
        if rels_file.exists():
            data = json.load(open(rels_file))
            stats['total_relationships'] = len(data.get('data', []))

        # Calculate connectivity
        if stats['total_entities'] > 0:
            stats['avg_connections'] = stats['total_relationships'] / stats['total_entities']

        return stats

    def _get_investment_intelligence_stats(self, storage_path: Path) -> Dict[str, Any]:
        """Parse entities for Tier 3 investment intelligence metrics"""
        import json

        TICKERS = {'NVDA', 'TSMC', 'AMD', 'ASML', 'INTC', 'QCOM', 'AVGO', 'TXN', 'MU', 'LRCX'}

        stats = {
            'tickers_covered': [],
            'buy_signals': 0,
            'sell_signals': 0,
            'price_targets': 0,
            'risk_mentions': 0
        }

        # Parse entities for investment signals
        entities_file = storage_path / 'vdb_entities.json'
        if not entities_file.exists():
            return stats

        data = json.load(open(entities_file))
        tickers_found = set()

        for entity in data.get('data', []):
            text = f"{entity.get('entity_name', '')} {entity.get('content', '')}".upper()

            # Detect tickers
            for ticker in TICKERS:
                if ticker in text:
                    tickers_found.add(ticker)

            # Detect signals
            if 'BUY' in text or 'RATING:BUY' in text:
                stats['buy_signals'] += 1
            if 'SELL' in text or 'RATING:SELL' in text:
                stats['sell_signals'] += 1
            if 'PRICE TARGET' in text or 'PRICE_TARGET' in text:
                stats['price_targets'] += 1
            if 'RISK' in text:
                stats['risk_mentions'] += 1

        stats['tickers_covered'] = sorted(list(tickers_found))

        return stats


# Session management for Streamlit UI and workflow notebooks
# Singleton pattern ensures consistent state across notebook cells and UI sessions
_ice_system_instance: Optional[ICESimplified] = None

def get_ice_system(config: Optional[ICEConfig] = None) -> ICESimplified:
    """
    Get singleton ICE system instance for session consistency

    Week 2 Integration: Session management for Streamlit UI and workflow notebooks
    - Ensures same ICE instance used across notebook cells
    - Maintains state for Streamlit session_state
    - Prevents re-initialization overhead
    - Thread-safe singleton pattern

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        Singleton ICE system instance

    Usage:
        # In Streamlit:
        ice = get_ice_system()

        # In Jupyter notebooks:
        ice = get_ice_system()  # Same instance across cells

        # Reset if needed:
        reset_ice_system()
        ice = get_ice_system()  # Fresh instance
    """
    global _ice_system_instance

    if _ice_system_instance is None:
        _ice_system_instance = create_ice_system(config)
        logger.info("✅ Created new ICE system singleton instance")

    return _ice_system_instance

def reset_ice_system():
    """
    Reset singleton ICE system instance

    Use this to force reinitialization (e.g., after config changes)
    Week 2 Integration: Supports session reset in UI and notebooks
    """
    global _ice_system_instance

    if _ice_system_instance is not None:
        logger.info("Resetting ICE system singleton instance")
        _ice_system_instance = None

# Convenience function for quick setup
def create_ice_system(config: Optional[ICEConfig] = None) -> ICESimplified:
    """
    Create and initialize ICE simplified system

    Args:
        config: Optional configuration (will use defaults if not provided)

    Returns:
        Initialized ICE system ready for use
    """
    try:
        ice = ICESimplified(config)

        if ice.is_ready():
            logger.info("✅ ICE system created and ready for operations")
            return ice
        else:
            logger.error("❌ ICE system created but not ready - check LightRAG initialization")
            return ice

    except Exception as e:
        logger.error(f"❌ Failed to create ICE system: {e}")
        raise


if __name__ == "__main__":
    # Example usage with Week 2 health monitoring features
    print("🚀 ICE Simplified Architecture Demo - Week 2 Integration")
    print("=" * 60)

    try:
        # Create system
        ice = create_ice_system()

        # NEW: Display system health status
        print("\n🏥 System Health Status:")
        print("-" * 60)
        status = ice.get_system_status()
        print(f"Ready: {status.get('ready', False)}")
        print(f"Components: {status.get('components', {})}")

        if status.get('errors'):
            print(f"Errors: {status.get('errors')}")

        print(f"Metrics: {status.get('metrics', {})}")

        if ice.is_ready():
            print("\n✅ ICE system ready for operations")

            # Example portfolio
            test_holdings = ['NVDA', 'TSMC', 'AMD']

            # Ingest data
            print(f"\n📡 Ingesting data for {test_holdings}...")
            ingestion_result = ice.ingest_portfolio_data(test_holdings)
            print(f"Ingestion: {len(ingestion_result['successful'])} successful, {ingestion_result['total_documents']} documents")

            # Analyze portfolio
            print(f"\n📊 Analyzing portfolio...")
            analysis = ice.analyze_portfolio(test_holdings)
            print(f"Analysis completion rate: {analysis['summary']['analysis_completion_rate']:.1f}%")

            # NEW: Display final system status with metrics
            print("\n🏥 Final System Status:")
            print("-" * 60)
            final_status = ice.get_system_status()
            print(f"Query count: {final_status.get('metrics', {}).get('query_count', 0)}")
            print(f"Last query: {final_status.get('metrics', {}).get('last_query', 'None')}")

        else:
            print("\n❌ ICE system not ready - check configuration")
            print("System status:", ice.get_system_status())

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()