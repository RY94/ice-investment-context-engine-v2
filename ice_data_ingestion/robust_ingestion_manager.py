# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/robust_ingestion_manager.py
# Robust data ingestion manager with comprehensive error handling and validation
# Addresses identified bottlenecks, brittle assumptions, and edge cases in the pipeline
# RELEVANT FILES: ice_integration.py, config.py, mcp_infrastructure.py, news_processor.py

"""
Robust Data Ingestion Manager for ICE

This module provides a production-ready data ingestion system with:
- Comprehensive error handling and recovery
- Input validation and sanitization
- Efficient caching and deduplication
- Circuit breaker pattern for failing APIs
- Graceful degradation strategies
- Performance optimizations
- Data quality monitoring
"""

import asyncio
import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import time
from functools import wraps
import re

logger = logging.getLogger(__name__)


class DataSourceStatus(Enum):
    """Health status of data sources"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"


class DataQuality(Enum):
    """Data quality levels"""
    HIGH = "high"      # Complete, fresh, validated
    MEDIUM = "medium"  # Partial or slightly stale
    LOW = "low"        # Incomplete or very stale
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    quality: DataQuality
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_data: Optional[Dict] = None


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for API endpoints"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    is_open: bool = False
    half_open_attempts: int = 0
    success_count: int = 0


class DataValidator:
    """Validates and sanitizes incoming data"""

    # Required fields for different data types
    REQUIRED_FIELDS = {
        'stock': ['symbol', 'price', 'timestamp'],
        'news': ['title', 'url', 'published_date'],
        'filing': ['form_type', 'filing_date', 'company']
    }

    # Valid date formats to try
    DATE_FORMATS = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d-%m-%Y"
    ]

    @classmethod
    def validate_symbol(cls, symbol: Any) -> Optional[str]:
        """Validate and sanitize stock symbol"""
        if symbol is None:
            return None

        # Convert to string and clean
        symbol_str = str(symbol).strip().upper()

        # Remove special characters except dash and dot
        symbol_clean = re.sub(r'[^A-Z0-9\-\.]', '', symbol_str)

        # Check length constraints
        if len(symbol_clean) == 0 or len(symbol_clean) > 10:
            return None

        # Check if it's a valid pattern
        if not re.match(r'^[A-Z][A-Z0-9\-\.]*$', symbol_clean):
            return None

        return symbol_clean

    @classmethod
    def parse_date(cls, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats"""
        if date_value is None:
            return None

        # If already datetime, return it
        if isinstance(date_value, datetime):
            return date_value

        # Try parsing string dates
        if isinstance(date_value, str):
            for fmt in cls.DATE_FORMATS:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue

        # Try timestamp
        try:
            if isinstance(date_value, (int, float)):
                return datetime.fromtimestamp(date_value)
        except:
            pass

        return None

    @classmethod
    def sanitize_text(cls, text: Any) -> str:
        """Sanitize text content"""
        if text is None:
            return ""

        # Convert to string
        text_str = str(text)

        # Remove potential XSS/injection patterns
        text_clean = re.sub(r'<script[^>]*>.*?</script>', '', text_str, flags=re.IGNORECASE | re.DOTALL)
        text_clean = re.sub(r'javascript:', '', text_clean, flags=re.IGNORECASE)
        text_clean = re.sub(r'on\w+\s*=', '', text_clean, flags=re.IGNORECASE)

        # Normalize whitespace
        text_clean = ' '.join(text_clean.split())

        return text_clean

    @classmethod
    def validate_data(cls, data: Dict, data_type: str) -> ValidationResult:
        """Comprehensive data validation"""
        issues = []
        warnings = []
        sanitized = {}

        # Check required fields
        required = cls.REQUIRED_FIELDS.get(data_type, [])
        for field in required:
            if field not in data or data[field] is None:
                issues.append(f"Missing required field: {field}")

        # Type-specific validation
        if data_type == 'stock':
            # Validate symbol
            symbol = cls.validate_symbol(data.get('symbol'))
            if symbol:
                sanitized['symbol'] = symbol
            else:
                issues.append("Invalid stock symbol")

            # Validate price
            try:
                price = float(data.get('price', 0))
                if price < 0:
                    warnings.append("Negative price detected")
                elif price > 1000000:
                    warnings.append("Unusually high price detected")
                sanitized['price'] = price
            except:
                issues.append("Invalid price format")

            # Validate timestamp
            timestamp = cls.parse_date(data.get('timestamp'))
            if timestamp:
                sanitized['timestamp'] = timestamp
                # Check staleness
                age = datetime.now() - timestamp
                if age > timedelta(days=7):
                    warnings.append("Data is more than 7 days old")
            else:
                issues.append("Invalid timestamp")

        elif data_type == 'news':
            # Validate and sanitize text fields
            sanitized['title'] = cls.sanitize_text(data.get('title'))
            sanitized['content'] = cls.sanitize_text(data.get('content', ''))
            sanitized['url'] = cls.sanitize_text(data.get('url'))

            # Validate date
            pub_date = cls.parse_date(data.get('published_date'))
            if pub_date:
                sanitized['published_date'] = pub_date
            else:
                warnings.append("Could not parse publication date")

        # Determine quality
        if issues:
            quality = DataQuality.LOW if len(issues) > 2 else DataQuality.MEDIUM
        elif warnings:
            quality = DataQuality.MEDIUM
        else:
            quality = DataQuality.HIGH

        return ValidationResult(
            is_valid=len(issues) == 0,
            quality=quality,
            issues=issues,
            warnings=warnings,
            sanitized_data=sanitized if not issues else None
        )


class DataDeduplicator:
    """Handles data deduplication using content hashing"""

    def __init__(self, cache_dir: str = "storage/cache/dedup_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.seen_hashes = self._load_cache()
        self.duplicates_found = 0

    def _load_cache(self) -> Set[str]:
        """Load previously seen hashes"""
        cache_file = self.cache_dir / "seen_hashes.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()

    def _save_cache(self):
        """Persist seen hashes"""
        cache_file = self.cache_dir / "seen_hashes.json"
        try:
            # Keep only recent hashes (last 10000)
            recent_hashes = list(self.seen_hashes)[-10000:]
            with open(cache_file, 'w') as f:
                json.dump(recent_hashes, f)
        except Exception as e:
            logger.error(f"Failed to save dedup cache: {e}")

    def compute_hash(self, data: Dict) -> str:
        """Compute content hash for deduplication"""
        # Create canonical representation
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def is_duplicate(self, data: Dict) -> bool:
        """Check if data is duplicate"""
        data_hash = self.compute_hash(data)

        if data_hash in self.seen_hashes:
            self.duplicates_found += 1
            return True

        self.seen_hashes.add(data_hash)

        # Periodically save cache
        if len(self.seen_hashes) % 100 == 0:
            self._save_cache()

        return False


class CircuitBreaker:
    """Circuit breaker pattern for failing APIs"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_attempts: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_attempts = half_open_max_attempts
        self.states = defaultdict(CircuitBreakerState)

    def call(self, func):
        """Decorator for circuit breaker protection"""
        @wraps(func)
        async def wrapper(service_name: str, *args, **kwargs):
            state = self.states[service_name]

            # Check if circuit is open
            if state.is_open:
                # Check if recovery timeout has passed
                if state.last_failure_time:
                    time_since_failure = (datetime.now() - state.last_failure_time).seconds
                    if time_since_failure > self.recovery_timeout:
                        # Try half-open state
                        state.is_open = False
                        state.half_open_attempts += 1
                        logger.info(f"Circuit breaker half-open for {service_name}")
                    else:
                        raise Exception(f"Circuit breaker open for {service_name}")

            try:
                result = await func(service_name, *args, **kwargs)

                # Success - reset failure count
                state.failure_count = 0
                state.success_count += 1

                # Close circuit if was half-open
                if state.half_open_attempts > 0:
                    state.half_open_attempts = 0
                    logger.info(f"Circuit breaker closed for {service_name}")

                return result

            except Exception as e:
                state.failure_count += 1
                state.last_failure_time = datetime.now()

                # Check if should open circuit
                if state.failure_count >= self.failure_threshold:
                    state.is_open = True
                    logger.warning(f"Circuit breaker opened for {service_name} after {state.failure_count} failures")

                # Check half-open attempts
                if state.half_open_attempts >= self.half_open_max_attempts:
                    state.is_open = True
                    state.half_open_attempts = 0
                    logger.warning(f"Circuit breaker re-opened for {service_name} after failed recovery")

                raise e

        return wrapper


class RobustIngestionManager:
    """Production-ready data ingestion manager with comprehensive safeguards"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.validator = DataValidator()
        self.deduplicator = DataDeduplicator()
        self.circuit_breaker = CircuitBreaker()
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'duplicates_filtered': 0,
            'validation_failures': 0,
            'average_response_time': 0
        }
        self.data_sources = {}
        self._initialize_data_sources()

    def _initialize_data_sources(self):
        """Initialize data source connections with fallbacks"""
        # Import here to avoid circular dependencies
        try:
            from .ice_integration import ICEDataIntegrationManager
            self.ice_manager = ICEDataIntegrationManager()
            self.data_sources['ice'] = DataSourceStatus.HEALTHY
        except Exception as e:
            logger.error(f"Failed to initialize ICE manager: {e}")
            self.data_sources['ice'] = DataSourceStatus.FAILED

        try:
            from .free_api_connectors import free_api_manager
            self.fallback_manager = free_api_manager
            self.data_sources['fallback'] = DataSourceStatus.HEALTHY
        except Exception as e:
            logger.error(f"Failed to initialize fallback manager: {e}")
            self.data_sources['fallback'] = DataSourceStatus.FAILED

    async def ingest_with_validation(
        self,
        symbol: str,
        data_type: str = 'stock',
        add_to_knowledge_base: bool = True
    ) -> Dict[str, Any]:
        """Ingest data with comprehensive validation and error handling"""

        start_time = time.time()
        self.performance_metrics['total_requests'] += 1

        try:
            # Step 1: Validate input
            clean_symbol = self.validator.validate_symbol(symbol)
            if not clean_symbol:
                self.performance_metrics['validation_failures'] += 1
                return {
                    'success': False,
                    'error': 'Invalid symbol format',
                    'symbol': symbol
                }

            # Step 2: Check deduplication cache
            cache_key = {'symbol': clean_symbol, 'type': data_type}
            if self.deduplicator.is_duplicate(cache_key):
                self.performance_metrics['duplicates_filtered'] += 1
                logger.info(f"Duplicate request filtered for {clean_symbol}")
                return {
                    'success': True,
                    'cached': True,
                    'symbol': clean_symbol,
                    'message': 'Using cached data'
                }

            # Step 3: Try primary data source with circuit breaker
            result = None
            if self.data_sources.get('ice') != DataSourceStatus.FAILED:
                try:
                    result = await self._fetch_with_retry(
                        'ice',
                        clean_symbol,
                        data_type,
                        add_to_knowledge_base
                    )
                except Exception as e:
                    logger.warning(f"Primary source failed: {e}")
                    self.data_sources['ice'] = DataSourceStatus.DEGRADED

            # Step 4: Fallback if primary failed
            if not result and self.data_sources.get('fallback') != DataSourceStatus.FAILED:
                logger.info(f"Using fallback for {clean_symbol}")
                try:
                    result = await self._fetch_from_fallback(clean_symbol, data_type)
                except Exception as e:
                    logger.error(f"Fallback also failed: {e}")
                    self.data_sources['fallback'] = DataSourceStatus.DEGRADED

            # Step 5: Validate result
            if result:
                validation = self.validator.validate_data(result, data_type)
                if validation.is_valid:
                    result['validation'] = {
                        'quality': validation.quality.value,
                        'warnings': validation.warnings
                    }
                    if validation.sanitized_data:
                        result.update(validation.sanitized_data)
                else:
                    logger.warning(f"Validation issues: {validation.issues}")
                    result['validation'] = {
                        'quality': validation.quality.value,
                        'issues': validation.issues,
                        'warnings': validation.warnings
                    }

            # Step 6: Update metrics
            elapsed = time.time() - start_time
            self._update_metrics(success=bool(result), response_time=elapsed)

            if result:
                result['metrics'] = {
                    'response_time': elapsed,
                    'data_source': 'primary' if self.data_sources.get('ice') == DataSourceStatus.HEALTHY else 'fallback'
                }
                return result
            else:
                self.performance_metrics['failed_requests'] += 1
                return {
                    'success': False,
                    'error': 'All data sources failed',
                    'symbol': clean_symbol
                }

        except Exception as e:
            logger.error(f"Unexpected error in ingestion: {e}")
            self.performance_metrics['failed_requests'] += 1
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol
            }

    async def _fetch_with_retry(
        self,
        source: str,
        symbol: str,
        data_type: str,
        add_to_knowledge_base: bool,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """Fetch data with exponential backoff retry"""

        @self.circuit_breaker.call
        async def protected_fetch(service_name: str, *args, **kwargs):
            if service_name == 'ice' and self.ice_manager:
                return await self.ice_manager.ingest_company_intelligence(
                    symbol, add_to_knowledge_base
                )
            return None

        for attempt in range(max_retries):
            try:
                return await protected_fetch(source, symbol, data_type)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retry {attempt + 1} after {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    raise e

        return None

    async def _fetch_from_fallback(self, symbol: str, data_type: str) -> Optional[Dict]:
        """Fetch from fallback source"""
        if self.fallback_manager:
            return await self.fallback_manager.get_comprehensive_data(symbol)
        return None

    def _update_metrics(self, success: bool, response_time: float):
        """Update performance metrics"""
        if success:
            self.performance_metrics['successful_requests'] += 1

        # Update rolling average response time
        total = self.performance_metrics['total_requests']
        avg = self.performance_metrics['average_response_time']
        self.performance_metrics['average_response_time'] = (
            (avg * (total - 1) + response_time) / total
        )

    async def batch_ingest(
        self,
        symbols: List[str],
        batch_size: int = 10,
        delay_between_batches: float = 1.0
    ) -> Dict[str, Any]:
        """Efficiently ingest multiple symbols in batches"""

        results = {}
        failed = []

        # Process in batches
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]

            # Process batch concurrently
            tasks = [
                self.ingest_with_validation(symbol)
                for symbol in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            for symbol, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    failed.append(symbol)
                    results[symbol] = {'success': False, 'error': str(result)}
                else:
                    results[symbol] = result

            # Delay between batches to avoid rate limiting
            if i + batch_size < len(symbols):
                await asyncio.sleep(delay_between_batches)

        return {
            'results': results,
            'summary': {
                'total': len(symbols),
                'successful': len([r for r in results.values() if r.get('success')]),
                'failed': len(failed),
                'failed_symbols': failed
            },
            'metrics': self.get_metrics()
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        metrics = self.performance_metrics.copy()

        # Add success rate
        if metrics['total_requests'] > 0:
            metrics['success_rate'] = (
                metrics['successful_requests'] / metrics['total_requests']
            )
        else:
            metrics['success_rate'] = 0

        # Add deduplication stats
        metrics['duplicates_found'] = self.deduplicator.duplicates_found

        # Add data source health
        metrics['data_sources'] = {
            name: status.value
            for name, status in self.data_sources.items()
        }

        # Add circuit breaker states
        metrics['circuit_breakers'] = {
            name: {
                'is_open': state.is_open,
                'failure_count': state.failure_count,
                'success_count': state.success_count
            }
            for name, state in self.circuit_breaker.states.items()
        }

        return metrics

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of ingestion system"""

        # Check data source health
        healthy_sources = sum(
            1 for status in self.data_sources.values()
            if status == DataSourceStatus.HEALTHY
        )
        total_sources = len(self.data_sources)

        # Check circuit breakers
        open_breakers = sum(
            1 for state in self.circuit_breaker.states.values()
            if state.is_open
        )

        # Calculate overall health
        metrics = self.get_metrics()
        success_rate = metrics.get('success_rate', 0)

        if healthy_sources == 0 or success_rate < 0.1:
            overall_health = 'CRITICAL'
        elif healthy_sources < total_sources / 2 or success_rate < 0.5:
            overall_health = 'DEGRADED'
        elif open_breakers > 0 or success_rate < 0.8:
            overall_health = 'WARNING'
        else:
            overall_health = 'HEALTHY'

        return {
            'status': overall_health,
            'healthy_sources': f"{healthy_sources}/{total_sources}",
            'open_circuit_breakers': open_breakers,
            'success_rate': f"{success_rate:.1%}",
            'average_response_time': f"{metrics['average_response_time']:.2f}s",
            'duplicates_filtered': metrics['duplicates_found'],
            'validation_failures': metrics['validation_failures'],
            'timestamp': datetime.now().isoformat()
        }


# Singleton instance
robust_ingestion_manager = None


def get_robust_manager(config: Optional[Dict] = None) -> RobustIngestionManager:
    """Get or create singleton robust ingestion manager"""
    global robust_ingestion_manager
    if robust_ingestion_manager is None:
        robust_ingestion_manager = RobustIngestionManager(config)
    return robust_ingestion_manager


async def demo_robust_ingestion():
    """Demonstration of robust ingestion capabilities"""

    manager = get_robust_manager()

    print("🚀 Robust Data Ingestion Demo")
    print("=" * 50)

    # Test 1: Valid symbol
    print("\n1. Testing valid symbol (AAPL)...")
    result = await manager.ingest_with_validation("AAPL")
    print(f"   Result: {result.get('success')}")
    if result.get('validation'):
        print(f"   Quality: {result['validation'].get('quality')}")

    # Test 2: Invalid symbol
    print("\n2. Testing invalid symbol...")
    result = await manager.ingest_with_validation("INVALID123@#$")
    print(f"   Result: {result.get('success')}")
    print(f"   Error: {result.get('error')}")

    # Test 3: Batch ingestion
    print("\n3. Testing batch ingestion...")
    symbols = ["AAPL", "GOOGL", "MSFT", "INVALID", "TSLA"]
    batch_result = await manager.batch_ingest(symbols, batch_size=3)
    print(f"   Summary: {batch_result['summary']}")

    # Test 4: Edge cases
    print("\n4. Testing edge cases...")
    edge_cases = ["", None, "A" * 50, "123", "AAPL GOOGL"]
    for symbol in edge_cases:
        result = await manager.ingest_with_validation(symbol or "None")
        print(f"   {symbol or 'None'}: {result.get('success')}")

    # Show metrics
    print("\n📊 Performance Metrics:")
    metrics = manager.get_metrics()
    for key, value in metrics.items():
        if not isinstance(value, dict):
            print(f"   {key}: {value}")

    # Show health status
    print("\n🏥 Health Status:")
    health = manager.get_health_status()
    for key, value in health.items():
        print(f"   {key}: {value}")

    print("\n✅ Demo completed!")


if __name__ == "__main__":
    asyncio.run(demo_robust_ingestion())