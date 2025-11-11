# SOURCE_EMAIL Regex Fix for Malformed Markers

**Date**: 2025-10-29
**Issue**: 4 out of 5 sources showing as "unknown" in query results
**Root Cause**: SOURCE_EMAIL markers in storage have extra `|subject:` field at end that parser didn't expect

## Problem

**Stored Marker Format** (found in `ice_lightrag/storage/kv_store_full_docs.json`):
```
[SOURCE_EMAIL:Tencent Q2 2025 Earnings|sender:"Jia Jun (AGT Partners)" <jiajun@agtpartners.com.sg>|date:Sun, 17 Aug 2025 10:59:59 +0800|subject:Tencent Q2 2025 Earnings]
```

**Expected Format** (from Phase 1 tests):
```
[SOURCE_EMAIL:Tencent Q2 2025 Earnings|sender:Jia Jun (AGT Partners)|date:Thu, 15 Aug 2025 10:30:45 +0800]
```

**Issue**: Extra `|subject:Tencent Q2 2025 Earnings` at the end (4 fields instead of 3)

## Original Regex Pattern

```python
# src/ice_lightrag/context_parser.py line 53 (before fix)
'email': re.compile(r'\[SOURCE_EMAIL:([^\|]+)\|sender:([^\|]+)\|date:([^\]]+)\]')
```

**Problem**: The `date` capture group would match `Sun, 17 Aug 2025 10:59:59 +0800|subject:Tencent Q2 2025 Earnings` (includes the extra |subject: part), breaking date parsing and causing chunks to be classified as "unknown".

## Fixed Regex Pattern

```python
# src/ice_lightrag/context_parser.py line 53 (after fix)
'email': re.compile(r'\[SOURCE_EMAIL:([^\|]+)\|sender:([^\|]+)\|date:([^\|]+?)(?:\|subject:[^\]]+)?\]')
```

**Key Changes**:
1. Changed `date:([^\|]+)` to `date:([^\|]+?)` - non-greedy match stops before optional |subject:
2. Added `(?:\|subject:[^\]]+)?` - optional non-capturing group for the extra |subject: field

## Validation

**Test Results** (`tmp/tmp_test_regex_fix.py`):
- ✅ Original format (3 fields): Correctly parsed
- ✅ Malformed format (4 fields): Correctly parsed
- ✅ Dates extracted correctly: 2025-08-15 and 2025-08-17
- ✅ Both recognized as "email" source type

## Files Modified

- `src/ice_lightrag/context_parser.py` line 53 - Updated regex pattern

## Impact

**Before Fix**: 4/5 sources showed as "unknown" because malformed markers failed to parse
**After Fix**: All email sources should now parse correctly regardless of format

## Notes

- The malformed format appears to have duplicate subject information (unlabeled first field + labeled |subject: at end)
- This fix provides backward compatibility for both formats
- The root cause of WHY markers are being created with this format needs separate investigation (likely in email ingestion pipeline)

## Related Issues

- Only 1 document found in storage (expected 178) - suggests incomplete graph building
- Todo: Investigate email pipeline where SOURCE_EMAIL markers are created

## Testing

Run notebook Cell 31 with query "what is tencent's operating margin in q2 2025?" to verify sources no longer show as "unknown".
