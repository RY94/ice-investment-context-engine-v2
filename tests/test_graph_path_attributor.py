# Location: tests/test_graph_path_attributor.py
# Purpose: Validate GraphPathAttributor implementation
# Why: Ensure per-hop source attribution works correctly
# Relevant Files: src/ice_core/graph_path_attributor.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ice_core.graph_path_attributor import GraphPathAttributor


def test_attribute_simple_path():
    """Test attribution for a simple 2-hop path"""
    print("\n" + "="*80)
    print("TEST 1: Attribute Simple 2-Hop Path")
    print("="*80)

    # Sample causal path
    causal_paths = [
        [
            {"entity1": "NVIDIA", "relation": "DEPENDS_ON", "entity2": "TSMC"},
            {"entity1": "TSMC", "relation": "LOCATED_IN", "entity2": "Taiwan"}
        ]
    ]

    # Sample parsed context (from context parser)
    parsed_context = {
        "entities": [
            {"id": 1, "entity": "NVIDIA"},
            {"id": 2, "entity": "TSMC"},
            {"id": 3, "entity": "Taiwan"}
        ],
        "relationships": [],
        "chunks": [
            {
                "chunk_id": 1,
                "content": "NVIDIA relies on TSMC for advanced chip manufacturing...",
                "source_type": "email",
                "confidence": 0.90,
                "date": "2025-08-15",
                "relevance_rank": 1
            },
            {
                "chunk_id": 2,
                "content": "TSMC's Taiwan facilities produce 90% of advanced chips...",
                "source_type": "api",
                "confidence": 0.85,
                "date": "2025-08-12",
                "relevance_rank": 2
            }
        ],
        "summary": {}
    }

    attributor = GraphPathAttributor()
    attributed_paths = attributor.attribute_paths(causal_paths, parsed_context)

    print(f"\n✅ Attributed {len(attributed_paths)} path(s)")

    # Validate path 0
    path0 = attributed_paths[0]
    print(f"\nPath 0:")
    print(f"   Description: {path0['path_description']}")
    print(f"   Length: {path0['path_length']}")
    print(f"   Overall confidence: {path0['overall_confidence']}")

    assert path0['path_length'] == 2, f"Expected 2 hops, got {path0['path_length']}"
    assert len(path0['hops']) == 2, f"Expected 2 attributed hops"

    # Validate hop 1
    hop1 = path0['hops'][0]
    print(f"\n   Hop 1: {hop1['relationship']}")
    print(f"      Sources: {hop1['sources']}")
    print(f"      Confidence: {hop1['confidence']}")
    print(f"      Date: {hop1['date']}")
    print(f"      Supporting chunks: {hop1['num_supporting_chunks']}")

    assert hop1['entity1'] == 'NVIDIA'
    assert hop1['entity2'] == 'TSMC'
    assert hop1['num_supporting_chunks'] == 1  # Only chunk 1 mentions both

    # Validate hop 2
    hop2 = path0['hops'][1]
    print(f"\n   Hop 2: {hop2['relationship']}")
    print(f"      Sources: {hop2['sources']}")
    print(f"      Confidence: {hop2['confidence']}")
    print(f"      Date: {hop2['date']}")
    print(f"      Supporting chunks: {hop2['num_supporting_chunks']}")

    assert hop2['entity1'] == 'TSMC'
    assert hop2['entity2'] == 'Taiwan'

    # Test formatted output
    formatted = attributor.format_attributed_path(path0)
    print(f"\n✅ Formatted output:")
    print(formatted)

    return attributed_paths


def test_attribute_multi_path():
    """Test attribution for multiple paths"""
    print("\n" + "="*80)
    print("TEST 2: Attribute Multiple Paths")
    print("="*80)

    # Two alternative paths
    causal_paths = [
        [{"entity1": "A", "relation": "REL1", "entity2": "B"}],  # Path 1: A → B
        [{"entity1": "A", "relation": "REL2", "entity2": "C"}]   # Path 2: A → C
    ]

    parsed_context = {
        "entities": [],
        "relationships": [],
        "chunks": [
            {
                "chunk_id": 1,
                "content": "A relates to B via relationship 1",
                "source_type": "email",
                "confidence": 0.92,
                "date": "2025-08-15",
                "relevance_rank": 1
            },
            {
                "chunk_id": 2,
                "content": "A connects to C through relationship 2",
                "source_type": "api",
                "confidence": 0.88,
                "date": "2025-08-14",
                "relevance_rank": 2
            }
        ],
        "summary": {}
    }

    attributor = GraphPathAttributor()
    attributed_paths = attributor.attribute_paths(causal_paths, parsed_context)

    print(f"\n✅ Attributed {len(attributed_paths)} paths")
    assert len(attributed_paths) == 2

    for i, path in enumerate(attributed_paths):
        print(f"\nPath {i}: {path['path_description']}")
        print(f"   Confidence: {path['overall_confidence']}")
        print(f"   Hops: {path['path_length']}")

    return attributed_paths


def test_no_supporting_chunks():
    """Test hop attribution when no chunks support the relationship"""
    print("\n" + "="*80)
    print("TEST 3: Attribution with No Supporting Chunks (Inferred Relationship)")
    print("="*80)

    causal_paths = [
        [{"entity1": "X", "relation": "INFERRED", "entity2": "Y"}]
    ]

    parsed_context = {
        "entities": [],
        "relationships": [],
        "chunks": [
            {
                "chunk_id": 1,
                "content": "This chunk discusses completely different entities like Apple and Microsoft",
                "source_type": "unknown",
                "confidence": 0.50,
                "relevance_rank": 1
            }
        ],
        "summary": {}
    }

    attributor = GraphPathAttributor()
    attributed_paths = attributor.attribute_paths(causal_paths, parsed_context)

    path0 = attributed_paths[0]
    hop0 = path0['hops'][0]

    print(f"\nInferred hop: {hop0['relationship']}")
    print(f"   Supporting chunks: {hop0['num_supporting_chunks']}")
    print(f"   Confidence: {hop0['confidence']}")

    # Should have low confidence (0.40) for inferred relationship
    assert hop0['num_supporting_chunks'] == 0
    assert hop0['confidence'] == 0.40  # Default for inferred

    print("\n✅ Correctly assigned low confidence for inferred relationship")

    return attributed_paths


def test_redundancy_boost():
    """Test that multiple supporting chunks increase confidence"""
    print("\n" + "="*80)
    print("TEST 4: Confidence Boost from Redundant Sources")
    print("="*80)

    causal_paths = [
        [{"entity1": "A", "relation": "REL", "entity2": "B"}]
    ]

    # Multiple chunks support the same relationship
    parsed_context = {
        "entities": [],
        "relationships": [],
        "chunks": [
            {
                "chunk_id": 1,
                "content": "A and B are related according to source 1",
                "source_type": "email",
                "confidence": 0.80,
                "relevance_rank": 1
            },
            {
                "chunk_id": 2,
                "content": "A and B relationship confirmed by source 2",
                "source_type": "api",
                "confidence": 0.85,
                "relevance_rank": 2
            },
            {
                "chunk_id": 3,
                "content": "A and B connection verified by source 3",
                "source_type": "email",
                "confidence": 0.82,
                "relevance_rank": 3
            }
        ],
        "summary": {}
    }

    attributor = GraphPathAttributor()
    attributed_paths = attributor.attribute_paths(causal_paths, parsed_context)

    hop0 = attributed_paths[0]['hops'][0]

    print(f"\nHop with redundant sources:")
    print(f"   Supporting chunks: {hop0['num_supporting_chunks']}")
    print(f"   Confidence: {hop0['confidence']}")
    print(f"   Sources: {hop0['sources']}")

    # Should have 3 supporting chunks
    assert hop0['num_supporting_chunks'] == 3

    # Confidence should be boosted
    # Average: (0.80 + 0.85 + 0.82) / 3 = 0.823
    # Redundancy boost: +0.10 (2 additional chunks * 0.05)
    # Final: 0.823 + 0.10 = 0.923 → 0.92
    assert hop0['confidence'] >= 0.90  # Should be boosted above average

    print(f"\n✅ Redundancy boost applied: {hop0['confidence']}")

    return attributed_paths


if __name__ == "__main__":
    print("\n" + "="*80)
    print("GRAPH PATH ATTRIBUTOR - VALIDATION TESTS")
    print("="*80)
    print("\nValidating Phase 4: Graph Path Attribution...")

    # Run all tests
    test1_result = test_attribute_simple_path()
    test2_result = test_attribute_multi_path()
    test3_result = test_no_supporting_chunks()
    test4_result = test_redundancy_boost()

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    tests_passed = sum([
        test1_result is not None,
        test2_result is not None,
        test3_result is not None,
        test4_result is not None
    ])

    print(f"\nTests Passed: {tests_passed}/4")

    if tests_passed == 4:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("   Phase 4: Graph Path Attribution ready for integration")
    else:
        print(f"\n⚠️  {4 - tests_passed} tests failed")
        print("   Review failures before proceeding")
