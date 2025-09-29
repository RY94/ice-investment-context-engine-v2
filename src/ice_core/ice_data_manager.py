# ice_core/ice_data_manager.py
"""
ICE Data Manager - Orchestrates data pipeline from external sources to LightRAG
Manages Exa MCP integration, document processing, and automated knowledge base updates
Provides scheduled data ingestion and real-time portfolio monitoring capabilities  
Relevant files: ice_data_ingestion/exa_mcp_connector.py, ice_lightrag/ice_rag.py, ice_system_manager.py
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class ICEDataManager:
    """
    Data pipeline manager for ICE Investment Context Engine
    
    This class orchestrates data flow from external sources to the ICE knowledge base:
    - Exa MCP web search and company research integration
    - Automated document processing and ingestion into LightRAG
    - Real-time portfolio monitoring and alert generation
    - Background data refresh and change detection
    
    Design principles:
    - Asynchronous processing for performance
    - Error resilience with retry mechanisms  
    - Configurable data source priorities
    - Incremental updates to avoid duplication
    """
    
    def __init__(self, lightrag_instance=None, exa_connector=None, graph_builder=None):
        """
        Initialize ICE Data Manager
        
        Args:
            lightrag_instance: SimpleICERAG instance for document ingestion
            exa_connector: ExaMCPConnector for web search and research
            graph_builder: ICEGraphBuilder for relationship extraction
        """
        self.lightrag = lightrag_instance
        self.exa_connector = exa_connector
        self.graph_builder = graph_builder
        
        # Data pipeline configuration
        self.max_documents_per_batch = 10
        self.refresh_interval_minutes = 30
        self.priority_tickers = set()
        
        # Processing state tracking
        self.last_refresh = None
        self.processing_status = {
            "active": False,
            "last_batch_size": 0,
            "last_batch_time": None,
            "errors": []
        }
        
        # Document deduplication cache  
        self.processed_documents = set()
        self.document_cache_file = Path("storage/cache/processed_documents.json")
        self._load_document_cache()
        
        logger.info("ICE Data Manager initialized")
    
    def _load_document_cache(self):
        """Load previously processed document cache for deduplication"""
        try:
            if self.document_cache_file.exists():
                with open(self.document_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.processed_documents = set(cache_data.get('processed_urls', []))
                logger.info(f"Loaded {len(self.processed_documents)} processed documents from cache")
        except Exception as e:
            logger.warning(f"Could not load document cache: {e}")
    
    def _save_document_cache(self):
        """Save processed document cache to disk"""
        try:
            self.document_cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_data = {
                'processed_urls': list(self.processed_documents),
                'last_updated': datetime.utcnow().isoformat()
            }
            with open(self.document_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save document cache: {e}")
    
    def add_priority_ticker(self, ticker: str):
        """
        Add ticker to priority monitoring list
        
        Args:
            ticker: Stock ticker to monitor (e.g., "NVDA")
        """
        self.priority_tickers.add(ticker.upper())
        logger.info(f"Added {ticker} to priority monitoring list")
    
    def remove_priority_ticker(self, ticker: str):
        """
        Remove ticker from priority monitoring list
        
        Args:
            ticker: Stock ticker to remove from monitoring
        """
        self.priority_tickers.discard(ticker.upper())
        logger.info(f"Removed {ticker} from priority monitoring list")
    
    async def fetch_and_ingest_company_data(self, company_query: str, 
                                          max_documents: int = 5) -> Dict[str, Any]:
        """
        Fetch latest company data and ingest into ICE knowledge base
        
        Args:
            company_query: Company name or ticker symbol
            max_documents: Maximum number of documents to process
            
        Returns:
            Dict with ingestion results and processed document count
        """
        if not self.lightrag or not self.lightrag.is_ready():
            return {
                "status": "error",
                "message": "LightRAG not available for data ingestion"
            }
        
        self.processing_status["active"] = True
        ingestion_results = {
            "status": "success",
            "company": company_query,
            "documents_processed": 0,
            "documents_added": 0,
            "errors": []
        }
        
        try:
            # Method 1: Try LightRAG earnings fetching first
            if hasattr(self.lightrag, 'fetch_and_add_earnings'):
                earnings_result = self.lightrag.fetch_and_add_earnings(company_query)
                if earnings_result["status"] == "success":
                    ingestion_results["documents_processed"] += 1
                    ingestion_results["documents_added"] += 1
                    ingestion_results["earnings_data"] = earnings_result
            
            # Method 2: Use Exa MCP for additional research if available
            if self.exa_connector:
                try:
                    web_results = await self._fetch_company_research_via_exa(
                        company_query, max_documents - 1
                    )
                    
                    for doc_result in web_results:
                        ingestion_results["documents_processed"] += 1
                        
                        # Check for duplicates
                        doc_id = doc_result.get("url", f"doc_{len(self.processed_documents)}")
                        if doc_id in self.processed_documents:
                            continue
                        
                        # Ingest document into LightRAG
                        ingest_result = self.lightrag.add_document(
                            doc_result["text"],
                            doc_result.get("doc_type", "web_research")
                        )
                        
                        if ingest_result["status"] == "success":
                            ingestion_results["documents_added"] += 1
                            self.processed_documents.add(doc_id)
                        else:
                            ingestion_results["errors"].append(
                                f"Failed to ingest {doc_id}: {ingest_result['message']}"
                            )
                            
                except Exception as e:
                    ingestion_results["errors"].append(f"Exa MCP error: {str(e)}")
            
            # Update graph relationships if graph builder available
            if self.graph_builder and ingestion_results["documents_added"] > 0:
                try:
                    self.graph_builder.refresh_edges_from_recent_documents()
                    ingestion_results["graph_updated"] = True
                except Exception as e:
                    ingestion_results["errors"].append(f"Graph update error: {str(e)}")
            
            # Save updated document cache
            self._save_document_cache()
            
            # Update processing status
            self.processing_status.update({
                "active": False,
                "last_batch_size": ingestion_results["documents_processed"],
                "last_batch_time": datetime.utcnow()
            })
            
            logger.info(f"Company data ingestion completed: {company_query}, "
                       f"processed {ingestion_results['documents_processed']} docs")
            
            return ingestion_results
            
        except Exception as e:
            self.processing_status["active"] = False
            logger.error(f"Company data ingestion failed for {company_query}: {e}")
            return {
                "status": "error", 
                "message": f"Data ingestion failed: {str(e)}"
            }
    
    async def _fetch_company_research_via_exa(self, company_query: str, 
                                            max_docs: int = 5) -> List[Dict]:
        """
        Fetch company research documents via Exa MCP connector
        
        Args:
            company_query: Company name or ticker
            max_docs: Maximum documents to fetch
            
        Returns:
            List of document dictionaries with text and metadata
        """
        documents = []
        
        try:
            # Import here to avoid circular dependencies
            from ice_data_ingestion.exa_mcp_connector import ExaSearchQuery, ExaSearchType
            
            # Research query for comprehensive company analysis
            research_query = ExaSearchQuery(
                query=f"{company_query} earnings financial analysis risk factors",
                search_type=ExaSearchType.COMPANY_RESEARCH,
                num_results=max_docs,
                use_autoprompt=True,
                include_text=True,
                include_highlights=True
            )
            
            # Execute search via Exa MCP
            search_results = await self.exa_connector.search(research_query)
            
            for result in search_results.get("results", [])[:max_docs]:
                if result.get("text") and len(result["text"]) > 100:  # Meaningful content
                    documents.append({
                        "text": result["text"],
                        "title": result.get("title", "Unknown"),
                        "url": result.get("url", ""),
                        "doc_type": "exa_research",
                        "published_date": result.get("published_date"),
                        "score": result.get("score", 0.5)
                    })
                    
        except Exception as e:
            logger.error(f"Exa MCP research failed for {company_query}: {e}")
        
        return documents
    
    async def batch_refresh_portfolio_data(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Refresh data for multiple portfolio tickers in batch
        
        Args:
            tickers: List of ticker symbols to refresh
            
        Returns:
            Dict with batch processing results
        """
        batch_results = {
            "status": "success",
            "tickers_processed": 0,
            "total_documents": 0,
            "ticker_results": {},
            "errors": []
        }
        
        self.processing_status["active"] = True
        
        try:
            # Process tickers in batches to avoid API rate limits
            batch_size = 3
            ticker_batches = [tickers[i:i+batch_size] for i in range(0, len(tickers), batch_size)]
            
            for batch in ticker_batches:
                # Process batch concurrently
                batch_tasks = [
                    self.fetch_and_ingest_company_data(ticker, max_documents=3) 
                    for ticker in batch
                ]
                
                batch_task_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for ticker, result in zip(batch, batch_task_results):
                    if isinstance(result, Exception):
                        batch_results["errors"].append(f"{ticker}: {str(result)}")
                    else:
                        batch_results["ticker_results"][ticker] = result
                        batch_results["tickers_processed"] += 1
                        batch_results["total_documents"] += result.get("documents_processed", 0)
                
                # Brief pause between batches to respect rate limits
                await asyncio.sleep(2)
            
            self.last_refresh = datetime.utcnow()
            logger.info(f"Batch refresh completed: {len(tickers)} tickers, "
                       f"{batch_results['total_documents']} total documents")
            
        except Exception as e:
            batch_results["status"] = "error"
            batch_results["errors"].append(f"Batch processing error: {str(e)}")
            logger.error(f"Batch portfolio refresh failed: {e}")
        
        finally:
            self.processing_status["active"] = False
        
        return batch_results
    
    def start_background_monitoring(self, refresh_interval_minutes: int = 30):
        """
        Start background monitoring for priority tickers
        
        Args:
            refresh_interval_minutes: How often to refresh data
        """
        self.refresh_interval_minutes = refresh_interval_minutes
        
        # This would typically be implemented with a proper background task scheduler
        # For now, provide the interface for future implementation
        logger.info(f"Background monitoring configured for {len(self.priority_tickers)} tickers "
                   f"with {refresh_interval_minutes}-minute refresh interval")
        
        # TODO: Implement actual background task scheduling
        # Could use APScheduler or similar for production deployment
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        Get current data processing status and metrics
        
        Returns:
            Dict with processing status and performance metrics
        """
        return {
            "active_processing": self.processing_status["active"],
            "priority_tickers": list(self.priority_tickers),
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "processed_document_count": len(self.processed_documents),
            "recent_batch": {
                "size": self.processing_status["last_batch_size"],
                "time": self.processing_status["last_batch_time"].isoformat() 
                       if self.processing_status["last_batch_time"] else None
            },
            "error_count": len(self.processing_status["errors"]),
            "recent_errors": self.processing_status["errors"][-5:]  # Last 5 errors
        }
    
    def clear_document_cache(self):
        """Clear processed document cache for fresh data ingestion"""
        self.processed_documents.clear()
        try:
            if self.document_cache_file.exists():
                self.document_cache_file.unlink()
            logger.info("Document cache cleared")
        except Exception as e:
            logger.warning(f"Could not clear document cache file: {e}")
    
    async def detect_portfolio_changes(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Detect significant changes in portfolio companies since last refresh
        
        Args:
            tickers: List of tickers to analyze for changes
            
        Returns:
            Dict with detected changes and alert-worthy events
        """
        if not self.lightrag or not self.lightrag.is_ready():
            return {"status": "error", "message": "LightRAG not available"}
        
        change_analysis = {
            "status": "success",
            "analysis_time": datetime.utcnow().isoformat(),
            "tickers_analyzed": len(tickers),
            "significant_changes": [],
            "alerts": []
        }
        
        try:
            # For each ticker, query recent changes
            for ticker in tickers[:5]:  # Limit to 5 for performance
                change_query = f"What are the most recent significant changes or developments for {ticker}?"
                
                result = self.lightrag.query(change_query, mode="hybrid")
                
                if result["status"] == "success" and result.get("result"):
                    # Simple change detection based on key risk/opportunity terms
                    response_text = result["result"].lower()
                    
                    alert_keywords = [
                        "earnings miss", "revenue decline", "guidance cut", "lawsuit",
                        "regulatory", "investigation", "bankruptcy", "acquisition",
                        "merger", "leadership change", "warning", "risk"
                    ]
                    
                    opportunity_keywords = [
                        "earnings beat", "revenue growth", "guidance raise", "contract win",
                        "partnership", "expansion", "breakthrough", "approval", "launch"
                    ]
                    
                    # Check for alert-worthy content
                    alerts_found = [kw for kw in alert_keywords if kw in response_text]
                    opportunities_found = [kw for kw in opportunity_keywords if kw in response_text]
                    
                    if alerts_found or opportunities_found:
                        change_analysis["significant_changes"].append({
                            "ticker": ticker,
                            "alert_keywords": alerts_found,
                            "opportunity_keywords": opportunities_found,
                            "summary": result["result"][:200] + "..."
                        })
                        
                        if alerts_found:
                            change_analysis["alerts"].append({
                                "ticker": ticker,
                                "type": "risk",
                                "keywords": alerts_found,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        
                        if opportunities_found:
                            change_analysis["alerts"].append({
                                "ticker": ticker,
                                "type": "opportunity", 
                                "keywords": opportunities_found,
                                "timestamp": datetime.utcnow().isoformat()
                            })
            
        except Exception as e:
            logger.error(f"Portfolio change detection failed: {e}")
            change_analysis["status"] = "error"
            change_analysis["error"] = str(e)
        
        return change_analysis