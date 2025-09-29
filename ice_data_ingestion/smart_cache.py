# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/smart_cache.py
# Elegant smart caching solution for Alpha Vantage API with corruption detection and adaptive strategies
# Solves rate-limiting cache corruption issues with validation-aware caching and intelligent TTL management
# RELEVANT FILES: news_apis.py, alpha_vantage_client.py, robust_client.py, secure_config.py

"""
Smart Cache System for Alpha Vantage API

This module provides an elegant solution to Alpha Vantage's cache corruption issue where
rate-limited responses return wrong ticker data. The smart cache includes:

1. Validation-aware caching that prevents corrupted data storage
2. Adaptive TTL based on quota usage and data quality
3. Multi-tier caching with in-memory and persistent layers
4. Circuit breaker pattern for API health monitoring
5. Cache warming and proactive quota management
6. Cross-source validation for data integrity

The design follows clean architecture principles with separation of concerns
and pluggable validators for extensibility.
"""

from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json
import hashlib
import logging
import time
from collections import OrderedDict
from functools import wraps
import threading
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class CacheValidationStatus(Enum):
    """Cache entry validation states"""
    VALID = "valid"
    INVALID = "invalid"
    CORRUPTED = "corrupted"
    UNVALIDATED = "unvalidated"
    EXPIRED = "expired"

class CircuitState(Enum):
    """Circuit breaker states for API health"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # API failing, block requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CacheMetadata:
    """Rich metadata for cache entries"""
    timestamp: datetime
    ttl_seconds: int
    validation_status: CacheValidationStatus
    requested_symbol: Optional[str] = None
    response_symbol: Optional[str] = None
    confidence_score: float = 1.0
    source_provider: Optional[str] = None
    quota_usage_at_cache: float = 0.0
    validation_failures: int = 0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl_seconds

    def is_valid(self) -> bool:
        """Check if cache entry is valid and not expired"""
        return (not self.is_expired() and
                self.validation_status == CacheValidationStatus.VALID)

class CacheValidator(ABC):
    """Abstract base class for cache validators"""

    @abstractmethod
    def validate(self, data: Dict[str, Any], metadata: CacheMetadata) -> Tuple[bool, float]:
        """
        Validate cache data and return (is_valid, confidence_score)
        """
        pass

class AlphaVantageValidator(CacheValidator):
    """Validator specific to Alpha Vantage responses"""

    def validate(self, data: Dict[str, Any], metadata: CacheMetadata) -> Tuple[bool, float]:
        """
        Validate Alpha Vantage response for ticker consistency

        Returns:
            Tuple of (is_valid, confidence_score)
        """
        # Check for rate limit error messages
        if "Note" in data or "Information" in data:
            error_msg = data.get("Note", data.get("Information", ""))
            if any(keyword in error_msg.lower() for keyword in
                   ["rate limit", "premium", "api call frequency", "thank you for using"]):
                logger.warning(f"Rate limit detected in response: {error_msg[:100]}")
                return False, 0.0

        # No symbol validation needed if not ticker-specific
        if not metadata.requested_symbol:
            return True, 1.0

        # Check symbol consistency
        response_symbol = data.get("Symbol", "").upper()
        requested_symbol = metadata.requested_symbol.upper()

        if not response_symbol:
            # Some endpoints don't return symbol field
            return True, 0.8

        if response_symbol != requested_symbol:
            logger.warning(f"Symbol mismatch: requested {requested_symbol}, got {response_symbol}")
            return False, 0.0

        # Additional data quality checks
        confidence = 1.0

        # Check for suspiciously empty responses
        if len(data) < 3:
            confidence *= 0.5

        # Check for timestamp freshness if available
        if "lastRefreshed" in data:
            try:
                last_refreshed = datetime.fromisoformat(data["lastRefreshed"])
                age_days = (datetime.now() - last_refreshed).days
                if age_days > 7:
                    confidence *= 0.7
            except:
                pass

        return True, confidence

class SmartCache:
    """
    Intelligent caching system with validation and adaptive strategies

    Features:
    - Two-tier caching (memory + disk)
    - Validation-aware storage
    - Adaptive TTL based on quota and quality
    - Circuit breaker for API health
    - Cache warming and preloading
    """

    def __init__(
        self,
        cache_dir: str = "storage/cache/smart_cache",
        memory_size: int = 100,
        default_ttl_hours: int = 6,
        validator: Optional[CacheValidator] = None
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Two-tier cache
        self.memory_cache: OrderedDict[str, Tuple[Dict, CacheMetadata]] = OrderedDict()
        self.memory_size = memory_size

        # Configuration
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self.validator = validator or AlphaVantageValidator()

        # Circuit breaker
        self.circuit_state = CircuitState.CLOSED
        self.circuit_failures = 0
        self.circuit_threshold = 5
        self.circuit_timeout = 300  # 5 minutes
        self.circuit_last_failure: Optional[datetime] = None

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "validations_passed": 0,
            "validations_failed": 0,
            "corrupted_prevented": 0
        }

        # Thread safety
        self.lock = threading.RLock()

    def _get_cache_key(self, provider: str, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate deterministic cache key"""
        # Include symbol explicitly in key for better clarity
        symbol = params.get("symbol", params.get("ticker", ""))
        key_data = f"{provider}_{endpoint}_{symbol}_{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _get_adaptive_ttl(self, quota_usage: float, validation_failures: int) -> int:
        """
        Calculate adaptive TTL based on current conditions

        Args:
            quota_usage: Percentage of quota used (0.0 to 1.0)
            validation_failures: Recent validation failure count

        Returns:
            TTL in seconds
        """
        base_ttl = self.default_ttl.total_seconds()

        # Extend TTL when approaching quota limits
        if quota_usage > 0.8:
            ttl_multiplier = 2.0
        elif quota_usage > 0.6:
            ttl_multiplier = 1.5
        else:
            ttl_multiplier = 1.0

        # Reduce TTL when experiencing validation failures
        if validation_failures > 5:
            ttl_multiplier *= 0.5
        elif validation_failures > 2:
            ttl_multiplier *= 0.75

        # Apply circuit breaker influence
        if self.circuit_state == CircuitState.OPEN:
            ttl_multiplier *= 3.0  # Cache much longer when API is failing

        return int(base_ttl * ttl_multiplier)

    def _evict_memory_cache(self):
        """LRU eviction for memory cache"""
        while len(self.memory_cache) >= self.memory_size:
            # Remove least recently used item
            self.memory_cache.popitem(last=False)

    def _update_circuit_breaker(self, success: bool):
        """Update circuit breaker state based on request outcome"""
        with self.lock:
            if success:
                if self.circuit_state == CircuitState.HALF_OPEN:
                    # Successful test, close circuit
                    self.circuit_state = CircuitState.CLOSED
                    self.circuit_failures = 0
                    logger.info("Circuit breaker closed - API recovered")
                elif self.circuit_state == CircuitState.CLOSED:
                    # Reset failure count on success
                    self.circuit_failures = 0
            else:
                self.circuit_failures += 1
                self.circuit_last_failure = datetime.now()

                if self.circuit_failures >= self.circuit_threshold:
                    if self.circuit_state != CircuitState.OPEN:
                        self.circuit_state = CircuitState.OPEN
                        logger.warning(f"Circuit breaker opened - {self.circuit_failures} failures")

    def _check_circuit_recovery(self):
        """Check if circuit should transition to half-open"""
        if self.circuit_state == CircuitState.OPEN and self.circuit_last_failure:
            elapsed = (datetime.now() - self.circuit_last_failure).total_seconds()
            if elapsed > self.circuit_timeout:
                self.circuit_state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker half-open - testing recovery")

    def get(
        self,
        provider: str,
        endpoint: str,
        params: Dict[str, Any],
        requested_symbol: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve validated cached response

        Returns None if no valid cache exists or validation fails
        """
        with self.lock:
            cache_key = self._get_cache_key(provider, endpoint, params)

            # Check memory cache first
            if cache_key in self.memory_cache:
                data, metadata = self.memory_cache[cache_key]
                if metadata.is_valid():
                    # Move to end (most recently used)
                    self.memory_cache.move_to_end(cache_key)
                    metadata.access_count += 1
                    metadata.last_accessed = datetime.now()
                    self.stats["hits"] += 1
                    logger.debug(f"Memory cache hit for {provider}:{endpoint} ({requested_symbol})")
                    return data
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]

            # Check disk cache
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        cache_entry = json.load(f)

                    # Reconstruct metadata
                    metadata = CacheMetadata(
                        timestamp=datetime.fromisoformat(cache_entry["metadata"]["timestamp"]),
                        ttl_seconds=cache_entry["metadata"]["ttl_seconds"],
                        validation_status=CacheValidationStatus(cache_entry["metadata"]["validation_status"]),
                        requested_symbol=cache_entry["metadata"].get("requested_symbol"),
                        response_symbol=cache_entry["metadata"].get("response_symbol"),
                        confidence_score=cache_entry["metadata"].get("confidence_score", 1.0),
                        validation_failures=cache_entry["metadata"].get("validation_failures", 0)
                    )

                    if metadata.is_valid():
                        data = cache_entry["data"]
                        # Promote to memory cache
                        self._evict_memory_cache()
                        self.memory_cache[cache_key] = (data, metadata)
                        self.stats["hits"] += 1
                        logger.debug(f"Disk cache hit for {provider}:{endpoint} ({requested_symbol})")
                        return data
                    else:
                        # Remove expired/invalid cache
                        cache_file.unlink()

                except Exception as e:
                    logger.warning(f"Failed to read cache {cache_file}: {e}")
                    cache_file.unlink()

            self.stats["misses"] += 1
            return None

    def set(
        self,
        provider: str,
        endpoint: str,
        params: Dict[str, Any],
        data: Dict[str, Any],
        requested_symbol: Optional[str] = None,
        quota_usage: float = 0.0
    ) -> bool:
        """
        Store response with validation

        Returns:
            bool: True if cached successfully, False if validation failed
        """
        with self.lock:
            # Create metadata
            metadata = CacheMetadata(
                timestamp=datetime.now(),
                ttl_seconds=self._get_adaptive_ttl(quota_usage, self.circuit_failures),
                validation_status=CacheValidationStatus.UNVALIDATED,
                requested_symbol=requested_symbol,
                response_symbol=data.get("Symbol"),
                source_provider=provider,
                quota_usage_at_cache=quota_usage,
                validation_failures=self.circuit_failures
            )

            # Validate data
            is_valid, confidence = self.validator.validate(data, metadata)

            if not is_valid:
                self.stats["validations_failed"] += 1
                self.stats["corrupted_prevented"] += 1
                self._update_circuit_breaker(False)
                logger.warning(f"Rejected corrupted cache for {provider}:{endpoint} ({requested_symbol})")
                return False

            metadata.validation_status = CacheValidationStatus.VALID
            metadata.confidence_score = confidence
            self.stats["validations_passed"] += 1
            self._update_circuit_breaker(True)

            cache_key = self._get_cache_key(provider, endpoint, params)

            # Store in memory cache
            self._evict_memory_cache()
            self.memory_cache[cache_key] = (data, metadata)

            # Store on disk
            cache_file = self.cache_dir / f"{cache_key}.json"
            cache_entry = {
                "data": data,
                "metadata": {
                    "timestamp": metadata.timestamp.isoformat(),
                    "ttl_seconds": metadata.ttl_seconds,
                    "validation_status": metadata.validation_status.value,
                    "requested_symbol": metadata.requested_symbol,
                    "response_symbol": metadata.response_symbol,
                    "confidence_score": metadata.confidence_score,
                    "source_provider": metadata.source_provider,
                    "quota_usage_at_cache": metadata.quota_usage_at_cache,
                    "validation_failures": metadata.validation_failures
                }
            }

            try:
                with open(cache_file, 'w') as f:
                    json.dump(cache_entry, f, indent=2)
                logger.debug(f"Cached {provider}:{endpoint} ({requested_symbol}) with TTL={metadata.ttl_seconds}s")
                return True
            except Exception as e:
                logger.error(f"Failed to write cache: {e}")
                return False

    def should_use_cache(self) -> bool:
        """
        Determine if cache should be used based on circuit state
        """
        self._check_circuit_recovery()

        if self.circuit_state == CircuitState.OPEN:
            # Force cache usage when API is down
            return True
        elif self.circuit_state == CircuitState.HALF_OPEN:
            # Use cache 80% of the time during recovery testing
            import random
            return random.random() < 0.8
        else:
            # Normal operation
            return True

    def warm_cache(self, provider: str, endpoint: str, symbol_list: List[str],
                   fetch_func: Callable, quota_usage: float = 0.0):
        """
        Proactively warm cache with priority symbols

        Args:
            provider: API provider name
            endpoint: API endpoint
            symbol_list: List of symbols to cache
            fetch_func: Function to fetch data for a symbol
            quota_usage: Current quota usage percentage
        """
        if quota_usage > 0.7:
            logger.info(f"Skipping cache warming - quota usage at {quota_usage:.0%}")
            return

        warmed = 0
        for symbol in symbol_list:
            # Check if already cached
            params = {"symbol": symbol}
            if self.get(provider, endpoint, params, symbol):
                continue

            try:
                # Fetch and cache
                data = fetch_func(symbol)
                if data:
                    self.set(provider, endpoint, params, data, symbol, quota_usage)
                    warmed += 1
                    time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.warning(f"Failed to warm cache for {symbol}: {e}")

        if warmed > 0:
            logger.info(f"Warmed cache with {warmed} symbols")

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics and health metrics"""
        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                "hit_rate": f"{hit_rate:.1%}",
                "total_hits": self.stats["hits"],
                "total_misses": self.stats["misses"],
                "validations_passed": self.stats["validations_passed"],
                "validations_failed": self.stats["validations_failed"],
                "corrupted_prevented": self.stats["corrupted_prevented"],
                "memory_cache_size": len(self.memory_cache),
                "circuit_state": self.circuit_state.value,
                "circuit_failures": self.circuit_failures
            }

    def clear_invalid(self):
        """Remove all invalid or expired cache entries"""
        with self.lock:
            # Clear memory cache
            keys_to_remove = []
            for key, (data, metadata) in self.memory_cache.items():
                if not metadata.is_valid():
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.memory_cache[key]

            # Clear disk cache
            removed = 0
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        cache_entry = json.load(f)

                    metadata = CacheMetadata(
                        timestamp=datetime.fromisoformat(cache_entry["metadata"]["timestamp"]),
                        ttl_seconds=cache_entry["metadata"]["ttl_seconds"],
                        validation_status=CacheValidationStatus(cache_entry["metadata"]["validation_status"])
                    )

                    if not metadata.is_valid():
                        cache_file.unlink()
                        removed += 1

                except Exception:
                    cache_file.unlink()
                    removed += 1

            logger.info(f"Cleared {len(keys_to_remove)} memory and {removed} disk cache entries")


def cached_api_call(cache: SmartCache, provider: str = "alpha_vantage"):
    """
    Decorator for automatic smart caching of API calls

    Usage:
        @cached_api_call(smart_cache)
        def get_company_overview(symbol: str) -> Dict:
            return alpha_vantage_client.get_company_overview(symbol)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract symbol from args/kwargs
            symbol = kwargs.get("symbol")
            if not symbol and args:
                symbol = args[0] if isinstance(args[0], str) else None

            # Generate cache params
            endpoint = func.__name__
            params = {"args": str(args), "kwargs": str(kwargs)}

            # Check cache
            if cache.should_use_cache():
                cached_data = cache.get(provider, endpoint, params, symbol)
                if cached_data:
                    return cached_data

            # Fetch from API
            try:
                data = func(*args, **kwargs)

                # Get quota usage if available
                quota_usage = kwargs.get("_quota_usage", 0.0)

                # Cache successful response
                if data:
                    cache.set(provider, endpoint, params, data, symbol, quota_usage)

                return data

            except Exception as e:
                # On API failure, try to return stale cache
                logger.warning(f"API call failed, checking stale cache: {e}")
                cached_data = cache.get(provider, endpoint, params, symbol)
                if cached_data:
                    logger.info("Returning stale cache due to API failure")
                    return cached_data
                raise

        return wrapper
    return decorator