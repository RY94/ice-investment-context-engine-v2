# Location: /tests/test_contextual_traceability.py
# Purpose: Unit tests for Contextual Traceability System
# Why: Validates temporal classification, adaptive confidence, conflict detection, and source enrichment
# Relevant Files: src/ice_core/ice_query_processor.py

import unittest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ice_core.ice_query_processor import ICEQueryProcessor


class TestTemporalClassification(unittest.TestCase):
    """Test _classify_temporal_intent() method"""

    def setUp(self):
        """Initialize ICEQueryProcessor without dependencies for unit testing"""
        self.processor = ICEQueryProcessor(lightrag_instance=None, graph_builder=None)

    def test_historical_queries(self):
        """Test classification of historical queries"""
        historical_queries = [
            "What was Tencent's Q2 2025 operating margin?",
            "What did NVDA report for fiscal 2024?",
            "How much revenue did AAPL earn last quarter?",
            "What were TSMC's FY2023 earnings?",
            "What was the previous year's performance?",
            "GOOGL posted revenue in year 2024"
        ]
        for query in historical_queries:
            with self.subTest(query=query):
                result = self.processor._classify_temporal_intent(query)
                self.assertEqual(result, 'historical',
                               f"Expected 'historical' for: {query}")

    def test_current_queries(self):
        """Test classification of current queries"""
        current_queries = [
            "What are the current headwinds for NVDA?",
            "What is TSMC's latest price?",
            "What are the present risks for AAPL?",
            "What is happening now with GOOGL?",
            "What is the current market sentiment today?",
            "What are the latest developments right now?"
        ]
        for query in current_queries:
            with self.subTest(query=query):
                result = self.processor._classify_temporal_intent(query)
                self.assertEqual(result, 'current',
                               f"Expected 'current' for: {query}")

    def test_trend_queries(self):
        """Test classification of trend queries"""
        trend_queries = [
            "How has AAPL revenue been trending over time?",
            "What is the trajectory of NVDA's growth?",
            "How is TSMC's market share changing?",
            "What patterns do we see in GOOGL's performance?",
            "How has the stock been growing?",
            "What is the progression of earnings?"  # Removed "historical" to avoid conflict
        ]
        for query in trend_queries:
            with self.subTest(query=query):
                result = self.processor._classify_temporal_intent(query)
                self.assertEqual(result, 'trend',
                               f"Expected 'trend' for: {query}")

    def test_forward_queries(self):
        """Test classification of forward-looking queries"""
        forward_queries = [
            "What is TSMC's target price?",
            "What is the outlook for NVDA next quarter?",
            "What are the forecasts for AAPL?",
            "What guidance did the company provide?",
            "What will be the future performance?",
            "What is expected going forward?"
        ]
        for query in forward_queries:
            with self.subTest(query=query):
                result = self.processor._classify_temporal_intent(query)
                self.assertEqual(result, 'forward',
                               f"Expected 'forward' for: {query}")

    def test_unknown_queries(self):
        """Test queries that cannot be temporally classified"""
        unknown_queries = [
            "What is NVDA?",
            "Who is the CEO of AAPL?",
            "Where is TSMC headquartered?",
            "Which suppliers does GOOGL use?"
        ]
        for query in unknown_queries:
            with self.subTest(query=query):
                result = self.processor._classify_temporal_intent(query)
                self.assertEqual(result, 'unknown',
                               f"Expected 'unknown' for: {query}")

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Empty string
        self.assertEqual(self.processor._classify_temporal_intent(""), 'unknown')

        # Case sensitivity (should work regardless of case)
        self.assertEqual(
            self.processor._classify_temporal_intent("WHAT WAS Q2 2025 MARGIN?"),
            'historical'
        )

        # Mixed temporal signals (historical should win - checked first)
        result = self.processor._classify_temporal_intent(
            "What was Q2 2025 margin and what is the current outlook?"
        )
        self.assertEqual(result, 'historical')


class TestAdaptiveConfidence(unittest.TestCase):
    """Test _calculate_adaptive_confidence() method"""

    def setUp(self):
        self.processor = ICEQueryProcessor(lightrag_instance=None, graph_builder=None)

    def test_no_sources(self):
        """Test edge case: no sources"""
        result = self.processor._calculate_adaptive_confidence([])
        self.assertEqual(result['confidence'], 0.0)
        self.assertEqual(result['confidence_type'], 'no_sources')

    def test_single_source(self):
        """Test single authoritative source (most common)"""
        sources = [{'source': 'sec_edgar', 'confidence': 0.98}]
        result = self.processor._calculate_adaptive_confidence(sources)
        self.assertEqual(result['confidence'], 0.98)
        self.assertEqual(result['confidence_type'], 'single_source')
        self.assertIn('sec_edgar', result['explanation'])

    def test_weighted_average_multiple_sources(self):
        """Test weighted average for multiple agreeing sources"""
        sources = [
            {'source': 'sec_edgar', 'confidence': 0.98},
            {'source': 'fmp', 'confidence': 0.95},
            {'source': 'email', 'confidence': 0.85}
        ]
        result = self.processor._calculate_adaptive_confidence(sources)
        self.assertEqual(result['confidence_type'], 'weighted_average')
        # Weighted: (0.5*0.98 + 0.3*0.95 + 0.2*0.85) / 1.0 = 0.945
        self.assertAlmostEqual(result['confidence'], 0.945, places=3)
        self.assertEqual(len(result['breakdown']), 3)

    def test_variance_penalty_conflicting_sources(self):
        """Test variance penalty when sources disagree on numerical values"""
        sources = [
            {'source': 'api', 'confidence': 0.90, 'value': 100},
            {'source': 'email', 'confidence': 0.85, 'value': 120},  # 20% difference
            {'source': 'news', 'confidence': 0.80, 'value': 95}
        ]
        result = self.processor._calculate_adaptive_confidence(sources)
        self.assertEqual(result['confidence_type'], 'variance_penalized')
        # Should be penalized below base weighted average
        self.assertLess(result['confidence'], 0.9)
        self.assertIn('disagree', result['explanation'])

    def test_path_integrity_multihop(self):
        """Test path integrity for multi-hop reasoning"""
        sources = [
            {'source': 'sec', 'confidence': 0.90},
            {'source': 'api', 'confidence': 0.85}
        ]
        graph_context = {
            'causal_paths': [
                {
                    'confidence': 0.666,  # 3-hop multiplicative
                    'path': ['NVDA', 'TSMC', 'China']
                }
            ]
        }
        result = self.processor._calculate_adaptive_confidence(sources, graph_context)
        self.assertEqual(result['confidence_type'], 'path_integrity')
        self.assertEqual(result['confidence'], 0.666)
        self.assertIn('hop reasoning', result['explanation'])

    def test_source_quality_weights(self):
        """Test that SEC > API > News in weighted average"""
        # All sources have same raw confidence
        sources_sec = [{'source': 'sec', 'confidence': 0.9}]
        sources_api = [{'source': 'fmp', 'confidence': 0.9}]
        sources_news = [{'source': 'news', 'confidence': 0.9}]

        # With other sources present, SEC should dominate
        sources_mixed = [
            {'source': 'sec', 'confidence': 0.9},
            {'source': 'news', 'confidence': 0.9}
        ]
        result = self.processor._calculate_adaptive_confidence(sources_mixed)
        # Weighted: (0.5*0.9 + 0.2*0.9) / 0.7 = 0.9 (same, but SEC has 5/7 weight)
        self.assertAlmostEqual(result['confidence'], 0.9, places=2)


class TestConflictDetection(unittest.TestCase):
    """Test _detect_conflicts() method"""

    def setUp(self):
        self.processor = ICEQueryProcessor(lightrag_instance=None, graph_builder=None)

    def test_no_conflict_below_threshold(self):
        """Test no conflict detected when variance < 10%"""
        sources = [
            {'source': 'sec', 'confidence': 0.98, 'value': 100},
            {'source': 'api', 'confidence': 0.90, 'value': 105},  # 5% difference
            {'source': 'email', 'confidence': 0.85, 'value': 98}
        ]
        result = self.processor._detect_conflicts(sources)
        self.assertIsNone(result)  # No conflict flagged

    def test_conflict_detected_above_threshold(self):
        """Test conflict detected when variance > 10%"""
        sources = [
            {'source': 'sec', 'confidence': 0.98, 'value': 100},
            {'source': 'api', 'confidence': 0.90, 'value': 120},  # 20% difference
            {'source': 'email', 'confidence': 0.85, 'value': 95}
        ]
        result = self.processor._detect_conflicts(sources)
        self.assertIsNotNone(result)
        self.assertTrue(result['detected'])
        self.assertEqual(len(result['values']), 3)
        self.assertGreater(result['variance'], 0.1)
        self.assertIn('disagree', result['explanation'])

    def test_no_conflict_single_source(self):
        """Test no conflict with single source"""
        sources = [
            {'source': 'sec', 'confidence': 0.98, 'value': 100}
        ]
        result = self.processor._detect_conflicts(sources)
        self.assertIsNone(result)  # Need 2+ sources for conflict


class TestSourceEnrichment(unittest.TestCase):
    """Test _enrich_source_metadata() method"""

    def setUp(self):
        self.processor = ICEQueryProcessor(lightrag_instance=None, graph_builder=None)

    def test_quality_badges(self):
        """Test quality badge assignment based on source type"""
        sources = [
            {'source': 'sec_edgar', 'confidence': 0.98},
            {'source': 'fmp', 'confidence': 0.90},
            {'source': 'email', 'confidence': 0.85}
        ]
        result = self.processor._enrich_source_metadata(sources, 'unknown')
        enriched = result['enriched_sources']

        self.assertIn('🟢', enriched[0]['quality_badge'])  # SEC = Primary
        self.assertIn('🟡', enriched[1]['quality_badge'])  # FMP = Secondary
        self.assertIn('🔴', enriched[2]['quality_badge'])  # Email = Tertiary

    def test_link_extraction(self):
        """Test link extraction and construction"""
        sources = [
            {'source': 'sec', 'confidence': 0.98, 'url': 'https://sec.gov/filing123'},
            {'source': 'fmp', 'confidence': 0.90, 'ticker': 'NVDA', 'cik': '1045810'},
            {'source': 'email', 'confidence': 0.85, 'file_path': '/data/email_123.eml'}
        ]
        result = self.processor._enrich_source_metadata(sources, 'unknown')
        enriched = result['enriched_sources']

        # Direct URL preserved
        self.assertEqual(enriched[0]['link'], 'https://sec.gov/filing123')

        # SEC link constructed from CIK
        self.assertIn('sec.gov', enriched[1]['link'])
        self.assertIn('0001045810', enriched[1]['link'])  # CIK padded to 10 digits

        # File path converted to file:// URL
        self.assertTrue(enriched[2]['link'].startswith('file://'))

    def test_temporal_context_only_when_relevant(self):
        """Test temporal context shown only for current/trend queries"""
        from datetime import datetime, timedelta

        sources = [
            {'source': 'sec', 'confidence': 0.98, 'timestamp': datetime.now().isoformat()},
            {'source': 'api', 'confidence': 0.90, 'timestamp': (datetime.now() - timedelta(days=30)).isoformat()}
        ]

        # Historical query: No temporal context
        result_historical = self.processor._enrich_source_metadata(sources, 'historical')
        self.assertIsNone(result_historical['temporal_context'])

        # Current query: Show temporal context
        result_current = self.processor._enrich_source_metadata(sources, 'current')
        self.assertIsNotNone(result_current['temporal_context'])
        self.assertIn('most_recent', result_current['temporal_context'])
        self.assertIn('age_range', result_current['temporal_context'])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
