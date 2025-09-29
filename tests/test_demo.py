# tests/test_demo.py  
# Simple demonstration tests to validate test framework components
# Shows test fixtures, environment management, and basic functionality
# RELEVANT FILES: test_fixtures.py, conftest.py, pytest.ini

import os
import pytest
from test_fixtures import TestDataFixtures, TestEnvironmentManager, create_test_config


class TestFrameworkDemo:
    """Demonstration of test framework functionality"""
    
    def test_fixtures_loading(self):
        """Test that test fixtures load correctly"""
        fixtures = TestDataFixtures()
        
        # Verify documents loaded
        assert len(fixtures.test_documents) == 5
        assert "NVIDIA Q3 2024 Earnings Call" in fixtures.test_documents[0]["title"]
        
        # Verify edges loaded  
        assert len(fixtures.test_edges) == 11
        edge_types = [edge["edge_type"] for edge in fixtures.test_edges]
        assert "depends_on" in edge_types
        assert "located_in" in edge_types
        
        # Verify queries loaded
        assert len(fixtures.test_queries) == 9
        query_types = [query["type"] for query in fixtures.test_queries]
        assert "entity_analysis" in query_types
        assert "multi_hop_analysis" in query_types
    
    def test_environment_management(self):
        """Test environment manager creates and cleans directories"""
        manager = TestEnvironmentManager()
        
        # Create test environment
        test_env = manager.create_test_environment("demo")
        assert os.path.exists(test_env)
        assert os.path.isdir(test_env)
        
        # Verify subdirectories created
        storage_dir = os.path.join(test_env, "storage")
        cache_dir = os.path.join(test_env, "cache")
        assert os.path.exists(storage_dir)
        assert os.path.exists(cache_dir)
        
        # Cleanup
        manager.cleanup_environment("demo")
        assert not os.path.exists(test_env)
    
    def test_config_creation(self):
        """Test configuration creation with defaults"""
        config = create_test_config()
        
        # Verify required config keys
        assert "test_timeout" in config
        assert "max_retries" in config
        assert "performance_benchmarks" in config
        
        # Verify performance benchmarks structure
        benchmarks = config["performance_benchmarks"]
        assert "max_query_time" in benchmarks
        assert "max_document_processing_time" in benchmarks
        assert benchmarks["max_query_time"] > 0
    
    def test_sample_data_quality(self):
        """Test quality of sample test data"""
        fixtures = TestDataFixtures()
        
        # Test document content quality
        doc = fixtures.get_sample_document("earnings_transcript")
        assert "revenue" in doc["text"].lower()
        assert "data center" in doc["text"].lower()
        
        # Test edge relationship structure
        edge = fixtures.get_sample_edges(1)[0]
        assert len(edge) >= 4  # Should have multiple fields
        assert isinstance(edge["weight"], float)  # weight should be float
        assert 0.0 <= edge["weight"] <= 1.0  # weight should be normalized
    
    def test_query_validation(self):
        """Test query validation functionality"""
        fixtures = TestDataFixtures()
        
        # Test simple query response validation
        mock_response = {
            "status": "success",
            "result": "NVDA depends on TSMC for chip manufacturing. This dependency creates significant supply chain risk as TSMC is the primary supplier for NVIDIA's advanced GPUs. The relationship is critical for NVIDIA's data center business, which relies heavily on cutting-edge 4nm and 3nm process technology that only TSMC can provide at scale.",
            "query_time": 2.5,
            "entities_found": ["NVDA", "TSMC"],
            "confidence": 0.85
        }
        
        issues = fixtures.validate_response(mock_response, "entity_analysis")
        assert len(issues) == 0  # Should pass validation
        
        # Test response with missing required fields
        incomplete_response = {"status": "success"}  # Missing result
        issues = fixtures.validate_response(incomplete_response, "entity_analysis")
        assert len(issues) > 0  # Should fail validation


@pytest.mark.performance
class TestPerformanceValidation:
    """Performance-related test demonstrations"""
    
    def test_fixtures_loading_speed(self):
        """Test that fixtures load within reasonable time"""
        import time
        
        start_time = time.time()
        fixtures = TestDataFixtures()
        load_time = time.time() - start_time
        
        # Should load fixtures quickly
        assert load_time < 1.0, f"Fixtures took too long to load: {load_time:.2f}s"
    
    def test_environment_creation_speed(self):
        """Test environment creation performance"""
        import time
        
        manager = TestEnvironmentManager()
        
        start_time = time.time()
        test_env = manager.create_test_environment("perf_test")
        create_time = time.time() - start_time
        
        # Cleanup
        manager.cleanup_environment("perf_test")
        
        # Should create environment quickly
        assert create_time < 0.5, f"Environment creation too slow: {create_time:.2f}s"


# Test functions for pytest compatibility
def test_framework_components():
    """Pytest-compatible test function"""
    demo = TestFrameworkDemo()
    demo.test_fixtures_loading()
    demo.test_environment_management() 
    demo.test_config_creation()
    demo.test_sample_data_quality()
    demo.test_query_validation()


def test_performance_components():
    """Pytest-compatible performance test function"""
    perf = TestPerformanceValidation()
    perf.test_fixtures_loading_speed()
    perf.test_environment_creation_speed()