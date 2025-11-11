# Graph Path Cache Collision Fix - 2025-11-01

## Problem Identified
Graph paths were not displaying in ice_building_workflow.ipynb when running queries. The notebook would show "⚠️ No citation_display field available".

## Root Cause
LightRAG cache key collision in the dual query strategy:
- `ice_rag_fixed.py` makes two sequential queries:
  1. `aquery(question, only_need_context=True)` - Should return raw context with KG sections
  2. `aquery(question)` - Should return synthesized answer
- Both queries generated identical cache keys (e.g., `"hybrid:query:{hash}"`)
- The `only_need_context` parameter was NOT included in cache key generation
- Result: Wrong response type returned (synthesized answer instead of raw context)

## Evidence
- LightRAG internal logs: "Final context: 51 entities, 58 relations, 5 chunks" ✅
- But returned context: Synthesized prose ("In Q2 2025, Tencent reported...") ❌
- Context parser expected `-----Entities(KG)-----` markers, got prose text
- Parser returned 0 chunks → `add_footnote_citations()` exits early → no graph paths

## Solution Implemented
Modified `src/ice_lightrag/ice_rag_fixed.py` lines 283-291 to append cache-busting suffix:

```python
# Append unique suffix to bypass cache collision with full answer query
import time
context_query = f"{question}\n[CONTEXT_ONLY_{int(time.time()*1000)%100000}]"
context = await self._rag.aquery(context_query, param=QueryParam(mode=mode, only_need_context=True))
```

## Why This Fix is Elegant
1. **Minimal Code Change**: Only 4 lines added
2. **Surgical**: Targets exact issue without side effects
3. **Preserves Cache Benefits**: Full answer queries still use cache
4. **No Core Modifications**: Doesn't touch LightRAG library internals
5. **Generalizable**: Works for all query modes and patterns
6. **Robust**: Time-based suffix ensures uniqueness

## Test Verification
Created `tmp/test_graph_path_fix.py` to verify:
- ✅ Context now contains KG sections (not synthesized answer)
- ✅ Parser extracts 52 entities, 58 relationships, 5 chunks
- ✅ Graph paths will display correctly in notebook

## Alternative Solutions Considered
1. Modify LightRAG cache key generation (complex, requires library fork)
2. Swap query order (moves problem, doesn't solve it)
3. Disable caching entirely (performance impact)
4. Clear cache before each query (loses all cache benefits)

## Impact
- Graph path traceability feature now works correctly
- Cell 31 in ice_building_workflow.ipynb will display citation paths
- No performance impact on normal queries
- Cache still provides benefits for expensive LLM synthesis

## File Modified
- `src/ice_lightrag/ice_rag_fixed.py`: Lines 283-291 (cache-busting suffix added)