# Location: /src/ice_lightrag/test_hybrid_categorization.py
# Purpose: Test hybrid categorization with confidence scoring and LLM fallback
# Why: Validate accuracy and performance of new hybrid categorization system
# Relevant Files: graph_categorization.py, entity_categories.py

import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ice_lightrag.graph_categorization import (
    categorize_entity,
    categorize_entity_with_confidence,
    categorize_entity_hybrid
)

# Test cases: (entity_name, expected_category, should_be_high_confidence)
TEST_CASES = [
    # High confidence cases (clear patterns)
    ("NVIDIA Corporation", "Company", True),
    ("NVDA", "Company", True),
    ("Taiwan Semiconductor Manufacturing Company", "Company", True),
    ("Market Capitalization", "Financial Metric", True),
    ("PE Ratio", "Financial Metric", True),
    ("SECTOR: TECHNOLOGY", "Industry/Sector", True),

    # Medium confidence cases
    ("Graphics Processing Units", "Technology/Product", True),
    ("California", "Geographic", True),

    # Ambiguous cases (should trigger LLM for hybrid mode)
    ("Goldman Sachs", "Company", False),  # Financial firm (clear when just the name)
    ("AI-driven revenue growth", "Financial Metric", False),  # Could be Financial or Technology
    ("Silicon Valley expansion", "Geographic", False),  # Could be Geographic or Corporate
]


def test_confidence_scoring():
    """Test that confidence scores are assigned correctly based on priority."""
    print("\n=== Testing Confidence Scoring ===")

    for entity_name, expected_cat, should_be_high in TEST_CASES[:6]:  # Test clear cases
        category, confidence = categorize_entity_with_confidence(entity_name)

        status = "✓" if confidence >= 0.80 else "✗"
        print(f"{status} {entity_name:40s} → {category:20s} (conf: {confidence:.2f})")

        if should_be_high and confidence < 0.80:
            print(f"   ⚠️  Expected high confidence (≥0.80) for clear case")


def test_keyword_only():
    """Test traditional keyword-based categorization (baseline)."""
    print("\n=== Testing Keyword-Only Categorization ===")

    start = time.time()
    results = []

    for entity_name, expected_cat, _ in TEST_CASES:
        category = categorize_entity(entity_name)
        results.append((entity_name, category, expected_cat))
        match = "✓" if category == expected_cat else "✗"
        print(f"{match} {entity_name:40s} → {category}")

    elapsed = time.time() - start
    correct = sum(1 for _, cat, exp in results if cat == exp)
    print(f"\nAccuracy: {correct}/{len(TEST_CASES)} ({100*correct/len(TEST_CASES):.1f}%)")
    print(f"Time: {elapsed*1000:.1f}ms ({elapsed*1000/len(TEST_CASES):.1f}ms per entity)")


def test_hybrid_mode():
    """Test hybrid categorization with LLM fallback for ambiguous cases."""
    print("\n=== Testing Hybrid Categorization (with LLM) ===")

    start = time.time()
    results = []
    llm_calls = 0

    for entity_name, expected_cat, should_be_high in TEST_CASES:
        category, confidence = categorize_entity_hybrid(entity_name, confidence_threshold=0.70)

        # LLM was called if confidence jumped to 0.90 from low keyword confidence
        if confidence == 0.90:
            llm_calls += 1
            indicator = "🤖"
        else:
            indicator = "⚡"

        results.append((entity_name, category, expected_cat))
        match = "✓" if category == expected_cat else "✗"
        print(f"{match} {indicator} {entity_name:40s} → {category:20s} (conf: {confidence:.2f})")

    elapsed = time.time() - start
    correct = sum(1 for _, cat, exp in results if cat == exp)

    print(f"\nAccuracy: {correct}/{len(TEST_CASES)} ({100*correct/len(TEST_CASES):.1f}%)")
    print(f"LLM calls: {llm_calls}/{len(TEST_CASES)} ({100*llm_calls/len(TEST_CASES):.1f}%)")
    print(f"Time: {elapsed*1000:.1f}ms ({elapsed*1000/len(TEST_CASES):.1f}ms per entity)")

    if elapsed > 5.0:
        print(f"⚠️  Warning: Total time exceeds 5s target for {len(TEST_CASES)} entities")


def main():
    """Run all tests."""
    print("=" * 80)
    print("ICE Hybrid Categorization Test Suite")
    print("=" * 80)

    try:
        test_confidence_scoring()
        test_keyword_only()
        test_hybrid_mode()

        print("\n" + "=" * 80)
        print("✅ All tests completed")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
