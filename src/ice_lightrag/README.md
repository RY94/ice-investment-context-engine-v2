# ICE LightRAG Integration

Simple LightRAG integration for the Investment Context Engine (ICE).

## Quick Start

1. **Install dependencies:**
   ```bash
   cd lightrag
   python setup.py
   ```

2. **Set API key:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

3. **Test the setup:**
   ```bash
   python test_basic.py
   ```

## Usage

### Basic RAG Operations

```python
from lightrag import SimpleICERAG

# Initialize
rag = SimpleICERAG()

# Add financial document
result = rag.add_document("NVIDIA reported...", "earnings_report")

# Query for insights
result = rag.query("What are NVIDIA's main risks?")
print(result["result"])
```

### Streamlit Integration

```python
import streamlit as st
from lightrag.streamlit_integration import render_rag_interface

st.title("ICE Investment Analysis")
render_rag_interface()
```

## Files

- `ice_rag.py` - Core LightRAG wrapper
- `streamlit_integration.py` - Streamlit UI components  
- `setup.py` - Installation script
- `test_basic.py` - Basic functionality test
- `requirements.txt` - Dependencies

## Integration with Existing ICE UI

Add to your existing Streamlit app:

```python
from lightrag.streamlit_integration import render_rag_interface

# Add anywhere in your Streamlit app
with st.expander("🤖 AI Analysis", expanded=True):
    render_rag_interface()
```

This provides document upload and query capabilities alongside your existing graph visualization.
