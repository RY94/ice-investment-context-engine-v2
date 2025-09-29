#!/bin/bash
# setup/ci_quality_checks.sh - Comprehensive quality checks for ICE system
# Run before any commit to ensure code quality and system health
# RELEVANT FILES: CLAUDE.md, setup/production_config.py, check/health_checks.py

echo "🔍 Running ICE Quality Checks..."

# Configuration
PYTHON_CMD="python"
PROJECT_ROOT="$(pwd)"
ERRORS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ERRORS=$((ERRORS + 1))
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_warning "$1 not found, skipping related checks"
        return 1
    fi
    return 0
}

# 1. Code formatting checks
echo -e "\n📝 Checking code formatting..."
if check_command "black"; then
    if $PYTHON_CMD -m black --check . --exclude="/(\.git|\.venv|venv|node_modules|__pycache__)/" 2>/dev/null; then
        print_success "Code formatting check passed"
    else
        print_error "Code formatting failed - run 'python -m black .'"
    fi
else
    print_warning "Black not installed - install with 'pip install black'"
fi

# 2. Import sorting
echo -e "\n📦 Checking import organization..."
if check_command "isort"; then
    if $PYTHON_CMD -m isort --check-only . --skip=.git --skip=.venv --skip=venv --skip=__pycache__ 2>/dev/null; then
        print_success "Import sorting check passed"
    else
        print_error "Import sorting failed - run 'python -m isort .'"
    fi
else
    print_warning "isort not installed - install with 'pip install isort'"
fi

# 3. Type checking
echo -e "\n🔍 Running type checks..."
if check_command "mypy"; then
    if $PYTHON_CMD -m mypy ice_lightrag/ --ignore-missing-imports --no-error-summary 2>/dev/null; then
        print_success "Type checks passed"
    else
        print_warning "Type check warnings found"
    fi
else
    print_warning "mypy not installed - install with 'pip install mypy'"
fi

# 4. Core functionality tests
echo -e "\n🧪 Testing core functionality..."

# Test basic LightRAG integration
if [ -f "ice_lightrag/test_basic.py" ]; then
    if $PYTHON_CMD ice_lightrag/test_basic.py >/dev/null 2>&1; then
        print_success "Basic LightRAG tests passed"
    else
        print_error "Basic LightRAG tests failed"
    fi
else
    print_warning "Basic test file not found: ice_lightrag/test_basic.py"
fi

# Test API key validation
if [ -f "test_api_key.py" ]; then
    if $PYTHON_CMD test_api_key.py >/dev/null 2>&1; then
        print_success "API key validation passed"
    else
        print_error "API key validation failed - check OPENAI_API_KEY"
    fi
else
    print_warning "API key test file not found: test_api_key.py"
fi

# Test simple demo
if [ -f "simple_demo.py" ]; then
    if timeout 30s $PYTHON_CMD simple_demo.py >/dev/null 2>&1; then
        print_success "Simple demo test passed"
    else
        print_warning "Simple demo test failed or timed out"
    fi
else
    print_warning "Simple demo file not found: simple_demo.py"
fi

# 5. Import checks for main modules
echo -e "\n📚 Checking module imports..."

# Check ICE LightRAG import
if $PYTHON_CMD -c "from ice_lightrag.ice_rag import ICELightRAG; print('ICELightRAG import successful')" 2>/dev/null; then
    print_success "ICELightRAG module imports correctly"
else
    print_error "ICELightRAG import failed"
fi

# Check Streamlit integration
if $PYTHON_CMD -c "from ice_lightrag.streamlit_integration import render_rag_interface; print('Streamlit integration import successful')" 2>/dev/null; then
    print_success "Streamlit integration imports correctly"
else
    print_warning "Streamlit integration import failed"
fi

# Check setup modules
if $PYTHON_CMD -c "from setup.local_llm_adapter import OllamaAdapter; print('Setup modules import successful')" 2>/dev/null; then
    print_success "Setup modules import correctly"
else
    print_warning "Setup modules import failed"
fi

# 6. Memory usage check
echo -e "\n🧠 Checking memory usage..."
MEMORY_CHECK_RESULT=$($PYTHON_CMD -c "
import psutil
import os
try:
    from ice_lightrag.ice_rag import ICELightRAG
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024
    ice_rag = ICELightRAG(working_dir='./ice_lightrag/storage')
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory
    print(f'Memory usage: {final_memory:.1f}MB (Δ{memory_increase:.1f}MB)')
    
    if memory_increase > 500:  # 500MB threshold
        print('WARNING: High memory usage detected')
        exit(1)
    else:
        print('Memory usage within acceptable limits')
        exit(0)
except Exception as e:
    print(f'Memory check failed: {e}')
    exit(2)
" 2>/dev/null)

memory_exit_code=$?
echo "$MEMORY_CHECK_RESULT"

if [ $memory_exit_code -eq 0 ]; then
    print_success "Memory usage check passed"
elif [ $memory_exit_code -eq 1 ]; then
    print_error "High memory usage detected"
else
    print_warning "Memory usage check failed"
fi

# 7. File structure validation
echo -e "\n📁 Validating file structure..."

# Check for required directories
required_dirs=("ice_lightrag" "ui_mockups" "setup" "user_data")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_success "Directory exists: $dir"
    else
        if [ "$dir" = "user_data" ]; then
            print_warning "Optional directory missing: $dir"
        else
            print_error "Required directory missing: $dir"
        fi
    fi
done

# Check for key files
required_files=("CLAUDE.md" "README.md" "simple_demo.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "File exists: $file"
    else
        print_error "Required file missing: $file"
    fi
done

# 8. Configuration validation
echo -e "\n⚙️  Validating configuration..."

# Check environment variables
if [ -n "$OPENAI_API_KEY" ]; then
    print_success "OPENAI_API_KEY is set"
    
    # Basic format validation
    if [[ "$OPENAI_API_KEY" == sk-* ]]; then
        print_success "OPENAI_API_KEY format appears valid"
    else
        print_warning "OPENAI_API_KEY format may be invalid (should start with 'sk-')"
    fi
else
    print_warning "OPENAI_API_KEY not set"
fi

# Check storage directory
STORAGE_DIR="${ICE_STORAGE_DIR:-./ice_lightrag/storage}"
if [ -d "$STORAGE_DIR" ]; then
    print_success "Storage directory exists: $STORAGE_DIR"
    
    if [ -w "$STORAGE_DIR" ]; then
        print_success "Storage directory is writable"
    else
        print_error "Storage directory is not writable: $STORAGE_DIR"
    fi
else
    print_warning "Storage directory does not exist: $STORAGE_DIR"
fi

# 9. Security checks
echo -e "\n🔐 Running security checks..."

# Check for exposed secrets in common files
secret_patterns=("sk-[a-zA-Z0-9]{48}" "api[_-]?key" "password" "secret" "token")
for pattern in "${secret_patterns[@]}"; do
    if grep -r -i --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude="*.pyc" "$pattern" . >/dev/null 2>&1; then
        print_warning "Potential secret found matching pattern: $pattern"
    fi
done

# Check file permissions
if find . -name "*.py" -perm -o=w 2>/dev/null | grep -q .; then
    print_warning "Some Python files are world-writable"
else
    print_success "Python file permissions look secure"
fi

# 10. Performance baseline
echo -e "\n⚡ Running performance baseline..."

PERF_RESULT=$($PYTHON_CMD -c "
import time
import sys
sys.path.append('.')

try:
    # Test query preprocessing performance
    from ice_lightrag.query_optimization import QueryPreprocessor
    
    preprocessor = QueryPreprocessor()
    start_time = time.time()
    
    test_queries = [
        'What are NVDA PE ratio risks?',
        'How does EBITDA impact company valuation through ROE analysis?',
        'Compare market performance of semiconductor stocks'
    ]
    
    for query in test_queries:
        preprocessor.preprocess_query(query)
        preprocessor.estimate_complexity(query)
    
    processing_time = (time.time() - start_time) * 1000
    print(f'Query preprocessing: {processing_time:.1f}ms for {len(test_queries)} queries')
    
    if processing_time > 100:
        print('WARNING: Query preprocessing is slow')
        exit(1)
    else:
        print('Query preprocessing performance is acceptable')
        exit(0)
        
except ImportError:
    print('Query optimization module not available')
    exit(2)
except Exception as e:
    print(f'Performance test failed: {e}')
    exit(2)
" 2>/dev/null)

perf_exit_code=$?
echo "$PERF_RESULT"

if [ $perf_exit_code -eq 0 ]; then
    print_success "Performance baseline check passed"
elif [ $perf_exit_code -eq 1 ]; then
    print_warning "Performance baseline below expectations"
else
    print_warning "Performance baseline check failed"
fi

# 11. Final summary
echo -e "\n📊 Quality Check Summary"
echo "=================================="

if [ $ERRORS -eq 0 ]; then
    print_success "All quality checks passed!"
    echo -e "\n🚀 Ready for commit!"
    exit 0
else
    print_error "$ERRORS error(s) found"
    echo -e "\n🛠️  Please fix errors before committing"
    exit 1
fi