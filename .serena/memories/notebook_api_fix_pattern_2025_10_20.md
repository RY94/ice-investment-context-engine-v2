# Notebook API Fix Pattern - Production API Compliance

**Date**: 2025-10-20  
**Context**: Fixed `pipeline_demo_notebook.ipynb` Cells 32, 34, 35 API mismatch  
**Pattern**: Test notebooks must use production API, not assumed simplified APIs

## Problem Pattern: Notebook-API Mismatch

**Symptom**: `AttributeError: 'DoclingProcessor' object has no attribute 'extract_text_from_attachment'`

**Root Cause**: Notebook written with assumed simplified API never implemented in production processors.

**Wrong Approach** (Brute Force):
- Add wrapper methods to processors for notebook compatibility
- Create adapters between notebook and production code
- Add test-specific code paths in production modules

**Correct Approach** (Architectural Integrity):
- Update notebook to match production API
- Tests validate actual production code path
- Zero test-specific code in production modules

## Production API Contract

**File**: `src/ice_docling/docling_processor.py:75` and `imap_email_ingestion_pipeline/attachment_processor.py:61`

```python
def process_attachment(self, attachment_data: Dict[str, Any], email_uid: str) -> Dict[str, Any]:
    """
    Args:
        attachment_data: Dict with keys:
            - 'part': Email part object (email.message.Message)
            - 'filename': Attachment filename
            - 'content_type': MIME type
        email_uid: Email unique identifier
    
    Returns:
        {
            'filename': str,
            'file_hash': str,
            'mime_type': str,
            'file_size': int,
            'storage_path': str,
            'processing_status': 'completed' | 'failed',
            'extraction_method': 'docling' | 'pypdf2',
            'extracted_text': str,
            'extracted_data': {'tables': [...]},
            'page_count': int,
            'error': str | None
        }
    """
```

## Fix Pattern: 3-Step Surgical Fix

### Step 1: Store Email Part Object

**File**: `pipeline_demo_notebook.ipynb` Cell 32

```python
# Add 'part' to attachment dict
attachments.append({
    'part': part,  # Email part object (needed by processors)
    'filename': filename,
    'content': payload,
    'size': len(payload),
    'content_type': part.get_content_type()
})
```

### Step 2: Call Production API (Docling)

**File**: `pipeline_demo_notebook.ipynb` Cell 34

```python
# Before (BROKEN):
with tempfile.NamedTemporaryFile(...) as tmp:
    tmp.write(att['content'])
    extracted_text = docling_processor.extract_text_from_attachment(tmp.name)  # ❌ Doesn't exist

# After (CORRECT):
attachment_data = {
    'part': att['part'],
    'filename': att['filename'],
    'content_type': att['content_type']
}
email_uid = f"test_{test_case['test_id']}_{att['filename'][:20]}"
result = docling_processor.process_attachment(attachment_data, email_uid)  # ✅ Production API
extracted_text = result.get('extracted_text', '')
success = result.get('processing_status') == 'completed'
```

### Step 3: Call Production API (Original)

**File**: `pipeline_demo_notebook.ipynb` Cell 35

Same structure as Step 2, but uses `AttachmentProcessor()`.

## Verification Checklist

- [ ] Search codebase for assumed method name (confirm doesn't exist)
- [ ] Find actual production method signature
- [ ] Verify both processors share exact same API
- [ ] Update notebook to use production API directly
- [ ] No wrapper functions, no adapters, no test-specific code
- [ ] Document in PROJECT_CHANGELOG.md with honest root cause

## Key Lessons

1. **Tests validate production code paths**: Notebooks should use actual APIs, not simplified versions
2. **API compatibility is intentional**: DoclingProcessor and AttachmentProcessor share identical API for drop-in replacement
3. **Email part objects are canonical**: Processors expect email.message.Message objects, not raw bytes
4. **Minimal code changes**: Surgical fixes beat comprehensive rewrites
5. **Architectural integrity**: When tests don't match production, fix tests (not production)

## Related Files

- `src/ice_docling/docling_processor.py` - Docling processor with production API
- `imap_email_ingestion_pipeline/attachment_processor.py` - Original processor (same API)
- `imap_email_ingestion_pipeline/pipeline_demo_notebook.ipynb` - Comparison testing notebook
- `PROJECT_CHANGELOG.md` Entry #83 - Complete fix documentation

## Future Prevention

When creating test notebooks:
1. Import and inspect production classes first
2. Use `dir(processor)` to see available methods
3. Check production file for actual method signatures
4. Never assume simplified APIs exist without verification
5. Reference production code locations in notebook markdown

## Cross-Reference

- Serena memory `imap_notebook_documentation_cross_referencing_2025_10_18` - Notebook architecture principles
- Serena memory `notebook_testing_validation_patterns_2025_10_20` - Testing strategies
- PROJECT_CHANGELOG.md Entry #83 - Before/after code comparison
