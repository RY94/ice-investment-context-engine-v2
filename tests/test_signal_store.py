# Location: tests/test_signal_store.py
# Purpose: Unit tests for Signal Store (SQLite-based structured storage)
# Why: Validate CRUD operations, query performance, and data integrity for dual-layer architecture
# Relevant Files: signal_store.py, test_dual_layer_integration.py

import pytest
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from updated_architectures.implementation.signal_store import SignalStore


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    # Use temporary directory for test database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def signal_store(temp_db):
    """Create Signal Store instance for testing"""
    store = SignalStore(db_path=temp_db)
    yield store
    store.close()


# ==================== TABLE CREATION TESTS ====================

def test_signal_store_initialization(temp_db):
    """Test Signal Store initializes correctly"""
    store = SignalStore(db_path=temp_db)

    # Verify database file created
    assert os.path.exists(temp_db)

    # Verify connection works
    assert store.conn is not None

    store.close()


def test_ratings_table_created(signal_store):
    """Test ratings table is created with proper schema"""
    cursor = signal_store.conn.cursor()

    # Check table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ratings'")
    assert cursor.fetchone() is not None

    # Check indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ratings'")
    indexes = [row[0] for row in cursor.fetchall()]

    assert 'idx_ratings_ticker' in indexes
    assert 'idx_ratings_timestamp' in indexes
    assert 'idx_ratings_ticker_timestamp' in indexes


# ==================== RATINGS CRUD TESTS ====================

def test_insert_rating(signal_store):
    """Test inserting a single rating"""
    row_id = signal_store.insert_rating(
        ticker='NVDA',
        rating='BUY',
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='email_12345',
        analyst='John Doe',
        firm='Goldman Sachs',
        confidence=0.87
    )

    assert row_id > 0


def test_insert_rating_minimal(signal_store):
    """Test inserting rating with minimal fields (only required)"""
    row_id = signal_store.insert_rating(
        ticker='AAPL',
        rating='HOLD',
        timestamp='2024-03-15T11:00:00Z',
        source_document_id='email_67890'
    )

    assert row_id > 0


def test_insert_ratings_batch(signal_store):
    """Test batch insert of multiple ratings"""
    ratings = [
        {
            'ticker': 'NVDA',
            'rating': 'BUY',
            'timestamp': '2024-03-15T10:30:00Z',
            'source_document_id': 'email_1',
            'analyst': 'John Doe',
            'firm': 'Goldman Sachs',
            'confidence': 0.87
        },
        {
            'ticker': 'AAPL',
            'rating': 'HOLD',
            'timestamp': '2024-03-15T11:00:00Z',
            'source_document_id': 'email_2',
            'confidence': 0.75
        },
        {
            'ticker': 'TSMC',
            'rating': 'OUTPERFORM',
            'timestamp': '2024-03-15T12:00:00Z',
            'source_document_id': 'email_3',
            'analyst': 'Jane Smith',
            'firm': 'Morgan Stanley'
        }
    ]

    count = signal_store.insert_ratings_batch(ratings)
    assert count == 3


def test_get_latest_rating(signal_store):
    """Test retrieving the latest rating for a ticker"""
    # Insert multiple ratings for same ticker
    signal_store.insert_rating(
        ticker='NVDA',
        rating='HOLD',
        timestamp='2024-03-10T10:00:00Z',
        source_document_id='email_old',
        confidence=0.80
    )

    signal_store.insert_rating(
        ticker='NVDA',
        rating='BUY',
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='email_new',
        analyst='John Doe',
        firm='Goldman Sachs',
        confidence=0.87
    )

    # Get latest should return most recent
    latest = signal_store.get_latest_rating('NVDA')

    assert latest is not None
    assert latest['ticker'] == 'NVDA'
    assert latest['rating'] == 'BUY'
    assert latest['timestamp'] == '2024-03-15T10:30:00Z'
    assert latest['analyst'] == 'John Doe'
    assert latest['firm'] == 'Goldman Sachs'
    assert latest['confidence'] == 0.87


def test_get_latest_rating_no_results(signal_store):
    """Test getting latest rating for non-existent ticker"""
    latest = signal_store.get_latest_rating('NONEXISTENT')
    assert latest is None


def test_get_rating_history(signal_store):
    """Test retrieving rating history for a ticker"""
    # Insert multiple ratings
    timestamps = [
        '2024-03-10T10:00:00Z',
        '2024-03-12T10:00:00Z',
        '2024-03-15T10:00:00Z'
    ]

    for i, ts in enumerate(timestamps):
        signal_store.insert_rating(
            ticker='NVDA',
            rating=f'RATING_{i}',
            timestamp=ts,
            source_document_id=f'email_{i}'
        )

    # Get history (should be descending by timestamp)
    history = signal_store.get_rating_history('NVDA', limit=10)

    assert len(history) == 3
    assert history[0]['timestamp'] == '2024-03-15T10:00:00Z'  # Most recent first
    assert history[1]['timestamp'] == '2024-03-12T10:00:00Z'
    assert history[2]['timestamp'] == '2024-03-10T10:00:00Z'


def test_get_rating_history_with_limit(signal_store):
    """Test rating history respects limit parameter"""
    # Insert 5 ratings
    for i in range(5):
        signal_store.insert_rating(
            ticker='NVDA',
            rating=f'RATING_{i}',
            timestamp=f'2024-03-{10+i:02d}T10:00:00Z',
            source_document_id=f'email_{i}'
        )

    # Request only 2
    history = signal_store.get_rating_history('NVDA', limit=2)
    assert len(history) == 2


def test_get_ratings_by_firm(signal_store):
    """Test retrieving all ratings from a specific firm"""
    # Insert ratings from multiple firms
    ratings = [
        {'ticker': 'NVDA', 'rating': 'BUY', 'firm': 'Goldman Sachs'},
        {'ticker': 'AAPL', 'rating': 'HOLD', 'firm': 'Goldman Sachs'},
        {'ticker': 'TSMC', 'rating': 'BUY', 'firm': 'Morgan Stanley'},
    ]

    for r in ratings:
        signal_store.insert_rating(
            ticker=r['ticker'],
            rating=r['rating'],
            timestamp='2024-03-15T10:00:00Z',
            source_document_id='test',
            firm=r.get('firm')
        )

    # Get Goldman Sachs ratings
    gs_ratings = signal_store.get_ratings_by_firm('Goldman Sachs')

    assert len(gs_ratings) == 2
    assert all(r['firm'] == 'Goldman Sachs' for r in gs_ratings)


def test_count_ratings(signal_store):
    """Test counting total ratings"""
    # Initially empty
    assert signal_store.count_ratings() == 0

    # Insert 3 ratings
    for i in range(3):
        signal_store.insert_rating(
            ticker=f'TICKER_{i}',
            rating='BUY',
            timestamp='2024-03-15T10:00:00Z',
            source_document_id=f'email_{i}'
        )

    assert signal_store.count_ratings() == 3


# ==================== TRANSACTION TESTS ====================

def test_transaction_commit(signal_store):
    """Test transaction commit works correctly"""
    signal_store.begin_transaction()

    signal_store.insert_rating(
        ticker='NVDA',
        rating='BUY',
        timestamp='2024-03-15T10:00:00Z',
        source_document_id='test'
    )

    signal_store.commit()

    # Verify data persisted
    assert signal_store.count_ratings() == 1


def test_transaction_rollback(signal_store):
    """Test transaction rollback discards changes"""
    signal_store.begin_transaction()

    signal_store.conn.execute("""
        INSERT INTO ratings (ticker, rating, timestamp, source_document_id)
        VALUES ('NVDA', 'BUY', '2024-03-15T10:00:00Z', 'test')
    """)

    signal_store.rollback()

    # Verify data NOT persisted
    assert signal_store.count_ratings() == 0


# ==================== PERFORMANCE TESTS ====================

def test_indexed_query_performance(signal_store):
    """Test indexed queries complete quickly"""
    import time

    # Insert 100 ratings for different tickers
    for i in range(100):
        signal_store.insert_rating(
            ticker=f'TICKER_{i % 10}',  # 10 unique tickers
            rating='BUY',
            timestamp=f'2024-03-15T{i % 24:02d}:00:00Z',
            source_document_id=f'email_{i}'
        )

    # Query with indexed ticker (should be fast)
    start = time.time()
    latest = signal_store.get_latest_rating('TICKER_5')
    latency = time.time() - start

    assert latest is not None
    assert latency < 0.1  # <100ms


# ==================== CONTEXT MANAGER TESTS ====================

def test_context_manager_normal_exit(temp_db):
    """Test context manager closes connection on normal exit"""
    with SignalStore(db_path=temp_db) as store:
        store.insert_rating(
            ticker='NVDA',
            rating='BUY',
            timestamp='2024-03-15T10:00:00Z',
            source_document_id='test'
        )

    # Connection should be closed after exiting context


def test_context_manager_exception_exit(temp_db):
    """Test context manager rolls back and closes on exception"""
    with pytest.raises(ValueError):
        with SignalStore(db_path=temp_db) as store:
            store.begin_transaction()
            # Use direct SQL instead of insert_rating() which auto-commits
            store.conn.execute("""
                INSERT INTO ratings (ticker, rating, timestamp, source_document_id)
                VALUES ('NVDA', 'BUY', '2024-03-15T10:00:00Z', 'test')
            """)
            raise ValueError("Simulated error")

    # Verify rollback happened (no data persisted)
    with SignalStore(db_path=temp_db) as store:
        assert store.count_ratings() == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
