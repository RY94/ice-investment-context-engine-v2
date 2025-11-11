# Crawl4AI Integration Testing Guide

## 📓 Available Notebooks for Testing

### 🎯 PRIMARY (Recommended for Testing)

#### 1. `ice_building_workflow.ipynb` - **MAIN PRODUCTION WORKFLOW**
**Location**: Project root
**What it tests**: Complete ICE system with Crawl4AI integration
**Why use this**: Tests the ACTUAL production path (DataIngester → IntelligentLinkProcessor)

**How to test**:
```python
# Cell 1: Set portfolio size
PORTFOLIO_SIZE = 'tiny'  # 10 min, 18 docs (2 tickers)
REBUILD_GRAPH = True     # Must rebuild to trigger email processing

# Cell 2: Check configuration (automatically shows)
# Look for: "IntelligentLinkProcessor initialized (hybrid URL fetching)"

# Run all cells and check logs for:
# - "✅ IntelligentLinkProcessor initialized"
# - "Downloaded X research reports from email links in [filename]"
# - Check data/downloaded_reports/ directory for PDFs
```

**Expected output**:
```
INFO:updated_architectures.implementation.data_ingestion:✅ IntelligentLinkProcessor initialized (hybrid URL fetching)
INFO:updated_architectures.implementation.data_ingestion:Downloaded 2 research reports from email links in dbs_research_nvda.eml
```

**What to verify**:
- [x] IntelligentLinkProcessor initialized
- [x] Link processing logs appear during email ingestion
- [x] Downloaded PDFs in `data/downloaded_reports/`
- [x] Enhanced documents contain [LINKED_REPORT:URL] markers
- [x] Knowledge graph contains research report content

---

#### 2. `imap_email_ingestion_pipeline/pipeline_demo_notebook.ipynb` - **EMAIL PIPELINE DEMO**
**Location**: `imap_email_ingestion_pipeline/`
**What it tests**: Detailed email processing with entity extraction, graph building
**Why use this**: Lower-level testing, shows detailed entity extraction and graph construction

**How to test**:
This notebook currently uses the old email processing pipeline (not DataIngester).
**Status**: May need updates to use DataIngester for link processing

---

### 📊 SECONDARY (For After Testing)

#### 3. `ice_query_workflow.ipynb` - **QUERY TESTING**
**Location**: Project root
**What it tests**: Query the graph AFTER it's been built with link processing
**Why use this**: Verify that linked report content is searchable

**How to test**:
```python
# After running ice_building_workflow.ipynb with REBUILD_GRAPH=True:

# Cell: Try queries that reference linked reports
query = "What research reports are available for NVDA?"
query = "What does DBS say about NVDA's China exposure?"

# Expected: Should retrieve content from both email bodies AND linked PDFs
```

---

## 🧪 Testing Workflow (Step-by-Step)

### Phase 1: Quick Verification (5 minutes)

**Test 1: Config Wiring Check**
```bash
cd updated_architectures/implementation
python3 << 'ENDTEST'
from config import ICEConfig
from data_ingestion import DataIngester

config = ICEConfig()
ingester = DataIngester(config=config)

print("=" * 60)
print("CRAWL4AI INTEGRATION CHECK")
print("=" * 60)
print(f"✓ IntelligentLinkProcessor exists: {ingester.link_processor is not None}")
print(f"✓ Config wired: {ingester.link_processor.use_crawl4ai == config.use_crawl4ai_links}")
print(f"✓ Current mode: {'Hybrid' if config.use_crawl4ai_links else 'Simple HTTP'}")
print("=" * 60)
ENDTEST
```

**Expected output**:
```
============================================================
CRAWL4AI INTEGRATION CHECK
============================================================
✓ IntelligentLinkProcessor exists: True
✓ Config wired: True
✓ Current mode: Simple HTTP
============================================================
```

---

### Phase 2: Email Processing Test (10 minutes)

**Test 2: ice_building_workflow.ipynb (Tiny Portfolio)**

1. Open `ice_building_workflow.ipynb`
2. Configure:
   ```python
   PORTFOLIO_SIZE = 'tiny'    # Fast: ~10 min, 18 docs
   REBUILD_GRAPH = True       # Required to trigger email processing
   ```
3. Run all cells
4. Monitor logs for:
   - "IntelligentLinkProcessor initialized"
   - "Downloaded X research reports from email links"
5. Check directory:
   ```bash
   ls -lh data/downloaded_reports/
   ```
6. Verify PDFs downloaded

---

### Phase 3: Content Verification (5 minutes)

**Test 3: Check Enhanced Documents**

After Phase 2 completes, check that linked reports are integrated:

```python
# In ice_building_workflow.ipynb, add a cell after graph building:

# Check last ingestion result
print(f"Documents ingested: {len(ingestion_result['email_documents'])}")

# Sample one document to verify link integration
sample_doc = ingestion_result['email_documents'][0]
if '[LINKED_REPORT:' in sample_doc:
    print("✅ Found linked report marker!")
    print("\nSample content:")
    print(sample_doc[:1000])
else:
    print("❌ No linked reports found (may be normal if emails don't have links)")
```

---

### Phase 4: Query Testing (5 minutes)

**Test 4: ice_query_workflow.ipynb**

1. Open `ice_query_workflow.ipynb`
2. Run connection cell (connects to existing graph from Phase 2)
3. Try queries:
   ```python
   # Query for research reports
   result = ice.query("What research reports mention NVDA?", mode='hybrid')
   print(result['answer'])
   
   # Query for specific content (if DBS report was downloaded)
   result = ice.query("What does DBS say about NVDA?", mode='hybrid')
   print(result['answer'])
   ```
4. Check if answers include content from linked PDFs (not just email summaries)

---

## 🔍 What to Look For

### ✅ Success Indicators

**In Logs**:
```
✅ IntelligentLinkProcessor initialized (hybrid URL fetching)
INFO: Found 3 links in email body
INFO: Classified 2 research reports, 1 portal links, 0 other
INFO: Downloaded 2 research reports from email links in dbs_nvda_research.eml
```

**In Files**:
```bash
data/downloaded_reports/
├── dbs_research_nvda_20240315.pdf
├── goldman_nvda_upgrade_20240316.pdf
└── ... (more PDFs)
```

**In Enhanced Documents**:
```
[SOURCE_EMAIL:12345|SENDER:research@dbs.com|DATE:2024-03-15]
[TICKER:NVDA|confidence:0.95]

Email content here...

---
[LINKED_REPORT:https://researchwise.dbsvresearch.com/...?E=...]
Full research report content extracted from PDF here...
(Multiple pages of detailed analysis)
```

**In Queries**:
- Answers reference both email summary AND linked report details
- Source attribution includes [LINKED_REPORT:...] markers

---

### ❌ Expected Limitations (Not Bugs)

1. **No links in sample emails**: If sample emails don't contain research report URLs, link processing will show 0 downloads
   - This is NORMAL - link processing only works when emails have URLs

2. **Simple HTTP mode only**: Default is `USE_CRAWL4AI_LINKS=false`
   - DBS URLs work with simple HTTP (fast, <2s)
   - Premium portals (Goldman, Morgan Stanley) would need Crawl4AI enabled

3. **Async processing warnings**: May see event loop warnings
   - This is cosmetic - processing still works correctly

---

## 🎛️ Configuration Options

### Default (Simple HTTP Only)
```bash
# No environment variables needed
jupyter notebook ice_building_workflow.ipynb
```

### Enable Crawl4AI (For Complex Sites)
```bash
export USE_CRAWL4AI_LINKS=true
export CRAWL4AI_TIMEOUT=60
export CRAWL4AI_HEADLESS=true

jupyter notebook ice_building_workflow.ipynb
```

---

## 📝 Debugging Checklist

If link processing doesn't work:

- [ ] Check IntelligentLinkProcessor initialized (logs)
- [ ] Verify sample emails actually contain URLs (check .eml files)
- [ ] Confirm URLs are in email body (not just subject)
- [ ] Check logs for link extraction ("Found X links")
- [ ] Verify no import errors (beautifulsoup4, aiohttp installed)
- [ ] Check data/downloaded_reports/ directory permissions

---

## 🎯 Recommended Testing Order

1. **Quick Check** (5 min): Run Test 1 (config wiring)
2. **Main Test** (10 min): Run Test 2 (ice_building_workflow.ipynb, tiny portfolio)
3. **Verify** (5 min): Run Test 3 (check enhanced documents)
4. **Query** (5 min): Run Test 4 (ice_query_workflow.ipynb)

**Total time**: ~25 minutes for complete validation

---

## 📊 Success Metrics

After testing, you should be able to confirm:

- [x] IntelligentLinkProcessor initializes without errors
- [x] Config wiring is correct (verification test passes)
- [x] Link processing runs during email ingestion
- [x] PDFs download to data/downloaded_reports/
- [x] Enhanced documents contain [LINKED_REPORT:...] markers
- [x] Knowledge graph queries return linked report content
- [x] Source attribution preserved ([LINKED_REPORT:URL])

If all checkboxes are ticked: **✅ Integration is working correctly!**

