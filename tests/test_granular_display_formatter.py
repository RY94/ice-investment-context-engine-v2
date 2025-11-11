# Location: tests/test_granular_display_formatter.py
# Purpose: Validate GranularDisplayFormatter implementation
# Why: Ensure comprehensive display formatting works correctly
# Relevant Files: src/ice_core/granular_display_formatter.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ice_core.granular_display_formatter import GranularDisplayFormatter


def get_sample_data():
    """Get sample attribution data for testing"""
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
                    "relevance_rank": 1,
                    "source_details": {
                        "subject": "Tencent Q2 2025 Earnings",
                        "sender": "Jia Jun (AGT Partners)"
                    }
                }
            ],
            "attribution_confidence": 0.87,
            "has_attribution": True
        },
        {
            "sentence": "This represents a 2% increase from Q1 2025.",
            "sentence_number": 2,
            "attributed_chunks": [
                {
                    "chunk_id": 2,
                    "source_type": "api",
                    "confidence": 0.85,
                    "similarity_score": 0.82,
                    "date": "2025-08-14",
                    "relevance_rank": 2,
                    "source_details": {
                        "api": "fmp",
                        "symbol": "TENCENT"
                    }
                }
            ],
            "attribution_confidence": 0.82,
            "has_attribution": True
        }
    ]

    parsed_context = {
        "chunks": [
            {
                "chunk_id": 1,
                "source_type": "email",
                "confidence": 0.90,
                "date": "2025-08-15",
                "relevance_rank": 1,
                "source_details": {
                    "subject": "Tencent Q2 2025 Earnings",
                    "sender": "Jia Jun (AGT Partners)"
                }
            },
            {
                "chunk_id": 2,
                "source_type": "api",
                "confidence": 0.85,
                "date": "2025-08-14",
                "relevance_rank": 2,
                "source_details": {
                    "api": "fmp",
                    "symbol": "TENCENT"
                }
            }
        ]
    }

    attributed_paths = [
        {
            "path_id": 0,
            "path_length": 2,
            "path_description": "NVIDIA → TSMC → Taiwan",
            "overall_confidence": 0.85,
            "hops": [
                {
                    "hop_number": 1,
                    "relationship": "NVIDIA --DEPENDS_ON--> TSMC",
                    "sources": ["email"],
                    "confidence": 0.90,
                    "num_supporting_chunks": 2,
                    "date": "2025-08-15"
                },
                {
                    "hop_number": 2,
                    "relationship": "TSMC --LOCATED_IN--> Taiwan",
                    "sources": ["api"],
                    "confidence": 0.85,
                    "num_supporting_chunks": 1,
                    "date": "2025-08-12"
                }
            ]
        }
    ]

    return attributed_sentences, parsed_context, attributed_paths


def test_answer_section():
    """Test answer section formatting"""
    print("\n" + "="*80)
    print("TEST 1: Answer Section Formatting")
    print("="*80)

    formatter = GranularDisplayFormatter()
    attributed_sentences, _, _ = get_sample_data()

    answer_section = formatter._format_answer_section(attributed_sentences)

    print("\nGenerated Answer Section:")
    print(answer_section)

    # Validate
    assert "✅ ANSWER" in answer_section
    assert "[1]" in answer_section
    assert "[2]" in answer_section
    assert "📧" in answer_section  # Email icon
    assert "📊" in answer_section  # API icon
    assert "0.87" in answer_section  # Similarity score
    assert "2025-08-15" in answer_section  # Date

    print("\n✅ Answer section formatted correctly")
    return answer_section


def test_sources_section():
    """Test sources section formatting"""
    print("\n" + "="*80)
    print("TEST 2: Sources Section Formatting")
    print("="*80)

    formatter = GranularDisplayFormatter()
    attributed_sentences, parsed_context, _ = get_sample_data()
    chunks = parsed_context['chunks']

    sources_section = formatter._format_sources_section(chunks, attributed_sentences)

    print("\nGenerated Sources Section:")
    print(sources_section)

    # Validate
    assert "📚 SOURCES" in sources_section
    assert "100% coverage" in sources_section  # Both sentences attributed
    assert "#1" in sources_section
    assert "Email: Tencent Q2 2025 Earnings" in sources_section
    assert "Confidence: 0.9" in sources_section
    assert "Sender: Jia Jun" in sources_section

    print("\n✅ Sources section formatted correctly")
    return sources_section


def test_paths_section():
    """Test reasoning paths section formatting"""
    print("\n" + "="*80)
    print("TEST 3: Reasoning Paths Section Formatting")
    print("="*80)

    formatter = GranularDisplayFormatter()
    _, _, attributed_paths = get_sample_data()

    paths_section = formatter._format_paths_section(attributed_paths)

    print("\nGenerated Paths Section:")
    print(paths_section)

    # Validate
    assert "🔗 REASONING PATHS" in paths_section
    assert "NVIDIA → TSMC → Taiwan" in paths_section
    assert "Hop 1:" in paths_section
    assert "Hop 2:" in paths_section
    assert "DEPENDS_ON" in paths_section
    assert "LOCATED_IN" in paths_section

    print("\n✅ Paths section formatted correctly")
    return paths_section


def test_statistics_section():
    """Test statistics section formatting"""
    print("\n" + "="*80)
    print("TEST 4: Statistics Section Formatting")
    print("="*80)

    formatter = GranularDisplayFormatter()
    attributed_sentences, _, _ = get_sample_data()

    stats_section = formatter._format_statistics_section(attributed_sentences)

    print("\nGenerated Statistics Section:")
    print(stats_section)

    # Validate
    assert "📊 ATTRIBUTION STATISTICS" in stats_section
    assert "Coverage: 100%" in stats_section
    assert "Average Confidence:" in stats_section
    assert "Sources:" in stats_section

    print("\n✅ Statistics section formatted correctly")
    return stats_section


def test_full_granular_response():
    """Test complete granular response formatting"""
    print("\n" + "="*80)
    print("TEST 5: Full Granular Response")
    print("="*80)

    formatter = GranularDisplayFormatter()
    attributed_sentences, parsed_context, attributed_paths = get_sample_data()

    answer = "Tencent's Q2 2025 operating margin was 34%. This represents a 2% increase from Q1 2025."

    full_response = formatter.format_granular_response(
        answer=answer,
        attributed_sentences=attributed_sentences,
        parsed_context=parsed_context,
        attributed_paths=attributed_paths,
        show_answer_sentences=True,
        show_sources=True,
        show_paths=True,
        show_statistics=True
    )

    print("\nGenerated Full Response:")
    print(full_response)

    # Validate all sections present
    assert "✅ ANSWER" in full_response
    assert "📚 SOURCES" in full_response
    assert "🔗 REASONING PATHS" in full_response
    assert "📊 ATTRIBUTION STATISTICS" in full_response

    print("\n✅ Full granular response formatted correctly")
    return full_response


def test_compact_response():
    """Test compact response formatting"""
    print("\n" + "="*80)
    print("TEST 6: Compact Response")
    print("="*80)

    formatter = GranularDisplayFormatter()
    attributed_sentences, _, _ = get_sample_data()

    answer = "Tencent's Q2 2025 operating margin was 34%. This represents a 2% increase from Q1 2025."

    compact_response = formatter.format_compact_response(
        answer=answer,
        attributed_sentences=attributed_sentences,
        show_sources=True
    )

    print("\nGenerated Compact Response:")
    print(compact_response)

    # Validate
    assert "**Answer:**" in compact_response
    assert "**Top Sources:**" in compact_response
    assert "[1]" in compact_response
    assert "[2]" in compact_response
    assert "📧" in compact_response
    assert "📊" in compact_response

    print("\n✅ Compact response formatted correctly")
    return compact_response


def test_no_paths():
    """Test formatting when no reasoning paths available (1-hop query)"""
    print("\n" + "="*80)
    print("TEST 7: Response Without Reasoning Paths")
    print("="*80)

    formatter = GranularDisplayFormatter()
    attributed_sentences, parsed_context, _ = get_sample_data()

    answer = "Simple answer."

    response_no_paths = formatter.format_granular_response(
        answer=answer,
        attributed_sentences=attributed_sentences,
        parsed_context=parsed_context,
        attributed_paths=None,  # No paths
        show_answer_sentences=True,
        show_sources=True,
        show_paths=True,
        show_statistics=True
    )

    print("\nGenerated Response (No Paths):")
    print(response_no_paths)

    # Validate paths section NOT present
    assert "✅ ANSWER" in response_no_paths
    assert "📚 SOURCES" in response_no_paths
    assert "🔗 REASONING PATHS" not in response_no_paths  # Should not appear
    assert "📊 ATTRIBUTION STATISTICS" in response_no_paths

    print("\n✅ Response without paths formatted correctly")
    return response_no_paths


if __name__ == "__main__":
    print("\n" + "="*80)
    print("GRANULAR DISPLAY FORMATTER - VALIDATION TESTS")
    print("="*80)
    print("\nValidating Phase 5: Enhanced Granular Display...")

    # Run all tests
    test1_result = test_answer_section()
    test2_result = test_sources_section()
    test3_result = test_paths_section()
    test4_result = test_statistics_section()
    test5_result = test_full_granular_response()
    test6_result = test_compact_response()
    test7_result = test_no_paths()

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    tests_passed = sum([
        test1_result is not None,
        test2_result is not None,
        test3_result is not None,
        test4_result is not None,
        test5_result is not None,
        test6_result is not None,
        test7_result is not None
    ])

    print(f"\nTests Passed: {tests_passed}/7")

    if tests_passed == 7:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("   Phase 5: Enhanced Granular Display ready for integration")
    else:
        print(f"\n⚠️  {7 - tests_passed} tests failed")
        print("   Review failures before proceeding")
