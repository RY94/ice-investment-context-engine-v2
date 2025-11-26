# Location: /tests/test_batch_failure_threshold.py
# Purpose: Test batch processing failure threshold mechanism
# Why: Verify that batch processing stops when failure rate exceeds threshold
# Relevant Files: updated_architectures/implementation/ice_simplified.py

"""
Unit tests for batch processing failure threshold mechanism.
Tests that document batch processing stops when failure rate exceeds the configured threshold,
preventing silent data loss and ensuring data quality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from updated_architectures.implementation.ice_simplified import ICECore, BatchProcessingError


class TestBatchFailureThreshold:
    """Test suite for batch processing failure threshold"""

    @pytest.fixture
    def mock_ice_system(self):
        """Create mock ICESystemManager for testing"""
        mock = Mock()
        mock.is_ready.return_value = True
        mock.get_status.return_value = {
            'status': 'healthy',
            'components': {'lightrag': 'ready', 'storage': 'ready'}
        }
        return mock

    @pytest.fixture
    def ice_core(self, mock_ice_system):
        """Create ICECore instance with mocked system manager"""
        with patch('updated_architectures.implementation.ice_simplified.get_ice_system') as mock_get:
            mock_get.return_value = mock_ice_system
            ice = ICECore()
            ice._system_manager = mock_ice_system
            ice._initialized = True
            return ice

    def test_batch_succeeds_below_threshold(self, ice_core, mock_ice_system):
        """Test that batch processing continues when failure rate is below threshold"""
        # Setup: 8 success, 1 failure = 11.1% failure rate (below default 10% threshold)
        documents = [
            {'content': f'doc{i}', 'file_path': f'test:{i}'} for i in range(9)
        ]

        # Mock responses: 8 successes, 1 failure
        mock_ice_system.add_document.side_effect = [
            {'status': 'success'} if i < 8 else {'status': 'error', 'message': 'Failed'}
            for i in range(9)
        ]

        # Execute - should NOT raise exception as we're at 11.1% (just above 10%)
        # Actually, let me fix this - with 9 documents, 1 failure = 11.1%, which SHOULD fail
        # Let's use 10 documents with 1 failure = 10% exactly (at threshold, should succeed)
        documents = [
            {'content': f'doc{i}', 'file_path': f'test:{i}'} for i in range(10)
        ]

        mock_ice_system.add_document.side_effect = [
            {'status': 'success'} if i < 9 else {'status': 'error', 'message': 'Failed'}
            for i in range(10)
        ]

        result = ice_core.add_documents_batch(documents, max_failure_rate=0.10)

        # Verify
        assert result['status'] == 'success'
        assert result['successful'] == 9
        assert result['failed'] == 1
        assert result['total'] == 10
        assert mock_ice_system.add_document.call_count == 10

    def test_batch_fails_above_threshold(self, ice_core, mock_ice_system):
        """Test that batch processing stops when failure rate exceeds threshold"""
        # Setup: 10 documents, will fail on 3rd document (30% failure rate > 10% threshold)
        documents = [
            {'content': f'doc{i}', 'file_path': f'test:{i}'} for i in range(10)
        ]

        # Mock responses: First 7 succeed, then 3 fail (but should stop at 2nd failure)
        def mock_add_document(content, doc_type=None, file_path=None):
            # Extract document index from content
            idx = int(content.replace('doc', ''))
            if idx in [2, 3, 4]:  # Fail documents 2, 3, 4
                return {'status': 'error', 'message': f'Failed doc {idx}'}
            return {'status': 'success'}

        mock_ice_system.add_document.side_effect = mock_add_document

        # Execute - should raise BatchProcessingError
        result = ice_core.add_documents_batch(documents, max_failure_rate=0.10)

        # Verify error response
        assert result['status'] == 'error'
        assert result['error_type'] == 'failure_threshold_exceeded'
        assert result['failed_count'] == 2  # Should stop at 2nd failure (20% > 10%)
        assert result['threshold'] == 0.10
        # Call count should be less than 10 (stopped early)
        assert mock_ice_system.add_document.call_count == 4  # 2 success + 2 failures

    def test_custom_failure_threshold(self, ice_core, mock_ice_system):
        """Test that custom failure threshold works correctly"""
        # Setup: 10 documents with 50% failure threshold
        documents = [
            {'content': f'doc{i}', 'file_path': f'test:{i}'} for i in range(10)
        ]

        # Mock responses: 4 successes, 6 failures (40% failure rate < 50% threshold)
        mock_ice_system.add_document.side_effect = [
            {'status': 'success'} if i < 6 else {'status': 'error', 'message': 'Failed'}
            for i in range(10)
        ]

        # Execute with 50% threshold - should succeed
        result = ice_core.add_documents_batch(documents, max_failure_rate=0.50)

        # Verify
        assert result['status'] == 'success'
        assert result['successful'] == 6
        assert result['failed'] == 4
        assert result['total'] == 10

    def test_zero_threshold_fails_on_first_error(self, ice_core, mock_ice_system):
        """Test that zero threshold fails immediately on first error"""
        documents = [
            {'content': f'doc{i}', 'file_path': f'test:{i}'} for i in range(5)
        ]

        # First document fails
        mock_ice_system.add_document.side_effect = [
            {'status': 'error', 'message': 'Failed'},
            {'status': 'success'},
            {'status': 'success'},
            {'status': 'success'},
            {'status': 'success'},
        ]

        # Execute with 0% threshold
        result = ice_core.add_documents_batch(documents, max_failure_rate=0.0)

        # Verify - should fail immediately
        assert result['status'] == 'error'
        assert result['error_type'] == 'failure_threshold_exceeded'
        assert result['failed_count'] == 1
        assert mock_ice_system.add_document.call_count == 1

    def test_exception_counted_as_failure(self, ice_core, mock_ice_system):
        """Test that exceptions are counted towards failure threshold"""
        documents = [
            {'content': f'doc{i}', 'file_path': f'test:{i}'} for i in range(10)
        ]

        # Mock responses: Some succeed, some raise exceptions
        def mock_add_document(content, doc_type=None, file_path=None):
            idx = int(content.replace('doc', ''))
            if idx == 1:
                raise ValueError("Invalid document format")
            elif idx == 2:
                raise RuntimeError("Processing error")
            return {'status': 'success'}

        mock_ice_system.add_document.side_effect = mock_add_document

        # Execute - should fail when exceptions exceed threshold
        result = ice_core.add_documents_batch(documents, max_failure_rate=0.10)

        # Verify
        assert result['status'] == 'error'
        assert result['error_type'] == 'failure_threshold_exceeded'
        assert result['failed_count'] == 2  # 2 exceptions = 20% > 10%
        assert result['threshold'] == 0.10

    def test_batch_with_all_failures(self, ice_core, mock_ice_system):
        """Test batch processing with 100% failure rate"""
        documents = [
            {'content': f'doc{i}', 'file_path': f'test:{i}'} for i in range(5)
        ]

        # All documents fail
        mock_ice_system.add_document.return_value = {'status': 'error', 'message': 'Failed'}

        # Execute - should fail after 2nd document (20% > 10%)
        result = ice_core.add_documents_batch(documents, max_failure_rate=0.10)

        # Verify
        assert result['status'] == 'error'
        assert result['error_type'] == 'failure_threshold_exceeded'
        assert mock_ice_system.add_document.call_count == 1  # Stops at first failure with 0 success

    def test_batch_with_no_failures(self, ice_core, mock_ice_system):
        """Test batch processing with 0% failure rate"""
        documents = [
            {'content': f'doc{i}', 'file_path': f'test:{i}'} for i in range(20)
        ]

        # All documents succeed
        mock_ice_system.add_document.return_value = {'status': 'success'}

        # Execute
        result = ice_core.add_documents_batch(documents)

        # Verify
        assert result['status'] == 'success'
        assert result['successful'] == 20
        assert result['failed'] == 0
        assert result['total'] == 20
        assert mock_ice_system.add_document.call_count == 20

    def test_batch_error_includes_partial_results(self, ice_core, mock_ice_system):
        """Test that partial results are included when batch fails"""
        documents = [
            {'content': f'doc{i}', 'file_path': f'test:{i}'} for i in range(10)
        ]

        # First 5 succeed, then failures
        mock_ice_system.add_document.side_effect = [
            {'status': 'success'} if i < 5 else {'status': 'error', 'message': f'Failed {i}'}
            for i in range(10)
        ]

        # Execute with low threshold
        result = ice_core.add_documents_batch(documents, max_failure_rate=0.10)

        # Verify partial results are included
        assert result['status'] == 'error'
        assert result['error_type'] == 'failure_threshold_exceeded'
        assert result['successful'] >= 5  # At least 5 succeeded before failure
        assert 'results' in result  # Partial results included
        assert 'errors' in result  # Error details included

    def test_empty_batch(self, ice_core, mock_ice_system):
        """Test handling of empty document batch"""
        documents = []

        # Execute
        result = ice_core.add_documents_batch(documents)

        # Verify - should handle gracefully
        assert result['status'] == 'error'  # No successful documents
        assert result['total'] == 0
        assert result['successful'] == 0
        assert result['failed'] == 0

    def test_batch_with_mixed_document_types(self, ice_core, mock_ice_system):
        """Test batch processing with both string and dict documents"""
        documents = [
            'Plain text document 1',  # String document (will log warning)
            {'content': 'Dict doc 1', 'file_path': 'test:1'},  # Dict with file_path
            {'content': 'Dict doc 2'},  # Dict without file_path (will log warning)
            'Plain text document 2',
        ]

        # All succeed
        mock_ice_system.add_document.return_value = {'status': 'success'}

        # Execute
        with patch('updated_architectures.implementation.ice_simplified.logger') as mock_logger:
            result = ice_core.add_documents_batch(documents)

        # Verify
        assert result['status'] == 'success'
        assert result['successful'] == 4
        # Verify warnings were logged for documents without file_path
        warning_calls = [call for call in mock_logger.warning.call_args_list]
        assert len(warning_calls) >= 2  # At least 2 warnings for missing file_path


if __name__ == '__main__':
    pytest.main([__file__, '-v'])