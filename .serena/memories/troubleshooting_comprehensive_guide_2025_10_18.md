# ICE Troubleshooting Comprehensive Guide

**Location**: CLAUDE.md Section 7 (migrated to Serena 2025-10-18)
**Purpose**: Complete troubleshooting reference for common ICE development issues
**Related Files**: `CLAUDE.md`, setup scripts, configuration files, test files

---

## 1. Environment Setup Issues

### API Key Not Found

**Error**: OpenAI API key not set

**Solution**:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

**Verify**:
```bash
python test_api_key.py
```

### LightRAG Import Error

**Error**: No module named 'lightrag'

**Solution**:
```bash
cd src/ice_lightrag && python setup.py && cd ../..
```

**Verify**:
```bash
python src/ice_lightrag/test_basic.py
```

### Jupyter Kernel Issues

**Error**: Kernel not found or crashes

**Solution**: Install ipykernel and register kernel
```bash
pip install ipykernel
python -m ipykernel install --user --name=ice_env
```

**Usage**: In notebook: Kernel → Change Kernel → ice_env

---

## 2. Integration Errors

### Module Import Failures

**Error**: Cannot import from ice_data_ingestion

**Check PYTHONPATH**:
```bash
export PYTHONPATH="${PYTHONPATH}:."
```

**Verify**:
```python
python -c "from ice_data_ingestion import robust_client; print('OK')"
```

### Email Connector Not Found

**Error**: No module named 'imap_email_ingestion_pipeline'

**Check file location**:
```bash
ls imap_email_ingestion_pipeline/email_connector.py
```

**Verify**:
```python
python -c "from imap_email_ingestion_pipeline.email_connector import EmailConnector; print('OK')"
```

### LightRAG Storage Corruption

**Symptom**: LightRAG storage becomes corrupted

**Solution**:
```bash
rm -rf ice_lightrag/storage/*
# Re-run building workflow to recreate graph
jupyter notebook ice_building_workflow.ipynb
```

---

## 3. Performance Issues

### Slow Query Response

**Causes & Solutions**:
- Check hop depth (limit to 3 max)
- Use `local` mode for simple lookups instead of `hybrid`
- Reduce confidence threshold if too restrictive
- Check if LightRAG storage is too large (>1GB may need optimization)

### Memory Issues

**Set NumExpr threads for large graphs**:
```bash
export NUMEXPR_MAX_THREADS=14
```

**Monitor memory usage**:
```bash
python check/health_checks.py
```

### API Rate Limiting

**Solutions**:
- Use `robust_client` with circuit breaker (automatically handles retries)
- Check rate limits in connector config
- Consider caching responses in `storage/cache/`

---

## 4. Data Quality Issues

### Missing Citations/Sources

**Diagnostics**:
- Verify source attribution in enhanced documents
- Check that `source_document_id` is included in all edges

**Validation**:
```bash
python tests/test_email_graph_integration.py
```

### Low Confidence Scores

**Causes**:
- Review entity extraction accuracy
- Check if enhanced document format is correct
- Validate extraction method against PIVF benchmarks

### Inconsistent Entity Extraction

**Solutions**:
- Use production `EntityExtractor` from email pipeline
- Verify confidence thresholds (should be >0.7 for high precision)
- Check inline metadata format: `[TICKER:NVDA|confidence:0.95]`

---

## 5. Debug Commands Reference

### System Health Check
```bash
python check/health_checks.py
```

### Validate All Data Sources
```bash
jupyter notebook sandbox/python_notebook/ice_data_sources_demo_simple.ipynb
```

### Test Email Integration
```bash
python tests/test_email_graph_integration.py
```

### LightRAG Quick Test
```bash
python src/ice_lightrag/quick_test.py
```

### Enable Debug Logging
```bash
export ICE_DEBUG=1
python updated_architectures/implementation/ice_simplified.py
```

### Check Logs
```bash
cat logs/session_start.json | python -m json.tool
cat logs/pre_tool_use.json | python -m json.tool
```

---

## Quick Reference Table

| Issue Type | First Action | Validation Command |
|------------|--------------|-------------------|
| API Key | `export OPENAI_API_KEY=...` | `python test_api_key.py` |
| Import Error | `export PYTHONPATH=.` | `python -c "import [module]"` |
| LightRAG Corrupted | `rm -rf ice_lightrag/storage/*` | Run building workflow |
| Slow Queries | Check hop depth, use `local` mode | Test with different modes |
| Memory Issues | `export NUMEXPR_MAX_THREADS=14` | `python check/health_checks.py` |

