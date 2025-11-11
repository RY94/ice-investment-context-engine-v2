# Storage Path Investigation - Complete Manual Access Guide

**Date**: 2025-11-06  
**Session Type**: Storage Architecture Investigation + User Access Documentation  
**Status**: ✅ COMPLETE - Full storage documentation created

---

## User Request

"analyse @ice_building_workflow.ipynb codes and its notebook thoroughly, then troubleshoot if the extracted/fetched documents from the emails get stored and to where? What is the path? i want to be able to manually access the files from the folder."

**Goal**: Provide complete manual access guide for email attachments and URL-fetched documents.

---

## Storage Location (DEFINITIVE ANSWER)

### Primary Storage Directory

**Absolute Path**:
```
/Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/data/attachments
```

**Relative Path** (from project root):
```
data/attachments/
```

### Directory Structure

```
data/attachments/
├── {email_uid}/              # Email identifier (filename without .eml)
│   └── {file_hash}/         # SHA-256 hash (64 chars) - deduplication
│       ├── original/        # Original files (PDF, Excel, Word, images)
│       │   └── {filename}
│       ├── extracted.txt    # Extracted text content
│       └── metadata.json    # Processing metadata
```

---

## How Email UID is Generated

**Code Reference**: `updated_architectures/implementation/data_ingestion.py:1205, 1242`

```python
email_uid = eml_file.stem  # Filename without extension
```

**Examples**:
| Email File | Email UID | Storage Folder |
|------------|-----------|----------------|
| `Tencent Q2 2025 Earnings.eml` | `Tencent Q2 2025 Earnings` | `data/attachments/Tencent Q2 2025 Earnings/` |
| `BABA Q1 2026 June Qtr Earnings.eml` | `BABA Q1 2026 June Qtr Earnings` | `data/attachments/BABA Q1 2026 June Qtr Earnings/` |

---

## Storage Path Configuration

### Code Location

**File**: `updated_architectments/implementation/data_ingestion.py`

**AttachmentProcessor initialization** (lines 126-154):
```python
# Docling initialization for email attachments
storage_path = Path(__file__).parent.parent.parent / 'data' / 'attachments'
```

**IntelligentLinkProcessor initialization** (lines 196-219):
```python
# Use same storage path as AttachmentProcessor for consistency
link_storage_path = Path(__file__).parent.parent.parent / 'data' / 'attachments'
link_storage_path.mkdir(parents=True, exist_ok=True)
```

**Why**: Unified storage architecture for both email attachments and URL-fetched PDFs

---

## Notebook Integration

### ice_building_workflow.ipynb

**Cell 2**: Configuration
```python
os.environ['USE_DOCLING_EMAIL'] = 'true'   # Email attachments via Docling
os.environ['USE_DOCLING_URLS'] = 'true'    # URL PDFs via Docling
os.environ['USE_CRAWL4AI_LINKS'] = 'true'  # Web scraping via Crawl4AI
```

**Cell 15**: Email processing - processes .eml files and stores attachments/URLs

**Cell 17**: Storage verification diagnostic
- Logs show: "✅ Unified storage path confirmed: .../data/attachments"
- Counts PDFs, metadata.json files
- Shows email folders created

**Cell 19**: PDF storage verification
- Lists all PDFs in unified storage
- Shows recent downloads (last 10 minutes)

---

## Manual Access Methods

### Method 1: Finder (macOS) - EASIEST

1. Press `Cmd + Shift + G` (Go to Folder)
2. Paste: `/Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/data/attachments`
3. Browse folders by email name
4. Open files directly

### Method 2: Terminal Commands

**List all processed emails**:
```bash
ls -1 "data/attachments/"
```

**Find all PDFs**:
```bash
find "data/attachments" -name "*.pdf"
```

**Find PDFs from specific email**:
```bash
find "data/attachments/Tencent Q2 2025 Earnings" -name "*.pdf"
```

**Count total documents**:
```bash
find "data/attachments" -type f \( -name "*.pdf" -o -name "*.xlsx" -o -name "*.docx" \) | wc -l
```

**Open PDF in Preview**:
```bash
open "data/attachments/{email_uid}/{hash}/original/{filename.pdf}"
```

### Method 3: Python Script

```python
from pathlib import Path

storage = Path("data/attachments")

# List all emails processed
for email_dir in storage.iterdir():
    if email_dir.is_dir():
        print(f"\nEmail: {email_dir.name}")
        
        # Find PDFs in this email
        pdfs = list(email_dir.glob("*/original/*.pdf"))
        for pdf in pdfs:
            print(f"  → {pdf.name} ({pdf.stat().st_size / 1024:.1f} KB)")
```

---

## metadata.json Format

**Every file has tracking metadata**:

```json
{
  "source_type": "email_attachment" | "url_pdf",
  "source_context": {
    "email_uid": "Tencent Q2 2025 Earnings",
    "email_subject": "Q2 2025 Financial Results",
    "email_date": "2025-08-15T10:30:00"
  },
  "file_info": {
    "original_filename": "tencent_q2_2025_earnings.pdf",
    "file_hash": "f795167dac6c947e...",
    "file_size": 2458624,
    "mime_type": "application/pdf"
  },
  "processing": {
    "timestamp": "2025-11-06T10:30:15",
    "extraction_method": "docling" | "pypdf2" | "ocr_tesseract",
    "status": "completed" | "failed" | "skipped",
    "page_count": 45,
    "text_chars": 125678,
    "tables_extracted": 12,
    "ocr_confidence": 0.98
  },
  "storage": {
    "original_path": "original/tencent_q2_2025_earnings.pdf",
    "extracted_text_path": "extracted.txt",
    "created_at": "2025-11-06T10:30:15"
  }
}
```

---

## File Types Stored

### Email Attachments (AttachmentProcessor)
- **PDF**: Research reports, earnings presentations
- **Excel** (.xlsx, .xls): Financial tables, data sheets
- **Word** (.docx, .doc): Analysis reports
- **PowerPoint** (.pptx, .ppt): Presentations
- **Images** (.png, .jpg): Charts, screenshots, tables (OCR applied)

### URL-Fetched Documents (IntelligentLinkProcessor)
- **Tier 1**: Direct download PDFs
- **Tier 2**: Token-authenticated PDFs (e.g., DBS Research)
- **Tier 3**: Simple crawl content (Reuters, Bloomberg)
- **Tier 4**: Portal-authenticated content
- **Tier 5**: News paywall content

---

## Current State (2025-11-06)

**Storage Directory Status**:
```bash
data/attachments/
├── test_cache_001/      # Test files (from validation)
└── test_email_001/      # Test files (from validation)
```

**Real Email Processing**: Not yet run
- Sample emails exist in `data/emails_samples/` (71 files)
- Ready for processing via Cell 15 in ice_building_workflow.ipynb

**To Process Real Emails**:
1. Open `ice_building_workflow.ipynb`
2. Run Cell 2 (configuration)
3. Run Cell 3 (ICE initialization)
4. Run Cell 15 (email processing)
5. Check `data/attachments/` for new folders

---

## Troubleshooting Guide

### Issue 1: "No files in data/attachments/ after running Cell 15"

**Diagnostic**:
```python
# Run in notebook
if hasattr(ice, 'ingester'):
    processor = ice.ingester.attachment_processor
    if processor is None:
        print("❌ AttachmentProcessor not initialized")
    else:
        print(f"✅ Using: {type(processor).__name__}")
```

**Solutions**:
1. Check Cell 3 logs for "✅ AttachmentProcessor initialized"
2. Verify USE_DOCLING_EMAIL environment variable
3. Check for initialization errors in Cell 3 output

### Issue 2: "Cannot find email's files"

**Remember**: Email UID = filename WITHOUT .eml extension

**Check**:
```bash
ls -1 "data/attachments/" | grep -i "tencent"
```

**Common mistake**:
- Looking for: `data/attachments/Tencent Q2 2025 Earnings.eml/` ❌
- Correct path: `data/attachments/Tencent Q2 2025 Earnings/` ✅

### Issue 3: "Files exist but extracted.txt is empty"

**Check metadata**:
```bash
cat "data/attachments/{email_uid}/{hash}/metadata.json" | grep status
```

**If status = "failed"**: Check Cell 15 logs for error messages

### Issue 4: "Hash directory name is too long to navigate"

**Use Tab completion**:
```bash
cd data/attachments/Tencent\ Q2\ 2025\ Earnings/
ls -1  # Shows hash directory
cd f795<TAB>  # Auto-completes full hash
```

**Or use wildcards**:
```bash
find "data/attachments/Tencent Q2 2025 Earnings" -name "*.pdf"
```

---

## Documentation Created

**File**: `tmp/tmp_storage_access_guide.md` (450 lines)

**Contents**:
1. Storage location (absolute and relative paths)
2. Directory structure explanation
3. Email UID generation logic
4. File hash generation (SHA-256)
5. Manual access methods (Finder, Terminal, VS Code)
6. metadata.json format and examples
7. Troubleshooting guide (4 common issues)
8. Quick reference commands
9. Step-by-step example (finding Tencent files)
10. Storage statistics Python code
11. Configuration reference

---

## Key Technical Details

### Storage Path Resolution

**Code**: `data_ingestion.py:201`
```python
link_storage_path = Path(__file__).parent.parent.parent / 'data' / 'attachments'
```

**Why `parent.parent.parent`**:
- `__file__`: `/...Project/updated_architectures/implementation/data_ingestion.py`
- `.parent`: `/...Project/updated_architectures/implementation/`
- `.parent.parent`: `/...Project/updated_architectures/`
- `.parent.parent.parent`: `/...Project/` (project root)
- Final: `/...Project/data/attachments/`

### Email Processing Flow

1. **Load .eml file** → Extract sender, subject, body, attachments
2. **Generate email_uid** → Filename stem (no extension)
3. **Process attachments**:
   - For each attachment → Extract content
   - Generate file_hash → SHA-256 checksum
   - Save to → `data/attachments/{email_uid}/{file_hash}/original/{filename}`
   - Extract text → `extracted.txt`
   - Save metadata → `metadata.json`
4. **Process URLs** (if IntelligentLinkProcessor enabled):
   - Extract URLs from email body
   - Classify tier (1-6)
   - Fetch content (Simple HTTP or Crawl4AI)
   - Save to same structure → `data/attachments/{email_uid}/{file_hash}/`

### Deduplication Logic

**SHA-256 Hash**:
- Same file content → Same hash
- Different emails with same attachment → Single storage
- Saves disk space + processing time

**Example**:
- Email A has `report.pdf` (hash: `abc123...`)
- Email B has same `report.pdf` (hash: `abc123...`)
- Storage: `Email_A/abc123.../` (first occurrence)
- Email B references same hash directory ✅

---

## Related Files

- `ice_building_workflow.ipynb` - Email processing notebook
- `updated_architectures/implementation/data_ingestion.py:126-219` - Storage configuration
- `imap_email_ingestion_pipeline/attachment_processor.py` - Email attachment processing
- `imap_email_ingestion_pipeline/intelligent_link_processor.py` - URL fetching
- `tmp/tmp_validation_report.md` - Processor validation results
- `tmp/tmp_storage_access_guide.md` - Complete manual access guide (this documentation)

---

## Quick Reference

**Storage Path**:
```
/Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/data/attachments
```

**Access via Finder**: `Cmd+Shift+G` → Paste path → Enter

**Access via Terminal**: `cd data/attachments && ls -la`

**Find PDFs**: `find data/attachments -name "*.pdf"`

**Read metadata**: `cat data/attachments/{email_uid}/{hash}/metadata.json`

**Open PDF**: `open data/attachments/{email_uid}/{hash}/original/{filename.pdf}`

---

**Memory Type**: Storage Architecture + User Documentation
**Related Memories**: processor_validation_comprehensive_testing_2025_11_06
