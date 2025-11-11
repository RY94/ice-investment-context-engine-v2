# src/ice_lightrag/ice_rag_fixed.py
"""
ELEGANT FIX: Jupyter-Native LightRAG wrapper with proper async handling
Replaces the problematic SimpleICERAG with a Jupyter-compatible version
Fixes the "This event loop is already running" issue with zero complexity increase

Week 3 Integration: SecureConfig for encrypted API key management
Relevant files: ice_rag.py, ice_integration.py, ice_data_ingestion/secure_config.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Add project root to path for SecureConfig import
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import SecureConfig for encrypted API key management (Week 3 integration)
from ice_data_ingestion.secure_config import get_secure_config

load_dotenv()
logger = logging.getLogger(__name__)

# Import nest_asyncio for Jupyter compatibility
try:
    import nest_asyncio
    nest_asyncio.apply()
    NEST_ASYNCIO_AVAILABLE = True
except ImportError:
    NEST_ASYNCIO_AVAILABLE = False

try:
    from lightrag import LightRAG, QueryParam
    # Model provider imports moved to model_provider.py factory
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False

# Import model provider factory for Ollama/OpenAI selection
try:
    from .model_provider import (
        get_llm_provider,
        get_extraction_temperature,
        get_query_temperature,
        create_model_kwargs_with_temperature
    )
    MODEL_PROVIDER_AVAILABLE = True
except ImportError:
    MODEL_PROVIDER_AVAILABLE = False
    logger.warning("Model provider factory not available")

# Import context parser for structured attribution (Phase 2)
try:
    from .context_parser import LightRAGContextParser
    CONTEXT_PARSER_AVAILABLE = True
except ImportError:
    CONTEXT_PARSER_AVAILABLE = False
    logger.warning("Context parser not available")


class JupyterICERAG:
    """
    Elegant Jupyter-native LightRAG wrapper with proper async handling

    FIXES:
    1. No threading complexity - uses native Jupyter async
    2. Lazy initialization prevents resource leaks
    3. Proper event loop detection and handling
    4. Batch document processing optimization
    5. Configuration-driven setup
    """

    def __init__(self, working_dir: Optional[str] = None):
        """Initialize with lazy loading and proper configuration"""
        # Configuration-driven setup (Fix #5)
        self.config = self._load_config()
        self.working_dir = Path(working_dir or self.config.get("working_dir", "./src/ice_lightrag/storage"))
        self.working_dir.mkdir(parents=True, exist_ok=True)

        # Lazy initialization (Fix #2)
        self._rag = None
        self._initialized = False
        self._initialization_failed = False

        # Event loop detection (Fix #3)
        self._loop = None
        self._detect_environment()

        # Initialize context parser for structured attribution (Phase 2)
        self._context_parser = LightRAGContextParser() if CONTEXT_PARSER_AVAILABLE else None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and defaults"""
        return {
            "working_dir": os.getenv("ICE_WORKING_DIR", "./src/ice_lightrag/storage"),
            "batch_size": int(os.getenv("ICE_BATCH_SIZE", "5")),
            "timeout": int(os.getenv("ICE_TIMEOUT", "30")),
            "retry_attempts": int(os.getenv("ICE_RETRY_ATTEMPTS", "3"))
        }

    def _detect_environment(self):
        """Detect if we're in Jupyter and handle event loops appropriately"""
        try:
            # Check if we're in Jupyter
            __IPYTHON__
            self._is_jupyter = True
            # In Jupyter, use the current event loop
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop, we'll create one when needed
                self._loop = None
        except NameError:
            # Not in Jupyter
            self._is_jupyter = False
            self._loop = None

    def _set_operation_temperature(self, temperature: float):
        """
        Dynamically set operation-specific temperature for next LLM call

        LightRAG v1.4.9 wraps llm_model_func during initialization:
        ```python
        self.llm_model_func = priority_limit_async_func_call(...)(
            partial(self.llm_model_func, hashing_kv=hashing_kv, **self.llm_model_kwargs)
        )
        ```

        This means llm_model_func already includes:
        - hashing_kv binding (for LLM response caching)
        - **llm_model_kwargs binding (temperature, seed, etc.)
        - priority_limit_async_func_call wrapper (for async management)

        CRITICAL FIX: We must ONLY update llm_model_kwargs, NOT llm_model_func.
        Replacing llm_model_func would break the hashing_kv and wrapper, causing LLM
        calls to fail silently with None responses.

        Args:
            temperature: Temperature value (0.0-1.0)
        """
        if not self._rag:
            logger.warning("Cannot set temperature - RAG not initialized")
            return

        # Create new kwargs with desired temperature
        new_kwargs = create_model_kwargs_with_temperature(
            self._base_kwargs_template, temperature
        )

        # ONLY update llm_model_kwargs
        # LightRAG's partial() at line 633 will pick up these new kwargs
        self._rag.llm_model_kwargs = new_kwargs

        logger.debug(f"Set operation temperature to {temperature}")

    async def _ensure_initialized(self) -> bool:
        """
        Lazy initialization with proper error handling and pipeline status

        Week 3 Integration: Uses SecureConfig for encrypted API key retrieval
        """
        if self._initialized:
            return True

        if self._initialization_failed:
            logger.warning("Skipping initialization - previous failure")
            return False

        if not LIGHTRAG_AVAILABLE:
            logger.error("LightRAG not available")
            self._initialization_failed = True
            return False

        if not MODEL_PROVIDER_AVAILABLE:
            logger.error("Model provider factory not available")
            self._initialization_failed = True
            return False

        try:
            # Get model provider based on configuration (OpenAI or Ollama)
            # Factory handles Ollama health checks and OpenAI fallback automatically
            # Returns 4-tuple: (llm_func, embed_func, model_config, base_kwargs_template)
            llm_func, embed_func, model_config, base_kwargs_template = get_llm_provider()

            # Store temperature configuration for dynamic switching between operations
            # Entity extraction uses lower temperature (0.3 default) for reproducibility
            # Query answering uses higher temperature (0.5 default) for creative synthesis
            self._base_llm_func = llm_func  # Store for reference (not used after init)
            self._base_kwargs_template = base_kwargs_template  # Template for creating new kwargs
            self._extraction_temperature = get_extraction_temperature()
            self._query_temperature = get_query_temperature()

            # Initialize LightRAG with selected provider
            # model_config contains llm_model_name and llm_model_kwargs for Ollama
            # Empty dict for OpenAI (uses defaults)
            self._rag = LightRAG(
                working_dir=str(self.working_dir),
                llm_model_func=llm_func,
                embedding_func=embed_func,
                **model_config
            )

            # Initialize LightRAG storages (doc_status, entities, relationships, chunks)
            await self._rag.initialize_storages()

            # Conditionally initialize pipeline status based on use case
            # Production: Enable for multi-worker coordination (required in v1.4.9+)
            # Testing: Disable to avoid GLOBAL state that prevents testing same document at different temps
            # Set ICE_TESTING_MODE=true in notebook for temperature effect testing
            if not os.getenv('ICE_TESTING_MODE'):
                from lightrag.kg.shared_storage import initialize_pipeline_status
                await initialize_pipeline_status()
                logger.info("✅ Storage and pipeline status initialized (production mode)")
            else:
                logger.info("✅ Storage initialized (pipeline status skipped - testing mode)")

            self._initialized = True
            logger.info("✅ JupyterICERAG initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize LightRAG: {e}")
            self._initialization_failed = True
            return False

    def is_ready(self) -> bool:
        """Check if system is ready (sync check, no initialization)"""
        return self._initialized and self._rag is not None

    async def add_document(self, text: str, doc_type: str = "financial", file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a single document with proper error handling and source tracking.

        Uses entity extraction temperature (default 0.3) for LLM-based entity/relationship extraction.
        Lower temperature ensures reproducible graphs for backtesting and compliance.

        Args:
            text: Document content
            doc_type: Document type tag (e.g., 'financial', 'email')
            file_path: Optional source file path for traceability (e.g., 'email:Tencent_Q2_2025_Earnings.eml')

        Returns:
            Dict with status and message
        """
        if not await self._ensure_initialized():
            return {"status": "error", "message": "System not initialized"}

        try:
            # Set temperature for entity extraction (reproducibility-focused)
            self._set_operation_temperature(self._extraction_temperature)

            enhanced_text = f"[{doc_type.upper()}] {text}"
            await self._rag.ainsert(enhanced_text, file_paths=file_path if file_path else None)
            return {"status": "success", "message": "Document processed"}
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {"status": "error", "message": str(e)}

    async def add_documents_batch(self, documents: list, batch_size: Optional[int] = None) -> Dict[str, Any]:
        """
        OPTIMIZATION: Batch document processing (Fix #1)
        Process multiple documents efficiently in batches
        """
        if not await self._ensure_initialized():
            return {"status": "error", "message": "System not initialized"}

        batch_size = batch_size or self.config["batch_size"]
        total_docs = len(documents)
        successful = 0
        failed = 0
        errors = []

        try:
            # Process in batches to avoid overwhelming the system
            for i in range(0, total_docs, batch_size):
                batch = documents[i:i + batch_size]
                batch_tasks = []

                for doc in batch:
                    if isinstance(doc, dict):
                        text = doc.get("content", "")
                        doc_type = doc.get("type", "financial")
                        file_path = doc.get("file_path", None)  # Extract file_path for traceability
                    else:
                        text = str(doc)
                        doc_type = "financial"
                        file_path = None

                    task = self.add_document(text, doc_type, file_path=file_path)
                    batch_tasks.append(task)

                # Process batch concurrently
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                for result in batch_results:
                    if isinstance(result, Exception):
                        failed += 1
                        errors.append(str(result))
                    elif isinstance(result, dict) and result.get("status") == "success":
                        successful += 1
                    else:
                        failed += 1
                        errors.append(result.get("message", "Unknown error"))

            return {
                "status": "success" if successful > 0 else "error",
                "total_documents": total_docs,
                "successful": successful,
                "failed": failed,
                "errors": errors[:5],  # Limit error list
                "message": f"Processed {successful}/{total_docs} documents successfully"
            }

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "total_documents": total_docs,
                "successful": 0,
                "failed": total_docs
            }

    async def query(self, question: str, mode: str = "hybrid") -> Dict[str, Any]:
        """
        Query with proper timeout and retry handling, extracts source attribution

        Uses query answering temperature (default 0.5) for LLM-based response synthesis.
        Higher temperature enables creative connections while maintaining consistency.

        v1.4.9 UPDATE: Uses aquery_llm for HONEST tracing - single query returns both answer
        AND the exact context used to generate it. No more dual-query dishonesty.
        """
        if not await self._ensure_initialized():
            return {"status": "error", "message": "System not initialized", "engine": "lightrag"}

        try:
            # Set temperature for query answering (creativity-focused)
            self._set_operation_temperature(self._query_temperature)

            # SINGLE QUERY with structured response (v1.4.9+ aquery_llm)
            # Returns: answer, entities, relationships, chunks, references in ONE call
            # This guarantees honest tracing: displayed context matches LLM's actual context
            result_dict = await asyncio.wait_for(
                self._rag.aquery_llm(question, param=QueryParam(mode=mode)),
                timeout=self.config["timeout"]
            )

            # Validate LightRAG response structure (prevent silent failures)
            if not result_dict or not isinstance(result_dict, dict):
                raise ValueError("Invalid LightRAG response: expected dict, got {type(result_dict)}")
            if "llm_response" not in result_dict:
                raise ValueError("LightRAG response missing required field: llm_response")
            if "data" not in result_dict:
                raise ValueError("LightRAG response missing required field: data")

            # Extract components from structured response
            llm_response = result_dict.get("llm_response", {})
            answer = llm_response.get("content", "")
            data = result_dict.get("data", {})

            # Extract structured data (already parsed by LightRAG)
            entities = data.get("entities", [])
            relationships = data.get("relationships", [])
            chunks = data.get("chunks", [])
            references = data.get("references", [])  # NEW: Native v1.4.9 file references

            # Build parsed_context from structured data (backward compatibility)
            # No regex parsing needed - LightRAG provides clean structured data
            parsed_context = {
                "entities": entities,
                "relationships": relationships,
                "chunks": chunks,  # Required by graph_path_attributor, sentence_attributor, granular_display_formatter
                "summary": f"Retrieved {len(entities)} entities, {len(relationships)} relationships, {len(chunks)} chunks"
            }
            logger.info(f"Parsed context: {parsed_context['summary']}")

            # Build context string from chunks (contains SOURCE markers)
            # chunks is where LightRAG stores the actual retrieved text with markers
            context_lines = []
            for c in chunks:
                content = c.get('content', c.get('text', ''))
                if content:  # Only add non-empty chunks
                    context_lines.append(f"{content}\n\n")
            context = "".join(context_lines)

            # Extract SOURCE markers from chunks content (where they actually live)
            sources = self._extract_sources(context)

            # Calculate confidence from chunks content
            confidence = self._calculate_confidence(context)

            return {
                "status": "success",
                "result": answer,  # Alias for backward compat
                "answer": answer,
                "sources": sources,  # Legacy: Extracted from SOURCE markers
                "confidence": confidence,  # Aggregated confidence
                "context": context,  # Reconstructed for backward compat
                "parsed_context": parsed_context,  # Structured data (HONEST - from same query as answer)
                "references": references,  # NEW (v1.4.9): Native file references
                "engine": "lightrag",
                "mode": mode
            }

        except asyncio.TimeoutError:
            return {"status": "error", "message": "Query timeout", "engine": "lightrag"}
        except (KeyError, ValueError) as e:
            # Response structure errors (missing fields, invalid format)
            logger.error(f"LightRAG response structure error: {e}", exc_info=True)
            return {"status": "error", "message": f"Invalid response structure: {e}", "engine": "lightrag"}
        except Exception as e:
            # Unexpected errors (catch-all for unknown issues)
            logger.error(f"Unexpected query failure: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "engine": "lightrag"}

    def _extract_sources(self, context_text: str) -> list:
        """
        Extract source attribution from retrieved context for traceability

        PRIORITY ORDER (higher priority = more specific):
        1. [SOURCE:FMP|SYMBOL:NVDA] - API ingestion markers (HIGHEST PRIORITY)
        2. [SOURCE_EMAIL:subject|...] - Email ingestion markers
        3. [TICKER:NVDA|confidence:0.95] - Entity extraction markers
        4. [KG] / [DC] - LightRAG reference markers (FALLBACK ONLY)

        Args:
            context_text: Retrieved context from LightRAG (contains chunks with SOURCE markers)

        Returns: [{'source': 'fmp', 'confidence': 0.95, 'symbol': 'NVDA'}, ...]
        """
        import re

        sources_dict = {}

        # Pattern 1: API ingestion format [SOURCE:FMP|SYMBOL:NVDA]
        # Captures source type (FMP, NEWSAPI, etc.) and ticker symbol
        api_pattern = r'\[SOURCE:(\w+)\|SYMBOL:([^\]]+)\]'
        api_matches = re.findall(api_pattern, context_text)
        for source_type, symbol in api_matches:
            key = f"{source_type}:{symbol}"
            sources_dict[key] = {
                'source': source_type.lower(),  # 'fmp', 'newsapi', 'sec_edgar'
                'confidence': 0.85,  # Default confidence for API sources
                'symbol': symbol,
                'type': 'api'
            }

        # Pattern 2: Email ingestion format [SOURCE_EMAIL:subject|...]
        email_pattern = r'\[SOURCE_EMAIL:([^\|]+)\|'
        email_matches = re.findall(email_pattern, context_text)
        for subject in email_matches:
            key = f"EMAIL:{subject[:30]}"  # Truncate long subjects
            sources_dict[key] = {
                'source': 'email',
                'confidence': 0.90,  # Email sources often have high confidence
                'symbol': subject[:50],
                'type': 'email'
            }

        # Pattern 3: Entity markers [TICKER:NVDA|confidence:0.95]
        # Extract confidence if available
        ticker_conf_pattern = r'\[TICKER:([^\|]+)\|confidence:([\d.]+)'
        ticker_conf_matches = re.findall(ticker_conf_pattern, context_text)
        for ticker, conf in ticker_conf_matches:
            if ticker and len(ticker) <= 5:
                key = f"ENTITY:{ticker}"
                sources_dict[key] = {
                    'source': 'entity_extraction',
                    'confidence': float(conf),
                    'symbol': ticker,
                    'type': 'entity'
                }

        # Pattern 4 (FALLBACK): LightRAG references [KG] / [DC]
        # Only use if NO real SOURCE markers found
        if not sources_dict:
            if '[KG]' in context_text:
                sources_dict['KG:GRAPH'] = {
                    'source': 'knowledge_graph',
                    'confidence': 0.70,
                    'symbol': 'GRAPH',
                    'type': 'internal'
                }
            if '[DC]' in context_text:
                sources_dict['DC:DOCS'] = {
                    'source': 'document_context',
                    'confidence': 0.70,
                    'symbol': 'DOCS',
                    'type': 'internal'
                }

        sources = list(sources_dict.values())

        if sources:
            logger.info(f"Extracted {len(sources)} unique sources: {[s['source'] for s in sources]}")
        else:
            logger.warning("No SOURCE markers found in context - check data ingestion pipeline")

        return sources

    def _calculate_confidence(self, answer_text: str) -> float:
        """
        Calculate aggregated confidence from answer text

        Pattern: confidence:0.92 or confidence=0.85
        Returns: Average confidence (0.0-1.0), or None if no confidence found
        """
        import re

        # Find all confidence scores in answer
        pattern = r'confidence[:=]\s*(\d+\.?\d*)'
        matches = re.findall(pattern, answer_text, re.IGNORECASE)

        if not matches:
            return None

        # Convert to floats and calculate average
        confidences = [float(c) for c in matches]
        avg_confidence = sum(confidences) / len(confidences)

        logger.info(f"Calculated confidence: {avg_confidence:.2f} from {len(confidences)} scores")

        return round(avg_confidence, 2)


class JupyterSyncWrapper:
    """
    Sync wrapper that properly handles Jupyter environments
    Uses the existing event loop instead of creating new threads
    """

    def __init__(self, working_dir: Optional[str] = None):
        """Initialize sync wrapper"""
        self._async_rag = JupyterICERAG(working_dir)

    def _run_async(self, coro):
        """Run async coroutine using the appropriate method for the environment"""
        # nest_asyncio.apply() at module level (line 32) makes event loops re-entrant
        # This allows safe use of run_until_complete() even when loop is running
        try:
            loop = asyncio.get_event_loop()

            if loop.is_closed():
                # BUG FIX (2025-11-04): asyncio.run() fails if closed loop exists in thread
                # Must remove closed loop before creating new one
                asyncio.set_event_loop(None)  # Remove closed loop from thread
                new_loop = asyncio.new_event_loop()  # Create fresh loop
                asyncio.set_event_loop(new_loop)  # Set as current
                try:
                    result = new_loop.run_until_complete(coro)
                    return result
                finally:
                    # Don't close loop here - leave it for reuse
                    # new_loop.close()
                    pass

            return loop.run_until_complete(coro)
        except RuntimeError as e:
            if "no running event loop" in str(e).lower():
                # No event loop exists - create one (standard Python environment)
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result = new_loop.run_until_complete(coro)
                    return result
                finally:
                    # Don't close loop here - leave it for reuse
                    pass
            else:
                # Unexpected error - re-raise
                raise

    def is_ready(self) -> bool:
        """Sync version of is_ready"""
        return self._async_rag.is_ready()

    def add_document(self, text: str, doc_type: str = "financial", file_path: Optional[str] = None):
        """Sync version of add_document"""
        return self._run_async(self._async_rag.add_document(text, doc_type, file_path=file_path))

    def add_documents_batch(self, documents: list):
        """Sync version of batch processing"""
        return self._run_async(self._async_rag.add_documents_batch(documents))

    def query(self, question: str, mode: str = "hybrid"):
        """Sync version of query"""
        return self._run_async(self._async_rag.query(question, mode))


# Backward compatibility aliases
SimpleICERAG = JupyterSyncWrapper
ICELightRAG = JupyterICERAG


# Export the fixed version
__all__ = ['JupyterICERAG', 'JupyterSyncWrapper', 'SimpleICERAG', 'ICELightRAG']