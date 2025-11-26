# Actual Storage Structures: Real Examples from ICE System

**Date**: 2025-11-12
**Source**: Examined actual kv_store_doc_status.json and kv_store_text_chunks.json files

---

## Document Structure (kv_store_doc_status.json)

### Real Example: Email Document

```json
{
  "doc-ad20e1662356b48fe1a4dd7ce16e25f2": {
    "status": "processed",
    "chunks_count": 5,
    "chunks_list": [
      "chunk-5dc7429aa22f71187d7bb2db12f09643",
      "chunk-1e9eff5f00d12f7d612eff9fe1f065c8",
      "chunk-b3ad86059b093ecd098de28412b81b1d",
      "chunk-ebf5e9c35e46f1e2a1c3eda5db2f727a",
      "chunk-ec26c359747e05f05d700d7a955ee94c"
    ],
    "content_summary": "[EMAIL_HISTORICAL] [SOURCE_EMAIL:Tencent Q2 2025 Earnings|sender:\"Jia Jun (AGT Partners)\" <jiajun@agtpartners.com.sg>|date:Sun, 17 Aug 2025 10:59:59 +0800|subject:Tencent Q2 2025 Earnings]\n\n[TICKER:GPM|confidence:0.60] [TICKER:TME|confidence:0.60] [TICKER:DAU|confidence:0.60]...",
    "content_length": 15987,
    "created_at": "2025-11-12T01:56:17.805942+00:00",
    "updated_at": "2025-11-12T01:57:24.777753+00:00",
    "file_path": "email:Tencent Q2 2025 Earnings.eml",
    "track_id": "insert_20251112_095617_254f4727",
    "metadata": {
      "processing_start_time": 1762912577,
      "processing_end_time": 1762912644
    }
  }
}
```

### Analysis

**Key Fields**:
- `status`: "processed" (document successfully ingested)
- `chunks_list`: Array of 5 chunk IDs (document split into 5 chunks)
- `file_path`: `"email:Tencent Q2 2025 Earnings.eml"` ← **SOURCE ATTRIBUTION**
- `content_summary`: First ~200 chars of content (includes SOURCE markers)
- `created_at`/`updated_at`: Timestamps
- `track_id`: Insert operation ID

**Source Attribution Markers in Summary**:
- `[SOURCE_EMAIL:Tencent Q2 2025 Earnings|...]` - Email marker
- `[TICKER:GPM|confidence:0.60]` - Entity markers with confidence

### Real Example: News API Document

```json
{
  "doc-8d597289951a016c49477ba0c648df34": {
    "status": "processed",
    "chunks_count": 1,
    "chunks_list": [
      "chunk-8d597289951a016c49477ba0c648df34"
    ],
    "content_summary": "[NEWS] [SOURCE:NEWSAPI|SYMBOL:FICO|DATE:2025-11-12T09:57:24.808974]\nNews Article: A Fight Over Credit Scores Turns Into All-Out War\n\nA long-simmering battle over who controls credit scoring in America has erupted into open warfare. Fair Isaac, whose...",
    "content_length": 779,
    "created_at": "2025-11-12T01:57:24.809574+00:00",
    "updated_at": "2025-11-12T01:57:41.076836+00:00",
    "file_path": "newsapi:FICO_52c1a661",
    "track_id": "insert_20251112_095724_1c2f019c",
    "metadata": {
      "processing_start_time": 1762912644,
      "processing_end_time": 1762912661
    }
  }
}
```

### Analysis

**Key Differences from Email**:
- `chunks_count`: 1 (shorter document)
- `file_path`: `"newsapi:FICO_52c1a661"` ← **API SOURCE PATTERN**
- Source marker: `[SOURCE:NEWSAPI|SYMBOL:FICO|DATE:...]` (different format than email)

### Real Example: SEC Filing Document

```json
{
  "doc-20f4113ed19189c5b391328db4571c64": {
    "status": "processed",
    "chunks_count": 1,
    "chunks_list": [
      "chunk-20f4113ed19189c5b391328db4571c64"
    ],
    "content_summary": "[REGULATORY] [SOURCE:SEC_EDGAR|SYMBOL:FICO|DATE:2025-11-12T09:57:24.808974]\nSEC EDGAR Filing: 144 - FICO\n\nFiling Date: 2025-11-10\nAccession Number: 0001968582-25-001044\nFile Number: 001-11689\nAcceptance DateTime: 2025-11-10T16:51:04.000Z\nAct: 33\nDocu...",
    "content_length": 458,
    "created_at": "2025-11-12T01:57:41.105355+00:00",
    "updated_at": "2025-11-12T01:57:57.850379+00:00",
    "file_path": "sec_edgar:FICO_0001968582-25-001044_metadata",
    "track_id": "insert_20251112_095741_a7f8d9c3",
    "metadata": {
      "processing_start_time": 1762912661,
      "processing_end_time": 1762912677
    }
  }
}
```

### Analysis

**Key Fields**:
- `file_path`: `"sec_edgar:FICO_0001968582-25-001044_metadata"` ← **SEC PATTERN**
- Source marker: `[SOURCE:SEC_EDGAR|SYMBOL:FICO|DATE:...]`
- Metadata: Accession number embedded in file_path

---

## Chunk Structure (kv_store_text_chunks.json)

### Real Example: Email Chunk 1 of 5

```json
{
  "chunk-5dc7429aa22f71187d7bb2db12f09643": {
    "tokens": 1200,
    "content": "[EMAIL_HISTORICAL] [SOURCE_EMAIL:Tencent Q2 2025 Earnings|sender:\"Jia Jun (AGT Partners)\" <jiajun@agtpartners.com.sg>|date:Sun, 17 Aug 2025 10:59:59 +0800|subject:Tencent Q2 2025 Earnings]\n\n[TICKER:GPM|confidence:0.60] [TICKER:TME|confidence:0.60] [TICKER:DAU|confidence:0.60] [TICKER:PUBG|confidence:0.60] [TICKER:AI|confidence:0.60] [TICKER:FPS|confidence:0.60] [TICKER:CODM|confidence:0.60] [TICKER:EPIC|confidence:0.60] [TICKER:CTR|confidence:0.60] [TICKER:GPU|confidence:0.60] [TICKER:API|confidence:0.60] [TICKER:WASO|confidence:0.60] [RATING:initiated|ticker:N/A|confidence:0.85] [ANALYST:Peacekeeper Elite|firm:Unknown|confidence:0.80] [ANALYST:Arena Breakout|firm:Unknown|confidence:0.80] [ANALYST:App Store|firm:Unknown|confidence:0.80] [COMPANY:UNKNOWN|ticker:N/A|confidence:0.70] [COMPANY:UNKNOWN|ticker:N/A|confidence:0.70] [COMPANY:UNKNOWN|ticker:N/A|confidence:0.70] [COMPANY:UNKNOWN|ticker:N/A|confidence:0.70] [COMPANY:UNKNOWN|ticker:N/A|confidence:0.70] [SENTIMENT:bullish|score:0.43|confidence:0.80] [TABLE_METRIC:Total Revenue|value:184.5|period:2Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.95] [TABLE_METRIC:Total Revenue|value:161.1|period:2Q2024|ticker:Tencent Q2 2025 Earnings|confidence:0.95] [TABLE_METRIC:Total Revenue|value:+15%|period:YoY|ticker:Tencent Q2 2025 Earnings|confidence:0.95] [TABLE_METRIC:Total Revenue|value:180.0|period:1Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.95] [TABLE_METRIC:Total Revenue|value:+2%|period:QoQ|ticker:Tencent Q2 2025 Earnings|confidence:0.95] [TABLE_METRIC:Value-added Services|value:91.4|period:2Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.75]...",
    "chunk_order_index": 0,
    "full_doc_id": "doc-ad20e1662356b48fe1a4dd7ce16e25f2",
    "file_path": "email:Tencent Q2 2025 Earnings.eml",
    "llm_cache_list": [
      "default:extract:d4f29165dca310c65bd86de0862636c7",
      "default:extract:bffbf5219519846e40c2a8d40944f9f6"
    ],
    "create_time": 1762912577,
    "update_time": 1762912625,
    "_id": "chunk-5dc7429aa22f71187d7bb2db12f09643"
  }
}
```

### Analysis

**Key Fields**:
- `tokens`: 1200 (standard chunk size)
- `content`: Full chunk text WITH all SOURCE markers and extracted attributes
- `chunk_order_index`: 0 (first chunk in document)
- `full_doc_id`: Links back to document
- `file_path`: `"email:Tencent Q2 2025 Earnings.eml"` ← **REPEATED WITH CHUNK**
- `llm_cache_list`: LLM response cache keys (for temperature variation testing)
- `create_time`/`update_time`: Unix timestamps

**Content Structure**:
1. Doc type tag: `[EMAIL_HISTORICAL]`
2. SOURCE marker: `[SOURCE_EMAIL:subject|sender|date|...]`
3. Extracted entities with confidence: `[TICKER:X|confidence:Y]`
4. Extracted ratings, analysts: `[RATING:...]`, `[ANALYST:...]`
5. Sentiment scores: `[SENTIMENT:bullish|score:0.43|confidence:0.80]`
6. Metrics: `[TABLE_METRIC:name|value:...|period:...|confidence:...]`

### Real Example: Email Chunk 2 of 5 (Continuation)

```json
{
  "chunk-1e9eff5f00d12f7d612eff9fe1f065c8": {
    "tokens": 1200,
    "content": ":Domestic Games'|value:-6%|period:QoQ|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:International Games|value:18.8|period:2Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:International Games|value:13.9|period:2Q2024|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:International Games|value:+35%|period:YoY|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:International Games|value:16.6|period:1Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:International Games|value:+13%|period:QoQ|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Marketing Services?|value:35.8|period:2Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Marketing Services?|value:29.9|period:2Q2024|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Marketing Services?|value:+20%|period:YoY|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Marketing Services?|value:31.9|period:1Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Marketing Services?|value:+12%|period:QoQ|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Fin Tech and Business Services|value:55.5|period:2Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Fin Tech and Business Services|value:50.4|period:2Q2024|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Fin Tech and Business Services|value:+10%|period:YoY|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Fin Tech and Business Services|value:54.9|period:1Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Fin Tech and Business Services|value:+ 1%|period:QoQ|ticker:Tencent Q2 2025 Earnings|confidence:0.75] [TABLE_METRIC:Others|value:1.8|period:2Q2025|ticker:Tencent Q2 2025 Earnings|confidence:0.75]...",
    "chunk_order_index": 1,
    "full_doc_id": "doc-ad20e1662356b48fe1a4dd7ce16e25f2",
    "file_path": "email:Tencent Q2 2025 Earnings.eml",
    "llm_cache_list": [
      "default:extract:92d86c5b12ccbd77c9a3f598a7e3e598",
      "default:extract:16b6e7fd1d0c3746c1f573ca99dfcff3"
    ],
    "create_time": 1762912577,
    "update_time": 1762912603,
    "_id": "chunk-1e9eff5f00d12f7d612eff9fe1f065c8"
  }
}
```

### Analysis

**Key Observations**:
- `chunk_order_index`: 1 (second chunk)
- `file_path`: **SAME AS CHUNK 1** - "email:Tencent Q2 2025 Earnings.eml"
- `full_doc_id`: **SAME** - Points to same document
- Content continues from chunk 1 (continuation of metrics)

**Why file_path is Replicated**:
- Enables direct chunk → source lookup
- Chunks can be processed independently
- No need to reference parent document for source
- Efficient for vector DB queries

---

## Data Statistics from Actual Storage

### Document Distribution

From the examined files:
- **Email documents**: 1 (5 chunks)
- **NewsAPI documents**: Multiple (1-2 chunks each)
- **SEC Edgar documents**: Multiple (1 chunk each)
- **Total documents examined**: 3+

### Source Types Found

| Source Type | Count | File_path Pattern | Confidence |
|-------------|-------|------------------|-----------|
| Email | 1 | `email:Subject.eml` | 0.90 |
| NewsAPI | Multiple | `newsapi:TICKER_hash` | 0.85 |
| SEC Edgar | Multiple | `sec_edgar:TICKER_accession_metadata` | 0.90 |

### Extracted Entity Types

Found in chunk content markers:
- `[TICKER:X|confidence:Y]` - Stock tickers
- `[RATING:value|ticker:X|confidence:Y]` - Ratings
- `[ANALYST:name|firm:X|confidence:Y]` - Analyst names
- `[COMPANY:name|ticker:X|confidence:Y]` - Company entities
- `[SENTIMENT:type|score:X|confidence:Y]` - Sentiment analysis
- `[TABLE_METRIC:name|value:X|period:Y|confidence:Z]` - Financial metrics

### Confidence Scores Observed

| Source Type | Range | Typical |
|-------------|-------|---------|
| TABLE_METRIC (financial) | 0.75-0.95 | 0.95 |
| TICKER (stock symbol) | 0.60 | 0.60 |
| RATING | 0.85 | 0.85 |
| ANALYST | 0.80 | 0.80 |
| COMPANY | 0.70 | 0.70 |
| SENTIMENT | 0.80 | 0.80 |

---

## Storage File Metadata

### kv_store_doc_status.json
- **Purpose**: Document-level metadata
- **Structure**: Flat JSON object (key = doc-{hash})
- **Size examined**: Multiple documents
- **Retention**: Permanent (until deleted)
- **Access pattern**: Read-heavy (for status checks)

### kv_store_text_chunks.json
- **Purpose**: Chunk storage with content
- **Structure**: Flat JSON object (key = chunk-{hash})
- **Size examined**: 5+ chunks
- **Retention**: Permanent (until cleaned)
- **Access pattern**: Read-heavy (for queries)

---

## Source Attribution Chains Observed

### Chain 1: Email Document (Complete)

```
ice_simplified.py
  ↓ file_path="email:Tencent Q2 2025 Earnings.eml"
ICESystemManager
  ↓ passes file_path through
JupyterICERAG
  ↓ calls LightRAG.ainsert(text, file_paths="email:...")
kv_store_doc_status.json
  ├─ doc-ad20e1662356b48fe1a4dd7ce16e25f2
  │  ├─ file_path: "email:Tencent Q2 2025 Earnings.eml" ✓
  │  └─ chunks_list: [chunk-1, chunk-2, ...]
  ↓
kv_store_text_chunks.json
  ├─ chunk-5dc7429aa22f71187d7bb2db12f09643
  │  ├─ file_path: "email:Tencent Q2 2025 Earnings.eml" ✓
  │  ├─ full_doc_id: "doc-ad20e1662356b48fe1a4dd7ce16e25f2" ✓
  │  └─ content: "[SOURCE_EMAIL:...Tencent Q2 2025 Earnings...]" ✓
  ├─ chunk-1e9eff5f00d12f7d612eff9fe1f065c8
  │  ├─ file_path: "email:Tencent Q2 2025 Earnings.eml" ✓
  │  └─ content: "[TABLE_METRIC:...]..." ✓
  └─ ... 3 more chunks with same file_path
```

### Chain 2: News API Document (Complete)

```
data_ingestion.py
  ↓ file_path="newsapi:FICO_52c1a661"
ice_simplified.py
  ↓ passes to system manager
ICESystemManager → JupyterICERAG → LightRAG
  ↓
kv_store_doc_status.json
  └─ doc-8d597289951a016c49477ba0c648df34
     ├─ file_path: "newsapi:FICO_52c1a661" ✓
     └─ chunks_list: [chunk-8d597289951a016c49477ba0c648df34]
      ↓
kv_store_text_chunks.json
  └─ chunk-8d597289951a016c49477ba0c648df34
     ├─ file_path: "newsapi:FICO_52c1a661" ✓
     ├─ full_doc_id: "doc-8d597289951a016c49477ba0c648df34" ✓
     └─ content: "[SOURCE:NEWSAPI|SYMBOL:FICO|DATE:...]..."✓
```

---

## Query-Time Structure

When LightRAG returns query results:

```python
result_dict = {
    "llm_response": {
        "content": "Tencent reported Q2 2025 revenue of..."
    },
    "data": {
        "entities": [...],
        "relationships": [...],
        "chunks": [
            {
                "content": "[SOURCE_EMAIL:Tencent Q2 2025 Earnings|...] Revenue 184.5...",
                "file_path": "email:Tencent Q2 2025 Earnings.eml",  # ← AVAILABLE
                "chunk_order_index": 0,
                "_id": "chunk-5dc7429aa22f71187d7bb2db12f09643"
            },
            {
                "content": "[TABLE_METRIC:Total Revenue|...]...",
                "file_path": "email:Tencent Q2 2025 Earnings.eml",  # ← AVAILABLE
                "chunk_order_index": 1,
                "_id": "chunk-1e9eff5f00d12f7d612eff9fe1f065c8"
            }
        ],
        "references": [  # v1.4.9 feature
            "email:Tencent Q2 2025 Earnings.eml",
            "newsapi:FICO_52c1a661"
        ]
    }
}
```

---

## Key Observations

1. **file_path is consistently present** at all levels
2. **SOURCE markers are embedded** in chunk content
3. **Chunks link to documents** via full_doc_id
4. **Confidence scores are detailed** (per entity type)
5. **Multiple extraction methods** provide redundancy
6. **Storage is denormalized** (file_path replicated with chunks)

---

**Data verified on**: 2025-11-12
**Status**: All observations confirmed with actual data
