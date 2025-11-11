# Location: tests/test_dual_layer_ratings.py
# Purpose: End-to-end tests for dual-layer ratings workflow (Signal Store + LightRAG)
# Why: Validate complete vertical slice: ingest → dual-write → query routing → <1s latency
# Relevant Files: signal_store.py, data_ingestion.py, query_router.py, ice_simplified.py

import pytest
import os
import tempfile
import time
from pathlib import Path

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from updated_architectures.implementation.signal_store import SignalStore
from updated_architectures.implementation.query_router import QueryRouter, QueryType
from updated_architectures.implementation.config import ICEConfig


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


@pytest.fixture
def test_config(temp_signal_store):
    """Create test configuration with Signal Store enabled"""
    config = ICEConfig()
    config.use_signal_store = True
    config.signal_store_path = temp_signal_store.db_path
    return config


@pytest.fixture
def query_router(temp_signal_store):
    """Create QueryRouter instance"""
    return QueryRouter(signal_store=temp_signal_store)


# ==================== QUERY ROUTER TESTS ====================

def test_router_detects_structured_rating_query(query_router):
    """Test router correctly identifies structured rating queries"""
    queries = [
        "What's NVDA's latest rating?",
        "Show me the rating for AAPL",
        "What is the current recommendation for TSMC?",
        "Get NVDA rating"
    ]

    for query in queries:
        query_type, confidence = query_router.route_query(query)
        assert query_type == QueryType.STRUCTURED_RATING
        assert confidence >= 0.85


def test_router_detects_semantic_why_query(query_router):
    """Test router correctly identifies semantic WHY queries"""
    queries = [
        "Why did Goldman upgrade NVDA?",
        "Explain why the analyst is bullish"
    ]

    for query in queries:
        query_type, confidence = query_router.route_query(query)
        assert query_type == QueryType.SEMANTIC_WHY
        assert confidence >= 0.85

    # This query contains both "reason" (semantic) and "rating" (structured)
    # Should be classified as HYBRID (correct behavior)
    query_type, confidence = query_router.route_query("What is the reason for the rating change?")
    assert query_type == QueryType.HYBRID
    assert confidence >= 0.80


def test_router_detects_semantic_how_query(query_router):
    """Test router correctly identifies semantic HOW queries"""
    queries = [
        "How does China risk impact NVDA?",
        "How will the rating affect stock price?",
        "How does this influence the portfolio?"
    ]

    for query in queries:
        query_type, confidence = query_router.route_query(query)
        assert query_type == QueryType.SEMANTIC_HOW
        assert confidence >= 0.85


def test_router_detects_hybrid_query(query_router):
    """Test router correctly identifies hybrid queries"""
    queries = [
        "What's NVDA's rating and why did it change?",
        "Show me the rating and explain the reasoning",
        "What is the recommendation and how does it impact our portfolio?"
    ]

    for query in queries:
        query_type, confidence = query_router.route_query(query)
        assert query_type == QueryType.HYBRID
        assert confidence >= 0.80


def test_router_extracts_ticker(query_router):
    """Test router extracts ticker from query"""
    test_cases = [
        ("What's NVDA's latest rating?", "NVDA"),
        ("Show me AAPL rating", "AAPL"),
        ("Get the recommendation for TSMC", "TSMC"),
        ("What about META?", "META")
    ]

    for query, expected_ticker in test_cases:
        ticker = query_router.extract_ticker(query)
        assert ticker == expected_ticker


def test_router_no_ticker_in_query(query_router):
    """Test router returns None when no ticker found"""
    queries = [
        "What are the latest market trends?",
        "Show me all ratings",
        "Get portfolio summary"
    ]

    for query in queries:
        ticker = query_router.extract_ticker(query)
        assert ticker is None


# ==================== DUAL-WRITE INTEGRATION TESTS ====================

def test_rating_dual_write_to_signal_store(temp_signal_store):
    """Test ratings are written to Signal Store during ingestion"""
    # Simulate EntityExtractor output
    merged_entities = {
        'tickers': [{'ticker': 'NVDA', 'confidence': 0.95}],
        'ratings': [{'rating': 'BUY', 'confidence': 0.87, 'source': 'rating_pattern'}]
    }

    email_data = {
        'message_id': 'test_email_123',
        'from': 'analyst@goldmansachs.com',
        'subject': 'NVDA Upgrade',
        'date': '2024-03-15T10:30:00Z'
    }

    # Test the helper method directly without full DataIngester initialization
    from updated_architectures.implementation.data_ingestion import DataIngester

    # Create minimal mock object with just the method we need
    class MinimalIngester:
        def __init__(self, signal_store):
            self.signal_store = signal_store

        # Copy the method from DataIngester
        _write_ratings_to_signal_store = DataIngester._write_ratings_to_signal_store

    ingester = MinimalIngester(temp_signal_store)

    # Execute dual-write
    ingester._write_ratings_to_signal_store(
        merged_entities=merged_entities,
        email_data=email_data,
        timestamp=email_data['date']
    )

    # Verify data written to Signal Store
    latest = temp_signal_store.get_latest_rating('NVDA')
    assert latest is not None
    assert latest['ticker'] == 'NVDA'
    assert latest['rating'] == 'BUY'
    assert latest['confidence'] == 0.87
    assert latest['firm'] == 'analyst@goldmansachs.com'


def test_dual_write_graceful_degradation(temp_signal_store):
    """Test dual-write continues even if Signal Store fails"""
    merged_entities = {
        'tickers': [{'ticker': 'NVDA', 'confidence': 0.95}],
        'ratings': [{'rating': 'BUY', 'confidence': 0.87}]
    }

    email_data = {
        'message_id': 'test_email_456',
        'from': 'analyst@ms.com',
        'date': '2024-03-15T11:00:00Z'
    }

    # Close Signal Store to simulate failure
    temp_signal_store.close()

    from updated_architectures.implementation.data_ingestion import DataIngester

    # Create minimal mock object
    class MinimalIngester:
        def __init__(self, signal_store):
            self.signal_store = signal_store

        _write_ratings_to_signal_store = DataIngester._write_ratings_to_signal_store

    ingester = MinimalIngester(temp_signal_store)

    # This should NOT raise exception (graceful degradation)
    try:
        ingester._write_ratings_to_signal_store(
            merged_entities=merged_entities,
            email_data=email_data,
            timestamp=email_data['date']
        )
    except Exception as e:
        pytest.fail(f"Dual-write should not fail: {e}")


# ==================== QUERY PERFORMANCE TESTS ====================

def test_signal_store_query_latency(temp_signal_store):
    """Test Signal Store query completes in <1s"""
    # Insert test data
    temp_signal_store.insert_rating(
        ticker='NVDA',
        rating='BUY',
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='test_email',
        firm='Goldman Sachs',
        confidence=0.87
    )

    # Measure query latency
    start = time.time()
    result = temp_signal_store.get_latest_rating('NVDA')
    latency = time.time() - start

    assert result is not None
    assert latency < 1.0  # <1s target
    assert latency < 0.1  # Should be much faster (<100ms)


def test_signal_store_batch_query_performance(temp_signal_store):
    """Test Signal Store handles multiple queries efficiently"""
    # Insert ratings for 10 tickers
    tickers = ['NVDA', 'AAPL', 'TSMC', 'ASML', 'AMD', 'INTC', 'TSM', 'QCOM', 'TXN', 'MU']
    for ticker in tickers:
        temp_signal_store.insert_rating(
            ticker=ticker,
            rating='BUY',
            timestamp='2024-03-15T10:30:00Z',
            source_document_id='test_batch'
        )

    # Query all 10 tickers
    start = time.time()
    for ticker in tickers:
        result = temp_signal_store.get_latest_rating(ticker)
        assert result is not None

    total_latency = time.time() - start

    # 10 queries should complete in <1s total
    assert total_latency < 1.0


# ==================== QUERY ROUTER RESULT FORMATTING ====================

def test_router_formats_signal_store_result(query_router):
    """Test router formats Signal Store results correctly"""
    rating_data = {
        'ticker': 'NVDA',
        'rating': 'BUY',
        'firm': 'Goldman Sachs',
        'analyst': 'John Doe',
        'confidence': 0.87,
        'timestamp': '2024-03-15T10:30:00Z'
    }

    formatted = query_router.format_signal_store_result(rating_data, "What's NVDA's rating?")

    assert 'NVDA' in formatted
    assert 'BUY' in formatted
    assert 'Goldman Sachs' in formatted
    assert 'John Doe' in formatted
    assert '0.87' in formatted


def test_router_formats_empty_result(query_router):
    """Test router handles empty results gracefully"""
    formatted = query_router.format_signal_store_result(None, "What's XYZ's rating?")

    assert 'No Signal Store data found' in formatted


# ==================== INTEGRATION TESTS ====================

def test_end_to_end_rating_query_flow(temp_signal_store):
    """Test complete flow: ingest → dual-write → query → <1s latency"""
    # Step 1: Insert rating (simulates dual-write)
    temp_signal_store.insert_rating(
        ticker='NVDA',
        rating='BUY',
        timestamp='2024-03-15T10:30:00Z',
        source_document_id='goldman_email',
        firm='Goldman Sachs',
        analyst='John Doe',
        confidence=0.87
    )

    # Step 2: Initialize router
    router = QueryRouter(signal_store=temp_signal_store)

    # Step 3: Route query
    query = "What's NVDA's latest rating?"
    query_type, confidence = router.route_query(query)

    assert query_type == QueryType.STRUCTURED_RATING
    assert confidence >= 0.85

    # Step 4: Extract ticker and query
    ticker = router.extract_ticker(query)
    assert ticker == 'NVDA'

    # Step 5: Execute query and measure latency
    start = time.time()
    result = temp_signal_store.get_latest_rating(ticker)
    latency = time.time() - start

    # Step 6: Validate result and performance
    assert result is not None
    assert result['rating'] == 'BUY'
    assert result['firm'] == 'Goldman Sachs'
    assert latency < 1.0  # <1s target


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
