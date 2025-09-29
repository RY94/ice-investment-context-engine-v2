# ice_unified_rag.py
# Unified interface for both LightRAG and LazyGraphRAG systems
# Provides seamless switching between RAG engines for ICE development
# Enables comparative analysis and performance benchmarking

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

# Add paths for imports
sys.path.append('./ice_lightrag')
sys.path.append('./ice_lazyrag')


@dataclass
class RAGEngineInfo:
    """Information about available RAG engines"""
    name: str
    version: str
    description: str
    available: bool
    error_message: Optional[str] = None


class ICEUnifiedRAG:
    """
    Unified interface for ICE RAG systems supporting both LightRAG and LazyGraphRAG.
    
    Provides:
    - Seamless switching between engines
    - Common interface for all operations
    - Performance comparison capabilities
    - Fallback handling for unavailable engines
    """
    
    def __init__(self, default_engine: str = "lightrag", working_dir: str = "./unified_storage"):
        """
        Initialize unified RAG system with specified default engine.
        
        Args:
            default_engine: "lightrag" or "lazyrag"
            working_dir: Base directory for storage
        """
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(exist_ok=True)
        
        # Engine instances
        self.lightrag = None
        self.lazyrag = None
        
        # Engine availability
        self.available_engines = self._detect_available_engines()
        
        # Current engine state
        self.current_engine_name = None
        self.current_engine = None
        
        # Query history
        self.query_history = []
        
        # Performance metrics
        self.performance_metrics = {
            "lightrag": {"queries": 0, "total_time": 0, "avg_time": 0, "errors": 0},
            "lazyrag": {"queries": 0, "total_time": 0, "avg_time": 0, "errors": 0}
        }
        
        # Initialize default engine
        self.set_engine(default_engine)
    
    def _detect_available_engines(self) -> Dict[str, RAGEngineInfo]:
        """Detect which RAG engines are available"""
        engines = {}
        
        # Test LightRAG availability
        try:
            from ice_rag import ICELightRAG, LIGHTRAG_AVAILABLE
            if LIGHTRAG_AVAILABLE:
                engines["lightrag"] = RAGEngineInfo(
                    name="LightRAG",
                    version="1.0",
                    description="Traditional pre-built knowledge graph RAG system",
                    available=True
                )
            else:
                engines["lightrag"] = RAGEngineInfo(
                    name="LightRAG",
                    version="1.0", 
                    description="Traditional pre-built knowledge graph RAG system",
                    available=False,
                    error_message="LightRAG dependencies not available"
                )
        except ImportError as e:
            engines["lightrag"] = RAGEngineInfo(
                name="LightRAG", 
                version="Unknown",
                description="Traditional pre-built knowledge graph RAG system",
                available=False,
                error_message=str(e)
            )
        
        # Test LazyRAG availability
        try:
            from lazy_rag import SimpleLazyRAG
            engines["lazyrag"] = RAGEngineInfo(
                name="LazyGraphRAG",
                version="0.1.0", 
                description="Dynamic on-demand knowledge graph construction",
                available=True
            )
        except ImportError as e:
            engines["lazyrag"] = RAGEngineInfo(
                name="LazyGraphRAG",
                version="Unknown",
                description="Dynamic on-demand knowledge graph construction", 
                available=False,
                error_message=str(e)
            )
        
        return engines
    
    def get_available_engines(self) -> Dict[str, RAGEngineInfo]:
        """Get information about available engines"""
        return self.available_engines
    
    def is_engine_available(self, engine_name: str) -> bool:
        """Check if specified engine is available"""
        return engine_name in self.available_engines and self.available_engines[engine_name].available
    
    def set_engine(self, engine_name: str) -> bool:
        """
        Set the active RAG engine.
        
        Args:
            engine_name: "lightrag" or "lazyrag"
            
        Returns:
            True if engine was successfully set, False otherwise
        """
        if not self.is_engine_available(engine_name):
            print(f"❌ Engine '{engine_name}' is not available")
            return False
        
        try:
            if engine_name == "lightrag":
                if self.lightrag is None:
                    from ice_rag import SimpleICERAG
                    self.lightrag = SimpleICERAG()
                    # Set working directory if the SimpleICERAG has that capability
                    if hasattr(self.lightrag.async_rag, 'working_dir'):
                        self.lightrag.async_rag.working_dir = self.working_dir / "lightrag"
                self.current_engine = self.lightrag
                
            elif engine_name == "lazyrag":
                if self.lazyrag is None:
                    from lazy_rag import SimpleLazyRAG
                    self.lazyrag = SimpleLazyRAG(working_dir=str(self.working_dir / "lazyrag"))
                self.current_engine = self.lazyrag
                
            else:
                print(f"❌ Unknown engine: {engine_name}")
                return False
            
            self.current_engine_name = engine_name
            print(f"✅ Switched to {self.available_engines[engine_name].name}")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing {engine_name}: {e}")
            return False
    
    def get_current_engine(self) -> Optional[str]:
        """Get name of currently active engine"""
        return self.current_engine_name
    
    def is_ready(self) -> bool:
        """Check if current engine is ready"""
        if self.current_engine is None:
            return False
        
        # Check engine-specific readiness
        if hasattr(self.current_engine, 'is_ready'):
            return self.current_engine.is_ready()
        
        return True
    
    def query(self, question: str, mode: str = "hybrid", **kwargs) -> Dict[str, Any]:
        """
        Execute query using current engine with unified interface.
        
        Args:
            question: Natural language query
            mode: Query mode (varies by engine)
            **kwargs: Engine-specific parameters
            
        Returns:
            Standardized query result dictionary
        """
        if not self.is_ready():
            return {
                "status": "error",
                "message": f"No active engine or engine not ready",
                "engine": self.current_engine_name,
                "answer": "System not ready for queries",
                "query_time": 0
            }
        
        # Record query start
        start_time = time.time()
        query_record = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "mode": mode,
            "engine": self.current_engine_name,
            "kwargs": kwargs
        }
        
        try:
            # Execute query with appropriate interface
            if self.current_engine_name == "lightrag":
                result = self._query_lightrag(question, mode, **kwargs)
            elif self.current_engine_name == "lazyrag":
                result = self._query_lazyrag(question, mode, **kwargs)
            else:
                raise ValueError(f"Unknown engine: {self.current_engine_name}")
            
            # Calculate timing
            query_time = time.time() - start_time
            
            # Standardize result format
            standardized_result = self._standardize_result(result, query_time)
            
            # Update performance metrics
            self._update_performance_metrics(self.current_engine_name, query_time, success=True)
            
            # Record query
            query_record.update({
                "success": True,
                "result": standardized_result,
                "query_time": query_time
            })
            
            self.query_history.append(query_record)
            
            return standardized_result
            
        except Exception as e:
            query_time = time.time() - start_time
            
            # Update error metrics
            self._update_performance_metrics(self.current_engine_name, query_time, success=False)
            
            error_result = {
                "status": "error",
                "message": str(e),
                "engine": self.current_engine_name,
                "answer": f"Error processing query with {self.current_engine_name}: {e}",
                "query_time": query_time,
                "sources": [],
                "reasoning_chain": "",
                "confidence_scores": {}
            }
            
            query_record.update({
                "success": False,
                "result": error_result,
                "error": str(e),
                "query_time": query_time
            })
            
            self.query_history.append(query_record)
            
            return error_result
    
    def _query_lightrag(self, question: str, mode: str, **kwargs) -> Dict[str, Any]:
        """Execute query using LightRAG"""
        # LightRAG has async interface, so we use the async version
        import asyncio
        if hasattr(self.lightrag, 'query'):
            # Synchronous version
            return self.lightrag.query(question, mode)
        else:
            # Async version - handle Jupyter's existing event loop
            try:
                # Try to get current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # In Jupyter, use nest_asyncio to handle nested loops
                    try:
                        import nest_asyncio
                        nest_asyncio.apply()
                        return asyncio.run(self.lightrag.aquery(question, mode))
                    except ImportError:
                        # Fallback: create a task in current loop
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self.lightrag.aquery(question, mode))
                            return future.result()
                else:
                    return asyncio.run(self.lightrag.aquery(question, mode))
            except Exception as e:
                # Fallback to sync if async fails
                if hasattr(self.lightrag, 'query'):
                    return self.lightrag.query(question, mode)
                else:
                    return {"status": "error", "message": f"Async query failed: {str(e)}"}
    
    def _query_lazyrag(self, question: str, mode: str, **kwargs) -> Dict[str, Any]:
        """Execute query using LazyRAG"""
        # LazyRAG parameters
        max_hops = kwargs.get('max_hops', 3)
        confidence_threshold = kwargs.get('confidence_threshold', 0.7)
        
        return self.lazyrag.query(
            question=question,
            mode=mode,
            max_hops=max_hops,
            confidence_threshold=confidence_threshold
        )
    
    def _standardize_result(self, result: Dict[str, Any], query_time: float) -> Dict[str, Any]:
        """Standardize result format across engines"""
        
        # Handle different result formats
        if isinstance(result, dict):
            # LazyRAG format
            if "result" in result and "status" in result:
                return {
                    "status": result.get("status", "success"),
                    "message": result.get("message", ""),
                    "engine": self.current_engine_name,
                    "answer": result.get("result", ""),
                    "query_time": query_time,
                    "sources": result.get("sources", []),
                    "reasoning_chain": result.get("reasoning_paths", []),
                    "confidence_scores": {"overall": result.get("confidence_score", 0.5)},
                    "entities_analyzed": result.get("entities_analyzed", 0),
                    "relationships_found": result.get("relationships_found", 0),
                    "subgraph": result.get("subgraph", None),
                    "processing_details": result
                }
            else:
                # LightRAG format (simple string or dict)
                answer = result if isinstance(result, str) else str(result)
                return {
                    "status": "success",
                    "message": "",
                    "engine": self.current_engine_name,
                    "answer": answer,
                    "query_time": query_time,
                    "sources": [],
                    "reasoning_chain": "",
                    "confidence_scores": {"overall": 0.5},
                    "entities_analyzed": 0,
                    "relationships_found": 0,
                    "processing_details": result
                }
        else:
            # Simple string result
            return {
                "status": "success",
                "message": "",
                "engine": self.current_engine_name,
                "answer": str(result),
                "query_time": query_time,
                "sources": [],
                "reasoning_chain": "",
                "confidence_scores": {"overall": 0.5},
                "entities_analyzed": 0,
                "relationships_found": 0
            }
    
    def add_document(self, text: str, doc_type: str = "financial", **kwargs) -> Dict[str, Any]:
        """Add document to current engine"""
        if not self.is_ready():
            return {"status": "error", "message": "No active engine"}
        
        try:
            if self.current_engine_name == "lightrag":
                # LightRAG interface
                import asyncio
                return asyncio.run(self.current_engine.add_document(text, doc_type))
            elif self.current_engine_name == "lazyrag":
                # LazyRAG interface
                return self.current_engine.add_document(text, doc_type)
            else:
                return {"status": "error", "message": f"Unknown engine: {self.current_engine_name}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def add_edges_from_data(self, edge_data: List[Union[tuple, Dict[str, Any]]]) -> Dict[str, Any]:
        """Add structured edge data (LazyRAG only)"""
        if not self.is_ready():
            return {"status": "error", "message": "No active engine"}
        
        if self.current_engine_name == "lazyrag":
            try:
                return self.current_engine.add_edges_from_data(edge_data)
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "warning", "message": f"Edge addition not supported by {self.current_engine_name}"}
    
    def get_entity_context(self, entity: str) -> Dict[str, Any]:
        """Get entity context (LazyRAG only)"""
        if not self.is_ready():
            return {}
        
        if self.current_engine_name == "lazyrag":
            try:
                return self.current_engine.get_entity_context(entity)
            except Exception as e:
                print(f"Error getting entity context: {e}")
                return {}
        else:
            return {"message": f"Entity context not supported by {self.current_engine_name}"}
    
    def find_paths(self, source: str, target: str, max_hops: int = 3) -> List[Dict[str, Any]]:
        """Find paths between entities (LazyRAG only)"""
        if not self.is_ready():
            return []
        
        if self.current_engine_name == "lazyrag":
            try:
                return self.current_engine.find_paths(source, target, max_hops)
            except Exception as e:
                print(f"Error finding paths: {e}")
                return []
        else:
            return [{"message": f"Path finding not supported by {self.current_engine_name}"}]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        base_stats = {
            "current_engine": self.current_engine_name,
            "available_engines": {name: info.available for name, info in self.available_engines.items()},
            "query_history_count": len(self.query_history),
            "performance_metrics": self.performance_metrics
        }
        
        # Get engine-specific stats
        if self.is_ready():
            try:
                engine_stats = self.current_engine.get_stats()
                base_stats["engine_stats"] = engine_stats
            except Exception as e:
                base_stats["engine_stats_error"] = str(e)
        
        return base_stats
    
    def _update_performance_metrics(self, engine: str, query_time: float, success: bool):
        """Update performance metrics"""
        if engine in self.performance_metrics:
            metrics = self.performance_metrics[engine]
            metrics["queries"] += 1
            
            if success:
                metrics["total_time"] += query_time
                metrics["avg_time"] = metrics["total_time"] / metrics["queries"]
            else:
                metrics["errors"] += 1
    
    def compare_engines(self, question: str, modes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare performance of both engines on the same question.
        
        Args:
            question: Query to test
            modes: List of modes to test (default: ["hybrid"])
            
        Returns:
            Comparison results
        """
        if modes is None:
            modes = ["hybrid"]
        
        results = {}
        original_engine = self.current_engine_name
        
        # Test each available engine
        for engine_name, engine_info in self.available_engines.items():
            if not engine_info.available:
                continue
                
            results[engine_name] = {}
            
            # Switch to engine
            if self.set_engine(engine_name):
                for mode in modes:
                    try:
                        result = self.query(question, mode)
                        results[engine_name][mode] = {
                            "success": result["status"] == "success",
                            "query_time": result["query_time"],
                            "answer_length": len(result["answer"]),
                            "entities_analyzed": result.get("entities_analyzed", 0),
                            "relationships_found": result.get("relationships_found", 0),
                            "confidence": result.get("confidence_scores", {}).get("overall", 0)
                        }
                    except Exception as e:
                        results[engine_name][mode] = {
                            "success": False,
                            "error": str(e),
                            "query_time": 0
                        }
        
        # Restore original engine
        if original_engine and self.is_engine_available(original_engine):
            self.set_engine(original_engine)
        
        return {
            "question": question,
            "modes_tested": modes,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }


# Convenience function for easy initialization
def create_unified_rag(default_engine: str = "lightrag") -> ICEUnifiedRAG:
    """Create and return a unified RAG instance"""
    return ICEUnifiedRAG(default_engine=default_engine)


# Mock fallback for when neither engine is available
class MockUnifiedRAG:
    """Mock system when no engines are available"""
    
    def __init__(self):
        self.query_history = []
        self.current_engine_name = "mock"
    
    def is_ready(self):
        return True
    
    def query(self, question, mode="hybrid", **kwargs):
        return {
            "status": "success",
            "engine": "mock",
            "answer": f"Mock response for: {question}\n\nThis is a development mock system. Neither LightRAG nor LazyRAG are available.",
            "query_time": 0.1,
            "sources": [],
            "reasoning_chain": "",
            "confidence_scores": {"overall": 0.5}
        }
    
    def get_stats(self):
        return {
            "current_engine": "mock",
            "available_engines": {"lightrag": False, "lazyrag": False},
            "query_history_count": len(self.query_history)
        }
    
    def get_available_engines(self):
        return {
            "mock": RAGEngineInfo("Mock", "1.0", "Development mock system", True)
        }