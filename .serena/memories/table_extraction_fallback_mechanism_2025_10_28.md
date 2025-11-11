# Table Extraction Fallback Mechanism (2025-10-28)

## Problem Statement

**User Query Failure**: "What is baba's three months ended june 30, 2025 RMB consolidated adjusted ebita for cloud intelligence group?"

**Root Cause**: EBITA/profitability table (image002.png) extraction failed despite:
- ✅ DoclingProcessor extracted table successfully (11 rows × 5 cols)
- ✅ Structure-based detection (Entry #97) worked for revenue table
- ❌ Structure-based detection failed for EBITA table → 0 entities extracted

**Why It Failed**: Profitability tables have mixed content:
- Section headers: "By Segment:", empty cells
- Data rows: "Adjusted EBITA", "45,035", "38,844"
- Creates ~40% text, ~60% numbers in value columns
- Fails strict "majority numbers" criterion

## Solution: Two-Pass Column Detection

### Implementation
**File**: `imap_email_ingestion_pipeline/table_entity_extractor.py`
**Method**: `_detect_column_types()` (lines 255-325)

### Algorithm
```python
# Pass 1: Strict detection (majority numbers)
column_stats = {}
for col in columns:
    text_count, number_count = count_content(col)
    column_stats[col] = {'text_count': text_count, 'number_count': number_count}
    
    if text_count > number_count:
        metric_col = col
    elif number_count > 0:
        value_cols.append(col)

# Pass 2: Fallback (≥30% numbers) - only if strict failed
if metric_col is not None and not value_cols:
    for col, stats in column_stats.items():
        if col == metric_col:
            continue
        
        total = stats['text_count'] + stats['number_count']
        if total > 0 and stats['number_count'] / total >= 0.3:
            value_cols.append(col)
```

### Design Decisions

**Why 30% threshold?**
- Too low (10%): Would accept true text columns
- Too high (60%): Would still fail on heavily-sectioned tables
- 30%: Balances mixed-content value columns vs text columns

**Why two-pass?**
- Clean tables (revenue): Strict pass succeeds → fast, accurate
- Mixed tables (EBITA): Fallback pass succeeds → robust
- Non-destructive: Fallback only when strict finds 0 value columns

## Validation Results

**BEFORE Fallback**:
- 50 [TABLE_METRIC: markers (revenue table only)
- 77 financial_metrics
- 0 EBITA metrics

**AFTER Fallback**:
- 87 [TABLE_METRIC: markers (+37, +74%)
- 114 financial_metrics (+37, +48%)
- ✅ Consolidated adjusted EBITA: 45,035 (2024), 38,844 (2025)
- ✅ Cloud Intelligence EBITA: 2,337 (2024), 2,954 (2025)

## Generalizability

**Works for**:
- Clean revenue tables → strict pass
- Mixed profitability tables → fallback pass
- Any company's section-header tables
- No company-specific tuning required

**Code Impact**:
- 30 lines added
- No breaking changes
- Logged fallback activations for debugging

## Files Modified
1. `imap_email_ingestion_pipeline/table_entity_extractor.py` (lines 255-325)

## Related Documentation
- `PROJECT_CHANGELOG.md` Entry #98
- Dependency on Entry #97 (structure-based detection)

## Testing Pattern
```python
from updated_architectures.implementation.data_ingestion import DataIngester
from updated_architectures.implementation.config import ICEConfig

config = ICEConfig()
ingester = DataIngester(config=config)

documents = ingester.fetch_email_documents(
    email_files=["BABA Q1 2026 June Qtr Earnings.eml"],
    limit=1
)

# Check for EBITA metrics in extracted entities
entities = ingester.last_extracted_entities[0]
for metric in entities.get('financial_metrics', []):
    if 'ebita' in metric.get('metric', '').lower():
        print(f"✅ {metric.get('metric')} = {metric.get('value')}")
```

## Key Learnings
1. Financial tables often have section headers/subtotals/empty rows
2. Statistical thresholds (30%) generalize better than semantic patterns
3. Two-pass detection balances speed (strict) and robustness (fallback)
4. Minimal code changes (30 lines) can yield significant impact (+74% extraction)