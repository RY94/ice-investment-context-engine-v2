# Code Examples: File_Path Flow Through ICE System

## 1. Data Ingestion: Where file_path Originates

### Email Pipeline Example

**File**: `/updated_architectures/implementation/ice_simplified.py`
**Lines**: 1000-1030

```python
# Email documents return with file_path
email_docs = self.data_ingester.get_email_documents()
# Returns: List[Dict] with format:
# {
#   'content': 'Tencent earnings call notes...',
#   'file_path': 'email:Tencent Q2 2025 Earnings.eml',  # <-- FILE_PATH HERE
#   'type': 'financial'
# }

# Then passed to add_document
for email_doc in email_docs:
    result = self._system_manager.add_document(
        email_doc['content'],
        doc_type='email',
        file_path=email_doc['file_path']  # <-- PASSED HERE
    )
```

### API Pipeline Example

**File**: `/updated_architectures/implementation/data_ingestion.py`
**Lines**: 837-879

```python
def fetch_financial_documents(self, symbols: List[str]):
    # FMP example
    for doc in fmp_docs:
        doc_hash = hashlib.md5(doc['content'].encode()).hexdigest()[:8]
        doc_dict = {
            'content': doc['content'],
            'file_path': f"fmp:{symbol}_{doc_hash}",  # <-- CREATED HERE
            'type': 'financial'
        }
    
    # NewsAPI example
    for doc in newsapi_docs:
        doc_hash = hashlib.md5(doc['content'].encode()).hexdigest()[:8]
        doc_dict = {
            'content': doc['content'],
            'file_path': f"newsapi:{symbol}_{doc_hash}",  # <-- CREATED HERE
            'type': 'news'
        }
    
    # SEC Edgar example
    for doc in sec_docs:
        doc_dict = {
            'content': doc['content'],
            'file_path': f"sec_edgar:{symbol}_{accession_number}_metadata",  # <-- CREATED HERE
            'type': 'regulatory'
        }
```

---

## 2. Orchestration: Passing Through System Manager

**File**: `/src/ice_core/ice_system_manager.py`
**Lines**: 321-342

```python
def add_document(
    self, 
    text: str, 
    doc_type: str = "financial", 
    update_graph: bool = True, 
    file_path: Optional[str] = None  # <-- RECEIVES file_path
) -> Dict[str, Any]:
    """
    Add document to ICE knowledge base with optional graph update

    Args:
        text: Document content
        doc_type: Type of financial document
        file_path: Optional source file path for traceability (e.g., 'email:filename.eml')

    Returns:
        Dict with ingestion results and graph updates
    """
    if not self.is_ready():
        return {
            "status": "error",
            "message": "ICE system not ready for document ingestion"
        }

    try:
        # Add document to LightRAG with file_path for traceability
        result = self.lightrag.add_document(text, doc_type, file_path=file_path)
        # <-- PASSES file_path to LightRAG wrapper

        # Note: Graph updates disabled for now (Week 3+ feature)
        logger.info(f"Document added: type={doc_type}, graph_updated={update_graph}")
        return result
        
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        return {
            "status": "error",
            "message": f"Document processing failed: {str(e)}"
        }
```

---

## 3. LightRAG Wrapper: Adding to Storage

**File**: `/src/ice_lightrag/ice_rag_fixed.py`
**Lines**: 236-263

```python
async def add_document(
    self, 
    text: str, 
    doc_type: str = "financial", 
    file_path: Optional[str] = None  # <-- RECEIVES file_path
) -> Dict[str, Any]:
    """
    Add a single document with proper error handling and source tracking.

    Uses entity extraction temperature (default 0.3) for LLM-based entity/relationship extraction.
    Lower temperature ensures reproducible graphs for backtesting and compliance.

    Args:
        text: Document content
        doc_type: Document type tag (e.g., 'financial', 'email')
        file_path: Optional source file path for traceability 
                   (e.g., 'email:Tencent_Q2_2025_Earnings.eml')

    Returns:
        Dict with status and message
    """
    if not await self._ensure_initialized():
        return {"status": "error", "message": "System not initialized"}

    try:
        # Set temperature for entity extraction (reproducibility-focused)
        self._set_operation_temperature(self._extraction_temperature)

        enhanced_text = f"[{doc_type.upper()}] {text}"
        
        # LightRAG's ainsert stores file_path with document
        await self._rag.ainsert(
            enhanced_text, 
            file_paths=file_path if file_path else None  # <-- PASSES to LightRAG
        )
        
        return {"status": "success", "message": "Document processed"}
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        return {"status": "error", "message": str(e)}
```

---

## 4. Storage: How LightRAG Persists file_path

LightRAG stores file_path in two JSON files:

### Level 1: Document Status (kv_store_doc_status.json)

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
    "content_summary": "[EMAIL_HISTORICAL] [SOURCE_EMAIL:Tencent Q2 2025 Earnings|...]",
    "content_length": 15987,
    "created_at": "2025-11-12T01:56:17.805942+00:00",
    "updated_at": "2025-11-12T01:57:24.777753+00:00",
    "file_path": "email:Tencent Q2 2025 Earnings.eml",  // ← STORED HERE
    "track_id": "insert_20251112_095617_254f4727",
    "metadata": {
      "processing_start_time": 1762912577,
      "processing_end_time": 1762912644
    }
  }
}
```

### Level 2: Text Chunks (kv_store_text_chunks.json)

```json
{
  "chunk-5dc7429aa22f71187d7bb2db12f09643": {
    "tokens": 1200,
    "content": "[EMAIL_HISTORICAL] [SOURCE_EMAIL:Tencent Q2 2025 Earnings|sender:\"Jia Jun (AGT Partners)\" <jiajun@agtpartners.com.sg>|date:Sun, 17 Aug 2025 10:59:59 +0800|subject:Tencent Q2 2025 Earnings]\n\n[TICKER:GPM|confidence:0.60]...",
    "chunk_order_index": 0,
    "full_doc_id": "doc-ad20e1662356b48fe1a4dd7ce16e25f2",
    "file_path": "email:Tencent Q2 2025 Earnings.eml",  // ← STORED HERE WITH CHUNK
    "llm_cache_list": [
      "default:extract:d4f29165dca310c65bd86de0862636c7",
      "default:extract:bffbf5219519846e40c2a8d40944f9f6"
    ],
    "create_time": 1762912577,
    "update_time": 1762912625,
    "_id": "chunk-5dc7429aa22f71187d7bb2db12f09643"
  },
  
  "chunk-1e9eff5f00d12f7d612eff9fe1f065c8": {
    // ... same structure ...
    "file_path": "email:Tencent Q2 2025 Earnings.eml",  // ← REPLICATED
    "full_doc_id": "doc-ad20e1662356b48fe1a4dd7ce16e25f2"
  },
  
  // ... 3 more chunks, all with same file_path ...
}
```

**Key insight**: file_path is stored **with every chunk**, not just document-level. This allows direct chunk → source mapping without extra database lookups.

---

## 5. Query: Retrieving Chunks with file_path

**File**: `/src/ice_lightrag/ice_rag_fixed.py`
**Lines**: 330-410

```python
async def query(self, question: str, mode: str = "hybrid") -> Dict[str, Any]:
    """
    Query with proper timeout and retry handling, extracts source attribution

    v1.4.9 UPDATE: Uses aquery_llm for HONEST tracing - single query returns both answer
    AND the exact context used to generate it.
    """
    if not await self._ensure_initialized():
        return {"status": "error", "message": "System not initialized", "engine": "lightrag"}

    try:
        # Set temperature for query answering (creativity-focused)
        self._set_operation_temperature(self._query_temperature)

        # SINGLE QUERY with structured response (v1.4.9+ aquery_llm)
        # Returns: answer, entities, relationships, chunks, references in ONE call
        # This guarantees honest tracing: displayed context matches LLM's actual context
        result_dict = await asyncio.wait_for(
            self._rag.aquery_llm(question, param=QueryParam(mode=mode)),
            timeout=self.config["timeout"]
        )

        # Validate LightRAG response structure (prevent silent failures)
        if not result_dict or not isinstance(result_dict, dict):
            raise ValueError("Invalid LightRAG response: expected dict")
        if "llm_response" not in result_dict:
            raise ValueError("LightRAG response missing required field: llm_response")
        if "data" not in result_dict:
            raise ValueError("LightRAG response missing required field: data")

        # Extract components from structured response
        llm_response = result_dict.get("llm_response", {})
        answer = llm_response.get("content", "")
        data = result_dict.get("data", {})

        # Extract structured data (already parsed by LightRAG)
        entities = data.get("entities", [])
        relationships = data.get("relationships", [])
        chunks = data.get("chunks", [])  # <-- CHUNKS INCLUDE file_path
        references = data.get("references", [])  # <-- NATIVE v1.4.9 file references

        # Build parsed_context from structured data (backward compatibility)
        parsed_context = {
            "entities": entities,
            "relationships": relationships,
            "chunks": chunks,  # Contains: content, file_path, chunk_order_index
            "summary": f"Retrieved {len(entities)} entities, {len(relationships)} relationships, {len(chunks)} chunks"
        }
        logger.info(f"Parsed context: {parsed_context['summary']}")

        # Build context string from chunks (contains SOURCE markers)
        # chunks is where LightRAG stores the actual retrieved text with markers
        context_lines = []
        for c in chunks:
            content = c.get('content', c.get('text', ''))
            # CHUNK STRUCTURE HERE:
            # {
            #   'content': '[SOURCE_EMAIL:...] actual text...',
            #   'file_path': 'email:Tencent Q2 2025 Earnings.eml',  ← AVAILABLE
            #   'chunk_order_index': 0
            # }
            if content:  # Only add non-empty chunks
                context_lines.append(f"{content}\n\n")
        context = "".join(context_lines)

        # Extract SOURCE markers from chunks content (where they actually live)
        sources = self._extract_sources(context)

        # Calculate confidence from chunks content
        confidence = self._calculate_confidence(context)

        return {
            "status": "success",
            "result": answer,  # Alias for backward compat
            "answer": answer,
            "sources": sources,  # Legacy: Extracted from SOURCE markers
            "confidence": confidence,  # Aggregated confidence
            "context": context,  # Reconstructed for backward compat
            "parsed_context": parsed_context,  # Structured data (HONEST - from same query as answer)
            "references": references,  # NEW (v1.4.9): Native file references
            "engine": "lightrag",
            "mode": mode
        }
```

---

## 6. Source Attribution: TIER 1 (Extract from Markers)

**File**: `/src/ice_lightrag/ice_rag_fixed.py`
**Lines**: 423-506

```python
def _extract_sources(self, context_text: str) -> list:
    """
    Extract source attribution from retrieved context for traceability

    PRIORITY ORDER (higher priority = more specific):
    1. [SOURCE:FMP|SYMBOL:NVDA] - API ingestion markers (HIGHEST PRIORITY)
    2. [SOURCE_EMAIL:subject|...] - Email ingestion markers
    3. [TICKER:NVDA|confidence:0.95] - Entity extraction markers
    4. [KG] / [DC] - LightRAG reference markers (FALLBACK ONLY)

    Args:
        context_text: Retrieved context from LightRAG (contains chunks with SOURCE markers)

    Returns: [{'source': 'fmp', 'confidence': 0.95, 'symbol': 'NVDA'}, ...]
    """
    import re

    sources_dict = {}

    # Pattern 1: API ingestion format [SOURCE:FMP|SYMBOL:NVDA]
    # Captures source type (FMP, NEWSAPI, etc.) and ticker symbol
    api_pattern = r'\[SOURCE:(\w+)\|SYMBOL:([^\]]+)\]'
    api_matches = re.findall(api_pattern, context_text)
    for source_type, symbol in api_matches:
        key = f"{source_type}:{symbol}"
        sources_dict[key] = {
            'source': source_type.lower(),  # 'fmp', 'newsapi', 'sec_edgar'
            'confidence': 0.85,  # Default confidence for API sources
            'symbol': symbol,
            'type': 'api'
        }

    # Pattern 2: Email ingestion format [SOURCE_EMAIL:subject|...]
    email_pattern = r'\[SOURCE_EMAIL:([^\|]+)\|'
    email_matches = re.findall(email_pattern, context_text)
    for subject in email_matches:
        key = f"EMAIL:{subject[:30]}"  # Truncate long subjects
        sources_dict[key] = {
            'source': 'email',
            'confidence': 0.90,  # Email sources often have high confidence
            'symbol': subject[:50],
            'type': 'email'
        }

    # Pattern 3: Entity markers [TICKER:NVDA|confidence:0.95]
    # Extract confidence if available
    ticker_conf_pattern = r'\[TICKER:([^\|]+)\|confidence:([\d.]+)'
    ticker_conf_matches = re.findall(ticker_conf_pattern, context_text)
    for ticker, conf in ticker_conf_matches:
        if ticker and len(ticker) <= 5:
            key = f"ENTITY:{ticker}"
            sources_dict[key] = {
                'source': 'entity_extraction',
                'confidence': float(conf),
                'symbol': ticker,
                'type': 'entity'
            }

    # Pattern 4 (FALLBACK): LightRAG references [KG] / [DC]
    # Only use if NO real SOURCE markers found
    if not sources_dict:
        if '[KG]' in context_text:
            sources_dict['KG:GRAPH'] = {
                'source': 'knowledge_graph',
                'confidence': 0.70,
                'symbol': 'GRAPH',
                'type': 'internal'
            }
        if '[DC]' in context_text:
            sources_dict['DC:DOCS'] = {
                'source': 'document_context',
                'confidence': 0.70,
                'symbol': 'DOCS',
                'type': 'internal'
            }

    sources = list(sources_dict.values())

    if sources:
        logger.info(f"Extracted {len(sources)} unique sources: {[s['source'] for s in sources]}")
    else:
        logger.warning("No SOURCE markers found in context - check data ingestion pipeline")

    return sources
```

---

## 7. Source Attribution: TIER 3 (File_Path Fallback)

**File**: `/src/ice_lightrag/context_parser.py`
**Lines**: 294-365

```python
def _derive_source_from_file_path(self, file_path: str) -> Dict[str, Any]:
    """
    TIER 3 FALLBACK: Derive source_type from file_path when NO SOURCE markers found.

    file_path patterns:
    - "email:Tencent Q2 2025 Earnings.eml" → source_type="email"
    - "newsapi:FICO_52c1a661" → source_type="api" (NEWSAPI data for FICO)
    - "sec_edgar:FICO_0001968582-25-001044_metadata" → source_type="sec"
    - "unknown" or invalid → source_type="unknown"

    Args:
        file_path: File path from LightRAG storage (Tier 1 tracking)

    Returns:
        Dict with source_type, source_details, confidence, date
    """
    if not file_path or file_path == 'unknown':
        return self._default_source()

    # Parse file_path format: "source_type:details"
    if ':' not in file_path:
        return self._default_source()

    parts = file_path.split(':', 1)
    source_type_prefix = parts[0].lower()
    details = parts[1] if len(parts) > 1 else ''

    # Map file_path prefix to source_type
    if source_type_prefix == 'email':
        # Parse filename to extract subject (remove .eml extension)
        subject = details.rsplit('.eml', 1)[0] if details.endswith('.eml') else details

        return {
            "source_type": "email",
            "source_details": {
                "subject": subject,  # Add for display compatibility with Tier 2
                "filename": details,
                "extraction_method": "file_path_fallback"
            },
            "confidence": 0.90,  # High confidence - verified email source (same as Tier 2)
            "date": None
        }
        
    elif source_type_prefix == 'api' or source_type_prefix in ['newsapi', 'fmp', 'benzinga', 'finnhub']:
        # Extract API provider and symbol from details if possible
        # Format: "api:fmp:NVDA" → provider="fmp", symbol="NVDA"
        api_parts = details.split(':', 1)
        provider = api_parts[0] if api_parts else 'unknown'
        symbol = api_parts[1] if len(api_parts) > 1 else None

        return {
            "source_type": "api",
            "source_details": {
                "provider": provider,
                "symbol": symbol,
                "extraction_method": "file_path_fallback"
            },
            "confidence": 0.85,  # High confidence - verified API source (same as Tier 2)
            "date": None
        }
        
    elif source_type_prefix == 'sec':
        return {
            "source_type": "sec",
            "source_details": {
                "filing_type": details,
                "extraction_method": "file_path_fallback"
            },
            "confidence": 0.90,  # High confidence - official SEC filings
            "date": None
        }
    else:
        # Unknown prefix → fallback to default
        return self._default_source()

def _default_source(self) -> Dict[str, Any]:
    """
    Ultimate fallback when no SOURCE markers AND no valid file_path.

    This should rarely be reached now that we have Tier 3 (file_path fallback).
    """
    return {
        "source_type": "unknown",
        "source_details": {
            "extraction_method": "default_fallback"
        },
        "confidence": 0.30,  # Very low confidence for truly unknown sources
        "date": None
    }
```

---

## 8. Complete Query Response Example

```python
# After query("What did Tencent report about revenue?")

response = {
    "status": "success",
    "answer": "Tencent reported Q2 2025 revenue of 184.5 billion yuan, up 15% year-over-year from 161.1 billion yuan in Q2 2024. This beat analyst estimates of 178.94 billion yuan.",
    
    "sources": [
        {
            "source": "email",
            "confidence": 0.90,
            "symbol": "Tencent Q2 2025 Earnings",
            "type": "email"
        },
        {
            "source": "entity_extraction",
            "confidence": 0.95,
            "symbol": "TCEHY",
            "type": "entity"
        }
    ],
    
    "references": [
        "email:Tencent Q2 2025 Earnings.eml",
        "newsapi:TCEHY_abc123def456"
    ],
    
    "context": "[EMAIL_HISTORICAL] [SOURCE_EMAIL:Tencent Q2 2025 Earnings|sender:\"Jia Jun (AGT Partners)\" <jiajun@agtpartners.com.sg>|date:Sun, 17 Aug 2025 10:59:59 +0800|...]\n\nResults\n- Revenue and adjusted net income beat estimates\nRevenue\n184.50 billion yuan, +15% y/y, estimate 178.94 billion\n...",
    
    "parsed_context": {
        "entities": [
            {
                "id": 1,
                "entity": "TENCENT",
                "type": "company",
                "description": "Chinese technology conglomerate"
            },
            {
                "id": 2,
                "entity": "Revenue",
                "type": "metric",
                "description": "184.5 billion yuan in Q2 2025"
            }
        ],
        "relationships": [
            {
                "id": 1,
                "entity1": "TENCENT",
                "entity2": "Revenue",
                "relation": "reported"
            }
        ],
        "chunks": [
            {
                "content": "[SOURCE_EMAIL:Tencent Q2 2025 Earnings|...] Revenue 184.50 billion yuan...",
                "file_path": "email:Tencent Q2 2025 Earnings.eml",  # ← FILE_PATH AVAILABLE
                "chunk_order_index": 0
            },
            {
                "content": "[TICKER:TCEHY|confidence:0.95] Operating profit 60.10 billion...",
                "file_path": "email:Tencent Q2 2025 Earnings.eml",
                "chunk_order_index": 1
            }
        ],
        "summary": "Retrieved 5 entities, 3 relationships, 2 chunks"
    },
    
    "engine": "lightrag",
    "mode": "hybrid"
}
```

---

## Key Takeaways

1. **File_path originates** in data ingestion (email, APIs, etc.)
2. **Flows transparently** through ICESystemManager (no transformation)
3. **Stored persistently** in two places: document + chunk levels
4. **Retrieved with query** results in chunks
5. **Extracted as sources** via TIER 1 markers (primary)
6. **Fallback to TIER 3** by parsing file_path format (if needed)

---

Generated: 2025-11-12
