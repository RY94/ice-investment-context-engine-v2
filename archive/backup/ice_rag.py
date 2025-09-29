# lightrag/ice_rag.py
"""
Minimal LightRAG wrapper for ICE Investment Context Engine
Simple interface for financial document processing and querying
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    logger.warning("LightRAG not installed. Run: pip install lightrag")


class ICELightRAG:
    """Simple LightRAG wrapper for financial analysis"""
    
    def __init__(self, working_dir: str = "./lightrag/storage"):
        """Initialize ICE LightRAG system"""
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.rag: Optional[LightRAG] = None
        
        if not LIGHTRAG_AVAILABLE:
            logger.error("LightRAG module not available")
            return
            
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not set")
            return
            
        try:
            self.rag = LightRAG(
                working_dir=str(self.working_dir),
                llm_model_func=gpt_4o_mini_complete,
                embedding_func=openai_embed
            )
            run_async(self._initialize_storages())
            logger.info(f"LightRAG initialized with working_dir: {self.working_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize LightRAG: {e}")
            self.rag = None
    
    async def _initialize_storages(self) -> None:
        """Initialize LightRAG storages"""
        if not self.rag:
            return
            
        try:
            await self.rag.initialize_storages()
            
            # Initialize pipeline status if available
            try:
                from lightrag.kg.shared_storage import initialize_pipeline_status
                await initialize_pipeline_status()
                logger.debug("Pipeline status initialized")
            except ImportError:
                logger.debug("Pipeline status module not available")
            
            logger.debug("Storage initialized successfully")
        except Exception as e:
            logger.error(f"Storage initialization failed: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if LightRAG is ready to use"""
        return self.rag is not None
    
    async def add_document(self, text: str, doc_type: str = "financial") -> Dict[str, Any]:
        """Add a financial document to the knowledge base"""
        if not self.is_ready():
            return {"status": "error", "message": "LightRAG not available"}
        
        if not text or not text.strip():
            return {"status": "error", "message": "Empty document provided"}
            
        try:
            enhanced_text = f"[{doc_type.upper()}] {text.strip()}"
            await self.rag.ainsert(enhanced_text)
            logger.info(f"Document added: {doc_type}, length: {len(text)}")
            return {"status": "success", "message": "Document processed"}
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return {"status": "error", "message": str(e)}
    
    async def query(self, question: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Query the knowledge base for investment insights"""
        if not self.is_ready():
            return {"status": "error", "message": "LightRAG not available"}
        
        if not question or not question.strip():
            return {"status": "error", "message": "Empty question provided"}
        
        valid_modes = ["local", "global", "hybrid", "naive"]
        if mode not in valid_modes:
            logger.warning(f"Invalid mode '{mode}', using 'hybrid'")
            mode = "hybrid"
            
        try:
            result = await self.rag.aquery(question.strip(), param=QueryParam(mode=mode))
            logger.info(f"Query executed: mode={mode}, question_length={len(question)}")
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"status": "error", "message": str(e)}


# Simple sync wrappers for easier integration
def run_async(coro):
    """Helper to run async functions in sync context"""
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        
        # If we're in a running loop (like Streamlit), use a thread pool
        import concurrent.futures
        import threading
        
        def run_in_thread():
            # Create a completely new event loop in the thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop is running, safe to use asyncio.run
        return asyncio.run(coro)


class SimpleICERAG:
    """Synchronous wrapper for easier integration"""
    
    def __init__(self, working_dir: str = "./lightrag/storage"):
        import concurrent.futures
        import threading
        
        # Create a dedicated thread pool executor that persists for this instance
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.thread_local_loop = None
        
        # Initialize LightRAG in the dedicated thread
        def init_in_thread():
            # Create and set event loop for this dedicated thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.thread_local_loop = loop
            return ICELightRAG(working_dir)
        
        future = self.executor.submit(init_in_thread)
        self.async_rag = future.result()
        
        # Import earnings functionality
        try:
            from earnings_fetcher import fetch_company_earnings
            self.earnings_available = True
            self._fetch_earnings = fetch_company_earnings
        except ImportError:
            logger.warning("earnings_fetcher not available")
            self.earnings_available = False
    
    def is_ready(self) -> bool:
        return self.async_rag.is_ready()
    
    def add_document(self, text: str, doc_type: str = "financial") -> Dict[str, Any]:
        """Add document (sync version)"""
        try:
            future = self.executor.submit(
                lambda: asyncio.run_coroutine_threadsafe(
                    self.async_rag.add_document(text, doc_type), 
                    self.thread_local_loop
                ).result(timeout=180)  # 3 minute timeout for document processing
            )
            return future.result(timeout=210)  # 3.5 minute timeout for thread pool
        except TimeoutError:
            logger.error(f"Document addition timed out for doc_type: {doc_type}")
            return {"status": "error", "message": "Document processing timed out. Try with a shorter document."}
        except Exception as e:
            logger.error(f"Document addition failed: {e}")
            return {"status": "error", "message": f"Failed to add document: {str(e)}"}
    
    def query(self, question: str, mode: str = "hybrid") -> Dict[str, Any]:
        """Query knowledge base (sync version)"""
        try:
            future = self.executor.submit(
                lambda: asyncio.run_coroutine_threadsafe(
                    self.async_rag.query(question, mode),
                    self.thread_local_loop
                ).result(timeout=120)  # 2 minute timeout for async operation
            )
            return future.result(timeout=150)  # 2.5 minute timeout for thread pool
        except TimeoutError:
            logger.error(f"Query timed out for question: {question}")
            return {"status": "error", "message": "Query timed out. Please try a simpler question or check your connection."}
        except Exception as e:
            logger.error(f"Query failed with exception: {e}")
            return {"status": "error", "message": f"Query failed: {str(e)}"}
    
    def fetch_and_add_earnings(self, company_query: str) -> Dict[str, Any]:
        """
        Fetch latest earnings for a company and add to knowledge base
        
        Args:
            company_query: Company name or ticker symbol (e.g., "NVDA", "nvidia")
        
        Returns:
            Dict with status and details about the operation
        """
        if not self.earnings_available:
            return {
                "status": "error",
                "message": "Earnings fetching not available. Check earnings_fetcher module."
            }
        
        if not self.is_ready():
            return {
                "status": "error", 
                "message": "LightRAG not ready"
            }
        
        try:
            # Fetch earnings data
            earnings_result = self._fetch_earnings(company_query)
            
            if earnings_result["status"] != "success":
                return earnings_result
            
            # Add earnings document to knowledge base
            doc_result = self.add_document(
                earnings_result["document_text"], 
                "earnings_report"
            )
            
            if doc_result["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Failed to add earnings to knowledge base: {doc_result['message']}"
                }
            
            return {
                "status": "success",
                "ticker": earnings_result["ticker"],
                "company_name": earnings_result["company_name"], 
                "source": earnings_result["source"],
                "last_updated": earnings_result["last_updated"],
                "message": f"Added latest earnings for {earnings_result['company_name']} ({earnings_result['ticker']}) to knowledge base"
            }
            
        except Exception as e:
            logger.error(f"Error in fetch_and_add_earnings for {company_query}: {e}")
            return {
                "status": "error",
                "message": f"Failed to fetch and add earnings: {str(e)}"
            }
    
    def query_with_earnings(self, question: str, company_query: str = None, mode: str = "hybrid") -> Dict[str, Any]:
        """
        Query with automatic earnings fetching if company is mentioned
        
        Args:
            question: The question to ask
            company_query: Optional specific company to fetch earnings for
            mode: LightRAG query mode
        
        Returns:
            Dict with query results and earnings info if fetched
        """
        result = {"status": "success", "earnings_fetched": False}
        
        # If company specified, fetch earnings first
        if company_query and self.earnings_available:
            earnings_result = self.fetch_and_add_earnings(company_query)
            if earnings_result["status"] == "success":
                result["earnings_fetched"] = True
                result["earnings_info"] = {
                    "ticker": earnings_result["ticker"],
                    "company_name": earnings_result["company_name"],
                    "source": earnings_result["source"]
                }
            else:
                # Continue with query even if earnings fetch failed
                result["earnings_error"] = earnings_result["message"]
        
        # Execute the query
        query_result = self.query(question, mode)
        result.update(query_result)
        
        return result
