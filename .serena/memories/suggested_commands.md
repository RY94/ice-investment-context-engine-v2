# ICE Development Commands (Updated: 2025-01-22)

## Quick Start Commands

### 🆕 Dual Workflow Notebooks (PRIMARY INTERFACE)
```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Start knowledge graph building workflow
jupyter notebook ice_building_workflow.ipynb

# Start investment query workflow  
jupyter notebook ice_query_workflow.ipynb
```

### Simplified Architecture (Production Ready)
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

## Development Workflow

### Environment Setup
```bash
# Set required API key
export OPENAI_API_KEY="your-openai-api-key"

# Install dependencies
pip install -r requirements.txt

# Install LightRAG dependencies
cd src/ice_lightrag && python setup.py && cd ../..

# Create user data directory for persistent storage
mkdir -p user_data

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

# Test dual notebook integration (10 tests, 100% pass rate)
python tests/test_dual_notebook_integration.py

# Test email graph integration (Phase 1 validation)
python tests/test_email_graph_integration.py

# Test core demo functionality
python src/simple_demo.py
```

### Running the Application
```bash
# Primary development interface (dual workflow notebooks)
jupyter notebook ice_building_workflow.ipynb
jupyter notebook ice_query_workflow.ipynb

# Run simplified production interface
cd updated_architectures/implementation && python ice_simplified.py

# Run Streamlit UI (SHELVED until Phase 5 - post 90% AI completion)
streamlit run --server.port 8502 UI/ice_ui_v17.py
```

### Local LLM Setup (Cost Optimization)
```bash
# Install and start Ollama
ollama pull llama3.1:8b
ollama serve

# Use local LLM adapter
python setup/local_llm_setup.py
```

### Debug Mode
```bash
# Enhanced logging
export PYTHONPATH="${PYTHONPATH}:." && export ICE_DEBUG=1 && python src/simple_demo.py
```

## Integration Testing (Week 1 Complete)

### Data Source Validation
```bash
# Test API/MCP sources
cd updated_architectures/implementation && python data_ingestion.py

# Test email pipeline (74 sample emails)
cd imap_email_ingestion_pipeline && python ice_integrator.py

# Test SEC EDGAR connector
cd ice_data_ingestion && python sec_edgar_connector.py

# Verify all sources → LightRAG (26 documents expected)
cd updated_architectures/implementation && python ice_simplified.py
```

### Email Enhanced Documents Testing
```bash
# Run enhanced document creator unit tests (27 tests)
cd imap_email_ingestion_pipeline/tests && python -m pytest test_enhanced_doc_creator.py -v

# Validate email graph integration (5 tests)
cd tests && python test_email_graph_integration.py
```

## macOS-Specific Notes
- Use `brew` for package management (e.g., `brew install python`)
- Python 3 command: `python3` (not `python`)
- Open files/apps: `open filename` or `open -a AppName`
- Fast file search: `mdfind "filename"` (Spotlight-based)
- Some GNU tools have different names (e.g., `gsed` instead of `sed`)

## Common Troubleshooting

### API Key Issues
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API key validity
python test_api_key.py
```

### LightRAG Issues
```bash
# Reinstall LightRAG dependencies
cd src/ice_lightrag && python setup.py && cd ../..

# Check LightRAG storage
ls -la src/ice_lightrag/storage/
```

### Import Path Issues
```bash
# Check Python path
echo $PYTHONPATH

# Set Python path if needed
export PYTHONPATH="${PYTHONPATH}:."
```