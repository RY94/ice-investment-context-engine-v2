# CSV to XLSX Migration & Column Standardization

**Date**: 2025-11-08
**Purpose**: Document migration from CSV to XLSX format and column name standardization
**Context**: RAGAS evaluation framework integration, MinimalEvaluator compatibility

---

## Migration Summary

### Files Migrated
1. **test_queries.csv → test_queries.xlsx**
   - 12 portfolio analysis queries
   - Original columns: query_id, persona, query, complexity, recommended_mode, use_case
   - **Column change**: `query` renamed to `query_text` for evaluator compatibility

2. **test_queries_1.csv → test_queries_1.xlsx**  
   - 8 queries with validated ground truth from email samples
   - Original columns: query_id, user_input, reference, category, source_email
   - **Column added**: `query_text` (copy of `user_input`) for evaluator compatibility
   - Final columns: query_id, query_text, user_input, reference, category, source_email

### CSV Files Deleted
- ✅ `test_queries.csv` - Replaced by test_queries.xlsx
- ✅ `test_queries_1.csv` - Replaced by test_queries_1.xlsx

---

## Column Naming Rationale

### Problem
Three different column names for the same data:
- **test_queries.csv**: Used `query` column
- **test_queries_1.csv**: Used `user_input` column (RAGAS standard)
- **MinimalEvaluator**: Expects `query_text` column (line 129-130)

### Solution: Dual Column Strategy
- **test_queries.xlsx**: Standardized to `query_text` (matches evaluator)
- **test_queries_1.xlsx**: Keeps both `query_text` AND `user_input`
  - `user_input`: RAGAS standard field
  - `query_text`: MinimalEvaluator requirement (copy of user_input)

### Benefits
1. **Evaluator compatibility**: Both files have `query_text` column (no runtime conversion needed)
2. **RAGAS compatibility**: test_queries_1.xlsx keeps `user_input` for RAGAS metrics
3. **Simplified notebook logic**: Removed runtime conversion code from Cell 23
4. **Better file format**: XLSX provides better structure, formatting, data validation

---

## Code Changes

### ice_query_workflow.ipynb Cell 23
**Before**:
```python
test_queries_filename = 'test_queries.csv'
test_queries_df = pd.read_csv(test_queries_filename)

# Runtime conversion logic (REMOVED)
if 'query_text' not in test_queries_df.columns and 'query' in test_queries_df.columns:
    test_queries_df['query_text'] = test_queries_df['query']
```

**After**:
```python
test_queries_filename = 'test_queries.xlsx'
test_queries_df = pd.read_excel(test_queries_filename, engine='openpyxl')

# Validate required columns (simplified - no conversion needed)
if 'query_id' not in test_queries_df.columns:
    test_queries_df['query_id'] = [f"Q{i+1}" for i in range(len(test_queries_df))]
```

### Why Conversion Logic Removed
- Files now have `query_text` column built-in
- No need for runtime pandas DataFrame manipulation
- Cleaner, more maintainable code

---

## Technical Implementation

### Conversion Script
```python
import pandas as pd

# 1. test_queries.csv → test_queries.xlsx (rename column)
df = pd.read_csv('test_queries.csv')
df = df.rename(columns={'query': 'query_text'})
df.to_excel('test_queries.xlsx', index=False, engine='openpyxl')

# 2. test_queries_1.csv → test_queries_1.xlsx (add query_text)
df1 = pd.read_csv('test_queries_1.csv')
df1['query_text'] = df1['user_input']  # Dual column support
cols = ['query_id', 'query_text', 'user_input', 'reference', 'category', 'source_email']
df1 = df1[cols]
df1.to_excel('test_queries_1.xlsx', index=False, engine='openpyxl')

# 3. Delete old CSV files
os.remove('test_queries.csv')
os.remove('test_queries_1.csv')
```

### Validation Tests Run
✅ XLSX files load successfully with `pd.read_excel(engine='openpyxl')`
✅ Both files contain `query_text` column
✅ test_queries_1.xlsx contains both `query_text` and `user_input`
✅ MinimalEvaluator accepts both files (query_text column present)
✅ RAGAS compatibility confirmed (user_input column present)
✅ Notebook Cell 23 loads files without errors
✅ End-to-end evaluation workflow tested

---

## RAGAS Compatibility Notes

### RAGAS Standard Fields
- **Required**: `user_input` (the query text)
- **Optional**: `reference` (ground truth), `contexts`, `response`

### ICE Files Mapping
- **test_queries.xlsx**: Uses `query_text` (evaluator-first design)
- **test_queries_1.xlsx**: Uses both `query_text` + `user_input` (dual support)

### Why Both Column Names?
RAGAS is DataFrame-agnostic (works with any format), but has conventional field names. By supporting both `query_text` (evaluator) and `user_input` (RAGAS), we ensure compatibility with:
1. ICE's MinimalEvaluator (requires query_text)
2. RAGAS framework (expects user_input)
3. Future evaluation tools

---

## Key Learning: Column Naming Consistency

**Lesson**: When integrating external frameworks (MinimalEvaluator, RAGAS), align on standard column names early to avoid runtime conversion logic.

**Best Practice**: 
- Document expected column names in tool requirements
- Standardize files to match tool expectations
- Use dual columns when supporting multiple standards
- Avoid runtime DataFrame manipulation when possible

---

## References

- **Evaluator**: `/src/ice_evaluation/minimal_evaluator.py` (lines 129-130)
- **Notebook**: `/ice_query_workflow.ipynb` Cell 23
- **RAGAS Docs**: `/project_information/about_ragas/08_for_ice_integration.md`
- **Session Notes**: `/PROGRESS.md` (2025-11-08 session)
