# Ollama Integration Patterns for ICE

**Date Created**: 2025-10-10
**Last Updated**: 2025-10-11
**Purpose**: Document Ollama integration patterns, configuration modes, provider switching methods, and troubleshooting solutions for ICE Investment Context Engine

---

## Overview

ICE now supports 3 LLM provider configurations via factory pattern in `src/ice_lightrag/model_provider.py`:
1. **OpenAI** (default): gpt-4o-mini + 1536-dim embeddings, $5/month
2. **Hybrid** (recommended): Ollama LLM + OpenAI embeddings, $2/month, 60% cost reduction
3. **Full Ollama**: qwen3:30b-32k + 768-dim embeddings, $0/month, requires graph rebuild

---

## File Locations

### Core Implementation
- `src/ice_lightrag/model_provider.py` - Model provider factory (214 lines)
  - `get_llm_provider()` - Main factory function
  - `check_ollama_service()` - Health check for Ollama service
  - `check_ollama_model_available()` - Model availability validation
  - `_fallback_to_openai()` - Automatic fallback logic

- `src/ice_lightrag/ice_rag_fixed.py` - Integration point (lines 38-51, 131-144)
  - Imports model_provider factory
  - Calls `get_llm_provider()` during LightRAG initialization
  - Passes model_config to LightRAG constructor

### Testing & Documentation
- `src/ice_lightrag/test_basic.py` - Provider selection tests (lines 64-173)
- `md_files/OLLAMA_TEST_RESULTS.md` - Comprehensive test results (500+ lines)
- `md_files/ICE_GRAPH_IMPLEMENTATION.md` - Graph Management & Maintenance section (lines 569-728)
- `md_files/LOCAL_LLM_GUIDE.md` - Provider switching methods section (lines 146-330)
- `ice_building_workflow.ipynb` - Cell 7: Provider config, Cell 7.5: Switching, Cell 8-9: Graph clearing
- `ice_query_workflow.ipynb` - Cell 5: Provider config, Cell 5.5: Switching

---

## Provider Switching Methods

ICE supports **3 methods** for switching between OpenAI, Hybrid, and Full Ollama modes.

### Method 1: Terminal Environment Variables

**Best for**: Scripts, automation, production deployments

**Usage**:
```bash
# OpenAI (default)
export OPENAI_API_KEY="sk-..."

# Hybrid (recommended)
export LLM_PROVIDER="ollama"
export EMBEDDING_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."

# Full Ollama
export LLM_PROVIDER="ollama"
export EMBEDDING_PROVIDER="ollama"
```

**When**: Set before starting Jupyter or Python scripts

---

### Method 2: Notebook Cell (Recommended for Interactive Work)

**Best for**: Interactive development, testing, experimenting

**Location**: 
- `ice_building_workflow.ipynb` - Cell 7.5 (after provider config docs)
- `ice_query_workflow.ipynb` - Cell 5.5 (after provider config docs)

**Implementation** (minimal code - 3 one-liners):
```python
# Provider Switching - Uncomment ONE option below, then restart kernel

# Option 1: OpenAI ($5/mo, highest quality)
# import os; os.environ['LLM_PROVIDER'] = 'openai'; os.environ['OPENAI_API_KEY'] = 'sk-YOUR-KEY'; print("✅ Switched to OpenAI")

# Option 2: Hybrid ($2/mo, 60% savings, recommended)
# import os; os.environ['LLM_PROVIDER'] = 'ollama'; os.environ['EMBEDDING_PROVIDER'] = 'openai'; os.environ['OPENAI_API_KEY'] = 'sk-YOUR-KEY'; print("✅ Switched to Hybrid")

# Option 3: Full Ollama ($0/mo, requires graph clearing)
# import os; os.environ['LLM_PROVIDER'] = 'ollama'; os.environ['EMBEDDING_PROVIDER'] = 'ollama'; print("✅ Switched to Full Ollama - Clear graph in Cell 9 if needed")
```

**How to use**:
1. Find switching cell (right after provider configuration markdown)
2. **Uncomment ONE line** - Remove `#` from your chosen option
3. Replace `sk-YOUR-KEY` with actual OpenAI API key (if needed)
4. **Run cell** - Press `Shift+Enter`
5. **Restart kernel** - `Kernel → Restart Kernel` (critical for changes to take effect)
6. Continue with notebook workflow

**Design Principles**:
- ✅ **Minimal code** - Only 3 executable lines (one per option)
- ✅ **Safety-first** - All options commented by default
- ✅ **Clear feedback** - Prints confirmation message when switched
- ✅ **Single action** - Uncomment one line, run, restart
- ✅ **No complexity** - No if/else logic, no functions

**Advantages**:
- No terminal commands needed
- Changes documented in notebook
- Easy to share configurations
- Visual confirmation of active provider
- Recommended for most users

---

### Method 3: Jupyter Magic Commands

**Best for**: Quick testing, temporary switches, debugging

**Usage**:
```python
# OpenAI
%env LLM_PROVIDER=openai
%env OPENAI_API_KEY=sk-YOUR-KEY

# Hybrid
%env LLM_PROVIDER=ollama
%env EMBEDDING_PROVIDER=openai
%env OPENAI_API_KEY=sk-YOUR-KEY

# Full Ollama
%env LLM_PROVIDER=ollama
%env EMBEDDING_PROVIDER=ollama
```

**When**: Add at top of any notebook cell for quick switching

**Advantages**:
- Fastest method (one cell)
- No kernel restart needed (usually)
- Good for A/B testing

---

### Method Comparison

| Method | Best For | Speed | Persistence | Recommended For |
|--------|----------|-------|-------------|-----------------|
| **Terminal** | Scripts, automation | Fast | Session | Production, scripting |
| **Notebook Cell** | Interactive work | Fast | Saved in notebook | Development, sharing |
| **Magic Commands** | Quick testing | Fastest | Temporary | A/B testing, debugging |

**Recommendation**: Use **Method 2 (Notebook Cell)** for interactive work, **Method 1 (Terminal)** for scripts.

---

## Configuration Patterns

### Pattern 1: OpenAI (Default)
```bash
# Option A: No environment variables (uses default)
python ice_simplified.py

# Option B: Explicit configuration
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."
```

**Use When**: Default setup, highest quality, no local setup required

### Pattern 2: Hybrid (Recommended)
```bash
export LLM_PROVIDER="ollama"
export EMBEDDING_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."

# Ensure Ollama running with model pulled
ollama serve  # In separate terminal
ollama pull qwen3:30b-32k
```

**Use When**:
- Existing OpenAI graphs (1536-dim compatible)
- 60% cost reduction desired
- No graph rebuild acceptable
- Quality maintained

**Benefits**:
- Free LLM processing (Ollama local)
- OpenAI embedding quality maintained
- Backward compatible with existing graphs
- Easy switching between providers

### Pattern 3: Full Ollama (Future-State)
```bash
export LLM_PROVIDER="ollama"
export EMBEDDING_PROVIDER="ollama"

# Pull both models
ollama pull qwen3:30b-32k
ollama pull nomic-embed-text:latest  # Note :latest suffix required!
```

**Use When**: 
- Building new graph from scratch
- Zero cost priority
- Accept 768-dim embeddings

**Caution**: Incompatible with existing 1536-dim OpenAI graphs

---

## Critical Issue: Embedding Dimension Mismatch

### Problem Discovery
```
ERROR: Embedding dim mismatch, expected: 768, but loaded: 1536
```

**Root Cause**: 
- Existing LightRAG graph built with OpenAI embeddings (1536-dim)
- Full Ollama mode uses nomic-embed-text (768-dim)
- Dimension incompatibility prevents loading existing graphs

### Solution Implemented
Use **hybrid mode** to maintain 1536-dim compatibility:
```bash
export LLM_PROVIDER="ollama"          # Free LLM processing
export EMBEDDING_PROVIDER="openai"    # Keep 1536-dim embeddings
```

**Result**: 
- Existing graphs load successfully ✅
- No rebuild required ✅
- 60% cost reduction achieved ✅

### Alternative Solutions (Not Implemented)
1. **Rebuild graph**: Delete `src/ice_lightrag/storage/` and rebuild with 768-dim
2. **Document limitation**: Warn users that switching requires rebuild

---

## Factory Pattern Implementation

### Core Function Signature
```python
def get_llm_provider() -> Tuple[Callable, Callable, Dict[str, Any]]:
    """
    Returns:
        Tuple of (llm_func, embed_func, model_config)
    """
```

### Environment Variables
```python
LLM_PROVIDER = "openai" | "ollama"  # Default: "openai"
LLM_MODEL = "gpt-4o-mini" | "qwen3:30b-32k"  # Model name
EMBEDDING_PROVIDER = "openai" | "ollama"  # Default: same as LLM_PROVIDER
EMBEDDING_MODEL = "nomic-embed-text:latest"  # Ollama embedding model
EMBEDDING_DIM = 1536 | 768  # Embedding dimension
OLLAMA_HOST = "http://localhost:11434"  # Ollama service URL
OLLAMA_NUM_CTX = 32768  # Context window size
```

### Health Check Pattern
```python
# Two-tier validation
if not check_ollama_service(ollama_host):
    return _fallback_to_openai("Service not running")

if not check_ollama_model_available(model_name, ollama_host):
    return _fallback_to_openai("Model not found")
```

### Return Patterns

**OpenAI Mode**:
```python
return (
    gpt_4o_mini_complete,  # LLM function
    openai_embed,          # Embedding function
    {}                     # Empty config (uses defaults)
)
```

**Ollama Mode**:
```python
return (
    ollama_model_complete,
    embed_func,  # Can be ollama_embed or openai_embed
    {
        "llm_model_name": "qwen3:30b-32k",
        "llm_model_kwargs": {
            "host": "http://localhost:11434",
            "options": {"num_ctx": 32768},
            "timeout": 300
        }
    }
)
```

---

## Integration Point Pattern

### Before (Hardcoded)
```python
# src/ice_lightrag/ice_rag_fixed.py (old)
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

self._rag = LightRAG(
    working_dir=str(self.working_dir),
    llm_model_func=gpt_4o_mini_complete,
    embedding_func=openai_embed
)
```

### After (Factory-Based)
```python
# src/ice_lightrag/ice_rag_fixed.py (new)
from .model_provider import get_llm_provider

llm_func, embed_func, model_config = get_llm_provider()
self._rag = LightRAG(
    working_dir=str(self.working_dir),
    llm_model_func=llm_func,
    embedding_func=embed_func,
    **model_config  # Includes llm_model_name, llm_model_kwargs for Ollama
)
```

**Why This Pattern**:
- Single integration point (lines 131-144)
- Factory handles all provider selection logic
- Clean separation of concerns
- Easy to test (mock factory return values)

---

## Testing Patterns

### Mock-Based Testing
```python
# Test Ollama selection with mocked health checks
with patch('model_provider.check_ollama_service', return_value=True), \
     patch('model_provider.check_ollama_model_available', return_value=True):
    os.environ["LLM_PROVIDER"] = "ollama"
    llm_func, embed_func, model_config = get_llm_provider()
    assert model_config["llm_model_name"] == "qwen3:30b-32k"
```

### Fallback Testing
```python
# Test automatic fallback on unavailable Ollama
with patch('model_provider.check_ollama_service', return_value=False):
    os.environ["LLM_PROVIDER"] = "ollama"
    llm_func, embed_func, model_config = get_llm_provider()
    assert model_config == {}  # Empty config = OpenAI fallback
```

### Integration Testing (Manual)
```python
# Test with real Ollama service
import os
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["EMBEDDING_PROVIDER"] = "openai"

from ice_rag import SimpleICERAG
ice = SimpleICERAG()
result = ice.add_document("test doc", doc_type="test")
assert result["status"] == "success"
```

---

## Common Issues & Solutions

### Issue 1: "Embedding model not found"
**Error**: `check_ollama_model_available("nomic-embed-text")` returns False
**Cause**: Model name missing `:latest` suffix
**Solution**: Changed default to `"nomic-embed-text:latest"` in line 140
**Fix**: `embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")`

### Issue 2: "Ollama service not running"
**Error**: Health check fails at `check_ollama_service()`
**Cause**: Ollama not started
**Solution**: 
```bash
ollama serve  # Start in separate terminal
# Or as background process: nohup ollama serve &
```

### Issue 3: "Model not pulled"
**Error**: `check_ollama_model_available("qwen3:30b-32k")` returns False
**Cause**: Model not downloaded
**Solution**: 
```bash
ollama pull qwen3:30b-32k  # 18.5GB download
ollama pull nomic-embed-text:latest  # 274MB download
```

### Issue 4: Dimension mismatch on existing graph
**Error**: `Embedding dim mismatch, expected: 768, but loaded: 1536`
**Cause**: Switching from OpenAI (1536-dim) to full Ollama (768-dim)
**Solution**: Use hybrid mode instead
```bash
export LLM_PROVIDER="ollama"
export EMBEDDING_PROVIDER="openai"  # Keep 1536-dim
```

---

## Performance Observations

### LLM Processing (qwen3:30b-32k)
- Entity extraction: ~5-10 seconds per document
- Query response: ~10-20 seconds per query
- Quality: Comparable to gpt-4o-mini for financial text
- Context window: 32k tokens (sufficient for LightRAG)

### Embedding Processing
- **OpenAI (1536-dim)**: ~1-2 seconds per document, high quality
- **Ollama (768-dim)**: ~3-5 seconds per document, good quality

### Graph Operations
- Storage: Nano-vectordb with configurable dimensions
- Persistence: All operations successful
- Files created:
  - `vdb_entities.json` (embedding dimension specific)
  - `vdb_relationships.json`
  - `vdb_chunks.json`
  - `graph_chunk_entity_relation.graphml`

---

## Decision Framework

### Choose OpenAI When:
- Default setup preferred
- Highest quality priority
- No local setup acceptable
- Cost not primary concern ($5/mo)

### Choose Hybrid When:
- Existing OpenAI graphs (1536-dim)
- 60% cost reduction desired ($2/mo)
- Quality maintained important
- **Recommended for most users**

### Choose Full Ollama When:
- Building new graph from scratch
- Zero cost priority ($0/mo)
- Accept 768-dim embeddings
- Local-only deployment required

---

## Graph Management

**Critical Insight**: Embedding dimension (1536 vs 768) determines graph compatibility. Clearing graph is sometimes necessary, but often avoidable.

### When to Clear Graph

✅ **Clear in these scenarios:**

1. **Switching to Full Ollama** (1536-dim → 768-dim)
   - OpenAI/Hybrid uses 1536-dimensional embeddings
   - Full Ollama uses 768-dimensional embeddings
   - Dimension mismatch prevents loading existing graph
   - **Solution**: Clear and rebuild with 768-dim

2. **Graph corruption**
   - LightRAG reports storage loading errors
   - Inconsistent entity/relationship counts
   - Query failures or incorrect results
   - **Solution**: Clear corrupted storage, rebuild from source documents

3. **Testing fresh builds**
   - Validating entity extraction improvements
   - Testing new data sources integration
   - Need clean baseline for comparison
   - **Solution**: Clear graph, rebuild with new pipeline

❌ **Don't clear when:**

1. **Switching LLM provider only** (OpenAI ↔ Hybrid)
   - Same embedding dimension (1536-dim)
   - Full graph compatibility maintained
   - **Why safe**: Only LLM processing changes, embeddings unchanged
   - **Benefit**: 60% cost reduction with zero downtime

2. **Adding new documents** (incremental updates)
   - LightRAG supports incremental graph building
   - New entities merge with existing knowledge
   - **Why safe**: No data loss, preserves existing graph
   - **Benefit**: Faster than full rebuild

3. **Changing query modes** (local, global, hybrid, mix, naive)
   - All modes use same underlying graph
   - Query strategy doesn't affect storage
   - **Why safe**: Read-only operations
   - **Benefit**: Can experiment with modes freely

### How to Clear Graph

**Method 1: Python (Safest, Recommended)**
```python
from pathlib import Path
import shutil

storage_path = Path('src/ice_lightrag/storage')
if storage_path.exists():
    shutil.rmtree(storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    print("✅ Graph cleared - will rebuild from scratch")
```

**Method 2: Notebook Cell (Most Convenient)**
- Location: `ice_building_workflow.ipynb` Cell 9 (right after graph management docs)
- Markdown guidance in Cell 8 with when/when-not scenarios
- Python code in Cell 9 commented by default (safety)
- Single uncomment action to activate clearing

**Method 3: Backup-First Approach (Safest)**
```python
import shutil
from datetime import datetime

storage_path = Path('src/ice_lightrag/storage')
backup_path = Path(f'src/ice_lightrag/storage_backup_{datetime.now():%Y%m%d_%H%M%S}')
shutil.move(storage_path, backup_path)
print(f"✅ Backup created: {backup_path}")
```

### Verification After Clearing

```bash
# Check storage empty
ls src/ice_lightrag/storage/
# Should show: empty directory or no directory

# Rebuild and verify new files created
# After running ice_building_workflow.ipynb:
ls src/ice_lightrag/storage/
# Should show:
# - vdb_entities.json
# - vdb_relationships.json
# - vdb_chunks.json
# - graph_chunk_entity_relation.graphml
```

### Documentation References

- **Technical details**: `md_files/ICE_GRAPH_IMPLEMENTATION.md` lines 569-728
- **Interactive clearing**: `ice_building_workflow.ipynb` Cell 8-9
- **Switching methods**: `md_files/LOCAL_LLM_GUIDE.md` lines 146-330
- **When/when-not guidance**: All documentation provides complete scenarios
- **Best practices**: Backup-first approach, validation steps, rebuild workflows

---

## Migration Guide

### From OpenAI to Hybrid (No Rebuild)
```bash
# Step 1: Install Ollama
brew install ollama  # macOS
# or download from https://ollama.com

# Step 2: Pull model
ollama serve  # In separate terminal
ollama pull qwen3:30b-32k

# Step 3: Update environment (choose method):
# Method 1 (Terminal): export LLM_PROVIDER="ollama" ...
# Method 2 (Notebook): Use Cell 7.5 in ice_building_workflow.ipynb
# Method 3 (Magic): %env LLM_PROVIDER=ollama ...

# Step 4: Test
python updated_architectures/implementation/ice_simplified.py
```

### From Hybrid to Full Ollama (Requires Rebuild)
```bash
# Step 1: Pull embedding model
ollama pull nomic-embed-text:latest

# Step 2: Clear existing graph (REQUIRED)
# Use notebook Cell 9 in ice_building_workflow.ipynb (uncomment clearing code)
# OR use Python shutil.rmtree method

# Step 3: Update environment
export LLM_PROVIDER="ollama"
export EMBEDDING_PROVIDER="ollama"
unset OPENAI_API_KEY  # Optional, no longer needed

# Step 4: Rebuild graph
jupyter notebook ice_building_workflow.ipynb
# Run all cells to rebuild with 768-dim embeddings
```

---

## Validation Results Summary

**Test Date**: 2025-10-10
**Configuration Tested**: Hybrid mode (qwen3:30b-32k + OpenAI embeddings)

### Building Workflow ✅
- Documents processed: 2 (NVDA, TSMC earnings)
- Entities extracted: 13 nodes
- Relationships created: 8 edges
- Graph dimension: 1536-dim (compatible)

### Query Workflow ✅
- All 5 LightRAG modes tested and working:
  - LOCAL: Entity lookup ✅
  - GLOBAL: High-level summary ✅
  - HYBRID: Investment analysis ✅
  - MIX: Complex multi-aspect ✅
  - NAIVE: Simple semantic search ✅

### Multi-Hop Reasoning ✅
- Test query: "How does China market risk impact NVIDIA through its suppliers?"
- Reasoning chain: NVDA → TSMC → China risk (2-hop)
- Result: Successfully traced relationship chain with correct attribution

### Cost Validation ✅
- Hybrid mode: $2/month (60% reduction vs OpenAI)
- Quality: Maintained, comparable to pure OpenAI
- Compatibility: Full backward compatibility confirmed

---

## Future Enhancements

### Potential Improvements
1. **Auto-detection**: Automatically select best available provider
2. **Configuration UI**: Streamlit interface for easy switching
3. **Performance Profiling**: Benchmark OpenAI vs Ollama quality
4. **Hybrid Fallback**: Auto-switch to pure OpenAI if Ollama fails mid-session
5. **Multi-Model Support**: Support for additional Ollama models (llama3, mistral, etc.)

### Known Limitations
1. **Rerank Warning**: "Rerank is enabled but no rerank model configured" (cosmetic, no impact)
2. **LLM Latency**: Ollama ~10-20s vs OpenAI ~2-5s per query (acceptable trade-off)
3. **Full Ollama Dimension**: 768-dim requires graph rebuild from existing 1536-dim graphs

---

## Related Documentation

- `md_files/OLLAMA_TEST_RESULTS.md` - Comprehensive test results (500+ lines)
- `md_files/ICE_GRAPH_IMPLEMENTATION.md` - Graph architecture and management (lines 569-728)
- `md_files/LOCAL_LLM_GUIDE.md` - Ollama setup guide + provider switching methods (lines 146-330)
- `PROJECT_CHANGELOG.md` - Entry #30 (implementation), Entry #31 (testing)
- `ice_building_workflow.ipynb` - Cell 7 (provider config), Cell 7.5 (switching), Cell 8-9 (graph clearing)
- `ice_query_workflow.ipynb` - Cell 5 (provider config), Cell 5.5 (switching)