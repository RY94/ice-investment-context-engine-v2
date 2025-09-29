# tests/conftest.py
# Pytest configuration and shared fixtures for ICE RAG testing
# Provides common test utilities, environment setup, and configuration
# Enables consistent testing across all test modules

import os
import sys
import pytest
import tempfile
import shutil
import traceback
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_fixtures import TestDataFixtures, TestEnvironmentManager, create_test_config


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Session-wide test configuration"""
    return create_test_config()


@pytest.fixture(scope="session") 
def test_fixtures() -> TestDataFixtures:
    """Session-wide test data fixtures"""
    return TestDataFixtures()


@pytest.fixture(scope="function")
def test_environment() -> Generator[str, None, None]:
    """Function-scoped test environment with cleanup"""
    temp_dir = tempfile.mkdtemp(prefix="ice_pytest_")
    
    # Create subdirectories
    (Path(temp_dir) / "storage").mkdir(exist_ok=True)
    (Path(temp_dir) / "cache").mkdir(exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="class")
def class_test_environment() -> Generator[str, None, None]:
    """Class-scoped test environment for sharing between test methods"""
    temp_dir = tempfile.mkdtemp(prefix="ice_pytest_class_")
    
    # Create subdirectories
    (Path(temp_dir) / "storage").mkdir(exist_ok=True)
    (Path(temp_dir) / "cache").mkdir(exist_ok=True)
    (Path(temp_dir) / "lightrag").mkdir(exist_ok=True)
    (Path(temp_dir) / "lazyrag").mkdir(exist_ok=True)
    (Path(temp_dir) / "unified").mkdir(exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def environment_manager() -> Generator[TestEnvironmentManager, None, None]:
    """Session-wide environment manager"""
    manager = TestEnvironmentManager()
    yield manager
    manager.cleanup_all_environments()


@pytest.fixture
def api_key_available() -> bool:
    """Check if OpenAI API key is available"""
    return bool(os.getenv("OPENAI_API_KEY"))


@pytest.fixture
def mock_api_key() -> Generator[str, None, None]:
    """Provide mock API key for testing without real API calls"""
    original_key = os.environ.get("OPENAI_API_KEY")
    mock_key = "sk-mock-key-for-testing-1234567890"
    
    os.environ["OPENAI_API_KEY"] = mock_key
    yield mock_key
    
    # Restore original key
    if original_key:
        os.environ["OPENAI_API_KEY"] = original_key
    else:
        os.environ.pop("OPENAI_API_KEY", None)


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "lightrag: mark test as LightRAG specific")
    config.addinivalue_line("markers", "lazygraphrag: mark test as LazyGraphRAG specific")
    config.addinivalue_line("markers", "unified: mark test as Unified RAG specific")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_api_key: mark test as requiring OpenAI API key")
    config.addinivalue_line("markers", "requires_dependencies: mark test as requiring specific dependencies")


# Skip conditions for different test types
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Skip API-dependent tests if no API key
    if not api_key:
        skip_api = pytest.mark.skip(reason="OPENAI_API_KEY not set")
        for item in items:
            if "requires_api_key" in item.keywords:
                item.add_marker(skip_api)
    
    # Check for component availability
    try:
        import lightrag
        lightrag_available = True
    except ImportError:
        lightrag_available = False
    
    if not lightrag_available:
        skip_lightrag = pytest.mark.skip(reason="LightRAG not installed")
        for item in items:
            if "lightrag" in item.keywords:
                item.add_marker(skip_lightrag)
    
    # Check LazyGraphRAG availability
    try:
        sys.path.append(str(Path(__file__).parent.parent / "ice_lazyrag"))
        from lazy_rag import SimpleLazyRAG
        lazyrag_available = True
    except ImportError:
        lazyrag_available = False
    
    if not lazyrag_available:
        skip_lazyrag = pytest.mark.skip(reason="LazyGraphRAG not available")
        for item in items:
            if "lazygraphrag" in item.keywords:
                item.add_marker(skip_lazyrag)


# Custom pytest fixtures for specific test needs
@pytest.fixture
def sample_documents(test_fixtures):
    """Provide sample documents for testing"""
    return test_fixtures.test_documents


@pytest.fixture
def sample_edges(test_fixtures):
    """Provide sample edges for graph testing"""
    return test_fixtures.test_edges


@pytest.fixture
def sample_queries(test_fixtures):
    """Provide sample queries for testing"""
    return test_fixtures.test_queries


@pytest.fixture
def performance_benchmarks(test_config):
    """Provide performance benchmark expectations"""
    return test_config["performance_benchmarks"]


# Utility fixtures for common test patterns
@pytest.fixture
def assert_response_quality(test_fixtures):
    """Fixture providing response quality assertion function"""
    def _assert_quality(response: Dict[str, Any], query_type: str = "general"):
        """Assert response meets quality standards"""
        issues = test_fixtures.validate_response(response, query_type)
        if issues:
            pytest.fail(f"Response quality issues: {issues}")
        return True
    
    return _assert_quality


@pytest.fixture
def assert_performance(performance_benchmarks):
    """Fixture providing performance assertion function"""
    def _assert_performance(actual_time: float, operation_type: str = "max_query_time"):
        """Assert operation meets performance expectations"""
        max_time = performance_benchmarks.get(operation_type, 10.0)
        assert actual_time < max_time, f"Operation too slow: {actual_time:.2f}s > {max_time}s"
        return True
    
    return _assert_performance


# Test reporting fixtures
@pytest.fixture(autouse=True)
def test_timing(request):
    """Automatically time all tests"""
    import time
    start_time = time.time()
    
    def fin():
        duration = time.time() - start_time
        # Add timing info to test metadata
        if hasattr(request.node, 'rep_call'):
            request.node.rep_call.duration = duration
    
    request.addfinalizer(fin)


# Error handling and debugging fixtures
@pytest.fixture
def debug_mode():
    """Check if running in debug mode"""
    return os.getenv("ICE_DEBUG", "").lower() in ["1", "true", "yes"]


@pytest.fixture
def capture_errors():
    """Fixture to capture and analyze errors during testing"""
    errors = []
    
    def _capture_error(error: Exception, context: str = ""):
        """Capture error with context"""
        errors.append({
            "error": error,
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "traceback": traceback.format_exc() if hasattr(error, '__traceback__') else None
        })
    
    return _capture_error, errors


# Session-wide reporting hooks
def pytest_sessionstart(session):
    """Called after the Session object has been created"""
    print("\n🚀 Starting ICE RAG Systems Test Session")
    print("=" * 60)
    
    # Environment info
    print(f"Python: {sys.version.split()[0]}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"API Key: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not Set'}")


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    print("\n" + "=" * 60)
    print("🏁 Test Session Complete")
    
    # Summary based on exit status
    if exitstatus == 0:
        print("✅ All tests passed successfully!")
    elif exitstatus == 1:
        print("⚠️ Some tests failed - check results above")
    elif exitstatus == 2:
        print("❌ Test execution interrupted or configuration error")
    else:
        print(f"⚠️ Test session ended with exit status: {exitstatus}")


# Test result reporting
def pytest_runtest_logreport(report):
    """Called for each test report"""
    if report.when == "call":
        # Add custom reporting logic here if needed
        pass


# Custom assertion helpers
class ICETestHelpers:
    """Collection of test helper methods"""
    
    @staticmethod
    def assert_dict_structure(actual: Dict, expected_keys: List[str], optional_keys: List[str] = None):
        """Assert dictionary has expected structure"""
        optional_keys = optional_keys or []
        
        # Check required keys
        missing_keys = [key for key in expected_keys if key not in actual]
        if missing_keys:
            pytest.fail(f"Missing required keys: {missing_keys}")
        
        return True
    
    @staticmethod
    def assert_response_format(response: Dict, response_type: str = "query"):
        """Assert response follows expected format"""
        if response_type == "query":
            required_keys = ["status", "result"]
            optional_keys = ["message", "query_time", "engine"]
        elif response_type == "document":
            required_keys = ["status"]
            optional_keys = ["message", "entities_found", "processing_time"]
        else:
            required_keys = ["status"]
            optional_keys = ["message"]
        
        return ICETestHelpers.assert_dict_structure(response, required_keys, optional_keys)


@pytest.fixture
def test_helpers():
    """Provide test helper methods"""
    return ICETestHelpers