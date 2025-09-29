# ice_data_ingestion/robust_client.py
"""
Robust HTTP Client with Retry Logic, Circuit Breaker, and Connection Pooling
Implements production-grade resilience patterns for financial data APIs
Handles transient failures, rate limiting, and service degradation gracefully
Relevant files: financial_news_connectors.py, sec_edgar_connector.py, mcp_client_manager.py
"""

import asyncio
import aiohttp
import requests
import time
import logging
from enum import Enum
from typing import Optional, Dict, Any, Callable, Union, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from functools import wraps
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures exceeded threshold, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open before closing
    timeout: float = 60.0  # Seconds before trying half-open
    excluded_exceptions: tuple = ()  # Exceptions that don't trip the breaker


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd
    retry_on: tuple = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        aiohttp.ClientError,
    )


@dataclass
class PoolConfig:
    """Configuration for connection pooling"""
    pool_connections: int = 10
    pool_maxsize: int = 20
    max_retries: int = 3
    backoff_factor: float = 0.3
    timeout: float = 30.0


@dataclass
class ServiceMetrics:
    """Metrics for service monitoring"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_opens: int = 0
    total_retries: int = 0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation

    Prevents cascading failures by stopping requests to failing services
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker"""
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.metrics = ServiceMetrics()

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitOpenError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
            else:
                self.metrics.failed_requests += 1
                raise CircuitOpenError(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    async def async_call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Async version of call"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
            else:
                self.metrics.failed_requests += 1
                raise CircuitOpenError(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try reset"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.config.timeout

    def _on_success(self):
        """Handle successful call"""
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.last_success = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' is now CLOSED")

    def _on_failure(self, exception: Exception):
        """Handle failed call"""
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.last_failure = datetime.now()

        # Check if exception should trip the breaker
        if isinstance(exception, self.config.excluded_exceptions):
            return

        self.last_failure_time = time.time()
        self.failure_count += 1

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.metrics.circuit_opens += 1
            logger.warning(f"Circuit breaker '{self.name}' is now OPEN (half-open test failed)")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.metrics.circuit_opens += 1
            logger.warning(f"Circuit breaker '{self.name}' is now OPEN (threshold exceeded)")


class RetryHandler:
    """
    Sophisticated retry logic with exponential backoff and jitter
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry handler"""
        self.config = config or RetryConfig()

    def retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for retry logic"""
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return self._execute_with_retry(func, *args, **kwargs)
        return wrapper

    def async_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Async decorator for retry logic"""
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await self._async_execute_with_retry(func, *args, **kwargs)
        return wrapper

    def _execute_with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic"""
        last_exception = None
        delay = self.config.initial_delay

        for attempt in range(self.config.max_attempts):
            try:
                return func(*args, **kwargs)
            except self.config.retry_on as e:
                last_exception = e
                if attempt < self.config.max_attempts - 1:
                    sleep_time = self._calculate_delay(attempt, delay)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    delay = min(delay * self.config.exponential_base, self.config.max_delay)

        logger.error(f"All {self.config.max_attempts} attempts failed")
        raise last_exception

    async def _async_execute_with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute async function with retry logic"""
        last_exception = None
        delay = self.config.initial_delay

        for attempt in range(self.config.max_attempts):
            try:
                return await func(*args, **kwargs)
            except self.config.retry_on as e:
                last_exception = e
                if attempt < self.config.max_attempts - 1:
                    sleep_time = self._calculate_delay(attempt, delay)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f}s..."
                    )
                    await asyncio.sleep(sleep_time)
                    delay = min(delay * self.config.exponential_base, self.config.max_delay)

        logger.error(f"All {self.config.max_attempts} attempts failed")
        raise last_exception

    def _calculate_delay(self, attempt: int, base_delay: float) -> float:
        """Calculate delay with optional jitter"""
        delay = base_delay
        if self.config.jitter:
            # Add random jitter (±25%)
            jitter = delay * 0.25 * (2 * random.random() - 1)
            delay += jitter
        return max(0, delay)


class ConnectionPoolManager:
    """
    Manages connection pools for different services
    """

    def __init__(self):
        """Initialize connection pool manager"""
        self._pools: Dict[str, requests.Session] = {}
        self._async_pools: Dict[str, aiohttp.ClientSession] = {}
        self._configs: Dict[str, PoolConfig] = {}

    def get_session(self, service: str, config: Optional[PoolConfig] = None) -> requests.Session:
        """
        Get or create a session with connection pooling

        Args:
            service: Service identifier
            config: Pool configuration

        Returns:
            Configured requests Session
        """
        if service not in self._pools:
            pool_config = config or PoolConfig()
            self._configs[service] = pool_config

            # Create session with connection pooling
            session = requests.Session()

            # Configure retry strategy
            retry_strategy = Retry(
                total=pool_config.max_retries,
                backoff_factor=pool_config.backoff_factor,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
            )

            # Configure adapter with connection pooling
            adapter = HTTPAdapter(
                pool_connections=pool_config.pool_connections,
                pool_maxsize=pool_config.pool_maxsize,
                max_retries=retry_strategy
            )

            session.mount("http://", adapter)
            session.mount("https://", adapter)

            # Set default timeout
            session.request = self._wrap_request_with_timeout(session.request, pool_config.timeout)

            self._pools[service] = session
            logger.info(f"Created connection pool for {service}")

        return self._pools[service]

    async def get_async_session(self, service: str, config: Optional[PoolConfig] = None) -> aiohttp.ClientSession:
        """Get or create async session with connection pooling"""
        if service not in self._async_pools:
            pool_config = config or PoolConfig()
            self._configs[service] = pool_config

            # Configure connector with pooling
            connector = aiohttp.TCPConnector(
                limit=pool_config.pool_maxsize,
                limit_per_host=pool_config.pool_connections,
                ttl_dns_cache=300
            )

            # Configure timeout
            timeout = aiohttp.ClientTimeout(total=pool_config.timeout)

            # Create session
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )

            self._async_pools[service] = session
            logger.info(f"Created async connection pool for {service}")

        return self._async_pools[service]

    def _wrap_request_with_timeout(self, request_func: Callable, timeout: float) -> Callable:
        """Wrap request function with default timeout"""
        @wraps(request_func)
        def wrapper(*args, **kwargs):
            if 'timeout' not in kwargs:
                kwargs['timeout'] = timeout
            return request_func(*args, **kwargs)
        return wrapper

    def close_all(self):
        """Close all connection pools"""
        for session in self._pools.values():
            session.close()
        self._pools.clear()

        for session in self._async_pools.values():
            asyncio.create_task(session.close())
        self._async_pools.clear()

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all pools"""
        metrics = {}
        for service, config in self._configs.items():
            metrics[service] = {
                'pool_connections': config.pool_connections,
                'pool_maxsize': config.pool_maxsize,
                'has_sync_pool': service in self._pools,
                'has_async_pool': service in self._async_pools
            }
        return metrics


class RobustHTTPClient:
    """
    Production-grade HTTP client with all resilience patterns
    """

    def __init__(self, service_name: str):
        """Initialize robust HTTP client"""
        self.service_name = service_name
        self.circuit_breaker = CircuitBreaker(service_name)
        self.retry_handler = RetryHandler()
        self.pool_manager = ConnectionPoolManager()
        self.metrics = defaultdict(ServiceMetrics)

    def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with full resilience

        Args:
            method: HTTP method
            url: Target URL
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        start_time = time.time()

        try:
            # Get pooled session
            session = self.pool_manager.get_session(self.service_name)

            # Apply circuit breaker and retry logic
            @self.retry_handler.retry
            def make_request():
                return self.circuit_breaker.call(
                    session.request,
                    method,
                    url,
                    **kwargs
                )

            response = make_request()

            # Record metrics
            elapsed = time.time() - start_time
            self.metrics[self.service_name].response_times.append(elapsed)
            self.metrics[self.service_name].total_requests += 1
            self.metrics[self.service_name].successful_requests += 1

            return response

        except Exception as e:
            # Record failure metrics
            self.metrics[self.service_name].total_requests += 1
            self.metrics[self.service_name].failed_requests += 1
            raise

    async def async_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Async version of request"""
        start_time = time.time()

        try:
            # Get pooled session
            session = await self.pool_manager.get_async_session(self.service_name)

            # Apply circuit breaker and retry logic
            @self.retry_handler.async_retry
            async def make_request():
                return await self.circuit_breaker.async_call(
                    session.request,
                    method,
                    url,
                    **kwargs
                )

            response = await make_request()

            # Record metrics
            elapsed = time.time() - start_time
            self.metrics[self.service_name].response_times.append(elapsed)
            self.metrics[self.service_name].total_requests += 1
            self.metrics[self.service_name].successful_requests += 1

            return response

        except Exception as e:
            # Record failure metrics
            self.metrics[self.service_name].total_requests += 1
            self.metrics[self.service_name].failed_requests += 1
            raise

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of client metrics"""
        service_metrics = self.metrics[self.service_name]
        circuit_metrics = self.circuit_breaker.metrics

        return {
            'service': self.service_name,
            'circuit_state': self.circuit_breaker.state.value,
            'total_requests': service_metrics.total_requests,
            'success_rate': f"{service_metrics.success_rate:.2%}",
            'avg_response_time': f"{service_metrics.avg_response_time:.3f}s",
            'circuit_opens': circuit_metrics.circuit_opens,
            'total_retries': circuit_metrics.total_retries,
            'pool_metrics': self.pool_manager.get_metrics().get(self.service_name, {})
        }


class CircuitOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


# Global client registry
_robust_clients: Dict[str, RobustHTTPClient] = {}


def get_robust_client(service_name: str) -> RobustHTTPClient:
    """Get or create a robust HTTP client for a service"""
    if service_name not in _robust_clients:
        _robust_clients[service_name] = RobustHTTPClient(service_name)
    return _robust_clients[service_name]