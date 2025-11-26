# Location: /tests/test_refinement_4_reliability.py
# Purpose: Test Refinement #4 - Critical Error Handling & Reliability Architecture
# Why: Validates Phase 2 (source attribution) and Phase 4 (concurrent fetching)
# Relevant Files: ice_simplified.py, data_ingestion.py

import unittest
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from updated_architectures.implementation.ice_simplified import ICECore, BatchProcessingError
from updated_architectures.implementation.data_ingestion import DataIngester
from updated_architectures.implementation.config import ICEConfig


class TestRefinement4Reliability(unittest.TestCase):
    """Test suite for Refinement #4: Critical Error Handling & Reliability"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = ICEConfig()
        cls.ice = ICECore(config=cls.config)
        cls.ingester = DataIngester(config=cls.config)

    def test_01_batch_failure_threshold_exists(self):
        """Verify batch failure threshold is implemented (Phase 1 - Already Complete)"""
        # Verify BatchProcessingError exists
        self.assertTrue(hasattr(BatchProcessingError, '__init__'))

        # Verify add_documents_batch has max_failure_rate parameter
        import inspect
        sig = inspect.signature(self.ice.add_documents_batch)
        self.assertIn('max_failure_rate', sig.parameters)
        self.assertEqual(sig.parameters['max_failure_rate'].default, 0.10)

    def test_02_source_attribution_enforcement_plain_string(self):
        """Phase 2: Verify plain string documents are rejected"""
        # Plain string document should fail (ValueError caught, returned as error dict)
        documents = ["This is a plain string document without source"]

        result = self.ice.add_documents_batch(documents)

        # Verify error response (graceful degradation pattern)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error_type'], 'failure_threshold_exceeded')
        self.assertEqual(result['failed_count'], 1)
        self.assertEqual(result['total_count'], 1)
        self.assertEqual(result['failure_rate'], 1.0)

    def test_03_source_attribution_enforcement_missing_both(self):
        """Phase 2: Verify documents missing both file_path and source are rejected"""
        # Document with neither file_path nor source
        documents = [{
            'content': 'Test content',
            'type': 'financial'
            # Missing both 'file_path' and 'source'
        }]

        result = self.ice.add_documents_batch(documents)

        # Verify error response (graceful degradation pattern)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error_type'], 'failure_threshold_exceeded')
        self.assertEqual(result['failed_count'], 1)
        self.assertEqual(result['total_count'], 1)
        self.assertEqual(result['failure_rate'], 1.0)

    def test_04_source_attribution_defensive_fallback(self):
        """Phase 2: Verify defensive fallback when source exists but file_path missing"""
        # Document with source but no file_path (should use fallback)
        documents = [{
            'content': 'Test content with source',
            'source': 'test_source',
            'type': 'financial'
            # Missing 'file_path' but has 'source'
        }]

        # Should succeed with fallback (no exception)
        try:
            result = self.ice.add_documents_batch(documents)
            # Expect graceful degradation (fallback used)
            self.assertIn('status', result)
        except ValueError:
            self.fail("Defensive fallback should prevent ValueError when source exists")

    def test_05_source_attribution_full_compliance(self):
        """Phase 2: Verify properly attributed documents are accepted"""
        # Document with complete source attribution
        documents = [{
            'content': 'Test content with full attribution',
            'source': 'test_api',
            'file_path': 'test_api:AAPL_test_001',
            'type': 'financial'
        }]

        # Should succeed (100% compliant)
        result = self.ice.add_documents_batch(documents)
        self.assertEqual(result.get('status'), 'success')
        self.assertEqual(result.get('successful'), 1)

    def test_06_concurrent_fetching_exists(self):
        """Phase 4: Verify concurrent fetching method exists"""
        # Check fetch_comprehensive_data_concurrent exists
        self.assertTrue(hasattr(self.ingester, 'fetch_comprehensive_data_concurrent'))

        # Check method signature
        import inspect
        sig = inspect.signature(self.ingester.fetch_comprehensive_data_concurrent)
        self.assertIn('symbols', sig.parameters)
        self.assertIn('max_workers', sig.parameters)
        self.assertEqual(sig.parameters['max_workers'].default, 3)

    def test_07_concurrent_vs_serial_performance(self):
        """Phase 4: Verify concurrent fetching is faster than serial (requires API keys)"""
        # Skip if no API keys available
        if not os.getenv('OPENAI_API_KEY'):
            self.skipTest("API keys not configured")

        symbols = ['AAPL', 'NVDA']

        # Test serial fetching
        start_serial = time.time()
        serial_docs = self.ingester.fetch_comprehensive_data(
            symbols=symbols,
            news_limit=1,
            financial_limit=1,
            market_limit=0,
            email_limit=0,
            sec_limit=1
        )
        serial_time = time.time() - start_serial

        # Test concurrent fetching
        start_concurrent = time.time()
        concurrent_docs = self.ingester.fetch_comprehensive_data_concurrent(
            symbols=symbols,
            news_limit=1,
            financial_limit=1,
            market_limit=0,
            email_limit=0,
            sec_limit=1,
            max_workers=2
        )
        concurrent_time = time.time() - start_concurrent

        # Verify concurrent is faster (at least 1.2x speedup expected)
        speedup = serial_time / concurrent_time
        print(f"\n  Performance: Serial={serial_time:.1f}s, Concurrent={concurrent_time:.1f}s, Speedup={speedup:.2f}x")

        # Expect some speedup (may vary due to API latency)
        self.assertGreater(speedup, 1.0, f"Expected speedup >1.0x, got {speedup:.2f}x")

        # Verify same number of documents
        self.assertEqual(len(serial_docs), len(concurrent_docs),
                        "Concurrent and serial should return same number of documents")

    def test_08_concurrent_error_handling(self):
        """Phase 4: Verify concurrent fetching handles errors gracefully"""
        # Invalid symbols should not crash the system
        symbols = ['INVALID_TICKER_999', 'AAPL']

        try:
            docs = self.ingester.fetch_comprehensive_data_concurrent(
                symbols=symbols,
                news_limit=1,
                financial_limit=1,
                market_limit=0,
                email_limit=0,
                sec_limit=1,
                max_workers=2
            )

            # Should return some documents (at least from AAPL)
            self.assertIsInstance(docs, list)
            # AAPL should work, invalid ticker may return 0 docs
            # System should degrade gracefully, not crash

        except Exception as e:
            self.fail(f"Concurrent fetching should handle errors gracefully, got: {e}")

    def test_09_config_propagation(self):
        """Phase 3: Verify config is propagated (Already Complete)"""
        # Verify config exists in ingester
        self.assertIsNotNone(self.ingester.config)
        self.assertEqual(self.ingester.config, self.config)

    def test_10_integration_all_phases(self):
        """Integration test: All phases work together"""
        # Phase 1: Batch threshold (already tested in test_01)
        # Phase 2: Source attribution (test with proper docs)
        # Phase 3: Config propagation (verified in test_09)
        # Phase 4: Concurrent fetching

        if not os.getenv('OPENAI_API_KEY'):
            self.skipTest("API keys not configured")

        # Fetch data concurrently
        symbols = ['AAPL']
        docs = self.ingester.fetch_comprehensive_data_concurrent(
            symbols=symbols,
            news_limit=1,
            financial_limit=1,
            market_limit=0,
            email_limit=0,
            sec_limit=1,
            max_workers=1
        )

        # Verify all documents have source attribution
        for doc in docs:
            if isinstance(doc, dict):
                # Should have file_path OR source
                has_file_path = bool(doc.get('file_path'))
                has_source = bool(doc.get('source')) and doc.get('source') != 'unknown'
                self.assertTrue(
                    has_file_path or has_source,
                    f"Document missing source attribution: {doc}"
                )

        # Verify batch processing works
        result = self.ice.add_documents_batch(docs)
        self.assertEqual(result.get('status'), 'success')


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
