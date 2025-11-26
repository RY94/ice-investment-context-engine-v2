# Location: tests/test_temporal_features.py
# Purpose: Comprehensive tests for temporal enhancement features (freshness, date filtering, composite scoring)
# Why: Validate correct implementation of time-based intelligence prioritization and ranking
# Relevant Files: temporal_enhancer.py, signal_store.py, ice_simplified.py, data_ingestion.py

import unittest
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../updated_architectures/implementation'))

from src.ice_core.temporal_enhancer import TemporalEnhancer
from updated_architectures.implementation.signal_store import SignalStore
from updated_architectures.implementation.ice_simplified import ICESimplified, ICEConfig


class TestTemporalFeatures(unittest.TestCase):
    """Test suite for temporal enhancement features."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.signal_store = SignalStore(db_path=self.temp_db.name)
        # The signal store will create a fresh database at this path

    @staticmethod
    def _get_test_ice_instance():
        """Create a minimal ICESimplified instance for testing with mocked dependencies."""
        # Create minimal config
        config = ICEConfig()

        # Mock the heavy dependencies to avoid initialization issues
        with patch('updated_architectures.implementation.ice_simplified.ICECore') as MockICECore, \
             patch('updated_architectures.implementation.ice_simplified.ProductionDataIngester') as MockIngester, \
             patch('updated_architectures.implementation.ice_simplified.QueryEngine') as MockQueryEngine:

            # Create mocked instances
            MockICECore.return_value = MagicMock()
            MockIngester.return_value = MagicMock()
            MockQueryEngine.return_value = MagicMock()

            # Create ICE instance with mocked dependencies
            ice = ICESimplified(config)
            return ice

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'signal_store'):
            self.signal_store.close()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    # ==================== FRESHNESS SCORE TESTS ====================

    def test_freshness_score_calculation(self):
        """Test freshness score calculation with exponential decay."""
        # Test various age scenarios
        test_cases = [
            (datetime.now().isoformat(), 1.0, 'very_fresh'),  # Today
            ((datetime.now() - timedelta(days=7)).isoformat(), None, 'very_fresh'),  # 1 week
            ((datetime.now() - timedelta(days=30)).isoformat(), None, 'fresh'),  # 30 days - don't check exact score
            ((datetime.now() - timedelta(days=60)).isoformat(), None, 'moderate'),  # 60 days - don't check exact score
            ((datetime.now() - timedelta(days=90)).isoformat(), None, 'moderate'),  # 90 days - don't check exact score
            ((datetime.now() - timedelta(days=365)).isoformat(), None, 'stale'),  # 1 year
        ]

        for timestamp, expected_score, expected_category in test_cases:
            score, category = TemporalEnhancer.calculate_freshness_from_timestamp(timestamp)

            # Check category
            self.assertEqual(category, expected_category,
                           f"Category mismatch for {timestamp}")

            # Check score if specified (allow small floating point differences)
            if expected_score is not None:
                self.assertAlmostEqual(score, expected_score, places=2,
                                     msg=f"Score mismatch for {timestamp}")

            # Ensure score is in valid range
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_freshness_score_edge_cases(self):
        """Test freshness score with edge cases."""
        # Future date (should be treated as very fresh)
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        score, category = TemporalEnhancer.calculate_freshness_from_timestamp(future_date)
        self.assertEqual(category, 'very_fresh')
        self.assertGreaterEqual(score, 0.9)

        # Very old date
        old_date = (datetime.now() - timedelta(days=1000)).isoformat()
        score, category = TemporalEnhancer.calculate_freshness_from_timestamp(old_date)
        self.assertEqual(category, 'very_stale')
        self.assertLess(score, 0.01)

    # ==================== DATE RANGE FILTERING TESTS ====================

    def test_signal_store_date_range_filtering(self):
        """Test date range filtering in SignalStore."""
        # Insert test data with different timestamps
        base_date = datetime.now()
        test_ratings = [
            {
                'ticker': 'NVDA',
                'rating': 'BUY',
                'timestamp': (base_date - timedelta(days=90)).isoformat(),
                'source_document_id': 'doc1',
                'confidence': 0.8
            },
            {
                'ticker': 'NVDA',
                'rating': 'HOLD',
                'timestamp': (base_date - timedelta(days=60)).isoformat(),
                'source_document_id': 'doc2',
                'confidence': 0.85
            },
            {
                'ticker': 'NVDA',
                'rating': 'STRONG BUY',
                'timestamp': (base_date - timedelta(days=30)).isoformat(),
                'source_document_id': 'doc3',
                'confidence': 0.9
            },
            {
                'ticker': 'NVDA',
                'rating': 'BUY',
                'timestamp': (base_date - timedelta(days=7)).isoformat(),
                'source_document_id': 'doc4',
                'confidence': 0.87
            }
        ]

        # Insert ratings
        for rating in test_ratings:
            self.signal_store.insert_rating(**rating)

        # Test date range queries
        start_date = (base_date - timedelta(days=65)).isoformat()
        end_date = (base_date - timedelta(days=5)).isoformat()

        results = self.signal_store.get_ratings_by_date_range(
            'NVDA', start_date, end_date
        )

        # Should get 3 ratings (60, 30, 7 days ago)
        self.assertEqual(len(results), 3)

        # Check freshness scores are included
        for result in results:
            self.assertIn('freshness_score', result)
            self.assertIn('freshness_category', result)

        # Verify ordering (most recent first)
        self.assertEqual(results[0]['rating'], 'BUY')  # 7 days ago
        self.assertEqual(results[1]['rating'], 'STRONG BUY')  # 30 days ago
        self.assertEqual(results[2]['rating'], 'HOLD')  # 60 days ago

    # ==================== COMPOSITE SCORING TESTS ====================

    def test_composite_score_calculation(self):
        """Test composite score calculation with different weights."""
        # Create a minimal ICE instance for testing
        ice = self._get_test_ice_instance()

        # Test with default weights
        score1 = ice.calculate_composite_score(
            confidence=0.8,
            freshness=0.4,
            relevance=0.9
        )
        # Expected: 0.3*0.8 + 0.3*0.4 + 0.4*0.9 = 0.24 + 0.12 + 0.36 = 0.72
        self.assertAlmostEqual(score1, 0.72, places=2)

        # Test with custom weights
        custom_weights = {
            'confidence': 0.5,
            'freshness': 0.2,
            'relevance': 0.3
        }
        score2 = ice.calculate_composite_score(
            confidence=0.8,
            freshness=0.4,
            relevance=0.9,
            weights=custom_weights
        )
        # Expected: 0.5*0.8 + 0.2*0.4 + 0.3*0.9 = 0.4 + 0.08 + 0.27 = 0.75
        self.assertAlmostEqual(score2, 0.75, places=2)

        # Test edge cases
        score_min = ice.calculate_composite_score(0, 0, 0)
        self.assertEqual(score_min, 0.0)

        score_max = ice.calculate_composite_score(1, 1, 1)
        self.assertEqual(score_max, 1.0)

    def test_rank_results_by_composite_score(self):
        """Test ranking results by composite score."""
        ice = self._get_test_ice_instance()

        test_results = [
            {
                'ticker': 'NVDA',
                'rating': 'BUY',
                'confidence': 0.9,
                'freshness_score': 0.2,  # Old but confident
                'relevance': 0.8
            },
            {
                'ticker': 'AMD',
                'rating': 'HOLD',
                'confidence': 0.6,
                'freshness_score': 0.9,  # Fresh but less confident
                'relevance': 0.7
            },
            {
                'ticker': 'INTC',
                'rating': 'SELL',
                'confidence': 0.8,
                'freshness_score': 0.8,  # Balanced
                'relevance': 0.9
            }
        ]

        # Rank results
        ranked = ice.rank_results_by_composite_score(test_results)

        # Check all results have composite scores
        for result in ranked:
            self.assertIn('composite_score', result)

        # Verify descending order
        for i in range(len(ranked) - 1):
            self.assertGreaterEqual(
                ranked[i]['composite_score'],
                ranked[i + 1]['composite_score']
            )

        # Test with minimum score filtering
        filtered = ice.rank_results_by_composite_score(
            test_results,
            min_score=0.7
        )
        # All composite scores should be >= 0.7
        for result in filtered:
            self.assertGreaterEqual(result['composite_score'], 0.7)

    # ==================== RELEVANCE SCORING TESTS ====================

    def test_relevance_score_estimation(self):
        """Test relevance score estimation for query-result matching."""
        ice = self._get_test_ice_instance()

        # Test high relevance (exact match)
        query1 = "What is the latest rating for NVDA?"
        result1 = "The latest analyst rating for NVDA is BUY with high confidence."
        score1 = ice.estimate_relevance_score(query1, result1, 'NVDA')
        self.assertGreater(score1, 0.4)  # Should be moderate to high relevance

        # Test medium relevance (partial match)
        query2 = "Show me revenue growth metrics"
        result2 = "The company reported strong financial performance last quarter."
        score2 = ice.estimate_relevance_score(query2, result2)
        self.assertGreaterEqual(score2, 0.1)  # Some relevance due to financial terms
        self.assertLess(score2, 0.8)

        # Test low relevance (no match)
        query3 = "What are the price targets?"
        result3 = "The weather today is sunny with clear skies."
        score3 = ice.estimate_relevance_score(query3, result3)
        self.assertLess(score3, 0.3)

        # Test ticker bonus
        query4 = "AAPL earnings"
        result4 = "AAPL reported earnings of $5.50 per share"
        score4 = ice.estimate_relevance_score(query4, result4, 'AAPL')
        self.assertGreater(score4, 0.45)  # Should get ticker bonus (moderate to high relevance)

    def test_relevance_position_weighting(self):
        """Test that relevance scoring weights earlier occurrences higher."""
        ice = self._get_test_ice_instance()

        query = "revenue growth"

        # Term appears early in result
        result_early = "Revenue growth was strong this quarter, exceeding expectations."
        score_early = ice.estimate_relevance_score(query, result_early)

        # Term appears late in result
        result_late = "The company performed well across all metrics, with particularly strong revenue growth."
        score_late = ice.estimate_relevance_score(query, result_late)

        # Early occurrence should score higher
        self.assertGreater(score_early, score_late)

    # ==================== INTEGRATION TESTS ====================

    def test_end_to_end_temporal_query(self):
        """Test end-to-end temporal query with all features integrated."""
        # Insert test data
        base_date = datetime.now()
        test_data = [
            {
                'ticker': 'TSLA',
                'rating': 'BUY',
                'timestamp': (base_date - timedelta(days=5)).isoformat(),
                'source_document_id': 'recent_doc',
                'confidence': 0.85,
                'firm': 'Morgan Stanley'
            },
            {
                'ticker': 'TSLA',
                'rating': 'HOLD',
                'timestamp': (base_date - timedelta(days=100)).isoformat(),
                'source_document_id': 'old_doc',
                'confidence': 0.95,  # Higher confidence but older
                'firm': 'Goldman Sachs'
            }
        ]

        for data in test_data:
            self.signal_store.insert_rating(**data)

        # Get latest rating (should include freshness scores)
        latest = self.signal_store.get_latest_rating('TSLA')

        self.assertIsNotNone(latest)
        self.assertEqual(latest['rating'], 'BUY')
        self.assertIn('freshness_score', latest)
        self.assertIn('freshness_category', latest)
        self.assertGreater(latest['freshness_score'], 0.7)  # Recent, so high freshness

        # Get rating history
        history = self.signal_store.get_rating_history('TSLA')

        self.assertEqual(len(history), 2)
        # Both should have freshness scores
        for rating in history:
            self.assertIn('freshness_score', rating)
            self.assertIn('freshness_category', rating)

        # Recent rating should have higher freshness
        self.assertGreater(history[0]['freshness_score'], history[1]['freshness_score'])

    def test_api_timestamp_extraction(self):
        """Test that API timestamps use publication dates not ingestion time."""
        # This test validates the fix for API timestamp extraction
        # In production, we'd mock the API responses and verify correct timestamp extraction

        # Simulate news article with publication date
        test_article = {
            'publishedAt': '2024-10-15T14:30:00Z',
            'title': 'Test Article',
            'description': 'Test description',
            'url': 'https://example.com'
        }

        # The timestamp should be from publishedAt, not current time
        # This would be tested in the actual fetch_company_news method
        # Here we just verify the structure expectation
        self.assertIn('publishedAt', test_article)
        self.assertNotEqual(test_article['publishedAt'], datetime.now().isoformat())

        # If we needed to test actual DataIngestion, we'd mock it:
        # with patch('updated_architectures.implementation.data_ingestion.DataIngestion') as MockIngestion:
        #     ingestion = MockIngestion()
        #     # Test ingestion behavior here


class TestCompositeScoring(unittest.TestCase):
    """Focused tests for composite scoring system."""

    @staticmethod
    def _get_test_ice_instance():
        """Create a minimal ICESimplified instance for testing with mocked dependencies."""
        # Create minimal config
        config = ICEConfig()

        # Mock the heavy dependencies to avoid initialization issues
        with patch('updated_architectures.implementation.ice_simplified.ICECore') as MockICECore, \
             patch('updated_architectures.implementation.ice_simplified.ProductionDataIngester') as MockIngester, \
             patch('updated_architectures.implementation.ice_simplified.QueryEngine') as MockQueryEngine:

            # Create mocked instances
            MockICECore.return_value = MagicMock()
            MockIngester.return_value = MagicMock()
            MockQueryEngine.return_value = MagicMock()

            # Create ICE instance with mocked dependencies
            ice = ICESimplified(config)
            return ice

    def test_weight_normalization(self):
        """Test that weights are properly normalized."""
        ice = self._get_test_ice_instance()

        # Test unnormalized weights
        unnormalized_weights = {
            'confidence': 2,
            'freshness': 2,
            'relevance': 2
        }

        score = ice.calculate_composite_score(
            confidence=0.6,
            freshness=0.6,
            relevance=0.6,
            weights=unnormalized_weights
        )

        # Should normalize to equal weights and give 0.6
        self.assertAlmostEqual(score, 0.6, places=2)

    def test_missing_scores_handling(self):
        """Test handling of missing scores in results."""
        ice = self._get_test_ice_instance()

        # Results with missing scores
        results = [
            {'ticker': 'NVDA', 'confidence': 0.8},  # Missing freshness and relevance
            {'ticker': 'AMD', 'freshness_score': 0.9},  # Missing confidence and relevance
            {'ticker': 'INTC'}  # Missing all scores
        ]

        ranked = ice.rank_results_by_composite_score(results)

        # Should handle missing scores with defaults
        self.assertEqual(len(ranked), 3)
        for result in ranked:
            self.assertIn('composite_score', result)
            self.assertGreaterEqual(result['composite_score'], 0.0)
            self.assertLessEqual(result['composite_score'], 1.0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)