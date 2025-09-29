# ice_lightrag/query_optimization.py
# Advanced query optimization and performance tuning for ICE system
# Provides caching, preprocessing, and performance monitoring for queries
# RELEVANT FILES: ice_lightrag/ice_rag.py, CLAUDE.md, setup/architecture_patterns.py

import time
import hashlib
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class QueryMetrics:
    """Query execution metrics"""
    execution_time_ms: float
    cache_hit: bool
    preprocessing_time_ms: float
    llm_time_ms: float
    post_processing_time_ms: float
    token_count: int
    confidence_score: float


class QueryCache:
    """Intelligent caching system for query results"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
    
    def generate_cache_key(self, query: str, kwargs: Dict) -> str:
        """Generate unique cache key for query and parameters"""
        # Normalize query
        normalized_query = query.strip().lower()
        
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        
        # Create combined string
        combined = f"{normalized_query}_{sorted_kwargs}"
        
        # Generate hash
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if valid"""
        if cache_key not in self.cache:
            return None
        
        cached_item = self.cache[cache_key]
        
        # Check TTL
        if time.time() - cached_item['timestamp'] > self.ttl_seconds:
            self._remove(cache_key)
            return None
        
        # Update access time
        self.access_times[cache_key] = time.time()
        return cached_item['result']
    
    def put(self, cache_key: str, result: Dict[str, Any]):
        """Store result in cache"""
        # Evict if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
        self.access_times[cache_key] = time.time()
    
    def _remove(self, cache_key: str):
        """Remove item from cache"""
        self.cache.pop(cache_key, None)
        self.access_times.pop(cache_key, None)
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times, key=self.access_times.get)
        self._remove(lru_key)
    
    def clear(self):
        """Clear all cached items"""
        self.cache.clear()
        self.access_times.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_ratio': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1),
            'oldest_item_age_hours': (time.time() - min(
                (item['timestamp'] for item in self.cache.values()),
                default=time.time()
            )) / 3600
        }


class QueryPreprocessor:
    """Query preprocessing and optimization"""
    
    def __init__(self):
        self.financial_abbreviations = {
            'PE': 'price to earnings ratio',
            'P/E': 'price to earnings ratio',
            'ROE': 'return on equity',
            'ROA': 'return on assets',
            'ROI': 'return on investment',
            'EBITDA': 'earnings before interest taxes depreciation amortization',
            'FCF': 'free cash flow',
            'EPS': 'earnings per share',
            'P/B': 'price to book ratio',
            'PEG': 'price earnings growth ratio',
            'ROIC': 'return on invested capital',
            'WACC': 'weighted average cost of capital',
            'NPV': 'net present value',
            'IRR': 'internal rate of return',
            'DCF': 'discounted cash flow',
            'CAGR': 'compound annual growth rate'
        }
        
        self.query_patterns = {
            'risk_analysis': ['risk', 'threat', 'danger', 'vulnerability', 'exposure'],
            'financial_performance': ['revenue', 'profit', 'earnings', 'income', 'performance'],
            'market_analysis': ['market', 'competition', 'industry', 'sector', 'peers'],
            'growth_analysis': ['growth', 'expansion', 'development', 'increase', 'scaling']
        }
    
    def preprocess_query(self, query: str) -> str:
        """Preprocess and optimize query text"""
        # Normalize whitespace
        query = ' '.join(query.split())
        
        # Expand financial abbreviations
        for abbr, expansion in self.financial_abbreviations.items():
            # Case-insensitive replacement with word boundaries
            import re
            pattern = r'\b' + re.escape(abbr) + r'\b'
            query = re.sub(pattern, expansion, query, flags=re.IGNORECASE)
        
        # Add context hints based on detected patterns
        query = self._add_context_hints(query)
        
        return query
    
    def _add_context_hints(self, query: str) -> str:
        """Add context hints based on query patterns"""
        query_lower = query.lower()
        
        # Detect query type and add relevant context
        for pattern_type, keywords in self.query_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                # Add subtle context hints without changing the core query
                if pattern_type == 'risk_analysis' and 'analysis' not in query_lower:
                    query += ' analysis'
                elif pattern_type == 'financial_performance' and 'company' not in query_lower:
                    query += ' for the company'
        
        return query
    
    def estimate_complexity(self, query: str) -> Dict[str, Any]:
        """Estimate query complexity for parameter optimization"""
        query_lower = query.lower()
        
        # Count complexity indicators
        multi_hop_indicators = [
            'through', 'via', 'because of', 'leads to', 'results in',
            'causes', 'impacts', 'affects', 'influences', 'depends on'
        ]
        
        temporal_indicators = ['trend', 'over time', 'historically', 'forecast', 'predict']
        comparison_indicators = ['compare', 'versus', 'vs', 'better than', 'worse than']
        
        complexity_score = 1
        indicators = {
            'multi_hop': sum(1 for indicator in multi_hop_indicators if indicator in query_lower),
            'temporal': sum(1 for indicator in temporal_indicators if indicator in query_lower),
            'comparison': sum(1 for indicator in comparison_indicators if indicator in query_lower)
        }
        
        # Calculate complexity
        complexity_score += indicators['multi_hop'] * 0.5
        complexity_score += indicators['temporal'] * 0.3
        complexity_score += indicators['comparison'] * 0.4
        
        # Estimate required hops
        estimated_hops = min(3, max(1, int(complexity_score)))
        
        return {
            'complexity_score': complexity_score,
            'estimated_hops': estimated_hops,
            'indicators': indicators,
            'recommended_timeout': min(120, max(30, int(complexity_score * 20)))
        }


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics_history = []
        self.performance_thresholds = {
            'fast_query_ms': 1000,
            'acceptable_query_ms': 5000,
            'slow_query_ms': 10000
        }
    
    @contextmanager
    def measure_performance(self):
        """Context manager for measuring query performance"""
        start_time = time.time()
        metrics = {
            'start_time': start_time,
            'preprocessing_time': 0,
            'llm_time': 0,
            'postprocessing_time': 0
        }
        
        class PerfContext:
            def __init__(self, metrics):
                self.metrics = metrics
            
            def mark_preprocessing_complete(self):
                self.metrics['preprocessing_time'] = (time.time() - self.metrics['start_time']) * 1000
            
            def mark_llm_complete(self):
                current_time = time.time()
                if 'llm_start' not in self.metrics:
                    self.metrics['llm_start'] = current_time
                self.metrics['llm_time'] = (current_time - self.metrics.get('llm_start', current_time)) * 1000
            
            def mark_postprocessing_complete(self):
                self.metrics['postprocessing_time'] = (time.time() - self.metrics['start_time']) * 1000 - self.metrics['preprocessing_time'] - self.metrics['llm_time']
        
        context = PerfContext(metrics)
        
        try:
            yield context
        finally:
            total_time = (time.time() - start_time) * 1000
            metrics['total_time'] = total_time
            self.metrics_history.append(metrics)
    
    def get_performance_summary(self, last_n: int = 10) -> Dict[str, Any]:
        """Get performance summary for recent queries"""
        if not self.metrics_history:
            return {"message": "No performance data available"}
        
        recent_metrics = self.metrics_history[-last_n:]
        
        total_times = [m['total_time'] for m in recent_metrics]
        preprocessing_times = [m.get('preprocessing_time', 0) for m in recent_metrics]
        llm_times = [m.get('llm_time', 0) for m in recent_metrics]
        
        return {
            'query_count': len(recent_metrics),
            'avg_total_time_ms': sum(total_times) / len(total_times),
            'avg_preprocessing_time_ms': sum(preprocessing_times) / len(preprocessing_times),
            'avg_llm_time_ms': sum(llm_times) / len(llm_times),
            'min_time_ms': min(total_times),
            'max_time_ms': max(total_times),
            'fast_queries': len([t for t in total_times if t < self.performance_thresholds['fast_query_ms']]),
            'slow_queries': len([t for t in total_times if t > self.performance_thresholds['slow_query_ms']])
        }


class OptimizedICEQuery:
    """Main query optimization orchestrator"""
    
    def __init__(self, ice_rag, cache_size: int = 1000, cache_ttl_hours: int = 24):
        self.ice_rag = ice_rag
        self.cache = QueryCache(cache_size, cache_ttl_hours)
        self.preprocessor = QueryPreprocessor()
        self.performance_monitor = PerformanceMonitor()
    
    def execute_optimized_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute optimized query with caching, preprocessing, and monitoring"""
        
        with self.performance_monitor.measure_performance() as perf_context:
            # 1. Check cache first
            cache_key = self.cache.generate_cache_key(query, kwargs)
            cached_result = self.cache.get(cache_key)
            
            if cached_result:
                cached_result['cache_hit'] = True
                cached_result['execution_time_ms'] = 0  # Cache hit
                return cached_result
            
            # 2. Query preprocessing and optimization
            perf_context.mark_preprocessing_complete()
            
            optimized_query = self.preprocessor.preprocess_query(query)
            complexity_analysis = self.preprocessor.estimate_complexity(optimized_query)
            optimized_kwargs = self._optimize_parameters(kwargs, complexity_analysis)
            
            # 3. Execute query with LLM
            perf_context.mark_llm_complete()
            
            result = self.ice_rag.query(optimized_query, **optimized_kwargs)
            
            # 4. Post-process and enhance result
            perf_context.mark_postprocessing_complete()
            
            enhanced_result = self._postprocess_result(result, complexity_analysis)
            enhanced_result['cache_hit'] = False
            enhanced_result['preprocessing'] = {
                'original_query': query,
                'optimized_query': optimized_query,
                'complexity_analysis': complexity_analysis
            }
            
            # 5. Cache the result
            self.cache.put(cache_key, enhanced_result)
            
            return enhanced_result
    
    def _optimize_parameters(self, kwargs: Dict, complexity_analysis: Dict) -> Dict:
        """Optimize parameters based on query complexity"""
        optimized = kwargs.copy()
        
        # Set hop count based on complexity
        if 'max_hops' not in optimized:
            optimized['max_hops'] = complexity_analysis['estimated_hops']
        
        # Set confidence threshold
        if 'confidence_threshold' not in optimized:
            # Higher complexity queries need lower thresholds for flexibility
            base_threshold = 0.7
            complexity_adjustment = (complexity_analysis['complexity_score'] - 1) * 0.05
            optimized['confidence_threshold'] = max(0.5, base_threshold - complexity_adjustment)
        
        # Set timeout based on complexity
        if 'timeout' not in optimized:
            optimized['timeout'] = complexity_analysis['recommended_timeout']
        
        return optimized
    
    def _postprocess_result(self, result: Dict, complexity_analysis: Dict) -> Dict:
        """Post-process and enhance query results"""
        enhanced_result = result.copy()
        
        # Add optimization metadata
        enhanced_result['optimization'] = {
            'complexity_score': complexity_analysis['complexity_score'],
            'estimated_hops': complexity_analysis['estimated_hops'],
            'performance_category': self._categorize_performance(
                enhanced_result.get('execution_time_ms', 0)
            )
        }
        
        # Enhance confidence scoring if available
        if 'confidence' in enhanced_result:
            enhanced_result['confidence_category'] = self._categorize_confidence(
                enhanced_result['confidence']
            )
        
        return enhanced_result
    
    def _categorize_performance(self, execution_time_ms: float) -> str:
        """Categorize query performance"""
        thresholds = self.performance_monitor.performance_thresholds
        
        if execution_time_ms < thresholds['fast_query_ms']:
            return 'fast'
        elif execution_time_ms < thresholds['acceptable_query_ms']:
            return 'acceptable'
        elif execution_time_ms < thresholds['slow_query_ms']:
            return 'slow'
        else:
            return 'very_slow'
    
    def _categorize_confidence(self, confidence: float) -> str:
        """Categorize confidence level"""
        if confidence >= 0.9:
            return 'very_high'
        elif confidence >= 0.8:
            return 'high'
        elif confidence >= 0.7:
            return 'medium'
        elif confidence >= 0.6:
            return 'low'
        else:
            return 'very_low'
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        return {
            'cache_stats': self.cache.stats(),
            'performance_stats': self.performance_monitor.get_performance_summary(),
            'query_count': len(self.performance_monitor.metrics_history)
        }
    
    def clear_cache(self):
        """Clear query cache"""
        self.cache.clear()
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.performance_monitor.metrics_history.clear()


def main():
    """Query optimization utility CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICE Query Optimization Utility')
    parser.add_argument('command', choices=['test', 'benchmark', 'analyze'],
                       help='Optimization command')
    parser.add_argument('--query', help='Query to test/analyze')
    parser.add_argument('--iterations', type=int, default=10,
                       help='Number of iterations for benchmarking')
    
    args = parser.parse_args()
    
    # Mock ICE RAG for testing
    class MockICERAG:
        def query(self, query, **kwargs):
            import random
            time.sleep(random.uniform(0.1, 0.5))  # Simulate processing time
            return {
                'answer': f'Mock answer for: {query}',
                'confidence': random.uniform(0.6, 0.95),
                'execution_time_ms': random.uniform(100, 2000)
            }
    
    mock_ice_rag = MockICERAG()
    optimizer = OptimizedICEQuery(mock_ice_rag)
    
    if args.command == 'test':
        test_query = args.query or "What are the key PE ratio risks for NVDA?"
        
        print(f"🔍 Testing query optimization: {test_query}")
        result = optimizer.execute_optimized_query(test_query)
        
        print(f"✅ Result: {result}")
        print(f"📊 Stats: {optimizer.get_optimization_stats()}")
    
    elif args.command == 'benchmark':
        test_queries = [
            "What are NVDA's key risks?",
            "How does PE ratio affect company valuation?",
            "Compare NVDA and AMD market performance",
            "What supply chain risks impact semiconductor companies through their suppliers?"
        ]
        
        print(f"🏁 Running benchmark with {args.iterations} iterations")
        
        for i in range(args.iterations):
            for query in test_queries:
                optimizer.execute_optimized_query(query)
            print(f"Completed iteration {i+1}/{args.iterations}")
        
        stats = optimizer.get_optimization_stats()
        print(f"📈 Final benchmark results:")
        print(json.dumps(stats, indent=2))
    
    elif args.command == 'analyze':
        if not args.query:
            print("❌ --query required for analyze command")
            return
        
        preprocessor = QueryPreprocessor()
        
        print(f"🔬 Analyzing query: {args.query}")
        
        # Preprocessing analysis
        optimized_query = preprocessor.preprocess_query(args.query)
        complexity = preprocessor.estimate_complexity(optimized_query)
        
        print(f"📝 Original: {args.query}")
        print(f"📝 Optimized: {optimized_query}")
        print(f"📊 Complexity analysis:")
        print(json.dumps(complexity, indent=2))


if __name__ == "__main__":
    main()