# Location: tests/test_signal_store_complete_schema.py
# Purpose: Unit tests for Phase 4 Signal Store schema (price_targets, entities, relationships)
# Why: Validate CRUD operations for all remaining tables in dual-layer architecture
# Relevant Files: signal_store.py

import pytest
import os
import tempfile
from pathlib import Path

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from updated_architectures.implementation.signal_store import SignalStore


# ==================== FIXTURES ====================

@pytest.fixture
def temp_signal_store():
    """Create temporary Signal Store for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    store = SignalStore(db_path=db_path)
    yield store

    store.close()
    if os.path.exists(db_path):
        os.remove(db_path)


# ==================== PRICE TARGETS TABLE TESTS ====================

def test_insert_price_target(temp_signal_store):
    """Test inserting a price target"""
    row_id = temp_signal_store.insert_price_target(
        ticker='NVDA',
        target_price=500.0,
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='email_123',
        analyst='John Doe',
        firm='Goldman Sachs',
        confidence=0.92
    )
    assert row_id > 0


def test_get_latest_price_target(temp_signal_store):
    """Test retrieving the latest price target"""
    # Insert two price targets
    temp_signal_store.insert_price_target(
        ticker='NVDA',
        target_price=450.0,
        timestamp='2024-03-10T10:00:00Z',
        source_document_id='email_123',
        firm='Morgan Stanley'
    )
    temp_signal_store.insert_price_target(
        ticker='NVDA',
        target_price=500.0,
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='email_456',
        firm='Goldman Sachs'
    )

    # Get latest (should be the second one)
    latest = temp_signal_store.get_latest_price_target('NVDA')
    assert latest is not None
    assert latest['target_price'] == 500.0
    assert latest['firm'] == 'Goldman Sachs'
    assert latest['timestamp'] == '2024-03-15T10:30:00Z'


def test_get_price_target_history(temp_signal_store):
    """Test retrieving price target history"""
    # Insert three price targets
    targets = [
        (400.0, '2024-03-01T10:00:00Z'),
        (450.0, '2024-03-10T10:00:00Z'),
        (500.0, '2024-03-15T10:00:00Z')
    ]

    for price, timestamp in targets:
        temp_signal_store.insert_price_target(
            ticker='NVDA',
            target_price=price,
            timestamp=timestamp,
            source_document_id='email_test'
        )

    # Get history (should be in descending order)
    history = temp_signal_store.get_price_target_history('NVDA', limit=10)
    assert len(history) == 3
    assert history[0]['target_price'] == 500.0  # Most recent first
    assert history[1]['target_price'] == 450.0
    assert history[2]['target_price'] == 400.0


def test_count_price_targets(temp_signal_store):
    """Test counting price targets"""
    assert temp_signal_store.count_price_targets() == 0

    temp_signal_store.insert_price_target(
        ticker='NVDA',
        target_price=500.0,
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='email_123'
    )
    assert temp_signal_store.count_price_targets() == 1

    temp_signal_store.insert_price_target(
        ticker='AAPL',
        target_price=200.0,
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='email_456'
    )
    assert temp_signal_store.count_price_targets() == 2


# ==================== ENTITIES TABLE TESTS ====================

def test_insert_entity(temp_signal_store):
    """Test inserting an entity"""
    row_id = temp_signal_store.insert_entity(
        entity_id='TICKER:NVDA',
        entity_type='TICKER',
        entity_name='NVDA',
        source_document_id='email_123',
        confidence=0.98
    )
    assert row_id > 0


def test_insert_entities_batch(temp_signal_store):
    """Test batch inserting entities"""
    entities = [
        {
            'entity_id': 'TICKER:NVDA',
            'entity_type': 'TICKER',
            'entity_name': 'NVDA',
            'source_document_id': 'email_123',
            'confidence': 0.98
        },
        {
            'entity_id': 'TICKER:TSMC',
            'entity_type': 'TICKER',
            'entity_name': 'TSMC',
            'source_document_id': 'email_123',
            'confidence': 0.96
        },
        {
            'entity_id': 'PERSON:Jensen_Huang',
            'entity_type': 'PERSON',
            'entity_name': 'Jensen Huang',
            'source_document_id': 'email_456',
            'confidence': 0.95
        }
    ]

    count = temp_signal_store.insert_entities_batch(entities)
    assert count == 3
    assert temp_signal_store.count_entities() == 3


def test_get_entity(temp_signal_store):
    """Test retrieving an entity by ID"""
    temp_signal_store.insert_entity(
        entity_id='TICKER:NVDA',
        entity_type='TICKER',
        entity_name='NVDA',
        source_document_id='email_123',
        confidence=0.98
    )

    entity = temp_signal_store.get_entity('TICKER:NVDA')
    assert entity is not None
    assert entity['entity_type'] == 'TICKER'
    assert entity['entity_name'] == 'NVDA'
    assert entity['confidence'] == 0.98


def test_get_entities_by_type(temp_signal_store):
    """Test retrieving entities by type"""
    # Insert entities of different types
    entities = [
        {'entity_id': 'TICKER:NVDA', 'entity_type': 'TICKER', 'entity_name': 'NVDA', 'source_document_id': 'email_123'},
        {'entity_id': 'TICKER:TSMC', 'entity_type': 'TICKER', 'entity_name': 'TSMC', 'source_document_id': 'email_123'},
        {'entity_id': 'PERSON:Jensen_Huang', 'entity_type': 'PERSON', 'entity_name': 'Jensen Huang', 'source_document_id': 'email_456'},
        {'entity_id': 'COMPANY:NVIDIA', 'entity_type': 'COMPANY', 'entity_name': 'NVIDIA', 'source_document_id': 'email_789'}
    ]
    temp_signal_store.insert_entities_batch(entities)

    # Get all TICKER entities
    tickers = temp_signal_store.get_entities_by_type('TICKER', limit=10)
    assert len(tickers) == 2
    ticker_ids = [e['entity_id'] for e in tickers]
    assert 'TICKER:NVDA' in ticker_ids
    assert 'TICKER:TSMC' in ticker_ids

    # Get all PERSON entities
    persons = temp_signal_store.get_entities_by_type('PERSON', limit=10)
    assert len(persons) == 1
    assert persons[0]['entity_id'] == 'PERSON:Jensen_Huang'


def test_count_entities(temp_signal_store):
    """Test counting entities"""
    assert temp_signal_store.count_entities() == 0

    temp_signal_store.insert_entity(
        entity_id='TICKER:NVDA',
        entity_type='TICKER',
        entity_name='NVDA',
        source_document_id='email_123'
    )
    assert temp_signal_store.count_entities() == 1

    temp_signal_store.insert_entity(
        entity_id='TICKER:TSMC',
        entity_type='TICKER',
        entity_name='TSMC',
        source_document_id='email_456'
    )
    assert temp_signal_store.count_entities() == 2


# ==================== RELATIONSHIPS TABLE TESTS ====================

def test_insert_relationship(temp_signal_store):
    """Test inserting a relationship"""
    row_id = temp_signal_store.insert_relationship(
        source_entity='COMPANY:TSMC',
        target_entity='COMPANY:NVIDIA',
        relationship_type='SUPPLIES_TO',
        source_document_id='email_123',
        confidence=0.92
    )
    assert row_id > 0


def test_insert_relationships_batch(temp_signal_store):
    """Test batch inserting relationships"""
    relationships = [
        {
            'source_entity': 'COMPANY:TSMC',
            'target_entity': 'COMPANY:NVIDIA',
            'relationship_type': 'SUPPLIES_TO',
            'source_document_id': 'email_123',
            'confidence': 0.92
        },
        {
            'source_entity': 'PERSON:Jensen_Huang',
            'target_entity': 'COMPANY:NVIDIA',
            'relationship_type': 'CEO_OF',
            'source_document_id': 'email_456',
            'confidence': 0.98
        },
        {
            'source_entity': 'COMPANY:NVIDIA',
            'target_entity': 'TECH:AI',
            'relationship_type': 'OPERATES_IN',
            'source_document_id': 'email_789',
            'confidence': 0.95
        }
    ]

    count = temp_signal_store.insert_relationships_batch(relationships)
    assert count == 3
    assert temp_signal_store.count_relationships() == 3


def test_get_relationships_by_source(temp_signal_store):
    """Test retrieving relationships filtered by source entity"""
    relationships = [
        {
            'source_entity': 'COMPANY:NVIDIA',
            'target_entity': 'TECH:AI',
            'relationship_type': 'OPERATES_IN',
            'source_document_id': 'email_123'
        },
        {
            'source_entity': 'COMPANY:NVIDIA',
            'target_entity': 'TECH:GAMING',
            'relationship_type': 'OPERATES_IN',
            'source_document_id': 'email_456'
        },
        {
            'source_entity': 'COMPANY:TSMC',
            'target_entity': 'COMPANY:NVIDIA',
            'relationship_type': 'SUPPLIES_TO',
            'source_document_id': 'email_789'
        }
    ]
    temp_signal_store.insert_relationships_batch(relationships)

    # Get relationships where NVIDIA is the source
    nvidia_rels = temp_signal_store.get_relationships(source_entity='COMPANY:NVIDIA')
    assert len(nvidia_rels) == 2
    targets = [r['target_entity'] for r in nvidia_rels]
    assert 'TECH:AI' in targets
    assert 'TECH:GAMING' in targets


def test_get_relationships_by_target(temp_signal_store):
    """Test retrieving relationships filtered by target entity"""
    relationships = [
        {
            'source_entity': 'COMPANY:TSMC',
            'target_entity': 'COMPANY:NVIDIA',
            'relationship_type': 'SUPPLIES_TO',
            'source_document_id': 'email_123'
        },
        {
            'source_entity': 'PERSON:Jensen_Huang',
            'target_entity': 'COMPANY:NVIDIA',
            'relationship_type': 'CEO_OF',
            'source_document_id': 'email_456'
        }
    ]
    temp_signal_store.insert_relationships_batch(relationships)

    # Get relationships where NVIDIA is the target
    nvidia_incoming = temp_signal_store.get_relationships(target_entity='COMPANY:NVIDIA')
    assert len(nvidia_incoming) == 2


def test_get_relationships_by_type(temp_signal_store):
    """Test retrieving relationships filtered by type"""
    relationships = [
        {
            'source_entity': 'COMPANY:TSMC',
            'target_entity': 'COMPANY:NVIDIA',
            'relationship_type': 'SUPPLIES_TO',
            'source_document_id': 'email_123'
        },
        {
            'source_entity': 'COMPANY:SAMSUNG',
            'target_entity': 'COMPANY:QUALCOMM',
            'relationship_type': 'SUPPLIES_TO',
            'source_document_id': 'email_456'
        },
        {
            'source_entity': 'PERSON:Jensen_Huang',
            'target_entity': 'COMPANY:NVIDIA',
            'relationship_type': 'CEO_OF',
            'source_document_id': 'email_789'
        }
    ]
    temp_signal_store.insert_relationships_batch(relationships)

    # Get all SUPPLIES_TO relationships
    supply_rels = temp_signal_store.get_relationships(relationship_type='SUPPLIES_TO')
    assert len(supply_rels) == 2


def test_count_relationships(temp_signal_store):
    """Test counting relationships"""
    assert temp_signal_store.count_relationships() == 0

    temp_signal_store.insert_relationship(
        source_entity='COMPANY:TSMC',
        target_entity='COMPANY:NVIDIA',
        relationship_type='SUPPLIES_TO',
        source_document_id='email_123'
    )
    assert temp_signal_store.count_relationships() == 1

    temp_signal_store.insert_relationship(
        source_entity='PERSON:Jensen_Huang',
        target_entity='COMPANY:NVIDIA',
        relationship_type='CEO_OF',
        source_document_id='email_456'
    )
    assert temp_signal_store.count_relationships() == 2


# ==================== INTEGRATION TESTS ====================

def test_complete_schema_integration(temp_signal_store):
    """Test all 5 tables working together"""
    # 1. Insert ratings
    temp_signal_store.insert_rating(
        ticker='NVDA',
        rating='BUY',
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='email_123',
        firm='Goldman Sachs',
        confidence=0.87
    )

    # 2. Insert metrics
    temp_signal_store.insert_metric(
        ticker='NVDA',
        metric_type='Operating Margin',
        metric_value='62.3%',
        source_document_id='email_123',
        period='Q2 2024',
        confidence=0.95
    )

    # 3. Insert price target
    temp_signal_store.insert_price_target(
        ticker='NVDA',
        target_price=500.0,
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='email_123',
        firm='Goldman Sachs',
        confidence=0.92
    )

    # 4. Insert entities
    entities = [
        {'entity_id': 'TICKER:NVDA', 'entity_type': 'TICKER', 'entity_name': 'NVDA', 'source_document_id': 'email_123'},
        {'entity_id': 'COMPANY:NVIDIA', 'entity_type': 'COMPANY', 'entity_name': 'NVIDIA', 'source_document_id': 'email_123'},
        {'entity_id': 'COMPANY:TSMC', 'entity_type': 'COMPANY', 'entity_name': 'TSMC', 'source_document_id': 'email_456'}
    ]
    temp_signal_store.insert_entities_batch(entities)

    # 5. Insert relationships
    relationships = [
        {
            'source_entity': 'COMPANY:TSMC',
            'target_entity': 'COMPANY:NVIDIA',
            'relationship_type': 'SUPPLIES_TO',
            'source_document_id': 'email_456'
        }
    ]
    temp_signal_store.insert_relationships_batch(relationships)

    # Verify all tables have data
    assert temp_signal_store.count_ratings() == 1
    assert temp_signal_store.count_metrics() == 1
    assert temp_signal_store.count_price_targets() == 1
    assert temp_signal_store.count_entities() == 3
    assert temp_signal_store.count_relationships() == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
