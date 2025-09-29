# ICE RAG Systems Test Suite

Comprehensive testing framework for the ICE (Investment Context Engine) RAG systems, providing thorough validation of LightRAG, LazyGraphRAG, and Unified RAG implementations.

## 🚀 Quick Start

### Run All Tests
```bash
cd tests
python test_runner.py
```

### Run Specific Test Suite
```bash
# Test only LightRAG
python test_runner.py --suites lightrag

# Test only LazyGraphRAG  
python test_runner.py --suites lazygraphrag

# Test only Unified RAG
python test_runner.py --suites unified

# Test multiple specific suites
python test_runner.py --suites lightrag unified
```

### Run with Detailed Output
```bash
python test_runner.py --verbose
```

### Save Results
```bash
python test_runner.py --save results.json --verbose
```

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Pytest configuration and fixtures
├── pytest.ini                # Pytest settings
├── test_fixtures.py           # Shared test data and utilities
├── test_runner.py             # Main test runner
├── test_lightrag.py           # LightRAG test suite
├── test_lazygraphrag.py       # LazyGraphRAG test suite  
├── test_unified_rag.py        # Unified RAG test suite
├── results/                   # Test results storage
└── README.md                  # This documentation
```

## 🧪 Test Suites Overview

### 1. LightRAG Test Suite (`test_lightrag.py`)
Tests the traditional knowledge graph RAG system with OpenAI integration.

**Key Test Areas:**
- System availability and initialization
- Document processing (async/sync)
- Query functionality across different modes
- Error handling and edge cases
- Performance characteristics
- Integration scenarios

**Example:**
```bash
python test_runner.py --suites lightrag --verbose
```

### 2. LazyGraphRAG Test Suite (`test_lazygraphrag.py`)
Tests the dynamic lazy graph construction system with multi-hop reasoning.

**Key Test Areas:**
- Graph store functionality
- Query processor analysis
- Document processing
- Edge management and graph construction
- Lazy querying with subgraph extraction
- Multi-hop reasoning capabilities
- Performance and caching behavior
- Integration scenarios

**Example:**
```bash
python test_runner.py --suites lazygraphrag --verbose
```

### 3. Unified RAG Test Suite (`test_unified_rag.py`)
Tests the unified interface supporting multiple RAG engines.

**Key Test Areas:**
- Engine detection and availability
- Engine switching functionality
- Unified document processing
- Unified querying interface
- Engine comparison capabilities
- Edge management across engines
- Performance comparison
- Error handling and fallbacks

**Example:**
```bash
python test_runner.py --suites unified --verbose
```

## 🔧 Using Pytest

### Basic Pytest Commands
```bash
# Run all tests
pytest

# Run specific test file
pytest test_lightrag.py

# Run tests with specific marker
pytest -m "lightrag"
pytest -m "integration"
pytest -m "slow"

# Run tests requiring API key (will be skipped if not available)
pytest -m "requires_api_key"

# Run with coverage report
pytest --cov=tests --cov-report=html

# Run specific test method
pytest test_lightrag.py::TestLightRAGPytest::test_lightrag_availability
```

### Test Markers
- `@pytest.mark.lightrag` - LightRAG specific tests
- `@pytest.mark.lazygraphrag` - LazyGraphRAG specific tests
- `@pytest.mark.unified` - Unified RAG specific tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.requires_api_key` - Tests requiring OpenAI API key
- `@pytest.mark.performance` - Performance tests

## ⚙️ Configuration

### Environment Variables
```bash
# Required for full LightRAG functionality
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Set execution mode
export JUPYTER_EXECUTION_MODE="test"

# Optional: Enable debug mode
export ICE_DEBUG="1"
```

### Custom Configuration
Create a configuration file and pass it to the test runner:

```json
{
  "openai_api_key": "your-key",
  "test_timeout": 45.0,
  "max_retries": 3,
  "performance_benchmarks": {
    "max_query_time": 8.0,
    "max_document_processing_time": 4.0,
    "max_edge_addition_time": 0.8
  }
}
```

```bash
python test_runner.py --config my_config.json
```

## 📊 Test Output and Reporting

### Standard Output
The test runner provides comprehensive reporting including:

```
🚀 ICE RAG Systems - Comprehensive Test Runner
===========================================================
Running 3 test suite(s): lightrag, lazygraphrag, unified
Started at: 2024-01-15 14:30:00

🔍 Running System Availability Check...
📦 Checking critical dependencies...
  ✅ pandas
  ✅ numpy
  ✅ networkx
  ...

🧪 Running ICE LightRAG Test Suite...
📝 Traditional knowledge graph RAG with OpenAI integration
===========================================================
✅ LightRAG system availability tests passed
✅ LightRAG initialization tests passed
...

📊 COMPREHENSIVE TEST RESULTS SUMMARY
===========================================================
⏱️ Total Duration: 45.2 seconds
🏗️ Test Suites: 3/3 completed (100.0%)
🧪 Individual Tests: 28/30 passed (93.3%)
```

### Saved Results
When using `--save`, results are saved in JSON format with detailed information:

```json
{
  "test_run_info": {
    "timestamp": "2024-01-15T14:30:00",
    "total_duration": 45.2,
    "suites_completed": 3,
    "config": {...}
  },
  "system_info": {
    "python_version": "3.11.0",
    "dependencies": {...},
    "environment_variables": {...}
  },
  "overall_stats": {
    "total_tests": 30,
    "total_passed": 28,
    "overall_success_rate": 93.3
  },
  "suite_results": {...}
}
```

## 🛠️ Test Development

### Adding New Tests

1. **Create test functions** following the `test_*` naming convention:
```python
def test_my_new_feature(self):
    """Test description"""
    # Arrange
    setup_data = self.fixtures.get_sample_document()
    
    # Act  
    result = self.rag_instance.new_feature(setup_data)
    
    # Assert
    assert result["status"] == "success"
    assert len(result["data"]) > 0
```

2. **Use test fixtures** for consistent data:
```python
def test_with_fixtures(self, test_fixtures, test_environment):
    sample_doc = test_fixtures.get_sample_document("earnings_transcript")
    # Use test_environment for isolated testing
```

3. **Add appropriate markers**:
```python
@pytest.mark.lightrag
@pytest.mark.integration
def test_lightrag_integration(self):
    # Test implementation
```

### Test Data Management

Test data is managed through `test_fixtures.py`:

```python
from tests.test_fixtures import TestDataFixtures

fixtures = TestDataFixtures()

# Get sample documents
doc = fixtures.get_sample_document("earnings_transcript")
docs = fixtures.test_documents

# Get sample edges
edges = fixtures.get_sample_edges(5)

# Get test queries
query = fixtures.get_test_query("complex")

# Validate responses
issues = fixtures.validate_response(response, "risk_analysis")
```

## 🐛 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
ImportError: No module named 'lightrag'
```
- Install required dependencies
- Check Python path configuration
- Verify test is properly marked to skip when dependencies missing

**2. API Key Issues**
```bash
⚠️ OPENAI_API_KEY not set. Some features may not work.
```
- Set environment variable: `export OPENAI_API_KEY="your-key"`
- Or use mock API key fixture for testing without real API calls

**3. Test Timeouts**
```bash
FAILED test_lightrag.py::test_query_performance - Test timed out
```
- Increase timeout in configuration
- Check system performance and dependencies
- Consider marking slow tests with `@pytest.mark.slow`

**4. File Permission Errors**
```bash
PermissionError: [Errno 13] Permission denied
```
- Ensure test directory is writable
- Check file system permissions
- Temporary directories should be accessible

### Debug Mode

Enable debug mode for detailed output:
```bash
export ICE_DEBUG=1
python test_runner.py --verbose
```

### Test Isolation Issues

Each test should be isolated. If tests interfere with each other:
1. Use proper setup/teardown methods
2. Use unique test environments per test
3. Clear any global state between tests

## 📈 Performance Benchmarks

Default performance expectations:

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Query Processing | < 5.0s | Standard query response |
| Document Processing | < 3.0s | Single document ingestion |
| Edge Addition | < 0.5s | Single edge processing |
| System Initialization | < 10.0s | Full system startup |

Adjust benchmarks in configuration for different environments.

## 🤝 Contributing

### Adding New Test Suites

1. Create new test file: `test_newsystem.py`
2. Implement test class extending base patterns
3. Add to `test_runner.py` test suite mapping
4. Update this README with documentation
5. Add appropriate pytest markers

### Test Quality Guidelines

- **Comprehensive Coverage**: Test happy path, edge cases, and error conditions
- **Clear Assertions**: Use descriptive assertion messages
- **Proper Isolation**: Tests should not depend on each other
- **Performance Awareness**: Include timing assertions for critical operations
- **Documentation**: Document complex test scenarios and expected behaviors

---

## 📋 Test Checklist

Before running tests in production:

- [ ] OpenAI API key configured
- [ ] All dependencies installed
- [ ] Test environment has sufficient disk space
- [ ] Network connectivity available for API calls
- [ ] Python environment properly configured
- [ ] File permissions allow temporary file creation

## 📞 Support

For issues with the test framework:

1. Check this README for common solutions
2. Review test output for specific error messages
3. Verify system configuration and dependencies
4. Check individual test suite documentation
5. Run with `--verbose` flag for detailed output

---

*Last updated: January 2024*
*ICE RAG Systems Test Suite v1.0.0*