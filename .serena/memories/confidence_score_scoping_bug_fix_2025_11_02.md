# Confidence Score Scoping Bug Fix (November 2, 2025)

## Bug Report

**Error**: `UnboundLocalError: cannot access local variable 'build_confidence_cache' where it is not associated with a value`

**Location**: `ice_building_workflow.ipynb` Cell 31, line 50

**User Impact**: Notebook crashed when running query after implementing confidence fix

## Root Cause

**Python Scoping Rule Violation**: Functions must be DEFINED before USE within the same scope.

**What Happened**:
```python
def add_footnote_citations(query_result):
    # Line 50: CALL to build_confidence_cache
    confidence_cache = build_confidence_cache(chunks)  # ❌ ERROR
    
    # ... 50+ lines of code ...
    
    # Line 108: DEFINITION of build_confidence_cache  
    def build_confidence_cache(chunks):  # ❌ TOO LATE
        ...
```

**Why It Failed**:
- Both `build_confidence_cache` and `get_entity_confidence` are nested inside `add_footnote_citations`
- Initial implementation placed definitions AFTER their first use (lines 108, 136)
- Python reads top-to-bottom: when line 50 executes, line 108 hasn't been read yet
- Result: `UnboundLocalError` because function doesn't exist at call time

## Solution

**Move helper functions to TOP** of `add_footnote_citations`, right after docstring:

```python
def add_footnote_citations(query_result):
    """Docstring..."""
    
    # Helper functions defined FIRST (lines 45-110)
    def build_confidence_cache(chunks):
        ...
    
    def get_entity_confidence(entity_name, entities, confidence_cache=None):
        ...
    
    # Now they can be called (line 145)
    confidence_cache = build_confidence_cache(chunks)  # ✅ WORKS
```

## Implementation

**File Modified**: `ice_building_workflow.ipynb` Cell 31

**Changes**:
1. Extracted `build_confidence_cache` (28 lines) from line 107
2. Extracted `get_entity_confidence` (64 lines) from line 135
3. Moved BOTH to line 45 (after `add_footnote_citations` docstring)
4. Order now correct: DEFINE → USE

**Before** (broken):
```
Line 32:  def add_footnote_citations(...)
Line 50:  confidence_cache = build_confidence_cache(chunks)  # ❌ ERROR
Line 107: def build_confidence_cache(...)  # Too late
Line 135: def get_entity_confidence(...)
```

**After** (fixed):
```
Line 32:  def add_footnote_citations(...)
Line 45:  def build_confidence_cache(...)  # Moved up
Line 74:  def get_entity_confidence(...)  # Moved up
Line 145: confidence_cache = build_confidence_cache(chunks)  # ✅ WORKS
```

## Testing

**Verification**:
- ✅ Functions ordered correctly: DEFINE before USE
- ✅ Nested scope preserved (still inside `add_footnote_citations`)
- ✅ No logic changes, pure reordering

**Next Step**: User needs to restart kernel and re-run Cell 31

## Why Nested Functions?

**Design Decision**: Keep helpers nested (not module-level) because:
1. **Encapsulation**: Only used within `add_footnote_citations`
2. **Namespace cleanliness**: Don't pollute Cell 31 namespace
3. **Logical grouping**: Helpers are implementation details

## Related Memory

See `confidence_score_semantic_fix_2025_11_02` for the original feature implementation.

This memory documents the scoping bug fix that followed.
