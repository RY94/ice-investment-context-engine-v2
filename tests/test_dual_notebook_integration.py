#!/usr/bin/env python3
"""
File: tests/test_dual_notebook_integration.py
Purpose: Integration tests for dual notebook workflow implementation
Business Purpose: Validate building and query workflows work end-to-end

Tests the integration between ice_simplified.py methods and the dual notebook design
to ensure all required methods exist and return proper metrics.

RELEVANT FILES: ice_simplified.py, ice_core.py, ice_building_workflow.ipynb, ice_query_workflow.ipynb
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestDualNotebookIntegration(unittest.TestCase):
    """Integration tests for dual notebook workflow"""

    def setUp(self):
        """Set up test environment"""
        self.holdings = ['NVDA', 'TSMC', 'AMD', 'ASML']

    def test_ice_simplified_methods_exist(self):
        """Test that all required methods exist in ice_simplified.py"""
        from updated_architectures.implementation.ice_simplified import ICESimplified

        # Check building workflow methods
        self.assertTrue(hasattr(ICESimplified, 'ingest_historical_data'))
        self.assertTrue(hasattr(ICESimplified, 'ingest_incremental_data'))
        self.assertTrue(hasattr(ICESimplified, 'ingest_portfolio_data'))
        self.assertTrue(hasattr(ICESimplified, 'analyze_portfolio'))

    def test_ice_core_methods_exist(self):
        """Test that all required methods exist in ice_core.py"""
        from updated_architectures.implementation.ice_core import ICECore

        # Check core workflow methods
        self.assertTrue(hasattr(ICECore, 'build_knowledge_graph_from_scratch'))
        self.assertTrue(hasattr(ICECore, 'add_documents_to_existing_graph'))
        self.assertTrue(hasattr(ICECore, 'get_storage_stats'))
        self.assertTrue(hasattr(ICECore, 'get_graph_stats'))
        self.assertTrue(hasattr(ICECore, 'get_working_dir'))
        self.assertTrue(hasattr(ICECore, 'get_query_modes'))

    def test_query_modes_validation(self):
        """Test that all 6 official query modes are supported"""
        from updated_architectures.implementation.ice_core import ICECore

        # Mock the initialization to avoid needing real API keys
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}), \
             patch.object(ICECore, '_initialize_lightrag'), \
             patch.object(ICECore, 'is_ready', return_value=True):

            core = ICECore()
            valid_modes = core.get_query_modes()

            # Should be exactly 6 modes including 'bypass'
            expected_modes = ['naive', 'local', 'global', 'hybrid', 'mix', 'bypass']
            self.assertEqual(set(valid_modes), set(expected_modes))
            self.assertEqual(len(valid_modes), 6)
            self.assertNotIn('kg', valid_modes)  # 'kg' is not an official mode
            self.assertIn('bypass', valid_modes)  # 'bypass' should be included

    def test_bypass_mode_query(self):
        """Test that bypass mode works correctly (direct LLM without retrieval)"""
        from updated_architectures.implementation.ice_core import ICECore

        # Mock the initialization and query response
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}), \
             patch.object(ICECore, '_initialize_lightrag'), \
             patch.object(ICECore, 'is_ready', return_value=True):

            core = ICECore()
            core._rag = Mock()

            # Mock query response for bypass mode
            core._rag.query.return_value = {
                'status': 'success',
                'answer': 'Direct LLM response without knowledge graph retrieval'
            }

            # Test bypass mode query
            result = core.query("What are general investment strategies?", mode='bypass')

            # Verify the query was called with bypass mode
            core._rag.query.assert_called_once_with(
                "What are general investment strategies?",
                mode='bypass'
            )

            # Verify metrics are still added
            self.assertIn('status', result)
            self.assertIn('metrics', result)
            self.assertEqual(result['metrics']['query_mode'], 'bypass')
            self.assertIn('query_time', result['metrics'])

    def test_building_workflow_methods_return_metrics(self):
        """Test that building workflow methods return proper metrics"""
        from updated_architectures.implementation.ice_simplified import ICESimplified

        # Mock the system to avoid needing real API keys
        with patch.object(ICESimplified, '__init__', return_value=None), \
             patch.object(ICESimplified, 'is_ready', return_value=True):

            ice = ICESimplified()
            ice.ingester = Mock()
            ice.core = Mock()

            # Mock core methods to return expected format
            ice.core.add_documents_batch.return_value = {
                'status': 'success',
                'metrics': {'processing_time': 1.0}
            }
            ice.core.build_knowledge_graph_from_scratch.return_value = {
                'status': 'success',
                'mode': 'initial_build',
                'total_documents': 4,
                'metrics': {'building_time': 2.0}
            }
            ice.core.add_documents_to_existing_graph.return_value = {
                'status': 'success',
                'mode': 'incremental_update',
                'total_documents': 4,
                'metrics': {'update_time': 1.5}
            }

            # Mock ingester
            ice.ingester.fetch_comprehensive_data.return_value = ['sample document']
            ice.ingester.available_services = ['demo_service']

            # Test historical data method returns metrics
            result = ice.ingest_historical_data(self.holdings, years=2)

            self.assertIn('status', result)
            self.assertIn('metrics', result)
            self.assertIn('processing_time', result['metrics'])
            self.assertIn('data_sources_used', result['metrics'])
            self.assertEqual(result['time_period'], '2 years')

            # Test incremental data method returns metrics
            result = ice.ingest_incremental_data(self.holdings, days=7)

            self.assertIn('status', result)
            self.assertIn('metrics', result)
            self.assertIn('processing_time', result['metrics'])
            self.assertEqual(result['time_period'], 'last 7 days')

    def test_query_workflow_methods_return_metrics(self):
        """Test that query workflow methods return proper metrics"""
        from updated_architectures.implementation.ice_core import ICECore

        # Mock the initialization and query response
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}), \
             patch.object(ICECore, '_initialize_lightrag'), \
             patch.object(ICECore, 'is_ready', return_value=True):

            core = ICECore()
            core._rag = Mock()

            # Mock query response
            core._rag.query.return_value = {
                'status': 'success',
                'answer': 'Sample investment analysis response'
            }

            # Test query method returns metrics (using default mode 'mix')
            result = core.query("What are the risks for NVIDIA?", mode='mix')

            self.assertIn('status', result)
            self.assertIn('metrics', result)
            self.assertIn('query_time', result['metrics'])
            self.assertIn('query_mode', result['metrics'])
            self.assertIn('answer_length', result['metrics'])
            self.assertIn('api_cost_estimated', result['metrics'])

    def test_default_query_mode(self):
        """Test that default query mode is 'mix' when not specified"""
        from updated_architectures.implementation.ice_core import ICECore

        # Mock the initialization and query response
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}), \
             patch.object(ICECore, '_initialize_lightrag'), \
             patch.object(ICECore, 'is_ready', return_value=True):

            core = ICECore()
            core._rag = Mock()

            # Mock query response
            core._rag.query.return_value = {
                'status': 'success',
                'answer': 'Response using default mode'
            }

            # Test query without specifying mode (should use 'mix' as default)
            result = core.query("What is the market outlook?")

            # Verify 'mix' mode was used as default
            core._rag.query.assert_called_once_with(
                "What is the market outlook?",
                mode='mix'
            )

            # Verify metrics show 'mix' as the mode
            self.assertEqual(result['metrics']['query_mode'], 'mix')

    def test_storage_inspection_methods(self):
        """Test storage inspection methods work properly"""
        from updated_architectures.implementation.ice_core import ICECore

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}), \
             patch.object(ICECore, '_initialize_lightrag'), \
             patch.object(ICECore, 'is_ready', return_value=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:

            # Mock file stats
            mock_stat.return_value.st_size = 1024 * 1024  # 1MB

            core = ICECore(working_dir='/tmp/test')

            # Test storage stats
            storage_stats = core.get_storage_stats()

            self.assertIn('components', storage_stats)
            self.assertIn('chunks_vdb', storage_stats['components'])
            self.assertIn('entities_vdb', storage_stats['components'])
            self.assertIn('relationships_vdb', storage_stats['components'])
            self.assertIn('chunk_entity_relation_graph', storage_stats['components'])

            # Test graph stats
            graph_stats = core.get_graph_stats()
            self.assertIn('is_ready', graph_stats)

            # Test working dir
            working_dir = core.get_working_dir()
            self.assertIsInstance(working_dir, str)

    def test_notebook_files_exist(self):
        """Test that notebook files were created"""
        building_notebook = project_root / 'ice_building_workflow.ipynb'
        query_notebook = project_root / 'ice_query_workflow.ipynb'

        self.assertTrue(building_notebook.exists(), "Building notebook should exist")
        self.assertTrue(query_notebook.exists(), "Query notebook should exist")

        # Test notebook content structure
        import json

        with open(building_notebook) as f:
            building_nb = json.load(f)

        with open(query_notebook) as f:
            query_nb = json.load(f)

        # Verify notebook structure
        self.assertIn('cells', building_nb)
        self.assertIn('cells', query_nb)
        self.assertTrue(len(building_nb['cells']) > 6)  # Should have 6+ sections
        self.assertTrue(len(query_nb['cells']) > 6)     # Should have 6+ sections

    def test_workflow_mode_logic_implementation(self):
        """Test workflow mode logic (initial vs update) is implemented"""
        from updated_architectures.implementation.ice_core import ICECore

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}), \
             patch.object(ICECore, '_initialize_lightrag'), \
             patch.object(ICECore, 'is_ready', return_value=True):

            core = ICECore()

            # Mock methods exist and have mode-specific behavior
            self.assertTrue(hasattr(core, 'build_knowledge_graph_from_scratch'))
            self.assertTrue(hasattr(core, 'add_documents_to_existing_graph'))

            # Test methods have different signatures indicating mode support
            import inspect

            scratch_sig = inspect.signature(core.build_knowledge_graph_from_scratch)
            incremental_sig = inspect.signature(core.add_documents_to_existing_graph)

            # Both should take documents parameter
            self.assertIn('documents', scratch_sig.parameters)
            self.assertIn('documents', incremental_sig.parameters)

    def test_deprecated_design_archived(self):
        """Test that deprecated design file was properly archived"""
        deprecated_file = project_root / 'ICE_MAIN_NOTEBOOK_DESIGN_V2.md'
        archive_dir = project_root / 'archive' / 'deprecated_designs'

        # Original file should not exist
        self.assertFalse(deprecated_file.exists(), "Deprecated file should be archived")

        # Archive directory should exist
        self.assertTrue(archive_dir.exists(), "Archive directory should exist")

        # Archived file should exist with timestamp
        archived_files = list(archive_dir.glob('ICE_MAIN_NOTEBOOK_DESIGN_V2_*.md'))
        self.assertTrue(len(archived_files) > 0, "Archived file should exist with timestamp")


class TestMethodIntegration(unittest.TestCase):
    """Test integration between methods as used in notebooks"""

    def test_building_to_query_workflow_integration(self):
        """Test that building workflow outputs can be used by query workflow"""
        from updated_architectures.implementation.ice_simplified import create_ice_system

        # This tests the integration pattern used in notebooks
        with patch('updated_architectures.implementation.ice_simplified.ICESimplified') as MockICE:
            mock_ice = Mock()
            MockICE.return_value = mock_ice
            mock_ice.is_ready.return_value = True

            # Mock building workflow outputs
            mock_ice.ingest_historical_data.return_value = {
                'status': 'success',
                'holdings_processed': ['NVDA', 'TSMC'],
                'total_documents': 10,
                'metrics': {'processing_time': 5.0}
            }

            mock_ice.core.build_knowledge_graph_from_scratch.return_value = {
                'status': 'success',
                'total_documents': 10,
                'metrics': {'building_time': 3.0}
            }

            # Mock query workflow inputs
            mock_ice.analyze_portfolio.return_value = {
                'status': 'success',
                'risk_analysis': {'NVDA': {'status': 'success', 'analysis': 'Risk analysis'}},
                'summary': {'total_holdings': 2}
            }

            mock_ice.core.query.return_value = {
                'status': 'success',
                'answer': 'Investment analysis response',
                'metrics': {'query_time': 1.5}
            }

            # Test integration workflow
            ice = create_ice_system()

            # Building workflow
            self.assertTrue(ice.is_ready())
            build_result = ice.ingest_historical_data(['NVDA', 'TSMC'])
            self.assertEqual(build_result['status'], 'success')

            # Query workflow using built system
            analysis_result = ice.analyze_portfolio(['NVDA', 'TSMC'])
            self.assertEqual(analysis_result['status'], 'success')

            query_result = ice.core.query("Test query")
            self.assertEqual(query_result['status'], 'success')

            # Verify metrics are propagated
            self.assertIn('metrics', build_result)
            self.assertIn('metrics', query_result)


if __name__ == '__main__':
    # Configure test output
    print("🧪 Running Dual Notebook Integration Tests")
    print("━" * 50)

    # Run tests
    unittest.main(verbosity=2)