# Docling Future Integrations - User Uploads, Archives, News PDFs

**Location**: `md_files/DOCLING_FUTURE_INTEGRATIONS.md`
**Purpose**: Document architecture for integrations 3-5 (implement when actually needed)
**Status**: Architecture documented, NOT yet implemented
**Related Files**: `config.py`, `DOCLING_INTEGRATION_ARCHITECTURE.md`

---

## 🎯 Design Philosophy: Build When Needed

**ICE Principle #4**: "Build for ACTUAL problems, not imagined ones"

These three integration points are architecturally documented but NOT implemented because:
- User hasn't requested these features yet
- Current focus: SEC + Email (covers critical gaps)
- Implementation deferred until user demonstrates need

**When to Implement**: User explicitly requests the feature OR business case emerges

---

## 📚 Integration Point 3: User Document Uploads

### Business Use Case

Portfolio manager wants to upload proprietary research documents:
- Internal investment memos (PDF/Word)
- Third-party research reports (PDF)
- Conference presentations (PowerPoint)
- Custom financial models (Excel)

**Coverage**: User-specific, varies by workflow

### Architecture (To Be Implemented)

**File**: `src/ice_docling/user_upload_processor.py` (NOT YET CREATED)

**API Design**:
```python
class UserUploadProcessor(DoclingProcessor):
    """Process user-uploaded investment documents"""

    def upload_document(self,
                       file_data: bytes,
                       filename: str,
                       metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload and process user document

        Args:
            file_data: Binary file content
            filename: Original filename
            metadata: User-provided metadata (tags, category, etc.)

        Returns:
            Dict with:
                - document_id: Unique identifier
                - enhanced_document: Processed text with inline markup
                - extracted_entities: EntityExtractor output
                - graph_data: GraphBuilder output
        """
        # 1. Validate file (type, size, content)
        # 2. Store original in user_uploads/
        # 3. Convert with docling
        # 4. Run EntityExtractor + GraphBuilder
        # 5. Create enhanced document
        # 6. Ingest into LightRAG
        # 7. Return upload confirmation
```

**Integration Points**:
1. Add to `data_ingestion.py`: `upload_user_document(file_data, metadata)`
2. Storage: `data/user_uploads/{user_id}/{document_id}/`
3. Toggle: `config.use_docling_uploads` (default: false)

**Estimated Complexity**: ~150 lines (similar to DoclingProcessor)

---

## 🗄️ Integration Point 4: Historical Archives

### Business Use Case

One-time bulk migration of historical research library:
- 5 years of broker research PDFs (hundreds of files)
- Historical investment memos and meeting notes
- Archived financial models and presentations

**Coverage**: One-time operation, 100-1000+ documents

### Architecture (To Be Implemented)

**File**: `src/ice_docling/archive_processor.py` (NOT YET CREATED)

**API Design**:
```python
class ArchiveProcessor:
    """Batch process historical document archives"""

    def batch_process_directory(self,
                                archive_path: Path,
                                file_patterns: List[str] = ['*.pdf', '*.xlsx', '*.docx'],
                                batch_size: int = 10) -> BatchResult:
        """
        Batch process entire directory of historical documents

        Args:
            archive_path: Path to directory with historical files
            file_patterns: Glob patterns for file matching
            batch_size: Number of files to process concurrently

        Returns:
            BatchResult with:
                - total_files: Number of files found
                - processed: Number successfully processed
                - failed: Number that failed
                - progress: Real-time progress updates
                - errors: List of error details
        """
        # 1. Scan directory recursively
        # 2. Filter by file patterns
        # 3. Process in batches (avoid memory exhaustion)
        # 4. Track progress (logging + optional callback)
        # 5. Handle errors gracefully (skip file, log error, continue)
        # 6. Batch ingest into LightRAG (every N documents)
        # 7. Return summary statistics
```

**Key Features**:
- Progress tracking: Real-time updates via logging
- Error handling: Skip failed files, continue processing
- Memory management: Process in batches (default: 10 files)
- Resume capability: Track processed files, skip on re-run

**Integration Points**:
1. CLI script: `python scripts/migrate_archives.py --archive-dir /path/to/archives`
2. Toggle: `config.use_docling_archives` (default: false)
3. Storage: `data/archives/{batch_id}/{document_id}/`

**Estimated Complexity**: ~200 lines (includes batch logic, progress tracking)

---

## 📰 Integration Point 5: News PDFs

### Business Use Case

Some news sources publish PDF reports (edge case, <1% of news):
- Regulatory announcements (PDF)
- Third-party research reports distributed as news
- Conference materials shared via news feeds

**Coverage**: <1% of news (most news is text-based via APIs)

### Architecture (To Be Implemented)

**File**: `src/ice_docling/news_pdf_processor.py` (NOT YET CREATED)

**Integration Pattern**: EXTENSION (similar to SEC filings)
- Existing: `fetch_company_news()` returns text articles from NewsAPI/Finnhub
- Enhancement: Check for PDF links, download and extract with docling

**API Design**:
```python
class NewsPDFProcessor:
    """Extract content from news PDFs"""

    def process_news_pdf(self, pdf_url: str, metadata: Dict) -> Dict[str, Any]:
        """
        Download and extract news PDF

        Args:
            pdf_url: URL to news PDF
            metadata: News metadata (source, date, ticker, etc.)

        Returns:
            Dict with enhanced_document, extracted_entities, graph_data
        """
        # 1. Download PDF from URL
        # 2. Extract with docling
        # 3. Run EntityExtractor + GraphBuilder
        # 4. Format as enhanced document
        # 5. Return (for ingestion by fetch_company_news)
```

**Integration Points**:
1. Modify `data_ingestion.py`: `fetch_company_news()` - check for PDF links in API responses
2. If PDF link found: Use NewsPDFProcessor, else use text from API
3. Toggle: `config.use_docling_news` (default: false)

**Estimated Complexity**: ~120 lines (similar to SECFilingProcessor but simpler)

---

## 📊 Summary: Future Integrations

| Integration | Use Case | Coverage | Complexity | Priority |
|-------------|----------|----------|------------|----------|
| **User Uploads** | Upload proprietary research | User-specific | ~150 lines | Medium |
| **Archives** | Bulk migrate historical docs | One-time | ~200 lines | Medium |
| **News PDFs** | Extract news PDFs | <1% of news | ~120 lines | Low |

**Total Estimated Effort**: ~470 lines code + testing/docs

---

## 🎯 Implementation Triggers

### User Uploads - Implement When:
- User explicitly requests "I want to upload my own research"
- User feedback: "Can I add my investment memos to ICE?"
- Business case: User demonstrates need in workflow

### Historical Archives - Implement When:
- User has large archive (100+ files) to migrate
- User requests: "How can I bulk import my old research?"
- One-time migration project identified

### News PDFs - Implement When:
- User identifies news source that publishes PDFs
- Example: "XYZ regulatory news only available as PDFs"
- Current text-based news insufficient

---

## 📋 Implementation Checklist (When Needed)

**For Each Integration**:
1. [ ] Create processor file in `src/ice_docling/`
2. [ ] Follow existing patterns (EntityExtractor + GraphBuilder)
3. [ ] Add integration point in `data_ingestion.py`
4. [ ] Update `config.py` toggle documentation
5. [ ] Write unit tests
6. [ ] Test with EntityExtractor/GraphBuilder
7. [ ] Update `DOCLING_INTEGRATION_TESTING.md`
8. [ ] Update `DOCLING_INTEGRATION_ARCHITECTURE.md`

---

## 🔗 Related Documentation

- **Current Integrations**: `DOCLING_INTEGRATION_ARCHITECTURE.md` - SEC + Email patterns
- **Testing**: `DOCLING_INTEGRATION_TESTING.md` - How to test when implemented
- **Configuration**: `config.py` - Toggle flags (already defined, waiting for implementation)

---

**Last Updated**: 2025-10-19
**Status**: Documented, awaiting implementation trigger
**Principle**: ICE Design Principle #4 - "Build for ACTUAL problems, not imagined ones"
