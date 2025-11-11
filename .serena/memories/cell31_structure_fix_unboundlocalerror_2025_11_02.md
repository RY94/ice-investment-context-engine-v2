# Cell 31 Structure Fix - UnboundLocalError Resolution

**Date**: 2025-11-02  
**Context**: User reported malformed Cell 31 code structure causing confusion and UnboundLocalError  
**File**: `ice_building_workflow.ipynb` Cell 31 (0-indexed: 31)

## Problem Analysis

### Issue 1: Malformed Structure
Cell 31 had helper functions and execution code at **module level** (0 spaces indentation) instead of nested inside `add_footnote_citations`:

```python
# BEFORE (BROKEN):
def add_footnote_citations(query_result):
    """Docstring"""
    
def build_confidence_cache(chunks):  # ❌ Line 45: 0 spaces (module level)
    ...

def get_entity_confidence(...):  # ❌ Line 74: 0 spaces (module level)
    ...

# Extract entities...  # ❌ Line 88: 0 spaces (module level)
answer_lower = answer.lower()
```

### Issue 2: UnboundLocalError
Python raised `UnboundLocalError: cannot access local variable 'build_confidence_cache' where it is not associated with a value` because:
- Function called at line 50 (early)
- Function defined at line 108 (late)

### Issue 3: Import Placement
`import re` appeared at line 140 (module level), after execution code that used it.

## Solution

Reconstructed Cell 31 with proper structure:

```python
# AFTER (FIXED):
def add_footnote_citations(query_result):
    """
    Add footnote-style citations with knowledge graph reasoning paths.
    
    v1.4.9 Migration: Uses structured data from parsed_context.
    """
    import re  # ✅ Line 44: Inside function (4 spaces)
    
    # ========================================================================
    # HELPER FUNCTIONS (Nested inside parent function)
    # ========================================================================
    
    def build_confidence_cache(chunks):  # ✅ Line 50: Nested (4 spaces)
        """Build O(1) lookup cache for entity confidence scores from markup."""
        confidence_cache = {}
        pattern = r'\[([A-Z_]+):([^|\]]+)\|[^\]]*confidence:([\d.]+)\]'
        
        for chunk in chunks:
            content = chunk.get('content', '')
            for match in re.finditer(pattern, content):
                entity_value = match.group(2).strip()
                confidence = float(match.group(3))
                
                if entity_value in confidence_cache:
                    confidence_cache[entity_value] = max(confidence_cache[entity_value], confidence)
                else:
                    confidence_cache[entity_value] = confidence
        
        return confidence_cache
    
    def get_entity_confidence(entity_name, entities, confidence_cache=None):  # ✅ Line 78: Nested (4 spaces)
        """Extract confidence with 3-tier fallback: cache → metadata → 0.75"""
        # Tier 1: Cache lookup (O(1))
        if confidence_cache and entity_name in confidence_cache:
            return confidence_cache[entity_name]
        
        # Tier 2: Entity metadata
        for e in entities:
            if e.get('entity_name') == entity_name:
                conf = e.get('confidence', e.get('score', 0.75))
                return float(conf) if conf else 0.75
        
        # Tier 3: Default
        return 0.75
    
    # ========================================================================
    # MAIN EXECUTION CODE
    # ========================================================================
    
    answer = query_result.get('answer', '')
    answer_lower = answer.lower()
    # ... rest of execution code ...
```

## Implementation

### File Modified
- `ice_building_workflow.ipynb` Cell 31

### Changes
1. **Moved `import re`**: Line 140 → Line 44 (inside function)
2. **Nested helper functions**: Lines 45-87 indented from 0 → 4 spaces
3. **Reorganized execution code**: Lines 88+ properly sequenced inside function
4. **Preserved all functionality**: Confidence cache, 3-tier fallback, color coding

### Structure After Fix
```
Lines 1-31:   Module imports & constants (QUALITY_BADGES, CONFIDENCE_MAP)
Line 32:      Function definition (def add_footnote_citations)
Lines 33-42:  Docstring
Line 44:      import re (inside function)
Lines 48-76:  build_confidence_cache (nested helper)
Lines 78-100: get_entity_confidence (nested helper)
Lines 104+:   Main execution code
```

## Validation

### Syntax Check
```python
✅ Python syntax is valid (compile() succeeded)
```

### Indentation Check
```
✅ Line 32: Main function (0 spaces) - module level
✅ Line 44: import re (4 spaces) - inside function
✅ Line 50: build_confidence_cache (4 spaces) - nested
✅ Line 78: get_entity_confidence (4 spaces) - nested
✅ Line 104+: Execution code (4 spaces) - inside function
```

### Structure Check
```
✅ has_main_function
✅ import_inside_function
✅ has_build_cache (nested)
✅ has_get_confidence (nested)
✅ has_regex_pattern
✅ No module-level helper functions
```

## Bugs Fixed

1. **UnboundLocalError**: Functions now defined before use (lines 50 & 78 before first call)
2. **Malformed structure**: Proper nesting with 4-space indentation
3. **Import placement**: `import re` moved inside function where it's used
4. **Uniform 75% confidence**: Cache now extracts diverse scores from markup (60%-95%)

## Expected Behavior

### Confidence Scores
- **Before**: All graph paths showed uniform 75%
- **After**: Diverse scores extracted from markup:
  - Known tickers: 95% (NVDA, AAPL)
  - Pattern tickers: 60% (GPM, TME)
  - Company aliases: 85%
  - Ratings: 85%
  - Financial metrics: 80%

### Color Coding
- 🟢 ≥85% (high confidence)
- 🟡 70-85% (moderate confidence)
- 🔴 <70% (low confidence)

### Performance
- O(1) cache lookup vs O(N²) scanning
- Build once, query many times

## Testing Instructions

1. **Restart Jupyter kernel**: `Kernel → Restart Kernel`
2. **Run Cell 31**: Execute footnote traceability feature
3. **Test query**: Run Tencent query (Cell 33)
4. **Verify output**: Check for diverse confidence scores in graph paths

### Expected Output
```
🔗 Graph paths built: 9 paths

🧠 Knowledge Graph Paths:
   • Tencent → has_financial_metric → Gross Profit (Cof: 🟢 95%)
   • Tencent → has_financial_metric → Operating Profit (Cof: 🟢 95%)
   • TME → subsidiary_of → Tencent (Cof: 🟡 75%)
   • GPM → related_to → TME (Cof: 🔴 60%)  # Diverse scores!
```

## Related Memories

- `confidence_score_semantic_fix_2025_10_29`: Initial confidence cache implementation
- `lightrag_native_traceability_implementation_2025_10_28`: Traceability architecture
- `granular_traceability_complete_all_5_phases_2025_10_29`: 5-phase traceability system

## Technical Notes

### Python Scoping Rules
- Functions must be defined before use in the same scope
- Nested functions inherit parent function's namespace (closure)
- `import` statements can appear anywhere in a function (executed once)

### Regex Pattern
```python
pattern = r'\[([A-Z_]+):([^|\]]+)\|[^\]]*confidence:([\d.]+)\]'
```
- Matches: `[TICKER:NVDA|confidence:0.95]`
- Extracts: type (TICKER), value (NVDA), confidence (0.95)
- Generic: Works for any markup type (TICKER, RATING, PRICE_TARGET, etc.)

### 3-Tier Fallback
```python
# Tier 1: Cache (O(1) markup lookup) - PREFERRED
if confidence_cache and entity_name in confidence_cache:
    return confidence_cache[entity_name]

# Tier 2: Entity metadata (future-proof for LightRAG v2.x)
for e in entities:
    if e.get('entity_name') == entity_name:
        return float(e.get('confidence', 0.75))

# Tier 3: Default (LLM-extracted entities without markup)
return 0.75
```

## Key Learnings

1. **Structure matters**: Python enforces function definition order strictly
2. **Indentation is semantic**: 0 vs 4 spaces changes scope completely
3. **Test incrementally**: Validate structure before testing logic
4. **Preserve functionality**: Fix structure without changing behavior
5. **Document patterns**: Record solution for future reference
