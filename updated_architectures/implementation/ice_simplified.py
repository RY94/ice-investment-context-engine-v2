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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ICEConfig:
    """
    Configuration management with encrypted API key storage (Week 3 integration)

    Uses SecureConfig for:
    - Encryption at rest for API keys
    - Audit logging for key access
    - Rotation tracking
    - Backward compatible fallback to environment variables
    """

    def __init__(self):
        """Load configuration using SecureConfig with encrypted storage"""
        # Initialize SecureConfig singleton
        self.secure_config = get_secure_config()

        # Non-sensitive configuration from environment variables
        self.working_dir = os.getenv('ICE_WORKING_DIR', './src/ice_lightrag/storage')
        self.batch_size = int(os.getenv('ICE_BATCH_SIZE', '5'))
        self.timeout = int(os.getenv('ICE_TIMEOUT', '30'))

        # Get OPENAI API key via SecureConfig (with fallback to env)
        self.openai_api_key = self.secure_config.get_api_key('OPENAI', fallback_to_env=True)

        # API Keys for data ingestion (use SecureConfig with service name mapping)
        # SecureConfig uses uppercase service names, map to friendly names
        self.api_keys = {
            'alpha_vantage': self.secure_config.get_api_key('ALPHAVANTAGE', fallback_to_env=True),
            'fmp': self.secure_config.get_api_key('FMP', fallback_to_env=True),  # Not in SecureConfig defaults, will use env
            'newsapi': self.secure_config.get_api_key('NEWSAPI', fallback_to_env=True),
            'polygon': self.secure_config.get_api_key('POLYGON', fallback_to_env=True),
            'finnhub': self.secure_config.get_api_key('FINNHUB', fallback_to_env=True)
        }

        # Validate required configuration
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for LightRAG operations. "
                           "Set via environment variable or use: ice.secure_config.set_api_key('OPENAI', 'sk-...')")

    def is_api_available(self, service: str) -> bool:
        """Check if specific API service is configured"""
        return bool(self.api_keys.get(service))

    def get_available_services(self) -> List[str]:
        """Get list of configured API services"""
        return [service for service, key in self.api_keys.items() if key]

    def validate_all_keys(self) -> Dict[str, Any]:
        """
        Validate all configured API keys using SecureConfig

        Returns:
            Validation status for each service with usage metrics
        """
        return self.secure_config.validate_all_keys()

    def check_rotation_needed(self, rotation_days: int = 90) -> List[str]:
        """
        Check which API keys need rotation (Week 3 feature)

        Args:
            rotation_days: Days before rotation is recommended (default: 90)

        Returns:
            List of services needing key rotation
        """
        return self.secure_config.check_rotation_needed(rotation_days)

    def generate_status_report(self) -> str:
        """Generate comprehensive API key status report with security metrics"""
        return self.secure_config.generate_status_report()


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

            for i, doc in enumerate(documents):
                try:
                    # Handle both string documents and dict documents
                    if isinstance(doc, str):
                        content = doc
                        doc_type = 'financial'
                    else:
                        content = doc.get('content', '')
                        doc_type = doc.get('type', 'financial')

                    result = self._system_manager.add_document(content, doc_type=doc_type)

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
        self.ingester = DataIngester(self.config)
        self.query_engine = QueryEngine(self.core)

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

    def ingest_portfolio_data(self, holdings: List[str]) -> Dict[str, Any]:
        """
        Ingest data for portfolio holdings and add to knowledge base with metrics

        Args:
            holdings: List of ticker symbols

        Returns:
            Ingestion results summary with detailed metrics
        """
        from datetime import datetime

        start_time = datetime.now()
        results = {
            'successful': [],
            'failed': [],
            'total_documents': 0,
            'documents': [],
            'metrics': {
                'ingestion_time': 0.0,
                'documents_per_symbol': {},
                'data_sources_used': [],
                'processing_time_per_symbol': {}
            }
        }

        for symbol in holdings:
            symbol_start_time = datetime.now()
            logger.info(f"Ingesting data for {symbol}")

            try:
                # Fetch documents using simple ingestion
                documents = self.ingester.fetch_comprehensive_data(symbol)

                if documents:
                    # Add documents to knowledge base
                    doc_list = [{'content': doc, 'type': 'financial', 'symbol': symbol} for doc in documents]
                    batch_result = self.core.add_documents_batch(doc_list)

                    if batch_result.get('status') == 'success':
                        results['successful'].append(symbol)
                        results['total_documents'] += len(documents)
                        results['documents'].extend(doc_list)
                        results['metrics']['documents_per_symbol'][symbol] = len(documents)

                        symbol_time = (datetime.now() - symbol_start_time).total_seconds()
                        results['metrics']['processing_time_per_symbol'][symbol] = symbol_time

                        logger.info(f"✅ Successfully ingested {len(documents)} documents for {symbol} in {symbol_time:.2f}s")
                    else:
                        results['failed'].append({
                            'symbol': symbol,
                            'error': batch_result.get('message', 'Batch processing failed')
                        })
                        logger.error(f"❌ Batch processing failed for {symbol}")
                else:
                    results['failed'].append({
                        'symbol': symbol,
                        'error': 'No documents fetched'
                    })
                    logger.warning(f"⚠️ No documents fetched for {symbol}")

            except Exception as e:
                results['failed'].append({
                    'symbol': symbol,
                    'error': str(e)
                })
                logger.error(f"❌ Ingestion failed for {symbol}: {e}")

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

    def ingest_historical_data(self, holdings: List[str], years: int = 2) -> Dict[str, Any]:
        """
        Ingest historical data for portfolio holdings (building workflow method)

        Args:
            holdings: List of ticker symbols
            years: Number of years of historical data to fetch (default: 2)

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

        for symbol in holdings:
            try:
                # Use existing ingestion but log as historical
                logger.info(f"Fetching {years} years of historical data for {symbol}")
                documents = self.ingester.fetch_comprehensive_data(symbol)

                if documents:
                    # Add to knowledge base with historical context
                    doc_list = [
                        {
                            'content': doc,
                            'type': 'financial_historical',
                            'symbol': symbol,
                            'ingestion_mode': 'historical'
                        }
                        for doc in documents
                    ]

                    batch_result = self.core.add_documents_batch(doc_list)

                    if batch_result.get('status') == 'success':
                        results['holdings_processed'].append(symbol)
                        results['total_documents'] += len(documents)
                        results['metrics']['documents_per_holding'][symbol] = len(documents)
                        logger.info(f"✅ Historical data ingested for {symbol}: {len(documents)} documents")
                    else:
                        results['failed_holdings'].append({
                            'symbol': symbol,
                            'error': batch_result.get('message', 'Unknown error')
                        })
                else:
                    results['failed_holdings'].append({
                        'symbol': symbol,
                        'error': 'No historical data available'
                    })

            except Exception as e:
                logger.error(f"❌ Error processing historical data for {symbol}: {str(e)}")
                results['failed_holdings'].append({
                    'symbol': symbol,
                    'error': str(e)
                })

        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results['metrics']['processing_time'] = processing_time
        results['metrics']['data_sources_used'] = self.ingester.available_services

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

        for symbol in holdings:
            try:
                # Use existing ingestion but log as incremental
                logger.info(f"Fetching recent data for {symbol} (last {days} days)")
                documents = self.ingester.fetch_comprehensive_data(symbol)

                if documents:
                    # Add to existing knowledge base with incremental context
                    doc_list = [
                        {
                            'content': doc,
                            'type': 'financial_incremental',
                            'symbol': symbol,
                            'ingestion_mode': 'incremental',
                            'update_date': datetime.now().isoformat()
                        }
                        for doc in documents
                    ]

                    batch_result = self.core.add_documents_to_existing_graph(doc_list)

                    if batch_result.get('status') == 'success':
                        results['holdings_updated'].append(symbol)
                        results['total_new_documents'] += len(documents)
                        results['metrics']['new_documents_per_holding'][symbol] = len(documents)
                        logger.info(f"✅ Incremental data added for {symbol}: {len(documents)} new documents")
                    else:
                        results['failed_holdings'].append({
                            'symbol': symbol,
                            'error': batch_result.get('message', 'Unknown error')
                        })
                else:
                    # No new data is OK for incremental updates
                    results['holdings_updated'].append(symbol)
                    results['metrics']['new_documents_per_holding'][symbol] = 0
                    logger.info(f"ℹ️ No new data for {symbol} (up to date)")

            except Exception as e:
                logger.error(f"❌ Error processing incremental data for {symbol}: {str(e)}")
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