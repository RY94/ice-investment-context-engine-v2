# Docling Integration Architecture

**Location**: `md_files/DOCLING_INTEGRATION_ARCHITECTURE.md`
**Purpose**: Technical architecture and design decisions for docling integration
**Audience**: Developers understanding implementation patterns
**Related Files**: `config.py`, `sec_filing_processor.py`, `docling_processor.py`

---

## 🏗️ Architecture Overview

### Design Pattern: Three Integration Patterns

Docling integration uses **three distinct patterns** based on the nature of the integration:

| Pattern | Use Case | Files | Coexistence |
|---------|----------|-------|-------------|
| **EXTENSION** | Add new capability | SEC filings, News PDFs | Original + Enhanced |
| **REPLACEMENT** | Swap implementation | Email attachments | Both exist, toggle selects |
| **NEW FEATURE** | Brand new functionality | User uploads, Archives | Only new code |

---

## 🔧 Pattern 1: EXTENSION (SEC Filings)

### Current State
- **Existing**: `sec_edgar_connector.py` fetches filing metadata (form type, date, accession)
- **Gap**: No actual filing content or financial tables
- **Result**: Metadata-only documents in LightRAG

### Enhanced State
- **Original**: Metadata fetch still runs (unchanged)
- **Addition**: Content extraction added conditionally
- **Result**: Full content with financial tables OR metadata-only (toggle-dependent)

### Code Flow

```python
# data_ingestion.py: fetch_sec_filings()

# 1. Metadata fetch (ALWAYS runs, unchanged)
filings = sec_connector.get_recent_filings(symbol)

# 2. Content extraction (NEW, conditional)
if config.use_docling_sec:
    for filing in filings:
        # Extract full content with docling
        result = sec_processor.extract_filing_content(filing)
        documents.append(result['enhanced_document'])  # Rich content
else:
    for filing in filings:
        documents.append(create_metadata_document(filing))  # Original behavior
```

### Key Decision: No Base Class

**Why**: Shared code minimal (~10 lines: converter.convert() call)

**Alternative Considered**: Create `DoclingBaseProcessor` with shared conversion logic

**Rejected Because**:
- Base class adds 80 lines of infrastructure for 10 lines of reuse
- SECFilingProcessor has unique: Download logic, XBRL routing, CIK lookup
- DoclingProcessor has unique: Email part handling, storage paths
- Each processor ~150-280 lines standalone vs ~230-360 with base class
- KISS principle: Simple standalone processors easier to understand

---

## 🔄 Pattern 2: REPLACEMENT (Email Attachments)

### Current State
- **Existing**: `AttachmentProcessor` (PyPDF2/openpyxl, 42% table accuracy)
- **Location**: `imap_email_ingestion_pipeline/attachment_processor.py` (547 lines)

### Enhanced State
- **New**: `DoclingProcessor` (docling, 97.9% table accuracy)
- **Location**: `src/ice_docling/docling_processor.py` (150 lines)
- **Coexistence**: BOTH files exist, toggle controls which is instantiated

### API Compatibility

**Critical Requirement**: Exact same signature and return structure

```python
# Both processors must have:
def __init__(self, storage_path: str): ...

def process_attachment(
    self,
    attachment_data: Dict[str, Any],
    email_uid: str
) -> Dict[str, Any]:
    return {
        'filename': str,
        'file_hash': str,
        'mime_type': str,
        'file_size': int,
        'storage_path': str,
        'processing_status': str,
        'extraction_method': str,  # Identifies which processor
        'extracted_text': str,
        'extracted_data': dict,
        'page_count': int,
        'error': str | None
    }
```

### Storage Path Compatibility

**Critical Requirement**: Exact same directory structure

```python
# Both must create identical paths:
storage_path / email_uid / file_hash / original / filename
storage_path / email_uid / file_hash / extracted.txt
```

**Why**: Enables seamless switching - processed files accessible regardless of processor used

### Code Flow

```python
# data_ingestion.py: __init__()

if config.use_docling_email:
    self.attachment_processor = DoclingProcessor(storage_path)  # New
else:
    self.attachment_processor = AttachmentProcessor(storage_path)  # Original

# Rest of code unchanged - uses self.attachment_processor.process_attachment()
```

---

## ➕ Pattern 3: NEW FEATURE (User Uploads, Archives)

### Characteristics
- No existing implementation to replace or extend
- Clean slate implementation
- No backward compatibility concerns

### Implementation (Future)
- Create new processor classes
- Add new methods to DataIngester
- Follow EntityExtractor/GraphBuilder integration pattern

**Status**: Documented in `DOCLING_FUTURE_INTEGRATIONS.md`, not yet implemented

---

## 🔗 EntityExtractor/GraphBuilder Integration

### Critical Design Decision

**Both SEC and Email processors integrate with EntityExtractor + GraphBuilder**

**Why**:
1. **Consistency**: Same pipeline for all documents
2. **Inline Markup**: Enhanced documents with [TICKER:NVDA|confidence:0.95]
3. **Graph Relationships**: Typed edges (COMPANY_FILES, ANALYST_RECOMMENDS, etc.)
4. **Phase 2.6.2 Ready**: Stores graph_data in last_graph_data for Signal Store

### Email Pipeline (Existing Pattern)

```
Email → AttachmentProcessor → EntityExtractor → GraphBuilder → create_enhanced_document() → LightRAG
```

### SEC Pipeline (Same Pattern)

```
SEC Filing → SECFilingProcessor → EntityExtractor → GraphBuilder → create_enhanced_document() → LightRAG
```

### Dependency Injection

```python
# SEC processor initialized with existing components
self._sec_processor = SECFilingProcessor(
    entity_extractor=self.entity_extractor,  # Reuse existing!
    graph_builder=self.graph_builder,        # Reuse existing!
    robust_client=RobustHTTPClient(),
    sec_connector=self.sec_connector          # Reuse existing!
)
```

**Benefit**: ~1,350 lines of existing code reused (EntityExtractor 668 + GraphBuilder 680)

---

## 🧠 Smart Routing: XBRL vs Docling

### SEC Filing Formats

| Format | Prevalence | Current Handling | Future Enhancement |
|--------|------------|------------------|-------------------|
| **XBRL** | ~70% of 10-K/10-Q | Docling extraction (MVP) | Parse structured data (100% accuracy) |
| **HTML** | ~25% | Docling extraction | Continue docling |
| **PDF** | ~5% | Docling extraction | Continue docling |

### Routing Logic (MVP)

```python
if is_xbrl or is_inline_xbrl:
    # MVP: Use docling (XBRL parsing = future enhancement)
    logger.info("XBRL filing detected (will use docling for MVP)")
    result = _extract_with_docling(...)
else:
    # HTML/PDF
    result = _extract_with_docling(...)
```

### Future Enhancement: XBRL Parser

```python
if is_xbrl:
    # Parse XBRL structured data (100% accuracy, faster)
    result = _parse_xbrl_filing(...)  # To be implemented
else:
    # Docling for HTML/PDF (97.9% accuracy)
    result = _extract_with_docling(...)
```

**Benefit**: Higher accuracy (100% vs 97.9%), faster processing for XBRL filings

---

## 🛡️ Production Patterns

### 1. RobustHTTPClient Integration

**Decision**: Use production `RobustHTTPClient` instead of plain `requests`

```python
# SEC processor
self.http_client = RobustHTTPClient('sec_edgar')
response = self.http_client.request('GET', url, ...)  # Circuit breaker + retry
```

**Benefits**:
- Circuit breaker pattern (fails fast after N errors)
- Exponential backoff retry logic
- Connection pooling
- Metrics tracking

### 2. Caching Strategy

**Decision**: Cache downloaded SEC filings to avoid re-downloads

```python
cache_key = f"{accession_number}_{primary_document}"
cache_path = self.cache_dir / cache_key

if cache_path.exists():
    return cache_path  # Use cached file

# Download and cache
cache_path.write_bytes(response.content)
```

**Benefits**:
- Faster subsequent processing
- Reduced SEC EDGAR load
- Works offline for cached filings

### 3. Error Handling: No Auto-Fallback

**Decision**: User specified "No auto-fallback, raise clear errors"

```python
except Exception as e:
    # DON'T: Silent fallback to PyPDF2
    # DO: Clear error with actionable solutions
    raise RuntimeError(
        f"❌ Docling processing failed for {filename}\n"
        f"Reason: {str(e)}\n"
        f"Solutions:\n"
        f"  1. Run: python scripts/download_docling_models.py\n"
        f"  2. Set: export USE_DOCLING_EMAIL=false\n"
    ) from e
```

**Benefits**:
- Clear failure diagnosis
- Actionable solutions
- No hidden fallback behavior

---

## 📊 Code Metrics

### Implementation Summary

| Component | Lines | Type | Purpose |
|-----------|-------|------|---------|
| **config.py** | +36 | Modified | Feature flags + helper |
| **data_ingestion.py** | +145 | Modified | SEC + Email integration |
| **ice_simplified.py** | +1 | Modified | Pass config |
| **sec_filing_processor.py** | 280 | NEW | SEC content extraction |
| **docling_processor.py** | 150 | NEW | Email attachment processing |
| **download_docling_models.py** | 106 | NEW | Model pre-loader |
| **__init__.py** | 18 | NEW | Package init |
| **Total Code** | **736** | | |

### Code Reuse

| Existing Component | Lines | How Reused |
|-------------------|-------|------------|
| **EntityExtractor** | 668 | Dependency injection to both processors |
| **GraphBuilder** | 680 | Dependency injection to both processors |
| **RobustHTTPClient** | 116 | Dependency injection to SEC processor |
| **SECEdgarConnector** | 203 | Dependency injection (CIK lookup, rate limiting) |
| **create_enhanced_document** | 100+ | Direct import, same format |
| **Total Reused** | **~1,767** | |

**Reuse Ratio**: 1,767 existing / 736 new = 2.4x code reuse

---

## 🎯 Design Principles Applied

### 1. Simple Orchestration + Production Modules

**ICE Principle #5**: "Delegate to production modules, keep orchestrator simple"

- SEC/Docling processors: Simple delegation to docling library
- EntityExtractor/GraphBuilder: Reuse existing production modules
- RobustHTTPClient: Reuse existing robust networking
- Total orchestration: ~150-280 lines per processor (simple)

### 2. Quality Within Resource Constraints

**ICE Principle #1**: "80-90% capability at <20% enterprise cost"

- Accuracy: 97.9% (professional-grade)
- Cost: $0/month (local execution)
- Code budget: 736 lines (within <2,000 line orchestrator principle)

### 3. User-Directed Evolution

**ICE Principle #4**: "Build for ACTUAL problems, not imagined ones"

- Implemented: SEC + Email (critical gaps identified)
- Documented only: User uploads, Archives, News PDFs (future, when needed)

---

## 🔄 Backward Compatibility

### Original Implementations Preserved

- ✅ `AttachmentProcessor` remains at `imap_email_ingestion_pipeline/attachment_processor.py`
- ✅ `sec_edgar_connector.py` metadata fetch unchanged
- ✅ No breaking changes to existing APIs
- ✅ Default toggles: `true` (docling enabled) but graceful fallback if not installed

### Migration Path

**Day 1**: Both implementations available
**Testing**: Users can A/B test PyPDF2 vs Docling
**Decision**: After validation, can disable old implementation via toggle
**Cleanup**: Old code can be archived (not deleted) after extensive production use

---

**Last Updated**: 2025-10-19
**Related**: `DOCLING_INTEGRATION_TESTING.md`, `DOCLING_FUTURE_INTEGRATIONS.md`
**Code Locations**: `src/ice_docling/`, `updated_architectures/implementation/`
