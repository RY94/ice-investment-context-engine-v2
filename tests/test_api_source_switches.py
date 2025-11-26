# Location: /tests/test_api_source_switches.py
# Purpose: Unit tests for granular API source switches (Phase 1 Feature)
# Why: Validates 3-layer control hierarchy, caching, and early exit logic
# Relevant Files: data_ingestion.py, ice_simplified.py, ice_building_workflow.ipynb

import unittest
import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'updated_architectures' / 'implementation'))

from data_ingestion import DataIngester

# Suppress logs during testing
logging.disable(logging.CRITICAL)


class TestAPISourceSwitches(unittest.TestCase):
    """Test granular API source switches (8 individual controls + master switch)"""

    def setUp(self):
        """Set up test fixtures with mock API keys"""
        # Mock API keys for all 8 services
        self.api_keys = {
            'newsapi': 'test_newsapi_key',
            'benzinga': 'test_benzinga_key',
            'finnhub': 'test_finnhub_key',
            'marketaux': 'test_marketaux_key',
            'fmp': 'test_fmp_key',
            'alpha_vantage': 'test_av_key',
            'polygon': 'test_polygon_key',
            # Note: SEC EDGAR doesn't need API key
        }

        # Create ingester with mock keys
        self.ingester = DataIngester(api_keys=self.api_keys)

    def tearDown(self):
        """Clean up after each test"""
        # Clear cache
        if hasattr(self.ingester, '_api_availability_cache'):
            self.ingester._api_availability_cache.clear()


class TestConfigurationSetting(TestAPISourceSwitches):
    """Test set_api_source_config() method"""

    def test_set_config_updates_internal_state(self):
        """Config update should modify internal api_config"""
        config = {
            'api_source_enabled': False,
            'newsapi_enabled': False
        }

        self.ingester.set_api_source_config(config)

        self.assertEqual(self.ingester.api_config['api_source_enabled'], False)
        self.assertEqual(self.ingester.api_config['newsapi_enabled'], False)

    def test_set_config_clears_cache(self):
        """Config update should invalidate cache"""
        # Populate cache
        self.ingester.is_service_available('newsapi')
        self.assertIn('newsapi', self.ingester._api_availability_cache)

        # Update config
        self.ingester.set_api_source_config({'newsapi_enabled': False})

        # Cache should be cleared
        self.assertEqual(len(self.ingester._api_availability_cache), 0)

    def test_set_config_with_none_warns(self):
        """Passing None should not crash"""
        # Should not raise exception
        self.ingester.set_api_source_config(None)


class TestThreeLayerPrecedence(TestAPISourceSwitches):
    """Test 3-layer control hierarchy: Master → Individual → API Key"""

    def test_layer0_master_switch_off_disables_all(self):
        """Layer 0: Master switch OFF → all APIs disabled"""
        config = {'api_source_enabled': False}
        self.ingester.set_api_source_config(config)

        # All APIs should be disabled regardless of keys
        self.assertFalse(self.ingester.is_service_available('newsapi'))
        self.assertFalse(self.ingester.is_service_available('benzinga'))
        self.assertFalse(self.ingester.is_service_available('fmp'))
        self.assertFalse(self.ingester.is_service_available('polygon'))

    def test_layer1_individual_switch_off(self):
        """Layer 1: Individual switch OFF → specific API disabled"""
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': False,  # Only NewsAPI disabled
            'benzinga_enabled': True
        }
        self.ingester.set_api_source_config(config)

        # NewsAPI should be disabled
        self.assertFalse(self.ingester.is_service_available('newsapi'))

        # Benzinga should still be available (has key and enabled)
        self.assertTrue(self.ingester.is_service_available('benzinga'))

    def test_layer2_no_api_key_disables_service(self):
        """Layer 2: No API key → service disabled even if switches enabled"""
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': True
        }

        # Create ingester WITHOUT newsapi key
        ingester_no_key = DataIngester(api_keys={'fmp': 'test_key'})
        ingester_no_key.set_api_source_config(config)

        # NewsAPI should be disabled (no key)
        self.assertFalse(ingester_no_key.is_service_available('newsapi'))

    def test_all_layers_enabled(self):
        """All layers enabled → service available"""
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': True
        }
        self.ingester.set_api_source_config(config)

        # NewsAPI should be available (master ON, individual ON, key exists)
        self.assertTrue(self.ingester.is_service_available('newsapi'))


class TestCaching(TestAPISourceSwitches):
    """Test API availability caching for performance"""

    def test_cache_is_used_for_repeated_calls(self):
        """Repeated calls should use cache"""
        # First call - populates cache
        result1 = self.ingester.is_service_available('newsapi')

        # Cache should be populated
        self.assertIn('newsapi', self.ingester._api_availability_cache)

        # Second call - should use cache (same result)
        result2 = self.ingester.is_service_available('newsapi')

        self.assertEqual(result1, result2)

    def test_cache_cleared_on_config_change(self):
        """Cache should clear when configuration changes"""
        # Populate cache
        self.ingester.is_service_available('newsapi')
        initial_cache_size = len(self.ingester._api_availability_cache)
        self.assertGreater(initial_cache_size, 0)

        # Change config
        self.ingester.set_api_source_config({'newsapi_enabled': False})

        # Cache should be cleared
        self.assertEqual(len(self.ingester._api_availability_cache), 0)


class TestEarlyExit(TestAPISourceSwitches):
    """Test early exit logic in fetch methods"""

    def test_fetch_news_early_exit_all_disabled(self):
        """fetch_company_news should exit early if all news APIs disabled"""
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': False,
            'benzinga_enabled': False,
            'finnhub_enabled': False,
            'marketaux_enabled': False
        }
        self.ingester.set_api_source_config(config)

        # Should return empty list without attempting API calls
        result = self.ingester.fetch_company_news('AAPL', limit=5)

        self.assertEqual(result, [])

    def test_fetch_financial_early_exit_all_disabled(self):
        """fetch_financial_fundamentals should exit early if all financial APIs disabled"""
        config = {
            'api_source_enabled': True,
            'fmp_enabled': False,
            'alpha_vantage_enabled': False
        }
        self.ingester.set_api_source_config(config)

        # Should return empty list without attempting API calls
        result = self.ingester.fetch_financial_fundamentals('AAPL', limit=2)

        self.assertEqual(result, [])

    def test_fetch_market_early_exit_polygon_disabled(self):
        """fetch_market_data should exit early if Polygon disabled"""
        config = {
            'api_source_enabled': True,
            'polygon_enabled': False
        }
        self.ingester.set_api_source_config(config)

        # Should return empty list without attempting API call
        result = self.ingester.fetch_market_data('AAPL', limit=1)

        self.assertEqual(result, [])

    def test_fetch_sec_early_exit_disabled(self):
        """fetch_sec_filings should exit early if SEC EDGAR disabled"""
        config = {
            'api_source_enabled': True,
            'sec_edgar_enabled': False
        }
        self.ingester.set_api_source_config(config)

        # Should return empty list without attempting API call
        result = self.ingester.fetch_sec_filings('AAPL', limit=2)

        self.assertEqual(result, [])


class TestBackwardCompatibility(TestAPISourceSwitches):
    """Test backward compatibility without api_source_config"""

    def test_default_behavior_all_enabled(self):
        """Without config, all APIs with keys should be enabled (backward compatible)"""
        # Fresh ingester without any config changes
        ingester = DataIngester(api_keys=self.api_keys)

        # All APIs with keys should be available
        self.assertTrue(ingester.is_service_available('newsapi'))
        self.assertTrue(ingester.is_service_available('benzinga'))
        self.assertTrue(ingester.is_service_available('fmp'))
        self.assertTrue(ingester.is_service_available('polygon'))


class TestEdgeCases(TestAPISourceSwitches):
    """Test edge cases and boundary conditions"""

    def test_limit_zero_returns_empty(self):
        """All fetch methods should return empty list when limit=0"""
        self.assertEqual(self.ingester.fetch_company_news('AAPL', limit=0), [])
        self.assertEqual(self.ingester.fetch_financial_fundamentals('AAPL', limit=0), [])
        self.assertEqual(self.ingester.fetch_market_data('AAPL', limit=0), [])
        self.assertEqual(self.ingester.fetch_sec_filings('AAPL', limit=0), [])

    def test_partial_api_availability(self):
        """Some APIs enabled, some disabled should work correctly"""
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': True,
            'benzinga_enabled': False,
            'finnhub_enabled': True,
            'marketaux_enabled': False
        }
        self.ingester.set_api_source_config(config)

        # Check availability
        self.assertTrue(self.ingester.is_service_available('newsapi'))
        self.assertFalse(self.ingester.is_service_available('benzinga'))
        self.assertTrue(self.ingester.is_service_available('finnhub'))
        self.assertFalse(self.ingester.is_service_available('marketaux'))


def run_tests():
    """Run all tests with detailed output"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConfigurationSetting))
    suite.addTests(loader.loadTestsFromTestCase(TestThreeLayerPrecedence))
    suite.addTests(loader.loadTestsFromTestCase(TestCaching))
    suite.addTests(loader.loadTestsFromTestCase(TestEarlyExit))
    suite.addTests(loader.loadTestsFromTestCase(TestBackwardCompatibility))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
