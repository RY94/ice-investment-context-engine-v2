# Location: /tests/test_temporal_features_comprehensive.py
# Purpose: Comprehensive tests for all temporal enhancements and features
# Why: Ensures temporal architecture correctly addresses all 7 query types
# Relevant Files: signal_store.py, temporal_analyzer.py, period_utils.py

"""
Comprehensive Temporal Features Test Suite

Tests all temporal enhancements including:
- Event date inference and backfill
- Calendar events queries
- YoY/QoQ comparisons
- Growth rate calculations
- Trend detection
- Period generation
- Period arithmetic utilities
"""

import unittest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from updated_architectures.implementation.signal_store import SignalStore
from src.ice_core.temporal_analyzer import TemporalAnalyzer
from src.ice_core.period_utils import (
    parse_period_string, next_period, previous_period,
    period_difference, add_periods, period_to_date_range
)


class TestTemporalFeatures(unittest.TestCase):
    """Test suite for temporal architecture enhancements."""

    def setUp(self):
        """Set up test database and sample data."""
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.store = SignalStore(db_path=self.test_db.name)
        self.analyzer = TemporalAnalyzer(self.store)
        self._insert_test_data()

    def tearDown(self):
        """Clean up test database."""
        self.store.conn.close()
        os.unlink(self.test_db.name)

    def _insert_test_data(self):
        """Insert sample data for testing."""
        cursor = self.store.conn.cursor()

        # Insert financial metrics with various periods
        test_metrics = [
            ('FICO', 'Revenue', 450000000, 'Q1 2024', '2024-04-15'),
            ('FICO', 'Revenue', 465000000, 'Q2 2024', '2024-07-15'),
            ('FICO', 'Revenue', 470000000, 'Q3 2024', '2024-10-15'),
            ('FICO', 'Revenue', 420000000, 'Q1 2023', '2023-04-15'),
            ('FICO', 'Revenue', 430000000, 'Q2 2023', '2023-07-15'),
            ('FICO', 'Net Income', 95000000, 'Q1 2024', '2024-04-15'),
            ('FICO', 'Net Income', 98000000, 'Q2 2024', '2024-07-15'),
            ('FICO', 'Net Income', 85000000, 'Q1 2023', '2023-04-15'),
        ]

        for ticker, metric, value, period, event_date in test_metrics:
            cursor.execute("""
                INSERT INTO financial_metrics
                (ticker, metric_name, metric_value, period, event_date, source, confidence)
                VALUES (?, ?, ?, ?, ?, 'Test', 0.9)
            """, (ticker, metric, value, period, event_date))

        # Insert calendar events
        test_events = [
            ('FICO', '2024-07-15', 'earnings_call', 'Q2 2024 Earnings', True),
            ('FICO', '2024-10-15', 'earnings_call', 'Q3 2024 Earnings', True),
            ('FICO', '2025-01-15', 'earnings_call', 'Q4 2024 Earnings', False),
        ]

        for ticker, date, event_type, desc, is_confirmed in test_events:
            cursor.execute("""
                INSERT INTO calendar_events
                (ticker, event_date, event_type, description, is_confirmed)
                VALUES (?, ?, ?, ?, ?)
            """, (ticker, date, event_type, desc, is_confirmed))

        # Insert ratings for recency testing
        test_ratings = [
            ('FICO', 'Buy', 'Analyst A', 'Firm A', '2024-10-01', 0.8),
            ('FICO', 'Hold', 'Analyst B', 'Firm B', '2024-09-15', 0.9),
            ('FICO', 'Buy', 'Analyst C', 'Firm C', '2024-10-10', 0.7),
        ]

        for ticker, rating, analyst, firm, date, conf in test_ratings:
            cursor.execute("""
                INSERT INTO ratings
                (ticker, rating, analyst, firm, signal_date, confidence, event_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ticker, rating, analyst, firm, date, conf, date))

        self.store.conn.commit()

    # ==================== EVENT DATE TESTS ====================

    def test_event_date_inference(self):
        """Test fiscal period to event date inference."""
        test_cases = [
            ('Q1 2024', '2024-04-15'),
            ('Q2 2024', '2024-07-15'),
            ('Q3 2024', '2024-10-15'),
            ('Q4 2024', '2025-01-15'),
            ('FY2024', '2025-02-15'),
            ('2024-Q2', '2024-07-15'),  # Yahoo format
            ('current', datetime.now().strftime('%Y-%m-%d')),
        ]

        for period, expected in test_cases:
            result = SignalStore._infer_event_date_from_period(period)
            if period != 'current':
                self.assertEqual(result, expected, f"Failed for period: {period}")

    def test_event_date_backfill(self):
        """Test backfill functionality for event dates."""
        # First do a dry run
        dry_result = self.store.backfill_event_dates(dry_run=True)
        self.assertIsInstance(dry_result, dict)

        # Then do actual backfill
        result = self.store.backfill_event_dates(dry_run=False)
        self.assertIsInstance(result, dict)

    # ==================== CALENDAR EVENTS TESTS ====================

    def test_get_events_in_date_range(self):
        """Test querying events within a date range."""
        events = self.store.get_events_in_date_range(
            'FICO', '2024-07-01', '2024-12-31', event_type='earnings_call'
        )

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['event_type'], 'earnings_call')
        self.assertIn('freshness_days', events[0])

    def test_get_events_near_date(self):
        """Test querying events near a specific date."""
        events = self.store.get_events_near_date(
            'FICO', '2024-07-15', window_days=30
        )

        self.assertIn('before', events)
        self.assertIn('on_date', events)
        self.assertIn('after', events)

    def test_get_signals_around_event(self):
        """Test querying signals around an event."""
        signals = self.store.get_signals_around_event(
            'FICO', '2024-07-15',
            days_before=30, days_after=30,
            signal_types=['rating']
        )

        self.assertIn('before', signals)
        self.assertIn('after', signals)
        self.assertIn('event', signals)
        self.assertIn('summary', signals)

    # ==================== COMPARISON TESTS ====================

    def test_compare_yoy(self):
        """Test year-over-year comparison."""
        result = self.store.compare_yoy('FICO', 'Revenue', 2024, 1)

        self.assertIsNotNone(result['current_period'])
        self.assertIsNotNone(result['previous_period'])
        self.assertIsNotNone(result['percent_change'])
        self.assertEqual(result['comparison_type'], 'YoY')

        # Verify calculation
        current_val = 450000000
        previous_val = 420000000
        expected_change = ((current_val - previous_val) / previous_val) * 100
        self.assertAlmostEqual(result['percent_change'], expected_change, places=2)

    def test_compare_qoq(self):
        """Test quarter-over-quarter comparison."""
        result = self.store.compare_qoq('FICO', 'Revenue', 2024, 2)

        self.assertIsNotNone(result['current_period'])
        self.assertIsNotNone(result['previous_period'])
        self.assertEqual(result['current_quarter'], 'Q2 2024')
        self.assertEqual(result['previous_quarter'], 'Q1 2024')

    def test_calculate_growth_rate(self):
        """Test CAGR calculation."""
        result = self.store.calculate_growth_rate('FICO', 'Revenue', 2023, 2024, 1)

        self.assertIsNotNone(result['cagr'])
        self.assertIsNotNone(result['total_growth'])
        self.assertEqual(result['years'], 1)
        self.assertIn('growth_classification', result)

    # ==================== TREND DETECTION TESTS ====================

    def test_detect_metric_trend(self):
        """Test trend detection in metrics."""
        result = self.analyzer.detect_metric_trend(
            'FICO', 'Revenue', periods=3, period_type='quarterly'
        )

        self.assertIn('trend_direction', result)
        self.assertIn('trend_strength', result)
        self.assertIn('slope', result)
        self.assertIn('p_value', result)

    def test_calculate_momentum(self):
        """Test momentum calculation."""
        result = self.analyzer.calculate_momentum(
            'FICO', 'Revenue', short_periods=2, long_periods=3
        )

        self.assertIn('momentum_signal', result)
        self.assertIn('momentum_ratio', result)
        self.assertIn('short_ma', result)
        self.assertIn('long_ma', result)

    def test_identify_inflection_points(self):
        """Test inflection point identification."""
        result = self.analyzer.identify_inflection_points(
            'FICO', 'Revenue', threshold_pct=10.0
        )

        self.assertIn('inflection_points', result)
        self.assertIsInstance(result['inflection_points'], list)

    def test_analyze_volatility(self):
        """Test volatility analysis."""
        result = self.analyzer.analyze_volatility(
            'FICO', 'Revenue', periods=5
        )

        self.assertIn('coefficient_of_variation', result)
        self.assertIn('volatility_classification', result)
        self.assertIn('std_deviation', result)

    # ==================== PERIOD GENERATION TESTS ====================

    def test_get_trailing_quarters(self):
        """Test trailing quarters generation."""
        quarters = self.store.get_trailing_quarters(4, from_date='2024-10-15')

        self.assertEqual(len(quarters), 4)
        self.assertEqual(quarters[0]['period'], 'Q4 2024')
        self.assertIn('start_date', quarters[0])
        self.assertIn('end_date', quarters[0])
        self.assertIn('announcement_date', quarters[0])

    def test_get_fiscal_years(self):
        """Test fiscal years generation."""
        years = self.store.get_fiscal_years(3, from_year=2024)

        self.assertEqual(len(years), 3)
        self.assertEqual(years[0]['period'], 'FY2024')
        self.assertEqual(years[1]['period'], 'FY2023')

    def test_generate_comparison_periods(self):
        """Test comparison period generation."""
        comparisons = self.store.generate_comparison_periods(
            'FICO', 'Revenue', 'yoy', lookback_periods=2
        )

        self.assertIsInstance(comparisons, list)
        for comp in comparisons:
            self.assertIn('current_period', comp)
            self.assertIn('previous_period', comp)
            self.assertIn('has_both', comp)

    # ==================== PERIOD UTILITIES TESTS ====================

    def test_parse_period_string(self):
        """Test period string parsing."""
        test_cases = [
            ('Q2 2024', ('quarterly', 2024, 2)),
            ('FY2024', ('annual', 2024, None)),
            ('2024-Q3', ('quarterly', 2024, 3)),
        ]

        for period, expected in test_cases:
            result = parse_period_string(period)
            self.assertEqual(result, expected)

    def test_next_previous_period(self):
        """Test period navigation."""
        self.assertEqual(next_period('Q1 2024'), 'Q2 2024')
        self.assertEqual(next_period('Q4 2024'), 'Q1 2025')
        self.assertEqual(previous_period('Q1 2024'), 'Q4 2023')
        self.assertEqual(previous_period('Q2 2024'), 'Q1 2024')

    def test_period_difference(self):
        """Test period difference calculation."""
        self.assertEqual(period_difference('Q3 2024', 'Q1 2024'), 2)
        self.assertEqual(period_difference('Q1 2025', 'Q4 2024'), 1)
        self.assertEqual(period_difference('FY2024', 'FY2022'), 2)

    def test_add_periods(self):
        """Test period arithmetic."""
        self.assertEqual(add_periods('Q1 2024', 2), 'Q3 2024')
        self.assertEqual(add_periods('Q4 2024', -3), 'Q1 2024')
        self.assertEqual(add_periods('FY2024', 1), 'FY2025')

    def test_period_to_date_range(self):
        """Test period to date range conversion."""
        start, end = period_to_date_range('Q2 2024')
        self.assertEqual(start, '2024-04-01')
        self.assertEqual(end, '2024-06-30')

        start, end = period_to_date_range('FY2024')
        self.assertEqual(start, '2024-01-01')
        self.assertEqual(end, '2024-12-31')

    # ==================== INTEGRATION TESTS ====================

    def test_temporal_query_type_1_time_bounded(self):
        """Test Query Type 1: Time-Bounded Queries."""
        # Should find metrics in July 2024
        cursor = self.store.conn.cursor()
        july_metrics = cursor.execute("""
            SELECT * FROM financial_metrics
            WHERE ticker = 'FICO'
            AND COALESCE(event_date, created_at) >= '2024-07-01'
            AND COALESCE(event_date, created_at) <= '2024-07-31'
        """).fetchall()

        self.assertGreater(len(july_metrics), 0)

    def test_temporal_query_type_4_comparison(self):
        """Test Query Type 4: Temporal Comparison Queries."""
        yoy = self.store.compare_yoy('FICO', 'Revenue', 2024, 2)
        self.assertIsNotNone(yoy['percent_change'])

        qoq = self.store.compare_qoq('FICO', 'Revenue', 2024, 2)
        self.assertIsNotNone(qoq['absolute_change'])

    def test_temporal_query_type_5_event_driven(self):
        """Test Query Type 5: Event-Driven Queries."""
        events = self.store.get_events_in_date_range('FICO', '2024-01-01', '2024-12-31')
        self.assertGreater(len(events), 0)

        signals = self.store.get_signals_around_event('FICO', '2024-07-15')
        self.assertIn('before', signals)
        self.assertIn('after', signals)

    def test_temporal_query_type_7_trend_detection(self):
        """Test Query Type 7: Trend Detection Queries."""
        trend = self.analyzer.detect_metric_trend('FICO', 'Revenue')
        self.assertIn('trend_direction', trend)

        momentum = self.analyzer.calculate_momentum('FICO', 'Revenue')
        self.assertIn('momentum_signal', momentum)


if __name__ == '__main__':
    unittest.main()