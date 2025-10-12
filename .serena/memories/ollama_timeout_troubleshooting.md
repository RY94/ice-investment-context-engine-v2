# Ollama Timeout Troubleshooting: Entity Extraction Failures

## Problem Pattern
**Symptom**: `httpx.ReadTimeout` during LightRAG entity extraction in `ice_building_workflow.ipynb`
**Error Location**: LightRAG's `extract_entities` function during document processing
**Root Cause**: Large Ollama models (30B parameters) timing out on large documents

## Specific Error Example
```
ERROR: LLM func: Error in decorated function for task 13254142160_436983.318345125
ERROR: Failed to extract entities and relationships: Chunks[1/1]
httpx.ReadTimeout
```

## Root Cause Analysis
1. **Model Size**: `qwen3:30b-32k` (30B parameters) is slow for real-time extraction
2. **Document Volume**: 2 years historical data creates large documents (thousands of tokens)
3. **Timeout Cascade**: HTTP client timeout (60s) < LLM function timeout (180s)
4. **Context Window**: Large context windows (32k) increase processing time

## Solution: Two-Parameter Fix

### Fix 1: Reduce Data Volume
**File**: `ice_building_workflow.ipynb`, Cell 21
**Change**: `years=2` → `years=1`
**Impact**: 50% less data, faster processing, reduced timeout risk

### Fix 2: Switch to Faster Ollama Model
**File**: `ice_building_workflow.ipynb`, Cell 8
**Change**: Add `os.environ['LLM_MODEL'] = 'llama3.1:8b'`
**Impact**: 4x faster processing (8B vs 30B model), maintains free cost

## Implementation Details

### Model Configuration Pattern
The system reads `LLM_MODEL` environment variable in `src/ice_lightrag/model_provider.py:121`:
```python
model_name = os.getenv("LLM_MODEL", "qwen3:30b-32k")  # Default to 30B
```

Setting the variable in Cell 8 overrides the default when Cell 10 calls `create_ice_system()` (system reinitialization).

### Recommended Faster Models
- **llama3.1:8b** (recommended): Fast, 128k context, good quality
- **qwen2.5:7b**: Very fast, 32k context, same family
- **mistral:7b-instruct**: Fast, good reasoning for financial analysis

### Prerequisites
Ensure the target model is pulled:
```bash
ollama pull llama3.1:8b
```

## Notebook Workflow Context
**Critical cells**:
- Cell 3: Initial `ice = create_ice_system()` (uses defaults)
- Cell 8: Set environment variables (LLM_PROVIDER, EMBEDDING_PROVIDER, LLM_MODEL)
- Cell 10: **Re-initialize** `ice = create_ice_system()` (reads new env vars)
- Cell 21: Data ingestion with `years` parameter

**Restart kernel requirement**: Environment variable changes require kernel restart for full effect.

## Verification Steps
After applying fix:
1. Run Cell 8 (set env vars with llama3.1:8b)
2. Run Cell 10 (reinitialize system)
3. Run Cell 21 (ingest with years=1)
4. Monitor logs for successful entity extraction
5. Verify no `httpx.ReadTimeout` errors

## Related Files
- `ice_building_workflow.ipynb` - Primary workflow notebook (Cell 8, Cell 21)
- `src/ice_lightrag/model_provider.py:121` - Model selection logic
- `updated_architectures/implementation/ice_simplified.py` - System orchestrator
- `md_files/LOCAL_LLM_GUIDE.md` - Ollama setup documentation

## Key Learnings
- **Model selection matters**: 8B models sufficient for financial entity extraction
- **Data volume impacts**: Reduce years parameter for faster testing
- **Environment variables**: Cell 10 reinitialization enables runtime provider switching
- **Minimal changes**: 2 one-line edits solve complex timeout issues
