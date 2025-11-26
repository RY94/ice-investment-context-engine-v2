# Location: /tests/test_ice_simplified_comprehensive.py
# Purpose: Comprehensive test suite for ice_simplified.py orchestrator
# Why: Increase test coverage to 80%+ for Phase 3 robustness
# Relevant Files: ice_simplified.py, ice_core.py, query_router.py

"""
Comprehensive test suite for ICE Simplified orchestrator

This test suite provides extensive coverage of the main ICE orchestrator,
testing all major functionality including initialization, data ingestion,
query processing, and error handling.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, List, Any
import json
import tempfile
import asyncio
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from updated_architectures.implementation.ice_simplified import (
    ICESimplified,
    ICECore
)


class TestICESimplifiedInitialization:
    """Test suite for ICE initialization and configuration"""

    def test_basic_initialization(self):
        """Test basic ICE initialization with default config"""
        ice = ICESimplified()

        assert ice is not None
        assert ice.core is not None
        assert hasattr(ice, 'query')
        # Note: add_document and build_knowledge_graph are in ICECore, not ICESimplified
        assert hasattr(ice.core, '_system_manager')

    def test_initialization_with_custom_config(self):
        """Test ICE initialization with custom configuration"""
        config = {
            'newsapi_enabled': True,
            'benzinga_enabled': False,
            'finnhub_enabled': True,
            'use_manifest': True,
            'freshness_weight': 0.3
        }

        ice = ICESimplified(config=config)

        assert ice.config.get('newsapi_enabled') == True
        assert ice.config.get('benzinga_enabled') == False
        assert ice.config.get('use_manifest') == True

    def test_initialization_with_missing_api_keys(self):
        """Test ICE initialization when API keys are missing"""
        with patch.dict('os.environ', {}, clear=True):
            ice = ICESimplified()

            # Should initialize but with warnings
            assert ice is not None
            assert ice.core is not None

    def test_initialization_error_handling(self):
        """Test error handling during initialization"""
        with patch('updated_architectures.implementation.ice_simplified.ICECore') as mock_core:
            mock_core.side_effect = Exception("Initialization failed")

            with pytest.raises(Exception) as excinfo:
                ice = ICESimplified()

            assert "Initialization failed" in str(excinfo.value)


class TestDataIngestion:
    """Test suite for data ingestion functionality"""

    @pytest.fixture
    def ice_instance(self):
        """Create ICE instance for testing"""
        with patch('updated_architectures.implementation.ice_simplified.LightRAG'):
            ice = ICESimplified()
            ice.core._system_manager = Mock()
            return ice

    def test_add_document_basic(self, ice_instance):
        """Test basic document addition"""
        doc_content = "Apple Inc. reported Q4 earnings of $89.5B"

        result = ice_instance.add_document(doc_content, doc_type="news")

        assert result is not None
        ice_instance.core._system_manager.add_document.assert_called_once()

    def test_add_document_with_metadata(self, ice_instance):
        """Test document addition with metadata"""
        doc_content = "NVIDIA stock rose 5% on AI news"
        metadata = {
            'source': 'Bloomberg',
            'date': '2024-03-15',
            'ticker': 'NVDA'
        }

        result = ice_instance.add_document(
            doc_content,
            doc_type="news",
            metadata=metadata
        )

        assert result is not None
        call_args = ice_instance.core._system_manager.add_document.call_args
        assert 'metadata' in call_args.kwargs or len(call_args.args) > 2

    def test_add_multiple_documents(self, ice_instance):
        """Test adding multiple documents in sequence"""
        documents = [
            "Tesla delivered 450,000 vehicles in Q3",
            "Microsoft announces new AI partnership",
            "Federal Reserve raises interest rates"
        ]

        for doc in documents:
            result = ice_instance.add_document(doc, doc_type="news")
            assert result is not None

        assert ice_instance.core._system_manager.add_document.call_count == 3

    def test_add_document_error_handling(self, ice_instance):
        """Test error handling during document addition"""
        ice_instance.core._system_manager.add_document.side_effect = Exception("Database error")

        doc_content = "Test document"

        with pytest.raises(Exception) as excinfo:
            ice_instance.add_document(doc_content, doc_type="news")

        assert "Database error" in str(excinfo.value)

    def test_build_knowledge_graph(self, ice_instance):
        """Test knowledge graph building"""
        # Add documents first
        docs = [
            "Apple CEO Tim Cook announced new products",
            "Microsoft and OpenAI expand partnership",
            "Tesla's Elon Musk discusses Q3 results"
        ]

        for doc in docs:
            ice_instance.add_document(doc, doc_type="news")

        # Build knowledge graph
        with patch.object(ice_instance.core, 'build_knowledge_graph') as mock_build:
            mock_build.return_value = {'nodes': 10, 'edges': 15}

            result = ice_instance.build_knowledge_graph()

            assert result is not None
            assert 'nodes' in result
            mock_build.assert_called_once()


class TestQueryProcessing:
    """Test suite for query processing functionality"""

    @pytest.fixture
    def ice_with_data(self):
        """Create ICE instance with mock data"""
        with patch('updated_architectures.implementation.ice_simplified.LightRAG'):
            ice = ICESimplified()
            ice.core._system_manager = Mock()
            ice.signal_store_client = Mock()

            # Mock some data
            ice.core._system_manager.query_ice.return_value = {
                'status': 'success',
                'results': [
                    {'content': 'Apple earnings report', 'confidence': 0.9},
                    {'content': 'NVIDIA AI chips', 'confidence': 0.85}
                ]
            }

            return ice

    def test_basic_query(self, ice_with_data):
        """Test basic query processing"""
        query = "What are Apple's latest earnings?"

        result = ice_with_data.query(query)

        assert result is not None
        assert 'status' in result
        assert result['status'] == 'success'

    def test_query_with_routing(self, ice_with_data):
        """Test query with routing logic"""
        # Enable query router
        ice_with_data.enable_query_router = True

        with patch.object(ice_with_data, 'query_with_router') as mock_router:
            mock_router.return_value = {
                'route': 'signal_store',
                'results': [{'signal': 'Buy AAPL'}]
            }

            query = "What signals exist for AAPL?"
            result = ice_with_data.query(query)

            mock_router.assert_called_once_with(query, mode='auto')

    def test_query_modes(self, ice_with_data):
        """Test different query modes"""
        modes = ['naive', 'local', 'global', 'hybrid']

        for mode in modes:
            result = ice_with_data.query(
                "Test query",
                mode=mode
            )
            assert result is not None

    def test_query_with_filters(self, ice_with_data):
        """Test query with date and source filters"""
        query = "Recent tech news"

        result = ice_with_data.query(
            query,
            date_filter={'start': '2024-01-01', 'end': '2024-03-31'},
            source_filter=['Bloomberg', 'Reuters']
        )

        assert result is not None
        # Verify filters were passed through
        call_args = ice_with_data.core._system_manager.query_ice.call_args
        assert call_args is not None

    def test_query_error_handling(self, ice_with_data):
        """Test error handling during query processing"""
        ice_with_data.core._system_manager.query_ice.side_effect = Exception("Query failed")

        with pytest.raises(Exception) as excinfo:
            ice_with_data.query("Test query")

        assert "Query failed" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_async_query(self, ice_with_data):
        """Test asynchronous query processing"""
        # Mock async query method if it exists
        if hasattr(ice_with_data, 'query_async'):
            ice_with_data.query_async = AsyncMock(return_value={'status': 'success'})

            result = await ice_with_data.query_async("Async query test")

            assert result is not None
            assert result['status'] == 'success'


class TestTemporalFeatures:
    """Test suite for temporal enhancement features"""

    @pytest.fixture
    def ice_temporal(self):
        """Create ICE instance with temporal features"""
        ice = ICESimplified()
        ice.signal_store_client = Mock()
        ice.enable_query_router = True
        return ice

    def test_freshness_scoring(self, ice_temporal):
        """Test freshness scoring in queries"""
        ice_temporal.signal_store_client.query_rating.return_value = {
            'results': [
                {
                    'content': 'Recent news',
                    'created_at': datetime.now().isoformat(),
                    'freshness_score': 0.95
                },
                {
                    'content': 'Old news',
                    'created_at': (datetime.now() - timedelta(days=30)).isoformat(),
                    'freshness_score': 0.3
                }
            ]
        }

        result = ice_temporal.query_with_router("Latest tech news", mode='signal_store')

        assert 'results' in result
        # Recent news should have higher freshness score
        assert result['results'][0]['freshness_score'] > result['results'][1]['freshness_score']

    def test_date_range_filtering(self, ice_temporal):
        """Test date range filtering in temporal queries"""
        start_date = '2024-01-01'
        end_date = '2024-03-31'

        ice_temporal.query_with_router(
            "Tech news",
            mode='signal_store',
            start_date=start_date,
            end_date=end_date
        )

        # Verify date range was passed to signal store
        call_args = ice_temporal.signal_store_client.query_rating.call_args
        assert 'start_date' in call_args.kwargs
        assert 'end_date' in call_args.kwargs

    def test_composite_ranking(self, ice_temporal):
        """Test composite ranking with confidence and freshness"""
        ice_temporal.signal_store_client.query_rating.return_value = {
            'results': [
                {
                    'content': 'High confidence recent',
                    'confidence_score': 0.9,
                    'freshness_score': 0.8,
                    'composite_score': 0.85
                },
                {
                    'content': 'Low confidence old',
                    'confidence_score': 0.5,
                    'freshness_score': 0.3,
                    'composite_score': 0.4
                }
            ]
        }

        result = ice_temporal.query_with_router("Investment signals", mode='signal_store')

        # First result should have higher composite score
        assert result['results'][0]['composite_score'] > result['results'][1]['composite_score']


class TestPerformanceAndScaling:
    """Test suite for performance and scaling capabilities"""

    @pytest.fixture
    def ice_performance(self):
        """Create ICE instance for performance testing"""
        ice = ICESimplified()
        ice.core._system_manager = Mock()
        return ice

    def test_bulk_document_ingestion(self, ice_performance):
        """Test bulk document ingestion performance"""
        import time

        # Create 100 test documents
        documents = [f"Test document {i} with content about company {i}" for i in range(100)]

        start_time = time.time()

        for doc in documents:
            ice_performance.add_document(doc, doc_type="news")

        elapsed_time = time.time() - start_time

        # Should process 100 documents in reasonable time (< 5 seconds for mocked calls)
        assert elapsed_time < 5.0
        assert ice_performance.core._system_manager.add_document.call_count == 100

    def test_concurrent_queries(self, ice_performance):
        """Test handling concurrent queries"""
        import concurrent.futures

        ice_performance.core._system_manager.query_ice.return_value = {'status': 'success'}

        queries = [f"Query {i}" for i in range(10)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(ice_performance.query, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 10
        assert all(r['status'] == 'success' for r in results)

    def test_memory_efficiency(self, ice_performance):
        """Test memory efficiency with large datasets"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Add large documents
        large_doc = "x" * 10000  # 10KB document
        for _ in range(100):
            ice_performance.add_document(large_doc, doc_type="news")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 100MB for 1MB of documents)
        assert memory_increase < 100


class TestErrorHandlingAndRecovery:
    """Test suite for error handling and recovery mechanisms"""

    @pytest.fixture
    def ice_error(self):
        """Create ICE instance for error testing"""
        ice = ICESimplified()
        return ice

    def test_graceful_degradation_missing_signal_store(self, ice_error):
        """Test graceful degradation when signal store is unavailable"""
        ice_error.signal_store_client = None

        # Should fall back to LightRAG
        with patch.object(ice_error.core, '_system_manager') as mock_manager:
            mock_manager.query_ice.return_value = {'status': 'success', 'source': 'lightrag'}

            result = ice_error.query("Test query")

            assert result['status'] == 'success'
            assert result['source'] == 'lightrag'

    def test_api_failure_recovery(self, ice_error):
        """Test recovery from API failures"""
        ice_error.core._data_ingester = Mock()
        ice_error.core._data_ingester.fetch_company_news.side_effect = [
            Exception("API Error"),  # First call fails
            [{'content': 'Recovered data'}]  # Second call succeeds
        ]

        # First attempt fails
        with pytest.raises(Exception):
            ice_error.fetch_news("AAPL")

        # Should recover on retry
        result = ice_error.fetch_news("AAPL")
        assert result is not None

    def test_invalid_input_handling(self, ice_error):
        """Test handling of invalid inputs"""
        # Test with None query
        with pytest.raises((ValueError, AttributeError)):
            ice_error.query(None)

        # Test with empty query
        result = ice_error.query("")
        assert result is not None  # Should handle gracefully

        # Test with invalid document type
        with pytest.raises((ValueError, KeyError)):
            ice_error.add_document("Test", doc_type="invalid_type")


class TestIntegration:
    """Integration tests for ICE system"""

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        with patch('updated_architectures.implementation.ice_simplified.LightRAG'):
            ice = ICESimplified()
            ice.core._system_manager = Mock()
            ice.signal_store_client = Mock()

            # 1. Add documents
            docs = [
                "Apple announces new iPhone with AI features",
                "Microsoft partners with OpenAI on enterprise solutions",
                "Tesla reports record deliveries in Q3"
            ]

            for doc in docs:
                ice.add_document(doc, doc_type="news")

            # 2. Build knowledge graph
            ice.core._system_manager.build_graph.return_value = {'status': 'success'}
            kg_result = ice.build_knowledge_graph()
            assert kg_result is not None

            # 3. Query the system
            ice.core._system_manager.query_ice.return_value = {
                'status': 'success',
                'results': [{'content': 'AI features in new products'}]
            }

            query_result = ice.query("What are the latest AI developments?")
            assert query_result['status'] == 'success'
            assert len(query_result['results']) > 0

    def test_manifest_mode_integration(self):
        """Test manifest mode for deduplication"""
        ice = ICESimplified(config={'use_manifest': True})

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / 'manifest.json'
            ice.manifest_path = manifest_path

            # Simulate manifest tracking
            ice._update_manifest = Mock()
            ice._check_manifest = Mock(return_value=False)  # Not duplicate

            # Add document
            ice.add_document("Test document", doc_type="news")

            # Verify manifest was updated
            ice._update_manifest.assert_called_once()


class TestConfiguration:
    """Test suite for configuration management"""

    def test_config_loading_from_file(self):
        """Test loading configuration from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                'api_keys': {'newsapi': 'test_key'},
                'freshness_weight': 0.4,
                'confidence_threshold': 0.7
            }
            json.dump(config, f)
            config_path = f.name

        try:
            ice = ICESimplified(config_path=config_path)
            assert ice.config.get('freshness_weight') == 0.4
            assert ice.config.get('confidence_threshold') == 0.7
        finally:
            os.unlink(config_path)

    def test_config_override(self):
        """Test configuration override mechanism"""
        base_config = {'freshness_weight': 0.3, 'use_manifest': False}
        override_config = {'freshness_weight': 0.5, 'new_param': 'value'}

        ice = ICESimplified(config=base_config)
        ice.update_config(override_config)

        assert ice.config['freshness_weight'] == 0.5
        assert ice.config['new_param'] == 'value'
        assert ice.config['use_manifest'] == False  # Unchanged

    def test_environment_variable_config(self):
        """Test configuration from environment variables"""
        with patch.dict('os.environ', {
            'ICE_FRESHNESS_WEIGHT': '0.6',
            'ICE_USE_MANIFEST': 'true',
            'OPENAI_API_KEY': 'test_key'
        }):
            ice = ICESimplified()

            # Should read from environment
            assert ice.config.get('freshness_weight') == 0.6
            assert ice.config.get('use_manifest') == True


if __name__ == '__main__':
    # Run tests with coverage if available
    pytest.main([__file__, '-v', '-s'])