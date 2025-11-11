# ICE Integration Guide - Docling & Crawl4AI

> **Purpose**: Comprehensive guide for Docling and Crawl4AI integrations
> **Audience**: Claude Code AI instances working on document processing or URL fetching
> **When to Load**: When working on document processing, table extraction, or URL handling
> **Parent Doc**: `CLAUDE.md` (core daily workflows)

**Last Updated**: 2025-11-05
**Status**: Production-ready integrations

---

## 📋 Integration Overview

ICE uses two major switchable integrations for professional-grade document processing:

1. **Docling** - IBM's AI-powered document parser (42% → 97.9% table accuracy)
2. **Crawl4AI** - Smart URL fetching with browser automation (hybrid approach)

Both follow the **Switchable Architecture Pattern**: Original and enhanced implementations coexist, toggle via environment variables.

---

## 🔄 Docling Integration (Switchable Architecture)

### Overview

**Docling** is IBM's open-source AI-powered document parser integrated into ICE for professional-grade table extraction.

**Key Metrics**:
- SEC Filing tables: 0% → 97.9% extraction rate
- Email attachment tables: 42% → 97.9% accuracy
- Cost: $0/month (local execution)
- Model cache: ~500MB (DocLayNet + TableFormer + Granite-Docling VLM)

**Switchable Design**: Both original and docling implementations coexist. Toggle via `config.py` environment variables.

### Quick Toggle

```bash
# Enable docling (default: true)
export USE_DOCLING_SEC=true          # SEC filings
export USE_DOCLING_EMAIL=true        # Email attachments
export USE_DOCLING_URLS=true         # URL PDFs

# Disable (fallback to PyPDF2/pdfplumber - 42% accuracy)
export USE_DOCLING_SEC=false
export USE_DOCLING_EMAIL=false
export USE_DOCLING_URLS=false

# Verify configuration
python -c "from updated_architectures.implementation.config import ICEConfig; config = ICEConfig(); print(config.get_docling_status())"
```

### Architecture Patterns

#### Pattern 1: EXTENSION (SEC Filings)
**Before**: Metadata fetch only (0% content extraction)
**After**: Metadata + docling content extraction (97.9% tables)

```python
# updated_architectures/implementation/data_ingestion.py
if self.config.use_docling_sec:
    # Smart routing: XBRL vs docling
    if filing_type in ['10-K', '10-Q']:
        content = docling_processor.process_sec_filing(filing_url)
    else:
        content = fetch_metadata_only(filing_url)
```

#### Pattern 2: REPLACEMENT (Email Attachments)
**Before**: AttachmentProcessor with PyPDF2 (42% accuracy)
**After**: DoclingProcessor API-compatible (97.9% accuracy)

```python
# imap_email_ingestion_pipeline/attachment_processor.py
def process_attachment(self, file_path, content_type):
    if self.use_docling and content_type == 'application/pdf':
        # Use Docling (97.9% table accuracy)
        return self.docling_processor.process_pdf(file_path)
    else:
        # Fallback to PyPDF2 (42% accuracy)
        return self._extract_with_pdfplumber(file_path)
```

#### Pattern 3: NEW FEATURE (URL PDFs)
**Addition**: URL PDFs now use Docling processor

```python
# imap_email_ingestion_pipeline/intelligent_link_processor.py
async def _extract_pdf_text(self, content: bytes, filename: str):
    # 3-tier graceful degradation
    if self.use_docling_urls:
        # 1. Try Docling first (97.9% accuracy)
        docling_text = self._extract_pdf_with_docling(content, filename)
        if docling_text:
            return docling_text

    # 2. Fall back to pdfplumber (42% accuracy)
    try:
        return pdfplumber_extract(content)
    except:
        # 3. Fall back to PyPDF2 (basic text)
        return pypdf2_extract(content)
```

### Key Features

**SEC Filing Processor** (`src/ice_docling/sec_filing_processor.py` - 280 lines):
- Extracts financial tables from 10-K/10-Q filings
- Smart routing: XBRL vs docling (future XBRL parser ready)
- RobustHTTPClient integration (circuit breaker + retry)
- Downloads with caching to `data/sec_filings/`
- EntityExtractor + GraphBuilder integration

**Email Attachment Processor** (`src/ice_docling/docling_processor.py` - 150 lines):
- Drop-in replacement for `AttachmentProcessor`
- API-compatible: same `process_attachment()` interface
- Handles images (PNG, JPEG), PDFs, Excel, Word, PowerPoint
- Storage structure: `data/attachments/{email_uid}/{file_hash}/`
- Returns `{'extracted_text': ..., 'extracted_data': {'tables': [...]}, ...}`

**URL PDF Processor** (integrated 2025-11-04):
- Added `process_pdf_bytes()` method to DoclingProcessor
- BytesIO + DocumentStream (official Docling API)
- IntelligentLinkProcessor integration with graceful degradation
- Same storage path as email attachments (unified architecture)

### Model Pre-loading

```bash
# Download ~500MB AI models (one-time setup)
python scripts/download_docling_models.py

# Models downloaded:
# - DocLayNet: Document layout analysis
# - TableFormer: Table structure recognition
# - Granite-Docling VLM: Visual language model

# Cached at: ~/.cache/docling/
```

### Production Patterns

1. **RobustHTTPClient**: Circuit breaker + retry + connection pooling
2. **Caching**: Downloaded files cached to avoid re-processing
3. **Clear Error Handling**: Actionable error messages with solutions
4. **No Auto-Fallback**: Fails explicitly if Docling not configured (no silent degradation)
5. **API Compatibility**: Same interface as original processors
6. **Code Reuse**: 2.4x ratio (1,767 lines reused / 656 new)

### Integration Files

| File | Lines | Purpose |
|------|-------|---------|
| `src/ice_docling/docling_processor.py` | 150 | Email attachments + URL PDFs |
| `src/ice_docling/sec_filing_processor.py` | 280 | SEC filings processor |
| `scripts/download_docling_models.py` | 106 | Model pre-loader |
| `updated_architectures/implementation/config.py` | +10 | Configuration toggles |
| `updated_architectures/implementation/data_ingestion.py` | +20 | Orchestration wiring |

### Comprehensive Documentation

| Document | Lines | Purpose |
|----------|-------|---------|
| `md_files/DOCLING_INTEGRATION_TESTING.md` | 267 | Testing procedures, toggle usage |
| `md_files/DOCLING_INTEGRATION_ARCHITECTURE.md` | 241 | Architecture patterns, design decisions |
| `md_files/DOCLING_FUTURE_INTEGRATIONS.md` | 190 | Future integrations (uploads, archives, news) |

### Testing

```bash
# Test SEC filing processing
python tmp/tmp_docling_sec_test.py

# Test email attachment processing
python tmp/tmp_docling_email_test.py

# Test URL PDF processing
python tmp/tmp_phase2_docling_url_test.py

# Validate configuration
python -c "from config import ICEConfig; print(ICEConfig().get_docling_status())"
```

### Troubleshooting

**Issue**: "Docling module not found"
```bash
# Solution
pip install docling
python scripts/download_docling_models.py
```

**Issue**: "Models not cached"
```bash
# Solution
python scripts/download_docling_models.py
ls ~/.cache/docling/  # Verify ~500MB cache
```

**Issue**: "Want to disable Docling temporarily"
```bash
# Solution
export USE_DOCLING_EMAIL=false
export USE_DOCLING_SEC=false
export USE_DOCLING_URLS=false
```

### Serena Memories

- `docling_integration_comprehensive_2025_10_19` - Initial integration
- `docling_table_extraction_implementation_2025_10_20` - Table extraction
- `url_pdf_docling_integration_phase2_2025_11_04` - URL PDF integration

---

## 🌐 Crawl4AI Integration (Hybrid URL Fetching)

### Overview

**Crawl4AI** provides smart routing between simple HTTP and browser automation for URL processing.

**Key Metrics**:
- URL success rate: 60% (simple HTTP) → 85% (hybrid)
- 6-tier classification system
- Tier 1-2: Always enabled (simple HTTP)
- Tier 3-5: Requires enablement (browser automation)
- Tier 6: Always skipped (social media, tracking)

**Switchable Design**: Simple HTTP (fast, free, default) + Crawl4AI (premium portals, JS sites, optional).

### Quick Toggle

```bash
# Enable Crawl4AI (hybrid approach)
export USE_CRAWL4AI_LINKS=true
export CRAWL4AI_TIMEOUT=60           # Timeout per page (seconds)
export CRAWL4AI_HEADLESS=true        # Run browser in background

# URL Rate Limiting (added 2025-11-05 for robustness)
export URL_RATE_LIMIT_DELAY=1.0      # Seconds between requests per domain
export URL_CONCURRENT_DOWNLOADS=3     # Max concurrent downloads

# Disable (simple HTTP only, default)
export USE_CRAWL4AI_LINKS=false
```

### 6-Tier URL Classification System

| Tier | Type | Examples | Method | Required |
|------|------|----------|--------|----------|
| **1** | Direct PDF links | DBS PDFs, UBS reports | Simple HTTP | Always enabled |
| **2** | Token-authenticated | SEC EDGAR | Simple HTTP + auth | Always enabled |
| **3** | JavaScript-rendered | Goldman Sachs, Morgan Stanley | Crawl4AI | Needs enablement |
| **4** | Premium portals | Bloomberg, Reuters IR pages | Crawl4AI | Needs enablement |
| **5** | Paywalled content | WSJ, Financial Times | Crawl4AI | Needs enablement |
| **6** | Skip | Social media, tracking | - | Always skipped |

### Smart Routing Logic

```python
# imap_email_ingestion_pipeline/intelligent_link_processor.py

async def fetch_url(self, url):
    # Classify URL (returns tier 1-6)
    tier = self._classify_url(url)

    if tier in [1, 2]:
        # Simple HTTP (fast, free, always works)
        # Good for: Direct PDFs, SEC EDGAR, UBS reports
        content = await self._download_with_retry(session, url)

    elif tier in [3, 4, 5] and self.use_crawl4ai:
        # Browser automation (slower, resource-intensive)
        # Good for: Goldman Sachs, Morgan Stanley, Bloomberg portals
        content = await self._fetch_with_crawl4ai(url)

    else:
        # Graceful degradation: fallback to simple HTTP
        try:
            content = await self._download_with_retry(session, url)
        except:
            if self.use_crawl4ai:
                content = await self._fetch_with_crawl4ai(url)
            else:
                logger.warning(f"URL tier {tier} requires Crawl4AI enablement")
    return content
```

### URL Classification Examples

```python
# Tier 1: Direct PDF links (always works)
"https://www.dbs.com/research/NVDA_report.pdf"
"https://www.ubs.com/ir/quarterly_earnings.pdf"

# Tier 2: Token-authenticated (simple HTTP + credentials)
"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001234567"

# Tier 3: JavaScript-rendered (needs Crawl4AI)
"https://www.goldmansachs.com/insights/pages/research.html"
"https://www.morganstanley.com/ideas/semiconductor-outlook"

# Tier 4: Premium portals (needs Crawl4AI)
"https://www.bloomberg.com/company/press-releases/nvda-earnings"
"https://ir.reuters.com/investor-relations/financial-reports"

# Tier 5: Paywalled (needs Crawl4AI + subscription)
"https://www.wsj.com/articles/nvidia-chip-shortage-continues"
"https://www.ft.com/content/semiconductor-analysis"

# Tier 6: Skip (social media, tracking)
"https://twitter.com/nvidia/status/12345"
"https://www.facebook.com/nvidia/posts/67890"
```

### Success Criteria (4 Levels)

1. **Level 1**: URLs extracted from email bodies ✅
2. **Level 2**: Content downloaded via HTTP or Crawl4AI ⚠️ (needs enablement for Tier 3-5)
3. **Level 3**: Text/tables extracted via Docling ✅
4. **Level 4**: Entities/relationships ingested into LightRAG ✅

### Cache Management

```bash
# Check cache status
ls -lh data/link_cache/

# Clear cache for testing
rm -rf data/link_cache/*

# Cache structure:
# data/link_cache/{domain_hash}/{url_hash}.html
# data/link_cache/{domain_hash}/{url_hash}_metadata.json
```

### Configuration in code

```python
# updated_architectures/implementation/config.py
self.use_crawl4ai_links = os.getenv('USE_CRAWL4AI_LINKS', 'false').lower() == 'true'
self.crawl4ai_timeout = int(os.getenv('CRAWL4AI_TIMEOUT', '60'))
self.crawl4ai_headless = os.getenv('CRAWL4AI_HEADLESS', 'true').lower() == 'true'

# URL rate limiting (added 2025-11-05)
self.rate_limit_delay = float(os.getenv('URL_RATE_LIMIT_DELAY', '1.0'))
self.concurrent_downloads = int(os.getenv('URL_CONCURRENT_DOWNLOADS', '3'))
```

### Integration Files

| File | Lines | Purpose |
|------|-------|---------|
| `imap_email_ingestion_pipeline/intelligent_link_processor.py` | +103 | Smart routing logic |
| `updated_architectures/implementation/config.py` | +15 | Configuration toggles |
| `ice_building_workflow.ipynb` | +10 | Cell 1 env var setup |

### Testing

```bash
# Test with Crawl4AI enabled
export USE_CRAWL4AI_LINKS=true
python tmp/tmp_crawl4ai_test.py

# Test with Crawl4AI disabled (simple HTTP only)
export USE_CRAWL4AI_LINKS=false
python tmp/tmp_crawl4ai_test.py

# Check which URLs succeeded/failed
grep "Successfully fetched" logs/link_processor.log
grep "Failed to fetch" logs/link_processor.log
```

### Troubleshooting

**Issue**: "Crawl4AI not installed"
```bash
# Solution
pip install crawl4ai playwright
playwright install chromium
```

**Issue**: "Tier 3-5 URLs failing"
```bash
# Diagnosis
export USE_CRAWL4AI_LINKS=false  # Check if tier classification is correct
grep "URL tier" logs/link_processor.log

# Solution (if tier 3-5 URLs failing)
export USE_CRAWL4AI_LINKS=true  # Enable Crawl4AI
```

**Issue**: "Too many concurrent requests"
```bash
# Solution
export URL_CONCURRENT_DOWNLOADS=1  # Reduce concurrency
export URL_RATE_LIMIT_DELAY=2.0    # Increase delay
```

### Comprehensive Documentation

| Document | Purpose |
|----------|---------|
| `md_files/CRAWL4AI_INTEGRATION_PLAN.md` | Complete integration strategy |
| `md_files/CRAWL4AI_TESTING_GUIDE.md` | Testing procedures |
| `md_files/CRAWL4AI_TEST_EMAILS.md` | Test email dataset |

### Serena Memories

- `crawl4ai_hybrid_integration_plan_2025_10_21` - Integration strategy
- `crawl4ai_6tier_classification_phase1_2025_11_02` - 6-tier classification
- `crawl4ai_enablement_notebook_2025_11_04` - Notebook integration

### Notebook Enablement

```python
# ice_building_workflow.ipynb Cell 1
import os

# Crawl4AI configuration (optional - for premium portals)
os.environ['USE_CRAWL4AI_LINKS'] = 'true'
os.environ['CRAWL4AI_TIMEOUT'] = '60'
os.environ['CRAWL4AI_HEADLESS'] = 'true'

# URL rate limiting
os.environ['URL_RATE_LIMIT_DELAY'] = '1.0'
os.environ['URL_CONCURRENT_DOWNLOADS'] = '3'
```

---

## 🔀 Integration Comparison

| Feature | Docling | Crawl4AI |
|---------|---------|----------|
| **Purpose** | Document parsing (PDFs, images, tables) | URL fetching (web scraping) |
| **Accuracy** | 97.9% table extraction | 85% URL success rate (vs 60% simple HTTP) |
| **Cost** | $0/month (local execution) | $0/month (local browser) |
| **Setup** | `pip install docling` + model download (~500MB) | `pip install crawl4ai playwright` + chromium |
| **When to Enable** | Always (default: true) | Only for Tier 3-5 URLs (default: false) |
| **Fallback** | PyPDF2/pdfplumber (42% accuracy) | Simple HTTP (60% success rate) |
| **Performance** | 6-15s per document | 3-10s per URL |
| **Resource Usage** | ~500MB model cache | ~200MB browser cache |

---

## 🎯 When to Use Each Integration

### Use Docling When:
- ✅ Processing SEC filings (10-K, 10-Q, 8-K)
- ✅ Extracting tables from email attachments (PDFs, Excel)
- ✅ Processing URL-linked research reports
- ✅ Need >95% table extraction accuracy
- ✅ Local execution preferred (no cloud costs)

### Use Crawl4AI When:
- ✅ URLs require JavaScript rendering (Goldman, Morgan Stanley)
- ✅ Premium portals need browser automation (Bloomberg, Reuters)
- ✅ Paywalled content requires session handling (WSJ, FT)
- ✅ Simple HTTP fails for specific domains
- ⚠️ **Not needed** for direct PDF links (Tier 1-2)

### Use Neither (Simple HTTP) When:
- ✅ Direct PDF links work (DBS, UBS, SEC EDGAR)
- ✅ Cost minimization is priority
- ✅ Speed is more important than success rate
- ✅ URLs are Tier 1-2 classification

---

## 📚 Related Documentation

- **CLAUDE.md** - Core daily workflows (parent document)
- **CLAUDE_PATTERNS.md** - ICE coding patterns (patterns 6-7 details)
- **ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md** - UDMA architecture
- **README.md** - Storage architecture section
- **Serena Memories** - Implementation-specific details

---

**Last Updated**: 2025-11-05
**Maintained By**: Claude Code + Roy Yeo
**Version**: 1.0
