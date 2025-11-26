# Source Attribution Quick Reference

## Where file_path Lives

### Input Format (Data Ingestion)
```
Email:    "email:Tencent Q2 2025 Earnings.eml"
API:      "newsapi:FICO_52c1a661" | "fmp:NVDA_hash" | "sec_edgar:SYMBOL_accession"
Pattern:  "source_type:unique_identifier"
```

### Storage (Persistent)
```
Level 1: kv_store_doc_status.json
  └─ doc-{hash}.file_path = "email:Subject.eml"

Level 2: kv_store_text_chunks.json
  ├─ chunk-{hash1}.file_path = "email:Subject.eml"
  ├─ chunk-{hash2}.file_path = "email:Subject.eml"
  └─ chunk-{hash3}.file_path = "email:Subject.eml"
```

### Query Retrieval
```
LightRAG.aquery_llm(question)
  └─ Returns chunks:
     {
       "content": "[SOURCE_EMAIL:...]...",
       "file_path": "email:Subject.eml",
       "full_doc_id": "doc-{hash}",
       "chunk_order_index": 0
     }
```

---

## Attribution Chain: From Input to Output

```
┌──────────────────────────────────────────────────────────────┐
│                    INGESTION (Input)                          │
│ source = "email", file_path = "Tencent Q2 2025 Earnings.eml" │
└────────────────────┬─────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
   ┌─────────────┐          ┌──────────────┐
   │ ice_simple  │          │ data_ingest  │
   │  _fied.py   │──────→   │ ion.py       │
   │ add_doc()   │          │ (embeds [S..])
   └─────┬───────┘          └──────────────┘
         │
         ↓ (file_path passed through)
   ┌──────────────────────┐
   │ ICESystemManager     │
   │ add_document()       │ (transparent pass-through)
   └──────┬───────────────┘
          │
          ↓ (file_path parameter)
   ┌──────────────────────┐
   │ JupyterICERAG        │
   │ add_document()       │
   │ → ainsert(...,       │
   │   file_paths=file_p) │
   └──────┬───────────────┘
          │
          ↓ PERSISTENCE
   ┌────────────────────────────────────┐
   │ LightRAG Storage                   │
   │ ├─ kv_store_doc_status.json        │
   │ │  {file_path: "email:..."}        │
   │ └─ kv_store_text_chunks.json       │
   │    {file_path: "email:..." x5}     │
   └────────────┬───────────────────────┘
                │
      (Time passes, query arrives)
                │
                ↓ RETRIEVAL
   ┌────────────────────────────────────┐
   │ Query: "Question about Tencent?"   │
   │ LightRAG.aquery_llm()              │
   │ Returns: chunks WITH file_path     │
   └────────────┬───────────────────────┘
                │
    ┌───────────┴────────────┐
    ↓                        ↓
┌──────────────────┐   ┌────────────────────┐
│ TIER 1: Extract  │   │ TIER 3: Fallback   │
│ from SOURCE      │   │ from file_path     │
│ markers in       │   │ (if no markers)    │
│ content          │   │                    │
│                  │   │ "email:..." →      │
│ [SOURCE_EMAIL:   │   │ source_type="email"│
│  ...] → "email"  │   │ confidence=0.90    │
│ confidence=0.90  │   │                    │
└──────────┬───────┘   └────────────┬───────┘
           │                        │
           └────────────┬───────────┘
                        ↓
            ┌──────────────────────┐
            │ Query Response:      │
            │ {                    │
            │   "answer": "...",   │
            │   "sources": [       │
            │     {                │
            │       "source":      │
            │         "email",     │
            │       "confidence":  │
            │         0.90         │
            │     }                │
            │   ],                 │
            │   "references": [    │
            │     "email:Tencent..." │
            │   ]                  │
            │ }                    │
            └──────────────────────┘
```

---

## Attribution Confidence Scores

| Source Type | Tier | Confidence | How |
|-------------|------|-----------|-----|
| Email | 1 | 0.90 | `[SOURCE_EMAIL:...]` in content OR file_path ends with .eml |
| API with date | 1 | 0.85 | `[SOURCE:FMP\|SYMBOL:NVDA\|DATE:...]` in content |
| API legacy | 1 | 0.85 | `[SOURCE:FMP\|SYMBOL:NVDA]` in content |
| Entity extraction | 2 | Variable (0.30-0.95) | `[TICKER:NVDA\|confidence:X]` in content |
| File_path fallback (email) | 3 | 0.90 | File_path = "email:filename" |
| File_path fallback (API) | 3 | 0.85 | File_path = "newsapi:id" or "fmp:id" |
| File_path fallback (SEC) | 3 | 0.90 | File_path = "sec_edgar:..." |
| Unknown | 4 | 0.30 | No markers, no valid file_path |

---

## Code Locations

### Phase 1: Input
**File**: `/updated_architectures/implementation/ice_simplified.py`
**Lines**: 260-284
**Key**: Passes `file_path` from data ingestion to system manager

### Phase 2: Orchestration
**File**: `/src/ice_core/ice_system_manager.py`
**Lines**: 321-342
**Key**: Transparent pass-through to LightRAG wrapper

### Phase 3: Storage
**File**: `/src/ice_lightrag/ice_rag_fixed.py`
**Lines**: 236-260 (add_document)
**Key**: Calls `self._rag.ainsert(text, file_paths=file_path)`

### Phase 4: Retrieval
**File**: `/src/ice_lightrag/ice_rag_fixed.py`
**Lines**: 330-410 (query method)
**Key**: Gets chunks with file_path from LightRAG

### Phase 5: Attribution
**File**: `/src/ice_lightrag/ice_rag_fixed.py`
**Lines**: 423-506 (_extract_sources method)
**Key**: Extracts from SOURCE markers (TIER 1-2)

### Phase 6: Fallback
**File**: `/src/ice_lightrag/context_parser.py`
**Lines**: 294-365 (_derive_source_from_file_path)
**Key**: Derives attribution from file_path format (TIER 3)

---

## Storage Files

### kv_store_doc_status.json
```json
{
  "doc-ad20e1662356b48fe1a4dd7ce16e25f2": {
    "status": "processed",
    "chunks_count": 5,
    "file_path": "email:Tencent Q2 2025 Earnings.eml",  // ← HERE
    "created_at": "2025-11-12T01:56:17.805942+00:00",
    "updated_at": "2025-11-12T01:57:24.777753+00:00",
    "track_id": "insert_20251112_095617_254f4727"
  }
}
```

### kv_store_text_chunks.json
```json
{
  "chunk-5dc7429aa22f71187d7bb2db12f09643": {
    "content": "[EMAIL_HISTORICAL] [SOURCE_EMAIL:...]\n\n[TICKER:...]...",
    "file_path": "email:Tencent Q2 2025 Earnings.eml",  // ← AND HERE
    "full_doc_id": "doc-ad20e1662356b48fe1a4dd7ce16e25f2",
    "chunk_order_index": 0,
    "tokens": 1200,
    "create_time": 1762912577,
    "update_time": 1762912625,
    "_id": "chunk-5dc7429aa22f71187d7bb2db12f09643"
  }
}
```

---

## Test Cases

### Test 1: Document with SOURCE markers
- Input: Email with embedded `[SOURCE_EMAIL:...]` markers
- Expected: TIER 1 extraction, confidence=0.90
- Actual: ✅ Working (confirmed in query response)

### Test 2: Document without markers but with file_path
- Input: Document stored with file_path="email:..."
- Expected: TIER 3 fallback, confidence=0.90
- Actual: ⚠️ PARTIALLY WORKING - context_parser has logic but not always invoked

### Test 3: Invalid file_path
- Input: file_path="invalid_format"
- Expected: Falls to default_source(), confidence=0.30
- Actual: ✅ Should work (context_parser logic present)

### Test 4: Multiple sources in one query
- Input: Query returns chunks from email + API sources
- Expected: Both sources in response
- Actual: ✅ Working (multiple patterns extracted)

---

## Gaps and Next Steps

### Gap 1: TIER 3 Not Always Applied
**Problem**: `_extract_sources()` doesn't automatically apply file_path fallback
**Solution**: Enhance to always check file_path if no SOURCE markers found

### Gap 2: Chunk-Level Sources Not Reported
**Problem**: Query returns document-level sources, not per-chunk
**Solution**: Add `chunk_sources` array to response with file_path for each chunk

### Gap 3: v1.4.9 References Field Verification
**Problem**: Unclear if `references` field is populated
**Solution**: Run query and inspect `result_dict["data"]["references"]`

---

## Quick Diagnosis Commands

### Check storage for file_path presence
```bash
# Document level
grep -o '"file_path":"[^"]*"' ice_lightrag/storage/kv_store_doc_status.json | head -5

# Chunk level
grep -o '"file_path":"[^"]*"' ice_lightrag/storage/kv_store_text_chunks.json | head -5
```

### Check if SOURCE markers present
```bash
# Count documents with SOURCE markers
grep -c '\[SOURCE' ice_lightrag/storage/kv_store_text_chunks.json

# Count documents without SOURCE markers (need TIER 3)
grep -c -L '\[SOURCE' ice_lightrag/storage/kv_store_text_chunks.json
```

### Trace a query result
```python
# In notebook:
result = rag.query("What did Tencent report?", mode="hybrid")

# Check sources
print(result["sources"])
# Expected: [{"source": "email", "confidence": 0.90, ...}, ...]

# Check references (v1.4.9)
print(result.get("references"))
# Expected: ["email:Tencent Q2 2025 Earnings.eml", ...]
```

---

**Last Updated**: 2025-11-12
