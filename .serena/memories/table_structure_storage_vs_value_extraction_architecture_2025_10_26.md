# Table Structure Storage vs Value Extraction Architecture
**Date**: 2025-10-26
**Context**: Architectural clarification on how ICE processes financial table images
**Status**: Current implementation uses value extraction; dual-layer planned for table structure storage

## Core Question

"Are we doing table extraction for the financial tables to extract the table structure and cells relationships into the graph such that when a query is asked, we can query for those table structure and relationships from the graph and then lookup the dataframe to get the values?"

## Answer: NO (Current) → YES (Planned)

### Current Implementation: VALUE EXTRACTION

**Data Flow**:
```
Inline Image (PNG) 
→ Docling AI Models (97.9% accuracy)
→ Structured DataFrame (rows × columns)
→ TableEntityExtractor (extract VALUES from each cell)
→ Enhanced Document (inline markup: [TABLE_METRIC:...])
→ LightRAG Storage (text chunks with markup preserved)
→ Query Processing (semantic search → LLM synthesis)
```

**Key Files**:
- `table_entity_extractor.py:139-212` - `_extract_from_table()` processes each value column
- `enhanced_doc_creator.py:252-291` - Embeds table entities as inline markup
- `graph_builder.py:375-427` - `_process_financial_metrics()` creates metric nodes

**Example Data Flow**:
```python
# Step 1: Docling extracts structured DataFrame
DataFrame:
  Metric              | 2Q2025          | 2Q2024          | YoY  | 1Q2025
  Operating profit    | 60.10B yuan     | 51.05B yuan     | +18% | 58.20B
  Op. margin          | 31%             | 29%             | +2pp | 30%

# Step 2: TableEntityExtractor converts to entities (multi-column extraction)
Entities:
  {'metric': 'Operating profit', 'value': '60.10 billion yuan', 'period': '2Q2025', 'ticker': 'TCEHY', 'confidence': 0.95, 'source': 'table'}
  {'metric': 'Operating profit', 'value': '51.05 billion yuan', 'period': '2Q2024', 'ticker': 'TCEHY', 'confidence': 0.95, 'source': 'table'}
  {'metric': 'Op. margin', 'value': '31%', 'period': '2Q2025', 'ticker': 'TCEHY', 'confidence': 0.92, 'source': 'table'}
  {'metric': 'Op. margin', 'value': '29%', 'period': '2Q2024', 'ticker': 'TCEHY', 'confidence': 0.92, 'source': 'table'}
  # ... 55 total entities (11 rows × 5 columns)

# Step 3: EnhancedDocCreator embeds as inline markup
Enhanced Document:
  [TABLE_METRIC:Operating profit|value:60.10 billion yuan|period:2Q2025|ticker:TCEHY|confidence:0.95]
  [TABLE_METRIC:Operating profit|value:51.05 billion yuan|period:2Q2024|ticker:TCEHY|confidence:0.95]
  [MARGIN:Op. margin|value:31%|period:2Q2025|ticker:TCEHY|confidence:0.92]
  [MARGIN:Op. margin|value:29%|period:2Q2024|ticker:TCEHY|confidence:0.92]
  
  Original Email Body Content:
  Tencent Q2 2025 earnings: Operating profit 60.10 billion yuan...

# Step 4: LightRAG stores as text chunks (markup preserved)
# Step 5: Query retrieves text → LLM parses values
```

**Critical Points**:
- ✅ Values extracted and embedded as text (inline markup)
- ✅ Metadata preserved (period, ticker, confidence)
- ✅ Multi-column extraction enables historical queries
- ❌ NO separate table structure storage
- ❌ NO DataFrame retention after ingestion
- ❌ NO direct SQL-like lookups

### Planned Dual-Layer Architecture: WOULD ENABLE TABLE STRUCTURE STORAGE

**Gap**: Only ~350 lines to implement (Phase 2.6.2 - Signal Store)

**Signal Store Schema** (planned):
```python
# SQLite tables for structured queries
metrics_table:
    ticker | metric_type | value | period | confidence | source | timestamp
    TCEHY  | Operating Profit | 60.10B yuan | 2Q2025 | 0.95 | table | 2025-08-17
    TCEHY  | Operating Profit | 51.05B yuan | 2Q2024 | 0.95 | table | 2025-08-17
    TCEHY  | Op. Margin | 31% | 2Q2025 | 0.92 | table | 2025-08-17
    TCEHY  | Op. Margin | 29% | 2Q2024 | 0.92 | table | 2025-08-17
```

**Dual-Layer Query Processing**:
```python
# Current (LightRAG only)
query: "What is Tencent's Q2 2024 operating margin?"
→ Semantic search retrieves text chunks with [MARGIN:...|period:2Q2024|...]
→ LLM parses inline markup → "29%"

# Planned (Dual-Layer)
query: "What is Tencent's Q2 2024 operating margin?"
→ Router detects structured query
→ Signal Store: SELECT value FROM metrics WHERE ticker='TCEHY' AND metric='Operating Margin' AND period='2Q2024'
→ Direct result: "29%" (instant, no LLM needed)

# Complex queries use BOTH layers
query: "How does China regulation impact Tencent's margins?"
→ Signal Store: Get margin time-series
→ LightRAG: Get regulation discussions (semantic)
→ Combine for comprehensive answer
```

**Implementation Breakdown**:
- 200 lines: Signal Store wrapper (SQLite schema + CRUD)
- 100 lines: Query router (structured vs semantic detection)
- 50 lines: Dual-write orchestration (LightRAG + Signal Store)
- **Total**: ~350 lines

**Blocked MVP Modules** (pending Signal Store):
- Portfolio Metrics Module (time-series analysis)
- Risk Alerts Module (threshold-based alerts)
- Performance Dashboard Module (aggregation queries)

## Multi-Column Extraction Implementation

**FIX #1**: `table_entity_extractor.py:139-212` - Multi-column extraction loop

**Why**: Enable queries like:
- "What was Q2 2024 margin?" (needs historical columns)
- "What's the YoY growth?" (needs comparison columns)

**How**: Loop through ALL value columns, not just first column
```python
for value_col in column_map.get('value_cols', []):  # e.g., 2Q2025, 2Q2024, YoY, 1Q2025, QoQ
    single_col_map = {
        'metric_col': column_map['metric_col'],
        'value_cols': [value_col]  # Extract one column at a time
    }
    metric_entity = self._parse_financial_metric(row, single_col_map, ...)
```

**FIX #3**: `enhanced_doc_creator.py:266-280` - Increased markup limits
- `table_metrics_only[:100]` (was 10) - Accommodate 55 entities from 11×5 table
- `table_margin_metrics[:50]` (was 5) - Accommodate multi-column margins

## Inline Markup Format

**Pattern**: `[TYPE:main_value|key1:value1|key2:value2|confidence:0.XX]`

**Table-Specific Markup**:
```
[TABLE_METRIC:Operating profit|value:60.10 billion yuan|period:2Q2025|ticker:TCEHY|confidence:0.95]
[MARGIN:Op. margin|value:31%|period:2Q2025|ticker:TCEHY|confidence:0.92]
```

**Why Inline Markup Works**:
- Survives LightRAG chunking (text-based storage)
- Preserves all metadata (period, ticker, confidence)
- LLM can parse structured format
- Enables semantic + structured retrieval

## Testing Validation

**Test Suite**: `tests/test_imap_email_pipeline_comprehensive.py`
- 21 tests, ALL PASSING
- 5 suites: Email Source, Entity Extraction, Enhanced Documents, Graph Construction, DataIngester Integration
- CRITICAL: ZERO truncation warnings (metadata preservation validated)

**Real-World Test**: Tencent Q2 2025 Earnings.eml
- 2 inline PNG images (151KB, 311KB)
- 11 rows × 5 columns = 55 table entities extracted
- 97.9% accuracy with Docling (vs 42% Tesseract OCR)

## Summary

| Aspect | Current (Value Extraction) | Planned (Dual-Layer) |
|--------|---------------------------|---------------------|
| **Storage** | Text chunks with inline markup | Text (LightRAG) + Structured (Signal Store) |
| **Query** | Semantic search → LLM synthesis | Smart router → SQL direct lookup OR semantic |
| **Structure** | NO table structure preserved | YES table structure in SQLite |
| **DataFrame** | Discarded after extraction | Retained in Signal Store |
| **Complexity** | Simple (current) | +350 lines (minimal overhead) |
| **Use Cases** | Semantic queries | Semantic + Structured + Time-series |

**Recommendation**: Current implementation is CORRECT for LightRAG-only phase. Dual-layer is next logical enhancement for structured queries.

## Files Referenced

- `imap_email_ingestion_pipeline/table_entity_extractor.py` (430 lines)
- `imap_email_ingestion_pipeline/enhanced_doc_creator.py` (lines 252-291)
- `imap_email_ingestion_pipeline/graph_builder.py` (680 lines)
- `src/ice_docling/docling_processor.py` (lines 74-173)
- `tests/test_imap_email_pipeline_comprehensive.py` (21 tests)
- `ICE_DEVELOPMENT_TODO.md` (Phase 2.6.2 Signal Store tasks)

## Related Serena Memories

- `dual_layer_architecture_comprehensive_analysis_2025_10_26` - Complete dual-layer rationale
- `comprehensive_table_extraction_multicolumn_2025_10_26` - Multi-column extraction implementation
- `docling_implementation_audit_2025_10_25` - Docling integration validation
