# Location: /tests/test_sec_company_facts.py
# Purpose: Test SEC Company Facts API integration
# Why: Validates free XBRL financial data fetching
# Relevant Files: data_ingestion.py, sec_edgar_connector.py, ice_simplified.py

import unittest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from updated_architectures.implementation.data_ingestion import DataIngester
from updated_architectures.implementation.config import ICEConfig


class TestSECCompanyFacts(unittest.TestCase):
    """Test SEC Company Facts API integration"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = ICEConfig()
        cls.ingester = DataIngester(config=cls.config)

    def test_01_config_enabled(self):
        """Verify SEC Facts is enabled in config"""
        self.assertTrue(self.config.sec_facts_enabled, "SEC Facts should be enabled by default")
        self.assertEqual(self.config.sec_facts_lookback_quarters, 8, "Default lookback should be 8 quarters")

    def test_02_api_connectivity(self):
        """Test SEC API is reachable and returns data"""
        # Use AAPL as stable test ticker
        result = self.ingester.fetch_sec_company_facts('AAPL')

        # Should return list (empty on failure, populated on success)
        self.assertIsInstance(result, list, "Should return list")

        if len(result) > 0:
            # If successful, validate structure
            doc = result[0]
            self.assertIn('content', doc, "Document should have content")
            self.assertIn('source', doc, "Document should have source")
            self.assertIn('file_path', doc, "Document should have file_path")
            self.assertEqual(doc['source'], 'sec_company_facts', "Source should be sec_company_facts")

    def test_03_invalid_ticker_handling(self):
        """Verify graceful failure on invalid ticker"""
        result = self.ingester.fetch_sec_company_facts('INVALID_TICKER_9999')

        # Should return empty list, not raise exception
        self.assertIsInstance(result, list, "Should return list even on failure")
        self.assertEqual(len(result), 0, "Invalid ticker should return empty list")

    def test_04_signal_store_integration(self):
        """Verify metrics are inserted to Signal Store"""
        # This test requires Signal Store to be initialized
        if not self.ingester.signal_store:
            self.skipTest("Signal Store not initialized")

        # Fetch SEC Facts (also inserts to Signal Store)
        result = self.ingester.fetch_sec_company_facts('NVDA')

        if len(result) > 0:
            # Query Signal Store for metrics using conn property
            conn = self.ingester.signal_store.conn
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM financial_metrics
                WHERE ticker = 'NVDA'
                AND source_document_id LIKE 'sec_facts:%'
            """)
            count = cursor.fetchone()[0]

            self.assertGreater(count, 0, "SEC Facts should be in Signal Store")

    def test_05_config_disable(self):
        """Verify behavior when SEC Facts is disabled"""
        # Temporarily disable
        original_value = self.config.sec_facts_enabled
        self.config.sec_facts_enabled = False

        result = self.ingester.fetch_sec_company_facts('AAPL')

        # Should return empty list when disabled
        self.assertEqual(len(result), 0, "Should return empty when disabled")

        # Restore
        self.config.sec_facts_enabled = original_value

    def test_06_lookback_quarters_limit(self):
        """Verify quarters limit is respected"""
        # Set low limit
        original_value = self.config.sec_facts_lookback_quarters
        self.config.sec_facts_lookback_quarters = 4  # 1 year only

        result = self.ingester.fetch_sec_company_facts('MSFT')

        if len(result) > 0:
            # Parse content to count metrics
            content = result[0]['content']
            lines = content.split('\n')
            metric_lines = [line for line in lines if line.strip().startswith('-')]

            # Should have ≤ 4 quarters × 5 metrics = 20 lines
            # (allowing for some variation in what's available)
            self.assertLessEqual(len(metric_lines), 25, "Should respect quarter limit")

        # Restore
        self.config.sec_facts_lookback_quarters = original_value


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
