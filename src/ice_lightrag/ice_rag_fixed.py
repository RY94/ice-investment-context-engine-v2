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
    from .model_provider import get_llm_provider
    MODEL_PROVIDER_AVAILABLE = True
except ImportError:
    MODEL_PROVIDER_AVAILABLE = False
    logger.warning("Model provider factory not available")


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
            llm_func, embed_func, model_config = get_llm_provider()

            # Initialize LightRAG with selected provider
            # model_config contains llm_model_name and llm_model_kwargs for Ollama
            # Empty dict for OpenAI (uses defaults)
            self._rag = LightRAG(
                working_dir=str(self.working_dir),
                llm_model_func=llm_func,
                embedding_func=embed_func,
                **model_config
            )

            # CRITICAL FIX: Initialize storages AND pipeline status
            await self._rag.initialize_storages()

            # Initialize pipeline status (REQUIRED for document processing)
            try:
                from lightrag.kg.shared_storage import initialize_pipeline_status
                await initialize_pipeline_status()
                logger.info("✅ Pipeline status initialized successfully")
            except ImportError as e:
                logger.warning(f"Pipeline status initialization import failed: {e}")
                # Try alternative initialization if available
                try:
                    # Some versions may have different import paths
                    from lightrag.storage import initialize_pipeline_status
                    await initialize_pipeline_status()
                    logger.info("✅ Pipeline status initialized (alternative import)")
                except ImportError:
                    logger.warning("Pipeline status initialization not available - will try to continue")

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

    async def add_document(self, text: str, doc_type: str = "financial") -> Dict[str, Any]:
        """Add a single document with proper error handling"""
        if not await self._ensure_initialized():
            return {"status": "error", "message": "System not initialized"}

        try:
            enhanced_text = f"[{doc_type.upper()}] {text}"
            await self._rag.ainsert(enhanced_text)
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
                    else:
                        text = str(doc)
                        doc_type = "financial"

                    task = self.add_document(text, doc_type)
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
        """Query with proper timeout and retry handling"""
        if not await self._ensure_initialized():
            return {"status": "error", "message": "System not initialized", "engine": "lightrag"}

        try:
            # Use timeout to prevent hanging
            result = await asyncio.wait_for(
                self._rag.aquery(question, param=QueryParam(mode=mode)),
                timeout=self.config["timeout"]
            )

            return {
                "status": "success",
                "result": result,
                "answer": result,
                "engine": "lightrag",
                "mode": mode
            }

        except asyncio.TimeoutError:
            return {"status": "error", "message": "Query timeout", "engine": "lightrag"}
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"status": "error", "message": str(e), "engine": "lightrag"}


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
        try:
            # In Jupyter, nest_asyncio should handle this
            if self._async_rag._is_jupyter and NEST_ASYNCIO_AVAILABLE:
                # Try to run directly (nest_asyncio should handle it)
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a task and wait for it
                    task = loop.create_task(coro)
                    return loop.run_until_complete(task)
                else:
                    return loop.run_until_complete(coro)
            else:
                # Standard environment
                return asyncio.run(coro)
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                # Fallback: return a future that can be awaited
                logger.warning("Event loop conflict detected - returning coroutine for direct await")
                return coro
            else:
                raise

    def is_ready(self) -> bool:
        """Sync version of is_ready"""
        return self._async_rag.is_ready()

    def add_document(self, text: str, doc_type: str = "financial"):
        """Sync version of add_document"""
        return self._run_async(self._async_rag.add_document(text, doc_type))

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