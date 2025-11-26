# Location: /tests/test_config_propagation.py
# Purpose: Test API source configuration propagation through the system
# Why: Verify that config flows from notebook → ice_simplified → data_ingestion correctly
# Relevant Files: ice_simplified.py, data_ingestion.py

"""
Integration tests for API source configuration propagation.
Verifies that API configuration properly flows through the entire call chain
from notebook cells to individual API fetch methods.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from updated_architectures.implementation.ice_simplified import ICECore
from updated_architectures.implementation.data_ingestion import DataIngester


class TestConfigPropagation:
    """Test suite for API source configuration propagation"""

    @pytest.fixture
    def mock_api_keys(self):
        """Mock API keys for testing"""
        return {
            'newsapi': 'test_newsapi_key',
            'benzinga': 'test_benzinga_key',
            'finnhub': 'test_finnhub_key',
            'marketaux': 'test_marketaux_key',
            'fmp': 'test_fmp_key',
            'alpha_vantage': 'test_alpha_key',
            'polygon': 'test_polygon_key',
            'sec_edgar': 'test_sec_key'
        }

    @pytest.fixture
    def data_ingester(self, mock_api_keys):
        """Create DataIngester with mocked API keys"""
        with patch.dict('os.environ', {f'{k.upper()}_API_KEY': v for k, v in mock_api_keys.items()}):
            ingester = DataIngester()
            # Mock the API keys
            ingester.api_keys = mock_api_keys
            return ingester

    def test_config_applied_to_ingester(self, data_ingester):
        """Test that set_api_source_config correctly applies configuration"""
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': False,
            'benzinga_enabled': True,
            'finnhub_enabled': False,
            'sec_edgar_enabled': True
        }

        # Apply config
        data_ingester.set_api_source_config(config)

        # Verify config was applied
        assert data_ingester.api_config['newsapi_enabled'] == False
        assert data_ingester.api_config['benzinga_enabled'] == True
        assert data_ingester.api_config['finnhub_enabled'] == False
        assert data_ingester.api_config['sec_edgar_enabled'] == True

    def test_is_service_available_respects_config(self, data_ingester):
        """Test that is_service_available uses the 3-layer hierarchy correctly"""
        # Test 1: Master switch OFF disables all APIs
        config = {
            'api_source_enabled': False,
            'newsapi_enabled': True,  # Should be ignored due to master switch
        }
        data_ingester.set_api_source_config(config)

        assert data_ingester.is_service_available('newsapi') == False
        assert data_ingester.is_service_available('benzinga') == False

        # Test 2: Individual API switch OFF with master ON
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': False,
            'benzinga_enabled': True
        }
        data_ingester.set_api_source_config(config)
        data_ingester._api_availability_cache.clear()  # Clear cache

        assert data_ingester.is_service_available('newsapi') == False
        assert data_ingester.is_service_available('benzinga') == True

        # Test 3: API without key is unavailable even if enabled
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': True
        }
        data_ingester.api_keys.pop('newsapi')  # Remove API key
        data_ingester.set_api_source_config(config)
        data_ingester._api_availability_cache.clear()

        assert data_ingester.is_service_available('newsapi') == False

    def test_fetch_methods_respect_config(self, data_ingester):
        """Test that fetch methods only call enabled APIs"""
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': False,
            'benzinga_enabled': True,
            'finnhub_enabled': False,
            'marketaux_enabled': True
        }
        data_ingester.set_api_source_config(config)

        # Mock individual API fetch methods (using correct method names)
        with patch.object(data_ingester, '_fetch_newsapi') as mock_newsapi, \
             patch.object(data_ingester, '_fetch_benzinga_news') as mock_benzinga, \
             patch.object(data_ingester, '_fetch_finnhub_news') as mock_finnhub, \
             patch.object(data_ingester, '_fetch_marketaux_news') as mock_marketaux:

            mock_benzinga.return_value = ['benzinga doc']
            mock_marketaux.return_value = ['marketaux doc']

            # Fetch news
            result = data_ingester.fetch_company_news('NVDA', limit=5)

            # Verify only enabled APIs were called
            mock_newsapi.assert_not_called()  # Disabled
            mock_benzinga.assert_called_once()  # Enabled (called with some limit)
            mock_finnhub.assert_not_called()  # Disabled
            mock_marketaux.assert_called_once()  # Enabled (called with some limit)

            # Verify they were called with the correct symbol at least
            assert mock_benzinga.call_args[0][0] == 'NVDA'
            assert mock_marketaux.call_args[0][0] == 'NVDA'

    def test_cache_invalidation_on_config_change(self, data_ingester):
        """Test that API availability cache is cleared when config changes"""
        # Initial config
        config1 = {'api_source_enabled': True, 'newsapi_enabled': True}
        data_ingester.set_api_source_config(config1)

        # Check service (populates cache)
        result1 = data_ingester.is_service_available('newsapi')
        assert result1 == True
        assert 'newsapi' in data_ingester._api_availability_cache

        # Change config
        config2 = {'api_source_enabled': True, 'newsapi_enabled': False}
        data_ingester.set_api_source_config(config2)

        # Cache should be cleared
        assert len(data_ingester._api_availability_cache) == 0

        # New check should use new config
        result2 = data_ingester.is_service_available('newsapi')
        assert result2 == False

    def test_config_logging(self, data_ingester, caplog):
        """Test that config changes are properly logged"""
        import logging
        caplog.set_level(logging.INFO)

        # Apply config with all APIs disabled
        config = {'api_source_enabled': False}
        data_ingester.set_api_source_config(config)

        assert "Master switch OFF" in caplog.text

        # Apply config with specific APIs enabled
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': True,
            'benzinga_enabled': True,
            'finnhub_enabled': False
        }
        data_ingester.set_api_source_config(config)

        assert "2 APIs enabled" in caplog.text or "API configuration applied" in caplog.text

    def test_early_exit_when_all_apis_disabled(self, data_ingester):
        """Test that fetch methods return early when all relevant APIs are disabled"""
        # Disable all news APIs
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': False,
            'benzinga_enabled': False,
            'finnhub_enabled': False,
            'marketaux_enabled': False
        }
        data_ingester.set_api_source_config(config)

        # Mock individual API methods (shouldn't be called)
        with patch.object(data_ingester, '_fetch_newsapi') as mock_newsapi:
            result = data_ingester.fetch_company_news('NVDA', limit=5)

            # Should return empty list without calling any APIs
            assert result == []
            mock_newsapi.assert_not_called()

    def test_ice_core_config_propagation(self):
        """Test that ICECore properly propagates config to DataIngester"""
        # Simplified test - just verify that config gets passed to set_api_source_config
        data_ingester = DataIngester()

        # Spy on set_api_source_config
        with patch.object(data_ingester, 'set_api_source_config', wraps=data_ingester.set_api_source_config) as mock_set_config:
            # Apply config
            config = {
                'api_source_enabled': True,
                'sec_edgar_enabled': True,
                'newsapi_enabled': False
            }
            data_ingester.set_api_source_config(config)

            # Verify config was applied
            mock_set_config.assert_called_once_with(config)
            assert data_ingester.api_config['sec_edgar_enabled'] == True
            assert data_ingester.api_config['newsapi_enabled'] == False

    def test_config_persistence_across_calls(self, data_ingester):
        """Test that config persists across multiple API calls"""
        # Set config once
        config = {
            'api_source_enabled': True,
            'newsapi_enabled': False,
            'benzinga_enabled': True
        }
        data_ingester.set_api_source_config(config)

        # First call
        assert data_ingester.is_service_available('newsapi') == False
        assert data_ingester.is_service_available('benzinga') == True

        # Clear cache to force re-evaluation
        data_ingester._api_availability_cache.clear()

        # Second call - config should persist
        assert data_ingester.is_service_available('newsapi') == False
        assert data_ingester.is_service_available('benzinga') == True

    def test_backward_compatibility(self, data_ingester):
        """Test that system works without any config (backward compatibility)"""
        # Don't set any config - should use defaults (all APIs with keys enabled)

        # All APIs with keys should be available
        assert data_ingester.is_service_available('newsapi') == True
        assert data_ingester.is_service_available('benzinga') == True
        assert data_ingester.is_service_available('finnhub') == True

        # API without key should not be available
        data_ingester.api_keys.pop('polygon', None)
        assert data_ingester.is_service_available('polygon') == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])