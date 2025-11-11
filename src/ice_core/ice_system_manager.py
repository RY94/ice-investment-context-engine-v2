# ice_core/ice_system_manager.py
"""
ICE System Manager - Main orchestrator for Investment Context Engine
Manages all ICE components including LightRAG, Exa MCP, and graph intelligence
Provides unified session management and coordinates data flows between modules
Relevant files: ice_lightrag/ice_rag.py, ice_data_ingestion/exa_mcp_connector.py, ui_mockups/ice_ui_v17.py
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Import custom exceptions for better error reporting
try:
    from .ice_exceptions import (
        LightRAGInitializationError,
        ComponentInitializationError,
        SystemNotReadyError,
        DataIngestionError,
        QueryProcessingError
    )
except ImportError:
    # Fallback if exceptions module not available
    LightRAGInitializationError = RuntimeError
    ComponentInitializationError = RuntimeError
    SystemNotReadyError = RuntimeError
    DataIngestionError = RuntimeError
    QueryProcessingError = RuntimeError

logger = logging.getLogger(__name__)

class ICESystemManager:
    """
    Main orchestrator for all ICE Investment Context Engine components
    
    This class provides a unified interface for:
    - LightRAG document processing and querying
    - Exa MCP data ingestion and web search
    - Graph-based intelligence and relationship extraction
    - Session state management for Streamlit UI
    
    Design principles:
    - Single source of truth for all ICE functionality
    - Lazy initialization for performance
    - Graceful degradation when components unavailable
    - Clear error handling with fallback behaviors
    """
    
    def __init__(self, working_dir: str = "./ice_lightrag/storage"):
        """
        Initialize ICE System Manager
        
        Args:
            working_dir: Directory for LightRAG storage and system state
        """
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Component initialization - lazy loading for performance
        self._lightrag = None
        self._exa_connector = None
        self._graph_builder = None
        self._query_processor = None
        self._data_manager = None
        
        # System state tracking
        self.initialization_status = {
            "lightrag": False,
            "exa_connector": False,
            "graph_builder": False,
            "query_processor": False,
            "data_manager": False
        }
        
        # Error tracking for graceful degradation
        self.component_errors = {}
        
        # Performance metrics
        self.query_count = 0
        self.last_query_time = None
        
        logger.info(f"ICE System Manager initialized with working_dir: {self.working_dir}")
    
    @property
    def lightrag(self):
        """
        Lazy-loaded LightRAG instance

        Returns:
            SimpleICERAG instance

        Raises:
            RuntimeError: If LightRAG initialization fails
        """
        if self._lightrag is None:
            try:
                # Import here to avoid circular dependencies
                # Week 2 Fix: Use fully qualified path from project root
                # Week 2.5 Fix: Import from ice_rag_fixed.py (Jupyter-compatible version)
                # Use JupyterSyncWrapper for sync context (ICESystemManager is not async)
                from src.ice_lightrag.ice_rag_fixed import JupyterSyncWrapper

                self._lightrag = JupyterSyncWrapper(str(self.working_dir))

                # Note: JupyterSyncWrapper uses lazy initialization
                # It will initialize on first usage (add_document/query)
                # We verify the wrapper was created, not full readiness
                if self._lightrag is None:
                    error_msg = "Failed to create LightRAG wrapper"
                    self.component_errors["lightrag"] = error_msg
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

                self.initialization_status["lightrag"] = True
                logger.info("LightRAG wrapper created successfully (lazy initialization mode)")

            except ImportError as e:
                error_msg = f"LightRAG module not found: {str(e)}"
                self.component_errors["lightrag"] = error_msg
                logger.error(error_msg)
                raise ImportError(f"{error_msg}\nPlease run: pip install lightrag")

            except Exception as e:
                error_msg = f"LightRAG initialization failed: {str(e)}"
                self.component_errors["lightrag"] = error_msg
                logger.error(error_msg)
                raise RuntimeError(error_msg)

        return self._lightrag
    
    @property 
    def exa_connector(self):
        """
        Lazy-loaded Exa MCP connector
        
        Returns:
            ExaMCPConnector instance or None if initialization failed
        """
        if self._exa_connector is None:
            try:
                from ice_data_ingestion.exa_mcp_connector import ExaMCPConnector
                
                self._exa_connector = ExaMCPConnector()
                self.initialization_status["exa_connector"] = True
                logger.info("Exa MCP connector initialized successfully")
                
            except Exception as e:
                self.component_errors["exa_connector"] = f"Exa MCP initialization error: {str(e)}"
                logger.error(f"Failed to initialize Exa MCP connector: {e}")
                
        return self._exa_connector
    
    @property
    def graph_builder(self):
        """
        Lazy-loaded Graph Builder instance

        Returns:
            ICEGraphBuilder instance or None if initialization failed
        """
        if self._graph_builder is None:
            try:
                from .ice_graph_builder import ICEGraphBuilder

                # Initialize without lightrag to avoid circular dependency
                self._graph_builder = ICEGraphBuilder()

                # Inject lightrag instance after initialization
                if self._lightrag:
                    self._graph_builder.set_lightrag_instance(self._lightrag)

                self.initialization_status["graph_builder"] = True
                logger.info("Graph Builder initialized successfully")

            except Exception as e:
                self.component_errors["graph_builder"] = f"Graph Builder initialization error: {str(e)}"
                logger.error(f"Failed to initialize Graph Builder: {e}")

        # Ensure lightrag is injected if it becomes available later
        elif self._graph_builder and self._lightrag and not self._graph_builder.lightrag:
            self._graph_builder.set_lightrag_instance(self._lightrag)

        return self._graph_builder
    
    @property
    def query_processor(self):
        """
        Lazy-loaded Query Processor instance

        Returns:
            ICEQueryProcessor instance or None if initialization failed
        """
        if self._query_processor is None:
            try:
                from .ice_query_processor import ICEQueryProcessor

                # Initialize with None to avoid circular dependency
                self._query_processor = ICEQueryProcessor(None, None)

                # Inject dependencies after initialization
                if self._lightrag:
                    self._query_processor.lightrag = self._lightrag
                if self._graph_builder:
                    self._query_processor.graph_builder = self._graph_builder

                self.initialization_status["query_processor"] = True
                logger.info("Query Processor initialized successfully")

            except Exception as e:
                self.component_errors["query_processor"] = f"Query Processor initialization error: {str(e)}"
                logger.error(f"Failed to initialize Query Processor: {e}")

        # Ensure dependencies are injected if they become available later
        elif self._query_processor:
            if self._lightrag and not hasattr(self._query_processor, 'lightrag'):
                self._query_processor.lightrag = self._lightrag
            if self._graph_builder and not hasattr(self._query_processor, 'graph_builder'):
                self._query_processor.graph_builder = self._graph_builder

        return self._query_processor
    
    def is_ready(self) -> bool:
        """
        Check if core ICE components are ready for use

        Returns:
            True if LightRAG is available, False otherwise

        Raises:
            RuntimeError: If system is not ready with detailed error information
        """
        try:
            if self._lightrag is None:
                # Try to initialize lightrag
                _ = self.lightrag

            # With lazy initialization, just check if wrapper exists
            # Full initialization happens on first usage (add_document/query)
            if not self._lightrag:
                errors = self.component_errors.copy()
                error_msg = "ICE System not ready. Component errors:\n"
                for component, error in errors.items():
                    error_msg += f"  - {component}: {error}\n"
                raise RuntimeError(error_msg)

            return True

        except Exception as e:
            # Re-raise with additional context
            if "not ready" not in str(e).lower():
                raise RuntimeError(f"System readiness check failed: {str(e)}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status for monitoring and debugging
        
        Returns:
            Dict with component statuses, errors, and performance metrics
        """
        # Trigger lazy loading for status check
        _ = self.lightrag, self.exa_connector, self.graph_builder, self.query_processor
        
        return {
            "ready": self.is_ready(),
            "components": self.initialization_status.copy(),
            "errors": self.component_errors.copy(),
            "metrics": {
                "query_count": self.query_count,
                "last_query": self.last_query_time.isoformat() if self.last_query_time else None,
                "working_directory": str(self.working_dir)
            }
        }
    
    def query_ice(self, question: str, mode: str = "hybrid", use_graph_context: bool = False) -> Dict[str, Any]:
        """
        Main ICE query interface - combines LightRAG with graph intelligence

        Args:
            question: User's investment question
            mode: LightRAG query mode ("hybrid", "local", "global", "naive")
            use_graph_context: Whether to enhance with graph-based context (Week 3+ feature, disabled for Week 2)

        Returns:
            Dict with query results, sources, and metadata

        Note: use_graph_context=False by default for Week 2 (ICEQueryProcessor is Week 3+ feature)
        """
        if not self.is_ready():
            return {
                "status": "error",
                "message": "ICE system not ready - check LightRAG initialization",
                "errors": self.component_errors
            }
        
        # Update metrics
        self.query_count += 1
        self.last_query_time = datetime.utcnow()
        
        try:
            # Enhanced query processing if available
            if use_graph_context and self.query_processor:
                result = self.query_processor.process_enhanced_query(question, mode)
            else:
                # Fallback to basic LightRAG query
                result = self.lightrag.query(question, mode)
                
            logger.info(f"ICE query completed: mode={mode}, graph_context={use_graph_context}")
            return result
            
        except Exception as e:
            logger.error(f"ICE query failed: {e}")
            return {
                "status": "error", 
                "message": f"Query processing failed: {str(e)}"
            }
    
    def add_document(self, text: str, doc_type: str = "financial", update_graph: bool = True, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Add document to ICE knowledge base with optional graph update

        Args:
            text: Document content
            doc_type: Type of financial document
            update_graph: Whether to update graph relationships after ingestion
            file_path: Optional source file path for traceability (e.g., 'email:filename.eml')

        Returns:
            Dict with ingestion results and graph updates
        """
        if not self.is_ready():
            return {
                "status": "error",
                "message": "ICE system not ready for document ingestion"
            }

        try:
            # Add document to LightRAG with file_path for traceability
            result = self.lightrag.add_document(text, doc_type, file_path=file_path)

            # Week 2.5 Note: Graph updates disabled for now (Week 3+ feature)
            # TODO Week 3: Re-enable with correct method name or implement stub
            # if result["status"] == "success" and update_graph and self.graph_builder:
            #     graph_result = self.graph_builder.refresh_edges_from_recent_documents()
            #     result["graph_updates"] = graph_result

            logger.info(f"Document added: type={doc_type}, graph_updated={update_graph}")
            return result
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            return {
                "status": "error",
                "message": f"Document processing failed: {str(e)}"
            }
    
    def get_ticker_intelligence(self, ticker: str, analysis_depth: int = 2) -> Dict[str, Any]:
        """
        Get comprehensive ticker intelligence using ICE capabilities
        
        Args:
            ticker: Stock ticker symbol (e.g., "NVDA")
            analysis_depth: Depth of analysis (1=basic, 2=detailed, 3=comprehensive)
            
        Returns:
            Dict with ticker intelligence including KPIs, risks, themes, and causal paths
        """
        if not self.is_ready():
            return {
                "status": "error",
                "message": "ICE system not ready for ticker analysis"
            }
        
        try:
            # Multi-query analysis for comprehensive intelligence
            queries = {
                "overview": f"What are the key business fundamentals and recent developments for {ticker}?",
                "risks": f"What are the main risks and vulnerabilities facing {ticker}?",
                "kpis": f"What are the key performance indicators and metrics for {ticker}?",
                "themes": f"What are the major investment themes and trends affecting {ticker}?"
            }
            
            intelligence = {
                "ticker": ticker,
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_depth": analysis_depth
            }
            
            # Execute queries
            for query_type, question in queries.items():
                result = self.query_ice(question, mode="hybrid", use_graph_context=True)
                intelligence[query_type] = result
                
            # Add graph-based causal paths if available
            if self.graph_builder:
                paths = self.graph_builder.find_causal_paths(ticker, max_hops=analysis_depth)
                intelligence["causal_paths"] = paths
                
            logger.info(f"Ticker intelligence generated: {ticker}, depth={analysis_depth}")
            return {
                "status": "success",
                "intelligence": intelligence
            }
            
        except Exception as e:
            logger.error(f"Ticker intelligence failed for {ticker}: {e}")
            return {
                "status": "error",
                "message": f"Ticker analysis failed: {str(e)}"
            }
    
    def fetch_and_analyze_company(self, company_query: str) -> Dict[str, Any]:
        """
        Fetch latest company data and add to ICE knowledge base
        
        Args:
            company_query: Company name or ticker for data fetching
            
        Returns:
            Dict with fetch results and analysis capability
        """
        if not self.is_ready():
            return {
                "status": "error", 
                "message": "ICE system not ready for data fetching"
            }
        
        try:
            # Use LightRAG earnings fetching if available
            if hasattr(self.lightrag, 'fetch_and_add_earnings'):
                earnings_result = self.lightrag.fetch_and_add_earnings(company_query)
                
                if earnings_result["status"] == "success":
                    # Update graph with new earnings data
                    if self.graph_builder:
                        self.graph_builder.refresh_edges_from_recent_documents()
                    
                    return {
                        "status": "success",
                        "message": f"Fetched and analyzed data for {company_query}",
                        "earnings_info": earnings_result
                    }
                else:
                    return earnings_result
            else:
                return {
                    "status": "info",
                    "message": "Automatic data fetching not available - add documents manually"
                }
                
        except Exception as e:
            logger.error(f"Company data fetch failed for {company_query}: {e}")
            return {
                "status": "error",
                "message": f"Data fetching failed: {str(e)}"
            }
    
    def reset_system(self):
        """
        Reset all components for fresh initialization
        Useful for debugging and state cleanup
        """
        self._lightrag = None
        self._exa_connector = None  
        self._graph_builder = None
        self._query_processor = None
        self._data_manager = None
        
        self.initialization_status = {k: False for k in self.initialization_status}
        self.component_errors.clear()
        
        logger.info("ICE System Manager reset - components will reinitialize on next access")


# Singleton pattern for Streamlit session management
_ice_system_instance = None

def get_ice_system_manager(working_dir: str = "./ice_lightrag/storage") -> ICESystemManager:
    """
    Get singleton ICE System Manager instance for Streamlit session consistency
    
    Args:
        working_dir: Working directory for system storage
        
    Returns:
        ICE System Manager singleton instance
    """
    global _ice_system_instance
    
    if _ice_system_instance is None:
        _ice_system_instance = ICESystemManager(working_dir)
        
    return _ice_system_instance