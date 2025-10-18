# IMAP Email Pipeline Integration Reference

**Location**: CLAUDE.md Section 6 (migrated to Serena 2025-10-18)
**Purpose**: Comprehensive reference for IMAP email pipeline integration patterns and workflows
**Related Files**: `updated_architectures/implementation/data_ingestion.py`, `imap_email_ingestion_pipeline/`, `ice_simplified.py`

---

## Overview

The IMAP email pipeline (`imap_email_ingestion_pipeline/`, 12,810 lines) processes 71 broker research emails into enhanced documents with inline entity markup. It is one of three data sources feeding LightRAG, alongside API/MCP and SEC filings.

## Three-Source Data Flow

```
ICESimplified.ingest_portfolio_data(holdings)
    ↓
DataIngester.fetch_comprehensive_data([symbol])
    ↓
┌─────────────────────────────────────────────────────┐
│ SOURCE 1: Email (IMAP Pipeline)                     │
│   fetch_email_documents(tickers=None, limit=71)     │
├─────────────────────────────────────────────────────┤
│ SOURCE 2: API/MCP (per symbol)                      │
│   fetch_company_news() + fetch_company_financials() │
├─────────────────────────────────────────────────────┤
│ SOURCE 3: SEC EDGAR (per symbol)                    │
│   fetch_sec_filings(symbol, limit=3)                │
└─────────────────────────────────────────────────────┘
    ↓
ICECore.add_documents_batch() → LightRAG
```

**Trust the Graph**: Uses `tickers=None` to enable cross-company relationship discovery (Entry #60).

## Integration Points

### 1. Initialization (`data_ingestion.py:88-100`)

```python
self.entity_extractor = EntityExtractor(config_dir)  # 668 lines
self.graph_builder = GraphBuilder()                   # 680 lines
self.attachment_processor = AttachmentProcessor()     # PDF/Excel
```

### 2. Email Processing (`data_ingestion.py:299-476`)

```python
def fetch_email_documents(self, tickers=None, limit=71):
    # Read 71 .eml files from data/emails_samples/
    # EntityExtractor: tickers, ratings, price targets, analysts
    # GraphBuilder: typed relationships (ANALYST_RECOMMENDS, FIRM_COVERS)
    # Returns: enhanced documents with inline markup
    return enhanced_documents
```

### 3. Orchestration (`ice_simplified.py:920-997`)

```python
for symbol in holdings:
    documents = self.ingester.fetch_comprehensive_data([symbol])
    self.core.add_documents_batch(documents)  # Combines all 3 sources
```

## IMAP Components

| Component | Purpose | Lines |
|-----------|---------|-------|
| **EntityExtractor** | Extract tickers, ratings, price targets, analysts with confidence scores | 668 |
| **GraphBuilder** | Create typed relationships (ANALYST_RECOMMENDS, FIRM_COVERS, PRICE_TARGET_SET) | 680 |
| **AttachmentProcessor** | Extract text from PDF/Excel (3/71 emails have attachments) | - |

## Enhanced Document Format

```
[TICKER:NVDA|confidence:0.95] [RATING:BUY|confidence:0.87]

Goldman Sachs raised price target to [PRICE_TARGET:500|confidence:0.92].

Source: broker_research_20240315.eml
```

**Result**: Improves LightRAG precision via embedded entity metadata.

## Working with Email Data

### Standard Workflow (Automatic 3-Source Integration)

```python
ice.ingest_portfolio_data(['NVDA', 'AAPL'])
```

### Access Structured Data (Phase 2.6.2)

```python
ingester.last_extracted_entities  # 71 entity dicts
ingester.last_graph_data          # 71 NetworkX graphs
```

### Email-Only Testing

```python
email_docs = ingester.fetch_email_documents(limit=10)
```

**Filter by ticker**: Use `tickers=['NVDA']` for testing only. Production uses `tickers=None`.

## Implementation Status

- ✅ **Phase 2.6.1 Complete**: All IMAP components integrated, 71 emails processed, enhanced documents in LightRAG
- ⏳ **Phase 2.6.2 Planned**: Investment Signal Store (SQLite) for fast structured queries using `last_extracted_entities`

## References

- **Testing**: `tests/test_email_graph_integration.py`, `tests/test_imap_email_pipeline_comprehensive.py`
- **Deep Dive**: Serena memories `comprehensive_email_extraction_2025_10_16`, `email_ingestion_trust_the_graph_strategy_2025_10_17`
- **Notebooks**: `imap_email_ingestion_pipeline/pipeline_demo_notebook.ipynb`
