# ICE Development Commands

## Quick Start Commands

### Simplified Architecture (Recommended)
```bash
# Set API key and navigate to implementation
export OPENAI_API_KEY="sk-..." && cd updated_architectures/implementation

# Test configuration
python config.py

# Run complete portfolio analysis
python ice_simplified.py

# Run architecture tests
cd ../tests && python test_architecture_structure.py
```

### Legacy Complex Architecture
```bash
# Full system startup (notebook-first development)
export OPENAI_API_KEY="sk-..." && cd src/ice_lightrag && python setup.py && cd ../.. && jupyter notebook ice_main_notebook.ipynb

# Local LLM setup (cost efficient)
ollama pull llama3.1:8b && ollama serve

# Debug mode with enhanced logging
export PYTHONPATH="${PYTHONPATH}:." && export ICE_DEBUG=1 && python src/simple_demo.py
```

## Development Workflow

### Environment Setup
```bash
# Set required API key
export OPENAI_API_KEY="your-openai-api-key"

# Install dependencies
pip install -r requirements.txt

# Install LightRAG dependencies
cd src/ice_lightrag && python setup.py && cd ../..

# Optional: Optimize NumExpr for CPU
export NUMEXPR_MAX_THREADS=14
```

### Testing Commands
```bash
# Test LightRAG integration
python src/ice_lightrag/test_basic.py

# Validate API key setup
python test_api_key.py

# Run all tests
python tests/test_runner.py

# Test core demo functionality
python src/simple_demo.py
```

### Running the Application
```bash
# Primary development interface (notebook-first)
jupyter notebook ice_main_notebook.ipynb

# Run simplified interface
python updated_architectures/implementation/ice_simplified.py

# Run Streamlit UI (SHELVED until Phase 5)
streamlit run --server.port 8502 UI/ice_ui_v17.py
```

## macOS-Specific Notes
- Use `brew` for package management
- Python 3 is `python3` command
- Use `open` command to open files/applications
- Use `mdfind` for fast filename searches