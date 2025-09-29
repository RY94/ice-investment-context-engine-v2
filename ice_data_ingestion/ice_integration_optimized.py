# ice_data_ingestion/ice_integration_optimized.py
"""
ELEGANT FIX: Optimized integration layer with batch processing and loose coupling
Replaces the problematic tight coupling in ice_integration.py with better patterns
Implements batch processing, circuit breaker, and configuration management
Relevant files: ice_integration.py, ../src/ice_lightrag/ice_rag_fixed.py
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker for handling repeated failures"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    async def call(self, func, *args, **kwargs):
        """Call async function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open - too many failures")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if self.state == "half_open":
                self.reset()
            return result
        except Exception as e:
            self._record_failure()
            raise e

    def _record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)

    def reset(self):
        """Reset the circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"


class OptimizedICEIntegration:
    """
    Optimized integration layer with loose coupling and batch processing

    FIXES:
    1. Loose coupling with lazy initialization
    2. Batch document processing
    3. Circuit breaker pattern for resilience
    4. Configuration management
    5. Intelligent caching
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize with loose coupling and configuration"""
        # Configuration management (Fix #4)
        self.config = self._load_config(config_path)

        # Lazy initialization (Fix #1)
        self._ice_rag = None
        self._mcp_manager = None
        self._fallback_manager = None

        # Circuit breakers for resilience (Fix #3)
        self.circuit_breakers = {
            "lightrag": CircuitBreaker(),
            "mcp": CircuitBreaker(),
            "fallback": CircuitBreaker()
        }

        # Simple cache for expensive operations (Fix #5)
        self._cache = {}
        self._cache_ttl = timedelta(minutes=self.config.get("cache_ttl_minutes", 10))

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration with sensible defaults"""
        defaults = {
            "batch_size": 10,
            "cache_ttl_minutes": 10,
            "max_retries": 3,
            "timeout_seconds": 30,
            "working_dir": "./src/ice_lightrag/storage"
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                defaults.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")

        return defaults

    async def _ensure_ice_rag(self):
        """Lazy initialization of ICE RAG with error isolation"""
        if self._ice_rag is not None:
            return self._ice_rag

        try:
            from src.ice_lightrag.ice_rag_fixed import JupyterICERAG
            self._ice_rag = JupyterICERAG(self.config["working_dir"])
            logger.info("ICE RAG initialized successfully")
            return self._ice_rag
        except Exception as e:
            logger.error(f"Failed to initialize ICE RAG: {e}")
            # Don't fail completely - system can work with MCP only
            return None

    async def _ensure_data_managers(self):
        """Lazy initialization of data managers"""
        if self._mcp_manager is None:
            try:
                from .mcp_data_manager import mcp_data_manager
                self._mcp_manager = mcp_data_manager
            except Exception as e:
                logger.warning(f"MCP manager not available: {e}")

        if self._fallback_manager is None:
            try:
                from .free_api_connectors import free_api_manager
                self._fallback_manager = free_api_manager
            except Exception as e:
                logger.warning(f"Fallback manager not available: {e}")

    def _get_cache_key(self, symbol: str, operation: str) -> str:
        """Generate cache key for operations"""
        return f"{symbol}_{operation}_{datetime.now().strftime('%Y%m%d_%H%M')}"

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False

        cached_time = datetime.fromisoformat(cache_entry.get("timestamp", "2020-01-01T00:00:00"))
        return datetime.now() - cached_time < self._cache_ttl

    async def batch_ingest_companies(
        self,
        symbols: List[str],
        add_to_knowledge_base: bool = True
    ) -> Dict[str, Any]:
        """
        OPTIMIZATION: Batch company intelligence ingestion
        Process multiple companies efficiently with intelligent batching
        """
        await self._ensure_data_managers()

        results = {}
        batch_size = self.config["batch_size"]

        # Process symbols in batches
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]

            # Create tasks for concurrent processing
            batch_tasks = []
            for symbol in batch_symbols:
                task = self._process_single_company_with_circuit_breaker(symbol)
                batch_tasks.append((symbol, task))

            # Execute batch concurrently
            for symbol, task in batch_tasks:
                try:
                    result = await task
                    results[symbol] = result
                except Exception as e:
                    logger.error(f"Failed to process {symbol}: {e}")
                    results[symbol] = {
                        "symbol": symbol,
                        "error": str(e),
                        "success": False,
                        "timestamp": datetime.now().isoformat()
                    }

        # Batch add to knowledge base if requested
        if add_to_knowledge_base and results:
            await self._batch_add_to_knowledge_base(results)

        return {
            "total_symbols": len(symbols),
            "successful": len([r for r in results.values() if r.get("success", False)]),
            "failed": len([r for r in results.values() if not r.get("success", False)]),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    async def _process_single_company_with_circuit_breaker(self, symbol: str) -> Dict[str, Any]:
        """Process single company with circuit breaker protection"""

        # Check cache first
        cache_key = self._get_cache_key(symbol, "intelligence")
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            logger.info(f"Using cached data for {symbol}")
            return self._cache[cache_key]["data"]

        try:
            # Use circuit breaker for MCP calls
            result = await self.circuit_breakers["mcp"].call(
                self._fetch_company_data_with_fallback, symbol
            )

            # Cache successful results
            self._cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"Circuit breaker prevented processing {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": f"Circuit breaker active: {str(e)}",
                "success": False,
                "timestamp": datetime.now().isoformat()
            }

    async def _fetch_company_data_with_fallback(self, symbol: str) -> Dict[str, Any]:
        """Fetch company data with intelligent fallback"""

        # Try MCP first
        if self._mcp_manager:
            try:
                from .mcp_data_manager import DataType, FinancialDataQuery

                query = FinancialDataQuery(data_type=DataType.STOCK_DATA, symbol=symbol)
                result = await self._mcp_manager.fetch_financial_data(query)

                if result and result.success:
                    return self._format_mcp_result(symbol, result)

            except Exception as e:
                logger.warning(f"MCP fetch failed for {symbol}: {e}")

        # Fallback to free APIs
        if self._fallback_manager:
            try:
                result = await self._fallback_manager.get_comprehensive_data(symbol)
                if result:
                    return self._format_fallback_result(symbol, result)
            except Exception as e:
                logger.warning(f"Fallback fetch failed for {symbol}: {e}")

        # If all fails
        raise Exception(f"All data sources failed for {symbol}")

    def _format_mcp_result(self, symbol: str, mcp_result) -> Dict[str, Any]:
        """Format MCP result efficiently"""
        return {
            "symbol": symbol,
            "success": True,
            "data_source": "mcp",
            "stock_data": mcp_result.stock_data[0] if mcp_result.stock_data else {},
            "confidence": mcp_result.confidence_score,
            "timestamp": datetime.now().isoformat()
        }

    def _format_fallback_result(self, symbol: str, fallback_result) -> Dict[str, Any]:
        """Format fallback result efficiently"""
        return {
            "symbol": symbol,
            "success": True,
            "data_source": "fallback",
            "stock_data": fallback_result.get("stock_data", {}),
            "confidence": 0.7,  # Lower confidence for fallback
            "timestamp": datetime.now().isoformat()
        }

    async def _batch_add_to_knowledge_base(self, results: Dict[str, Any]) -> int:
        """
        OPTIMIZATION: Batch knowledge base updates
        Process multiple documents in batches instead of one-by-one
        """
        ice_rag = await self._ensure_ice_rag()
        if not ice_rag:
            logger.warning("ICE RAG not available - skipping knowledge base updates")
            return 0

        try:
            # Prepare documents for batch processing
            documents = []
            for symbol, result in results.items():
                if result.get("success") and result.get("stock_data"):
                    doc_content = self._format_knowledge_document(symbol, result)
                    documents.append({
                        "content": doc_content,
                        "type": "market_intelligence"
                    })

            # Batch process with circuit breaker
            if documents:
                batch_result = await self.circuit_breakers["lightrag"].call(
                    ice_rag.add_documents_batch, documents
                )

                if isinstance(batch_result, dict):
                    successful = batch_result.get("successful", 0)
                    logger.info(f"Added {successful}/{len(documents)} documents to knowledge base")
                    return successful

            return 0

        except Exception as e:
            logger.error(f"Batch knowledge base update failed: {e}")
            return 0

    def _format_knowledge_document(self, symbol: str, result: Dict[str, Any]) -> str:
        """Format result as knowledge document efficiently"""
        stock_data = result.get("stock_data", {})

        doc = f"MARKET INTELLIGENCE: {symbol}\n"
        doc += f"Price: ${stock_data.get('price', 'N/A')}\n"
        doc += f"Change: {stock_data.get('change_percent', 'N/A')}%\n"
        doc += f"Volume: {stock_data.get('volume', 'N/A'):,}\n"
        doc += f"Market Cap: ${stock_data.get('market_cap', 'N/A'):,}\n"
        doc += f"Data Source: {result.get('data_source', 'unknown')}\n"
        doc += f"Confidence: {result.get('confidence', 0):.2f}\n"
        doc += f"Timestamp: {result['timestamp']}\n"

        return doc

    async def smart_query_with_context(self, query: str, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Smart query with automatic context refresh and caching"""
        # Refresh context if symbols provided
        if symbols:
            await self.batch_ingest_companies(symbols[:3])  # Limit for performance

        # Query the knowledge base
        ice_rag = await self._ensure_ice_rag()
        if ice_rag:
            return await ice_rag.query(query, mode="hybrid")
        else:
            return {
                "error": "Knowledge base not available",
                "timestamp": datetime.now().isoformat()
            }


# Global instance with lazy initialization
_optimized_integration = None


def get_optimized_integration() -> OptimizedICEIntegration:
    """Get the optimized integration instance"""
    global _optimized_integration
    if _optimized_integration is None:
        _optimized_integration = OptimizedICEIntegration()
    return _optimized_integration


# Convenience functions for easy migration
async def batch_ingest_companies(symbols: List[str], include_kb: bool = True) -> Dict[str, Any]:
    """Batch ingest multiple companies efficiently"""
    integration = get_optimized_integration()
    return await integration.batch_ingest_companies(symbols, include_kb)


async def smart_query_with_context(query: str, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """Smart query with automatic context refresh and caching"""
    integration = get_optimized_integration()
    return await integration.smart_query_with_context(query, symbols)