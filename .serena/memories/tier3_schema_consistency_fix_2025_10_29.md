# Tier 3 Schema Consistency Fix - Display Layer Compatibility

**Date**: 2025-10-29
**Context**: Addendum to `lightrag_native_traceability_implementation_2025_10_28`
**Issue**: Tier 3 chunks displaying as "Email: Unknown" despite correct source_type attribution
**Root Cause**: Schema mismatch between Tier 2 and Tier 3 `source_details` structure

## Problem Discovery

**User Query Output** showed inconsistent display:
- 1 chunk: "📧 Email: Tencent Q2 2025 Earnings" (confidence: 0.9) ✅
- 4 chunks: "📧 Email: Unknown" (confidence: 0.7) ❌

**All 5 chunks from same email file**, but only 1 displayed properly.

## Root Cause Analysis

**Tier 2 Schema** (inline SOURCE markers):
```python
{
    "source_type": "email",
    "source_details": {
        "subject": "Tencent Q2 2025 Earnings",  # ✅ Has subject
        "sender": '"Jia Jun (AGT Partners)" <jiajun@agtpartners.com.sg>',
        "raw_date": "Sun, 17 Aug 2025 10:59:59 +0800"
    },
    "confidence": 0.9,
    "date": "2025-08-17"
}
```

**Tier 3 Schema (BEFORE FIX)** (file_path fallback):
```python
{
    "source_type": "email",
    "source_details": {
        "filename": "Tencent Q2 2025 Earnings.eml",  # ❌ No subject
        "extraction_method": "file_path_fallback"
    },
    "confidence": 0.7,
    "date": None
}
```

**Display Code** (ice_building_workflow.ipynb):
```python
def format_email_display(chunk):
    source_details = chunk.get('source_details', {})
    email_name = source_details.get('subject', 'Unknown')  # ← Expects 'subject' key
    return f"📧 Email: {email_name}"
```

**Result**: Tier 3 chunks missing `subject` key → displayed as "Unknown"

## Solution

**File**: `/src/ice_lightrag/context_parser.py:322-335`

**Fix Applied** (2 lines added):
```python
if source_type_prefix == 'email':
    # Parse filename to extract subject (remove .eml extension)
    subject = details.rsplit('.eml', 1)[0] if details.endswith('.eml') else details

    return {
        "source_type": "email",
        "source_details": {
            "subject": subject,  # ✅ Add for display compatibility with Tier 2
            "filename": details,
            "extraction_method": "file_path_fallback"
        },
        "confidence": 0.70,
        "date": None
    }
```

**Parsing Logic**:
- Input: `"email:Tencent Q2 2025 Earnings.eml"` (file_path format)
- Extract details: `"Tencent Q2 2025 Earnings.eml"`
- Parse subject: `"Tencent Q2 2025 Earnings"` (remove .eml extension)
- Add to source_details for display compatibility

## Impact

**Before Fix**:
- 1 chunk (Tier 2): "📧 Email: Tencent Q2 2025 Earnings" (confidence: 0.9)
- 4 chunks (Tier 3): "📧 Email: Unknown" (confidence: 0.7) ❌

**After Fix**:
- 1 chunk (Tier 2): "📧 Email: Tencent Q2 2025 Earnings" (confidence: 0.9)
- 4 chunks (Tier 3): "📧 Email: Tencent Q2 2025 Earnings" (confidence: 0.7) ✅

## Validation

**Test Script**: `tmp/tmp_validate_tier3_logic.py` (deleted after validation)

**Results**:
```
✅ Has 'subject' key: True
✅ Subject value: 'Tencent Q2 2025 Earnings'
✅ Schema consistent with Tier 2
✅ Display shows proper email name
```

## Design Rationale

**Why Confidence Levels Differ** (by design, not a bug):
- **Tier 2 (0.9)**: High confidence - inline markers explicitly provided by data layer
- **Tier 3 (0.7)**: Moderate confidence - derived from file_path, less specific metadata
- **Default (0.3)**: Low confidence - no markers, no file_path

**Confidence levels appropriately reflect attribution quality/specificity.**

## Key Learnings

1. **Schema Consistency Critical**: Display layer depends on consistent source_details structure across all tiers
2. **Minimal Fix**: 2 lines added to parse filename and add subject key
3. **Tier System Working**: All 3 tiers functioning correctly:
   - Tier 1: LightRAG native file_paths tracking ✅
   - Tier 2: Inline SOURCE marker extraction ✅
   - Tier 3: file_path fallback with schema consistency ✅

## Related Files

- `/src/ice_lightrag/context_parser.py` (Tier 2 & 3 parsing)
- `/ice_building_workflow.ipynb` (Display formatting)
- `/ice_lightrag/storage/kv_store_text_chunks.json` (Tier 1 storage)

## Related Memories

- `lightrag_native_traceability_implementation_2025_10_28` (3-tier architecture)
- `query_level_traceability_implementation_2025_10_28` (end-to-end flow)
