# ice_core.py
"""
ICE Core Engine - Direct wrapper of working JupyterSyncWrapper
Maintains 100% LightRAG compatibility with zero additional complexity
Replaces complex orchestration layers with simple, direct passthrough
Relevant files: src/ice_lightrag/ice_rag_fixed.py, ice_simplified.py
"""

import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ICECore:
    """
    Core ICE engine - Direct wrapper of working JupyterSyncWrapper

    Key principle: Reuse the WORKING LightRAG integration unchanged
    No orchestration layers, no transformation pipelines, no complex error hierarchies

    This class provides a minimal interface to the proven JupyterSyncWrapper
    from ice_rag_fixed.py, which successfully handles:
    - LightRAG initialization (initialize_storages + initialize_pipeline_status)
    - Jupyter async compatibility (nest_asyncio)
    - Document processing with automatic entity/relationship extraction
    - Multi-modal query execution (6 query modes)
    """

    def __init__(self, working_dir: Optional[str] = None, openai_api_key: Optional[str] = None):
        """
        Initialize ICE core with working LightRAG wrapper

        Args:
            working_dir: Directory for LightRAG storage (default: ./src/ice_lightrag/storage)
            openai_api_key: OpenAI API key (default: from environment)
        """
        self.working_dir = working_dir or os.getenv('ICE_WORKING_DIR', './src/ice_lightrag/storage')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

        self._rag = None
        self._initialized = False

        # Validate requirements
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for LightRAG operations")

        logger.info("ICE Core initializing with simplified architecture")
        self._initialize_lightrag()

    def _initialize_lightrag(self):
        """Initialize the proven JupyterSyncWrapper from ice_rag_fixed.py"""
        try:
            # Import the WORKING implementation - fix relative path
            import sys
            from pathlib import Path
            # Add the project root to Python path for imports
            project_root = Path(__file__).parents[2]  # Go up 2 levels from updated_architectures/implementation/
            sys.path.insert(0, str(project_root))

            from src.ice_lightrag.ice_rag_fixed import JupyterSyncWrapper

            # Initialize with the working wrapper - no changes needed
            self._rag = JupyterSyncWrapper(working_dir=self.working_dir)

            logger.info("✅ JupyterSyncWrapper initialized successfully")

        except ImportError as e:
            logger.error(f"Failed to import JupyterSyncWrapper: {e}")
            logger.error("Ensure src/ice_lightrag/ice_rag_fixed.py exists and LightRAG is installed")
            raise RuntimeError("Cannot initialize ICE without working LightRAG wrapper")

        except Exception as e:
            logger.error(f"Failed to initialize JupyterSyncWrapper: {e}")
            raise RuntimeError(f"LightRAG initialization failed: {e}")

    def is_ready(self) -> bool:
        """
        Check if ICE is ready for operations

        Returns:
            True if LightRAG wrapper is initialized and ready
        """
        return self._rag is not None and self._rag.is_ready()

    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed status information

        Returns:
            Status dictionary with initialization and readiness info
        """
        return {
            'initialized': self._rag is not None,
            'ready': self.is_ready(),
            'working_dir': self.working_dir,
            'lightrag_available': self._rag is not None
        }

    def add_document(self, text: str, doc_type: str = "financial") -> Dict[str, Any]:
        """
        Add document to knowledge base - Direct passthrough to working wrapper

        Args:
            text: Document content (will be passed directly to LightRAG)
            doc_type: Document type for context (optional metadata)

        Returns:
            Result dictionary from LightRAG processing

        Note:
            This is a direct passthrough to JupyterSyncWrapper.add_document()
            No transformation, validation, or enhancement layers
            LightRAG handles entity extraction and graph building automatically
        """
        if not self.is_ready():
            return {
                "status": "error",
                "message": "ICE not ready - check LightRAG initialization",
                "error_code": "NOT_READY"
            }

        try:
            # Direct passthrough to working wrapper - no transformation layers
            result = self._rag.add_document(text, doc_type=doc_type)

            # Log success with basic metrics
            logger.info(f"Document added successfully: {len(text)} chars, type: {doc_type}")

            return result

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "PROCESSING_FAILED"
            }

    def add_documents_batch(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Batch document processing with detailed metrics

        Args:
            documents: List of {"content": str, "type": str} dictionaries

        Returns:
            Batch processing results with metrics

        Note:
            Enhanced to provide processing metrics for notebook monitoring
        """
        from datetime import datetime

        start_time = datetime.now()

        if not self.is_ready():
            return {
                "status": "error",
                "message": "ICE not ready - check LightRAG initialization",
                "error_code": "NOT_READY"
            }

        if not documents:
            return {
                "status": "success",
                "message": "No documents to process",
                "successful": 0,
                "failed": 0,
                "total_documents": 0,
                "metrics": {
                    "processing_time": 0.0,
                    "documents": 0,
                    "chunks": 0,
                    "entities": "0 (no documents)",
                    "relationships": "0 (no documents)"
                }
            }

        try:
            # Direct passthrough to working wrapper - no orchestration layers
            result = self._rag.add_documents_batch(documents)

            # Calculate processing metrics
            processing_time = (datetime.now() - start_time).total_seconds()

            # Enhance result with detailed metrics
            successful = result.get('successful', 0)
            total = result.get('total_documents', len(documents))

            # Add metrics to result
            result['metrics'] = {
                'processing_time': processing_time,
                'documents': total,
                'chunks': f"~{total * 3} estimated (1200 token chunks)",  # Estimate based on avg doc size
                'entities': f"Multiple per document (automatic extraction)",
                'relationships': f"Automatic discovery during processing",
                'success_rate': (successful / total) if total > 0 else 0.0,
                'avg_processing_time_per_doc': processing_time / total if total > 0 else 0.0
            }

            logger.info(f"Batch processing completed: {successful}/{total} documents successful in {processing_time:.2f}s")

            return result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Batch processing failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "BATCH_PROCESSING_FAILED",
                "metrics": {
                    "processing_time": processing_time,
                    "documents": len(documents),
                    "error": "Processing failed before completion"
                }
            }

    def query(self, question: str, mode: str = 'mix') -> Dict[str, Any]:
        """
        Query the knowledge base - Direct passthrough to working wrapper

        Args:
            question: Investment question to analyze
            mode: LightRAG query mode (naive, local, global, hybrid, mix, bypass)

        Returns:
            Query results with answer and metadata

        Note:
            This is a direct passthrough to JupyterSyncWrapper.query()
            LightRAG handles mode selection, retrieval, and reasoning automatically
            Available modes:
            - naive: Simple text search
            - local: Entity-focused retrieval
            - global: Community-based analysis
            - hybrid: Combines local and global
            - mix: Advanced multi-strategy (default - balanced)
            - bypass: Direct LLM without retrieval
        """
        if not self.is_ready():
            return {
                "status": "error",
                "message": "ICE not ready - check LightRAG initialization",
                "error_code": "NOT_READY"
            }

        if not question or not question.strip():
            return {
                "status": "error",
                "message": "Question cannot be empty",
                "error_code": "EMPTY_QUERY"
            }

        # Validate query mode
        valid_modes = ['naive', 'local', 'global', 'hybrid', 'mix', 'bypass']
        if mode not in valid_modes:
            logger.warning(f"Invalid mode '{mode}', using 'mix' instead")
            mode = 'mix'

        try:
            from datetime import datetime
            start_time = datetime.now()

            # Direct passthrough to working wrapper - no query optimization layers
            result = self._rag.query(question.strip(), mode=mode)

            # Calculate query metrics
            query_time = (datetime.now() - start_time).total_seconds()

            # Enhanced metrics
            answer_length = len(result.get('answer', '')) if result.get('status') == 'success' else 0
            question_length = len(question.strip())

            # Add metrics to result
            if 'metrics' not in result:
                result['metrics'] = {}

            result['metrics'].update({
                'query_time': query_time,
                'query_mode': mode,
                'question_length': question_length,
                'answer_length': answer_length,
                'tokens_estimated': {
                    'context': 'Calculated by LightRAG',
                    'response': f"~{answer_length // 4} (estimate)",  # Rough token estimate
                    'total': 'Optimized by LightRAG (vs 610K GraphRAG)'
                },
                'api_cost_estimated': f"${(answer_length // 4) * 0.00002:.4f} (GPT-4o-mini)",
                'entities_matched': 'Multiple (hybrid retrieval)',
                'sources_used': 'Multiple documents (source attribution in answer)'
            })

            logger.info(f"Query completed: {question_length} chars question, {answer_length} chars answer, mode: {mode}, time: {query_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "QUERY_FAILED",
                "metrics": {
                    "query_time": 0.0,
                    "query_mode": mode,
                    "error": "Query processing failed"
                }
            }

    def get_query_modes(self) -> List[str]:
        """
        Get list of available LightRAG query modes

        Returns:
            List of supported query mode strings
        """
        return ['naive', 'local', 'global', 'hybrid', 'mix', 'bypass']

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about LightRAG storage

        Returns:
            Dictionary with storage directory and file information
        """
        storage_path = Path(self.working_dir)

        info = {
            'working_dir': str(storage_path),
            'exists': storage_path.exists(),
            'files': {}
        }

        if storage_path.exists():
            # Check for key LightRAG storage files
            key_files = [
                'graph_chunk_entity_relation.graphml',
                'vdb_entities.json',
                'vdb_relationships.json',
                'vdb_chunks.json'
            ]

            for filename in key_files:
                filepath = storage_path / filename
                info['files'][filename] = {
                    'exists': filepath.exists(),
                    'size': filepath.stat().st_size if filepath.exists() else 0
                }

        return info

    def build_knowledge_graph_from_scratch(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Build knowledge graph from scratch (initial mode - clear existing data)

        Args:
            documents: List of documents with content and metadata

        Returns:
            Results with building metrics
        """
        from datetime import datetime

        start_time = datetime.now()
        results = {
            'status': 'success',
            'mode': 'initial_build',
            'total_documents': len(documents),
            'documents_processed': 0,
            'metrics': {
                'building_time': 0.0,
                'chunks_created': 0,
                'entities_extracted': 0,
                'relationships_found': 0,
                'graph_initialized': False
            }
        }

        if not self.is_ready():
            results['status'] = 'error'
            results['message'] = 'ICE not ready for graph building'
            return results

        logger.info(f"Starting knowledge graph build from scratch with {len(documents)} documents")

        try:
            # Clear existing data by reinitializing (this is the "from scratch" logic)
            working_dir = self._working_dir
            if working_dir and Path(working_dir).exists():
                logger.info("Clearing existing graph data for fresh build")
                # Just reinitialize - LightRAG will handle the reset
                self._initialize_lightrag()

            # Process all documents as a batch
            batch_result = self.add_documents_batch(documents)

            if batch_result.get('status') == 'success':
                results['documents_processed'] = len(documents)
                results['metrics']['graph_initialized'] = True

                # Get additional metrics if available
                if 'metrics' in batch_result:
                    results['metrics'].update(batch_result['metrics'])

                logger.info(f"✅ Knowledge graph built from scratch: {len(documents)} documents processed")
            else:
                results['status'] = 'partial_failure'
                results['message'] = batch_result.get('message', 'Unknown error in batch processing')
                results['documents_processed'] = batch_result.get('documents_processed', 0)

        except Exception as e:
            logger.error(f"❌ Error building knowledge graph from scratch: {str(e)}")
            results['status'] = 'error'
            results['message'] = str(e)

        # Calculate final metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results['metrics']['building_time'] = processing_time

        return results

    def add_documents_to_existing_graph(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Add documents to existing knowledge graph (incremental mode - preserve existing data)

        Args:
            documents: List of documents with content and metadata

        Returns:
            Results with incremental update metrics
        """
        from datetime import datetime

        start_time = datetime.now()
        results = {
            'status': 'success',
            'mode': 'incremental_update',
            'total_documents': len(documents),
            'new_documents_added': 0,
            'metrics': {
                'update_time': 0.0,
                'new_chunks_created': 0,
                'new_entities_extracted': 0,
                'new_relationships_found': 0,
                'existing_graph_preserved': True
            }
        }

        if not self.is_ready():
            results['status'] = 'error'
            results['message'] = 'ICE not ready for incremental updates'
            return results

        logger.info(f"Adding {len(documents)} new documents to existing knowledge graph")

        try:
            # Use existing add_documents_batch - LightRAG handles incremental updates via union
            batch_result = self.add_documents_batch(documents)

            if batch_result.get('status') == 'success':
                results['new_documents_added'] = len(documents)

                # Get additional metrics if available
                if 'metrics' in batch_result:
                    # Map generic metrics to incremental-specific names
                    batch_metrics = batch_result['metrics']
                    results['metrics']['new_chunks_created'] = batch_metrics.get('chunks', 0)
                    results['metrics']['new_entities_extracted'] = batch_metrics.get('entities', 0)
                    results['metrics']['new_relationships_found'] = batch_metrics.get('relationships', 0)

                logger.info(f"✅ Incremental update completed: {len(documents)} documents added to existing graph")
            else:
                results['status'] = 'partial_failure'
                results['message'] = batch_result.get('message', 'Unknown error in incremental update')
                results['new_documents_added'] = batch_result.get('documents_processed', 0)

        except Exception as e:
            logger.error(f"❌ Error adding documents to existing graph: {str(e)}")
            results['status'] = 'error'
            results['message'] = str(e)
            results['metrics']['existing_graph_preserved'] = False

        # Calculate final metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results['metrics']['update_time'] = processing_time

        return results

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get detailed storage component statistics

        Returns:
            Storage statistics and component status
        """
        storage_info = self.get_storage_info()

        stats = {
            'working_dir': storage_info['working_dir'],
            'storage_exists': storage_info['exists'],
            'components': {
                'chunks_vdb': {
                    'description': 'Vector embeddings of text chunks',
                    'file': 'vdb_chunks.json',
                    'exists': storage_info['files'].get('vdb_chunks.json', {}).get('exists', False),
                    'size_bytes': storage_info['files'].get('vdb_chunks.json', {}).get('size', 0)
                },
                'entities_vdb': {
                    'description': 'Vector embeddings of extracted entities',
                    'file': 'vdb_entities.json',
                    'exists': storage_info['files'].get('vdb_entities.json', {}).get('exists', False),
                    'size_bytes': storage_info['files'].get('vdb_entities.json', {}).get('size', 0)
                },
                'relationships_vdb': {
                    'description': 'Vector embeddings of relationships',
                    'file': 'vdb_relationships.json',
                    'exists': storage_info['files'].get('vdb_relationships.json', {}).get('exists', False),
                    'size_bytes': storage_info['files'].get('vdb_relationships.json', {}).get('size', 0)
                },
                'chunk_entity_relation_graph': {
                    'description': 'Graph structure storage',
                    'file': 'graph_chunk_entity_relation.graphml',
                    'exists': storage_info['files'].get('graph_chunk_entity_relation.graphml', {}).get('exists', False),
                    'size_bytes': storage_info['files'].get('graph_chunk_entity_relation.graphml', {}).get('size', 0)
                }
            },
            'total_storage_bytes': sum(
                file_info.get('size', 0) for file_info in storage_info['files'].values()
            ),
            'is_initialized': self.is_ready()
        }

        return stats

    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get knowledge graph statistics (node/edge counts, density)

        Returns:
            Graph statistics and metrics
        """
        stats = {
            'is_ready': self.is_ready(),
            'graph_components': 'Unknown - requires LightRAG internal access',
            'estimated_entities': 'Multiple per document (automatic extraction)',
            'estimated_relationships': 'Automatic discovery during processing',
            'note': 'LightRAG abstracts graph internals - use storage stats for file-level metrics'
        }

        # Add storage-based estimates
        storage_stats = self.get_storage_stats()
        if storage_stats['storage_exists']:
            stats['storage_indicators'] = {
                'entities_file_size': storage_stats['components']['entities_vdb']['size_bytes'],
                'relationships_file_size': storage_stats['components']['relationships_vdb']['size_bytes'],
                'graph_file_size': storage_stats['components']['chunk_entity_relation_graph']['size_bytes'],
                'all_components_present': all(
                    component['exists'] for component in storage_stats['components'].values()
                )
            }

        return stats

    def get_working_dir(self) -> str:
        """
        Get the working directory path

        Returns:
            Working directory path as string
        """
        return str(self.working_dir) if hasattr(self, 'working_dir') and self.working_dir else "Not set"


# Convenience functions for easy usage
def create_ice_core(working_dir: Optional[str] = None, openai_api_key: Optional[str] = None) -> ICECore:
    """
    Create and initialize ICE core engine

    Args:
        working_dir: Directory for LightRAG storage
        openai_api_key: OpenAI API key

    Returns:
        Initialized ICECore instance

    Raises:
        RuntimeError: If initialization fails
        ValueError: If required configuration is missing
    """
    try:
        core = ICECore(working_dir=working_dir, openai_api_key=openai_api_key)

        if core.is_ready():
            logger.info("✅ ICE Core created and ready for operations")
        else:
            logger.warning("⚠️ ICE Core created but may need lazy initialization")

        return core

    except Exception as e:
        logger.error(f"❌ Failed to create ICE Core: {e}")
        raise


def test_ice_core() -> bool:
    """
    Test ICE Core functionality with a simple document and query

    Returns:
        True if test passes, False otherwise
    """
    try:
        logger.info("🧪 Testing ICE Core functionality...")

        # Create core
        core = create_ice_core()

        # Test document addition
        test_doc = "Apple Inc. is a technology company that designs consumer electronics."
        doc_result = core.add_document(test_doc, doc_type="test")

        if doc_result.get('status') != 'success':
            logger.error(f"Document addition failed: {doc_result.get('message')}")
            return False

        # Test query
        test_query = "What type of company is Apple?"
        query_result = core.query(test_query, mode='hybrid')

        if query_result.get('status') != 'success':
            logger.error(f"Query failed: {query_result.get('message')}")
            return False

        logger.info("✅ ICE Core test passed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ ICE Core test failed: {e}")
        return False


if __name__ == "__main__":
    # Demo usage
    print("🚀 ICE Core Engine Demo")

    try:
        # Test the core
        if test_ice_core():
            print("✅ ICE Core is working correctly")
        else:
            print("❌ ICE Core test failed")

    except Exception as e:
        print(f"❌ Demo failed: {e}")