# ICE Troubleshooting Guide

> **Purpose**: Complete troubleshooting reference for ICE development
> **Audience**: Claude Code AI instances and developers debugging issues
> **When to Load**: When debugging errors, performance issues, or data quality problems
> **Parent Doc**: `CLAUDE.md` (core daily workflows)

**Last Updated**: 2025-11-05
**Status**: Comprehensive troubleshooting reference

---

## 🚀 Quick Debugging Workflow

**First Steps** (90% of issues):
1. Check system health: `python check/health_checks.py`
2. Review logs: `logs/session_start.json`, `logs/pre_tool_use.json`
3. Validate data sources: `sandbox/python_notebook/ice_data_sources_demo_simple.ipynb`
4. Check LightRAG storage: `ls -lh ice_lightrag/storage/`
5. Test basic functionality: `python src/ice_lightrag/quick_test.py`

---

## 📋 Quick Reference Table

| Issue Type | First Action | Validation Command |
|------------|--------------|-------------------|
| **API Key** | `export OPENAI_API_KEY="sk-..."` | `python test_api_key.py` |
| **Import Error** | `export PYTHONPATH=.` | `python -c "import [module]"` |
| **LightRAG Corrupted** | `rm -rf ice_lightrag/storage/*` | Run building workflow |
| **Slow Queries** | Check hop depth, use `local` mode | Test with different modes |
| **Memory Issues** | `export NUMEXPR_MAX_THREADS=14` | `python check/health_checks.py` |
| **Docling Not Working** | `pip install docling && python scripts/download_docling_models.py` | Check `~/.cache/docling/` |
| **Crawl4AI Failing** | `export USE_CRAWL4AI_LINKS=true` | Check tier classification in logs |
| **URLs Not Saving** | Run Cell 14.5 (clear cache) | Check `data/attachments/{email_uid}/` |

---

## 1. Environment Setup Issues

### API Key Not Found

**Error**: `OpenAI API key not set` or `OPENAI_API_KEY environment variable not found`

**Solution**:
```bash
# Set API key
export OPENAI_API_KEY="sk-your-api-key-here"

# Verify
python test_api_key.py
# Should output: "✅ API Key is valid"
```

**Alternative** (SecureConfig):
```bash
# Use encrypted storage (Week 3 integration)
python scripts/rotate_credentials.py
```

### LightRAG Import Error

**Error**: `No module named 'lightrag'`

**Solution**:
```bash
# Install LightRAG
cd src/ice_lightrag && python setup.py && cd ../..

# Verify
python src/ice_lightrag/test_basic.py
```

### Module Import Failures

**Error**: `Cannot import from ice_data_ingestion`

**Solution**:
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:."

# Verify
python -c "from ice_data_ingestion import robust_client; print('OK')"
```

### Jupyter Kernel Issues

**Error**: `Kernel not found` or kernel crashes

**Solution**:
```bash
# Install ipykernel
pip install ipykernel

# Register kernel
python -m ipykernel install --user --name=ice_env

# In notebook: Kernel → Change Kernel → ice_env
```

---

## 2. Integration Errors

### Email Connector Not Found

**Error**: `No module named 'imap_email_ingestion_pipeline'`

**Diagnosis**:
```bash
# Check file exists
ls imap_email_ingestion_pipeline/email_connector.py

# Verify
python -c "from imap_email_ingestion_pipeline.email_connector import EmailConnector; print('OK')"
```

### LightRAG Storage Corruption

**Symptom**: LightRAG storage becomes corrupted, queries fail

**Solution**:
```bash
# Remove corrupted storage
rm -rf ice_lightrag/storage/*

# Recreate graph
jupyter notebook ice_building_workflow.ipynb
# Run all cells to rebuild graph
```

### Docling Integration Not Working

**Error**: `Docling module not found` or `Models not cached`

**Solution**:
```bash
# Install Docling
pip install docling

# Download models (~500MB, one-time)
python scripts/download_docling_models.py

# Verify cache
ls -lh ~/.cache/docling/
# Should show ~500MB of model files

# Test
python tmp/tmp_docling_sec_test.py
```

### Crawl4AI URLs Failing

**Error**: Tier 3-5 URLs not downloading

**Diagnosis**:
```bash
# Check if Crawl4AI is enabled
export USE_CRAWL4AI_LINKS=false  # Test with simple HTTP
grep "URL tier" logs/link_processor.log
```

**Solution**:
```bash
# Install Crawl4AI
pip install crawl4ai playwright
playwright install chromium

# Enable Crawl4AI
export USE_CRAWL4AI_LINKS=true
export CRAWL4AI_TIMEOUT=60
export CRAWL4AI_HEADLESS=true
```

---

## 3. Performance Issues

### Slow Query Response

**Symptom**: Queries taking >10 seconds

**Causes & Solutions**:

1. **High hop depth**:
```python
# DON'T: Use >3 hops
result = ice.query("...", mode="mix")  # Can traverse >3 hops

# DO: Limit to 3 hops max
result = ice.query("...", mode="hybrid")  # Optimized for 2-3 hops
```

2. **Wrong query mode**:
```python
# DON'T: Use hybrid for simple lookups
result = ice.query("What is NVDA's ticker?", mode="hybrid")

# DO: Use local for simple queries
result = ice.query("What is NVDA's ticker?", mode="local")
```

3. **Check graph size**:
```bash
# Check storage size
du -sh ice_lightrag/storage/
# If >1GB, consider optimizing or pruning old documents
```

### Memory Issues

**Symptom**: Out of memory errors, system slowdown

**Solutions**:

1. **Set NumExpr threads**:
```bash
export NUMEXPR_MAX_THREADS=14
```

2. **Monitor memory**:
```bash
python check/health_checks.py
# Check "Memory Usage" section
```

3. **Reduce batch size**:
```python
# In data_ingestion.py
batch_size = 10  # Reduce from default 50
```

### API Rate Limiting

**Symptom**: `429 Too Many Requests` errors

**Solutions**:

1. **Use RobustHTTPClient** (handles retries automatically):
```python
from ice_data_ingestion.robust_client import RobustHTTPClient
client = RobustHTTPClient()  # Circuit breaker + retry + exponential backoff
```

2. **Check rate limits**:
```bash
# Review connector config
cat ice_data_ingestion/connectors/newsapi_connector.py | grep rate_limit
```

3. **Enable caching**:
```bash
ls storage/cache/
# Responses cached to avoid re-requesting
```

---

## 4. Data Quality Issues

### Missing Citations/Sources

**Symptom**: Query responses don't include source documents

**Diagnostics**:
```python
# Check if source attribution exists
result = ice.query("What is NVDA's rating?", mode="hybrid")
print(result.get('sources', []))
# Should show list of source documents

# Verify enhanced document format
with open('data/emails_samples/sample.eml', 'r') as f:
    content = f.read()
    assert '[SOURCE:' in content  # Should have SOURCE markers
```

**Validation**:
```bash
python tests/test_email_graph_integration.py
# Test 4 should verify source attribution
```

### Low Confidence Scores

**Symptom**: All entities have confidence <0.7

**Causes**:

1. **EntityExtractor not running**:
```python
# Check if EntityExtractor is enabled
# In data_ingestion.py, should see:
entities = self.entity_extractor.extract_entities(text)
```

2. **Wrong extraction method**:
```python
# DON'T: Let LightRAG extract everything (low confidence)
rag.insert(plain_text)

# DO: Use enhanced documents with EntityExtractor
enhanced_doc = create_enhanced_document(email, entities)
rag.insert(enhanced_doc)
```

3. **Validate confidence distribution**:
```python
# In ice_building_workflow.ipynb Cell 30.5
high_conf = [e for e in entities if e['confidence'] >= 0.80]
low_conf = [e for e in entities if e['confidence'] < 0.80]
print(f"High: {len(high_conf)}, Low: {len(low_conf)}")
# Should see >50% high confidence
```

### Inconsistent Entity Extraction

**Symptom**: Same ticker extracted differently across emails

**Solutions**:

1. **Use TickerValidator**:
```python
from imap_email_ingestion_pipeline.ticker_validator import TickerValidator
validator = TickerValidator()
filtered_entities = validator.filter_tickers(entities)
# Removes false positives: I, NOT, BUY, SELL, etc.
```

2. **Check inline metadata format**:
```python
# Correct format:
"[TICKER:NVDA|confidence:0.95]"

# Wrong formats (will be ignored):
"[TICKER:NVDA confidence:0.95]"  # Missing pipe
"TICKER:NVDA|confidence:0.95"     # Missing brackets
```

3. **Run validation tests**:
```bash
python tests/test_ticker_validator.py
# 30+ test cases verifying extraction consistency
```

---

## 5. Notebook Issues

### Cell Execution Errors

**Error**: `NameError: name 'ice' is not defined`

**Cause**: Cells executed out of order

**Solution**:
```bash
# Restart kernel and run all cells in order
# Kernel → Restart & Run All
```

### Graph Not Building

**Symptom**: Building workflow completes but graph is empty

**Diagnosis**:
```bash
# Check if documents were ingested
ls ice_lightrag/storage/
# Should see: vdb_chunks.json, vdb_entities.json, graph_chunk_entity_relation.graphml

# Check document count
python -c "from ice_lightrag import get_storage; print(get_storage().document_count())"
# Should show >0 documents
```

**Solution**:
```python
# In ice_building_workflow.ipynb Cell 22
REBUILD_GRAPH = True  # Force rebuild
```

### Visualization Not Showing

**Symptom**: Cell 31/32 doesn't display graph visualization

**Solution**:
```bash
# Install visualization dependencies
pip install matplotlib networkx pyvis

# Verify
python -c "import matplotlib, networkx, pyvis; print('OK')"

# Re-run visualization cells
```

---

## 6. Docling-Specific Issues

### Models Not Downloading

**Error**: `Model download failed` or `Connection timeout`

**Solution**:
```bash
# Use alternate download method
pip install --upgrade docling

# Manual model cache
mkdir -p ~/.cache/docling
cd ~/.cache/docling
# Download models from Docling GitHub releases

# Verify cache exists
ls -lh ~/.cache/docling/
# Should show ~500MB
```

### Table Extraction Failing

**Symptom**: Tables extracted but empty or garbled

**Diagnosis**:
```python
# Check extraction method
result = docling_processor.process_pdf(pdf_path)
print(result.get('extraction_method'))
# Should show 'docling', not 'pdfplumber' or 'pypdf2'

# Check table count
tables = result.get('extracted_data', {}).get('tables', [])
print(f"Tables extracted: {len(tables)}")
```

**Solution**:
```bash
# Ensure Docling is enabled
export USE_DOCLING_EMAIL=true
export USE_DOCLING_SEC=true
export USE_DOCLING_URLS=true

# Verify configuration
python -c "from config import ICEConfig; print(ICEConfig().get_docling_status())"
```

### Docling Processing Slow

**Symptom**: 30+ seconds per document

**Explanation**: Expected behavior (AI model inference)

**Optimization**:
```bash
# Process smaller batches
# In data_ingestion.py:
docling_batch_size = 5  # Reduce from default 10

# Use pdfplumber for documents without tables
export USE_DOCLING_EMAIL=false  # Faster, lower accuracy
```

---

## 7. Crawl4AI-Specific Issues

### Browser Not Installing

**Error**: `Playwright browser not found`

**Solution**:
```bash
pip install playwright
playwright install chromium

# Verify
playwright --help
```

### Tier 3-5 URLs Still Failing

**Diagnosis**:
```bash
# Check tier classification
grep "Classified URL" logs/link_processor.log
# Should show tier assignments

# Check if Crawl4AI is being used
grep "fetch_with_crawl4ai" logs/link_processor.log
```

**Solution**:
```bash
# Enable Crawl4AI
export USE_CRAWL4AI_LINKS=true

# Increase timeout for slow sites
export CRAWL4AI_TIMEOUT=120  # 2 minutes

# Test specific URL
python tmp/tmp_crawl4ai_test.py
```

### Rate Limiting from Servers

**Symptom**: `403 Forbidden` or `429 Too Many Requests`

**Solution**:
```bash
# Reduce concurrency
export URL_CONCURRENT_DOWNLOADS=1

# Increase delay between requests
export URL_RATE_LIMIT_DELAY=3.0  # 3 seconds

# Clear cache and retry
rm -rf data/link_cache/*
```

---

## 8. Debugging Commands Reference

### System Health Check
```bash
python check/health_checks.py
# Checks: API keys, imports, storage, memory
```

### Validate All Data Sources
```bash
jupyter notebook sandbox/python_notebook/ice_data_sources_demo_simple.ipynb
# Tests: API connections, MCP servers, email pipeline
```

### Test Email Integration
```bash
python tests/test_email_graph_integration.py
# Tests: EntityExtractor, GraphBuilder, enhanced documents
```

### LightRAG Quick Test
```bash
python src/ice_lightrag/quick_test.py
# Tests: Basic insert, query, storage
```

### Enable Debug Logging
```bash
export ICE_DEBUG=1
python updated_architectures/implementation/ice_simplified.py
# Verbose logging to console
```

### Check Logs
```bash
# Session start log
cat logs/session_start.json | python -m json.tool

# Pre-tool use log
cat logs/pre_tool_use.json | python -m json.tool

# User prompt submit log
cat logs/user_prompt_submit.json | python -m json.tool
```

### Test Specific Components

```bash
# Test SecureConfig
python tests/test_secure_config.py

# Test EntityExtractor
python tests/test_entity_extraction.py

# Test TickerValidator
python tests/test_ticker_validator.py

# Test dual-layer architecture
python tests/test_dual_layer_ratings.py
python tests/test_dual_layer_metrics.py
```

---

## 9. Advanced Debugging

### LightRAG Storage Investigation

```bash
# Check storage structure
ls -lh ice_lightrag/storage/

# Inspect vector DB
python -c "import json; print(json.load(open('ice_lightrag/storage/vdb_entities.json'))[:3])"

# Check graph structure
pip install networkx
python -c "import networkx as nx; G = nx.read_graphml('ice_lightrag/storage/graph_chunk_entity_relation.graphml'); print(f'Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}')"
```

### Email Pipeline Debugging

```bash
# Check email samples
ls -lh data/emails_samples/

# Test single email processing
python tmp/tmp_email_test.py

# Check enhanced document format
cat data/emails_samples/sample.eml | grep "\[TICKER:"
# Should show inline metadata markup
```

### Graph Statistics

```python
# In ice_building_workflow.ipynb
# Cell 28: Data source breakdown
# Cell 29: Entity type distribution
# Cell 30: Relationship analysis
```

---

## 10. When All Else Fails

### Nuclear Options (Last Resort)

1. **Complete storage reset**:
```bash
rm -rf ice_lightrag/storage/*
rm -rf data/attachments/*
rm -rf data/link_cache/*
rm -rf data/sec_filings/*
# Then rebuild graph from scratch
```

2. **Recreate Python environment**:
```bash
conda deactivate
conda remove -n ice_env --all
conda create -n ice_env python=3.8
conda activate ice_env
pip install -r requirements.txt
```

3. **Check for corrupted files**:
```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

### Get Help

1. **Check Serena memories** for specific issues:
```bash
# List all troubleshooting memories
ls .serena/memories/*troubleshooting*
ls .serena/memories/*bug*
ls .serena/memories/*fix*
```

2. **Review PROJECT_CHANGELOG.md** for recent changes that may have introduced issues

3. **Check GitHub issues** (if applicable)

---

## 📚 Related Documentation

- **CLAUDE.md** - Core daily workflows (parent document)
- **CLAUDE_PATTERNS.md** - ICE coding patterns
- **CLAUDE_INTEGRATIONS.md** - Docling and Crawl4AI details
- **ICE_ARCHITECTURE_IMPLEMENTATION_PLAN.md** - UDMA architecture
- **Serena Memory**: `troubleshooting_comprehensive_guide_2025_10_18` (this document's source)

---

**Last Updated**: 2025-11-05
**Maintained By**: Claude Code + Roy Yeo
**Version**: 1.0
