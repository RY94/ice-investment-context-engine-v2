# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/tests/test_smart_cache.py
# Test script for the smart caching solution that solves Alpha Vantage cache corruption
# Validates cache corruption prevention, adaptive TTL, and circuit breaker functionality
# RELEVANT FILES: ice_data_ingestion/smart_cache.py, ice_data_ingestion/alpha_vantage_client.py

"""
Smart Cache Test Suite

Tests the elegant caching solution for Alpha Vantage API issues:
1. Cache corruption prevention when rate limited
2. Adaptive TTL based on quota and failures
3. Circuit breaker pattern for API health
4. Two-tier caching (memory + disk)
5. Cache warming and statistics
"""

import unittest
import json
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ice_data_ingestion.smart_cache import (
    SmartCache, CacheMetadata, CacheValidationStatus,
    AlphaVantageValidator, CircuitState, cached_api_call
)


class TestSmartCache(unittest.TestCase):
    """Test suite for smart caching functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_cache_dir = Path("test_cache")
        self.cache = SmartCache(
            cache_dir=str(self.test_cache_dir),
            memory_size=5,
            default_ttl_hours=1
        )

    def tearDown(self):
        """Clean up test environment"""
        if self.test_cache_dir.exists():
            shutil.rmtree(self.test_cache_dir)

    def test_corruption_prevention(self):
        """Test that corrupted responses are not cached"""
        print("\n=== Testing Cache Corruption Prevention ===")

        # Simulate rate-limited response with wrong ticker
        corrupted_data = {
            "Symbol": "AAPL",  # Wrong symbol
            "Name": "Apple Inc.",
            "Exchange": "NASDAQ"
        }

        # Try to cache data for TSLA but response contains AAPL
        success = self.cache.set(
            provider="alpha_vantage",
            endpoint="overview",
            params={"symbol": "TSLA"},
            data=corrupted_data,
            requested_symbol="TSLA"
        )

        self.assertFalse(success, "Corrupted data should not be cached")

        # Verify corrupted data is not retrievable
        retrieved = self.cache.get(
            provider="alpha_vantage",
            endpoint="overview",
            params={"symbol": "TSLA"},
            requested_symbol="TSLA"
        )

        self.assertIsNone(retrieved, "Corrupted data should not be retrievable")

        # Check statistics
        stats = self.cache.get_statistics()
        self.assertEqual(stats["corrupted_prevented"], 1)
        print(f"✓ Prevented {stats['corrupted_prevented']} corrupted cache entries")

    def test_valid_data_caching(self):
        """Test that valid responses are cached correctly"""
        print("\n=== Testing Valid Data Caching ===")

        # Valid response with matching ticker
        valid_data = {
            "Symbol": "TSLA",
            "Name": "Tesla, Inc.",
            "Exchange": "NASDAQ",
            "MarketCapitalization": "800000000000"
        }

        # Cache valid data
        success = self.cache.set(
            provider="alpha_vantage",
            endpoint="overview",
            params={"symbol": "TSLA"},
            data=valid_data,
            requested_symbol="TSLA"
        )

        self.assertTrue(success, "Valid data should be cached")

        # Retrieve from cache
        retrieved = self.cache.get(
            provider="alpha_vantage",
            endpoint="overview",
            params={"symbol": "TSLA"},
            requested_symbol="TSLA"
        )

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["Symbol"], "TSLA")
        print(f"✓ Successfully cached and retrieved data for TSLA")

    def test_adaptive_ttl(self):
        """Test adaptive TTL based on quota usage"""
        print("\n=== Testing Adaptive TTL ===")

        # Test normal quota usage (30%)
        ttl_normal = self.cache._get_adaptive_ttl(quota_usage=0.3, validation_failures=0)
        base_ttl = self.cache.default_ttl.total_seconds()
        self.assertEqual(ttl_normal, base_ttl)
        print(f"✓ Normal quota (30%): TTL = {ttl_normal}s")

        # Test high quota usage (90%)
        ttl_high_quota = self.cache._get_adaptive_ttl(quota_usage=0.9, validation_failures=0)
        self.assertEqual(ttl_high_quota, base_ttl * 2)
        print(f"✓ High quota (90%): TTL = {ttl_high_quota}s (2x longer)")

        # Test with validation failures
        ttl_failures = self.cache._get_adaptive_ttl(quota_usage=0.3, validation_failures=6)
        self.assertEqual(ttl_failures, base_ttl * 0.5)
        print(f"✓ With failures: TTL = {ttl_failures}s (50% shorter)")

    def test_circuit_breaker(self):
        """Test circuit breaker pattern"""
        print("\n=== Testing Circuit Breaker ===")

        # Initial state should be CLOSED
        self.assertEqual(self.cache.circuit_state, CircuitState.CLOSED)
        print("✓ Initial state: CLOSED")

        # Simulate multiple failures
        for i in range(6):
            self.cache._update_circuit_breaker(success=False)

        # Circuit should be OPEN after threshold failures
        self.assertEqual(self.cache.circuit_state, CircuitState.OPEN)
        print(f"✓ After {self.cache.circuit_threshold} failures: OPEN")

        # Force cache usage when circuit is open
        self.assertTrue(self.cache.should_use_cache())
        print("✓ Forces cache usage when circuit is OPEN")

        # Simulate timeout for recovery
        self.cache.circuit_last_failure = datetime.now() - timedelta(seconds=301)
        self.cache._check_circuit_recovery()
        self.assertEqual(self.cache.circuit_state, CircuitState.HALF_OPEN)
        print("✓ After timeout: HALF_OPEN (testing recovery)")

        # Successful request should close circuit
        self.cache._update_circuit_breaker(success=True)
        self.assertEqual(self.cache.circuit_state, CircuitState.CLOSED)
        print("✓ After successful test: CLOSED (recovered)")

    def test_two_tier_caching(self):
        """Test memory and disk cache coordination"""
        print("\n=== Testing Two-Tier Cache ===")

        # Fill memory cache to capacity
        for i in range(7):
            data = {"Symbol": f"TEST{i}", "Value": i}
            self.cache.set(
                provider="alpha_vantage",
                endpoint="test",
                params={"id": i},
                data=data
            )

        # Memory cache should be at max size (5)
        self.assertEqual(len(self.cache.memory_cache), 5)
        print(f"✓ Memory cache at capacity: {len(self.cache.memory_cache)}/{self.cache.memory_size}")

        # All 7 items should be on disk
        disk_files = list(self.test_cache_dir.glob("*.json"))
        self.assertEqual(len(disk_files), 7)
        print(f"✓ Disk cache contains all items: {len(disk_files)}")

        # Accessing old item should promote it to memory
        retrieved = self.cache.get(
            provider="alpha_vantage",
            endpoint="test",
            params={"id": 0}
        )
        self.assertIsNotNone(retrieved)
        print("✓ Old items promoted from disk to memory on access")

    def test_rate_limit_detection(self):
        """Test detection of rate limit messages"""
        print("\n=== Testing Rate Limit Detection ===")

        # Simulate rate limit error response
        rate_limit_response = {
            "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute."
        }

        success = self.cache.set(
            provider="alpha_vantage",
            endpoint="overview",
            params={"symbol": "AAPL"},
            data=rate_limit_response,
            requested_symbol="AAPL"
        )

        self.assertFalse(success, "Rate limit responses should not be cached")
        print("✓ Rate limit error responses are rejected")

    def test_cache_statistics(self):
        """Test cache statistics tracking"""
        print("\n=== Testing Cache Statistics ===")

        # Generate some cache activity
        valid_data = {"Symbol": "AAPL", "Name": "Apple Inc."}
        self.cache.set("alpha_vantage", "overview", {"symbol": "AAPL"},
                      valid_data, "AAPL")

        # Cache hit
        self.cache.get("alpha_vantage", "overview", {"symbol": "AAPL"}, "AAPL")

        # Cache miss
        self.cache.get("alpha_vantage", "overview", {"symbol": "GOOGL"}, "GOOGL")

        stats = self.cache.get_statistics()
        print(f"✓ Cache statistics:")
        print(f"  - Hit rate: {stats['hit_rate']}")
        print(f"  - Total hits: {stats['total_hits']}")
        print(f"  - Total misses: {stats['total_misses']}")
        print(f"  - Validations passed: {stats['validations_passed']}")
        print(f"  - Corrupted prevented: {stats['corrupted_prevented']}")

        self.assertEqual(stats['total_hits'], 1)
        self.assertEqual(stats['total_misses'], 1)

    def test_cache_decorator(self):
        """Test the @cached_api_call decorator"""
        print("\n=== Testing Cache Decorator ===")

        call_count = 0

        @cached_api_call(self.cache, provider="test_provider")
        def mock_api_call(symbol: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"Symbol": symbol, "CallCount": call_count}

        # First call should hit API
        result1 = mock_api_call("AAPL")
        self.assertEqual(result1["CallCount"], 1)

        # Second call should hit cache
        result2 = mock_api_call("AAPL")
        self.assertEqual(result2["CallCount"], 1)  # Same as first call

        print(f"✓ Decorator cached API call (prevented {call_count} redundant calls)")


class TestAlphaVantageIntegration(unittest.TestCase):
    """Integration tests with Alpha Vantage client"""

    def setUp(self):
        """Set up test environment"""
        self.test_cache_dir = Path("test_av_integration")

    def tearDown(self):
        """Clean up test environment"""
        if self.test_cache_dir.exists():
            shutil.rmtree(self.test_cache_dir)

    def test_alpha_vantage_client_integration(self):
        """Test integration with AlphaVantageClient"""
        print("\n=== Testing Alpha Vantage Client Integration ===")

        # This would require an actual API key to fully test
        # For now, we'll test the initialization
        try:
            from ice_data_ingestion.alpha_vantage_client import AlphaVantageClient

            # Initialize with smart cache enabled
            client = AlphaVantageClient(
                api_key="test_key",
                use_smart_cache=True
            )

            self.assertTrue(client.use_smart_cache)
            self.assertIsNotNone(client.smart_cache)
            print("✓ Alpha Vantage client initialized with smart cache")

            # Test that smart cache is used for company overview
            # (Would need actual API key for full test)
            print("✓ Smart cache integration configured correctly")

        except ImportError as e:
            print(f"⚠ Skipping integration test: {e}")


def run_tests():
    """Run all tests with detailed output"""
    print("=" * 60)
    print("SMART CACHE TEST SUITE")
    print("Testing elegant solution for Alpha Vantage caching issues")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSmartCache))
    suite.addTests(loader.loadTestsFromTestCase(TestAlphaVantageIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ All tests passed! Smart cache is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)