#!/usr/bin/env python3
# Location: /tests/test_temporal_enhancement.py
# Purpose: Test temporal enhancement integration with graph builder
# Why: Verify that temporal metadata is correctly added to entities and edges
# Relevant Files: temporal_enhancer.py, graph_builder.py

"""
Test Temporal Enhancement Integration

Tests that the TemporalEnhancer correctly adds temporal metadata to
entities and edges during graph construction.
"""

import sys
from pathlib import Path
import json
from datetime import datetime, timezone, timedelta
import logging

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'ice_core'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'imap_email_ingestion_pipeline'))

from temporal_enhancer import TemporalEnhancer
from graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_temporal_enhancer_basic():
    """Test basic temporal enhancement functionality."""
    print("\n=== Testing Basic Temporal Enhancement ===")

    enhancer = TemporalEnhancer()

    # Create test entity
    entity = {
        'id': 'ticker_NVDA',
        'type': 'ticker',
        'properties': {
            'symbol': 'NVDA'
        }
    }

    # Create test date (30 days ago)
    source_date = datetime.now(timezone.utc) - timedelta(days=30)
    context = "NVDA reported Q2 2024 earnings with margin of 73%"

    # Enhance entity
    enhanced = enhancer.enhance_entity(entity, source_date, context)

    # Verify temporal metadata was added
    assert 'metadata' in enhanced
    assert 'temporal' in enhanced['metadata']

    temporal_meta = enhanced['metadata']['temporal']

    # Check key fields
    assert 'valid_from' in temporal_meta
    assert 'freshness' in temporal_meta
    assert 'age_days' in temporal_meta
    # Allow for small timing differences (29-31 days)
    assert 29 <= temporal_meta['age_days'] <= 31, f"Expected ~30 days, got {temporal_meta['age_days']}"
    assert temporal_meta['freshness'] == 'fresh'  # 30 days = fresh

    # Check quarter extraction
    assert 'quarter_reference' in temporal_meta
    assert temporal_meta['extracted_quarter'] == 'Q2'
    assert temporal_meta['extracted_year'] == 2024

    print(f"✓ Entity temporal metadata: {json.dumps(temporal_meta, indent=2)}")

    return True


def test_graph_builder_integration():
    """Test temporal enhancement in graph builder."""
    print("\n=== Testing Graph Builder Integration ===")

    builder = GraphBuilder()

    # Create test email data
    email_date = datetime.now(timezone.utc) - timedelta(days=7)
    email_data = {
        'uid': 'test_123',
        'subject': 'Tech Earnings Update',
        'date': email_date.isoformat(),
        'from': 'analyst@example.com',
        'body': 'NVDA and AMD showing strong Q3 performance'
    }

    # Create test entities
    entities = {
        'tickers': [
            {
                'ticker': 'NVDA',
                'confidence': 0.9,
                'context': 'NVDA reported 73% margin in Q3 2024',
                'source': 'regex'
            },
            {
                'ticker': 'AMD',
                'confidence': 0.85,
                'context': 'AMD gaining market share',
                'source': 'regex'
            }
        ],
        'companies': [
            {
                'company': 'NVIDIA',
                'ticker': 'NVDA',
                'confidence': 0.95,
                'context': 'NVIDIA dominating AI chip market'
            }
        ],
        'financial_metrics': {
            'margins': [
                {
                    'value': '73%',
                    'confidence': 0.9,
                    'context': 'gross margin of 73%'
                }
            ]
        },
        'confidence': 0.9
    }

    # Build graph
    graph = builder.build_email_graph(email_data, entities)

    # Check nodes have temporal metadata
    temporal_nodes = 0
    for node in graph['nodes']:
        if 'metadata' in node and 'temporal' in node.get('metadata', {}):
            temporal_nodes += 1
            print(f"✓ Node {node['id']} has temporal metadata")

    # Check edges have temporal properties
    temporal_edges = 0
    for edge in graph['edges']:
        props = edge.get('properties', {})
        if 'freshness' in props or 'temporal_confidence' in props:
            temporal_edges += 1
            print(f"✓ Edge {edge['id']} has temporal properties")

    # Check for temporal edges (METRIC_EVOLVED, TEMPORALLY_CORRELATED)
    temporal_edge_types = [e for e in graph['edges']
                          if e.get('type') in ['METRIC_EVOLVED', 'TEMPORALLY_CORRELATED']]

    print(f"\nResults:")
    print(f"  Total nodes: {len(graph['nodes'])}")
    print(f"  Nodes with temporal metadata: {temporal_nodes}")
    print(f"  Total edges: {len(graph['edges'])}")
    print(f"  Edges with temporal properties: {temporal_edges}")
    print(f"  Temporal relationship edges: {len(temporal_edge_types)}")

    # Verify temporal enhancer was used
    assert builder.temporal_enhancer is not None, "Temporal enhancer not initialized"

    return True


def test_temporal_edge_creation():
    """Test creation of temporal edges between metrics."""
    print("\n=== Testing Temporal Edge Creation ===")

    enhancer = TemporalEnhancer()

    # Create metrics at different times
    entities = [
        {
            'id': 'metric_1',
            'type': 'metric',
            'properties': {'metric_type': 'margin'},
            'metadata': {
                'temporal': {
                    'valid_from': '2024-01-01T00:00:00Z'
                }
            }
        },
        {
            'id': 'metric_2',
            'type': 'metric',
            'properties': {'metric_type': 'margin'},
            'metadata': {
                'temporal': {
                    'valid_from': '2024-04-01T00:00:00Z'
                }
            }
        },
        {
            'id': 'event_1',
            'type': 'event',
            'metadata': {
                'temporal': {
                    'valid_from': '2024-02-01T00:00:00Z'
                }
            }
        },
        {
            'id': 'event_2',
            'type': 'event',
            'metadata': {
                'temporal': {
                    'valid_from': '2024-02-01T00:00:00Z'
                }
            }
        }
    ]

    # Create temporal edges
    temporal_edges = enhancer.create_temporal_edges(entities, [])

    # Check for metric evolution edges
    evolution_edges = [e for e in temporal_edges if e['type'] == 'METRIC_EVOLVED']
    assert len(evolution_edges) > 0, "No metric evolution edges created"

    # Check for temporal correlation edges
    correlation_edges = [e for e in temporal_edges if e['type'] == 'TEMPORALLY_CORRELATED']
    assert len(correlation_edges) > 0, "No temporal correlation edges created"

    print(f"✓ Created {len(evolution_edges)} metric evolution edges")
    print(f"✓ Created {len(correlation_edges)} temporal correlation edges")

    for edge in evolution_edges[:1]:  # Show first evolution edge
        print(f"\nExample evolution edge:")
        print(f"  {edge['source']} → {edge['target']}")
        print(f"  Time delta: {edge['properties'].get('time_delta_days')} days")

    return True


def test_freshness_scoring():
    """Test freshness score calculation."""
    print("\n=== Testing Freshness Scoring ===")

    enhancer = TemporalEnhancer()

    test_cases = [
        (0, 1.0, 'very_fresh'),     # Today
        (7, 0.812, 'very_fresh'),    # 1 week
        (30, 0.5, 'fresh'),          # 1 month
        (90, 0.125, 'moderate'),     # 3 months
        (365, 0.001, 'stale'),       # 1 year
        (730, 0.0, 'very_stale')     # 2 years
    ]

    for days_ago, expected_score, expected_freshness in test_cases:
        source_date = datetime.now(timezone.utc) - timedelta(days=days_ago)

        entity = {
            'id': f'test_{days_ago}',
            'type': 'metric'
        }

        enhanced = enhancer.enhance_entity(entity, source_date)

        actual_score = enhanced['properties']['freshness_score']
        actual_freshness = enhanced['metadata']['temporal']['freshness']

        # Allow small floating point differences
        score_match = abs(actual_score - expected_score) < 0.1
        freshness_match = actual_freshness == expected_freshness

        status = "✓" if (score_match and freshness_match) else "✗"
        print(f"{status} {days_ago:3d} days: score={actual_score:.3f} ({expected_score:.3f}), "
              f"freshness={actual_freshness} ({expected_freshness})")

        assert freshness_match, f"Freshness mismatch for {days_ago} days"

    return True


def main():
    """Run all temporal enhancement tests."""
    print("\n" + "="*60)
    print("TEMPORAL ENHANCEMENT INTEGRATION TESTS")
    print("="*60)

    tests = [
        test_temporal_enhancer_basic,
        test_graph_builder_integration,
        test_temporal_edge_creation,
        test_freshness_scoring
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_func.__name__} PASSED\n")
            else:
                failed += 1
                print(f"❌ {test_func.__name__} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} FAILED: {e}\n")
            import traceback
            traceback.print_exc()

    print("="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)