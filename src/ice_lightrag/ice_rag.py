# src/ice_lightrag/ice_rag.py
"""
DEPRECATED - Use ice_rag_fixed.py instead
This file contains obsolete wrappers that don't work properly with Jupyter
Kept for backwards compatibility only - will be removed in next major version
"""

import os
import asyncio
import sys
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import nest_asyncio for Jupyter compatibility
try:
    import nest_asyncio
    nest_asyncio.apply()
    NEST_ASYNCIO_AVAILABLE = True
except ImportError:
    NEST_ASYNCIO_AVAILABLE = False
    print("⚠️ nest_asyncio not available - Jupyter notebook support may be limited")

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
    LIGHTRAG_AVAILABLE = True
    print("✅ LightRAG successfully imported!")
except ImportError as e:
    LIGHTRAG_AVAILABLE = False
    print(f"❌ LightRAG not available: {e}")


class ICELightRAG:
    """DEPRECATED - Use JupyterSyncWrapper from ice_rag_fixed.py instead
    This async wrapper doesn't work properly in Jupyter notebooks"""

    def __init__(self, working_dir="./lightrag/storage"):
        """Initialize ICE LightRAG system with better async handling"""
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.rag = None
        self._initialized = False

        if not LIGHTRAG_AVAILABLE:
            raise ImportError("LightRAG is not installed. Please run: pip install lightrag")

        # Check for API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. Please set it in your environment or .env file")

        # Initialize LightRAG synchronously
        try:
            self.rag = LightRAG(
                working_dir=str(self.working_dir),
                llm_model_func=gpt_4o_mini_complete,
                embedding_func=openai_embed
            )
            # Mark as needing async initialization
            self._initialized = False
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LightRAG: {e}")

    async def ensure_initialized(self):
        """Ensure async components are initialized (idempotent)"""
        if not self._initialized and self.rag:
            try:
                await self.rag.initialize_storages()
                # Try to initialize pipeline status if available
                try:
                    from lightrag.kg.shared_storage import initialize_pipeline_status
                    await initialize_pipeline_status()
                except ImportError:
                    pass  # Optional component
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize LightRAG storages: {e}")

    def is_ready(self):
        """Check if LightRAG is ready to use"""
        return self.rag is not None

    async def add_document(self, text: str, doc_type: str = "financial") -> Dict[str, Any]:
        """Add a financial document to the knowledge base (async)"""
        if not self.is_ready():
            raise RuntimeError("LightRAG not initialized properly")

        await self.ensure_initialized()

        try:
            enhanced_text = f"[{doc_type.upper()}] {text}"
            await self.rag.ainsert(enhanced_text)
            return {"status": "success", "message": "Document processed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def query(self, question: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Query the knowledge base for investment insights (async)"""
        if not self.is_ready():
            raise RuntimeError("LightRAG not initialized properly")

        await self.ensure_initialized()

        try:
            result = await self.rag.aquery(question, param=QueryParam(mode=mode))
            return {
                "status": "success",
                "result": result,
                "answer": result,
                "engine": "lightrag",
                "query_time": 0.5
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "engine": "lightrag"}


class SimpleICERAG:
    """DEPRECATED - Use JupyterSyncWrapper from ice_rag_fixed.py instead
    This thread-based wrapper can cause deadlocks in Jupyter"""

    def __init__(self, working_dir: str = "./lightrag/storage"):
        """Initialize with proper sync handling"""
        self.working_dir = working_dir
        self._async_rag = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._loop = None
        self._thread = None

        # Initialize in a separate thread to avoid event loop conflicts
        self._initialize_in_thread()

    def _initialize_in_thread(self):
        """Initialize async components in a dedicated thread"""
        def init_async():
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop

            # Initialize async RAG
            self._async_rag = ICELightRAG(self.working_dir)

            # Keep the loop running
            loop.run_forever()

        self._thread = threading.Thread(target=init_async, daemon=True)
        self._thread.start()

        # Wait for initialization (with timeout)
        import time
        for _ in range(10):  # Wait up to 1 second
            if self._async_rag is not None:
                break
            time.sleep(0.1)

        if self._async_rag is None:
            raise RuntimeError("Failed to initialize async RAG in thread")

    def _run_async(self, coro):
        """Run async coroutine in the dedicated thread's event loop"""
        if self._loop is None:
            raise RuntimeError("Event loop not initialized")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30)  # 30 second timeout

    def is_ready(self) -> bool:
        """Check if system is ready"""
        return self._async_rag is not None and self._async_rag.is_ready()

    def add_document(self, text: str, doc_type: str = "financial") -> Dict[str, Any]:
        """Add document (sync version)"""
        if not self.is_ready():
            return {"status": "error", "message": "System not ready"}

        try:
            return self._run_async(self._async_rag.add_document(text, doc_type))
        except Exception as e:
            return {"status": "error", "message": f"Document processing failed: {str(e)}"}

    def query(self, question: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Query knowledge base (sync version)"""
        if not self.is_ready():
            return {"status": "error", "message": "System not ready", "engine": "lightrag"}

        try:
            return self._run_async(self._async_rag.query(question, mode))
        except Exception as e:
            return {"status": "error", "message": f"Query failed: {str(e)}", "engine": "lightrag"}

    def __del__(self):
        """Cleanup resources"""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._executor:
            self._executor.shutdown(wait=False)
