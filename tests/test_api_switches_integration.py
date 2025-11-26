# Location: /tests/test_api_switches_integration.py
# Purpose: Integration test for granular API switches (configuration flow validation)
# Why: Validates end-to-end configuration behavior at DataIngester layer
# Relevant Files: ice_building_workflow.ipynb, ice_simplified.py, data_ingestion.py

import unittest
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'updated_architectures' / 'implementation'))

from data_ingestion import DataIngester

# Suppress logs during testing
logging.disable(logging.CRITICAL)


class TestAPISwitchesIntegration(unittest.TestCase):
    """Integration test for granular API source switches at DataIngester layer"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock API keys for all 8 services (simulating env vars from notebook)
        self.api_keys = {
            'newsapi': 'test_newsapi_key',
            'benzinga': 'test_benzinga_key',
            'finnhub': 'test_finnhub_key',
            'marketaux': 'test_marketaux_key',
            'fmp': 'test_fmp_key',
            'alpha_vantage': 'test_av_key',
            'polygon': 'test_polygon_key',
        }

        # Create DataIngester (this is what ice_simplified.py uses)
        self.ingester = DataIngester(api_keys=self.api_keys)

    def test_config_bundle_from_notebook_cell14(self):
        """Test configuration bundle from notebook Cell 14 applies correctly"""
        # Simulate configuration bundle from Cell 14 (exact format from notebook)
        api_source_config = {
            'api_source_enabled': True,
            'newsapi_enabled': True,
            'benzinga_enabled': False,
            'finnhub_enabled': True,
            'marketaux_enabled': False,
            'fmp_enabled': True,
            'alpha_vantage_enabled': False,
            'polygon_enabled': True,
            'sec_edgar_enabled': True
        }

        # Apply configuration (simulates ice_simplified.py passing config to DataIngester)
        self.ingester.set_api_source_config(api_source_config)

        # Verify configuration applied correctly
        self.assertEqual(self.ingester.api_config['api_source_enabled'], True)
        self.assertEqual(self.ingester.api_config['newsapi_enabled'], True)
        self.assertEqual(self.ingester.api_config['benzinga_enabled'], False)
        self.assertEqual(self.ingester.api_config['fmp_enabled'], True)
        self.assertEqual(self.ingester.api_config['alpha_vantage_enabled'], False)

    def test_master_switch_disables_all_apis(self):
        """Test master switch OFF disables all APIs end-to-end"""
        # Master switch OFF (simulates user setting api_source_enabled = False in notebook)
        api_source_config = {
            'api_source_enabled': False,
            'newsapi_enabled': True,  # Individual switches don't matter
            'benzinga_enabled': True,
            'fmp_enabled': True,
            'polygon_enabled': True
        }

        self.ingester.set_api_source_config(api_source_config)

        # All APIs should be disabled (validates 3-layer precedence Layer 0)
        self.assertFalse(self.ingester.is_service_available('newsapi'))
        self.assertFalse(self.ingester.is_service_available('benzinga'))
        self.assertFalse(self.ingester.is_service_available('fmp'))
        self.assertFalse(self.ingester.is_service_available('polygon'))

    def test_selective_api_enabling(self):
        """Test selective enabling of specific APIs (realistic user scenario)"""
        # User wants only NewsAPI and FMP enabled (e.g., news + financials only)
        api_source_config = {
            'api_source_enabled': True,
            'newsapi_enabled': True,
            'benzinga_enabled': False,
            'finnhub_enabled': False,
            'marketaux_enabled': False,
            'fmp_enabled': True,
            'alpha_vantage_enabled': False,
            'polygon_enabled': False,
            'sec_edgar_enabled': False
        }

        self.ingester.set_api_source_config(api_source_config)

        # Only NewsAPI and FMP should be available
        self.assertTrue(self.ingester.is_service_available('newsapi'))
        self.assertTrue(self.ingester.is_service_available('fmp'))

        # Others should be disabled
        self.assertFalse(self.ingester.is_service_available('benzinga'))
        self.assertFalse(self.ingester.is_service_available('polygon'))

    def test_fetch_methods_respect_configuration(self):
        """Test fetch methods respect granular configuration (validates early exit)"""
        # Disable all news APIs but enable financial/market APIs
        api_source_config = {
            'api_source_enabled': True,
            'newsapi_enabled': False,
            'benzinga_enabled': False,
            'finnhub_enabled': False,
            'marketaux_enabled': False,
            'fmp_enabled': True,
            'alpha_vantage_enabled': True,
            'polygon_enabled': True,
            'sec_edgar_enabled': True
        }

        self.ingester.set_api_source_config(api_source_config)

        # fetch_company_news should return empty (all news APIs disabled)
        news_result = self.ingester.fetch_company_news('AAPL', limit=5)
        self.assertEqual(news_result, [])

        # fetch_financial_fundamentals should return list (FMP/AV enabled)
        financial_result = self.ingester.fetch_financial_fundamentals('AAPL', limit=2)
        self.assertIsInstance(financial_result, list)

    def test_cache_performance_with_multiple_tickers(self):
        """Test caching prevents redundant checks (50 tickers × 4 APIs = 200+ calls)"""
        api_source_config = {
            'api_source_enabled': True,
            'newsapi_enabled': True,
            'fmp_enabled': True
        }

        self.ingester.set_api_source_config(api_source_config)

        # Simulate processing multiple tickers (realistic waterfall scenario)
        tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'META']

        for ticker in tickers:
            # Each call should hit cache after first check (performance optimization)
            self.assertTrue(self.ingester.is_service_available('newsapi'))
            self.assertTrue(self.ingester.is_service_available('fmp'))

        # Cache should have entries for checked services
        self.assertGreater(len(self.ingester._api_availability_cache), 0)

    def test_config_update_invalidates_cache(self):
        """Test configuration update clears cache (ensures consistency)"""
        # Initial config
        api_source_config = {
            'api_source_enabled': True,
            'newsapi_enabled': True
        }

        self.ingester.set_api_source_config(api_source_config)

        # Check availability (populates cache)
        self.assertTrue(self.ingester.is_service_available('newsapi'))
        initial_cache_size = len(self.ingester._api_availability_cache)
        self.assertGreater(initial_cache_size, 0)

        # Update config (user changes notebook Cell 14 and re-runs)
        new_config = {
            'api_source_enabled': True,
            'newsapi_enabled': False
        }

        self.ingester.set_api_source_config(new_config)

        # Cache should be cleared (cache invalidation)
        self.assertEqual(len(self.ingester._api_availability_cache), 0)

        # New check should return False (newsapi disabled)
        self.assertFalse(self.ingester.is_service_available('newsapi'))


def run_integration_tests():
    """Run all integration tests with detailed output"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAPISwitchesIntegration)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print(f"Integration Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
