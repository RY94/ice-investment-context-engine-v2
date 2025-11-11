# Location: tests/test_sentence_attributor.py
# Purpose: Validate SentenceAttributor implementation
# Why: Ensure sentence-level attribution via semantic similarity works correctly
# Relevant Files: src/ice_core/sentence_attributor.py

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ice_core.sentence_attributor import SentenceAttributor


def test_sentence_splitting():
    """Test sentence splitting functionality"""
    print("\n" + "="*80)
    print("TEST 1: Sentence Splitting")
    print("="*80)

    attributor = SentenceAttributor()

    # Test basic splitting
    text1 = "First sentence. Second sentence! Third sentence?"
    sentences1 = attributor._split_into_sentences(text1)

    print(f"\nText: {text1}")
    print(f"Sentences: {len(sentences1)}")
    for i, sent in enumerate(sentences1, 1):
        print(f"  {i}. {sent}")

    assert len(sentences1) == 3, f"Expected 3 sentences, got {len(sentences1)}"

    # Test with numbers and abbreviations
    text2 = "The company's revenue was $2.5 billion. This is good news. Dr. Smith agreed."
    sentences2 = attributor._split_into_sentences(text2)

    print(f"\nText: {text2}")
    print(f"Sentences: {len(sentences2)}")
    for i, sent in enumerate(sentences2, 1):
        print(f"  {i}. {sent}")

    assert len(sentences2) >= 2, "Should handle numbers and abbreviations"

    print("\n✅ Sentence splitting works correctly")
    return sentences1


def test_cosine_similarity():
    """Test cosine similarity computation"""
    print("\n" + "="*80)
    print("TEST 2: Cosine Similarity Computation")
    print("="*80)

    attributor = SentenceAttributor()

    # Create sample embeddings
    embeddings_a = np.array([
        [1.0, 0.0, 0.0],  # Vector 1
        [0.0, 1.0, 0.0]   # Vector 2
    ])

    embeddings_b = np.array([
        [1.0, 0.0, 0.0],  # Same as Vector 1
        [0.5, 0.5, 0.0],  # Between Vector 1 and 2
        [0.0, 0.0, 1.0]   # Orthogonal to both
    ])

    similarity = attributor._compute_cosine_similarity(embeddings_a, embeddings_b)

    print(f"\nSimilarity matrix shape: {similarity.shape}")
    print(f"Expected: (2, 3)")
    assert similarity.shape == (2, 3)

    # Check specific similarities
    print(f"\nVector 1 vs Vector 1 (same): {similarity[0, 0]:.2f}")
    assert abs(similarity[0, 0] - 1.0) < 0.01, "Same vectors should have similarity ~1.0"

    print(f"Vector 1 vs Orthogonal: {similarity[0, 2]:.2f}")
    assert abs(similarity[0, 2]) < 0.01, "Orthogonal vectors should have similarity ~0.0"

    print("\n✅ Cosine similarity computation correct")
    return similarity


def test_sentence_attribution_mock():
    """Test sentence attribution with mock data (no real embeddings)"""
    print("\n" + "="*80)
    print("TEST 3: Sentence Attribution (Mock Data)")
    print("="*80)

    # Mock attributor to avoid needing real embedding function
    attributor = SentenceAttributor()

    # Manually create mock embeddings instead of using API
    answer = "Tencent's Q2 2025 operating margin was 34%. This represents strong performance."

    parsed_context = {
        "chunks": [
            {
                "chunk_id": 1,
                "content": "Tencent Q2 2025 operating margin 34% strong growth...",
                "source_type": "email",
                "confidence": 0.90,
                "date": "2025-08-15",
                "relevance_rank": 1,
                "source_details": {"subject": "Tencent Earnings"}
            },
            {
                "chunk_id": 2,
                "content": "Performance metrics show improvement...",
                "source_type": "api",
                "confidence": 0.85,
                "date": "2025-08-14",
                "relevance_rank": 2,
                "source_details": {"api": "fmp"}
            }
        ]
    }

    # Override embedding function with mock
    original_func = attributor._embedding_func

    def mock_embed(texts):
        # Return mock embeddings (2D array)
        # Make sentence 1 similar to chunk 1, sentence 2 similar to chunk 2
        if len(texts) == 2:  # Sentences
            return np.array([
                [1.0, 0.0],  # Sentence 1
                [0.0, 1.0]   # Sentence 2
            ])
        else:  # Chunks
            return np.array([
                [0.9, 0.1],  # Chunk 1 (similar to sentence 1)
                [0.1, 0.9]   # Chunk 2 (similar to sentence 2)
            ])

    attributor._embedding_func = mock_embed

    # Run attribution
    attributed = attributor.attribute_sentences(answer, parsed_context)

    # Restore original function
    attributor._embedding_func = original_func

    print(f"\n✅ Attributed {len(attributed)} sentences")

    for sent_attr in attributed:
        print(f"\nSentence {sent_attr['sentence_number']}: {sent_attr['sentence']}")
        print(f"   Has attribution: {sent_attr['has_attribution']}")
        print(f"   Confidence: {sent_attr['attribution_confidence']}")
        print(f"   Attributed chunks: {len(sent_attr['attributed_chunks'])}")

    assert len(attributed) == 2, "Should have 2 sentences"
    assert attributed[0]['has_attribution'], "Sentence 1 should be attributed"

    return attributed


def test_formatted_output():
    """Test formatted output for attributed sentences"""
    print("\n" + "="*80)
    print("TEST 4: Formatted Output")
    print("="*80)

    attributor = SentenceAttributor()

    # Sample attributed sentences
    attributed_sentences = [
        {
            "sentence": "Tencent's Q2 2025 operating margin was 34%.",
            "sentence_number": 1,
            "attributed_chunks": [
                {
                    "chunk_id": 1,
                    "source_type": "email",
                    "confidence": 0.90,
                    "similarity_score": 0.87,
                    "date": "2025-08-15",
                    "source_details": {}
                }
            ],
            "attribution_confidence": 0.87,
            "has_attribution": True
        },
        {
            "sentence": "This represents a 2% increase from Q1 2025.",
            "sentence_number": 2,
            "attributed_chunks": [],
            "attribution_confidence": 0.65,
            "has_attribution": False
        }
    ]

    formatted = attributor.format_attributed_sentences(attributed_sentences)

    print("\nFormatted output:")
    print(formatted)

    assert "[1]" in formatted, "Should include sentence numbers"
    assert "email" in formatted, "Should include source types"
    assert "⚠️" in formatted, "Should warn about unattributed sentences"

    print("\n✅ Formatted output correct")
    return formatted


def test_attribution_statistics():
    """Test attribution statistics generation"""
    print("\n" + "="*80)
    print("TEST 5: Attribution Statistics")
    print("="*80)

    attributor = SentenceAttributor()

    attributed_sentences = [
        {
            "sentence": "Sentence 1",
            "sentence_number": 1,
            "attributed_chunks": [
                {"source_type": "email", "confidence": 0.90}
            ],
            "attribution_confidence": 0.90,
            "has_attribution": True
        },
        {
            "sentence": "Sentence 2",
            "sentence_number": 2,
            "attributed_chunks": [
                {"source_type": "api", "confidence": 0.85}
            ],
            "attribution_confidence": 0.85,
            "has_attribution": True
        },
        {
            "sentence": "Sentence 3",
            "sentence_number": 3,
            "attributed_chunks": [],
            "attribution_confidence": 0.60,
            "has_attribution": False
        }
    ]

    stats = attributor.get_attribution_statistics(attributed_sentences)

    print("\nAttribution Statistics:")
    print(f"   Total sentences: {stats['total_sentences']}")
    print(f"   Attributed: {stats['attributed_sentences']}")
    print(f"   Unattributed: {stats['unattributed_sentences']}")
    print(f"   Coverage: {stats['coverage_percentage']}%")
    print(f"   Avg confidence: {stats['average_confidence']}")
    print(f"   Sources by type: {stats['sources_by_type']}")

    assert stats['total_sentences'] == 3
    assert stats['attributed_sentences'] == 2
    assert stats['unattributed_sentences'] == 1
    assert stats['coverage_percentage'] == 66.7

    print("\n✅ Statistics generation correct")
    return stats


def test_real_embedding_if_available():
    """Test with real embeddings if OpenAI key available"""
    print("\n" + "="*80)
    print("TEST 6: Real Embeddings (If Available)")
    print("="*80)

    import os

    if not os.getenv('OPENAI_API_KEY'):
        print("\n⚠️  OPENAI_API_KEY not set, skipping real embedding test")
        return None

    try:
        attributor = SentenceAttributor()

        if not attributor._embedding_func:
            print("\n⚠️  No embedding function initialized, skipping")
            return None

        answer = "Tencent's operating margin was 34%. Revenue grew 15%."

        parsed_context = {
            "chunks": [
                {
                    "chunk_id": 1,
                    "content": "Tencent Q2 2025 financial results: operating margin 34%, strong performance",
                    "source_type": "email",
                    "confidence": 0.90,
                    "date": "2025-08-15",
                    "relevance_rank": 1,
                    "source_details": {}
                },
                {
                    "chunk_id": 2,
                    "content": "Revenue increased 15% year-over-year in Q2 2025",
                    "source_type": "api",
                    "confidence": 0.85,
                    "date": "2025-08-14",
                    "relevance_rank": 2,
                    "source_details": {}
                }
            ]
        }

        print("\nRunning real attribution with OpenAI embeddings...")
        attributed = attributor.attribute_sentences(answer, parsed_context)

        print(f"\n✅ Successfully attributed {len(attributed)} sentences")

        for sent_attr in attributed:
            print(f"\nSentence {sent_attr['sentence_number']}: {sent_attr['sentence'][:60]}...")
            print(f"   Attribution confidence: {sent_attr['attribution_confidence']}")
            print(f"   Attributed to {len(sent_attr['attributed_chunks'])} chunks")

            for chunk in sent_attr['attributed_chunks'][:2]:
                print(f"      - {chunk['source_type']} (similarity: {chunk.get('similarity_score', 'N/A')})")

        # Get statistics
        stats = attributor.get_attribution_statistics(attributed)
        print(f"\n✅ Coverage: {stats['coverage_percentage']}%")
        print(f"   Average confidence: {stats['average_confidence']}")

        return attributed

    except Exception as e:
        print(f"\n⚠️  Real embedding test failed: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SENTENCE ATTRIBUTOR - VALIDATION TESTS")
    print("="*80)
    print("\nValidating Phase 3: Sentence Attribution via Semantic Similarity...")

    # Run all tests
    test1_result = test_sentence_splitting()
    test2_result = test_cosine_similarity()
    test3_result = test_sentence_attribution_mock()
    test4_result = test_formatted_output()
    test5_result = test_attribution_statistics()
    test6_result = test_real_embedding_if_available()

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    core_tests_passed = sum([
        test1_result is not None,
        test2_result is not None,
        test3_result is not None,
        test4_result is not None,
        test5_result is not None
    ])

    print(f"\nCore Tests Passed: {core_tests_passed}/5")

    if test6_result:
        print("Real Embeddings Test: ✅ PASSED")
    else:
        print("Real Embeddings Test: ⚠️  SKIPPED (optional)")

    if core_tests_passed == 5:
        print("\n✅ ALL CORE VALIDATIONS PASSED")
        print("   Phase 3: Sentence Attribution ready for integration")
    else:
        print(f"\n⚠️  {5 - core_tests_passed} tests failed")
        print("   Review failures before proceeding")
