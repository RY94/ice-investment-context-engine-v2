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
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone

# Add project root to path for imports
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import SecureConfig for encrypted API key management (Week 3 integration)
from ice_data_ingestion.secure_config import get_secure_config

# Import production DataIngester with email pipeline (Phase 2.6.1)
from updated_architectures.implementation.data_ingestion import DataIngester as ProductionDataIngester

# Import ICEConfig with docling toggles and confidence centralization (Phase 2.8)
from updated_architectures.implementation.config import (
    ICEConfig,
    SOURCE_CONFIDENCE_MULTIPLIERS,
    get_confidence,
    get_source_confidence
)

# Import ingestion manifest for deduplication
from src.ice_core.ingestion_manifest import IngestionManifest

# Import relationship extractor for cross-company intelligence (Refinement #3)
from src.ice_core.relationship_extractor import RelationshipExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Custom exceptions for batch processing
class BatchProcessingError(Exception):
    """Raised when batch processing exceeds failure threshold"""
    def __init__(self, message: str, failed_count: int, total_count: int, threshold: float):
        self.message = message
        self.failed_count = failed_count
        self.total_count = total_count
        self.threshold = threshold
        self.failure_rate = failed_count / total_count if total_count > 0 else 0
        super().__init__(self.message)


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

            # Refinement #3: Initialize relationship extractor for multi-hop intelligence
            if self.config.relationship_extraction_enabled:
                self.relationship_extractor = RelationshipExtractor()
                self.relationship_cache = {}  # content_hash -> relationships

                # Source confidence multipliers (centralized in config.py, Phase 2.8)
                self.SOURCE_CONFIDENCE = SOURCE_CONFIDENCE_MULTIPLIERS
                logger.info("✅ Relationship extractor initialized for cross-company intelligence")
            else:
                self.relationship_extractor = None
                logger.info("Relationship extraction disabled")

            # Phase 2.7B Option 1: Initialize event extractor for event detection
            if self.config.event_extraction_enabled:
                try:
                    from src.ice_core.event_extractor import EventExtractor
                    self.event_extractor = EventExtractor()
                    self.event_cache = {}  # content_hash -> formatted events (separate from relationships)
                    logger.info("✅ Event extractor initialized (15 event types)")
                except Exception as e:
                    logger.warning(f"Event extractor disabled: {e}")
                    self.event_extractor = None
                    self.event_cache = {}
            else:
                self.event_extractor = None
                self.event_cache = {}

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

    def _extract_document_title(self, doc_content: str, source_type: str) -> str:
        """Extract document title based on source type using pattern matching"""
        import re

        patterns = {
            "Email": r"Subject:\s*(.+)",
            "SEC Filing": r"Form Type:\s*(.+)",
            "News": r"News Article:\s*(.+)",
            "Financial API": r"Company Profile:\s*(.+)"
        }

        pattern = patterns.get(source_type)
        if pattern:
            match = re.search(pattern, doc_content, re.MULTILINE)
            if match:
                return match.group(1).strip()[:70]

        # Fallback: first non-empty line
        for line in doc_content.split('\n')[:5]:
            line = line.strip()
            if line and not line.startswith('[') and not line.startswith('Symbol:'):
                return line[:70]

        return "Untitled"

    def _print_document_progress(self, doc_index: int, total_docs: int, doc_dict: Dict[str, Any], symbol: str = ""):
        """
        Print visually distinct progress for each document being processed

        Args:
            doc_index: Current document index (1-based)
            total_docs: Total number of documents
            doc_dict: Full document dictionary with content, file_path, source fields
            symbol: Ticker symbol being processed
        """
        # 4-Tier Source Detection (Robust metadata-first approach)
        # Tier 1: file_path field (most reliable, O(1))
        # Tier 2: source field (secondary metadata)
        # Tier 3: content patterns (fallback for edge cases)
        # Tier 4: legacy checks (backwards compatibility)

        source_type = "Unknown"
        source_icon = "📄"

        # TIER 1: Check file_path field (most reliable identifier)
        file_path = doc_dict.get('file_path', '') or ''  # Handle None
        if 'sec_edgar:' in file_path or 'sec:' in file_path:
            source_type = "SEC Filing"
            source_icon = "📑"
        elif 'email:' in file_path:
            source_type = "Email"
            source_icon = "📧"
        elif 'newsapi:' in file_path or 'news:' in file_path:
            source_type = "News"
            source_icon = "📰"
        elif 'finnhub:' in file_path:
            source_type = "News (Finnhub)"
            source_icon = "📰"
        elif 'marketaux:' in file_path:
            source_type = "News (MarketAux)"
            source_icon = "📰"
        elif 'benzinga:' in file_path:
            source_type = "News (Benzinga)"
            source_icon = "📰"
        elif 'yahoo:' in file_path:
            # Detect specific Yahoo Finance category from file_path suffix
            if '_market_' in file_path:
                source_type = "Yahoo Finance (Market)"
                source_icon = "📈"
            elif '_analyst_' in file_path:
                source_type = "Yahoo Finance (Analyst)"
                source_icon = "📊"
            elif '_holdings_' in file_path:
                source_type = "Yahoo Finance (Holdings)"
                source_icon = "🏦"
            elif '_financials_' in file_path:
                source_type = "Yahoo Finance (Financials)"
                source_icon = "📑"
            elif '_earnings_' in file_path:
                source_type = "Yahoo Finance (Earnings)"
                source_icon = "💰"
            else:
                source_type = "Yahoo Finance"
                source_icon = "📈"
        elif 'fmp:' in file_path or 'alpha_vantage:' in file_path or 'polygon:' in file_path:
            source_type = "Financial API"
            source_icon = "💹"
        elif 'exa_' in file_path:
            source_type = "Research"
            source_icon = "🔬"

        # TIER 2: Check source field (secondary metadata)
        elif doc_dict.get('source') == 'sec_edgar':
            source_type = "SEC Filing"
            source_icon = "📑"
        elif doc_dict.get('source') == 'email':
            source_type = "Email"
            source_icon = "📧"
        elif doc_dict.get('source') in ['newsapi', 'benzinga', 'finnhub', 'marketaux', 'news']:
            source_type = "News"
            source_icon = "📰"
        elif doc_dict.get('source') == 'yahoo_finance':
            source_type = "Yahoo Finance"
            source_icon = "📈"
        elif doc_dict.get('source') in ['fmp', 'alpha_vantage', 'polygon']:
            source_type = "Financial API"
            source_icon = "💹"
        elif doc_dict.get('source') in ['exa_company', 'exa_competitors']:
            source_type = "Research"
            source_icon = "🔬"

        # TIER 3: Check content patterns (fallback for edge cases)
        else:
            content = doc_dict.get('content', '')
            if "SEC Form" in content or "Form 4" in content or "Form 144" in content or "# 144:" in content:
                source_type = "SEC Filing"
                source_icon = "📑"
            elif "[SOURCE_EMAIL:" in content:
                source_type = "Email"
                source_icon = "📧"
            elif "News Article:" in content or "[SOURCE_NEWS" in content:
                source_type = "News"
                source_icon = "📰"
            elif "Company Profile:" in content or "Company Overview:" in content or "Company Details:" in content:
                source_type = "Financial API"
                source_icon = "💹"

            # TIER 4: Legacy checks (backwards compatibility)
            elif "SEC EDGAR Filing" in content or "[SOURCE_SEC" in content:
                source_type = "SEC Filing"
                source_icon = "📑"

        # Log error if source is Unknown (indicates bug in metadata pipeline)
        if source_type == "Unknown":
            content_preview = doc_dict.get('content', '')[:100]
            logger.error(f"❌ BUG: Document missing source attribution. "
                        f"file_path={file_path}, source={doc_dict.get('source')}, "
                        f"content={content_preview}")

        # Extract content for title extraction
        doc_content = doc_dict.get('content', '')

        # Extract title using helper method
        title = self._extract_document_title(doc_content, source_type)

        # Visual box formatting
        box_width = 80
        print(f"\n{'┏' + '━' * (box_width - 2) + '┓'}")
        print(f"┃ {source_icon} DOCUMENT {doc_index}/{total_docs}{' ' * (box_width - len(f'DOCUMENT {doc_index}/{total_docs}') - 6)}┃")
        print(f"┃ Source: {source_type:<{box_width - 11}}┃")
        if symbol:
            print(f"┃ Symbol: {symbol:<{box_width - 11}}┃")
        if title:
            print(f"┃ Title: {title:<{box_width - 11}}┃")
        print(f"{'┗' + '━' * (box_width - 2) + '┛'}")

    def add_documents_batch(self, documents: List[Union[str, Dict[str, str]]],
                          max_failure_rate: float = 0.10) -> Dict[str, Any]:
        """
        Batch document processing via ICESystemManager with failure threshold

        Args:
            documents: List of document strings OR {"content": str, "type": str} dictionaries
            max_failure_rate: Maximum acceptable failure rate (default: 0.10 = 10%)
                            Batch processing stops if failure rate exceeds this threshold

        Returns:
            Batch processing results with graceful degradation

        Raises:
            BatchProcessingError: When failure rate exceeds max_failure_rate
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
            total_docs = len(documents)  # Cache count before loop to prevent inconsistency

            for i, doc in enumerate(documents):
                try:
                    # Handle both string documents and dict documents
                    if isinstance(doc, str):
                        # CRITICAL: Plain string documents violate 100% source attribution requirement
                        # Reject instead of logging to enforce data quality
                        raise ValueError(
                            f"Document {i+1} rejected: plain string format has no source attribution. "
                            f"All documents must be dicts with 'file_path' or 'source' field for traceability."
                        )
                    else:
                        content = doc.get('content', '')
                        doc_type = doc.get('type', 'financial')
                        symbol = doc.get('symbol', '')
                        file_path = doc.get('file_path', None)  # Extract file_path for traceability

                        # CRITICAL: Source attribution is REQUIRED by architecture (ARCHITECTURE.md:106-109)
                        if not file_path:
                            source = doc.get('source', 'unknown')

                            # Defensive fallback: Use source field if available
                            if source and source != 'unknown':
                                file_path = f"{source}:doc_{i}"
                                logger.warning(f"⚠️ Document {i+1} missing file_path, using fallback: {file_path}")
                            else:
                                # No file_path AND no valid source = reject document
                                raise ValueError(
                                    f"Document {i+1} rejected: missing both 'file_path' and 'source'. "
                                    f"100% source attribution required (ARCHITECTURE.md:106-109). "
                                    f"type={doc_type}, symbol={symbol}"
                                )

                    # Refinement #3: Enhance document with cross-company relationships
                    # Extract ALL 7 relationship types (RELATED_TO, HOLDS, EMPLOYED_BY, etc.)
                    # Source confidence weighting: SEC 1.0x, news 0.75x, email 0.70x
                    # Enables multi-hop intelligence (e.g., TSMC → NVDA → Hyperscalers → REITs)
                    if self.config.relationship_extraction_enabled and self.relationship_extractor:
                        doc = self._enhance_with_relationships(doc)
                        content = doc.get('content', content)  # Get enhanced content

                    # Phase 2.7B Option 1: Enhance document with event detection
                    # Extract 15 event types (earnings, M&A, management, scandals, etc.)
                    # Pattern-based extraction with confidence filtering (default: 0.8 threshold)
                    # Events stored in separate cache to avoid collision with relationships
                    if self.config.event_extraction_enabled and self.event_extractor:
                        doc = self._enhance_with_events(doc)
                        content = doc.get('content', content)  # Get enhanced content

                    # Progress indicator: REMOVED to fix duplicate display bug
                    # Progress is now shown at ingestion level (ingest_historical_data)
                    # before calling this batch function, to avoid showing each doc 2-3 times
                    # self._print_document_progress(
                    #     doc_index=i+1,
                    #     total_docs=total_docs,
                    #     doc_content=content,
                    #     symbol=symbol
                    # )

                    result = self._system_manager.add_document(content, doc_type=doc_type, file_path=file_path)

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

                        # Check failure threshold after adding to errors
                        failure_rate = len(errors) / total_docs
                        if failure_rate > max_failure_rate:
                            logger.error(f"🔴 Batch processing stopped: failure rate {failure_rate:.2%} exceeds threshold {max_failure_rate:.2%}")
                            raise BatchProcessingError(
                                f"Batch processing failure rate ({failure_rate:.2%}) exceeded threshold ({max_failure_rate:.2%})",
                                failed_count=len(errors),
                                total_count=total_docs,
                                threshold=max_failure_rate
                            )

                except BatchProcessingError:
                    # Re-raise BatchProcessingError to stop the batch
                    raise
                except Exception as e:
                    errors.append({
                        'index': i,
                        'error': str(e)
                    })

                    # Check failure threshold after exception
                    failure_rate = len(errors) / total_docs
                    if failure_rate > max_failure_rate:
                        logger.error(f"🔴 Batch processing stopped: failure rate {failure_rate:.2%} exceeds threshold {max_failure_rate:.2%}")
                        raise BatchProcessingError(
                            f"Batch processing failure rate ({failure_rate:.2%}) exceeded threshold ({max_failure_rate:.2%})",
                            failed_count=len(errors),
                            total_count=total_docs,
                            threshold=max_failure_rate
                        )

            logger.info(f"Batch processing completed: {len(results)} successful, {len(errors)} failed")

            return {
                'status': 'success' if len(results) > 0 else 'error',
                'successful': len(results),
                'failed': len(errors),
                'total': len(documents),
                'results': results,
                'errors': errors
            }

        except BatchProcessingError as e:
            # Batch stopped due to failure threshold - provide detailed error info
            logger.error(f"Batch processing exceeded failure threshold: {e}")
            return {
                "status": "error",
                "message": str(e),
                "error_type": "failure_threshold_exceeded",
                "failed_count": e.failed_count,
                "total_count": e.total_count,
                "failure_rate": e.failure_rate,
                "threshold": e.threshold,
                "successful": len(results),
                "results": results,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {"status": "error", "message": str(e)}

    def query(self, question: str, mode: str = 'hybrid') -> Dict[str, Any]:
        """
        Query the knowledge base via ICESystemManager with temporal enhancement routing.

        Args:
            question: Investment question to analyze
            mode: LightRAG query mode (naive, local, global, hybrid, mix, kg)

        Returns:
            Query results with answer and metadata, includes graceful degradation

        Note:
            If parent ICESimplified instance is available, routes through query_with_router()
            which provides temporal enhancement (freshness scoring, date filtering, composite ranking).
            Otherwise falls back to basic LightRAG query.
        """
        if not self.is_ready():
            status = self.get_system_status()
            return {
                "status": "error",
                "message": "ICE not ready - check system status",
                "system_status": status
            }

        try:
            # Route through temporal-enhanced query layer if parent is available
            # This enables freshness scoring, date filtering, and composite ranking
            if hasattr(self, '_parent') and self._parent and hasattr(self._parent, 'query_with_router'):
                logger.info(f"Routing query through temporal enhancement layer")
                result = self._parent.query_with_router(question, mode=mode)
                logger.info(f"Temporal query completed: {len(question)} chars, mode: {mode}")
                return result

            # Fallback to basic LightRAG query (no temporal features)
            # Week 2: ICEQueryProcessor is Week 3+ feature, disable for now
            result = self._system_manager.query_ice(question, mode=mode, use_graph_context=False)
            logger.info(f"Query completed (basic): {len(question)} chars, mode: {mode}")
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

    # ========== REFINEMENT #3: RELATIONSHIP EXTRACTION METHODS (ICECore) ==========

    def _enhance_with_relationships(self, doc: Dict) -> Dict:
        """
        Extract ALL relationships from ANY document and enhance content.

        Applies universal relationship extraction with source-based confidence weighting.
        Relationships appended to document content for LightRAG natural parsing.

        Args:
            doc: Document dict with 'content', 'file_path', 'source' fields

        Returns:
            Enhanced document with relationships appended to content
        """
        if not self.relationship_extractor:
            return doc  # Extraction disabled

        # Graceful handling: If doc is string, return unchanged
        if isinstance(doc, str):
            return doc

        # Graceful handling: If doc is not a dict, return unchanged
        if not isinstance(doc, dict):
            return doc

        try:
            # Content-based caching for deduplication
            content = doc.get('content', '')
            if not content:
                return doc

            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Check cache first
            if content_hash in self.relationship_cache:
                relationships = self.relationship_cache[content_hash]
            else:
                # Extract entities (or use fallback)
                entities = self._ensure_entities(doc)

                # Extract ALL 7 relationship types
                # FIXED: Add document_id for provenance tracking (was missing)
                relationships = self.relationship_extractor.extract_relationships(
                    text=content,
                    entities=entities,
                    document_id=doc.get('file_path', 'unknown')
                )

                # Apply source confidence weighting
                source_type = self._detect_source_type(doc)
                confidence_multiplier = self.SOURCE_CONFIDENCE.get(source_type, 0.5)

                # Apply confidence weighting + quantification boost
                for rel in relationships:
                    base_confidence = getattr(rel, 'confidence', 0.5)
                    rel.confidence = base_confidence * confidence_multiplier

                    # Boost confidence for quantified relationships (+0.15)
                    if self._is_quantified(rel):
                        rel.confidence = min(1.0, rel.confidence + 0.15)

                # Filter by threshold
                threshold = self.config.relationship_confidence_threshold
                relationships = [r for r in relationships if r.confidence >= threshold]

                # Limit relationships per document
                max_rels = self.config.max_relationships_per_doc
                relationships = relationships[:max_rels]

                # Cache (FIFO eviction if full)
                if len(self.relationship_cache) >= self.config.relationship_cache_size:
                    # Remove oldest entry
                    self.relationship_cache.pop(next(iter(self.relationship_cache)))
                self.relationship_cache[content_hash] = relationships

            # Format and append relationships to content
            if relationships:
                formatted_rels = self._format_relationships(relationships)
                doc['content'] = content + "\n\n" + formatted_rels

            return doc

        except Exception as e:
            logger.warning(f"Relationship extraction failed: {e}, returning original document")
            return doc  # Graceful degradation

    def _ensure_entities(self, doc: Dict) -> List[Dict[str, Any]]:
        """
        Get entities from document or extract basic ones as fallback.

        Args:
            doc: Document dict

        Returns:
            List of entity dicts with 'text' and 'type' keys (required by RelationshipExtractor)
        """
        entities = doc.get('entities', [])

        # Normalize entities to dict format if provided as strings
        if entities:
            if isinstance(entities[0], str):
                # Convert ['NVDA', 'AMD'] → [{'text': 'NVDA', 'type': 'COMPANY'}, ...]
                return [{'text': e, 'type': 'COMPANY'} for e in entities]
            else:
                # Already dict format
                return entities

        # Fallback: Extract basic entities using regex
        content = doc.get('content', '')

        # Pattern 1: Ticker symbols (2-5 uppercase letters)
        tickers = re.findall(r'\b[A-Z]{2,5}\b', content)

        # Pattern 2: Company names (Capitalized Words, 2-4 words)
        company_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b', content)

        # Combine and deduplicate
        entities_list = list(set(tickers + company_names))[:50]

        # Convert to dict format required by RelationshipExtractor
        return [{'text': e, 'type': 'COMPANY'} for e in entities_list]

    def _detect_source_type(self, doc: Dict) -> str:
        """
        Detect document source for confidence weighting.

        Args:
            doc: Document dict with 'file_path' or 'source' fields

        Returns:
            Source type string (e.g., 'sec_edgar', 'newsapi', 'email')
        """
        file_path = doc.get('file_path', '').lower()
        source = doc.get('source', '').lower()

        # Pattern matching on file_path
        if 'sec_edgar' in file_path or 'sec_' in file_path:
            return 'sec_edgar'
        elif 'sec_facts' in file_path or 'xbrl' in file_path:
            return 'sec_facts'
        elif 'newsapi' in file_path:
            return 'newsapi'
        elif 'finnhub' in file_path:
            return 'finnhub'
        elif 'marketaux' in file_path:
            return 'marketaux'
        elif 'benzinga' in file_path:
            return 'benzinga'
        elif 'yahoo' in file_path:
            return 'yahoo'
        elif 'email' in file_path:
            return 'email'
        elif 'exa' in file_path:
            return 'exa'

        # Fallback to source field
        if 'sec' in source:
            return 'sec_edgar'
        elif 'news' in source:
            return 'newsapi'
        elif 'email' in source:
            return 'email'
        elif 'yahoo' in source:
            return 'yahoo'

        return 'unknown'

    def _is_quantified(self, relationship) -> bool:
        """
        Check if relationship has quantification (percentages, amounts).

        FIXED: Check relationship.attributes dict (not object attributes).
        Relationship dataclass stores quantification in attributes: Dict[str, Any].

        Args:
            relationship: Relationship object

        Returns:
            True if quantified (has percentage, amount, value, count, revenue in attributes)
        """
        if hasattr(relationship, 'attributes') and isinstance(relationship.attributes, dict):
            attrs = relationship.attributes
            return any(k in attrs and attrs[k] is not None
                       for k in ['percentage', 'amount', 'value', 'count', 'revenue'])
        return False

    def _format_relationships(self, relationships) -> str:
        """
        Format relationships for LightRAG natural parsing.

        Args:
            relationships: List of relationship objects

        Returns:
            Formatted string preserving directionality and confidence
        """
        formatted_lines = []
        formatted_lines.append("Cross-Company Relationships:")

        for rel in relationships:
            # FIXED: Use correct Relationship dataclass attributes
            # (source, target, context) not (source_entity, target_entity, description)
            source = getattr(rel, 'source', '')
            target = getattr(rel, 'target', '')
            rel_type = getattr(rel, 'relationship_type', 'RELATED_TO')
            confidence = getattr(rel, 'confidence', 0.5)
            context = getattr(rel, 'context', '')

            # Format: "source RELATIONSHIP_TYPE target (confidence: X.XX) [context]"
            line = f"- {source} {rel_type} {target} (confidence: {confidence:.2f})"
            if context:
                line += f" [{context}]"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _enhance_with_events(self, doc: Dict) -> Dict:
        """
        Extract and append events to document content (Phase 2.7B Option 1).
        Follows same pattern as _enhance_with_relationships().

        Args:
            doc: Document dictionary with content, ticker, file_path

        Returns:
            Enhanced document with events appended to content
        """
        try:
            content = doc.get('content', '')
            if not content or len(content) < 50:
                return doc  # Skip very short documents

            # Content-based caching (separate key prefix from relationships)
            import hashlib
            content_hash = f"event_{hashlib.sha256(content.encode()).hexdigest()}"

            if content_hash in self.event_cache:
                # Cache hit - instant return
                doc['content'] = content + self.event_cache[content_hash]
                return doc

            # Extract events (EventExtractor is self-contained, no entities needed)
            events = self.event_extractor.extract_events(
                document=content,
                ticker=doc.get('ticker'),
                document_date=None,  # Let extractor parse dates from content
                source_id=doc.get('file_path', 'unknown')
            )

            # Filter by confidence threshold
            high_conf_events = [
                e for e in events
                if e.confidence >= self.config.event_confidence_threshold
            ]

            # Limit to prevent noise
            high_conf_events = high_conf_events[:self.config.max_events_per_doc]

            if not high_conf_events:
                return doc  # No events to add

            # Phase 2.7B Option 5: Persist events to Signal Store for fast calendar queries
            # This enables "When is next earnings?" queries via SQL (<100ms)
            try:
                # Get signal_store via parent reference (ICECore has _parent pointing to ICESimplified)
                signal_store = None
                if hasattr(self, '_parent') and hasattr(self._parent, 'ingester'):
                    signal_store = getattr(self._parent.ingester, 'signal_store', None)
                elif hasattr(self, 'ingester'):
                    signal_store = getattr(self.ingester, 'signal_store', None)

                if signal_store:
                    from datetime import datetime as dt
                    event_dicts = []
                    for event in high_conf_events:
                        # Map EventNode to calendar_events schema
                        event_dicts.append({
                            'ticker': event.ticker,
                            'event_type': event.type.value if hasattr(event.type, 'value') else str(event.type),
                            'event_date': event.date.strftime('%Y-%m-%d') if event.date else dt.now().strftime('%Y-%m-%d'),
                            'event_value': event.magnitude,  # Map magnitude to event_value
                            'is_future': 1 if event.date and event.date > dt.now() else 0,
                            'source_document_id': event.source_document_id or doc.get('file_path', 'unknown')
                        })
                    if event_dicts:
                        inserted = signal_store.insert_calendar_events_batch(event_dicts)
                        logger.debug(f"[Option5] Persisted {inserted} events to Signal Store calendar_events")
            except Exception as e:
                logger.debug(f"[Option5] Signal Store event persistence failed (non-fatal): {e}")

            # Format for LightRAG
            formatted_events = self._format_events(high_conf_events)

            # Cache formatted result
            self.event_cache[content_hash] = formatted_events
            doc['content'] = content + formatted_events

            # FIFO cache eviction
            if len(self.event_cache) > self.config.event_cache_size:
                self.event_cache.pop(next(iter(self.event_cache)))

            return doc

        except Exception as e:
            logger.debug(f"Event extraction failed: {e}")
            return doc  # Graceful degradation - return original document

    def _format_events(self, events: List) -> str:
        """
        Format events for LightRAG natural parsing.
        Follows same pattern as _format_relationships().

        Args:
            events: List of EventNode objects

        Returns:
            Formatted string with event details
        """
        if not events:
            return ""

        formatted_lines = ["\n\nKey Events:"]

        for event in events:
            # Build event line with available attributes
            # FIXED: Use event.type (not event.event_type) - EventNode dataclass attr
            line = f"- {event.type.value}"

            # Add ticker if available
            if hasattr(event, 'ticker') and event.ticker:
                line += f" ({event.ticker})"

            # Add confidence score
            if hasattr(event, 'confidence'):
                line += f" [conf: {event.confidence:.2f}]"

            # Add impact if available
            if hasattr(event, 'impact') and event.impact:
                line += f" [impact: {event.impact}]"

            # Add description if available
            if hasattr(event, 'description') and event.description:
                # Truncate long descriptions
                desc = str(event.description)[:100]
                line += f" - {desc}"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)


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
        # Add parent reference for temporal query routing
        self.core._parent = self

        # Initialize ingestion manifest FIRST for incremental updates
        manifest_dir = Path(self.config.working_dir) / 'storage'
        self.manifest = IngestionManifest(manifest_dir)
        logger.info(f"✅ Ingestion manifest initialized ({len(self.manifest.manifest['documents'])} documents tracked)")

        # Use production DataIngester with email pipeline (Phase 2.6.1)
        # Pass config for docling feature flags + manifest for persistent content deduplication
        self.ingester = ProductionDataIngester(config=self.config, manifest=self.manifest)
        self.query_engine = QueryEngine(self.core)

        # Phase 2: Initialize query router for dual-layer architecture
        # Router decides when to use Signal Store (<1s) vs LightRAG (~12s)
        if self.config.use_signal_store and self.ingester.signal_store:
            from updated_architectures.implementation.query_router import QueryRouter
            self.query_router = QueryRouter(signal_store=self.ingester.signal_store)
            logger.info("✅ Query router initialized for dual-layer architecture")
        else:
            self.query_router = None
            logger.info("Signal Store disabled, using LightRAG only")

        # Refinement #3: Initialize relationship extractor for multi-hop intelligence
        if self.config.relationship_extraction_enabled:
            self.relationship_extractor = RelationshipExtractor()
            self.relationship_cache = {}  # content_hash -> relationships

            # Source confidence multipliers (centralized in config.py, Phase 2.8)
            self.SOURCE_CONFIDENCE = SOURCE_CONFIDENCE_MULTIPLIERS
            logger.info("✅ Relationship extractor initialized for cross-company intelligence")
        else:
            self.relationship_extractor = None
            logger.info("Relationship extraction disabled")

        # Phase 2.7B Option 1: Initialize event extractor for event detection
        if self.config.event_extraction_enabled:
            try:
                from src.ice_core.event_extractor import EventExtractor
                self.event_extractor = EventExtractor()
                self.event_cache = {}  # content_hash -> formatted events (separate from relationships)
                logger.info("✅ Event extractor initialized (15 event types)")
            except Exception as e:
                logger.warning(f"Event extractor disabled: {e}")
                self.event_extractor = None
                self.event_cache = {}
        else:
            self.event_extractor = None
            self.event_cache = {}

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

    # ========== REFINEMENT #3: RELATIONSHIP EXTRACTION METHODS ==========

    def _enhance_with_relationships(self, doc: Dict) -> Dict:
        """
        Extract ALL relationships from ANY document and enhance content.

        Applies universal relationship extraction with source-based confidence weighting.
        Relationships appended to document content for LightRAG natural parsing.

        Args:
            doc: Document dict with 'content', 'file_path', 'source' fields

        Returns:
            Enhanced document with relationships appended to content
        """
        if not self.relationship_extractor:
            return doc  # Extraction disabled

        # Graceful handling: If doc is string, return unchanged
        if isinstance(doc, str):
            return doc

        # Graceful handling: If doc is not a dict, return unchanged
        if not isinstance(doc, dict):
            return doc

        try:
            # Content-based caching for deduplication
            content = doc.get('content', '')
            if not content:
                return doc

            content_hash = hashlib.sha256(content.encode()).hexdigest()

            if content_hash in self.relationship_cache:
                relationships = self.relationship_cache[content_hash]
            else:
                # Get or extract entities
                entities = self._ensure_entities(doc)

                # Extract using ALL 7 relationship types
                relationships = self.relationship_extractor.extract_relationships(
                    text=content,
                    entities=entities,
                    doc_id=doc.get('file_path', 'unknown')
                )

                # Limit cache size
                if len(self.relationship_cache) >= self.config.relationship_cache_size:
                    # Remove oldest entry (simple FIFO)
                    self.relationship_cache.pop(next(iter(self.relationship_cache)))

                self.relationship_cache[content_hash] = relationships

            if not relationships:
                return doc

            # Apply source confidence multiplier
            source_type = self._detect_source_type(doc)
            confidence_mult = self.SOURCE_CONFIDENCE.get(source_type, 0.5)

            for rel in relationships:
                rel.confidence *= confidence_mult

                # Boost for quantified relationships
                if self._is_quantified(rel):
                    rel.confidence = min(1.0, rel.confidence + 0.15)

            # Filter by threshold
            filtered = [r for r in relationships
                       if r.confidence >= self.config.relationship_confidence_threshold]

            # Limit per-document relationships
            if len(filtered) > self.config.max_relationships_per_doc:
                # Keep highest confidence relationships
                filtered = sorted(filtered, key=lambda r: r.confidence, reverse=True)
                filtered = filtered[:self.config.max_relationships_per_doc]

            # Enhance document
            if filtered:
                rel_text = self._format_relationships(filtered)
                doc['content'] = f"{content}\n\n[EXTRACTED RELATIONSHIPS]\n{rel_text}"
                logger.debug(f"Enhanced doc with {len(filtered)} relationships")

            return doc

        except Exception as e:
            logger.warning(f"Relationship extraction failed: {e}")
            return doc  # Return original on failure

    def _ensure_entities(self, doc: Dict) -> List[Dict[str, Any]]:
        """
        Get entities from document or extract basic ones as fallback.

        Returns:
            List of entity dicts with 'text' and 'type' keys (required by RelationshipExtractor)
        """
        entities = doc.get('entities', [])

        # Normalize entities to dict format if provided as strings
        if entities:
            if isinstance(entities[0], str):
                # Convert ['NVDA', 'AMD'] → [{'text': 'NVDA', 'type': 'COMPANY'}, ...]
                return [{'text': e, 'type': 'COMPANY'} for e in entities]
            else:
                # Already dict format
                return entities

        # Basic entity extraction fallback (company names and tickers)
        content = doc.get('content', '')

        # Ticker pattern: 2-5 uppercase letters
        ticker_pattern = r'\b[A-Z]{2,5}\b'
        tickers = re.findall(ticker_pattern, content)

        # Common company suffixes
        company_pattern = r'\b(\w+(?:\s+\w+){0,2})\s+(?:Inc|Corp|Ltd|LLC|Company|Group|Holdings|Technologies|Systems)\b'
        companies = re.findall(company_pattern, content)

        entities_list = list(set(tickers + companies))[:50]  # Limit to prevent explosion

        # Convert to dict format required by RelationshipExtractor
        return [{'text': e, 'type': 'COMPANY'} for e in entities_list]

    def _detect_source_type(self, doc: Dict) -> str:
        """Detect document source for confidence weighting"""
        file_path = doc.get('file_path', '').lower()
        source = doc.get('source', '').lower()

        # Pattern matching for source detection
        if 'sec_edgar' in file_path or 'sec' in source:
            return 'sec_edgar'
        elif 'sec_facts' in file_path:
            return 'sec_facts'
        elif 'newsapi' in file_path or 'newsapi' in source:
            return 'newsapi'
        elif 'finnhub' in file_path or 'finnhub' in source:
            return 'finnhub'
        elif 'marketaux' in file_path or 'marketaux' in source:
            return 'marketaux'
        elif 'benzinga' in file_path or 'benzinga' in source:
            return 'benzinga'
        elif 'yahoo' in file_path or 'yahoo' in source:
            return 'yahoo'
        elif 'email' in file_path or '.eml' in file_path:
            return 'email'
        elif 'exa' in file_path or 'exa' in source:
            return 'exa'

        return 'unknown'

    def _is_quantified(self, relationship) -> bool:
        """Check if relationship has quantification (higher confidence)"""
        if hasattr(relationship, 'attributes') and relationship.attributes:
            attrs = relationship.attributes
            return any(k in attrs for k in ['percentage', 'amount', 'value', 'count', 'revenue'])
        return False

    def _format_relationships(self, relationships) -> str:
        """Format relationships for LightRAG natural parsing"""
        lines = []
        for rel in relationships:
            # Preserve directionality for multi-hop traversal
            line = f"{rel.source} {rel.relationship_type} {rel.target}"
            line += f" (confidence: {rel.confidence:.2f})"

            # Add attributes if present
            if hasattr(rel, 'attributes') and rel.attributes:
                attrs_str = ', '.join(f"{k}={v}" for k, v in rel.attributes.items())
                line += f" [{attrs_str}]"

            lines.append(line)

        return '\n'.join(lines)

    # ========== END RELATIONSHIP EXTRACTION METHODS ==========

    # ========== EVENT EXTRACTION METHODS (Phase 2.7B Option 1) ==========

    def _enhance_with_events(self, doc: Dict) -> Dict:
        """
        Extract and append events to document content (Phase 2.7B Option 1).
        Follows same pattern as _enhance_with_relationships().

        Args:
            doc: Document dictionary with content, ticker, file_path

        Returns:
            Enhanced document with events appended to content
        """
        try:
            content = doc.get('content', '')
            if not content or len(content) < 50:
                return doc  # Skip very short documents

            # Content-based caching (separate key prefix from relationships)
            import hashlib
            content_hash = f"event_{hashlib.sha256(content.encode()).hexdigest()}"

            if content_hash in self.event_cache:
                # Cache hit - instant return
                doc['content'] = content + self.event_cache[content_hash]
                return doc

            # Extract events (EventExtractor is self-contained, no entities needed)
            events = self.event_extractor.extract_events(
                document=content,
                ticker=doc.get('ticker'),
                document_date=None,  # Let extractor parse dates from content
                source_id=doc.get('file_path', 'unknown')
            )

            # Filter by confidence threshold
            high_conf_events = [
                e for e in events
                if e.confidence >= self.config.event_confidence_threshold
            ]

            # Limit to prevent noise
            high_conf_events = high_conf_events[:self.config.max_events_per_doc]

            if not high_conf_events:
                return doc  # No events to add

            # Phase 2.7B Option 5: Persist events to Signal Store for fast calendar queries
            # This enables "When is next earnings?" queries via SQL (<100ms)
            try:
                # Get signal_store via parent reference (ICECore has _parent pointing to ICESimplified)
                signal_store = None
                if hasattr(self, '_parent') and hasattr(self._parent, 'ingester'):
                    signal_store = getattr(self._parent.ingester, 'signal_store', None)
                elif hasattr(self, 'ingester'):
                    signal_store = getattr(self.ingester, 'signal_store', None)

                if signal_store:
                    from datetime import datetime as dt
                    event_dicts = []
                    for event in high_conf_events:
                        # Map EventNode to calendar_events schema
                        event_dicts.append({
                            'ticker': event.ticker,
                            'event_type': event.type.value if hasattr(event.type, 'value') else str(event.type),
                            'event_date': event.date.strftime('%Y-%m-%d') if event.date else dt.now().strftime('%Y-%m-%d'),
                            'event_value': event.magnitude,  # Map magnitude to event_value
                            'is_future': 1 if event.date and event.date > dt.now() else 0,
                            'source_document_id': event.source_document_id or doc.get('file_path', 'unknown')
                        })
                    if event_dicts:
                        inserted = signal_store.insert_calendar_events_batch(event_dicts)
                        logger.debug(f"[Option5] Persisted {inserted} events to Signal Store calendar_events")
            except Exception as e:
                logger.debug(f"[Option5] Signal Store event persistence failed (non-fatal): {e}")

            # Format for LightRAG
            formatted_events = self._format_events(high_conf_events)

            # Cache formatted result
            self.event_cache[content_hash] = formatted_events
            doc['content'] = content + formatted_events

            # FIFO cache eviction
            if len(self.event_cache) > self.config.event_cache_size:
                self.event_cache.pop(next(iter(self.event_cache)))

            return doc

        except Exception as e:
            logger.debug(f"Event extraction failed: {e}")
            return doc  # Graceful degradation - return original document

    def _format_events(self, events: List) -> str:
        """
        Format events for LightRAG natural parsing.
        Follows same pattern as _format_relationships().

        Args:
            events: List of EventNode objects

        Returns:
            Formatted string with event details
        """
        if not events:
            return ""

        formatted_lines = ["\n\nKey Events:"]

        for event in events:
            # Build event line with available attributes
            # FIXED: Use event.type (not event.event_type) - EventNode dataclass attr
            line = f"- {event.type.value}"

            # Add ticker if available
            if hasattr(event, 'ticker') and event.ticker:
                line += f" ({event.ticker})"

            # Add confidence score
            if hasattr(event, 'confidence'):
                line += f" [conf: {event.confidence:.2f}]"

            # Add impact if available
            if hasattr(event, 'impact') and event.impact:
                line += f" [impact: {event.impact}]"

            # Add description if available
            if hasattr(event, 'description') and event.description:
                # Truncate long descriptions
                desc = str(event.description)[:100]
                line += f" - {desc}"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    # ========== END EVENT EXTRACTION METHODS ==========

    def filter_new_documents(self, documents: List[Dict], source_type: str, ticker: str = None) -> List[Dict]:
        """
        Universal content deduplication filter for all document sources.

        Uses manifest content hashing to prevent duplicate document ingestion.
        Works uniformly across all APIs regardless of date handling.

        Args:
            documents: List of document dicts with 'content' field
            source_type: Source type ('api_news', 'api_financial', 'email', etc.)
            ticker: Optional ticker symbol for metadata

        Returns:
            Filtered list containing only new (not previously seen) documents
        """
        import hashlib

        new_docs = []
        for doc in documents:
            content = doc.get('content', '')
            if not content:
                continue

            # Check if content already exists in manifest
            if not self.manifest.is_content_duplicate(content):
                # Generate stable document ID from content hash
                content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
                doc_id = f"{source_type}_{ticker or 'unknown'}_{content_hash}"

                # Add to manifest to track
                self.manifest.add_document(doc_id, content, {
                    'source_type': source_type,
                    'ticker': ticker,
                    'source': doc.get('source'),
                    'ingested_at': datetime.now(timezone.utc).isoformat()
                })

                new_docs.append(doc)
            else:
                logger.debug(f"Skipping duplicate content for {ticker or 'unknown'} from {source_type}")

        if len(new_docs) < len(documents):
            logger.info(f"Filtered {len(documents) - len(new_docs)} duplicate documents from {source_type}")

        return new_docs

    def _aggregate_investment_signals(self, entities: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate investment signals from extracted entity data

        Processes EntityExtractor output to calculate investment intelligence metrics:
        - Email count and ticker coverage
        - BUY/SELL rating distribution
        - Average confidence scores

        Args:
            entities: List of entity dicts from EntityExtractor

        Returns:
            Dict with aggregated investment signal metrics
        """
        if not entities:
            return {
                'email_count': 0,
                'tickers_covered': 0,
                'buy_ratings': 0,
                'sell_ratings': 0,
                'avg_confidence': 0.0
            }

        tickers = set()
        buy_ratings = 0
        sell_ratings = 0
        confidences = []

        for ent in entities:
            # Aggregate tickers (handle both dict format from EntityExtractor and string format)
            ticker_list = ent.get('tickers', [])
            for ticker_obj in ticker_list:
                if isinstance(ticker_obj, dict):
                    # EntityExtractor format: {'ticker': 'NVDA', 'confidence': 0.95}
                    if 'ticker' in ticker_obj:
                        tickers.add(ticker_obj['ticker'])
                elif isinstance(ticker_obj, str):
                    # Simple string format
                    tickers.add(ticker_obj)

            # Count BUY/SELL ratings (handle both dict and string formats)
            ratings = ent.get('ratings', [])
            for rating_obj in ratings:
                if isinstance(rating_obj, dict):
                    # EntityExtractor format: {'rating': 'buy', 'confidence': 0.85}
                    rating_str = str(rating_obj.get('rating', '')).upper()
                elif isinstance(rating_obj, str):
                    rating_str = rating_obj.upper()
                else:
                    rating_str = str(rating_obj).upper()

                if 'BUY' in rating_str:
                    buy_ratings += 1
                if 'SELL' in rating_str:
                    sell_ratings += 1

            # Collect confidence scores
            if ent.get('confidence'):
                confidences.append(ent['confidence'])

        return {
            'email_count': len(entities),
            'tickers_covered': len(tickers),
            'buy_ratings': buy_ratings,
            'sell_ratings': sell_ratings,
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0.0
        }

    def ingest_portfolio_data(self, holdings: List[str], email_limit: int = 71, news_limit: int = 5, sec_limit: int = 3) -> Dict[str, Any]:
        """
        Ingest data for portfolio holdings and add to knowledge base with metrics

        Args:
            holdings: List of ticker symbols
            email_limit: Maximum number of emails to fetch (default: 71 - all samples)
            news_limit: Maximum number of news articles per symbol (default: 5)
            sec_limit: Maximum number of SEC filings per symbol (default: 3)

        Returns:
            Ingestion results summary with detailed metrics
        """
        from datetime import datetime

        start_time = datetime.now()
        results = {
            'successful': [],
            'failed': [],
            'email_documents': 0,        # Portfolio-wide email count
            'ticker_documents': 0,       # Ticker-specific docs count
            'total_documents': 0,
            'documents': [],
            'metrics': {
                'ingestion_time': 0.0,
                'email_processing_time': 0.0,
                'documents_per_symbol': {},
                'data_sources_used': [],
                'processing_time_per_symbol': {}
            }
        }

        # STEP 1: Fetch portfolio-wide emails ONCE (before symbol loop)
        # Rationale: Emails are broker research covering multiple tickers, not ticker-specific
        # "Trust the Graph" strategy - emails fetched unfiltered for relationship discovery
        email_start_time = datetime.now()
        try:
            email_docs = self.ingester.fetch_email_documents(tickers=None, limit=email_limit)
            if email_docs:
                # email_docs now returns List[Dict] with format: {'content': str, 'file_path': 'email:filename.eml', 'type': 'financial'}
                # Extract content and preserve file_path for LightRAG traceability
                email_doc_list = [
                    {
                        'content': doc['content'],  # Extract content from dict
                        'file_path': doc.get('file_path'),  # Pass through file_path for traceability
                        'type': 'email',
                        'symbol': 'PORTFOLIO'
                    }
                    for doc in email_docs
                ]

                email_result = self.core.add_documents_batch(email_doc_list)

                if email_result.get('status') == 'success':
                    results['email_documents'] = len(email_docs)
                    results['total_documents'] += len(email_docs)
                    results['documents'].extend(email_doc_list)
                    email_time = (datetime.now() - email_start_time).total_seconds()
                    results['metrics']['email_processing_time'] = email_time
                    logger.info(f"✅ Successfully ingested {len(email_docs)} portfolio-wide emails in {email_time:.2f}s")
                else:
                    logger.warning(f"⚠️ Email batch processing had issues: {email_result.get('message')}")
        except Exception as e:
            logger.warning(f"⚠️ Email ingestion failed (non-fatal): {e}")

        # STEP 2: Loop through holdings for ticker-specific data (API + SEC)
        for symbol in holdings:
            symbol_start_time = datetime.now()
            logger.info(f"Ingesting ticker-specific data for {symbol}")

            try:
                # Fetch ticker-specific data using individual methods (not fetch_comprehensive_data)
                # This prevents duplicate email fetching
                logger.info(f"💰 {symbol}: Fetching data from APIs...")
                financial_docs = self.ingester.fetch_company_financials(symbol, limit=news_limit)  # Returns List[Dict]
                news_docs = self.ingester.fetch_company_news(symbol, limit=news_limit, context='portfolio')  # Returns List[Dict] with smart source prioritization
                sec_docs = self.ingester.fetch_sec_filings(symbol, limit=sec_limit)  # Returns List[Dict]

                # SEC Company Facts API: Free XBRL financial metrics (Revenue, NetIncome, Assets, EPS, Cash)
                sec_facts_docs = []
                if self.config.sec_facts_enabled:
                    sec_facts_docs = self.ingester.fetch_sec_company_facts(symbol)  # Returns List[Dict]

                # Build document list with SOURCE markers for post-processing statistics
                # Phase 1: Enhanced SOURCE markers with timestamps (retrieval time)
                retrieval_timestamp = datetime.now().isoformat()

                doc_list = []
                for doc_dict in financial_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'financial'
                    })

                for doc_dict in news_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'news'
                    })

                for doc_dict in sec_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'regulatory'
                    })

                for doc_dict in sec_facts_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'financial'  # Financial metrics type
                    })

                if doc_list:
                    # Apply universal content deduplication before adding to graph
                    doc_list = self.filter_new_documents(doc_list, source_type='api', ticker=symbol)

                    # Add ticker-specific documents to knowledge base
                    batch_result = self.core.add_documents_batch(doc_list)

                    if batch_result.get('status') == 'success':
                        results['successful'].append(symbol)
                        results['ticker_documents'] += len(doc_list)
                        results['total_documents'] += len(doc_list)
                        results['documents'].extend(doc_list)
                        results['metrics']['documents_per_symbol'][symbol] = len(doc_list)

                        symbol_time = (datetime.now() - symbol_start_time).total_seconds()
                        results['metrics']['processing_time_per_symbol'][symbol] = symbol_time

                        logger.info(f"✅ {symbol}: {len(doc_list)} documents ingested in {symbol_time:.2f}s")
                    else:
                        results['failed'].append({
                            'symbol': symbol,
                            'error': batch_result.get('message', 'Batch processing failed')
                        })
                        logger.error(f"❌ Batch processing failed for {symbol}")
                else:
                    results['failed'].append({
                        'symbol': symbol,
                        'error': 'No ticker-specific documents fetched'
                    })
                    logger.warning(f"⚠️ No ticker-specific documents fetched for {symbol}")

            except Exception as e:
                results['failed'].append({
                    'symbol': symbol,
                    'error': str(e)
                })
                logger.error(f"❌ Ticker-specific ingestion failed for {symbol}: {e}")

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

    def calculate_composite_score(
        self,
        confidence: float = 0.5,
        freshness: float = 0.5,
        relevance: float = 1.0,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate composite score combining confidence, freshness, and relevance.

        Args:
            confidence: Confidence score (0-1) from entity extraction/source quality
            freshness: Temporal freshness score (0-1) from exponential decay
            relevance: Query relevance score (0-1) from semantic matching
            weights: Optional custom weights (default: balanced approach)
                    {'confidence': 0.3, 'freshness': 0.3, 'relevance': 0.4}

        Returns:
            Composite score (0-1) for ranking results

        Formula:
            composite = w_c * confidence + w_f * freshness + w_r * relevance

        Example:
            >>> score = ice.calculate_composite_score(0.87, 0.25, 0.9)
            >>> print(f"Composite score: {score:.2f}")  # 0.62
        """
        # Default balanced weights with slight preference for relevance
        if weights is None:
            weights = {
                'confidence': 0.3,  # Source quality and extraction confidence
                'freshness': 0.3,   # Temporal recency (exponential decay)
                'relevance': 0.4    # Query-result matching
            }

        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}

        # Calculate weighted composite score
        composite = (
            weights.get('confidence', 0.3) * confidence +
            weights.get('freshness', 0.3) * freshness +
            weights.get('relevance', 0.4) * relevance
        )

        # Ensure score is in valid range [0, 1]
        return max(0.0, min(1.0, composite))

    def estimate_relevance_score(
        self,
        query: str,
        result_text: str,
        ticker: Optional[str] = None
    ) -> float:
        """
        Estimate relevance score between query and result text.

        Simple keyword-based relevance scoring with potential for enhancement.
        Future versions could use embeddings or LLM-based similarity.

        Args:
            query: User's query string
            result_text: Text content from search result
            ticker: Optional ticker symbol for ticker-specific queries

        Returns:
            Relevance score (0-1) based on keyword matching and context

        Algorithm:
            1. Extract key terms from query (normalized)
            2. Count term occurrences in result (case-insensitive)
            3. Apply position weighting (earlier = higher relevance)
            4. Bonus for ticker symbol matches
        """
        import re

        # Normalize texts for comparison
        query_lower = query.lower()
        result_lower = result_text.lower() if result_text else ""

        if not result_lower:
            return 0.0

        # Extract key terms from query (remove common words)
        stop_words = {'the', 'a', 'an', 'is', 'are', 'what', 'which', 'how', 'why',
                      'when', 'where', 'for', 'of', 'in', 'on', 'at', 'to', 'from'}

        # Tokenize query
        query_terms = re.findall(r'\b[a-z]+\b', query_lower)
        key_terms = [term for term in query_terms if term not in stop_words and len(term) > 2]

        if not key_terms:
            # If no key terms, check for any overlap
            return 0.5 if any(word in result_lower for word in query_lower.split()) else 0.2

        # Count term occurrences in result
        term_scores = []
        result_length = len(result_lower)

        for term in key_terms:
            # Find all occurrences
            occurrences = [m.start() for m in re.finditer(r'\b' + re.escape(term) + r'\b', result_lower)]

            if occurrences:
                # Calculate term score with position weighting
                # Earlier occurrences get higher weight
                position_scores = [1.0 - (pos / result_length) for pos in occurrences]
                term_score = min(1.0, sum(position_scores) / 3)  # Cap contribution per term
                term_scores.append(term_score)
            else:
                term_scores.append(0.0)

        # Calculate base relevance
        if term_scores:
            base_relevance = sum(term_scores) / len(key_terms)
        else:
            base_relevance = 0.2

        # Ticker bonus: if ticker mentioned in query and found in result
        ticker_bonus = 0.0
        if ticker:
            ticker_lower = ticker.lower()
            if ticker_lower in query_lower and ticker_lower in result_lower:
                ticker_bonus = 0.2

        # Combined relevance score
        relevance = min(1.0, base_relevance + ticker_bonus)

        # Apply minimum threshold
        return max(0.1, relevance)

    def rank_results_by_composite_score(
        self,
        results: List[Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rank and filter results by composite score.

        Args:
            results: List of result dicts with confidence, freshness, relevance scores
            weights: Optional custom weights for composite scoring
            min_score: Minimum composite score threshold (default: 0.0)

        Returns:
            Sorted list of results with composite_score added, filtered by min_score

        Example:
            >>> results = [
            ...     {'ticker': 'NVDA', 'confidence': 0.9, 'freshness_score': 0.5, 'relevance': 0.8},
            ...     {'ticker': 'AMD', 'confidence': 0.7, 'freshness_score': 0.9, 'relevance': 0.6}
            ... ]
            >>> ranked = ice.rank_results_by_composite_score(results, min_score=0.5)
        """
        scored_results = []

        for result in results:
            # Extract scores with defaults
            confidence = result.get('confidence', 0.5)
            freshness = result.get('freshness_score', 0.5)
            relevance = result.get('relevance', 1.0)  # Default high if not specified

            # Calculate composite score
            composite_score = self.calculate_composite_score(
                confidence, freshness, relevance, weights
            )

            # Skip results below threshold
            if composite_score < min_score:
                continue

            # Add composite score to result
            result_copy = result.copy()
            result_copy['composite_score'] = composite_score
            scored_results.append(result_copy)

        # Sort by composite score (descending)
        scored_results.sort(key=lambda x: x['composite_score'], reverse=True)

        return scored_results

    def query_rating(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query analyst rating(s) for a ticker using dual-layer architecture.

        Routes to Signal Store (<1s) if available, otherwise falls back to LightRAG (~12s).
        Now supports date range filtering for temporal queries.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            start_date: Optional ISO format start date (e.g., '2024-01-01T00:00:00Z')
            end_date: Optional ISO format end date (e.g., '2024-06-30T23:59:59Z')

        Returns:
            Dict with rating data:
            {
                'ticker': 'NVDA',
                'rating': 'BUY',  # or 'ratings' list if date range specified
                'firm': 'Goldman Sachs',
                'analyst': 'John Doe',
                'confidence': 0.87,
                'timestamp': '2024-03-15T10:30:00Z',
                'source': 'signal_store' | 'lightrag',
                'latency_ms': 45
            }

        Examples:
            >>> ice.query_rating('NVDA')  # Latest rating
            {'ticker': 'NVDA', 'rating': 'BUY', 'source': 'signal_store', 'latency_ms': 45}

            >>> ice.query_rating('NVDA', '2024-04-01', '2024-06-30')  # Q2 2024 ratings
            {'ticker': 'NVDA', 'ratings': [...], 'count': 5, 'source': 'signal_store', ...}
        """
        import time
        start_time = time.time()

        ticker = ticker.upper()

        # Try Signal Store first (if enabled)
        if self.query_router and self.ingester.signal_store:
            try:
                # Use date range method if dates provided
                if start_date or end_date:
                    # Default to wide range if only one date provided
                    if not start_date:
                        start_date = '1970-01-01T00:00:00Z'
                    if not end_date:
                        from datetime import datetime
                        end_date = datetime.now().isoformat()

                    rating_data = self.ingester.signal_store.get_ratings_by_date_range(
                        ticker, start_date, end_date
                    )
                    latency_ms = int((time.time() - start_time) * 1000)

                    if rating_data:
                        # Rank ratings by composite score
                        ranked_ratings = self.rank_results_by_composite_score(rating_data)

                        result = {
                            'ticker': ticker,
                            'ratings': ranked_ratings,  # Now sorted by composite score
                            'count': len(ranked_ratings),
                            'date_range': {'start': start_date, 'end': end_date},
                            'source': 'signal_store',
                            'latency_ms': latency_ms,
                            'best_rating': ranked_ratings[0] if ranked_ratings else None
                        }
                        logger.info(f"✅ Signal Store date range query: {ticker} → {len(ranked_ratings)} ratings ranked by composite score ({latency_ms}ms)")
                        return result
                else:
                    # Use existing latest rating method
                    rating_data = self.ingester.signal_store.get_latest_rating(ticker)
                    latency_ms = int((time.time() - start_time) * 1000)

                if rating_data:
                    # Calculate composite score for single rating
                    confidence = rating_data.get('confidence', 0.5)
                    freshness = rating_data.get('freshness_score', 0.5)
                    composite_score = self.calculate_composite_score(confidence, freshness, 1.0)

                    rating_data['composite_score'] = composite_score
                    rating_data['source'] = 'signal_store'
                    rating_data['latency_ms'] = latency_ms
                    logger.info(f"✅ Signal Store rating query: {ticker} → {rating_data['rating']} (composite: {composite_score:.2f}, {latency_ms}ms)")
                    return rating_data

                logger.debug(f"No Signal Store data for {ticker}, falling back to LightRAG")

            except Exception as e:
                logger.warning(f"Signal Store query failed: {e}, falling back to LightRAG")

        # Fallback: Query LightRAG for semantic rating extraction
        try:
            query = f"What is the latest analyst rating or recommendation for {ticker}?"
            lightrag_result = self.core.query(query, mode='hybrid')

            latency_ms = int((time.time() - start_time) * 1000)

            # Estimate relevance score for LightRAG result
            relevance_score = self.estimate_relevance_score(
                query,
                str(lightrag_result),
                ticker
            )

            # For LightRAG, we estimate confidence and freshness
            # These could be enhanced with actual metadata extraction
            estimated_confidence = 0.6  # Medium confidence for semantic extraction
            estimated_freshness = 0.5   # Unknown freshness without timestamp

            # Calculate composite score
            composite_score = self.calculate_composite_score(
                estimated_confidence,
                estimated_freshness,
                relevance_score
            )

            # Parse LightRAG response for rating information
            # (This is a simplified parser - real implementation would use LLM extraction)
            rating_info = {
                'ticker': ticker,
                'rating': 'UNKNOWN',  # Would extract from lightrag_result
                'source': 'lightrag',
                'latency_ms': latency_ms,
                'relevance_score': relevance_score,
                'composite_score': composite_score,
                'raw_response': lightrag_result
            }

            logger.info(f"LightRAG rating query: {ticker} (relevance: {relevance_score:.2f}, composite: {composite_score:.2f}, {latency_ms}ms)")
            return rating_info

        except Exception as e:
            logger.error(f"Rating query failed for {ticker}: {e}")
            return {
                'ticker': ticker,
                'rating': 'ERROR',
                'error': str(e),
                'source': 'none',
                'latency_ms': int((time.time() - start_time) * 1000)
            }

    def query_metric(
        self,
        ticker: str,
        metric_type: str,
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query financial metric(s) for a ticker using dual-layer architecture.

        Routes to Signal Store (<1s) if available, otherwise falls back to LightRAG (~12s).
        Now supports date range filtering for temporal analysis.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            metric_type: Type of financial metric (e.g., 'Operating Margin', 'Revenue', 'EPS')
            period: Optional specific period filter (e.g., 'Q2 2024', 'FY2024', 'TTM')
            start_date: Optional ISO format start date for range queries
            end_date: Optional ISO format end date for range queries

        Returns:
            Dict with metric data:
            {
                'ticker': 'NVDA',
                'metric_type': 'Operating Margin',
                'metric_value': '62.3%',  # or 'metrics' list if date range specified
                'period': 'Q2 2024',
                'confidence': 0.95,
                'source': 'signal_store' | 'lightrag',
                'latency_ms': 35
            }

        Examples:
            >>> ice.query_metric('NVDA', 'Operating Margin')
            {'ticker': 'NVDA', 'metric_type': 'Operating Margin', 'metric_value': '62.3%', ...}

            >>> ice.query_metric('NVDA', 'Revenue', period='Q2 2024')
            {'ticker': 'NVDA', 'metric_type': 'Revenue', 'metric_value': '$26.97B', ...}

            >>> ice.query_metric('NVDA', 'Revenue', start_date='2024-01-01', end_date='2024-06-30')
            {'ticker': 'NVDA', 'metrics': [...], 'count': 2, 'date_range': {...}, ...}
        """
        import time
        start_time = time.time()

        ticker = ticker.upper()

        # Try Signal Store first (if enabled)
        if self.query_router and self.ingester.signal_store:
            try:
                # Use date range method if dates provided
                if start_date or end_date:
                    # Default to wide range if only one date provided
                    if not start_date:
                        start_date = '1970-01-01T00:00:00Z'
                    if not end_date:
                        from datetime import datetime
                        end_date = datetime.now().isoformat()

                    metric_data = self.ingester.signal_store.get_metrics_by_date_range(
                        ticker=ticker,
                        metric_type=metric_type,
                        start_date=start_date,
                        end_date=end_date
                    )
                    latency_ms = int((time.time() - start_time) * 1000)

                    if metric_data:
                        result = {
                            'ticker': ticker,
                            'metric_type': metric_type,
                            'metrics': metric_data,
                            'count': len(metric_data),
                            'date_range': {'start': start_date, 'end': end_date},
                            'source': 'signal_store',
                            'latency_ms': latency_ms
                        }
                        logger.info(f"✅ Signal Store date range metric query: {ticker} {metric_type} → {len(metric_data)} metrics ({latency_ms}ms)")
                        return result
                else:
                    # Use existing single metric method
                    metric_data = self.ingester.signal_store.get_metric(
                        ticker=ticker,
                        metric_type=metric_type,
                        period=period
                    )
                    latency_ms = int((time.time() - start_time) * 1000)

                if metric_data:
                    metric_data['source'] = 'signal_store'
                    metric_data['latency_ms'] = latency_ms
                    logger.info(f"✅ Signal Store metric query: {ticker} {metric_type} → {metric_data['metric_value']} ({latency_ms}ms)")
                    return metric_data

                logger.debug(f"No Signal Store data for {ticker} {metric_type}, falling back to LightRAG")

            except Exception as e:
                logger.warning(f"Signal Store metric query failed: {e}, falling back to LightRAG")

        # Fallback: Query LightRAG for semantic metric extraction
        try:
            period_str = f" for {period}" if period else ""
            query = f"What is the {metric_type} for {ticker}{period_str}?"
            lightrag_result = self.core.query(query, mode='hybrid')

            latency_ms = int((time.time() - start_time) * 1000)

            # Parse LightRAG response for metric information
            # (This is a simplified parser - real implementation would use LLM extraction)
            metric_info = {
                'ticker': ticker,
                'metric_type': metric_type,
                'metric_value': 'UNKNOWN',  # Would extract from lightrag_result
                'period': period,
                'source': 'lightrag',
                'latency_ms': latency_ms,
                'raw_response': lightrag_result
            }

            logger.info(f"LightRAG metric query: {ticker} {metric_type} ({latency_ms}ms)")
            return metric_info

        except Exception as e:
            logger.error(f"Metric query failed for {ticker} {metric_type}: {e}")
            return {
                'ticker': ticker,
                'metric_type': metric_type,
                'metric_value': 'ERROR',
                'error': str(e),
                'source': 'none',
                'latency_ms': int((time.time() - start_time) * 1000)
            }

    def query_calendar_events(
        self,
        ticker: str,
        event_type: Optional[str] = None,
        is_future: Optional[bool] = None,
        days_range: int = 90
    ) -> Dict[str, Any]:
        """
        Query upcoming/past calendar events from Signal Store.

        Routes directly to Signal Store for structured calendar data (earnings,
        dividends, ex-dividend dates). This is the Phase 2.7B Option 5 handler
        for completing the STRUCTURED_CALENDAR query pathway.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            event_type: Optional filter ('earnings', 'dividend', 'ex-dividend')
            is_future: True=upcoming only, False=past only, None=both
            days_range: Number of days to look back (default 90)

        Returns:
            Dict with calendar event data:
            {
                'status': 'success' | 'error',
                'ticker': 'NVDA',
                'events': [...],  # List of calendar events
                'count': 5,
                'next_event': {...},  # Nearest future event (if any)
                'source': 'signal_store'
            }

        Examples:
            >>> ice.query_calendar_events('NVDA', event_type='earnings')
            {'ticker': 'NVDA', 'events': [...], 'next_event': {...}, ...}

            >>> ice.query_calendar_events('AAPL', is_future=True)
            {'ticker': 'AAPL', 'events': [...upcoming events...], ...}
        """
        from datetime import datetime, timedelta

        ticker = ticker.upper()
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_range)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')

        # Validate Signal Store availability
        if not hasattr(self, 'ingester') or not self.ingester or not self.ingester.signal_store:
            logger.warning("Signal Store not available for calendar query")
            return {
                'status': 'error',
                'message': 'Signal Store not available',
                'ticker': ticker,
                'source': 'none'
            }

        try:
            events = self.ingester.signal_store.get_events_in_date_range(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                event_type=event_type,
                is_future=is_future
            )

            # Find next upcoming event (first event with date >= today)
            next_event = None
            for e in events:
                event_date = e.get('event_date', '')
                if event_date >= today:
                    next_event = e
                    break

            logger.info(f"Calendar query: {ticker} → {len(events)} events found")
            return {
                'status': 'success',
                'ticker': ticker,
                'events': events,
                'count': len(events),
                'next_event': next_event,
                'source': 'signal_store'
            }

        except Exception as e:
            logger.error(f"Calendar query failed for {ticker}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'ticker': ticker,
                'source': 'none'
            }

    def query_price(
        self,
        ticker: str,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """
        Query price targets from Signal Store.

        Routes directly to Signal Store for structured price target data.
        This is the Phase 2.8 handler for STRUCTURED_PRICE query pathway.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            include_history: If True, include historical price targets

        Returns:
            Dict with price target data:
            {
                'status': 'success' | 'error',
                'ticker': 'NVDA',
                'latest_price_target': {...},  # Most recent target
                'price_target_history': [...],  # List of targets (if include_history)
                'source': 'signal_store'
            }
        """
        ticker = ticker.upper()

        # Validate Signal Store availability
        if not hasattr(self, 'ingester') or not self.ingester or not self.ingester.signal_store:
            logger.warning("Signal Store not available for price query")
            return {
                'status': 'error',
                'message': 'Signal Store not available',
                'ticker': ticker,
                'source': 'none'
            }

        try:
            latest = self.ingester.signal_store.get_latest_price_target(ticker)
            history = []

            if include_history:
                history = self.ingester.signal_store.get_price_target_history(ticker, limit=10)

            logger.info(f"Price query: {ticker} → target found: {latest is not None}")
            return {
                'status': 'success',
                'ticker': ticker,
                'latest_price_target': latest,
                'price_target_history': history,
                'count': len(history) if history else (1 if latest else 0),
                'source': 'signal_store'
            }

        except Exception as e:
            logger.error(f"Price query failed for {ticker}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'ticker': ticker,
                'source': 'none'
            }

    def query_pricing_history(
        self,
        ticker: str,
        query_type: str = 'recent',
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Query historical prices and 52-week high/low from Signal Store.

        Routes directly to Signal Store for structured OHLCV data.
        This is the Phase 2.8 handler for STRUCTURED_PRICING_HISTORY pathway.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            query_type: 'recent' for recent prices, '52_week' for high/low stats
            days: Number of days of history (default 30)

        Returns:
            Dict with pricing history data:
            {
                'status': 'success' | 'error',
                'ticker': 'NVDA',
                '52_week_stats': {...},  # 52-week high/low/current
                'recent_prices': [...],  # Recent OHLCV data
                'source': 'signal_store'
            }
        """
        ticker = ticker.upper()

        # Validate Signal Store availability
        if not hasattr(self, 'ingester') or not self.ingester or not self.ingester.signal_store:
            logger.warning("Signal Store not available for pricing history query")
            return {
                'status': 'error',
                'message': 'Signal Store not available',
                'ticker': ticker,
                'source': 'none'
            }

        try:
            week_52 = self.ingester.signal_store.get_52_week_high_low(ticker)
            recent_prices = self.ingester.signal_store.get_price_history(
                ticker,
                limit=days
            )

            logger.info(f"Pricing history: {ticker} → {len(recent_prices)} days, 52wk stats: {week_52 is not None}")
            return {
                'status': 'success',
                'ticker': ticker,
                '52_week_stats': week_52,
                'recent_prices': recent_prices,
                'count': len(recent_prices),
                'source': 'signal_store'
            }

        except Exception as e:
            logger.error(f"Pricing history query failed for {ticker}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'ticker': ticker,
                'source': 'none'
            }

    def query_with_router(self, query: str, mode: str = 'hybrid') -> Dict[str, Any]:
        """
        Execute query using intelligent routing (Signal Store vs LightRAG).

        Uses QueryRouter to classify query intent and route to optimal layer:
        - Structured queries (What/Which/Show) → Signal Store (<1s)
        - Semantic queries (Why/How/Explain) → LightRAG (~12s)
        - Hybrid queries → Both layers, combined result

        Args:
            query: User query string
            mode: LightRAG query mode if routing to LightRAG ('local', 'global', 'hybrid', 'naive')

        Returns:
            Dict with query result:
            {
                'query': original query,
                'answer': response text,
                'query_type': 'structured_rating' | 'semantic_why' | etc.,
                'source': 'signal_store' | 'lightrag' | 'hybrid',
                'confidence': 0.90,
                'latency_ms': 850
            }

        Examples:
            >>> ice.query_with_router("What's NVDA's latest rating?")
            {'answer': 'BUY', 'source': 'signal_store', 'latency_ms': 45}

            >>> ice.query_with_router("Why did Goldman upgrade NVDA?")
            {'answer': '...reasoning...', 'source': 'lightrag', 'latency_ms': 12000}
        """
        import time
        start_time = time.time()

        # Route query to optimal layer
        if self.query_router:
            from updated_architectures.implementation.query_router import QueryType

            query_type, confidence = self.query_router.route_query(query)
            logger.info(f"Query routed: {query_type.value} (confidence: {confidence:.2f})")

            # Handle structured rating queries
            if query_type == QueryType.STRUCTURED_RATING:
                ticker = self.query_router.extract_ticker(query)
                if ticker:
                    rating_data = self.query_rating(ticker)
                    formatted_answer = self.query_router.format_signal_store_result(rating_data, query)

                    return {
                        'query': query,
                        'answer': formatted_answer,
                        'query_type': query_type.value,
                        'source': 'signal_store',
                        'confidence': confidence,
                        'latency_ms': int((time.time() - start_time) * 1000),
                        'raw_data': rating_data
                    }

            # Handle structured metric queries
            elif query_type == QueryType.STRUCTURED_METRIC:
                ticker = self.query_router.extract_ticker(query)
                metric_type, period = self.query_router.extract_metric_info(query)

                if ticker and metric_type:
                    metric_data = self.query_metric(ticker, metric_type, period)
                    formatted_answer = self.query_router.format_signal_store_result(metric_data, query)

                    return {
                        'query': query,
                        'answer': formatted_answer,
                        'query_type': query_type.value,
                        'source': 'signal_store',
                        'confidence': confidence,
                        'latency_ms': int((time.time() - start_time) * 1000),
                        'raw_data': metric_data
                    }

            # Handle structured calendar queries (Phase 2.7B Option 5)
            elif query_type == QueryType.STRUCTURED_CALENDAR:
                ticker = self.query_router.extract_ticker(query)
                if ticker:
                    event_type, is_future = self.query_router.extract_event_info(query)
                    calendar_data = self.query_calendar_events(
                        ticker=ticker,
                        event_type=event_type,
                        is_future=is_future
                    )

                    if calendar_data.get('status') == 'success':
                        formatted_answer = self.query_router.format_calendar_result(calendar_data, query)
                        return {
                            'query': query,
                            'answer': formatted_answer,
                            'query_type': query_type.value,
                            'source': 'signal_store',
                            'confidence': confidence,
                            'latency_ms': int((time.time() - start_time) * 1000),
                            'raw_data': calendar_data
                        }

            # Handle structured price target queries (Phase 2.8)
            elif query_type == QueryType.STRUCTURED_PRICE:
                ticker = self.query_router.extract_ticker(query)
                if ticker:
                    price_data = self.query_price(ticker, include_history=True)

                    if price_data.get('status') == 'success':
                        formatted_answer = self.query_router.format_price_target_result(price_data, query)
                        return {
                            'query': query,
                            'answer': formatted_answer,
                            'query_type': query_type.value,
                            'source': 'signal_store',
                            'confidence': confidence,
                            'latency_ms': int((time.time() - start_time) * 1000),
                            'raw_data': price_data
                        }

            # Handle structured pricing history queries (Phase 2.8)
            elif query_type == QueryType.STRUCTURED_PRICING_HISTORY:
                ticker = self.query_router.extract_ticker(query)
                if ticker:
                    pricing_data = self.query_pricing_history(ticker)

                    if pricing_data.get('status') == 'success':
                        formatted_answer = self.query_router.format_pricing_history_result(pricing_data, query)
                        return {
                            'query': query,
                            'answer': formatted_answer,
                            'query_type': query_type.value,
                            'source': 'signal_store',
                            'confidence': confidence,
                            'latency_ms': int((time.time() - start_time) * 1000),
                            'raw_data': pricing_data
                        }

            # Handle semantic queries (route to LightRAG)
            elif query_type in (QueryType.SEMANTIC_WHY, QueryType.SEMANTIC_HOW, QueryType.SEMANTIC_EXPLAIN):
                # Call ICESystemManager directly to avoid infinite recursion
                # (self.core.query() now routes through query_with_router)
                lightrag_result = self.core._system_manager.query_ice(query, mode=mode, use_graph_context=False)

                # BUG FIX: Extract answer string from lightrag_result dict (same issue as fallback path)
                answer_text = lightrag_result.get('answer', lightrag_result.get('result', ''))
                result = {
                    'query': query,
                    'answer': answer_text,  # Primary field (semantic clarity)
                    'result': answer_text,  # Backward compatibility alias (required by add_footnote_citations)
                    'query_type': query_type.value,
                    'source': 'lightrag',
                    'confidence': lightrag_result.get('confidence', confidence),  # Use LightRAG's confidence
                    'latency_ms': int((time.time() - start_time) * 1000)
                }

                # Preserve parsed_context if available (required by add_footnote_citations)
                if 'parsed_context' in lightrag_result:
                    result['parsed_context'] = lightrag_result['parsed_context']

                # Preserve other useful metadata (including 'status' for notebook compatibility)
                for key in ['status', 'sources', 'context', 'references', 'engine', 'mode']:
                    if key in lightrag_result:
                        result[key] = lightrag_result[key]

                return result

            # Handle hybrid queries (both layers)
            elif query_type == QueryType.HYBRID:
                # Get structured data from Signal Store (try ratings and metrics)
                ticker = self.query_router.extract_ticker(query)
                signal_store_data = None

                if ticker:
                    # Try rating query first
                    rating_data = self.query_rating(ticker)
                    if rating_data and rating_data.get('rating') != 'UNKNOWN':
                        signal_store_data = rating_data

                    # Also try metric query
                    metric_type, period = self.query_router.extract_metric_info(query)
                    if metric_type:
                        metric_data = self.query_metric(ticker, metric_type, period)
                        if metric_data and metric_data.get('metric_value') != 'UNKNOWN':
                            # If we have both, combine them
                            if signal_store_data:
                                signal_store_data = {
                                    'rating': rating_data,
                                    'metric': metric_data
                                }
                            else:
                                signal_store_data = metric_data

                # Get semantic context from LightRAG (call directly to avoid recursion)
                lightrag_result = self.core._system_manager.query_ice(query, mode=mode, use_graph_context=False)

                # BUG FIX: Extract answer string from lightrag_result dict
                lightrag_answer = lightrag_result.get('answer', lightrag_result.get('result', ''))

                # Combine results
                combined_answer = f"**Structured Data:**\n"
                if signal_store_data:
                    # Handle combined rating + metric response
                    if isinstance(signal_store_data, dict) and 'rating' in signal_store_data and 'metric' in signal_store_data:
                        combined_answer += self.query_router.format_signal_store_result(signal_store_data['rating'], query)
                        combined_answer += "\n\n"
                        combined_answer += self.query_router.format_signal_store_result(signal_store_data['metric'], query)
                    else:
                        combined_answer += self.query_router.format_signal_store_result(signal_store_data, query)
                else:
                    combined_answer += "No structured data found"

                combined_answer += f"\n\n**Semantic Analysis:**\n{lightrag_answer}"

                result = {
                    'query': query,
                    'answer': combined_answer,  # Primary field (semantic clarity)
                    'result': combined_answer,  # Backward compatibility alias (required by add_footnote_citations)
                    'query_type': query_type.value,
                    'source': 'hybrid',
                    'confidence': confidence,
                    'latency_ms': int((time.time() - start_time) * 1000),
                    'signal_store_data': signal_store_data
                }

                # Preserve parsed_context from LightRAG result (required by add_footnote_citations)
                if 'parsed_context' in lightrag_result:
                    result['parsed_context'] = lightrag_result['parsed_context']

                # Preserve other useful metadata from LightRAG (including 'status' for notebook compatibility)
                for key in ['status', 'sources', 'context', 'references', 'engine', 'mode']:
                    if key in lightrag_result:
                        result[key] = lightrag_result[key]

                return result

        # Fallback: No router available, use LightRAG only
        logger.debug("Query router not available, using LightRAG only")
        # Call ICESystemManager directly to avoid recursion
        lightrag_result = self.core._system_manager.query_ice(query, mode=mode, use_graph_context=False)

        # BUG FIX: Extract answer string from lightrag_result dict (it returns full response structure)
        # lightrag_result is a dict like: {"answer": "text...", "parsed_context": {...}, ...}
        # Preserve all metadata while ensuring answer field is a string
        answer_text = lightrag_result.get('answer', lightrag_result.get('result', ''))
        result = {
            'query': query,
            'answer': answer_text,  # Primary field (semantic clarity)
            'result': answer_text,  # Backward compatibility alias (required by add_footnote_citations)
            'query_type': 'semantic_explain',
            'source': 'lightrag',
            'confidence': lightrag_result.get('confidence', 0.50),  # Use LightRAG's confidence
            'latency_ms': int((time.time() - start_time) * 1000)
        }

        # Preserve parsed_context if available (required by add_footnote_citations)
        if 'parsed_context' in lightrag_result:
            result['parsed_context'] = lightrag_result['parsed_context']

        # Preserve other useful metadata (including 'status' for notebook compatibility)
        for key in ['status', 'sources', 'context', 'references', 'engine', 'mode']:
            if key in lightrag_result:
                result[key] = lightrag_result[key]

        return result

    def ingest_historical_data(self, holdings: List[str], years: int = 2,
                                email_limit: int = 71,
                                news_limit: int = 2,
                                financial_limit: int = 2,
                                market_limit: int = 1,
                                sec_limit: int = 2,
                                research_limit: int = 0,
                                email_files: Optional[List[str]] = None,
                                api_source_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ingest historical data for portfolio holdings (building workflow method)

        Args:
            holdings: List of ticker symbols
            years: Number of years of historical data to fetch (default: 2)
            email_limit: Maximum number of emails to fetch (default: 71)
            news_limit: Maximum number of news articles per symbol (default: 2)
            financial_limit: Maximum number of financial fundamental documents per symbol (default: 2)
            market_limit: Maximum number of market data documents per symbol (default: 1)
            sec_limit: Maximum number of SEC filings per symbol (default: 2)
            research_limit: Maximum number of research documents per symbol (default: 0 - on-demand)
            email_files: Optional list of specific .eml filenames to process (e.g., ['email1.eml'])
                        If provided, only these files are processed. If None, all files are processed.
            api_source_config: Optional dict with granular API switches
                              Keys: api_source_enabled, newsapi_enabled, benzinga_enabled, etc.
                              If None, all APIs with keys are enabled (backward compatible)

        Returns:
            Historical ingestion results with metrics
        """
        from datetime import datetime, timedelta

        start_time = datetime.now()

        # Apply API source configuration if provided
        if api_source_config and hasattr(self.ingester, 'set_api_source_config'):
            self.ingester.set_api_source_config(api_source_config)
            logger.info(f"✅ Applied granular API source configuration")

            # Debug logging to verify config was applied
            if hasattr(self.ingester, 'api_config'):
                enabled_count = sum(1 for k, v in self.ingester.api_config.items()
                                  if k.endswith('_enabled') and k != 'api_source_enabled' and v)
                logger.debug(f"🔍 Config verification: {enabled_count} APIs enabled after config application")
        elif api_source_config:
            logger.warning(f"⚠️ API source config provided but ingester doesn't support it")
        else:
            # Check if ingester already has config before warning
            if hasattr(self.ingester, 'api_config') and self.ingester.api_config:
                # Config already set from previous call, no warning needed
                enabled_count = sum(1 for k, v in self.ingester.api_config.items()
                                  if k.endswith('_enabled') and k != 'api_source_enabled' and v)
                logger.debug(f"🔍 Using existing API config: {enabled_count} APIs enabled")
            else:
                # Warning when no config provided and no existing config - helps detect missing parameter pass from Cell 31
                logger.warning(f"⚠️ No API source configuration provided - using defaults (all APIs with keys enabled)")
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
        print(f"🚀 Starting ingestion for {len(holdings)} holdings ({years} years)...")

        # Initialize entity aggregation for Phase 2.6.1
        all_entities = []

        # Track cumulative document count for progress display
        cumulative_doc_count = 0

        # PRE-FETCH PHASE: Calculate total documents for accurate progress display (Fix for "Document 12/7" bug)
        logger.info("📊 Pre-fetching documents to calculate totals...")
        print("\n📊 Pre-fetching documents to calculate totals...")
        total_all_docs = 0
        prefetched_data = {'emails': [], 'tickers': {}}

        # Pre-fetch emails
        try:
            print("  ⏳ Fetching emails...")
            email_docs = self.ingester.fetch_email_documents(tickers=None, limit=email_limit, email_files=email_files)
            if email_docs:
                prefetched_data['emails'] = email_docs
                total_all_docs += len(email_docs)
                print(f"     ✓ Found {len(email_docs)} emails")
        except Exception as e:
            logger.warning(f"⚠️ Email pre-fetch failed: {e}")
            print(f"     ⚠️ Email fetch failed: {e}")

        # Pre-fetch ticker documents (6 categories)
        for symbol in holdings:
            try:
                print(f"  ⏳ Fetching {symbol} data...")
                news_docs = self.ingester.fetch_company_news(symbol, limit=news_limit, context='portfolio')  # Smart source prioritization
                financial_docs = self.ingester.fetch_financial_fundamentals(symbol, financial_limit)
                market_docs = self.ingester.fetch_market_data(symbol, market_limit)
                sec_docs = self.ingester.fetch_sec_filings(symbol, limit=sec_limit)

                # SEC Company Facts: Free XBRL financial metrics
                sec_facts_docs = []
                if self.config.sec_facts_enabled:
                    sec_facts_docs = self.ingester.fetch_sec_company_facts(symbol)

                research_docs = []  # Research is on-demand, not auto-fetched
                if research_limit > 0:
                    try:
                        research_docs = self.ingester.research_company_deep(symbol, symbol, topics=None, include_competitors=False)[:research_limit]
                    except Exception as e:
                        # Research failures are non-critical but should be logged for visibility
                        logger.warning(f"⚠️ {symbol}: research_company_deep FAILED (non-critical): {type(e).__name__}: {e}")

                prefetched_data['tickers'][symbol] = {
                    'news': news_docs,
                    'financial': financial_docs,
                    'market': market_docs,
                    'sec': sec_docs,
                    'sec_facts': sec_facts_docs,
                    'research': research_docs
                }
                ticker_total = len(news_docs) + len(financial_docs) + len(market_docs) + len(sec_docs) + len(sec_facts_docs) + len(research_docs)
                total_all_docs += ticker_total
                print(f"     ✓ Found {ticker_total} documents (news: {len(news_docs)}, financial: {len(financial_docs)}, market: {len(market_docs)}, SEC: {len(sec_docs)}, SEC Facts: {len(sec_facts_docs)}, research: {len(research_docs)})")
            except Exception as e:
                logger.warning(f"⚠️ {symbol} pre-fetch failed: {e}")
                print(f"     ⚠️ {symbol} fetch failed: {e}")
                prefetched_data['tickers'][symbol] = {'news': [], 'financial': [], 'market': [], 'sec': [], 'sec_facts': [], 'research': []}

        logger.info(f"📊 Total documents to process: {total_all_docs}")
        print(f"\n📊 Total documents to process: {total_all_docs}")
        print("━" * 50)

        # STEP 1: Process portfolio-wide emails
        try:
            email_docs = prefetched_data['emails']
            if email_docs:
                # Capture entities from emails
                if hasattr(self.ingester, 'last_extracted_entities'):
                    all_entities.extend(self.ingester.last_extracted_entities)

                # email_docs now returns List[Dict] with format: {'content': str, 'file_path': 'email:filename.eml', 'type': 'financial'}
                # Extract content and preserve file_path for LightRAG traceability
                email_doc_list = [
                    {
                        'content': doc['content'],  # Extract content from dict
                        'file_path': doc.get('file_path'),  # Pass through file_path for traceability
                        'type': 'email_historical',
                        'symbol': 'PORTFOLIO',
                        'ingestion_mode': 'historical'
                    }
                    for doc in email_docs
                ]

                # Print progress for emails (using total_all_docs for accurate count)
                for idx, doc_dict in enumerate(email_doc_list, start=1):
                    cumulative_doc_count += 1
                    self.core._print_document_progress(
                        doc_index=cumulative_doc_count,
                        total_docs=total_all_docs,  # Fixed: use total across all sources
                        doc_dict=doc_dict,  # Pass full dict for metadata-first detection
                        symbol='PORTFOLIO'
                    )

                email_result = self.core.add_documents_batch(email_doc_list)
                if email_result.get('status') == 'success':
                    results['total_documents'] += len(email_docs)
                    logger.info(f"✅ Historical emails ingested: {len(email_docs)} documents")
        except Exception as e:
            logger.warning(f"⚠️ Historical email ingestion failed (non-fatal): {e}")

        # STEP 2: Loop through holdings for ticker-specific historical data (6 categories)
        for symbol in holdings:
            try:
                # Use prefetched ticker-specific data
                logger.info(f"💰 {symbol}: Processing {years} years of historical data...")
                ticker_data = prefetched_data['tickers'].get(symbol, {})
                news_docs = ticker_data.get('news', [])
                financial_docs = ticker_data.get('financial', [])
                market_docs = ticker_data.get('market', [])
                sec_docs = ticker_data.get('sec', [])
                research_docs = ticker_data.get('research', [])

                # Email entities already captured in STEP 1
                # Ticker-specific sources (news/financials/market/SEC/research) don't extract entities
                # So no new entities to capture here

                # Build document list with SOURCE markers (all 5 ticker categories)
                # Phase 1: Enhanced SOURCE markers with timestamps (retrieval time)
                retrieval_timestamp = datetime.now().isoformat()

                doc_list = []

                # Category 2: News
                for doc_dict in news_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'news'
                    })

                # Category 3: Financial fundamentals
                for doc_dict in financial_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'financial'
                    })

                # Category 4: Market data
                for doc_dict in market_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'market'
                    })

                # Category 5: SEC filings
                for doc_dict in sec_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'regulatory'
                    })

                # Category 6: Research (if any)
                for doc_dict in research_docs:
                    if isinstance(doc_dict, dict) and 'source' in doc_dict:
                        content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                        doc_list.append({
                            'content': content_with_marker,
                            'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                            'type': 'research'
                        })

                if doc_list:
                    # Print progress for each document (using total_all_docs for accurate count)
                    for idx, doc_dict in enumerate(doc_list, start=1):
                        cumulative_doc_count += 1
                        self.core._print_document_progress(
                            doc_index=cumulative_doc_count,
                            total_docs=total_all_docs,  # Fixed: use total across all sources
                            doc_dict=doc_dict,  # Pass full dict for metadata-first detection
                            symbol=symbol
                        )

                    # Apply universal content deduplication before adding to graph
                    doc_list = self.filter_new_documents(doc_list, source_type='api', ticker=symbol)

                    batch_result = self.core.add_documents_batch(doc_list)

                    if batch_result.get('status') == 'success':
                        results['holdings_processed'].append(symbol)
                        results['total_documents'] += len(doc_list)
                        results['metrics']['documents_per_holding'][symbol] = len(doc_list)
                        logger.info(f"✅ {symbol}: {len(doc_list)} historical documents ingested")
                    else:
                        results['failed_holdings'].append({
                            'symbol': symbol,
                            'error': batch_result.get('message', 'Unknown error')
                        })
                else:
                    results['failed_holdings'].append({
                        'symbol': symbol,
                        'error': 'No historical ticker data available'
                    })

            except Exception as e:
                logger.error(f"❌ Error processing historical ticker data for {symbol}: {str(e)}")
                results['failed_holdings'].append({
                    'symbol': symbol,
                    'error': str(e)
                })

        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results['metrics']['processing_time'] = processing_time
        results['metrics']['data_sources_used'] = self.ingester.available_services

        # Aggregate investment signals from Phase 2.6.1 EntityExtractor
        results['metrics']['investment_signals'] = self._aggregate_investment_signals(all_entities)

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

        # STEP 1: Fetch new portfolio-wide emails (if any)
        # For incremental updates, this fetches recent emails (could be filtered by date in future enhancement)
        try:
            email_docs = self.ingester.fetch_email_documents(tickers=None, limit=20)  # Reduced limit for incremental
            if email_docs:
                # email_docs now returns List[Dict] with format: {'content': str, 'file_path': 'email:filename.eml', 'type': 'financial'}
                # Extract content and preserve file_path for LightRAG traceability
                email_doc_list = [
                    {
                        'content': doc['content'],  # Extract content from dict
                        'file_path': doc.get('file_path'),  # Pass through file_path for traceability
                        'type': 'email_incremental',
                        'symbol': 'PORTFOLIO',
                        'ingestion_mode': 'incremental',
                        'update_date': datetime.now().isoformat()
                    }
                    for doc in email_docs
                ]

                email_result = self.core.add_documents_to_existing_graph(email_doc_list)
                if email_result.get('status') == 'success':
                    results['total_new_documents'] += len(email_docs)
                    logger.info(f"✅ Incremental emails added: {len(email_docs)} new documents")
        except Exception as e:
            logger.warning(f"⚠️ Incremental email fetch failed (non-fatal): {e}")

        # STEP 2: Loop through holdings for ticker-specific incremental data
        for symbol in holdings:
            try:
                # Fetch ticker-specific data (not emails, to prevent duplication)
                logger.info(f"💰 {symbol}: Fetching recent data (last {days} days)...")
                financial_docs = self.ingester.fetch_company_financials(symbol, limit=5)  # Returns List[Dict]
                news_docs = self.ingester.fetch_company_news(symbol, limit=5, context='portfolio')  # Returns List[Dict] with smart source prioritization
                sec_docs = self.ingester.fetch_sec_filings(symbol, limit=2)  # Returns List[Dict]

                # Build document list with SOURCE markers
                # Phase 1: Enhanced SOURCE markers with timestamps (retrieval time)
                retrieval_timestamp = datetime.now().isoformat()

                doc_list = []
                for doc_dict in financial_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'financial'
                    })

                for doc_dict in news_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'news'
                    })

                for doc_dict in sec_docs:
                    content_with_marker = f"[SOURCE:{doc_dict['source'].upper()}|SYMBOL:{symbol}|DATE:{retrieval_timestamp}]\n{doc_dict['content']}"
                    doc_list.append({
                        'content': content_with_marker,
                        'file_path': doc_dict.get('file_path'),  # PRESERVE file_path for source attribution
                        'type': 'regulatory'
                    })

                if doc_list:
                    # Apply universal content deduplication before adding to graph
                    doc_list = self.filter_new_documents(doc_list, source_type='api', ticker=symbol)

                    batch_result = self.core.add_documents_to_existing_graph(doc_list)

                    if batch_result.get('status') == 'success':
                        results['holdings_updated'].append(symbol)
                        results['total_new_documents'] += len(doc_list)
                        results['metrics']['new_documents_per_holding'][symbol] = len(doc_list)
                        logger.info(f"✅ {symbol}: {len(doc_list)} new documents added")
                    else:
                        results['failed_holdings'].append({
                            'symbol': symbol,
                            'error': batch_result.get('message', 'Unknown error')
                        })
                else:
                    # No new data is OK for incremental updates
                    results['holdings_updated'].append(symbol)
                    results['metrics']['new_documents_per_holding'][symbol] = 0
                    logger.info(f"ℹ️ No new ticker data for {symbol} (up to date)")

            except Exception as e:
                logger.error(f"❌ Error processing incremental ticker data for {symbol}: {str(e)}")
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

    def ingest_with_manifest(self, holdings: List[str],
                            email_limit: int = 71,
                            news_limit: int = 2,
                            financial_limit: int = 2,
                            market_limit: int = 1,
                            sec_limit: int = 2,
                            research_limit: int = 0,
                            email_files: Optional[List[str]] = None,
                            api_source_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Intelligent incremental ingestion using manifest to prevent duplicates.

        This method uses the IngestionManifest to:
        1. Track which documents have been ingested
        2. Detect portfolio changes (new tickers added/removed)
        3. Only fetch and process genuinely new documents
        4. Update portfolio relevance scores for existing entities

        Args:
            holdings: Current portfolio holdings
            email_limit: Max emails to process
            news_limit: News articles per ticker
            financial_limit: Financial docs per ticker
            market_limit: Market data per ticker
            sec_limit: SEC filings per ticker
            research_limit: Research docs per ticker
            email_files: Specific email files to process
            api_source_config: Optional dict with granular API switches
                              Keys: api_source_enabled, newsapi_enabled, benzinga_enabled, etc.
                              If None, all APIs with keys are enabled (backward compatible)

        Returns:
            Ingestion results with deduplication metrics
        """
        from datetime import datetime, timedelta

        start_time = datetime.now()

        # Apply API source configuration if provided
        if api_source_config and hasattr(self.ingester, 'set_api_source_config'):
            self.ingester.set_api_source_config(api_source_config)
            logger.info(f"✅ Applied granular API source configuration")

            # Debug logging to verify config was applied
            if hasattr(self.ingester, 'api_config'):
                enabled_count = sum(1 for k, v in self.ingester.api_config.items()
                                  if k.endswith('_enabled') and k != 'api_source_enabled' and v)
                logger.debug(f"🔍 Config verification: {enabled_count} APIs enabled after config application")
        elif api_source_config:
            logger.warning(f"⚠️ API source config provided but ingester doesn't support it")
        else:
            # Check if ingester already has config before warning
            if hasattr(self.ingester, 'api_config') and self.ingester.api_config:
                # Config already set from previous call, no warning needed
                enabled_count = sum(1 for k, v in self.ingester.api_config.items()
                                  if k.endswith('_enabled') and k != 'api_source_enabled' and v)
                logger.debug(f"🔍 Using existing API config: {enabled_count} APIs enabled")
            else:
                # Warning when no config provided and no existing config - helps detect missing parameter pass from Cell 31
                logger.warning(f"⚠️ No API source configuration provided - using defaults (all APIs with keys enabled)")

        # Calculate portfolio delta
        portfolio_delta = self.manifest.get_portfolio_delta(holdings)

        results = {
            'status': 'success',
            'portfolio_delta': portfolio_delta,
            'new_documents': 0,
            'skipped_duplicates': 0,
            'updated_documents': 0,
            'new_tickers_data': {},
            # Notebook compatibility: match ingest_historical_data response structure
            'holdings_processed': holdings.copy(),  # All holdings attempted (manifest tracks individually)
            'total_documents': 0,  # Will be set to new_documents count before return
            'failed_holdings': [],  # Track any failures during ingestion
            'metrics': {
                'processing_time': 0.0,
                'manifest_entries': len(self.manifest.manifest['documents']),
                'deduplication_rate': 0.0
            }
        }

        logger.info(f"🔄 Incremental ingestion with manifest")
        logger.info(f"   Portfolio delta: +{portfolio_delta['added']} -{portfolio_delta['removed']}")

        # Track cumulative counts for progress display
        all_new_docs = []
        skipped_count = 0

        # STEP 1: Process emails (check for new ones)
        try:
            logger.info("📧 Checking for new emails...")

            # Fetch available emails
            available_emails = self.ingester.fetch_email_documents(
                tickers=None,  # Universal ingestion
                limit=email_limit,
                email_files=email_files
            )

            # Filter to only genuinely new emails using manifest
            new_emails = []
            for email_doc in available_emails:
                # Generate document ID
                file_path = email_doc.get('file_path', '')
                doc_id = self.manifest.get_document_id('email', file_path.replace('email:', ''))

                # Check if already ingested
                if not self.manifest.is_document_ingested(doc_id):
                    # Also check content hash for duplicates with different names
                    if not self.manifest.is_content_duplicate(email_doc['content']):
                        new_emails.append(email_doc)

                        # Add to manifest
                        self.manifest.add_document(
                            doc_id=doc_id,
                            content=email_doc['content'],
                            metadata={
                                'source_type': 'email',
                                'file_path': file_path,
                                'portfolio_relevance': self._calculate_relevance(email_doc['content'], holdings)
                            }
                        )
                    else:
                        logger.debug(f"Skipping duplicate content: {doc_id}")
                        skipped_count += 1
                else:
                    logger.debug(f"Skipping already ingested: {doc_id}")
                    skipped_count += 1

            # Ingest only new emails
            if new_emails:
                logger.info(f"✅ Found {len(new_emails)} new emails (skipped {skipped_count} duplicates)")

                # Prepare documents for LightRAG
                email_doc_list = [
                    {
                        'content': doc['content'],
                        'file_path': doc.get('file_path'),
                        'type': 'email',
                        'symbol': 'PORTFOLIO',
                        'ingestion_mode': 'incremental_manifest'
                    }
                    for doc in new_emails
                ]

                # Add to existing graph
                email_result = self.core.add_documents_to_existing_graph(email_doc_list)

                if email_result.get('status') == 'success':
                    all_new_docs.extend(email_doc_list)
                    results['new_documents'] += len(new_emails)
            else:
                logger.info(f"ℹ️ No new emails to process ({skipped_count} already in graph)")

        except Exception as e:
            logger.error(f"Email processing failed: {e}")
            results['status'] = 'partial'

        # STEP 2: Process new tickers only (from portfolio delta)
        if portfolio_delta['added']:
            logger.info(f"📊 Fetching data for {len(portfolio_delta['added'])} new tickers: {portfolio_delta['added']}")

            for ticker in portfolio_delta['added']:
                ticker_docs = []

                try:
                    # Fetch all data types for new ticker
                    if news_limit > 0:
                        news_docs = self.ingester.fetch_company_news(ticker, limit=news_limit, context='portfolio')  # Smart source prioritization
                        for doc in news_docs:
                            # Use content hash for stable ID (prevents duplicates on re-fetch)
                            content = doc.get('content', str(doc))
                            content_hash = self.manifest.compute_content_hash(content)[:8]
                            doc_id = self.manifest.get_document_id('api_news', f"{ticker}_{content_hash}")

                            if not self.manifest.is_document_ingested(doc_id):
                                ticker_docs.append(doc)
                                self.manifest.add_document(doc_id, content, {
                                    'source_type': 'api_news',
                                    'ticker': ticker
                                })

                    if financial_limit > 0:
                        financial_docs = self.ingester.fetch_financial_fundamentals(ticker, financial_limit)
                        for doc in financial_docs:
                            # Use content hash for stable ID
                            content = doc.get('content', str(doc))
                            content_hash = self.manifest.compute_content_hash(content)[:8]
                            doc_id = self.manifest.get_document_id('api_financial', f"{ticker}_{content_hash}")

                            if not self.manifest.is_document_ingested(doc_id):
                                ticker_docs.append(doc)
                                self.manifest.add_document(doc_id, content, {
                                    'source_type': 'api_financial',
                                    'ticker': ticker
                                })

                    if sec_limit > 0:
                        sec_docs = self.ingester.fetch_sec_filings(ticker, limit=sec_limit)
                        for doc in sec_docs:
                            # Use content hash for stable ID
                            content = doc.get('content', str(doc))
                            content_hash = self.manifest.compute_content_hash(content)[:8]
                            doc_id = self.manifest.get_document_id('sec', f"{ticker}_{content_hash}")

                            if not self.manifest.is_document_ingested(doc_id):
                                ticker_docs.append(doc)
                                self.manifest.add_document(doc_id, content, {
                                    'source_type': 'sec',
                                    'ticker': ticker
                                })

                    # Add ticker docs to graph
                    if ticker_docs:
                        ticker_result = self.core.add_documents_to_existing_graph(ticker_docs)
                        if ticker_result.get('status') == 'success':
                            results['new_tickers_data'][ticker] = len(ticker_docs)
                            results['new_documents'] += len(ticker_docs)
                            all_new_docs.extend(ticker_docs)
                            logger.info(f"✅ {ticker}: Added {len(ticker_docs)} documents")

                    # Update API coverage in manifest
                    # Track how many documents of each type were actually fetched
                    news_count = len([d for d in ticker_docs if d.get('source', '').lower().startswith('newsapi')])
                    financial_count = len([d for d in ticker_docs if 'financial' in d.get('source', '').lower()])
                    sec_count = len([d for d in ticker_docs if 'sec' in d.get('source', '').lower()])

                    self.manifest.update_api_coverage(ticker, {
                        'news': news_count,
                        'financial': financial_count,
                        'sec': sec_count
                    })

                except Exception as e:
                    logger.error(f"Failed to fetch data for {ticker}: {e}")
                    results['status'] = 'partial'
                    results['failed_holdings'].append({
                        'symbol': ticker,
                        'error': str(e)
                    })

        # STEP 3: Update portfolio in manifest
        self.manifest.update_portfolio(holdings)

        # STEP 4: Save manifest
        self.manifest.save()

        # Calculate final metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results['metrics']['processing_time'] = processing_time
        results['skipped_duplicates'] = skipped_count
        results['total_documents'] = results['new_documents']  # Set for notebook compatibility

        # Calculate deduplication rate
        total_checked = results['new_documents'] + skipped_count
        if total_checked > 0:
            results['metrics']['deduplication_rate'] = (skipped_count / total_checked) * 100

        # Log summary
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 INCREMENTAL INGESTION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"✅ New documents: {results['new_documents']}")
        logger.info(f"⏭️ Skipped duplicates: {results['skipped_duplicates']}")
        logger.info(f"📈 Deduplication rate: {results['metrics']['deduplication_rate']:.1f}%")
        logger.info(f"⏱️ Processing time: {processing_time:.1f}s")
        logger.info(f"📁 Manifest entries: {results['metrics']['manifest_entries']}")

        if portfolio_delta['added']:
            logger.info(f"🆕 New tickers processed: {portfolio_delta['added']}")
        if portfolio_delta['removed']:
            logger.info(f"🗑️ Removed from portfolio: {portfolio_delta['removed']}")

        return results

    def _calculate_relevance(self, content: str, holdings: List[str]) -> float:
        """
        Calculate document relevance to portfolio.

        3-tier scoring system:
        - 1.0: Primary holdings (direct portfolio members)
        - 0.7: Ecosystem players (competitors, suppliers, customers)
        - 0.3: Peripheral entities (market context, broader trends)
        """
        content_upper = content.upper()

        # Check primary holdings (1.0)
        primary_count = sum(1 for ticker in holdings if ticker.upper() in content_upper)
        if primary_count > 0:
            return 1.0  # Primary holdings always 1.0

        # Check ecosystem (0.7)
        ecosystem_keywords = ['semiconductor', 'supply chain', 'competitor', 'customer', 'supplier', 'partner']
        ecosystem_count = sum(1 for keyword in ecosystem_keywords if keyword.upper() in content_upper)
        if ecosystem_count > 0:
            return 0.7  # Ecosystem always 0.7

        # Peripheral (0.3)
        return 0.3  # Default peripheral relevance

    def _format_progress_bar(self, count: int, total: int, width: int = 30) -> str:
        """
        Format visual progress bar for statistics display

        Args:
            count: Number of items in category
            total: Total number of items
            width: Character width of progress bar (default: 30)

        Returns:
            Formatted string with bar, count, and percentage

        Example:
            >>> ice._format_progress_bar(50, 100)
            '███████████████░░░░░░░░░░░░░░░  50 ( 50.0%)'
        """
        if total == 0:
            return '░' * width + '   0 (  0.0%)'

        filled = int(width * count / total)
        bar = '█' * filled + '░' * (width - filled)
        pct = f"{count/total*100:5.1f}%"
        return f"{bar} {count:3d} ({pct})"

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Generate comprehensive 3-tier knowledge graph statistics

        Tier 1: Document source breakdown (email, newsapi, fmp, etc.)
        Tier 2: Graph structure (entities, relationships, connectivity)
        Tier 3: Investment intelligence (signals, ticker coverage)

        Returns:
            Dict with tier1, tier2, tier3 statistics
        """
        import json
        import re
        from pathlib import Path
        from collections import Counter

        stats = {
            'tier1': {},
            'tier2': {},
            'tier3': {}
        }

        storage_path = Path(self.config.working_dir)

        # TIER 1: Document Source Breakdown
        stats['tier1'] = self._get_document_stats(storage_path)

        # TIER 2: Graph Structure Statistics
        stats['tier2'] = self._get_graph_structure_stats(storage_path)

        # TIER 3: Investment Intelligence Metrics
        stats['tier3'] = self._get_investment_intelligence_stats(storage_path)

        # Validate source marker coverage and log recommendations
        diversity = stats['tier1'].get('source_diversity', {})
        coverage = diversity.get('coverage_percentage', 0.0)
        status = diversity.get('status', 'unknown')
        total_docs = stats['tier1'].get('total', 0)
        docs_with_markers = diversity.get('documents_with_markers', 0)

        if coverage < 80.0:
            logger.warning(f"⚠️  SOURCE marker coverage: {coverage:.1f}% ({docs_with_markers}/{total_docs} documents)")
            logger.warning(f"   Only {diversity.get('unique_sources', 0)} unique source(s) detected")
            logger.warning(f"   Recommendation: Set REBUILD_GRAPH=True in ice_building_workflow.ipynb Cell 22")
            logger.warning(f"   This will rebuild the graph with correct SOURCE markers for accurate statistics")
        elif coverage < 100.0:
            logger.info(f"ℹ️  SOURCE marker coverage: {coverage:.1f}% ({docs_with_markers}/{total_docs} documents) - {status}")
        else:
            logger.info(f"✅ SOURCE marker coverage: 100% - All {total_docs} documents properly tagged")

        return stats

    def _get_document_stats(self, storage_path: Path) -> Dict[str, Any]:
        """Parse SOURCE markers from stored documents for Tier 1 statistics"""
        import json
        import re
        from collections import Counter

        doc_status_file = storage_path / 'kv_store_doc_status.json'
        if not doc_status_file.exists():
            return {'total': 0, 'by_source': {}, 'email': 0, 'api_total': 0, 'sec_total': 0}

        docs = json.load(open(doc_status_file))
        source_counts = Counter()

        # Parse SOURCE markers from content
        for doc in docs.values():
            content = doc.get('content_summary', '')

            # Match [SOURCE:NEWSAPI|SYMBOL:NVDA] pattern
            match = re.search(r'\[SOURCE:(\w+)\|', content)
            if match:
                source = match.group(1).lower()
                source_counts[source] += 1
            elif 'SOURCE_EMAIL' in content or '[TICKER:' in content:
                # Email documents use different markup pattern
                source_counts['email'] += 1

        # Calculate totals
        api_sources = {'newsapi', 'finnhub', 'marketaux', 'fmp', 'alpha_vantage', 'polygon', 'benzinga'}
        api_total = sum(source_counts[s] for s in api_sources)
        sec_total = source_counts.get('sec_edgar', 0)
        exa_total = source_counts.get('exa_company', 0) + source_counts.get('exa_competitors', 0)

        # Calculate source diversity metrics
        total_with_markers = sum(source_counts.values())
        total_without_markers = len(docs) - total_with_markers
        unique_sources = len([v for v in source_counts.values() if v > 0])
        coverage_percentage = (total_with_markers / len(docs) * 100) if len(docs) > 0 else 0.0

        # Determine completeness status
        has_email = source_counts.get('email', 0) > 0
        has_api = api_total > 0
        has_sec = sec_total > 0
        expected_sources_present = sum([has_email, has_api, has_sec])

        if expected_sources_present == 3 and coverage_percentage >= 95:
            status = 'complete'
        elif expected_sources_present >= 2 or coverage_percentage >= 50:
            status = 'partial'
        else:
            status = 'incomplete'

        return {
            'total': len(docs),
            'by_source': dict(source_counts),
            'email': source_counts.get('email', 0),
            'api_total': api_total,
            'sec_total': sec_total,
            'exa_total': exa_total,
            **{k: source_counts.get(k, 0) for k in ['newsapi', 'finnhub', 'marketaux', 'benzinga', 'fmp', 'alpha_vantage', 'polygon', 'sec_edgar', 'exa_company', 'exa_competitors']},
            'source_diversity': {
                'unique_sources': unique_sources,
                'expected_sources': 3,  # Email, API, SEC
                'expected_sources_present': expected_sources_present,
                'coverage_percentage': coverage_percentage,
                'documents_with_markers': total_with_markers,
                'documents_without_markers': total_without_markers,
                'status': status
            }
        }

    def _get_graph_structure_stats(self, storage_path: Path) -> Dict[str, Any]:
        """Read VDB files for Tier 2 graph structure statistics"""
        import json

        stats = {
            'total_entities': 0,
            'total_relationships': 0,
            'avg_connections': 0.0
        }

        # Parse entities
        entities_file = storage_path / 'vdb_entities.json'
        if entities_file.exists():
            data = json.load(open(entities_file))
            stats['total_entities'] = len(data.get('data', []))

        # Parse relationships
        rels_file = storage_path / 'vdb_relationships.json'
        if rels_file.exists():
            data = json.load(open(rels_file))
            stats['total_relationships'] = len(data.get('data', []))

        # Calculate connectivity
        if stats['total_entities'] > 0:
            stats['avg_connections'] = stats['total_relationships'] / stats['total_entities']

        return stats

    def _get_investment_intelligence_stats(self, storage_path: Path) -> Dict[str, Any]:
        """Parse entities for Tier 3 investment intelligence metrics"""
        import json

        TICKERS = {'NVDA', 'TSMC', 'AMD', 'ASML', 'INTC', 'QCOM', 'AVGO', 'TXN', 'MU', 'LRCX'}

        stats = {
            'tickers_covered': [],
            'buy_signals': 0,
            'sell_signals': 0,
            'price_targets': 0,
            'risk_mentions': 0
        }

        # Parse entities for investment signals
        entities_file = storage_path / 'vdb_entities.json'
        if not entities_file.exists():
            return stats

        data = json.load(open(entities_file))
        tickers_found = set()

        for entity in data.get('data', []):
            text = f"{entity.get('entity_name', '')} {entity.get('content', '')}".upper()

            # Detect tickers
            for ticker in TICKERS:
                if ticker in text:
                    tickers_found.add(ticker)

            # Detect signals
            if 'BUY' in text or 'RATING:BUY' in text:
                stats['buy_signals'] += 1
            if 'SELL' in text or 'RATING:SELL' in text:
                stats['sell_signals'] += 1
            if 'PRICE TARGET' in text or 'PRICE_TARGET' in text:
                stats['price_targets'] += 1
            if 'RISK' in text:
                stats['risk_mentions'] += 1

        stats['tickers_covered'] = sorted(list(tickers_found))

        return stats


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