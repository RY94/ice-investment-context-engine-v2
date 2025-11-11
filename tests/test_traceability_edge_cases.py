# Location: /tests/test_traceability_edge_cases.py
# Purpose: Comprehensive edge case testing for Contextual Traceability System
# Why: Verify honest functionality, no coverups, graceful degradation
# Relevant Files: src/ice_core/ice_query_processor.py, tests/test_contextual_traceability.py

import unittest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ice_core.ice_query_processor import ICEQueryProcessor


class TestEdgeCasesAndBugs(unittest.TestCase):
    """Test edge cases, potential bugs, and error handling"""

    def setUp(self):
        self.processor = ICEQueryProcessor(lightrag_instance=None, graph_builder=None)

    # ============ TEMPORAL CLASSIFICATION EDGE CASES ============

    def test_temporal_mixed_signals_historical_wins(self):
        """Test precedence when multiple temporal signals present"""
        # "Q2 2024" (historical) should win over "current"
        query = "What was the Q2 2024 revenue and what is the current outlook?"
        result = self.processor._classify_temporal_intent(query)
        self.assertEqual(result, 'historical',
                        "Historical patterns should be checked first and win")

    def test_temporal_empty_string(self):
        """Test empty string doesn't crash"""
        result = self.processor._classify_temporal_intent("")
        self.assertEqual(result, 'unknown')

    def test_temporal_none_input(self):
        """Test None input handling"""
        # This should crash gracefully or be prevented by typing
        try:
            result = self.processor._classify_temporal_intent(None)
            self.fail("Should handle None input gracefully")
        except (AttributeError, TypeError):
            pass  # Expected to fail

    def test_temporal_very_long_query(self):
        """Test performance with very long query (1000+ words)"""
        long_query = " ".join(["word"] * 1000) + " Q2 2024 revenue"
        result = self.processor._classify_temporal_intent(long_query)
        self.assertEqual(result, 'historical')

    # ============ ADAPTIVE CONFIDENCE EDGE CASES ============

    def test_confidence_empty_sources_list(self):
        """Test empty sources list returns 0 confidence"""
        result = self.processor._calculate_adaptive_confidence([])
        self.assertEqual(result['confidence'], 0.0)
        self.assertEqual(result['confidence_type'], 'no_sources')

    def test_confidence_sources_missing_confidence_field(self):
        """Test sources without confidence field use default 0.7"""
        sources = [{'source': 'test'}]  # No confidence field
        result = self.processor._calculate_adaptive_confidence(sources)
        self.assertEqual(result['confidence'], 0.7)

    def test_confidence_zero_division_in_variance(self):
        """Test variance calculation when mean is zero"""
        sources = [
            {'source': 'a', 'confidence': 0.9, 'value': 0},
            {'source': 'b', 'confidence': 0.8, 'value': 0}
        ]
        result = self.processor._calculate_adaptive_confidence(sources)
        # Should handle division by zero gracefully
        self.assertIsNotNone(result)

    def test_confidence_single_value_no_variance(self):
        """Test single value cannot compute stdev"""
        sources = [
            {'source': 'a', 'confidence': 0.9, 'value': 100}
        ]
        result = self.processor._calculate_adaptive_confidence(sources)
        # Should return single_source, not attempt variance calculation
        self.assertEqual(result['confidence_type'], 'single_source')

    def test_confidence_negative_values(self):
        """Test negative numerical values don't break variance"""
        sources = [
            {'source': 'a', 'confidence': 0.9, 'value': -100},
            {'source': 'b', 'confidence': 0.8, 'value': -120}
        ]
        result = self.processor._calculate_adaptive_confidence(sources)
        self.assertIsNotNone(result)
        # Should still calculate variance correctly

    def test_confidence_very_large_variance(self):
        """Test extreme variance (>100%)"""
        sources = [
            {'source': 'a', 'confidence': 0.9, 'value': 1},
            {'source': 'b', 'confidence': 0.8, 'value': 1000}  # 1000x difference
        ]
        result = self.processor._calculate_adaptive_confidence(sources)
        self.assertEqual(result['confidence_type'], 'variance_penalized')
        # Should floor at 0.5
        self.assertGreaterEqual(result['confidence'], 0.5)

    def test_confidence_unknown_source_gets_lowest_weight(self):
        """Test unknown sources get 0.1 weight in weighted average"""
        sources = [
            {'source': 'unknown_xyz', 'confidence': 0.9},
            {'source': 'sec', 'confidence': 0.8}
        ]
        result = self.processor._calculate_adaptive_confidence(sources)
        # SEC should dominate due to higher weight
        # (0.5*0.8 + 0.1*0.9) / 0.6 = 0.817
        self.assertAlmostEqual(result['confidence'], 0.817, places=2)

    # ============ SOURCE ENRICHMENT EDGE CASES ============

    def test_enrichment_sources_without_source_field(self):
        """Test sources missing 'source' field don't crash"""
        sources = [{'confidence': 0.9}]  # No 'source' field
        result = self.processor._enrich_source_metadata(sources, 'unknown')
        enriched = result['enriched_sources']
        self.assertEqual(enriched[0]['source'], 'unknown')  # Default fallback

    def test_enrichment_malformed_timestamp(self):
        """Test invalid timestamp format doesn't crash"""
        sources = [
            {'source': 'test', 'confidence': 0.9, 'timestamp': 'invalid-date-format'}
        ]
        result = self.processor._enrich_source_metadata(sources, 'current')
        enriched = result['enriched_sources']
        # Should gracefully degrade - no timestamp/age added
        self.assertNotIn('age', enriched[0])

    def test_enrichment_timestamp_future_date(self):
        """Test future timestamps (shouldn't happen but check graceful handling)"""
        future = (datetime.now() + timedelta(days=30)).isoformat()
        sources = [
            {'source': 'test', 'confidence': 0.9, 'timestamp': future}
        ]
        result = self.processor._enrich_source_metadata(sources, 'current')
        # Should handle gracefully (might show negative age or fail gracefully)
        self.assertIsNotNone(result)

    def test_enrichment_cik_padding(self):
        """Test CIK padding to 10 digits"""
        sources = [
            {'source': 'sec', 'confidence': 0.9, 'cik': '123'}  # Short CIK
        ]
        result = self.processor._enrich_source_metadata(sources, 'unknown')
        enriched = result['enriched_sources']
        # Should pad to 10 digits: 0000000123
        self.assertIn('0000000123', enriched[0]['link'])

    def test_enrichment_no_temporal_for_historical(self):
        """Verify temporal context NOT shown for historical queries"""
        sources = [
            {'source': 'sec', 'confidence': 0.9, 'timestamp': datetime.now().isoformat()}
        ]
        result = self.processor._enrich_source_metadata(sources, 'historical')
        self.assertIsNone(result['temporal_context'])

    def test_enrichment_no_temporal_for_forward(self):
        """Verify temporal context NOT shown for forward queries"""
        sources = [
            {'source': 'sec', 'confidence': 0.9, 'timestamp': datetime.now().isoformat()}
        ]
        result = self.processor._enrich_source_metadata(sources, 'forward')
        self.assertIsNone(result['temporal_context'])

    # ============ CONFLICT DETECTION EDGE CASES ============

    def test_conflict_no_numerical_values(self):
        """Test sources without 'value' field return None"""
        sources = [
            {'source': 'a', 'confidence': 0.9},
            {'source': 'b', 'confidence': 0.8}
        ]
        result = self.processor._detect_conflicts(sources)
        self.assertIsNone(result)

    def test_conflict_mixed_values_and_no_values(self):
        """Test mix of sources with/without values"""
        sources = [
            {'source': 'a', 'confidence': 0.9, 'value': 100},
            {'source': 'b', 'confidence': 0.8},  # No value
            {'source': 'c', 'confidence': 0.7, 'value': 105}
        ]
        result = self.processor._detect_conflicts(sources)
        # Should only use sources with values (a, c)
        # Variance ~5% should be below threshold
        self.assertIsNone(result)

    def test_conflict_string_values_ignored(self):
        """Test non-numeric 'value' fields are ignored"""
        sources = [
            {'source': 'a', 'confidence': 0.9, 'value': 'high'},  # String
            {'source': 'b', 'confidence': 0.8, 'value': 100}
        ]
        result = self.processor._detect_conflicts(sources)
        # Should ignore string value, only 1 numerical value left
        self.assertIsNone(result)

    def test_conflict_exactly_10_percent_threshold(self):
        """Test boundary case: exactly 10% variance"""
        # Create sources with exactly 10% coef_var
        # Mean=100, values=[90, 100, 110] → std=10, cv=0.1
        sources = [
            {'source': 'a', 'confidence': 0.9, 'value': 90},
            {'source': 'b', 'confidence': 0.8, 'value': 100},
            {'source': 'c', 'confidence': 0.7, 'value': 110}
        ]
        result = self.processor._detect_conflicts(sources)
        # Threshold is > 0.1, so exactly 0.1 should return None
        # BUT actual cv might be slightly different due to rounding
        # Let's check the actual behavior
        self.assertIsNone(result, "Exactly 10% should NOT trigger conflict (threshold is >0.1)")

    # ============ FORMAT ADAPTIVE DISPLAY EDGE CASES ============

    def test_display_minimal_enriched_result(self):
        """Test display with minimal data (only answer)"""
        enriched_result = {
            'answer': 'Test answer'
        }
        output = self.processor.format_adaptive_display(enriched_result)
        self.assertIn('Test answer', output)
        self.assertIn('✅ ANSWER', output)
        # Should not crash, gracefully show only answer card

    def test_display_all_cards(self):
        """Test display with all cards present"""
        enriched_result = {
            'answer': 'Test answer',
            'reliability': {
                'confidence': 0.85,
                'confidence_type': 'weighted_average',
                'explanation': 'Test explanation',
                'breakdown': {'sec': 0.9, 'api': 0.8}
            },
            'source_metadata': {
                'enriched_sources': [
                    {'source': 'sec', 'confidence': 0.9, 'quality_badge': '🟢 Primary'}
                ],
                'temporal_context': {
                    'most_recent': {'source': 'sec', 'age': '1 day ago'},
                    'oldest': {'source': 'sec', 'age': '1 day ago'},
                    'age_range': '1 day ago'
                }
            },
            'conflicts': {
                'detected': True,
                'values': [100, 120],
                'sources': ['sec', 'api'],
                'variance': 0.15,
                'explanation': 'Test conflict'
            },
            'graph_context': {
                'causal_paths': [{
                    'confidence': 0.7,
                    'path': ['A', 'B', 'C']
                }]
            }
        }
        output = self.processor.format_adaptive_display(enriched_result)
        # Should show all 6 cards
        self.assertIn('✅ ANSWER', output)
        self.assertIn('🎯 RELIABILITY', output)
        self.assertIn('📚 SOURCES', output)
        self.assertIn('⏰ TEMPORAL CONTEXT', output)
        self.assertIn('⚠️  CONFLICTS DETECTED', output)
        self.assertIn('🔗 REASONING PATH', output)

    def test_display_empty_sources_list(self):
        """Test display with empty sources list"""
        enriched_result = {
            'answer': 'Test',
            'source_metadata': {
                'enriched_sources': []
            }
        }
        output = self.processor.format_adaptive_display(enriched_result)
        # Should not show sources card if empty
        self.assertNotIn('📚 SOURCES', output)

    def test_display_unicode_handling(self):
        """Test display with unicode characters in answer"""
        enriched_result = {
            'answer': '中文测试 русский тест العربية'
        }
        output = self.processor.format_adaptive_display(enriched_result)
        self.assertIn('中文测试', output)
        # Should handle unicode correctly

    # ============ INTEGRATION EDGE CASES ============

    def test_end_to_end_minimal_flow(self):
        """Test minimal end-to-end flow"""
        # Simulate minimal real-world usage
        question = "What was Q2 2024 revenue?"
        sources = [{'source': 'sec', 'confidence': 0.95}]

        # Step 1: Classify temporal intent
        temporal_intent = self.processor._classify_temporal_intent(question)
        self.assertEqual(temporal_intent, 'historical')

        # Step 2: Enrich sources
        enriched_meta = self.processor._enrich_source_metadata(sources, temporal_intent)
        self.assertEqual(len(enriched_meta['enriched_sources']), 1)
        self.assertIsNone(enriched_meta['temporal_context'])  # Historical = no temporal

        # Step 3: Calculate confidence
        reliability = self.processor._calculate_adaptive_confidence(sources)
        self.assertEqual(reliability['confidence'], 0.95)
        self.assertEqual(reliability['confidence_type'], 'single_source')

        # Step 4: Detect conflicts
        conflicts = self.processor._detect_conflicts(enriched_meta['enriched_sources'])
        self.assertIsNone(conflicts)  # Single source = no conflict

        # Step 5: Format display
        enriched_result = {
            'answer': 'Revenue was $100M',
            'reliability': reliability,
            'source_metadata': enriched_meta,
            'conflicts': conflicts
        }
        output = self.processor.format_adaptive_display(enriched_result)
        self.assertIn('Revenue was $100M', output)
        self.assertIn('95%', output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
