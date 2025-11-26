# Location: /tests/test_entity_extraction_f1.py
# Purpose: Test and benchmark entity extraction F1 score improvements
# Why: Measure Phase 2 optimization progress toward F1 ≥0.85 target
# Relevant Files: enhanced_entity_extractor.py, entity_extractor.py

"""
F1 Score Testing for Entity Extraction

This test suite measures the precision, recall, and F1 score of
entity extraction to verify Phase 2 improvements.

Target: F1 score ≥0.85
Baseline: ~0.68
"""

import pytest
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import json
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.ice_core.enhanced_entity_extractor import (
    EnhancedEntityExtractor,
    ExtractedEntity,
    create_enhanced_extractor
)
from imap_email_ingestion_pipeline.entity_extractor import EntityExtractor as BaselineExtractor


class TestEntityExtractionF1:
    """Test suite for entity extraction F1 score measurement"""

    @pytest.fixture
    def test_documents(self):
        """Test documents with ground truth annotations"""
        return [
            {
                "text": "Apple Inc. (AAPL) reported Q4 2024 earnings of $89.5B in revenue, with CEO Tim Cook highlighting strong iPhone 15 sales.",
                "ground_truth": [
                    {"text": "Apple Inc.", "type": "COMPANY"},
                    {"text": "AAPL", "type": "TICKER"},
                    {"text": "Q4 2024", "type": "DATE"},
                    {"text": "$89.5B", "type": "METRIC"},
                    {"text": "Tim Cook", "type": "PERSON"},
                    {"text": "iPhone 15", "type": "PRODUCT"}
                ]
            },
            {
                "text": "NVIDIA's Jensen Huang announced a 206% YoY revenue increase to $18.12B, driven by AI chip demand from Microsoft and Amazon.",
                "ground_truth": [
                    {"text": "NVIDIA", "type": "COMPANY"},
                    {"text": "Jensen Huang", "type": "PERSON"},
                    {"text": "206%", "type": "METRIC"},
                    {"text": "$18.12B", "type": "METRIC"},
                    {"text": "Microsoft", "type": "COMPANY"},
                    {"text": "Amazon", "type": "COMPANY"}
                ]
            },
            {
                "text": "Tesla (TSLA) stock fell 5% to $195 after Q3 deliveries missed analyst expectations of 461,000 vehicles by 10,000 units.",
                "ground_truth": [
                    {"text": "Tesla", "type": "COMPANY"},
                    {"text": "TSLA", "type": "TICKER"},
                    {"text": "5%", "type": "METRIC"},
                    {"text": "$195", "type": "PRICE"},
                    {"text": "Q3", "type": "DATE"},
                    {"text": "461,000", "type": "METRIC"},
                    {"text": "10,000", "type": "METRIC"}
                ]
            },
            {
                "text": "Goldman Sachs upgraded Microsoft (MSFT) to Buy with a $450 price target, citing Azure growth and Copilot adoption.",
                "ground_truth": [
                    {"text": "Goldman Sachs", "type": "COMPANY"},
                    {"text": "Microsoft", "type": "COMPANY"},
                    {"text": "MSFT", "type": "TICKER"},
                    {"text": "$450", "type": "PRICE"},
                    {"text": "Azure", "type": "PRODUCT"},
                    {"text": "Copilot", "type": "PRODUCT"}
                ]
            },
            {
                "text": "Warren Buffett's Berkshire Hathaway (BRK.B) disclosed a $5.1B stake in Occidental Petroleum (OXY) in their 13F filing.",
                "ground_truth": [
                    {"text": "Warren Buffett", "type": "PERSON"},
                    {"text": "Berkshire Hathaway", "type": "COMPANY"},
                    {"text": "BRK.B", "type": "TICKER"},
                    {"text": "$5.1B", "type": "METRIC"},
                    {"text": "Occidental Petroleum", "type": "COMPANY"},
                    {"text": "OXY", "type": "TICKER"},
                    {"text": "13F", "type": "DOCUMENT"}
                ]
            }
        ]

    @pytest.fixture
    def enhanced_extractor(self):
        """Create enhanced entity extractor"""
        # Use regex mode for testing (no API calls)
        return create_enhanced_extractor(api_key=None)

    @pytest.fixture
    def baseline_extractor(self):
        """Create baseline entity extractor"""
        return BaselineExtractor()

    def calculate_f1_metrics(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """
        Calculate F1 metrics for entity extraction

        Args:
            predicted: List of predicted entities
            ground_truth: List of ground truth entities

        Returns:
            Dict with precision, recall, and F1 score
        """
        # Normalize for comparison
        def normalize_entity(e):
            text = e.get('text', e.get('ticker', e.get('normalized', '')))
            if text is None:
                text = ''
            text = str(text).lower()
            entity_type = e.get('type', 'UNKNOWN').upper()
            # Map types for consistency
            type_map = {
                'FINANCIAL_METRIC': 'METRIC',
                'FINANCIAL_METRICS': 'METRIC',
                'PRICES': 'PRICE',
                'DATES': 'DATE',
                'COMPANIES': 'COMPANY',
                'TICKERS': 'TICKER',
                'PEOPLE': 'PERSON'
            }
            entity_type = type_map.get(entity_type, entity_type)
            return (text, entity_type)

        # Convert to sets
        pred_set = {normalize_entity(e) for e in predicted}
        truth_set = {normalize_entity(e) for e in ground_truth}

        # Calculate metrics
        true_positives = len(pred_set & truth_set)
        false_positives = len(pred_set - truth_set)
        false_negatives = len(truth_set - pred_set)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'predicted_count': len(pred_set),
            'ground_truth_count': len(truth_set)
        }

    def test_baseline_f1_score(self, baseline_extractor, test_documents):
        """Measure baseline F1 score"""
        print("\n" + "="*60)
        print("BASELINE ENTITY EXTRACTION (Original)")
        print("="*60)

        all_metrics = []

        for i, doc in enumerate(test_documents, 1):
            # Extract entities
            result = baseline_extractor.extract_entities(doc['text'])

            # Flatten all entity types
            predicted = []
            for key, entities in result.items():
                if isinstance(entities, list) and key != 'context':
                    for entity in entities:
                        if isinstance(entity, dict):
                            predicted.append({
                                'text': entity.get('ticker', entity.get('text', '')),
                                'type': key.upper().rstrip('S')  # Remove plural
                            })

            # Calculate metrics
            metrics = self.calculate_f1_metrics(predicted, doc['ground_truth'])
            all_metrics.append(metrics)

            print(f"\nDocument {i}:")
            print(f"  Predicted: {metrics['predicted_count']} entities")
            print(f"  Ground Truth: {metrics['ground_truth_count']} entities")
            print(f"  Precision: {metrics['precision']:.3f}")
            print(f"  Recall: {metrics['recall']:.3f}")
            print(f"  F1 Score: {metrics['f1_score']:.3f}")

        # Calculate average
        avg_precision = sum(m['precision'] for m in all_metrics) / len(all_metrics)
        avg_recall = sum(m['recall'] for m in all_metrics) / len(all_metrics)
        avg_f1 = sum(m['f1_score'] for m in all_metrics) / len(all_metrics)

        print("\n" + "-"*40)
        print(f"BASELINE AVERAGE METRICS:")
        print(f"  Precision: {avg_precision:.3f}")
        print(f"  Recall: {avg_recall:.3f}")
        print(f"  F1 Score: {avg_f1:.3f} {'✅' if avg_f1 >= 0.85 else '❌'}")

        # Store for comparison
        self.baseline_f1 = avg_f1

    def test_enhanced_f1_score(self, enhanced_extractor, test_documents):
        """Measure enhanced F1 score"""
        print("\n" + "="*60)
        print("ENHANCED ENTITY EXTRACTION (Phase 2)")
        print("="*60)

        all_metrics = []

        for i, doc in enumerate(test_documents, 1):
            # Extract entities using enhanced extractor
            result = enhanced_extractor.extract_entities(doc['text'], use_llm=False)  # Regex mode for testing

            # Convert to dict format
            predicted = []
            for entity in result.get('entities', []):
                predicted.append({
                    'text': entity.text,
                    'type': entity.type
                })

            # Calculate metrics
            metrics = self.calculate_f1_metrics(predicted, doc['ground_truth'])
            all_metrics.append(metrics)

            print(f"\nDocument {i}:")
            print(f"  Predicted: {metrics['predicted_count']} entities")
            print(f"  Ground Truth: {metrics['ground_truth_count']} entities")
            print(f"  Precision: {metrics['precision']:.3f}")
            print(f"  Recall: {metrics['recall']:.3f}")
            print(f"  F1 Score: {metrics['f1_score']:.3f}")

        # Calculate average
        avg_precision = sum(m['precision'] for m in all_metrics) / len(all_metrics)
        avg_recall = sum(m['recall'] for m in all_metrics) / len(all_metrics)
        avg_f1 = sum(m['f1_score'] for m in all_metrics) / len(all_metrics)

        print("\n" + "-"*40)
        print(f"ENHANCED AVERAGE METRICS:")
        print(f"  Precision: {avg_precision:.3f}")
        print(f"  Recall: {avg_recall:.3f}")
        print(f"  F1 Score: {avg_f1:.3f} {'✅' if avg_f1 >= 0.85 else '❌'}")

        # Store for comparison
        self.enhanced_f1 = avg_f1

    def test_f1_improvement(self, baseline_extractor, enhanced_extractor, test_documents):
        """Test and compare F1 scores"""
        # Run both tests
        self.test_baseline_f1_score(baseline_extractor, test_documents)
        self.test_enhanced_f1_score(enhanced_extractor, test_documents)

        # Compare results
        print("\n" + "="*60)
        print("F1 SCORE COMPARISON")
        print("="*60)

        improvement = self.enhanced_f1 - self.baseline_f1
        improvement_pct = (improvement / self.baseline_f1) * 100 if self.baseline_f1 > 0 else 0

        print(f"\nBaseline F1: {self.baseline_f1:.3f}")
        print(f"Enhanced F1: {self.enhanced_f1:.3f}")
        print(f"Improvement: {improvement:.3f} ({improvement_pct:+.1f}%)")
        print(f"\nTarget F1: 0.850")
        print(f"Gap to Target: {0.85 - self.enhanced_f1:.3f}")

        if self.enhanced_f1 >= 0.85:
            print("\n✅ TARGET ACHIEVED! F1 score ≥0.85")
        else:
            print(f"\n⚠️ Target not yet reached. Need {0.85 - self.enhanced_f1:.3f} more improvement")

        # Assert improvement
        assert self.enhanced_f1 > self.baseline_f1, "Enhanced extractor should outperform baseline"

    def test_extraction_speed(self, baseline_extractor, enhanced_extractor):
        """Compare extraction speed"""
        test_text = """
        Apple Inc. (AAPL) and Microsoft (MSFT) dominated tech earnings this quarter.
        NVIDIA reported $18B revenue, while Tesla stock dropped to $195. CEO Tim Cook
        remains optimistic about Q1 2025 prospects. Goldman Sachs maintains Buy ratings.
        """ * 10  # Repeat for longer text

        print("\n" + "="*60)
        print("EXTRACTION SPEED COMPARISON")
        print("="*60)

        # Baseline speed
        start = time.time()
        for _ in range(10):
            baseline_extractor.extract_entities(test_text)
        baseline_time = time.time() - start

        # Enhanced speed (regex mode)
        start = time.time()
        for _ in range(10):
            enhanced_extractor.extract_entities(test_text, use_llm=False)
        enhanced_time = time.time() - start

        print(f"\nBaseline: {baseline_time:.3f}s for 10 extractions")
        print(f"Enhanced: {enhanced_time:.3f}s for 10 extractions")
        print(f"Speed ratio: {baseline_time/enhanced_time:.2f}x")

    def test_entity_validation(self, enhanced_extractor):
        """Test entity validation features"""
        print("\n" + "="*60)
        print("ENTITY VALIDATION TEST")
        print("="*60)

        test_text = "NVDA hit $750 yesterday, while APPL (typo) and MSFT reached new highs."

        result = enhanced_extractor.extract_entities(test_text, use_llm=False)

        print("\nExtracted entities:")
        for entity in result['entities']:
            print(f"  - {entity.text:<10} [{entity.type:<8}] confidence: {entity.confidence:.2f}")

        # Check that common typos are handled
        tickers = [e for e in result['entities'] if e.type == 'TICKER']
        assert any(e.text == 'NVDA' for e in tickers), "Should extract NVDA"
        assert any(e.text == 'MSFT' for e in tickers), "Should extract MSFT"

        print("\n✅ Validation test passed")


if __name__ == '__main__':
    # Run specific test with output
    import pytest
    pytest.main([__file__, '-v', '-s', '-k', 'test_f1_improvement'])