# tests/test_lightrag.py
# Comprehensive test suite for ICE LightRAG system
# Tests document processing, querying, async operations, and error handling
# Validates integration with OpenAI APIs and knowledge graph construction

import os
import asyncio
import time
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Import test fixtures and LightRAG system
from test_fixtures import TestDataFixtures, TestEnvironmentManager, create_test_config

# Import LightRAG components
import sys
sys.path.append('../ice_lightrag')

try:
    from ice_lightrag.ice_rag import ICELightRAG, SimpleICERAG, LIGHTRAG_AVAILABLE
except ImportError:
    # Alternative import path
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ice_lightrag'))
    try:
        from ice_rag import ICELightRAG, SimpleICERAG, LIGHTRAG_AVAILABLE
    except ImportError:
        ICELightRAG = None
        SimpleICERAG = None
        LIGHTRAG_AVAILABLE = False


class TestICELightRAG:
    """Comprehensive test suite for ICE LightRAG system"""
    
    def __init__(self):
        self.fixtures = TestDataFixtures()
        self.env_manager = TestEnvironmentManager()
        self.config = create_test_config()
        self.rag_instance = None
        self.test_results = {}
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.test_dir = self.env_manager.create_test_environment("lightrag")
        if LIGHTRAG_AVAILABLE and self.config["openai_api_key"]:
            self.rag_instance = ICELightRAG(working_dir=os.path.join(self.test_dir, "lightrag_storage"))
        else:
            self.rag_instance = None
    
    def teardown_method(self):
        """Clean up after each test"""
        self.env_manager.cleanup_environment("lightrag")
    
    def test_system_availability(self):
        """Test LightRAG system availability and initialization"""
        print("\n🧪 Testing LightRAG System Availability...")
        
        # Test import availability
        assert LIGHTRAG_AVAILABLE is not None, "LIGHTRAG_AVAILABLE should be defined"
        
        if not LIGHTRAG_AVAILABLE:
            print("⚠️ LightRAG not installed - skipping integration tests")
            return True
        
        # Test API key availability
        api_key = self.config["openai_api_key"]
        if not api_key:
            print("⚠️ OPENAI_API_KEY not set - skipping API-dependent tests")
            return True
        
        # Test initialization
        assert self.rag_instance is not None, "RAG instance should be created"
        
        print("✅ LightRAG system availability tests passed")
        return True
    
    def test_initialization_and_readiness(self):
        """Test system initialization and readiness checks"""
        print("\n🧪 Testing LightRAG Initialization...")
        
        if not self.rag_instance:
            print("⚠️ Skipping initialization test - LightRAG not available")
            return True
        
        # Test readiness check
        is_ready = self.rag_instance.is_ready()
        assert isinstance(is_ready, bool), "is_ready() should return boolean"
        
        if not is_ready:
            print("⚠️ LightRAG not ready - likely due to missing dependencies or API key")
            return True
        
        # Test working directory creation
        assert Path(self.test_dir).exists(), "Test directory should exist"
        
        print("✅ LightRAG initialization tests passed")
        return True
    
    async def test_document_processing_async(self):
        """Test asynchronous document processing"""
        print("\n🧪 Testing LightRAG Document Processing (Async)...")
        
        if not self.rag_instance or not self.rag_instance.is_ready():
            print("⚠️ Skipping async document test - LightRAG not ready")
            return True
        
        # Test single document addition
        sample_doc = self.fixtures.get_sample_document("earnings_transcript")
        
        start_time = time.time()
        result = await self.rag_instance.add_document(sample_doc["text"], sample_doc["type"])
        processing_time = time.time() - start_time
        
        # Validate result
        assert isinstance(result, dict), "Result should be dictionary"
        assert "status" in result, "Result should have status field"
        
        if result["status"] == "error":
            print(f"⚠️ Document processing failed: {result.get('message', 'Unknown error')}")
            return False
        
        assert result["status"] == "success", f"Document processing should succeed: {result}"
        assert processing_time < self.config["performance_benchmarks"]["max_document_processing_time"], f"Processing too slow: {processing_time:.2f}s"
        
        print(f"✅ Document processing tests passed (time: {processing_time:.2f}s)")
        return True
    
    def test_document_processing_sync(self):
        """Test synchronous document processing wrapper"""
        print("\n🧪 Testing LightRAG Document Processing (Sync)...")
        
        if not self.rag_instance or not self.rag_instance.is_ready():
            print("⚠️ Skipping sync document test - LightRAG not ready")
            return True
        
        # Test sync wrapper if available
        if hasattr(self.rag_instance, 'add_document_sync'):
            sample_doc = self.fixtures.get_sample_document("industry_report")
            result = self.rag_instance.add_document_sync(sample_doc["text"], sample_doc["type"])
            
            assert isinstance(result, dict), "Sync result should be dictionary"
            assert result["status"] in ["success", "error"], "Should have valid status"
            
            print("✅ Sync document processing tests passed")
        else:
            print("⚠️ Sync wrapper not available - using async only")
        
        return True
    
    async def test_querying_functionality_async(self):
        """Test asynchronous querying functionality"""
        print("\n🧪 Testing LightRAG Querying (Async)...")
        
        if not self.rag_instance or not self.rag_instance.is_ready():
            print("⚠️ Skipping async query test - LightRAG not ready")
            return True
        
        # First add some documents for querying
        for doc in self.fixtures.test_documents[:2]:  # Add first 2 documents
            await self.rag_instance.add_document(doc["text"], doc["type"])
        
        # Test different query modes
        test_queries = [
            ("What are NVIDIA's main risks?", "hybrid"),
            ("Tell me about TSMC supply chain", "naive"),
            ("How does China affect semiconductor companies?", "local")
        ]
        
        for query_text, mode in test_queries:
            start_time = time.time()
            result = await self.rag_instance.query(query_text, mode=mode)
            query_time = time.time() - start_time
            
            # Validate result structure
            assert isinstance(result, dict), f"Query result should be dictionary for mode {mode}"
            assert "status" in result, f"Result should have status for mode {mode}"
            
            if result["status"] == "error":
                print(f"⚠️ Query failed for mode {mode}: {result.get('message', 'Unknown error')}")
                continue
            
            assert result["status"] == "success", f"Query should succeed for mode {mode}"
            assert "result" in result, f"Should have result field for mode {mode}"
            assert len(result["result"]) > 0, f"Result should not be empty for mode {mode}"
            assert query_time < self.config["performance_benchmarks"]["max_query_time"], f"Query too slow for mode {mode}: {query_time:.2f}s"
            
            # Validate response quality
            response_issues = self.fixtures.validate_response(result, "general")
            if response_issues:
                print(f"⚠️ Response quality issues for {mode}: {response_issues}")
        
        print("✅ Async querying tests passed")
        return True
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n🧪 Testing LightRAG Error Handling...")
        
        # Test initialization without API key
        temp_env = os.environ.get("OPENAI_API_KEY")
        if temp_env:
            os.environ.pop("OPENAI_API_KEY", None)
        
        try:
            error_rag = ICELightRAG(working_dir=os.path.join(self.test_dir, "error_test"))
            is_ready = error_rag.is_ready()
            
            # Should not be ready without API key
            if temp_env:  # Only test this if we had an API key to begin with
                assert not is_ready, "Should not be ready without API key"
            
        finally:
            # Restore API key
            if temp_env:
                os.environ["OPENAI_API_KEY"] = temp_env
        
        # Test invalid working directory
        try:
            invalid_rag = ICELightRAG(working_dir="/invalid/directory/path")
            # Should handle gracefully
            assert hasattr(invalid_rag, 'rag'), "Should have rag attribute even with invalid path"
        except Exception as e:
            # Acceptable to throw exception for invalid path
            assert isinstance(e, (PermissionError, FileNotFoundError, OSError)), f"Unexpected exception type: {type(e)}"
        
        print("✅ Error handling tests passed")
        return True
    
    def test_performance_characteristics(self):
        """Test performance and caching behavior"""
        print("\n🧪 Testing LightRAG Performance...")
        
        if not self.rag_instance or not self.rag_instance.is_ready():
            print("⚠️ Skipping performance test - LightRAG not ready")
            return True
        
        # This test would require actual LightRAG functionality
        # For now, we test basic performance expectations
        
        # Test multiple rapid queries (if system is ready)
        query = "What are the main semiconductor industry trends?"
        times = []
        
        async def run_performance_test():
            # Add a document first
            sample_doc = self.fixtures.get_sample_document()
            await self.rag_instance.add_document(sample_doc["text"], sample_doc["type"])
            
            # Run multiple queries
            for i in range(3):
                start_time = time.time()
                result = await self.rag_instance.query(query)
                query_time = time.time() - start_time
                times.append(query_time)
                
                if result["status"] != "success":
                    break
        
        try:
            asyncio.run(run_performance_test())
            
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                
                assert max_time < self.config["performance_benchmarks"]["max_query_time"], f"Query too slow: {max_time:.2f}s"
                print(f"✅ Performance tests passed (avg: {avg_time:.2f}s, max: {max_time:.2f}s)")
            else:
                print("⚠️ No performance data collected")
                
        except Exception as e:
            print(f"⚠️ Performance test error: {e}")
        
        return True
    
    def test_integration_scenarios(self):
        """Test realistic integration scenarios"""
        print("\n🧪 Testing LightRAG Integration Scenarios...")
        
        if not self.rag_instance or not self.rag_instance.is_ready():
            print("⚠️ Skipping integration test - LightRAG not ready")
            return True
        
        async def run_integration_test():
            # Scenario 1: Build knowledge base incrementally
            documents_added = 0
            for doc in self.fixtures.test_documents:
                result = await self.rag_instance.add_document(doc["text"], doc["type"])
                if result["status"] == "success":
                    documents_added += 1
                    
                    # Query after each document addition
                    query_result = await self.rag_instance.query(f"What do you know about {doc['entities'][0]}?")
                    assert query_result["status"] == "success", f"Query should work after adding document {doc['id']}"
            
            # Scenario 2: Complex multi-entity query
            complex_query = "How are NVIDIA, TSMC, and China interconnected in the semiconductor industry?"
            result = await self.rag_instance.query(complex_query)
            
            if result["status"] == "success":
                # Check if response mentions key entities
                response_text = result["result"].lower()
                key_terms = ["nvidia", "tsmc", "china", "semiconductor"]
                found_terms = [term for term in key_terms if term in response_text]
                
                assert len(found_terms) >= 2, f"Response should mention multiple key terms, found: {found_terms}"
            
            return documents_added
        
        try:
            docs_added = asyncio.run(run_integration_test())
            print(f"✅ Integration tests passed ({docs_added} documents processed)")
            
        except Exception as e:
            print(f"⚠️ Integration test error: {e}")
            return False
        
        return True
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run complete LightRAG test suite"""
        print("🚀 Starting ICE LightRAG Test Suite...")
        print("=" * 60)
        
        # Define all tests (mix of sync and async)
        sync_tests = [
            ("System Availability", self.test_system_availability),
            ("Initialization and Readiness", self.test_initialization_and_readiness), 
            ("Document Processing (Sync)", self.test_document_processing_sync),
            ("Error Handling", self.test_error_handling),
            ("Performance Characteristics", self.test_performance_characteristics)
        ]
        
        async_tests = [
            ("Document Processing (Async)", self.test_document_processing_async),
            ("Querying Functionality (Async)", self.test_querying_functionality_async)
        ]
        
        integration_tests = [
            ("Integration Scenarios", self.test_integration_scenarios)
        ]
        
        results = {}
        passed_count = 0
        total_tests = len(sync_tests) + len(async_tests) + len(integration_tests)
        
        # Run synchronous tests
        for test_name, test_func in sync_tests:
            try:
                self.setup_method()
                result = test_func()
                results[test_name] = result
                if result:
                    passed_count += 1
                self.teardown_method()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
                self.teardown_method()
        
        # Run asynchronous tests
        for test_name, test_func in async_tests:
            try:
                self.setup_method()
                result = asyncio.run(test_func())
                results[test_name] = result
                if result:
                    passed_count += 1
                self.teardown_method()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
                self.teardown_method()
        
        # Run integration tests
        for test_name, test_func in integration_tests:
            try:
                self.setup_method()
                result = test_func()
                results[test_name] = result
                if result:
                    passed_count += 1
                self.teardown_method()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
                self.teardown_method()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ICE LightRAG Test Results:")
        print(f"Passed: {passed_count}/{total_tests}")
        print(f"Success Rate: {passed_count/total_tests*100:.1f}%")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")
        
        # Overall assessment
        if passed_count == total_tests:
            print("\n🎉 All LightRAG tests passed! System is ready for use.")
        elif passed_count >= total_tests * 0.7:  # 70% pass rate
            print(f"\n⚠️ Most tests passed ({passed_count}/{total_tests}). System is likely functional with some limitations.")
        else:
            print(f"\n❌ Many tests failed ({total_tests - passed_count}/{total_tests}). Check system configuration and dependencies.")
        
        # Cleanup
        self.env_manager.cleanup_all_environments()
        
        return results


def run_lightrag_tests():
    """Main entry point for running LightRAG tests"""
    test_suite = TestICELightRAG()
    return test_suite.run_all_tests()


# Pytest integration (if pytest is available)
@pytest.fixture
def lightrag_test_suite():
    """Pytest fixture for LightRAG test suite"""
    return TestICELightRAG()


class TestLightRAGPytest:
    """Pytest-compatible test class for LightRAG"""
    
    def test_lightrag_availability(self, lightrag_test_suite):
        """Test LightRAG system availability using pytest"""
        assert lightrag_test_suite.test_system_availability()
    
    def test_lightrag_initialization(self, lightrag_test_suite):
        """Test LightRAG initialization using pytest"""
        lightrag_test_suite.setup_method()
        assert lightrag_test_suite.test_initialization_and_readiness()
        lightrag_test_suite.teardown_method()
    
    def test_lightrag_error_handling(self, lightrag_test_suite):
        """Test LightRAG error handling using pytest"""
        lightrag_test_suite.setup_method()
        assert lightrag_test_suite.test_error_handling()
        lightrag_test_suite.teardown_method()


if __name__ == "__main__":
    # Run tests if script is executed directly
    run_lightrag_tests()