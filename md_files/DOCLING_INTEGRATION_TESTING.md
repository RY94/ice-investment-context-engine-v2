# Docling Integration Testing Guide

**Location**: `md_files/DOCLING_INTEGRATION_TESTING.md`
**Purpose**: Comprehensive testing procedures for docling integration
**Audience**: Developers testing docling switchable architecture
**Related Files**: `config.py`, `DOCLING_INTEGRATION_ARCHITECTURE.md`

---

## 🎯 Overview

Docling integration uses **switchable architecture** - toggle between original implementations and docling processors without code changes.

**Toggle Configuration**: Environment variables read by `config.py`

| Toggle | Default | Original | Docling | Improvement |
|--------|---------|----------|---------|-------------|
| `USE_DOCLING_SEC` | `true` | Metadata only (0%) | Full content + tables (97.9%) | ∞ |
| `USE_DOCLING_EMAIL` | `true` | PyPDF2 (42% accuracy) | Docling (97.9% accuracy) | 2.3x |

---

## 🚀 Quick Start: Toggle Configuration

### Method 1: Environment Variables (Recommended)

```bash
# Enable docling for SEC filings (default)
export USE_DOCLING_SEC=true

# Enable docling for email attachments (default)
export USE_DOCLING_EMAIL=true

# Disable docling for SEC (use metadata-only)
export USE_DOCLING_SEC=false

# Disable docling for email (use PyPDF2)
export USE_DOCLING_EMAIL=false
```

### Method 2: Inline Configuration (for testing)

```python
import os
os.environ['USE_DOCLING_SEC'] = 'false'  # Set before importing ICE

from updated_architectures.implementation.ice_simplified import ICESimplified
ice = ICESimplified()

# Check status
print(ice.config.get_docling_status())
# {'sec_filings': False, 'email_attachments': True, ...}
```

---

## 🧪 Testing Strategy: Three-Tier Approach

### Tier 1: Unit Testing (Component Level)

Test each processor standalone without full ICE integration.

#### Test 1.1: SEC Filing Processor

```python
# Test SEC processor directly
from src.ice_docling.sec_filing_processor import SECFilingProcessor
from ice_data_ingestion.sec_edgar_connector import SECEdgarConnector
from ice_data_ingestion.robust_client import RobustHTTPClient
from imap_email_ingestion_pipeline.entity_extractor import EntityExtractor
from imap_email_ingestion_pipeline.graph_builder import GraphBuilder

# Initialize
processor = SECFilingProcessor(
    entity_extractor=EntityExtractor(),
    graph_builder=GraphBuilder(),
    robust_client=RobustHTTPClient('sec_edgar'),
    sec_connector=SECEdgarConnector()
)

# Extract single filing
result = processor.extract_filing_content(
    accession_number='0001318605-24-000004',  # NVDA 10-K example
    primary_document='nvda-20240128.htm',
    ticker='NVDA',
    is_xbrl=True,
    is_inline_xbrl=False
)

# Verify
assert result['enhanced_document'] is not None
assert result['extracted_entities'] is not None
assert result['graph_data'] is not None
assert len(result['tables']) >= 0
print(f"✅ SEC processor test passed: {len(result['enhanced_document'])} chars")
```

#### Test 1.2: Docling Email Processor

```python
# Test docling processor with sample attachment
from src.ice_docling.docling_processor import DoclingProcessor
from pathlib import Path

processor = DoclingProcessor('test_storage')

# Mock attachment data (similar to email part)
test_pdf = Path('data/attachments/sample_research.pdf')
if test_pdf.exists():
    with open(test_pdf, 'rb') as f:
        content = f.read()

    # Create mock attachment_data
    class MockPart:
        def get_payload(self, decode=True):
            return content if decode else None

    attachment_data = {
        'part': MockPart(),
        'filename': 'sample_research.pdf',
        'content_type': 'application/pdf'
    }

    result = processor.process_attachment(attachment_data, 'test_email_001')

    # Verify
    assert result['processing_status'] == 'completed'
    assert result['extraction_method'] == 'docling'
    assert len(result['extracted_text']) > 0
    print(f"✅ Docling processor test passed: {result['page_count']} pages")
```

### Tier 2: Integration Testing (with EntityExtractor/GraphBuilder)

Test processors integrated with ICE components.

#### Test 2.1: SEC Integration Test

```bash
# Set toggle
export USE_DOCLING_SEC=true

# Run notebook
jupyter notebook ice_building_workflow.ipynb

# In notebook cell:
ice.ingest_portfolio_data(['NVDA'])

# Expected: SEC filings have enhanced documents with [TICKER:NVDA|confidence:0.95] markup
# Check: len(ice.ingester.last_graph_data) > 0 (graph data stored for Phase 2.6.2)
```

#### Test 2.2: Email Integration Test

```bash
# Set toggle
export USE_DOCLING_EMAIL=true

# Run notebook
jupyter notebook ice_building_workflow.ipynb

# In notebook cell:
ice.ingest_portfolio_data(['NVDA'])

# Check logs for:
# "✅ DoclingProcessor initialized (97.9% table accuracy)"
```

### Tier 3: PIVF Validation (Business Logic)

Test with actual investment queries from `test_queries.csv`.

#### Test 3.1: SEC Content Query (Q6 from PIVF)

**Query**: "What is TSMC's customer concentration risk?" (requires SEC 10-K data)

```python
# Enable SEC docling
export USE_DOCLING_SEC=true

# Rebuild knowledge graph
jupyter notebook ice_building_workflow.ipynb
ice.ingest_portfolio_data(['TSM'])  # TSMC

# Query
jupyter notebook ice_query_workflow.ipynb
response = ice.query("What is TSMC's customer concentration risk?", mode='hybrid')

# Expected: Response includes financial data from 10-K
# Without docling (USE_DOCLING_SEC=false): Only metadata, no concentration risk data
```

#### Test 3.2: Combined Email + SEC Query (Q11 from PIVF)

**Query**: "Are there any BUY or SELL recommendations for NVDA from major analysts?"

```python
# Enable both toggles
export USE_DOCLING_SEC=true
export USE_DOCLING_EMAIL=true

# Rebuild knowledge graph
ice.ingest_portfolio_data(['NVDA'])

# Query
response = ice.query("Are there any BUY or SELL recommendations for NVDA?", mode='hybrid')

# Expected: Combines email recommendations + SEC financial context
```

---

## 📊 Comparison Testing: PyPDF2 vs Docling

### Test 4: Table Extraction Accuracy

**Objective**: Quantify improvement in table extraction

```python
# Test with both processors
import os

# Test 1: PyPDF2 (original)
os.environ['USE_DOCLING_EMAIL'] = 'false'
from updated_architectures.implementation.data_ingestion import DataIngester
ingester1 = DataIngester()
result1 = ingester1.attachment_processor.process_attachment(attachment_data, 'test_001')

# Test 2: Docling
os.environ['USE_DOCLING_EMAIL'] = 'true'
ingester2 = DataIngester()
result2 = ingester2.attachment_processor.process_attachment(attachment_data, 'test_002')

# Compare
print(f"PyPDF2 chars:   {len(result1['extracted_text'])}")
print(f"Docling chars:  {len(result2['extracted_text'])}")
print(f"PyPDF2 method:  {result1['extraction_method']}")
print(f"Docling method: {result2['extraction_method']}")

# Expected: Docling extracts more content and tables with higher accuracy
```

### Benchmark Results (Expected)

| Metric | PyPDF2 (Original) | Docling | Improvement |
|--------|-------------------|---------|-------------|
| Table Accuracy | 42% | 97.9% | 2.3x |
| Processing Time | 0.5s/page | 3s/page | 6x slower (acceptable) |
| Text Extraction | Basic | Enhanced (markdown) | Better structure |
| Cost | $0 | $0 | Same |

---

## 🔧 Troubleshooting

### Issue 1: Models Not Downloaded

**Error**: `FileNotFoundError: Model file not found`

**Solution**:
```bash
python scripts/download_docling_models.py
# Wait 5-10 minutes for ~500MB download
# Re-run your test
```

### Issue 2: ImportError for Docling

**Error**: `ImportError: No module named 'docling'`

**Solution**:
```bash
pip install docling
python scripts/download_docling_models.py
```

### Issue 3: Toggle Not Working

**Symptoms**: Still using old processor despite setting toggle

**Debug**:
```python
from updated_architectures.implementation.ice_simplified import ICESimplified
ice = ICESimplified()

# Check config
print(ice.config.get_docling_status())
# Should show: {'sec_filings': True, 'email_attachments': True, ...}

# Check which processor was loaded
print(type(ice.ingester.attachment_processor).__name__)
# Should show: 'DoclingProcessor' (if toggle enabled) or 'AttachmentProcessor' (if disabled)
```

**Fix**: Ensure environment variable set BEFORE importing ICE
```python
import os
os.environ['USE_DOCLING_EMAIL'] = 'true'  # MUST be before import

from updated_architectures.implementation.ice_simplified import ICESimplified
ice = ICESimplified()
```

### Issue 4: SEC Extraction Failed

**Error**: `RuntimeError: ❌ SEC filing extraction failed...`

**Solutions**:
1. Check network connection (SEC EDGAR requires internet)
2. Run model pre-loader: `python scripts/download_docling_models.py`
3. Fallback to metadata: `export USE_DOCLING_SEC=false`

---

## ✅ Validation Checklist

**Before Declaring Success**:

- [ ] Config toggles work (can switch implementations without code changes)
- [ ] SEC processor: 0% → 97.9% table extraction
- [ ] Email processor: 42% → 97.9% table accuracy
- [ ] EntityExtractor integration: Enhanced documents have inline markup
- [ ] GraphBuilder integration: graph_data stored in last_graph_data
- [ ] PIVF Q6 answerable: "What is TSMC's customer concentration risk?"
- [ ] PIVF Q11 answerable: "BUY/SELL recommendations for NVDA?"
- [ ] Original implementations still work (backward compatible)
- [ ] No breaking changes to existing workflows

---

## 📋 Testing Workflow Summary

**Day 1: Unit Testing**
1. Test SEC processor standalone
2. Test Docling processor standalone
3. Verify API compatibility

**Day 2: Integration Testing**
1. Test with EntityExtractor/GraphBuilder
2. Verify graph_data storage
3. Check inline markup format

**Day 3: PIVF Validation**
1. Run Q6 (SEC content required)
2. Run Q11 (Email + SEC combined)
3. Validate accuracy and completeness

**Day 4: Comparison Benchmarks**
1. PyPDF2 vs Docling table extraction
2. Processing time measurements
3. Document quality comparison

---

**Last Updated**: 2025-10-19
**Related**: `DOCLING_INTEGRATION_ARCHITECTURE.md`, `config.py`
**Next Steps**: After testing, update `PROJECT_CHANGELOG.md` with validation results
