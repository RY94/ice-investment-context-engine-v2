# ICE Codebase Structure

## Root Directory Organization

### Core Implementation Files
- **`ice_main_notebook.ipynb`** - Primary development interface and AI solution interaction
- **`README.md`** - Project overview and documentation entry point
- **`CLAUDE.md`** - Essential development guidance and power user commands
- **`PROJECT_STRUCTURE.md`** - Complete directory organization reference
- **`ICE_DEVELOPMENT_TODO.md`** - Main project roadmap and task tracking
- **`requirements.txt`** - Core dependency specification

### Main Directories

#### `updated_architectures/` - Simplified Architecture (Production Ready)
- **`implementation/ice_simplified.py`** - Complete system (677 lines)
- **`implementation/config.py`** - Environment setup (420 lines)
- **`implementation/data_ingestion.py`** - 8 APIs (510 lines)
- **`implementation/query_engine.py`** - Portfolio analysis (534 lines)
- **`implementation/ice_core.py`** - LightRAG wrapper (374 lines)
- **`tests/`** - Structure + functional tests

#### `src/` - Core System Components
- **`ice_lightrag/`** - LightRAG integration and AI processing
  - `ice_rag.py` - Main LightRAG wrapper
  - `setup.py` - Dependencies installation
  - `test_basic.py` - Core functionality tests
- **`ice_core/`** - Core system management and orchestration
- **`simple_demo.py`** - Standalone testing and demonstration

#### `ice_data_ingestion/` - Financial Data APIs (15+ connectors)
- **API Clients**: Alpha Vantage, NewsAPI, Bloomberg, Polygon, etc.
- **`secure_config.py`** - Encrypted API key management
- **`robust_client.py`** - Retry + circuit breaker patterns
- **`data_validator.py`** - Multi-level validation
- **`test_scenarios.py`** - Comprehensive test coverage

#### `tests/` - Testing Infrastructure
- **`test_runner.py`** - Comprehensive test execution
- **`conftest.py`** - Pytest configuration
- Multiple test subdirectories for different components

#### Other Key Directories
- **`UI/`** - Streamlit interface components (SHELVED until Phase 5)
- **`data/`** - Data utilities, samples, and user portfolio data
- **`setup/`** - Environment configuration and local LLM setup
- **`archive/`** - Organized backups and legacy files
- **`sandbox/`** - Development experiments and prototypes

## Critical File Protection
Never delete or rename without explicit permission:
- `ICE_DEVELOPMENT_TODO.md`
- `ice_main_notebook.ipynb`
- `PROJECT_STRUCTURE.md`
- `PROJECT_CHANGELOG.md`
- `README.md`