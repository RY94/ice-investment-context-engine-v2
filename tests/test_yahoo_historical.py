# Location: /tests/test_yahoo_historical.py
# Purpose: Test Yahoo Finance historical data fetching with configurable lookback
# Why: Verify temporal enhancement for Yahoo Finance works correctly
# Relevant Files: data_ingestion.py, signal_store.py, config.py

"""
Test Yahoo Finance Historical Data Enhancement

Validates:
1. Configurable lookback period (financial_lookback_days)
2. Proper event_date tagging for each day
3. SignalStore integration with price_history table
4. Graceful degradation on errors
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd  # Add pandas import for DataFrame creation

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "updated_architectures" / "implementation"))

from updated_architectures.implementation.data_ingestion import DataIngester
from updated_architectures.implementation.config import ICEConfig


class TestYahooHistoricalData:
    """Test suite for Yahoo Finance historical data enhancement"""

    def test_yahoo_fetches_configured_lookback_period(self):
        """Verify Yahoo Finance respects financial_lookback_days config"""
        # Setup config with specific lookback
        config = ICEConfig()
        config.financial_lookback_days = 30  # 30 days for testing

        # Create ingester with config
        ingester = DataIngester(config=config)

        # Mock yfinance to avoid real API calls
        with patch('yfinance.Ticker') as mock_ticker_class:
            # Create mock ticker instance
            mock_ticker = MagicMock()
            mock_ticker_class.return_value = mock_ticker

            # Mock info data
            mock_ticker.info = {
                'longName': 'Apple Inc.',
                'currentPrice': 150.0,
                'previousClose': 148.0,
                'marketCap': 2500000000000
            }

            # Create mock historical data (simulate 20 trading days)
            import pandas as pd
            dates = pd.date_range(end=datetime.now(), periods=20, freq='B')  # Business days
            mock_history = pd.DataFrame({
                'Open': [145.0 + i * 0.5 for i in range(20)],
                'High': [146.0 + i * 0.5 for i in range(20)],
                'Low': [144.0 + i * 0.5 for i in range(20)],
                'Close': [145.5 + i * 0.5 for i in range(20)],
                'Volume': [100000000 + i * 1000000 for i in range(20)]
            }, index=dates)

            # Configure mock to return history when called with date range
            mock_ticker.history.return_value = mock_history

            # Fetch Yahoo market data
            documents = ingester._fetch_yahoo_market_data('AAPL')

            # Verify history was called with correct date range
            mock_ticker.history.assert_called()
            call_args = mock_ticker.history.call_args

            # Check that start date is approximately 30 days ago
            if call_args[1]:  # kwargs were used
                start_date = call_args[1].get('start')
                end_date = call_args[1].get('end')
                if start_date and end_date:
                    delta = (end_date - start_date).days
                    assert 29 <= delta <= 31, f"Expected ~30 day lookback, got {delta} days"

            # Verify we have historical documents
            historical_docs = [d for d in documents if 'Historical Market Data' in d]
            assert len(historical_docs) == 20, f"Expected 20 daily documents, got {len(historical_docs)}"

            # Verify summary document exists
            summary_docs = [d for d in documents if '30-Day Price Summary' in d]
            assert len(summary_docs) >= 1, "Expected at least one summary document"

    def test_event_date_tagging(self):
        """Verify each historical day has proper [EVENT_DATE:YYYY-MM-DD] tag"""
        config = ICEConfig()
        config.financial_lookback_days = 7  # Small lookback for testing

        ingester = DataIngester(config=config)

        with patch('yfinance.Ticker') as mock_ticker_class:
            mock_ticker = MagicMock()
            mock_ticker_class.return_value = mock_ticker
            mock_ticker.info = {'longName': 'Test Corp'}

            # Create 5 days of mock data
            import pandas as pd
            dates = pd.date_range(end=datetime.now(), periods=5, freq='B')
            mock_history = pd.DataFrame({
                'Open': [100.0] * 5,
                'High': [101.0] * 5,
                'Low': [99.0] * 5,
                'Close': [100.5] * 5,
                'Volume': [1000000] * 5
            }, index=dates)
            mock_ticker.history.return_value = mock_history

            documents = ingester._fetch_yahoo_market_data('TEST')

            # Check each daily document for event_date tag
            historical_docs = [d for d in documents if 'Historical Market Data' in d]
            for i, doc in enumerate(historical_docs):
                # Each document should have [EVENT_DATE:YYYY-MM-DD] tag
                assert '[EVENT_DATE:' in doc, f"Document {i} missing EVENT_DATE tag"

                # Extract and validate date format
                import re
                date_match = re.search(r'\[EVENT_DATE:(\d{4}-\d{2}-\d{2})\]', doc)
                assert date_match, f"Document {i} has invalid EVENT_DATE format"

                # Verify it's a valid date
                date_str = date_match.group(1)
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    pytest.fail(f"Invalid date format in EVENT_DATE: {date_str}")

    def test_graceful_degradation_on_error(self):
        """Verify Yahoo Finance continues with other categories if historical fetch fails"""
        config = ICEConfig()
        ingester = DataIngester(config=config)

        with patch('yfinance.Ticker') as mock_ticker_class:
            mock_ticker = MagicMock()
            mock_ticker_class.return_value = mock_ticker

            # Mock info for other categories
            mock_ticker.info = {
                'longName': 'Error Test Corp',
                'currentPrice': 100.0
            }

            # Make history() raise an exception
            mock_ticker.history.side_effect = Exception("Network error")

            # Other categories should still work
            mock_ticker.analyst_recommendations = pd.DataFrame({
                'period': ['0m'],
                'strongBuy': [5],
                'buy': [10],
                'hold': [8],
                'sell': [2],
                'strongSell': [1]
            })

            # Fetch should not crash
            documents = ingester._fetch_yahoo_market_data('ERROR')

            # Should have some documents from other categories
            assert len(documents) > 0, "Should have documents from other categories"

            # But no historical documents
            historical_docs = [d for d in documents if 'Historical Market Data' in d]
            assert len(historical_docs) == 0, "Should have no historical documents after error"

    def test_signal_store_integration(self):
        """Verify historical data is properly stored in SignalStore"""
        config = ICEConfig()
        config.use_signal_store = True
        config.financial_lookback_days = 5

        # Create mock signal store
        mock_signal_store = MagicMock()

        ingester = DataIngester(config=config)
        ingester.signal_store = mock_signal_store

        with patch('yfinance.Ticker') as mock_ticker_class:
            mock_ticker = MagicMock()
            mock_ticker_class.return_value = mock_ticker
            mock_ticker.info = {'longName': 'Store Test Corp'}

            # Create 3 days of mock data
            import pandas as pd
            dates = pd.date_range(end=datetime.now(), periods=3, freq='B')
            mock_history = pd.DataFrame({
                'Open': [100.0, 101.0, 102.0],
                'High': [101.0, 102.0, 103.0],
                'Low': [99.0, 100.0, 101.0],
                'Close': [100.5, 101.5, 102.5],
                'Volume': [1000000, 1100000, 1200000]
            }, index=dates)
            mock_ticker.history.return_value = mock_history

            # Fetch data
            documents = ingester._fetch_yahoo_market_data('STORE')

            # Verify insert_price_history_batch was called
            mock_signal_store.insert_price_history_batch.assert_called_once()

            # Check the data passed to signal store
            call_args = mock_signal_store.insert_price_history_batch.call_args[0][0]
            assert len(call_args) == 3, f"Expected 3 price records, got {len(call_args)}"

            # Verify each record has required fields
            for record in call_args:
                assert 'ticker' in record
                assert 'date' in record
                assert 'open_price' in record
                assert 'close_price' in record
                assert 'volume' in record
                assert record['ticker'] == 'STORE'

    def test_lookback_default_without_config(self):
        """Verify default 90-day lookback when no config provided"""
        # Create ingester without config
        ingester = DataIngester(config=None)

        with patch('yfinance.Ticker') as mock_ticker_class:
            mock_ticker = MagicMock()
            mock_ticker_class.return_value = mock_ticker
            mock_ticker.info = {'longName': 'Default Test Corp'}

            # Return empty history to avoid processing
            mock_ticker.history.return_value = pd.DataFrame()

            # Fetch data
            ingester._fetch_yahoo_market_data('DEFAULT')

            # The default should be 90 days
            # This is verified in the code: lookback_days = self.config.financial_lookback_days if self.config else 90
            # Since we're not passing config, it should use 90

            # Check the call to history()
            mock_ticker.history.assert_called()
            call_args = mock_ticker.history.call_args

            if call_args[1]:  # kwargs
                start_date = call_args[1].get('start')
                end_date = call_args[1].get('end')
                if start_date and end_date:
                    delta = (end_date - start_date).days
                    assert 85 <= delta <= 95, f"Expected ~90 day default lookback, got {delta} days"


if __name__ == "__main__":
    # Run tests
    test_suite = TestYahooHistoricalData()

    print("Running Yahoo Finance Historical Data Tests...")
    print("-" * 50)

    try:
        test_suite.test_yahoo_fetches_configured_lookback_period()
        print("✅ Test 1: Configurable lookback period - PASSED")
    except Exception as e:
        print(f"❌ Test 1: Configurable lookback period - FAILED: {e}")

    try:
        test_suite.test_event_date_tagging()
        print("✅ Test 2: Event date tagging - PASSED")
    except Exception as e:
        print(f"❌ Test 2: Event date tagging - FAILED: {e}")

    try:
        test_suite.test_graceful_degradation_on_error()
        print("✅ Test 3: Graceful degradation - PASSED")
    except Exception as e:
        print(f"❌ Test 3: Graceful degradation - FAILED: {e}")

    try:
        test_suite.test_signal_store_integration()
        print("✅ Test 4: SignalStore integration - PASSED")
    except Exception as e:
        print(f"❌ Test 4: SignalStore integration - FAILED: {e}")

    try:
        test_suite.test_lookback_default_without_config()
        print("✅ Test 5: Default lookback without config - PASSED")
    except Exception as e:
        print(f"❌ Test 5: Default lookback without config - FAILED: {e}")

    print("-" * 50)
    print("Test suite complete!")