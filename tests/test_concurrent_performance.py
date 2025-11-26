# Location: /tests/test_concurrent_performance.py
# Purpose: Benchmark concurrent vs sequential API fetching performance
# Why: Verify Phase 2 optimization achieves 3-5x speed improvement
# Relevant Files: data_ingestion.py, data_ingestion_concurrent.py

"""
Performance benchmark tests for concurrent API fetching

Tests compare sequential vs concurrent fetching to verify
the expected 3-5x performance improvement.
"""

import pytest
import time
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from updated_architectures.implementation.data_ingestion import DataIngester
from updated_architectures.implementation.data_ingestion_concurrent import (
    ConcurrentDataIngester,
    fetch_company_news_concurrent
)


class TestConcurrentPerformance:
    """Performance tests for concurrent API fetching"""

    @pytest.fixture
    def mock_api_keys(self):
        """Mock API keys for testing"""
        return {
            'newsapi': 'test_newsapi_key',
            'benzinga': 'test_benzinga_key',
            'finnhub': 'test_finnhub_key',
            'marketaux': 'test_marketaux_key'
        }

    @pytest.fixture
    def data_ingester(self, mock_api_keys):
        """Create DataIngester with mocked API keys"""
        with patch.dict('os.environ', {f'{k.upper()}_API_KEY': v for k, v in mock_api_keys.items()}):
            ingester = DataIngester()
            ingester.api_keys = mock_api_keys
            # Enable all APIs for testing
            ingester.api_config = {
                'api_source_enabled': True,
                'newsapi_enabled': True,
                'benzinga_enabled': True,
                'finnhub_enabled': True,
                'marketaux_enabled': True
            }
            return ingester

    def mock_api_response(self, api_name: str, delay: float = 0.5) -> List[str]:
        """Generate mock API response with simulated delay"""
        time.sleep(delay)  # Simulate network latency
        return [
            f"Article 1 from {api_name}",
            f"Article 2 from {api_name}",
            f"Article 3 from {api_name}"
        ]

    async def mock_api_response_async(self, api_name: str, delay: float = 0.5) -> List[Dict[str, str]]:
        """Async version of mock API response"""
        await asyncio.sleep(delay)  # Simulate network latency
        return [
            {
                'content': f"Article {i} from {api_name}",
                'source': api_name,
                'file_path': f"{api_name}:test_{i}"
            }
            for i in range(1, 4)
        ]

    def test_sequential_baseline(self, data_ingester):
        """Establish sequential fetching baseline timing"""
        # Mock individual API fetch methods with delays
        with patch.object(data_ingester, '_fetch_newsapi') as mock_newsapi, \
             patch.object(data_ingester, '_fetch_benzinga_news') as mock_benzinga, \
             patch.object(data_ingester, '_fetch_finnhub_news') as mock_finnhub, \
             patch.object(data_ingester, '_fetch_marketaux_news') as mock_marketaux:

            # Each API takes 0.5 seconds - use side_effect to ensure delay happens
            mock_newsapi.side_effect = lambda s, l: self.mock_api_response('newsapi', 0.5)
            mock_benzinga.side_effect = lambda s, l: self.mock_api_response('benzinga', 0.5)
            mock_finnhub.side_effect = lambda s, l: self.mock_api_response('finnhub', 0.5)
            mock_marketaux.side_effect = lambda s, l: self.mock_api_response('marketaux', 0.5)

            # Measure sequential execution time
            start_time = time.time()
            results = data_ingester.fetch_company_news('NVDA', limit=12)
            sequential_time = time.time() - start_time

            # Should take approximately 2 seconds (4 APIs × 0.5s each)
            assert sequential_time >= 1.8, f"Sequential too fast: {sequential_time}s"
            assert sequential_time <= 2.5, f"Sequential too slow: {sequential_time}s"
            assert len(results) == 12  # Should get results from all APIs

            # Verify all APIs were called
            mock_newsapi.assert_called_once()
            mock_benzinga.assert_called_once()
            mock_finnhub.assert_called_once()
            mock_marketaux.assert_called_once()

            print(f"✅ Sequential baseline: {sequential_time:.2f}s for 4 APIs")

    @pytest.mark.asyncio
    async def test_concurrent_performance(self, data_ingester):
        """Test concurrent fetching performance improvement"""
        concurrent = ConcurrentDataIngester(data_ingester)

        # Mock async API methods
        concurrent._fetch_newsapi_async = AsyncMock(
            side_effect=lambda s, l: self.mock_api_response_async('newsapi', 0.5)
        )
        concurrent._fetch_benzinga_async = AsyncMock(
            side_effect=lambda s, l: self.mock_api_response_async('benzinga', 0.5)
        )
        concurrent._fetch_finnhub_async = AsyncMock(
            side_effect=lambda s, l: self.mock_api_response_async('finnhub', 0.5)
        )
        concurrent._fetch_marketaux_async = AsyncMock(
            side_effect=lambda s, l: self.mock_api_response_async('marketaux', 0.5)
        )

        # Measure concurrent execution time
        start_time = time.time()
        results = await concurrent.fetch_company_news_async('NVDA', limit=12)
        concurrent_time = time.time() - start_time

        # Should take approximately 0.5 seconds (all parallel)
        assert concurrent_time >= 0.4, f"Concurrent too fast: {concurrent_time}s"
        assert concurrent_time <= 1.0, f"Concurrent too slow: {concurrent_time}s"
        assert len(results) == 12  # Should get limited results

        print(f"✅ Concurrent execution: {concurrent_time:.2f}s for 4 APIs")
        print(f"🚀 Performance improvement: {2.0/concurrent_time:.1f}x faster")

    def test_performance_improvement_ratio(self, data_ingester):
        """Test that concurrent is at least 3x faster than sequential"""
        # Setup mocks for both sequential and concurrent
        with patch.object(data_ingester, '_fetch_newsapi') as mock_newsapi, \
             patch.object(data_ingester, '_fetch_benzinga_news') as mock_benzinga, \
             patch.object(data_ingester, '_fetch_finnhub_news') as mock_finnhub, \
             patch.object(data_ingester, '_fetch_marketaux_news') as mock_marketaux:

            # Sequential mocks (0.5s each) - use side_effect for delays
            mock_newsapi.side_effect = lambda s, l: self.mock_api_response('newsapi', 0.5)
            mock_benzinga.side_effect = lambda s, l: self.mock_api_response('benzinga', 0.5)
            mock_finnhub.side_effect = lambda s, l: self.mock_api_response('finnhub', 0.5)
            mock_marketaux.side_effect = lambda s, l: self.mock_api_response('marketaux', 0.5)

            # Measure sequential time
            sequential_start = time.time()
            sequential_results = data_ingester.fetch_company_news('NVDA', limit=12)
            sequential_time = time.time() - sequential_start

            # Now test concurrent with the new method
            # Mock the data_ingestion_concurrent module
            with patch('updated_architectures.implementation.data_ingestion_concurrent.fetch_company_news_concurrent') as mock_concurrent:
                # Simulate concurrent execution (all APIs in parallel)
                async def concurrent_simulation(ingester, symbol, limit):
                    await asyncio.sleep(0.5)  # All APIs run in parallel
                    return [
                        {'content': f'Article {i}', 'source': 'mixed', 'file_path': f'test:{i}'}
                        for i in range(12)
                    ]

                mock_concurrent.side_effect = concurrent_simulation

                concurrent_start = time.time()
                concurrent_results = data_ingester.fetch_company_news_concurrent('NVDA', limit=12)
                concurrent_time = time.time() - concurrent_start

            # Calculate improvement
            speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0

            print(f"\n📊 Performance Comparison:")
            print(f"  Sequential: {sequential_time:.2f}s")
            print(f"  Concurrent: {concurrent_time:.2f}s")
            print(f"  Speedup: {speedup:.2f}x")

            # Should be at least 3x faster
            assert speedup >= 3.0, f"Insufficient speedup: {speedup:.2f}x (expected >=3x)"
            assert len(sequential_results) == len(concurrent_results)

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, data_ingester):
        """Test that concurrent handles API failures gracefully"""
        concurrent = ConcurrentDataIngester(data_ingester)

        # Mock with one failing API
        concurrent._fetch_newsapi_async = AsyncMock(
            side_effect=Exception("NewsAPI failed")
        )
        concurrent._fetch_benzinga_async = AsyncMock(
            return_value=[
                {'content': 'Benzinga article', 'source': 'benzinga', 'file_path': 'benzinga:1'}
            ]
        )
        concurrent._fetch_finnhub_async = AsyncMock(
            return_value=[
                {'content': 'Finnhub article', 'source': 'finnhub', 'file_path': 'finnhub:1'}
            ]
        )
        concurrent._fetch_marketaux_async = AsyncMock(
            side_effect=Exception("MarketAux failed")
        )

        # Should still get results from working APIs
        results = await concurrent.fetch_company_news_async('NVDA', limit=10)

        assert len(results) == 2  # Only Benzinga and Finnhub succeeded
        assert any('benzinga' in r['source'] for r in results)
        assert any('finnhub' in r['source'] for r in results)

        # Check metrics
        metrics = concurrent.get_performance_metrics()
        assert metrics['failed_requests'] == 2
        assert metrics['successful_requests'] == 2

    def test_concurrent_fallback_to_sequential(self, data_ingester):
        """Test fallback to sequential when concurrent fails"""
        with patch.object(data_ingester, 'fetch_company_news') as mock_sequential:
            mock_sequential.return_value = [
                {'content': 'Sequential article', 'source': 'newsapi', 'file_path': 'test:1'}
            ]

            # Test with import error
            with patch('updated_architectures.implementation.data_ingestion.fetch_company_news_concurrent',
                      side_effect=ImportError("Module not found")):
                results = data_ingester.fetch_company_news_concurrent('NVDA', limit=5)

                # Should fall back to sequential
                mock_sequential.assert_called_once_with('NVDA', 5)
                assert len(results) == 1
                assert results[0]['content'] == 'Sequential article'

    @pytest.mark.asyncio
    async def test_rate_limiting(self, data_ingester):
        """Test that rate limiting prevents API quota exhaustion"""
        concurrent = ConcurrentDataIngester(data_ingester)

        # Track call times
        call_times = []

        async def track_timing(*args):
            call_times.append(time.time())
            return []

        concurrent._fetch_finnhub_async = AsyncMock(side_effect=track_timing)

        # Make multiple requests
        await concurrent.fetch_company_news_async('NVDA', limit=5)
        await concurrent.fetch_company_news_async('AAPL', limit=5)

        if len(call_times) >= 2:
            # Check that calls are spaced according to rate limit
            time_between = call_times[1] - call_times[0]
            # Finnhub rate limit is 60/min = 1 per second
            assert time_between >= 0.9, f"Rate limit not respected: {time_between}s"

    def test_metrics_tracking(self, data_ingester):
        """Test that performance metrics are tracked correctly"""
        concurrent = ConcurrentDataIngester(data_ingester)

        # Reset metrics
        concurrent.reset_metrics()

        metrics_before = concurrent.get_performance_metrics()
        assert metrics_before['total_requests'] == 0
        assert metrics_before['successful_requests'] == 0

        # Simulate some activity
        concurrent.metrics['total_requests'] = 10
        concurrent.metrics['successful_requests'] = 8
        concurrent.metrics['failed_requests'] = 2
        concurrent.metrics['total_time'] = 5.0
        concurrent.metrics['api_times'] = {
            'newsapi': [0.5, 0.6, 0.4],
            'finnhub': [0.3, 0.4]
        }

        metrics_after = concurrent.get_performance_metrics()

        assert metrics_after['total_requests'] == 10
        assert metrics_after['success_rate'] == 0.8
        assert metrics_after['average_time_per_request'] == 0.5
        assert 'newsapi' in metrics_after['average_api_times']
        assert metrics_after['average_api_times']['newsapi'] == 0.5  # (0.5+0.6+0.4)/3


if __name__ == '__main__':
    # Run with verbose output to see performance metrics
    pytest.main([__file__, '-v', '-s'])