# Unified Storage Architecture - Single Source of Truth

**Date**: 2025-11-05
**Context**: Storage architecture documentation and validation
**Impact**: Confirmed unified storage pattern for all document types

---

## Architecture Overview

**Single Source of Truth**: All documents (email attachments and URL PDFs) stored in `data/attachments/` with unified hierarchical structure.

### Storage Pattern

```
data/attachments/
├── {email_uid}/                    # Email identifier for isolation
│   ├── {file_hash}/                # SHA-256 hash for deduplication
│   │   ├── original/               # Original files
│   │   │   └── {filename}          # PDF, Excel, images, etc.
│   │   ├── extracted.txt           # Extracted text content
│   │   └── metadata.json           # Source tracking & processing info
```

---

## Two Processing Flows

### Flow 1: Email Attachments

**Processor**: `AttachmentProcessor` (`imap_email_ingestion_pipeline/attachment_processor.py`)

**File Locations**:
- Lines 59-64: Initialization with `storage_path: str = "./data/attachments"`
- Lines 192-198: `_create_storage_directory()` creates `{email_uid}/{file_hash}/`
- Lines 105-109: Writes original file to `original/{filename}`
- Lines 133-136: Writes extracted text to `extracted.txt`
- Lines 169-171: Writes `metadata.json` with `source_type: "email_attachment"`

**Supported Types**: Images, PDFs, Excel, Word, PowerPoint

### Flow 2: URL PDFs

**Processor**: `IntelligentLinkProcessor` (`imap_email_ingestion_pipeline/intelligent_link_processor.py`)

**File Locations**:
- Lines 194-205: Initialization with `storage_path: str = "./data/attachments"`
- Lines 1014-1023: Creates `{email_uid}/{file_hash}/original/` and writes PDF
- Lines 1029-1032: Writes extracted text to `extracted.txt`
- Lines 1068-1070: Writes `metadata.json` with `source_type: "url_pdf"`

**Supported Types**: PDF files downloaded from URLs in email bodies

---

## Source Type Distinction

**How to distinguish**: Both flows use identical storage pattern. Distinction via `metadata.json`:

```json
{
  "source_type": "email_attachment",  // or "url_pdf"
  "original_filename": "...",
  "file_hash": "...",
  "email_uid": "...",
  "timestamp": "...",
  ...
}
```

---

## Orchestration

**File**: `updated_architectures/implementation/data_ingestion.py`

**AttachmentProcessor Initialization** (Lines 133-134):
```python
attachment_storage = Path(__file__).parent.parent.parent / 'data' / 'attachments'
self.attachment_processor = AttachmentProcessor(str(attachment_storage))
```

**IntelligentLinkProcessor Initialization** (Lines 201-202):
```python
link_storage_path = Path(__file__).parent.parent.parent / 'data' / 'attachments'
self.link_processor = IntelligentLinkProcessor(storage_path=str(link_storage_path))
```

**✅ BOTH use same path**: Unified storage confirmed.

---

## Text Extraction

**Switchable Architecture**: Can toggle between processors via environment variables

**Docling** (97.9% table accuracy):
```bash
export USE_DOCLING_EMAIL=true   # Email attachments
export USE_DOCLING_URLS=true    # URL PDFs
```

**PyPDF2/pdfplumber** (42% accuracy):
```bash
export USE_DOCLING_EMAIL=false
export USE_DOCLING_URLS=false
```

**Note**: `DoclingProcessor` (`src/ice_docling/docling_processor.py`) only PROCESSES files, does NOT write them. It reads from `data/attachments/` and returns extracted content.

---

## File Operations Summary

**Components That WRITE Files**:
1. `AttachmentProcessor` - Email attachments
2. `IntelligentLinkProcessor` - URL PDFs

**Components That Only READ/PROCESS**:
1. `DoclingProcessor` - Processes documents, returns extracted content
2. `BackfillMetadata` (`scripts/backfill_metadata.py`) - Only adds metadata.json to existing documents

**Components That Only ORCHESTRATE**:
1. `DataIngester` (`updated_architectures/implementation/data_ingestion.py`) - Delegates to processors

---

## Storage Statistics

**Current Size**: ~686 files (212 documents × ~3 files each)

**File Types**:
- Email attachments: Images, PDFs, Excel, Word, PowerPoint
- URL PDFs: Research reports, broker notes, financial documents

**Deduplication**: SHA-256 file hashing prevents duplicate storage

**Isolation**: `email_uid` directory level prevents file collision when same attachment appears in multiple emails

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Unified storage path** | Single source of truth, no fragmentation |
| **Hierarchical structure** | Email isolation + file deduplication |
| **metadata.json distinction** | Same pattern for different source types |
| **Async file I/O** | IntelligentLinkProcessor uses aiofiles for performance |
| **SHA-256 hashing** | Cryptographically secure deduplication |
| **Switchable extraction** | Toggle Docling vs legacy processors via env vars |

---

## Related Documentation

- **Storage Cleanup**: `md_files/STORAGE_ARCHITECTURE_CLEANUP_2025_11_04.md`
- **Metadata Implementation**: `md_files/METADATA_JSON_IMPLEMENTATION_2025_11_04.md`
- **Docling URL Integration**: `md_files/PHASE2_DOCLING_URL_PDF_INTEGRATION_SUCCESS_2025_11_05.md`
- **Project Structure**: `PROJECT_STRUCTURE.md:347-359`
- **README**: `README.md:95-119`

---

## Validation

**Tests Needed**:
1. AttachmentProcessor only writes to `data/attachments/`
2. IntelligentLinkProcessor only writes to `data/attachments/`
3. Both processors use identical storage pattern
4. metadata.json correctly distinguishes source types

**Status**: Documentation complete, validation tests pending.

---

**Last Updated**: 2025-11-05
**Author**: Claude Code
**Session**: Storage architecture documentation
