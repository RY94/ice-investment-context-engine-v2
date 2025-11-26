# Source Attribution Bug Fix - 2025-11-14

## Problem
SEC documents showing "Source: Unknown" in Cell 15 (ice_building_workflow.ipynb) ingestion display, despite having valid metadata.

## Root Cause Analysis
**Three interrelated issues identified:**

1. **Display function received only content string** (not full dict with metadata)
   - Location: `ice_simplified.py:199` (_print_document_progress)
   - Used fragile string pattern matching instead of metadata fields
   - Could not detect sources when content didn't match expected patterns

2. **Email documents missing `source` field**
   - Location: `data_ingestion.py:1939-1946`
   - Had `file_path` but no explicit `source` metadata

3. **Exa research documents missing `file_path` field**
   - Location: `data_ingestion.py:2317, 2349`
   - Had `source` but no `file_path` for traceability

## Architectural Principle Violated
From ARCHITECTURE.md:106-109:
> "Every fact, entity, relationship, and insight MUST trace to verifiable source document. Any data without source attribution is **rejected**."

**Verdict**: "Unknown" source should NEVER appear in production - it always indicates a bug in the metadata pipeline.

## Fix Implementation

### Fix #1: Metadata-First Display Function (3 locations)
**File**: `ice_simplified.py`

**Changes**:
1. Updated `_print_document_progress()` signature (line 199):
   - FROM: `doc_content: str`
   - TO: `doc_dict: Dict[str, Any]`

2. Implemented 4-tier detection logic:
   - **Tier 1**: Check `file_path` field (most reliable, O(1))
   - **Tier 2**: Check `source` field (secondary metadata)
   - **Tier 3**: Check content patterns (fallback for edge cases)
   - **Tier 4**: Legacy checks (backwards compatibility)

3. Added error logging when source is "Unknown"

4. Updated 2 call sites (lines 2140, 2226):
   - FROM: `doc_content=doc_dict['content']`
   - TO: `doc_dict=doc_dict`

### Fix #2: Email Source Metadata
**File**: `data_ingestion.py:1939-1946`

**Change**: Added `'source': 'email'` to email document dicts
```python
documents = [{
    'content': doc,
    'file_path': f"email:{metadata['filename']}",
    'source': 'email',  # NEW
    'type': 'financial'
}]
```

### Fix #3: Exa Research file_path Metadata
**File**: `data_ingestion.py:2318, 2358`

**Change**: Added `file_path` with content hash for traceability
```python
doc_hash = hashlib.md5(content[:200].encode()).hexdigest()[:8]
documents.append({
    'content': content.strip(),
    'source': 'exa_company',
    'file_path': f"exa_company:{symbol}_{doc_hash}"  # NEW
})
```

### Fix #4: Validation & Error Logging
**File**: `ice_simplified.py:338, 348`

**Change**: Upgraded logging from `warning` to `error` level
- Clearly indicates missing source attribution is a BUG
- Added defensive fallback using `source` field when available

## Impact

**Fixes**:
- ✅ SEC documents now show "SEC Filing" (not "Unknown")
- ✅ All document types display correct source
- ✅ Metadata gaps closed (email source, Exa file_path)
- ✅ Bugs visible immediately via error logs

**Benefits**:
- Metadata-first detection (fast O(1), reliable)
- Backwards compatible (keeps legacy checks)
- Generalizable (works for ALL document types)
- Pythonic (uses proper data structures)

## Testing Instructions

1. Restart notebook kernel
2. Re-run Cell 15 (ingestion) in ice_building_workflow.ipynb
3. Verify output:
   - ✅ SEC documents: "Source: SEC Filing"
   - ✅ Email documents: "Source: Email"
   - ✅ News articles: "Source: News"
   - ✅ Financial API: "Source: Financial API"
4. Check logs for no "Unknown" source errors

## Files Modified

1. `ice_simplified.py` (3 locations):
   - Line 199: _print_document_progress signature and 4-tier detection
   - Line 2140: Email call site
   - Line 2226: Ticker call site
   - Lines 338, 348: Error logging upgrade

2. `data_ingestion.py` (2 locations):
   - Lines 1939-1946: Email source metadata
   - Lines 2318, 2358: Exa file_path metadata

## Key Learnings

1. **Architecture as Contract**: Source attribution is not optional - it's a design invariant
2. **Metadata-first**: Always check structured fields before parsing content
3. **Fail Loudly**: "Unknown" should trigger errors, not silent fallbacks
4. **Defensive Programming**: Validate metadata at ingestion boundary
5. **Schema Consistency**: All fetch methods should return uniform dict structure

## Related Documentation
- ARCHITECTURE.md:106-109 (source attribution requirement)
- tmp/tmp_complete_root_cause_analysis.md (detailed analysis)
- tmp/tmp_verify_fix_logic.py (test validation - all 7 tests passed)
