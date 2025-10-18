# Date Entity Categorization Fix - Word Boundary Detection

**Date**: 2025-10-13
**File**: `src/ice_lightrag/graph_categorization.py`
**Problem**: Date detection using substring matching created false positives

## Original Bug

**Substring Matching Implementation**:
```python
if any(month in name_upper for month in ['JANUARY', ...]):
    return 'Other'
```

**False Positives**:
- "MAYBANK CORPORATION" → "Other" (contains "MAY")
- "MERCHANT BANK" → "Other" (contains "MARCH")
- Unintentional cover-up: Tests only validated dates, not false positives

## Final Solution

**Helper Function** (lines 55-79):
```python
def _is_date_entity(entity_name: str) -> bool:
    """Date detection with word boundary + digit requirement."""
    import re
    words = set(re.split(r'[^A-Z]+', entity_name.upper()))
    has_month = any(month in words for month in MONTH_NAMES)
    has_digit = any(char.isdigit() for char in entity_name)
    return has_month and has_digit
```

**Two-Part Heuristic**:
1. **Word boundary matching**: Month must be complete word, not substring
2. **Digit requirement**: True dates have numbers (day/year)

## Test Results

✅ **Dates (month + digit)**:
- "October 2, 2025" → "Other" ✅
- "January 15" → "Other" ✅

✅ **Companies with month substrings (word boundary fix)**:
- "MAYBANK CORPORATION" → "Company" ✅ (was: "Other")

✅ **Companies with month names but no digits**:
- "APRIL TECHNOLOGIES" → "Other" (no company suffix, expected)
- "DECEMBER CAPITAL GROUP" → "Company" (has "GROUP" suffix)

✅ **All keyword modes consistent** (TEST 1-3)

**Note**: Pure LLM mode (TEST 4) may differ due to semantic understanding

## Key Design Decisions

1. **Month + Digit Heuristic**: Companies can have month names (APRIL TECH), but real dates always have numbers
2. **Word Boundary**: Prevents substring false positives (MAYBANK contains MAY)
3. **No Brute Force**: O(12 × words) is efficient for small datasets
4. **No Cover-Ups**: Comprehensive testing validates both dates AND false positives

## Implementation Details

**Functions Updated** (3 locations):
- `categorize_entity()` - line 106
- `categorize_entity_with_confidence()` - line 219
- `categorize_entity_llm_only()` - line 383

All use: `if _is_date_entity(entity_name): return 'Other'`

**Performance**: O(n × 12) where n = entity name length, efficient and appropriate