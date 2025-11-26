# Location: /tests/test_option5_calendar.py
# Purpose: Integration tests for Phase 2.7B Option 5 - Signal Store Calendar Event Query
# Why: Validates calendar query routing, extraction, formatting, and end-to-end workflow
# Relevant Files: ice_simplified.py, query_router.py, signal_store.py

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from updated_architectures.implementation.query_router import QueryRouter, QueryType
from updated_architectures.implementation.config import ICEConfig


class TestOption5Calendar(unittest.TestCase):
    """Integration test suite for Phase 2.7B Option 5 - Calendar Event Queries"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = ICEConfig()
        # Create mock signal_store for QueryRouter
        cls.mock_signal_store = Mock()
        cls.query_router = QueryRouter(signal_store=cls.mock_signal_store)

    # =========================================================================
    # Test Group 1: Query Routing
    # =========================================================================

    def test_01_route_earnings_query(self):
        """Test 1: Verify earnings calendar queries route to STRUCTURED_CALENDAR"""
        test_queries = [
            "When is NVDA's next earnings?",
            "What is the earnings date for AAPL?",
            "Show me upcoming earnings for TSLA",
            "MSFT earnings schedule"
        ]

        for query in test_queries:
            query_type, confidence = self.query_router.route_query(query)
            self.assertEqual(
                query_type, QueryType.STRUCTURED_CALENDAR,
                f"Query '{query}' should route to STRUCTURED_CALENDAR, got {query_type}"
            )
            self.assertGreaterEqual(confidence, 0.85, f"Confidence should be >=0.85 for '{query}'")

    def test_02_route_dividend_query(self):
        """Test 2: Verify dividend calendar queries route correctly"""
        test_queries = [
            "When is JNJ's next dividend?",
            "Show AAPL dividend calendar",
            "What's the ex-dividend date for KO?"
        ]

        for query in test_queries:
            query_type, confidence = self.query_router.route_query(query)
            self.assertEqual(
                query_type, QueryType.STRUCTURED_CALENDAR,
                f"Query '{query}' should route to STRUCTURED_CALENDAR"
            )

    # =========================================================================
    # Test Group 2: Event Info Extraction
    # =========================================================================

    def test_03_extract_earnings_future(self):
        """Test 3: Extract 'next earnings' query correctly"""
        event_type, is_future = self.query_router.extract_event_info(
            "When is NVDA's next earnings?"
        )
        self.assertEqual(event_type, 'earnings')
        self.assertEqual(is_future, True)

    def test_04_extract_earnings_past(self):
        """Test 4: Extract 'last earnings' query correctly"""
        event_type, is_future = self.query_router.extract_event_info(
            "When was NVDA's last earnings call?"
        )
        self.assertEqual(event_type, 'earnings')
        self.assertEqual(is_future, False)

    def test_05_extract_dividend(self):
        """Test 5: Extract dividend event type"""
        event_type, is_future = self.query_router.extract_event_info(
            "Show upcoming dividend dates for KO"
        )
        self.assertEqual(event_type, 'dividend')
        self.assertEqual(is_future, True)

    def test_06_extract_ex_dividend(self):
        """Test 6: Extract ex-dividend event type"""
        event_type, is_future = self.query_router.extract_event_info(
            "What's the next ex-dividend date for JNJ?"
        )
        self.assertEqual(event_type, 'ex-dividend')
        self.assertEqual(is_future, True)

    def test_07_extract_generic_event(self):
        """Test 7: Extract generic event query (no specific type)"""
        event_type, is_future = self.query_router.extract_event_info(
            "What events are coming for MSFT?"
        )
        self.assertIsNone(event_type)
        self.assertEqual(is_future, True)

    def test_08_extract_neutral_query(self):
        """Test 8: Extract query without temporal direction"""
        event_type, is_future = self.query_router.extract_event_info(
            "Show AAPL earnings calendar"
        )
        self.assertEqual(event_type, 'earnings')
        self.assertIsNone(is_future)

    # =========================================================================
    # Test Group 3: Calendar Result Formatting
    # =========================================================================

    def test_09_format_with_next_event(self):
        """Test 9: Format result with next upcoming event"""
        calendar_data = {
            'ticker': 'NVDA',
            'events': [
                {'event_date': '2025-02-21', 'event_type': 'earnings', 'event_value': ''},
                {'event_date': '2025-05-21', 'event_type': 'earnings', 'event_value': ''}
            ],
            'count': 2,
            'next_event': {'event_date': '2025-02-21', 'event_type': 'earnings'}
        }

        result = self.query_router.format_calendar_result(calendar_data, "When is NVDA's next earnings?")

        self.assertIn('**Next Event for NVDA**', result)
        self.assertIn('earnings', result)
        self.assertIn('2025-02-21', result)
        self.assertIn('**Calendar (2 events)**', result)

    def test_10_format_empty_calendar(self):
        """Test 10: Format result when no events found"""
        calendar_data = {
            'ticker': 'XYZ',
            'events': [],
            'count': 0,
            'next_event': None
        }

        result = self.query_router.format_calendar_result(calendar_data, "Show XYZ calendar")

        self.assertIn('No calendar events found for XYZ', result)
        self.assertIn('Run data ingestion', result)

    def test_11_format_with_event_value(self):
        """Test 11: Format events that have values (e.g., dividend amount)"""
        calendar_data = {
            'ticker': 'KO',
            'events': [
                {'event_date': '2025-03-15', 'event_type': 'dividend', 'event_value': '$0.485'}
            ],
            'count': 1,
            'next_event': {'event_date': '2025-03-15', 'event_type': 'dividend', 'event_value': '$0.485'}
        }

        result = self.query_router.format_calendar_result(calendar_data, "KO dividend")

        self.assertIn('$0.485', result)

    def test_12_format_truncates_long_list(self):
        """Test 12: Format truncates events list to max 5"""
        calendar_data = {
            'ticker': 'AAPL',
            'events': [
                {'event_date': f'2025-0{i}-01', 'event_type': 'earnings', 'event_value': ''}
                for i in range(1, 9)  # 8 events
            ],
            'count': 8,
            'next_event': None
        }

        result = self.query_router.format_calendar_result(calendar_data, "AAPL calendar")

        self.assertIn('... and 3 more events', result)

    # =========================================================================
    # Test Group 4: ICESimplified Integration (Mocked)
    # =========================================================================

    def test_13_query_calendar_events_method_exists(self):
        """Test 13: Verify query_calendar_events method exists in ICESimplified"""
        from updated_architectures.implementation.ice_simplified import ICESimplified

        # Just verify the method signature exists
        self.assertTrue(hasattr(ICESimplified, 'query_calendar_events'))

        # Check method is callable
        method = getattr(ICESimplified, 'query_calendar_events')
        self.assertTrue(callable(method))

    def test_14_structured_calendar_handler_exists(self):
        """Test 14: Verify STRUCTURED_CALENDAR handler exists in query_with_router"""
        from updated_architectures.implementation.ice_simplified import ICESimplified
        import inspect

        # Get the source code of query_with_router
        source = inspect.getsource(ICESimplified.query_with_router)

        # Verify STRUCTURED_CALENDAR handler is present
        self.assertIn('STRUCTURED_CALENDAR', source)
        self.assertIn('extract_event_info', source)
        self.assertIn('query_calendar_events', source)
        self.assertIn('format_calendar_result', source)

    # =========================================================================
    # Test Group 5: Edge Cases
    # =========================================================================

    def test_15_case_insensitive_extraction(self):
        """Test 15: Event extraction is case insensitive"""
        queries = [
            ("WHEN IS NVDA'S NEXT EARNINGS?", 'earnings', True),
            ("when is nvda's next earnings?", 'earnings', True),
            ("When Is NVDA's Next Earnings?", 'earnings', True)
        ]

        for query, expected_type, expected_future in queries:
            event_type, is_future = self.query_router.extract_event_info(query)
            self.assertEqual(event_type, expected_type, f"Failed for: {query}")
            self.assertEqual(is_future, expected_future, f"Failed for: {query}")

    def test_16_extract_multiple_temporal_keywords(self):
        """Test 16: First matching temporal keyword wins"""
        # 'next' should take precedence
        event_type, is_future = self.query_router.extract_event_info(
            "What's next after the last earnings call?"
        )
        # 'next' appears first in the future_keywords list
        self.assertEqual(is_future, True)


class TestQueryRouterCalendarPatterns(unittest.TestCase):
    """Test the CALENDAR_EVENT_PATTERNS regex matching"""

    @classmethod
    def setUpClass(cls):
        cls.mock_signal_store = Mock()
        cls.query_router = QueryRouter(signal_store=cls.mock_signal_store)

    def test_calendar_pattern_variations(self):
        """Test various calendar query patterns route correctly"""
        patterns_to_test = [
            "when is the next earnings for NVDA",
            "what's AAPL's earnings date",
            "TSLA earnings schedule",
            "upcoming earnings for GOOGL",
            "earnings calendar for MSFT",
            "next dividend date for JNJ",
            "when is the ex-dividend for KO"
        ]

        for pattern in patterns_to_test:
            query_type, _ = self.query_router.route_query(pattern)
            self.assertEqual(
                query_type, QueryType.STRUCTURED_CALENDAR,
                f"Pattern '{pattern}' should route to STRUCTURED_CALENDAR"
            )


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
