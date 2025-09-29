# lightrag/ice_rag.py
"""
Minimal LightRAG wrapper for ICE Investment Context Engine
Simple interface for financial document processing and querying
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    print("LightRAG not installed. Run: pip install lightrag")


class ICELightRAG:
    """Simple LightRAG wrapper for financial analysis"""
    
    def __init__(self, working_dir="./lightrag/storage"):
        """Initialize ICE LightRAG system"""
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        if not LIGHTRAG_AVAILABLE:
            self.rag = None
            return
            
        # Check for API key
        if not os.getenv("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY not set. LightRAG may not work properly.")
            self.rag = None
            return
            
        try:
            self.rag = LightRAG(
                working_dir=str(self.working_dir),
                llm_model_func=gpt_4o_mini_complete,
                embedding_func=openai_embed
            )
            # Initialize storages
            run_async(self._initialize_storages())
        except Exception as e:
            print(f"Error initializing LightRAG: {e}")
            self.rag = None
    
    async def _initialize_storages(self):
        """Initialize LightRAG storages"""
        if self.rag:
            await self.rag.initialize_storages()
            # Initialize pipeline status
            try:
                from lightrag.kg.shared_storage import initialize_pipeline_status
                await initialize_pipeline_status()
            except ImportError:
                # If shared_storage is not available, continue without it
                pass
    
    def is_ready(self):
        """Check if LightRAG is ready to use"""
        return self.rag is not None
    
    async def add_document(self, text, doc_type="financial"):
        """Add a financial document to the knowledge base"""
        if not self.is_ready():
            return {"status": "error", "message": "LightRAG not available"}
            
        try:
            # Add document type context for better processing
            enhanced_text = f"[{doc_type.upper()}] {text}"
            await self.rag.ainsert(enhanced_text)
            return {"status": "success", "message": "Document processed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def query(self, question, mode="hybrid"):
        """Query the knowledge base for investment insights"""
        if not self.is_ready():
            return {"status": "error", "message": "LightRAG not available"}
            
        try:
            result = await self.rag.aquery(question, param=QueryParam(mode=mode))
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Simple sync wrappers for easier integration
def run_async(coro):
    """Helper to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Event loop already running, skip initialization
            return None
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


class SimpleICERAG:
    """Synchronous wrapper for easier integration"""
    
    def __init__(self):
        self.async_rag = ICELightRAG()
    
    def is_ready(self):
        return self.async_rag.is_ready()
    
    def add_document(self, text, doc_type="financial"):
        """Add document (sync version)"""
        return run_async(self.async_rag.add_document(text, doc_type))
    
    def query(self, question, mode="hybrid"):
        """Query knowledge base (sync version)"""
        return run_async(self.async_rag.query(question, mode))
