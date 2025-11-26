# Location: /tests/test_entity_extraction_f1_llm.py
# Purpose: Test entity extraction F1 score with LLM mode enabled
# Why: Measure true performance with GPT-4 enhancement
# Relevant Files: enhanced_entity_extractor.py, test_entity_extraction_f1.py

"""
F1 Score Testing with LLM Enhancement

This test measures the full performance of entity extraction
with GPT-4 enhancement enabled.

Target: F1 score ≥0.85
"""

import pytest
import sys
import os
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.ice_core.enhanced_entity_extractor import (
    EnhancedEntityExtractor,
    create_enhanced_extractor
)
from tests.test_entity_extraction_f1 import TestEntityExtractionF1


class TestEntityExtractionF1WithLLM(TestEntityExtractionF1):
    """Test suite for entity extraction with LLM enhancement"""

    def test_llm_enhanced_f1_score(self, test_documents):
        """Measure F1 score with LLM enhancement"""
        # Skip if no API key
        if not os.environ.get('OPENAI_API_KEY'):
            pytest.skip("OpenAI API key not available")

        print("\n" + "="*60)
        print("🚀 LLM-ENHANCED ENTITY EXTRACTION (Full Phase 2)")
        print("="*60)

        # Create enhanced extractor with LLM
        enhanced_extractor = create_enhanced_extractor(
            api_key=os.environ.get('OPENAI_API_KEY')
        )

        all_metrics = []

        for i, doc in enumerate(test_documents, 1):
            print(f"\nProcessing Document {i}...")

            # Extract entities using LLM
            result = enhanced_extractor.extract_entities(
                doc['text'],
                use_llm=True  # Enable GPT-4 enhancement
            )

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

            print(f"  Predicted: {metrics['predicted_count']} entities")
            print(f"  Ground Truth: {metrics['ground_truth_count']} entities")
            print(f"  Precision: {metrics['precision']:.3f}")
            print(f"  Recall: {metrics['recall']:.3f}")
            print(f"  F1 Score: {metrics['f1_score']:.3f}")

            # Show what was extracted vs missed
            if metrics['f1_score'] < 0.8:
                pred_set = {(p['text'].lower(), p['type']) for p in predicted}
                truth_set = {(g['text'].lower(), g['type']) for g in doc['ground_truth']}

                missed = truth_set - pred_set
                if missed:
                    print(f"  Missed entities: {missed}")

                extra = pred_set - truth_set
                if extra:
                    print(f"  Extra entities: {extra}")

        # Calculate average
        avg_precision = sum(m['precision'] for m in all_metrics) / len(all_metrics)
        avg_recall = sum(m['recall'] for m in all_metrics) / len(all_metrics)
        avg_f1 = sum(m['f1_score'] for m in all_metrics) / len(all_metrics)

        print("\n" + "-"*40)
        print(f"LLM-ENHANCED AVERAGE METRICS:")
        print(f"  Precision: {avg_precision:.3f}")
        print(f"  Recall: {avg_recall:.3f}")
        print(f"  F1 Score: {avg_f1:.3f} {'✅' if avg_f1 >= 0.85 else '❌'}")

        if avg_f1 >= 0.85:
            print("\n✅ TARGET ACHIEVED! F1 score ≥0.85 with LLM enhancement")
        else:
            print(f"\n⚠️ Gap to target: {0.85 - avg_f1:.3f}")

        # Compare with regex-only mode
        print("\n" + "="*60)
        print("COMPARING EXTRACTION MODES")
        print("="*60)

        # Quick regex-only test
        regex_extractor = create_enhanced_extractor(api_key=None)
        regex_metrics = []

        for doc in test_documents:
            result = regex_extractor.extract_entities(doc['text'], use_llm=False)
            predicted = [{'text': e.text, 'type': e.type} for e in result.get('entities', [])]
            metrics = self.calculate_f1_metrics(predicted, doc['ground_truth'])
            regex_metrics.append(metrics)

        regex_f1 = sum(m['f1_score'] for m in regex_metrics) / len(regex_metrics)

        print(f"Regex-only F1: {regex_f1:.3f}")
        print(f"LLM-enhanced F1: {avg_f1:.3f}")
        print(f"Improvement from LLM: {avg_f1 - regex_f1:.3f} ({((avg_f1 - regex_f1)/regex_f1)*100:+.1f}%)")

        # Test assertion
        assert avg_f1 > regex_f1, "LLM should improve F1 score"

    def test_cost_analysis(self):
        """Analyze cost implications of LLM usage"""
        if not os.environ.get('OPENAI_API_KEY'):
            pytest.skip("OpenAI API key not available")

        print("\n" + "="*60)
        print("💰 COST ANALYSIS")
        print("="*60)

        # Sample text (~200 tokens)
        sample_text = """
        Apple Inc. (AAPL) reported Q4 2024 earnings with revenue of $89.5B.
        CEO Tim Cook highlighted iPhone 15 sales. Microsoft (MSFT) and NVIDIA
        posted strong results. Tesla stock dropped 5% to $195.
        """ * 3

        # Estimate tokens
        approx_tokens = len(sample_text.split()) * 1.3  # Rough estimate

        # GPT-4 pricing (as of 2024)
        input_cost_per_1k = 0.03  # $0.03 per 1K input tokens
        output_cost_per_1k = 0.06  # $0.06 per 1K output tokens

        estimated_input = approx_tokens
        estimated_output = 100  # Typical entity extraction output

        cost_per_extraction = (
            (estimated_input / 1000 * input_cost_per_1k) +
            (estimated_output / 1000 * output_cost_per_1k)
        )

        print(f"Sample text: ~{int(approx_tokens)} tokens")
        print(f"Estimated cost per extraction: ${cost_per_extraction:.4f}")
        print(f"Cost for 1,000 documents: ${cost_per_extraction * 1000:.2f}")
        print(f"Cost for 10,000 documents: ${cost_per_extraction * 10000:.2f}")

        print("\n📊 Cost-Benefit Analysis:")
        print("  - Regex-only: $0 (F1 ~0.44)")
        print(f"  - LLM-enhanced: ${cost_per_extraction:.4f}/doc (F1 target 0.85)")
        print("  - Hybrid approach: Use LLM for critical docs, regex for others")
        print("  - Caching: Reduces repeated extraction costs by 80-90%")


if __name__ == '__main__':
    # Run specific test with output
    import pytest
    pytest.main([__file__, '-v', '-s', '-k', 'test_llm_enhanced'])