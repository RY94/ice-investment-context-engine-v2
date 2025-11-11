# Jupyter Notebook Cell Dependency - Defensive Programming Pattern

**Date**: 2025-11-07
**Context**: Notebook variable dependency error fix in `ice_query_workflow.ipynb` Cell 22
**Pattern Type**: Defensive error handling for Jupyter notebook variable dependencies

---

## Problem Pattern

**Common Issue**: Jupyter notebooks with cells that depend on variables created in other cells
- Cells in physical order may not match correct execution order
- Running cells out of sequence causes `NameError: name 'variable_name' is not defined`
- Silent failures or confusing error messages for users

**Example Case** (`ice_query_workflow.ipynb` Section 5):
- Physical order: Cell 22 (display) → Cell 23 (evaluate) → Cell 24 (load)
- Correct execution order: Cell 25 (header) → Cell 24 (load) → Cell 23 (evaluate) → Cell 22 (display)
- Variable dependencies: `test_queries_df` (Cell 24) → `results_df` (Cell 23) → display (Cell 22)

---

## Defensive Pattern Solution

### Code Template

```python
# ============================================================================
# Section X.Y: Cell Description
# ============================================================================
# DEPENDENCY CHECK: This cell requires variables from previous cells
# Run cells in this order: Cell A → Cell B → Cell C → Cell D (this cell)

if 'required_variable' not in dir():
    print("⚠️  ERROR: Required variable not found")
    print("=" * 60)
    print("\n📋 Section X cells must be run in order:")
    print("   1️⃣  Cell A: Description → creates 'variable_a'")
    print("   2️⃣  Cell B: Description → creates 'variable_b'")
    print("   3️⃣  Cell C: Description → uses 'variable_b', creates 'required_variable'")
    print("   4️⃣  Cell D: Description → uses 'required_variable' ⬅️ YOU ARE HERE")
    print("\n⚡ Quick fix: Run Cell A, then Cell B, then Cell C, then re-run this cell")
    print("=" * 60)
    raise NameError("Variable 'required_variable' not defined. Run cells in sequence (A → B → C → D)")

# Original cell logic here (unchanged)
```

### Key Components

1. **Variable Existence Check**: `if 'variable_name' not in dir():`
   - Uses Python's `dir()` to check if variable exists in current namespace
   - Works for any variable type (DataFrame, dict, list, etc.)

2. **User-Friendly Error Message**:
   - Clear header: "⚠️  ERROR: Required variable not found"
   - Numbered execution order with emojis (1️⃣ 2️⃣ 3️⃣ 4️⃣)
   - Visual indicator showing current cell position (⬅️ YOU ARE HERE)
   - Quick fix guidance with exact cell execution sequence

3. **Explicit NameError**:
   - Raises descriptive `NameError` with execution sequence
   - Prevents silent failures
   - Error message guides user to correct action

4. **Zero Behavioral Changes**:
   - Original cell logic preserved unchanged
   - Only adds defensive check at the start
   - No performance impact when dependencies satisfied

---

## Implementation Example (Cell 22)

**File**: `ice_query_workflow.ipynb` Cell 22

```python
# ============================================================================
# Section 5.3: Display Evaluation Results
# ============================================================================
# DEPENDENCY CHECK: This cell requires variables from previous cells
# Run cells in this order: Cell 25 (header) → Cell 24 (load) → Cell 23 (evaluate) → Cell 22 (display)

if 'results_df' not in dir():
    print("⚠️  ERROR: Evaluation results not found")
    print("=" * 60)
    print("\n📋 Section 5 cells must be run in order:")
    print("   1️⃣  Cell 25: Read section header (markdown)")
    print("   2️⃣  Cell 24: Load test queries → creates 'test_queries_df'")
    print("   3️⃣  Cell 23: Run evaluation → creates 'results_df'")
    print("   4️⃣  Cell 22: Display results → uses 'results_df' ⬅️ YOU ARE HERE")
    print("\n⚡ Quick fix: Run Cell 24, then Cell 23, then re-run this cell")
    print("=" * 60)
    raise NameError("Variable 'results_df' not defined. Run evaluation cells in sequence (24 → 23 → 22)")

# Display evaluation results
print("\n📊 Evaluation Results Summary")
# ... original display logic ...
```

---

## Benefits

**Defensive Programming:**
- ✅ No silent failures - explicit error with clear guidance
- ✅ Variable flow checking - verifies dependencies before use
- ✅ User experience - numbered steps with visual indicators
- ✅ Zero behavioral changes - display logic preserved

**Generalizability:**
- Applies to any Jupyter notebook variable dependencies
- Template for defensive checks in other cells
- Encourages best practices for notebook development
- Pattern works across Python notebooks, R notebooks, etc.

---

## When to Use This Pattern

**Apply this pattern when:**
1. Cell depends on variables created in other cells
2. Execution order matters for correctness
3. Cell is part of a multi-step workflow (Section 1 → 2 → 3)
4. Cell is used by others who may not know execution order
5. Silent failures could confuse users

**Skip this pattern when:**
1. Cell is self-contained (no external dependencies)
2. Cell creates variables but doesn't use external ones
3. Cell is purely markdown documentation
4. Dependencies are obvious from immediate context

---

## Related Files

- **Implementation**: `ice_query_workflow.ipynb` Cell 22
- **Documentation**: `PROJECT_CHANGELOG.md` entry #120
- **Session Notes**: `PROGRESS.md` (2025-11-07 session)

---

## Design Principles Applied

1. **KISS (Keep It Simple, Stupid)**: Simple `if` check + error message
2. **Fail Fast**: Detect error immediately before attempted use
3. **Transparency First**: Honest error reporting with clear guidance
4. **YAGNI (You Aren't Gonna Need It)**: Minimal code, no over-engineering
5. **Robustness**: Handles edge cases (variable existence) gracefully
