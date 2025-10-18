# Method 4 (Pure LLM) Design Decision - No Preprocessing

**Date**: 2025-10-13
**File**: `src/ice_lightrag/graph_categorization.py`
**Function**: `categorize_entity_llm_only()` (lines 368-420)

## Design Decision

**Method 4 is TRULY pure LLM with NO rule-based preprocessing.**

### What Was Removed

**Lines 389-391 (deleted)**:
```python
# Early return for date entities (temporal metadata, not investment entities)
if _is_date_entity(entity_name):
    return ('Other', 0.50)
```

### Rationale

**Purpose of Method 4**: Benchmarking and testing true LLM categorization performance

**Why remove preprocessing:**
1. **Honest comparison**: Shows actual LLM behavior vs keyword approaches
2. **True benchmarking**: Can measure LLM accuracy on all entity types (including dates)
3. **Semantic testing**: LLM might handle edge cases differently/better
4. **Name matches behavior**: "Pure LLM" means no rule-based logic

**Trade-offs accepted:**
- ❌ Method 4 may differ from Methods 1-3 on dates (by design, acceptable for testing)
- ❌ Slower (~1-2s per date entity, acceptable for benchmarking)
- ❌ More Ollama calls (acceptable for research purposes)

## Behavior Comparison

### Methods 1-3 (Keyword-Based)
```python
# All use _is_date_entity() preprocessing
if _is_date_entity("October 2, 2025"):
    return 'Other'  # or ('Other', 0.50)
# → Deterministic, guaranteed "Other" for dates
```

### Method 4 (Pure LLM)
```python
# No preprocessing - send directly to LLM
prompt = f"Categorize this financial entity into ONE category.\n"
         f"Entity: October 2, 2025\n"
         f"Categories: Company, Financial Metric, ...\n"
llm_category = _call_ollama(prompt)
# → LLM decides, may differ from keyword methods
```

## Expected Outcomes

**For dates like "October 2, 2025":**
- **Methods 1-3**: Always return "Other" (date detection active)
- **Method 4**: LLM categorization (may be "Other", "Regulation/Event", or invalid)

**This divergence is INTENTIONAL and ACCEPTABLE for testing purposes.**

## Updated Docstring

```python
def categorize_entity_llm_only(...):
    """
    Pure LLM categorization using local Ollama model (no preprocessing).

    Uses Ollama LLM for ALL entities with NO rule-based preprocessing.
    This includes dates, which other methods handle with _is_date_entity().

    Useful for benchmarking true LLM accuracy vs keyword/hybrid approaches.
    May categorize dates differently than keyword methods (by design).
    """
```

## Cell 12 Notebook Testing

When running Cell 12, expect:
- **TEST 1-3**: Dates → "Other" (consistent, rule-based)
- **TEST 4**: Dates → LLM decision (may differ, semantic-based)
- **Comparison stats**: Will show divergence rate between keyword and pure LLM

This is the correct behavior for honest LLM benchmarking.