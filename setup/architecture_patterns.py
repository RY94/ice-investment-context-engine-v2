# setup/architecture_patterns.py  
# Code architecture patterns and advanced design examples for ICE system
# Demonstrates dependency injection, error handling, and testing patterns
# RELEVANT FILES: CLAUDE.md, ice_lightrag/ice_rag.py, setup/development_workflows.py

import time
import tempfile
import shutil
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch
from dataclasses import dataclass


class ICEException(Exception):
    """Enhanced exception class with context preservation and recovery suggestions"""
    
    def __init__(self, message: str, context: Optional[Dict] = None, 
                 recovery_suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.context = context or {}
        self.recovery_suggestions = recovery_suggestions or []
        
    def __str__(self):
        base_msg = super().__str__()
        if self.recovery_suggestions:
            suggestions = '\n'.join([f"  • {s}" for s in self.recovery_suggestions])
            return f"{base_msg}\n\nRecovery suggestions:\n{suggestions}"
        return base_msg


class DependencyInjectionPatterns:
    """Examples of dependency injection patterns for ICE system"""
    
    @staticmethod
    def enhanced_ice_lightrag_example():
        """
        Example of ICELightRAG with dependency injection for testability
        This pattern allows mocking components for unit testing
        """
        
        class ICELightRAG:
            def __init__(self, working_dir="./storage", 
                         vector_db=None, graph_engine=None, llm_client=None):
                # Allow injection of dependencies for testing
                self.working_dir = working_dir
                self.vector_db = vector_db or self._init_default_vector_db()
                self.graph_engine = graph_engine or self._init_default_graph_engine()
                self.llm_client = llm_client or self._init_default_llm_client()
                
            def _init_default_vector_db(self):
                # Default ChromaDB implementation
                print("Initializing default ChromaDB vector database")
                return "ChromaDB_instance"
                
            def _init_default_graph_engine(self):
                # Default NetworkX implementation  
                print("Initializing default NetworkX graph engine")
                return "NetworkX_instance"
                
            def _init_default_llm_client(self):
                # Default OpenAI client
                print("Initializing default OpenAI LLM client")
                return "OpenAI_client_instance"
            
            def query(self, query_text: str) -> Dict[str, Any]:
                return {
                    "answer": f"Mock answer for: {query_text}",
                    "vector_db": str(self.vector_db),
                    "graph_engine": str(self.graph_engine),
                    "llm_client": str(self.llm_client)
                }
        
        # Usage examples
        print("=== Dependency Injection Examples ===")
        
        # Standard usage with defaults
        print("\n1. Standard usage:")
        ice_standard = ICELightRAG()
        result = ice_standard.query("Test query")
        print(f"Result: {result}")
        
        # Testing usage with mocked dependencies
        print("\n2. Testing usage with mocks:")
        mock_vector_db = Mock()
        mock_graph_engine = Mock()
        mock_llm_client = Mock()
        
        ice_test = ICELightRAG(
            vector_db=mock_vector_db,
            graph_engine=mock_graph_engine,
            llm_client=mock_llm_client
        )
        
        test_result = ice_test.query("Test query")
        print(f"Test result: {test_result}")


class ErrorHandlingPatterns:
    """Advanced error handling patterns with context and recovery suggestions"""
    
    @staticmethod
    def robust_query_processing_example():
        """Example of robust query processing with detailed error context"""
        
        def get_graph_state_summary() -> Dict[str, Any]:
            """Mock function to get graph state"""
            return {
                "entity_count": 1500,
                "relationship_count": 3200,
                "last_update": time.time()
            }
        
        def process_query(query: str, **kwargs) -> Dict[str, Any]:
            """Mock query processing function that might fail"""
            if "fail" in query.lower():
                raise Exception("Simulated query processing failure")
            return {"answer": f"Processed: {query}", "confidence": 0.85}
        
        def robust_query_processing(query: str, **kwargs) -> Dict[str, Any]:
            """Robust query processing with comprehensive error handling"""
            try:
                return process_query(query, **kwargs)
            except Exception as e:
                context = {
                    'query': query,
                    'kwargs': kwargs,
                    'timestamp': time.time(),
                    'graph_state': get_graph_state_summary()
                }
                suggestions = [
                    "Check if OpenAI API key is valid",
                    "Verify LightRAG storage directory exists", 
                    "Ensure graph has sufficient entities for query",
                    "Try reducing query complexity or hop count"
                ]
                raise ICEException(f"Query processing failed: {str(e)}", 
                                  context=context, recovery_suggestions=suggestions)
        
        # Usage examples
        print("=== Error Handling Examples ===")
        
        # Successful query
        try:
            print("\n1. Successful query:")
            result = robust_query_processing("What are NVDA's risks?")
            print(f"Success: {result}")
        except ICEException as e:
            print(f"Error: {e}")
        
        # Failed query with detailed error info
        try:
            print("\n2. Failed query with error context:")
            result = robust_query_processing("This query will fail")
        except ICEException as e:
            print(f"Detailed error: {e}")
            print(f"Error context: {e.context}")


class TestingPatterns:
    """Advanced testing patterns for ICE system components"""
    
    @staticmethod
    def advanced_testing_example():
        """Example of advanced testing patterns with fixtures and parametrization"""
        
        # Mock pytest functionality for demonstration
        class MockPytest:
            @staticmethod
            def fixture(func):
                return func
            
            @staticmethod
            def mark_parametrize(params, values):
                def decorator(func):
                    func._params = (params, values)
                    return func
                return decorator
        
        pytest = MockPytest()
        
        class TestICEAdvanced:
            @pytest.fixture
            def isolated_ice_instance(self):
                """Create ICE instance with temporary storage for testing"""
                temp_dir = tempfile.mkdtemp()
                print(f"Created temporary directory: {temp_dir}")
                
                # Mock ICELightRAG for this example
                class MockICELightRAG:
                    def __init__(self, working_dir):
                        self.working_dir = working_dir
                    
                    def query(self, query, max_hops=3):
                        return {
                            'hop_count': min(max_hops, len(query.split())),
                            'confidence': 0.8,
                            'answer': f"Mock answer for: {query}"
                        }
                
                ice_rag = MockICELightRAG(working_dir=temp_dir)
                
                # In real implementation, this would be:
                # yield ice_rag
                # shutil.rmtree(temp_dir)
                
                return ice_rag
            
            @pytest.mark_parametrize("query,expected_hops", [
                ("Direct supplier relationship", 1),
                ("Multi-step causal chain", 2), 
                ("Complex reasoning path", 3)
            ])
            def test_query_hop_patterns(self, isolated_ice_instance, query, expected_hops):
                """Test query processing with different hop patterns"""
                result = isolated_ice_instance.query(query, max_hops=expected_hops)
                
                # Mock assertions
                hop_count = result['hop_count']
                confidence = result['confidence']
                
                print(f"Testing: {query}")
                print(f"  Expected hops: {expected_hops}, Actual: {hop_count}")
                print(f"  Confidence: {confidence}")
                
                assert hop_count <= expected_hops, f"Hop count {hop_count} exceeds limit {expected_hops}"
                assert confidence >= 0.7, f"Confidence {confidence} below threshold"
                
                return True
            
            def test_api_failure_recovery(self, isolated_ice_instance):
                """Test graceful degradation when APIs fail"""
                
                # Mock the API failure scenario
                def mock_failing_query(query):
                    raise Exception("API Error")
                
                # In real implementation, this would use @patch
                print("Testing API failure recovery...")
                
                try:
                    # This would normally trigger the exception
                    mock_failing_query("Test query")
                except Exception as e:
                    # Verify proper error handling
                    error_msg = str(e)
                    print(f"Caught expected error: {error_msg}")
                    
                    # In real test, would check ICEException properties
                    assert "API Error" in error_msg
                    return True
        
        # Run example tests
        print("=== Advanced Testing Examples ===")
        
        test_instance = TestICEAdvanced()
        ice_mock = test_instance.isolated_ice_instance()
        
        # Test different query patterns
        test_cases = [
            ("Direct supplier relationship", 1),
            ("Multi-step causal chain", 2),
            ("Complex reasoning path", 3)
        ]
        
        for query, expected_hops in test_cases:
            test_instance.test_query_hop_patterns(ice_mock, query, expected_hops)
        
        # Test API failure recovery
        test_instance.test_api_failure_recovery(ice_mock)


class PerformancePatterns:
    """Performance optimization and monitoring patterns"""
    
    @staticmethod
    def query_optimization_example():
        """Example of query optimization with caching and preprocessing"""
        
        class OptimizedICEQuery:
            def __init__(self):
                self.query_cache = {}
                
            def execute_optimized_query(self, query: str, **kwargs) -> Dict[str, Any]:
                print(f"Processing optimized query: {query}")
                
                # 1. Check cache first
                cache_key = self._generate_cache_key(query, kwargs)
                if cache_key in self.query_cache:
                    cached_result = self.query_cache[cache_key]
                    if self._is_cache_valid(cached_result):
                        print("  ✅ Cache hit")
                        return cached_result['result']
                
                # 2. Query preprocessing and optimization
                optimized_query = self._preprocess_query(query)
                optimized_kwargs = self._optimize_parameters(kwargs)
                
                # 3. Execute with performance monitoring
                start_time = time.time()
                result = self._execute_query(optimized_query, **optimized_kwargs)
                execution_time = (time.time() - start_time) * 1000
                
                # 4. Post-process and cache result
                processed_result = {
                    'result': result,
                    'execution_time_ms': execution_time,
                    'cache_key': cache_key
                }
                self._cache_result(cache_key, processed_result)
                
                print(f"  Executed in {execution_time:.2f}ms")
                return processed_result
            
            def _generate_cache_key(self, query: str, kwargs: Dict) -> str:
                import hashlib
                combined = f"{query}_{sorted(kwargs.items())}"
                return hashlib.md5(combined.encode()).hexdigest()[:16]
            
            def _is_cache_valid(self, cached_result: Dict) -> bool:
                # Simple TTL check (1 hour)
                cache_age = time.time() - cached_result.get('timestamp', 0)
                return cache_age < 3600
            
            def _preprocess_query(self, query: str) -> str:
                """Optimize query text"""
                query = query.strip()
                
                # Expand financial abbreviations
                abbreviations = {
                    'PE': 'price to earnings ratio',
                    'ROE': 'return on equity',
                    'EBITDA': 'earnings before interest taxes depreciation amortization',
                    'FCF': 'free cash flow'
                }
                
                for abbr, expansion in abbreviations.items():
                    query = query.replace(abbr, expansion)
                
                print(f"  Preprocessed query: {query}")
                return query
            
            def _optimize_parameters(self, kwargs: Dict) -> Dict:
                """Optimize parameters based on query characteristics"""
                optimized = kwargs.copy()
                
                # Set defaults if not provided
                if 'max_hops' not in optimized:
                    optimized['max_hops'] = 2  # Conservative default
                if 'confidence_threshold' not in optimized:
                    optimized['confidence_threshold'] = 0.7
                    
                return optimized
            
            def _execute_query(self, query: str, **kwargs) -> Dict[str, Any]:
                """Mock query execution"""
                # Simulate processing time
                time.sleep(0.1)
                return {
                    "answer": f"Optimized answer for: {query}",
                    "confidence": kwargs.get('confidence_threshold', 0.7),
                    "hops_used": kwargs.get('max_hops', 2)
                }
            
            def _cache_result(self, cache_key: str, result: Dict):
                """Cache the result with timestamp"""
                result['timestamp'] = time.time()
                self.query_cache[cache_key] = result
                print(f"  Cached result with key: {cache_key}")
        
        # Usage example
        print("=== Query Optimization Example ===")
        
        optimizer = OptimizedICEQuery()
        
        # First query - cache miss
        result1 = optimizer.execute_optimized_query(
            "What are NVDA's PE ratio risks?",
            max_hops=3
        )
        
        # Second query - cache hit
        result2 = optimizer.execute_optimized_query(
            "What are NVDA's PE ratio risks?", 
            max_hops=3
        )


def main():
    """Run all architecture pattern examples"""
    print("🏗️  ICE Architecture Patterns Examples")
    print("=" * 50)
    
    # Run all examples
    DependencyInjectionPatterns.enhanced_ice_lightrag_example()
    ErrorHandlingPatterns.robust_query_processing_example()
    TestingPatterns.advanced_testing_example()
    PerformancePatterns.query_optimization_example()
    
    print("\n✅ All architecture pattern examples completed")


if __name__ == "__main__":
    main()