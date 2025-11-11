# LightRAG Chunk Similarity Score Investigation (2025-11-02)

## Investigation Summary

**Research Question**: Can we expose LightRAG's native chunk relevance/similarity metrics to show "how relevant is this chunk to the query?" with actual metric values?

**Answer**: YES - Similarity scores ARE calculated internally but intentionally EXCLUDED from final output. Multiple modification points available to expose them.

---

## Complete Data Flow Chain

### 1. NanoVectorDB.query() (nano-vectordb/dbs.py)
**Returns**: 
```python
{"__id__": "2", "text": "test2", "__metrics__": 0.994612}
```
- **Field**: `__metrics__` (cosine similarity, 0.0-1.0 range)
- **Status**: ✅ Score calculated and present

### 2. NanoVectorDBStorage.query() (lightrag/kg/nano_vector_db_impl.py:158-166)
**Transforms**:
```python
results = [
    {
        **{k: v for k, v in dp.items() if k != "vector"},
        "id": dp["__id__"],
        "distance": dp["__metrics__"],  # ← RENAMES __metrics__ to distance
        "created_at": dp.get("__created_at__"),
    }
    for dp in results
]
return results
```
- **Field**: `__metrics__` → `distance`
- **Status**: ✅ Score preserved, renamed

### 3. chunks_vdb.query() in Query Pipeline
- Called in `_find_related_text_unit_from_entities()` (operate.py:4252)
- Chunks retrieved with `distance` field intact
- Passed to `_merge_all_chunks()` → `_build_llm_context()`
- **Status**: ✅ Score still present in intermediate data

### 4. _build_llm_context() (lightrag/operate.py:3835-4014)
**Line 3938-3944 - FIRST EXCLUSION**:
```python
for i, chunk in enumerate(truncated_chunks):
    text_units_context.append({
        "reference_id": chunk["reference_id"],
        "content": chunk["content"],
        # ← Only 2 fields extracted for LLM context
    })
```
- **Purpose**: LLM context formatting (doesn't need scores)
- **Status**: ⚠️ First exclusion for LLM prompt, but chunks still passed to convert_to_user_format()

**Line 4002**: Calls `convert_to_user_format(truncated_chunks, ...)`
- `truncated_chunks` still contains `distance` field at this point

### 5. convert_to_user_format() (lightrag/utils.py:2834-2930)
**Lines 2924-2929 - THE CRITICAL EXCLUSION POINT**:
```python
# Convert chunks format (chunks already contain complete data)
formatted_chunks = []
for i, chunk in enumerate(chunks):
    chunk_data = {
        "reference_id": chunk.get("reference_id", ""),
        "content": chunk.get("content", ""),
        "file_path": chunk.get("file_path", "unknown_source"),
        "chunk_id": chunk.get("chunk_id", ""),
        # ← distance field NOT included in output
    }
    formatted_chunks.append(chunk_data)
```
- **Status**: ❌ **FINAL EXCLUSION** - `distance` field deliberately omitted

### 6. Final Output to ICE (src/ice_lightrag/ice_rag_fixed.py:305-322)
```python
chunks = data.get("chunks", [])
# Chunks only contain: ["reference_id", "content", "file_path", "chunk_id"]
# ← NO distance/similarity score
```

---

## Why Scores Are Excluded (Analysis)

Based on code patterns, the exclusion appears **intentional** for these reasons:

1. **Implicit relevance via ordering**: Chunks are pre-sorted by similarity (highest first)
   - User doesn't need explicit scores if order reflects relevance
   - Position in list (rank) serves as implicit metric

2. **Simplicity**: User-facing API kept minimal
   - 4 fields vs 5 fields
   - Reduces cognitive load for API consumers

3. **LLM context design**: The LLM prompt doesn't use similarity scores
   - Scores not needed for generation (only content matters)
   - LLM doesn't get chunk metadata in prompt

4. **Abstraction level**: LightRAG hides retrieval mechanics
   - User only cares about "relevant chunks", not similarity math
   - Keeps internal metrics internal

---

## Feasibility: Three Implementation Options

### Option 1: Modify LightRAG Source (RECOMMENDED)

**File**: `/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/utils.py`
**Line**: 2924-2929
**Change**:
```python
chunk_data = {
    "reference_id": chunk.get("reference_id", ""),
    "content": chunk.get("content", ""),
    "file_path": chunk.get("file_path", "unknown_source"),
    "chunk_id": chunk.get("chunk_id", ""),
    "distance": chunk.get("distance"),  # ← ADD THIS LINE (1-line change)
}
```

**Pros**:
- ✅ **Cleanest**: Source of truth modification
- ✅ **Complete**: Available for ALL downstream consumers (ICE, notebooks, future apps)
- ✅ **Minimal**: One-line code change
- ✅ **Honest**: Exposes actual similarity scores used in retrieval
- ✅ **Aligned with ICE philosophy**: "Fact-Grounded with Source Attribution" (ICE_PRD.md principle #3)

**Cons**:
- ⚠️ Requires LightRAG package modification (not in ICE codebase)
- ⚠️ Need to verify after LightRAG upgrades

---

### Option 2: ICE-Layer Post-Processing (Non-Invasive)

**File**: `src/ice_lightrag/ice_rag_fixed.py`
**Location**: After line 321 (where chunks are received)
**Implementation**:
```python
# After receiving chunks from LightRAG
chunks = data.get("chunks", [])

# Get similarity scores separately
if chunks:
    chunk_ids = [c["chunk_id"] for c in chunks]
    similarity_scores = await self.rag.chunks_vdb.query(query, top_k=len(chunk_ids))
    
    # Match scores to chunks by chunk_id
    for chunk in chunks:
        matching_score = next(
            (s for s in similarity_scores if s["id"] == chunk["chunk_id"]), 
            None
        )
        if matching_score:
            chunk["similarity_score"] = matching_score["distance"]
```

**Pros**:
- ✅ **Non-invasive**: No LightRAG source modification
- ✅ **ICE-controlled**: All code in ICE repository
- ✅ **Upgrade-safe**: Survives LightRAG updates

**Cons**:
- ⚠️ Extra vector query (performance overhead)
- ⚠️ More complex: Requires chunk_id matching logic
- ⚠️ Potential mismatch: If chunk_ids don't align perfectly

---

### Option 3: Notebook Display Enhancement (Quickest Test)

**File**: `ice_building_workflow.ipynb`
**Cell**: 33 (test query display)
**Implementation**:
```python
print(f"\n📄 Context chunks ({len(chunks)} chunks, ordered by relevance):")
for i, chunk in enumerate(chunks[:5]):
    # Show chunk order as implicit relevance indicator
    relevance_percentage = 100 * (len(chunks) - i) / len(chunks)
    print(f"\n   Chunk #{i+1} (relevance rank: {i+1}/{len(chunks)} = {relevance_percentage:.0f}%)")
    print(f"   File: {chunk.get('file_path', 'unknown')}")
    print(f"   Content preview: {chunk['content'][:200]}...")
    print(f"   Note: Chunks are pre-sorted by similarity to query")
```

**Pros**:
- ✅ **Fastest**: Immediate implementation
- ✅ **No code changes**: Display-only modification
- ✅ **User feedback**: Test if users want explicit scores before implementing

**Cons**:
- ⚠️ Not actual similarity scores (only rank-based approximation)
- ⚠️ Limited to notebooks (not available in API/programmatic use)
- ⚠️ Less precise: Order is heuristic, not actual cosine similarity

---

## Recommendation

### Primary: Option 1 (Modify LightRAG Source)

**Rationale**:
1. **Aligns with ICE philosophy**: "100% source traceability, confidence scores on all entities/relationships" (CLAUDE.md:4.4.3)
2. **Minimal cost**: One-line change for complete transparency
3. **Future-proof**: Any tool using ICE's LightRAG instance gets this benefit
4. **Honest metrics**: Exposes actual similarity scores, not derived/approximated values

**Implementation Steps**:
1. Modify `/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/utils.py:2929`
2. Add line: `"distance": chunk.get("distance"),`
3. Test in `ice_building_workflow.ipynb` Cell 33
4. Verify chunks now include `similarity_score` field
5. Update display to show: `print(f"Similarity: {chunk.get('distance', 'N/A')}")`

### Alternative: Start with Option 3 (Test User Value First)

If uncertain about user value, implement Option 3 first:
- Test if users actually want explicit similarity scores
- Gather feedback on display format
- Then commit to Option 1 if valuable

---

## Related Files

### Core Investigation Files
- `/Users/royyeo/anaconda3/lib/python3.11/site-packages/nano_vectordb/dbs.py` - Source of `__metrics__` scores
- `/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/kg/nano_vector_db_impl.py:158-166` - Renames to `distance`
- `/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/operate.py:3835-4014` - `_build_llm_context()`
- `/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/utils.py:2834-2930` - **Critical exclusion point**

### ICE Integration Files
- `src/ice_lightrag/ice_rag_fixed.py:305-322` - Receives final chunks
- `ice_building_workflow.ipynb` Cell 33 - Test query display

---

## Key Technical Insights

1. **Similarity scores exist at every stage until the last function**
   - They are NOT lost accidentally
   - They are deliberately excluded in `convert_to_user_format()`

2. **The `distance` field uses cosine similarity**
   - Range: 0.0-1.0 (higher = more similar)
   - Threshold: 0.2 (configurable in `cosine_better_than_threshold`)

3. **Chunk ordering is reliable**
   - Chunks ARE sorted by similarity (highest first)
   - Position in list directly correlates with relevance
   - E9/1 notation means: Entity source, frequency 9, order/rank #1

4. **ICE's 75% confidence is different**
   - 75% = ICE's entity extraction confidence (from entity_extractor.py)
   - NOT related to chunk similarity scores
   - Calculated as: average(text_quality=0.8, companies=0.8, metrics=0.7)

---

## Next Steps (If Implementing)

1. **If choosing Option 1**:
   - Backup LightRAG source: `cp utils.py utils.py.backup`
   - Make one-line modification
   - Test with existing queries
   - Document modification in ICE_PRD.md "Architecture Modifications" section

2. **If choosing Option 2**:
   - Implement in `ice_rag_fixed.py`
   - Add unit tests for score matching
   - Benchmark performance impact

3. **If choosing Option 3**:
   - Update notebook Cell 33 display
   - Gather user feedback
   - Decide whether to proceed with Option 1

---

**Investigation Date**: 2025-11-02
**Investigation By**: Claude Code (Sonnet 4.5)
**Status**: Complete - All three implementation options validated
**Decision Required**: Choose which option to implement (or none)
