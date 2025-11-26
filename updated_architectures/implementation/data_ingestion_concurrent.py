# Location: /updated_architectures/implementation/data_ingestion_concurrent.py
# Purpose: Concurrent API fetching implementation for 3-5x performance improvement
# Why: Phase 2 optimization - fetch from all APIs in parallel instead of sequentially
# Relevant Files: data_ingestion.py (original sequential implementation)

"""
Concurrent Data Ingestion Module for ICE

This module provides async/concurrent versions of API fetching methods
to improve performance by 3-5x through parallel execution.

Key Features:
- Concurrent fetching from multiple APIs using asyncio
- Rate limiting to respect API quotas
- Performance monitoring and telemetry
- Backward compatibility with existing DataIngester
"""

import asyncio
import aiohttp
import time
import hashlib
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from asyncio import Semaphore
import json

logger = logging.getLogger(__name__)

@dataclass
class APIRateLimits:
    """Rate limiting configuration for APIs"""
    newsapi: int = 500  # requests per day (free tier)
    benzinga: int = 5000  # requests per day (estimated)
    finnhub: int = 60  # requests per minute
    marketaux: int = 1000  # requests per day
    alpha_vantage: int = 5  # requests per minute
    polygon: int = 5  # requests per minute (free tier)

    def get_delay(self, api: str) -> float:
        """Calculate delay between requests to respect rate limits"""
        limits = {
            'newsapi': 24 * 3600 / self.newsapi,  # ~172 seconds
            'benzinga': 24 * 3600 / self.benzinga,  # ~17 seconds
            'finnhub': 60 / self.finnhub,  # 1 second
            'marketaux': 24 * 3600 / self.marketaux,  # ~86 seconds
            'alpha_vantage': 60 / self.alpha_vantage,  # 12 seconds
            'polygon': 60 / self.polygon,  # 12 seconds
        }
        return limits.get(api, 1.0)


class ConcurrentDataIngester:
    """
    Concurrent version of DataIngester for improved performance

    Features:
    - Async/await for all API calls
    - Concurrent fetching with asyncio.gather()
    - Rate limiting with semaphores
    - Performance telemetry
    """

    def __init__(self, original_ingester):
        """
        Initialize concurrent ingester wrapping the original DataIngester

        Args:
            original_ingester: Instance of DataIngester to wrap
        """
        self.ingester = original_ingester
        self.api_keys = original_ingester.api_keys
        self.api_config = original_ingester.api_config
        self.timeout = original_ingester.timeout

        # Rate limiting
        self.rate_limits = APIRateLimits()
        self.semaphores = {
            'newsapi': Semaphore(1),
            'benzinga': Semaphore(2),  # Allow 2 concurrent
            'finnhub': Semaphore(1),
            'marketaux': Semaphore(1),
            'alpha_vantage': Semaphore(1),
            'polygon': Semaphore(1)
        }

        # Performance tracking
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_time': 0.0,
            'api_times': {}
        }

    def is_service_available(self, service: str) -> bool:
        """Check if a service is available (delegate to original)"""
        return self.ingester.is_service_available(service)

    async def fetch_company_news_async(self, symbol: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Asynchronously fetch company news from all available APIs concurrently

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of articles per API

        Returns:
            List of dicts with 'content', 'source', and 'file_path' keys
        """
        start_time = time.time()

        # Determine which APIs are available
        available_apis = []
        if self.is_service_available('newsapi'):
            available_apis.append('newsapi')
        if self.is_service_available('benzinga'):
            available_apis.append('benzinga')
        if self.is_service_available('finnhub'):
            available_apis.append('finnhub')
        if self.is_service_available('marketaux'):
            available_apis.append('marketaux')

        if not available_apis:
            logger.warning(f"⚠️ {symbol}: No news APIs available. Returning empty list.")
            return []

        logger.info(f"🚀 {symbol}: Fetching from {len(available_apis)} APIs concurrently: {available_apis}")

        # Create tasks for concurrent execution
        tasks = []
        for api in available_apis:
            if api == 'newsapi':
                tasks.append(self._fetch_newsapi_async(symbol, limit))
            elif api == 'benzinga':
                tasks.append(self._fetch_benzinga_async(symbol, limit))
            elif api == 'finnhub':
                tasks.append(self._fetch_finnhub_async(symbol, limit))
            elif api == 'marketaux':
                tasks.append(self._fetch_marketaux_async(symbol, limit))

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        all_documents = []
        for api, result in zip(available_apis, results):
            if isinstance(result, Exception):
                logger.warning(f"❌ {api} failed for {symbol}: {result}")
                self.metrics['failed_requests'] += 1
            else:
                logger.info(f"  ✅ {api}: {len(result)} articles fetched")
                all_documents.extend(result)
                self.metrics['successful_requests'] += 1

        # Track performance
        elapsed = time.time() - start_time
        self.metrics['total_time'] += elapsed
        self.metrics['total_requests'] += len(available_apis)

        logger.info(f"⚡ {symbol}: Fetched {len(all_documents)} articles in {elapsed:.2f}s " +
                   f"(concurrent from {len(available_apis)} APIs)")

        # Return limited results
        return all_documents[:limit]

    async def _fetch_newsapi_async(self, symbol: str, limit: int) -> List[Dict[str, str]]:
        """Async version of NewsAPI fetching"""
        async with self.semaphores['newsapi']:
            start_time = time.time()

            url = "https://newsapi.org/v2/everything"
            params = {
                'q': f'"{symbol}" OR "{symbol} stock" OR "{symbol} earnings"',
                'apiKey': self.api_keys['newsapi'],
                'pageSize': min(limit, 20),
                'sortBy': 'relevancy',
                'language': 'en'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    response.raise_for_status()
                    data = await response.json()

            documents = []
            for article in data.get('articles', []):
                published_timestamp = article.get('publishedAt', datetime.now().isoformat())

                content = f"""
News Article: {article.get('title', 'Untitled')}

{article.get('description', '')}

{article.get('content', '')}

Source: {article.get('source', {}).get('name', 'Unknown')}
Published: {published_timestamp}
URL: {article.get('url', '')}
Symbol: {symbol}
Publication Date: {published_timestamp}
"""
                doc_hash = hashlib.md5(content[:200].encode()).hexdigest()[:8]
                documents.append({
                    'content': content.strip(),
                    'source': 'newsapi',
                    'file_path': f"newsapi:{symbol}_{doc_hash}"
                })

            # Track API-specific timing
            elapsed = time.time() - start_time
            if 'newsapi' not in self.metrics['api_times']:
                self.metrics['api_times']['newsapi'] = []
            self.metrics['api_times']['newsapi'].append(elapsed)

            # Rate limiting delay
            await asyncio.sleep(self.rate_limits.get_delay('newsapi'))

            return documents

    async def _fetch_benzinga_async(self, symbol: str, limit: int) -> List[Dict[str, str]]:
        """Async version of Benzinga fetching"""
        async with self.semaphores['benzinga']:
            # Note: Since Benzinga uses a special client, we'll run it in executor
            loop = asyncio.get_event_loop()

            def fetch_benzinga_sync():
                return self.ingester._fetch_benzinga_news(symbol, limit)

            start_time = time.time()
            benzinga_docs = await loop.run_in_executor(None, fetch_benzinga_sync)

            documents = []
            for doc in benzinga_docs:
                doc_hash = hashlib.md5(doc[:200].encode()).hexdigest()[:8]
                documents.append({
                    'content': doc,
                    'source': 'benzinga',
                    'file_path': f"benzinga:{symbol}_{doc_hash}"
                })

            # Track timing
            elapsed = time.time() - start_time
            if 'benzinga' not in self.metrics['api_times']:
                self.metrics['api_times']['benzinga'] = []
            self.metrics['api_times']['benzinga'].append(elapsed)

            return documents

    async def _fetch_finnhub_async(self, symbol: str, limit: int) -> List[Dict[str, str]]:
        """Async version of Finnhub fetching"""
        async with self.semaphores['finnhub']:
            start_time = time.time()

            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            url = "https://finnhub.io/api/v1/company-news"
            params = {
                'symbol': symbol,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'token': self.api_keys['finnhub']
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    response.raise_for_status()
                    articles = await response.json()

            documents = []
            for article in articles[:limit]:
                published_timestamp = datetime.fromtimestamp(
                    article.get('datetime', time.time())
                ).isoformat()

                content = f"""
News Article: {article.get('headline', 'Untitled')}

{article.get('summary', '')}

Source: {article.get('source', 'Finnhub')}
Published: {published_timestamp}
URL: {article.get('url', '')}
Symbol: {symbol}
Category: {article.get('category', 'general')}
Publication Date: {published_timestamp}
"""
                doc_hash = hashlib.md5(content[:200].encode()).hexdigest()[:8]
                documents.append({
                    'content': content.strip(),
                    'source': 'finnhub',
                    'file_path': f"finnhub:{symbol}_{doc_hash}"
                })

            # Track timing
            elapsed = time.time() - start_time
            if 'finnhub' not in self.metrics['api_times']:
                self.metrics['api_times']['finnhub'] = []
            self.metrics['api_times']['finnhub'].append(elapsed)

            # Rate limiting
            await asyncio.sleep(self.rate_limits.get_delay('finnhub'))

            return documents

    async def _fetch_marketaux_async(self, symbol: str, limit: int) -> List[Dict[str, str]]:
        """Async version of MarketAux fetching"""
        async with self.semaphores['marketaux']:
            start_time = time.time()

            url = "https://api.marketaux.com/v1/news/all"
            params = {
                'symbols': symbol,
                'filter_entities': 'true',
                'limit': min(limit, 10),
                'api_token': self.api_keys['marketaux']
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    response.raise_for_status()
                    data = await response.json()

            documents = []
            for article in data.get('data', []):
                published_timestamp = article.get('published_at', datetime.now().isoformat())

                # Extract entity highlights if available
                entities = article.get('entities', [])
                entity_mentions = ', '.join([
                    f"{e.get('name', 'Unknown')} ({e.get('type', 'N/A')})"
                    for e in entities[:5]
                ])

                content = f"""
News Article: {article.get('title', 'Untitled')}

{article.get('description', '')}

Source: {article.get('source', 'MarketAux')}
Published: {published_timestamp}
URL: {article.get('url', '')}
Symbol: {symbol}
Entities: {entity_mentions if entity_mentions else 'N/A'}
Publication Date: {published_timestamp}
"""
                doc_hash = hashlib.md5(content[:200].encode()).hexdigest()[:8]
                documents.append({
                    'content': content.strip(),
                    'source': 'marketaux',
                    'file_path': f"marketaux:{symbol}_{doc_hash}"
                })

            # Track timing
            elapsed = time.time() - start_time
            if 'marketaux' not in self.metrics['api_times']:
                self.metrics['api_times']['marketaux'] = []
            self.metrics['api_times']['marketaux'].append(elapsed)

            # Rate limiting
            await asyncio.sleep(self.rate_limits.get_delay('marketaux'))

            return documents

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        avg_times = {}
        for api, times in self.metrics['api_times'].items():
            if times:
                avg_times[api] = sum(times) / len(times)

        return {
            'total_requests': self.metrics['total_requests'],
            'successful_requests': self.metrics['successful_requests'],
            'failed_requests': self.metrics['failed_requests'],
            'total_time': self.metrics['total_time'],
            'average_time_per_request': self.metrics['total_time'] / max(1, self.metrics['total_requests']),
            'success_rate': self.metrics['successful_requests'] / max(1, self.metrics['total_requests']),
            'average_api_times': avg_times
        }

    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_time': 0.0,
            'api_times': {}
        }


def create_concurrent_ingester(original_ingester):
    """
    Factory function to create a concurrent ingester from existing DataIngester

    Args:
        original_ingester: Instance of DataIngester

    Returns:
        ConcurrentDataIngester instance
    """
    return ConcurrentDataIngester(original_ingester)


# Backward compatibility wrapper
async def fetch_company_news_concurrent(ingester, symbol: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Backward compatible wrapper for concurrent news fetching

    This function can be called from synchronous code using asyncio.run()

    Example:
        import asyncio
        from data_ingestion import DataIngester
        from data_ingestion_concurrent import fetch_company_news_concurrent

        ingester = DataIngester()
        news = asyncio.run(fetch_company_news_concurrent(ingester, 'NVDA', 10))
    """
    concurrent = ConcurrentDataIngester(ingester)
    return await concurrent.fetch_company_news_async(symbol, limit)


if __name__ == "__main__":
    # Performance testing
    import os
    from data_ingestion import DataIngester

    async def test_performance():
        """Test concurrent vs sequential performance"""

        # Setup
        ingester = DataIngester()
        concurrent = ConcurrentDataIngester(ingester)

        test_symbols = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN']

        # Sequential baseline
        print("\n📊 Sequential Fetching (Baseline):")
        sequential_start = time.time()
        for symbol in test_symbols:
            docs = ingester.fetch_company_news(symbol, limit=10)
            print(f"  {symbol}: {len(docs)} articles")
        sequential_time = time.time() - sequential_start
        print(f"⏱️ Sequential Total Time: {sequential_time:.2f}s\n")

        # Concurrent test
        print("🚀 Concurrent Fetching (Optimized):")
        concurrent_start = time.time()
        tasks = [concurrent.fetch_company_news_async(symbol, limit=10) for symbol in test_symbols]
        results = await asyncio.gather(*tasks)
        for symbol, docs in zip(test_symbols, results):
            print(f"  {symbol}: {len(docs)} articles")
        concurrent_time = time.time() - concurrent_start
        print(f"⏱️ Concurrent Total Time: {concurrent_time:.2f}s\n")

        # Performance comparison
        speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
        print(f"📈 Performance Improvement: {speedup:.2f}x faster")
        print(f"⏱️ Time Saved: {sequential_time - concurrent_time:.2f}s")

        # Display metrics
        metrics = concurrent.get_performance_metrics()
        print(f"\n📊 Detailed Metrics:")
        print(f"  Total Requests: {metrics['total_requests']}")
        print(f"  Success Rate: {metrics['success_rate']:.2%}")
        print(f"  Average Time per Request: {metrics['average_time_per_request']:.2f}s")
        print(f"  API Average Times:")
        for api, avg_time in metrics['average_api_times'].items():
            print(f"    - {api}: {avg_time:.2f}s")

    # Run test
    print("=" * 60)
    print("ICE Concurrent Data Ingestion - Performance Test")
    print("=" * 60)

    asyncio.run(test_performance())