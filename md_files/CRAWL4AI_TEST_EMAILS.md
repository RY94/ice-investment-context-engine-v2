# Test Emails for Crawl4AI Integration

**Created**: 2025-10-22
**Purpose**: Identify which emails to use for testing Crawl4AI link processing

---

## 🎯 Key Finding: Two Different Testing Purposes

### 📎 Attachment Processing (Docling) - 6 Emails
**From**: `pipeline_demo_notebook.ipynb` Cell 32
**What they test**: PDF/Excel/Image extraction from email **attachments**
**NOT for Crawl4AI**: These were selected for attachment processing, not link processing

### 🔗 Link Processing (Crawl4AI) - 62 Emails
**Found**: 62 out of 71 sample emails contain URLs
**What they test**: Downloading research reports from URLs in email **body**
**Perfect for Crawl4AI**: These contain actual research portal links

---

## 📧 Best Emails for Crawl4AI Testing

### ✅ DBS Research Portal URLs (5+ emails)

These emails contain `researchwise.dbsvresearch.com` URLs - **PERFECT for Crawl4AI testing**:

1. **CH_HK_ Foshan Haitian Flavouring (3288 HK)_ Brewing the sauce of success (NOT RATED).eml**
   - Contains: DBS research portal URL with embedded auth token
   - URL format: `https://researchwise.dbsvresearch.com/...?E=...`
   - Expected: Simple HTTP download (DBS URLs work without Crawl4AI)

2. **CH_HK_ Lianlian Digitech Co Ltd (2598 HK)_ Capturing stablecoin opportunity in crossborder payments (NOT RATED).eml**
   - Contains: DBS research portal URL
   - Expected: PDF download via simple HTTP

3. **CH_HK_ Nongfu Spring Co. Ltd (9633 HK)_ Leading the pack (NOT RATED).eml**
   - Contains: DBS research portal URL
   - Expected: PDF download via simple HTTP

4. **CH_HK_ Tencent Music Entertainment (1698 HK)_ Stronger growth with expanding revenue streams (NOT RATED).eml**
   - Contains: DBS research portal URL
   - Expected: PDF download via simple HTTP
   - **Note**: This is the email tested in `tmp_test_docling_workflow.py` (verified working!)

5. **DBS Economics & Strategy_ India_ Effects of 50% tariff.eml**
   - Contains: DBS research portal URL
   - Expected: PDF download via simple HTTP

---

## 🧪 Testing Verification

### Quick Test: Check if Email Has Research URLs

```bash
cd data/emails_samples

# Test with Tencent email (verified working in previous tests)
FILE="CH_HK_ Tencent Music Entertainment (1698 HK)_ Stronger growth with expanding revenue streams  (NOT RATED).eml"

if grep -q "researchwise.dbsvresearch.com" "$FILE"; then
    echo "✅ Found DBS research URL"
    grep -o "https://researchwise[^\"]*" "$FILE" | head -1
fi
```

**Expected URL format**:
```
https://researchwise.dbsvresearch.com/ResearchManager/DownloadResearch.aspx?E=iggjhkgbchd
```

---

## 📊 Email Statistics

**Total sample emails**: 71
**Emails with URLs**: 62 (87%)
**Emails with DBS research URLs**: 5+ confirmed
**Emails with attachments only**: 9 (13%)

---

## 🎯 Recommended Testing Approach

### Test 1: Single Email (Quick Validation - 2 minutes)

**Email**: `CH_HK_ Tencent Music Entertainment (1698 HK)_ Stronger growth with expanding revenue streams (NOT RATED).eml`

**Why**: Already verified working in `tmp_test_docling_workflow.py`
- Downloaded: 223 KB PDF
- Extracted: 42K chars, 4 tables
- Simple HTTP works (no Crawl4AI needed)

**How to test**:
```python
# In ice_building_workflow.ipynb, after DataIngester initialization:

# Test with single email
from pathlib import Path
emails_dir = Path("data/emails_samples")
test_file = "CH_HK_ Tencent Music Entertainment (1698 HK)_ Stronger growth with expanding revenue streams  (NOT RATED).eml"

# Process just this email to verify link processing
docs = ingester.fetch_email_documents(limit=1)  # Will process first email alphabetically

# Check logs for:
# - "IntelligentLinkProcessor initialized"
# - "Downloaded X research reports from email links"

# Check downloaded files
!ls -lh data/downloaded_reports/
```

---

### Test 2: Multiple Emails (Full Validation - 10 minutes)

**Emails**: Use all 5 DBS research emails

**How to test**: Run `ice_building_workflow.ipynb` with:
```python
PORTFOLIO_SIZE = 'tiny'    # 10 min, 18 docs
REBUILD_GRAPH = True       # Required
```

**Expected results**:
- 5+ research reports downloaded from DBS URLs
- PDFs in `data/downloaded_reports/`
- Enhanced documents contain `[LINKED_REPORT:URL]` markers
- Knowledge graph searchable for report content

---

## 📋 Success Indicators

When testing with these emails, you should see:

### ✅ In Logs
```
INFO:updated_architectures.implementation.data_ingestion:✅ IntelligentLinkProcessor initialized (hybrid URL fetching)
INFO:imap_email_ingestion_pipeline.intelligent_link_processor:Starting intelligent link processing
INFO:imap_email_ingestion_pipeline.intelligent_link_processor:Extracted 1 links from email
INFO:imap_email_ingestion_pipeline.intelligent_link_processor:Classified 1 research reports, 0 portal links, 0 other links
INFO:updated_architectures.implementation.data_ingestion:Downloaded 1 research reports from email links in CH_HK_ Tencent Music Entertainment (1698 HK)...
```

### ✅ In Files
```bash
$ ls -lh data/downloaded_reports/
-rw-r--r--  1 user  staff   223K Oct 22 14:30 tencent_music_research.pdf
-rw-r--r--  1 user  staff   512K Oct 22 14:31 foshan_haitian_research.pdf
...
```

### ✅ In Enhanced Documents
```python
# Check enhanced document content
print(docs[0][:1000])

# Should contain:
# [SOURCE_EMAIL:...]
# [TICKER:1698.HK|confidence:0.95]
# ...
# ---
# [LINKED_REPORT:https://researchwise.dbsvresearch.com/...]
# Full research report content here...
```

---

## ⚠️ Important Notes

### 1. Attachment Processing ≠ Link Processing

**Attachment Processing** (Docling):
- Files **attached** to emails (PDF, Excel, images)
- Processed during email parsing
- Already downloaded with email

**Link Processing** (Crawl4AI):
- URLs in email **body text**
- Require separate HTTP request to download
- This is what we're testing!

### 2. DBS URLs Don't Need Crawl4AI

DBS research portal URLs have embedded auth tokens (`?E=...`):
- Work with simple HTTP (fast, <2s)
- No browser automation needed
- Crawl4AI hybrid routing will classify as "simple" and use simple HTTP

**To test Crawl4AI browser automation**, you'd need:
- Premium portal URLs (Goldman, Morgan Stanley)
- JS-heavy IR sites (ir.nvidia.com)
- These may not be in sample emails

### 3. Expected Behavior

With `USE_CRAWL4AI_LINKS=false` (default):
- ✅ All URLs use simple HTTP
- ✅ DBS URLs download successfully
- ✅ Link processing works

With `USE_CRAWL4AI_LINKS=true`:
- ✅ DBS URLs still use simple HTTP (smart routing)
- ✅ Premium portals would use Crawl4AI (if present)
- ✅ Graceful fallback if Crawl4AI fails

---

## 🔍 Finding More Test Emails

### All Emails with URLs
```bash
cd data/emails_samples
grep -l "https\?://" *.eml > ../emails_with_urls.txt
wc -l ../emails_with_urls.txt
# Output: 62 emails
```

### Emails with Specific Domains
```bash
# DBS research
grep -l "researchwise\.dbsvresearch\.com" *.eml

# Goldman Sachs (if any)
grep -l "goldmansachs\.com" *.eml

# Morgan Stanley (if any)
grep -l "morganstanley\.com" *.eml

# Investor Relations
grep -l "investor\." *.eml
```

---

## 🎯 Quick Start Guide

**Want to test Crawl4AI integration right now?**

1. **Open** `ice_building_workflow.ipynb`
2. **Set** `PORTFOLIO_SIZE = 'tiny'` and `REBUILD_GRAPH = True`
3. **Run** all cells
4. **Watch logs** for "Downloaded X research reports from email links"
5. **Check** `data/downloaded_reports/` directory for PDFs
6. **Verify** success with verification cell (see CRAWL4AI_TESTING_GUIDE.md)

**That's it!** The 62 emails with URLs will automatically be processed, and you'll see link processing in action.

---

**Summary**: 
- ❌ **Don't use** the 6 Docling test emails for Crawl4AI (they're for attachments)
- ✅ **Use** the 5+ DBS research emails (they have actual research portal URLs)
- ✅ **Best test**: Run `ice_building_workflow.ipynb` and watch for "Downloaded X research reports"

