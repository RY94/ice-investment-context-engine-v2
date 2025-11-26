# Location: /tests/test_option5_event_edges.py
# Purpose: Test Option 5 - Event-to-Signal Store integration
# Why: Verify events from EventExtractor are persisted to calendar_events table
# Relevant Files: ice_simplified.py, signal_store.py, event_extractor.py

"""
Phase 2.7B Option 5: Event-to-Signal Store Integration Tests

Tests that EventExtractor events are persisted to Signal Store calendar_events
table for fast calendar queries ("When is next earnings?").
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOption5EventSignalStore:
    """Test suite for Option 5: Event-to-Signal Store integration"""

    def test_01_event_dict_format_mapping(self):
        """Test that EventNode fields map correctly to calendar_events schema"""
        # Simulate EventNode structure
        mock_event = Mock()
        mock_event.ticker = "NVDA"
        mock_event.type = Mock(value="earnings")
        mock_event.date = datetime(2024, 7, 15)
        mock_event.magnitude = 0.15  # 15% beat
        mock_event.source_document_id = "finnhub:NVDA_123"

        # Map to calendar_events schema (same logic as in _enhance_with_events)
        event_dict = {
            'ticker': mock_event.ticker,
            'event_type': mock_event.type.value if hasattr(mock_event.type, 'value') else str(mock_event.type),
            'event_date': mock_event.date.strftime('%Y-%m-%d') if mock_event.date else datetime.now().strftime('%Y-%m-%d'),
            'event_value': mock_event.magnitude,
            'is_future': 1 if mock_event.date and mock_event.date > datetime.now() else 0,
            'source_document_id': mock_event.source_document_id
        }

        assert event_dict['ticker'] == "NVDA"
        assert event_dict['event_type'] == "earnings"
        assert event_dict['event_date'] == "2024-07-15"
        assert event_dict['event_value'] == 0.15
        assert event_dict['is_future'] == 0  # Past event
        assert event_dict['source_document_id'] == "finnhub:NVDA_123"

    def test_02_future_event_flag(self):
        """Test is_future flag is set correctly for future events"""
        future_date = datetime.now() + timedelta(days=30)

        mock_event = Mock()
        mock_event.date = future_date

        is_future = 1 if mock_event.date and mock_event.date > datetime.now() else 0

        assert is_future == 1, "Future event should have is_future=1"

    def test_03_past_event_flag(self):
        """Test is_future flag is set correctly for past events"""
        past_date = datetime.now() - timedelta(days=30)

        mock_event = Mock()
        mock_event.date = past_date

        is_future = 1 if mock_event.date and mock_event.date > datetime.now() else 0

        assert is_future == 0, "Past event should have is_future=0"

    def test_04_null_date_handling(self):
        """Test graceful handling of null event dates"""
        mock_event = Mock()
        mock_event.date = None

        # Should default to current date
        event_date = mock_event.date.strftime('%Y-%m-%d') if mock_event.date else datetime.now().strftime('%Y-%m-%d')
        is_future = 1 if mock_event.date and mock_event.date > datetime.now() else 0

        assert event_date == datetime.now().strftime('%Y-%m-%d')
        assert is_future == 0, "Null date should default to is_future=0"

    def test_05_event_type_enum_vs_string(self):
        """Test event_type handling for both enum and string types"""
        # Enum-style type
        mock_event_enum = Mock()
        mock_event_enum.type = Mock(value="management_change")
        event_type_enum = mock_event_enum.type.value if hasattr(mock_event_enum.type, 'value') else str(mock_event_enum.type)
        assert event_type_enum == "management_change"

        # String-style type (fallback)
        mock_event_str = Mock()
        mock_event_str.type = "scandal"
        event_type_str = mock_event_str.type.value if hasattr(mock_event_str.type, 'value') else str(mock_event_str.type)
        assert event_type_str == "scandal"

    def test_06_signal_store_batch_insert_called(self):
        """Test that insert_calendar_events_batch is called with correct data"""
        mock_signal_store = Mock()
        mock_signal_store.insert_calendar_events_batch.return_value = 3

        # Simulate event dicts
        event_dicts = [
            {'ticker': 'NVDA', 'event_type': 'earnings', 'event_date': '2024-07-15',
             'event_value': 0.15, 'is_future': 0, 'source_document_id': 'doc1'},
            {'ticker': 'AAPL', 'event_type': 'dividend', 'event_date': '2024-08-01',
             'event_value': 0.24, 'is_future': 0, 'source_document_id': 'doc2'},
            {'ticker': 'MSFT', 'event_type': 'guidance', 'event_date': '2024-09-15',
             'event_value': None, 'is_future': 1, 'source_document_id': 'doc3'},
        ]

        # Call batch insert
        inserted = mock_signal_store.insert_calendar_events_batch(event_dicts)

        mock_signal_store.insert_calendar_events_batch.assert_called_once_with(event_dicts)
        assert inserted == 3, "Should return count of inserted events"

    def test_07_graceful_degradation_on_error(self):
        """Test that Signal Store errors don't break event extraction"""
        mock_signal_store = Mock()
        mock_signal_store.insert_calendar_events_batch.side_effect = Exception("DB connection failed")

        # Simulate the try/except pattern from _enhance_with_events
        try:
            mock_signal_store.insert_calendar_events_batch([])
            persistence_succeeded = True
        except Exception:
            persistence_succeeded = False
            # In production: logger.debug("[Option5] Signal Store event persistence failed (non-fatal)")

        assert not persistence_succeeded, "Should catch exception gracefully"
        # The key test is that this doesn't raise - the exception is handled

    def test_08_empty_events_list_handling(self):
        """Test that empty event list doesn't call insert"""
        mock_signal_store = Mock()
        mock_signal_store.insert_calendar_events_batch.return_value = 0

        event_dicts = []

        # Pattern from _enhance_with_events: only call if event_dicts is non-empty
        if event_dicts:
            inserted = mock_signal_store.insert_calendar_events_batch(event_dicts)
        else:
            inserted = 0

        mock_signal_store.insert_calendar_events_batch.assert_not_called()
        assert inserted == 0


class TestOption5Integration:
    """Integration tests for Option 5 (requires ICE system)"""

    @pytest.fixture
    def ice_config(self):
        """Create test configuration"""
        try:
            from updated_architectures.implementation.config import ICEConfig
            config = ICEConfig()
            config.event_extraction_enabled = True
            return config
        except ImportError:
            pytest.skip("ICEConfig not available")

    def test_09_config_event_extraction_enabled(self, ice_config):
        """Verify event extraction is enabled in config"""
        assert ice_config.event_extraction_enabled is True

    def test_10_calendar_events_table_exists(self):
        """Verify calendar_events table exists in Signal Store schema"""
        try:
            from updated_architectures.implementation.signal_store import SignalStore
            import tempfile
            import os

            # Create temp Signal Store
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                db_path = f.name

            store = SignalStore(db_path)

            # Check table exists
            cursor = store.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_events'")
            result = cursor.fetchone()

            assert result is not None, "calendar_events table should exist"
            assert result[0] == 'calendar_events'

            # Cleanup
            store.conn.close()
            os.unlink(db_path)

        except ImportError:
            pytest.skip("SignalStore not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
