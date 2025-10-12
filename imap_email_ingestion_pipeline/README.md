# Email Ingestion Pipeline for ICE Investment Context Engine

A production-ready email ingestion pipeline that transforms investment emails into structured knowledge for the ICE AI system.

## Overview

This pipeline processes emails from financial sources (brokers, research firms, internal communications) and extracts investment-relevant information including:

- **Tickers & Companies**: Mentioned stocks and companies with confidence scores
- **Financial Metrics**: Price targets, earnings, ratios, recommendations  
- **Attachments**: PDFs, Excel models, presentations with OCR processing
- **Entities**: People, dates, topics, sentiment analysis
- **Relationships**: Knowledge graph edges connecting all extracted information

All processed data integrates seamlessly with the ICE LightRAG system for advanced query and analysis capabilities.

## Architecture

### Core Components

1. **StateManager** (`state_manager.py`)
   - SQLite-based state tracking and deduplication
   - Metrics recording and performance monitoring
   - Incremental processing with UID tracking

2. **ResilientIMAPConnector** (`imap_connector.py`) 
   - Robust IMAP connection with auto-reconnection
   - Email threading and priority detection
   - Batch fetching with incremental sync

3. **AttachmentProcessor** (`attachment_processor.py`)
   - Multi-format document processing (PDF, Excel, Word, PowerPoint)
   - OCR fallback for scanned documents
   - Intelligent text extraction with confidence scoring

4. **OCREngine** (`ocr_engine.py`)
   - Multi-engine OCR (PaddleOCR, EasyOCR, Tesseract)
   - Automatic fallback and confidence comparison
   - Financial document optimization

5. **EntityExtractor** (`entity_extractor.py`)
   - Investment entity recognition (tickers, companies, people)
   - Financial metrics extraction (price targets, earnings)
   - Sentiment analysis and topic classification

6. **GraphBuilder** (`graph_builder.py`)
   - Knowledge graph structure creation
   - Timestamped edges with source attribution  
   - Relationship mapping between all entities

7. **ICEIntegrator** (`ice_integrator.py`)
   - LightRAG system integration
   - Batch document processing
   - Enhanced document creation with inline markup

8. **EnhancedDocCreator** (`enhanced_doc_creator.py`) 🆕 **Week 1.5 Addition**
   - Inline metadata markup generation
   - Confidence score preservation
   - Source attribution and traceability

9. **PipelineOrchestrator** (`pipeline_orchestrator.py`)
   - Main controller with parallel processing
   - Health monitoring and error recovery
   - Scheduling and continuous operation

### Enhanced Documents (Week 1.5)

The pipeline now creates **enhanced documents** that preserve EntityExtractor precision while using a single LightRAG graph. This solves the dual-graph problem by injecting custom extractions as structured markup within document text.

#### Enhanced Document Format

Enhanced documents include inline markup that preserves all extraction metadata:

```
[SOURCE_EMAIL:12345|sender:analyst@gs.com|date:2024-01-15|subject:NVDA Upgrade]
[PRIORITY:HIGH|confidence:0.85]

[TICKER:NVDA|confidence:0.95] [RATING:BUY|confidence:0.87]
[PRICE_TARGET:500|ticker:NVDA|currency:USD|confidence:0.92]
[ANALYST:John Doe|firm:Goldman Sachs|confidence:0.88]

=== ORIGINAL EMAIL CONTENT ===

We are upgrading NVIDIA (NVDA) to BUY with $500 price target.
Strong data center growth driven by AI demand...
```

#### Key Features

- **Confidence Preservation**: All entities include confidence scores (0.0-1.0)
- **Source Traceability**: Every document traces to email UID, sender, date
- **Threshold Filtering**: Only entities >0.5 confidence included
- **Special Character Handling**: Pipes (|), brackets ([]) automatically escaped
- **Size Management**: Documents truncated at 50KB with warnings

#### Usage

```python
from enhanced_doc_creator import create_enhanced_document

# Create enhanced document
enhanced_doc = create_enhanced_document(
    email_data={'uid': '123', 'from': 'analyst@gs.com', 'body': '...'},
    entities={'tickers': [{'ticker': 'NVDA', 'confidence': 0.95}]},
    graph_data={}  # Optional
)

# Or use via ICEEmailIntegrator (default: enhanced documents enabled)
integrator = ICEEmailIntegrator()
result = integrator.integrate_email_data(
    email_data=email_data,
    extracted_entities=entities,
    graph_data=graph_data,
    use_enhanced=True,       # Enhanced documents (default)
    save_graph_json=False    # No graph JSON waste (default)
)
```

#### Benefits

✅ **Single Query Interface**: All queries through LightRAG (no dual systems)
✅ **Cost Optimization**: No duplicate LLM calls (EntityExtractor uses regex + spaCy)
✅ **Precision Preservation**: Confidence scores embedded in markup
✅ **Fast MVP**: 2-3 weeks saved vs dual-layer architecture
✅ **Backward Compatible**: Old `_create_comprehensive_document()` still available

#### Testing

```bash
# Unit tests (27 tests)
cd tests && pytest test_enhanced_documents.py -v

# Integration tests + Week 3 metrics (7 tests)
cd .. && pytest tests/test_email_graph_integration.py -v
```

**Week 3 Metrics - ALL PASSED:**
- ✅ Ticker extraction accuracy: >95%
- ✅ Confidence preservation: Validated
- ✅ Query performance: <2s
- ✅ Source attribution: Traceable
- ✅ Cost optimization: No duplicate LLM calls

## Installation

### System Requirements
- Python 3.8+
- 4GB+ RAM (for OCR processing)
- 10GB+ storage for email attachments

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Install system dependencies (macOS)
brew install tesseract

# Install system dependencies (Ubuntu)
sudo apt install tesseract-ocr python3-magic
```

### OCR Setup
```bash
# For best accuracy, install PaddleOCR
pip install paddlepaddle paddleocr

# Alternative: EasyOCR
pip install easyocr

# Fallback: Tesseract (already installed above)
pip install pytesseract
```

## Configuration

### Email Credentials
Create environment variables or config file:
```bash
export EMAIL_ADDRESS="your-email@domain.com"  
export EMAIL_PASSWORD="your-app-password"
```

### Pipeline Config
Edit `config/pipeline_config.json`:
```json
{
  "email": {
    "server": "outlook.office365.com",
    "port": 993,
    "folder": "INBOX",
    "batch_size": 10
  },
  "processing": {
    "max_workers": 4,
    "timeout_seconds": 300
  },
  "scheduling": {
    "run_interval_minutes": 15
  }
}
```

## Usage

### Single Run
Process current emails once:
```bash
python pipeline_orchestrator.py \
  --email your@email.com \
  --password your-password \
  --mode single
```

### Continuous Operation  
Run pipeline continuously with scheduling:
```bash
python pipeline_orchestrator.py \
  --email your@email.com \
  --password your-password \
  --mode continuous
```

### Custom Configuration
```bash
python pipeline_orchestrator.py \
  --config ./custom_config.json \
  --email your@email.com \
  --password your-password \
  --mode continuous
```

## Data Flow

```
IMAP Email Fetch
    ↓
Priority Classification → [URGENT|RESEARCH|PORTFOLIO|ADMIN]
    ↓
State Check (Skip if processed)
    ↓
Email Content Processing
    ├── Body Text → Entity Extraction
    └── Attachments → Format Detection
         ├── PDF → Native extraction → OCR fallback
         ├── Excel → Formula + data extraction  
         ├── Word → Text + table extraction
         ├── PowerPoint → Slide + notes extraction
         └── Images → Multi-engine OCR
              ↓
         Entity & Relationship Extraction
              ↓
         Knowledge Graph Construction
              ↓
         ICE LightRAG Integration
              ↓
         State Update (Mark completed)
```

## Features

### Intelligence Features
- **Smart Deduplication**: Hash-based attachment deduplication
- **Priority Detection**: Urgent emails processed first
- **Thread Tracking**: Email conversation context
- **Confidence Scoring**: Quality metrics for all extractions
- **Incremental Sync**: Only process new emails

### Reliability Features  
- **Error Recovery**: Automatic retries with exponential backoff
- **Health Monitoring**: Component status checks
- **Graceful Shutdown**: Signal handling for clean stops
- **State Persistence**: Resume processing after crashes
- **Comprehensive Logging**: Detailed operation logs

### Performance Features
- **Parallel Processing**: Multi-threaded email processing
- **Batch Operations**: Efficient database and API calls
- **Smart Caching**: Avoid reprocessing identical content
- **Resource Management**: Memory and disk usage optimization

## Testing

### Run All Tests
```bash
python test_pipeline.py
```

### Component-Specific Tests
```bash
# Test specific component
python test_pipeline.py --component entity
python test_pipeline.py --component attachment
python test_pipeline.py --component graph
```

### Integration Test
```bash
python test_pipeline.py --integration
```

## Monitoring

### Pipeline Status
```python
from pipeline_orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()
status = orchestrator.get_pipeline_status()
print(json.dumps(status, indent=2))
```

### Key Metrics
- **Processing Rate**: Emails per minute
- **Error Rate**: Failed/total processing ratio  
- **OCR Confidence**: Average OCR accuracy
- **Storage Usage**: Attachment storage utilization
- **Component Health**: Individual component status

### Log Files
- `./data/logs/pipeline.log` - Main pipeline operations
- `./data/logs/errors.log` - Error details and stack traces
- `./data/state.db` - Processing state and metrics (SQLite)

## Integration with ICE

### Query Processed Emails
```python
from ice_integrator import ICEEmailIntegrator

integrator = ICEEmailIntegrator()
result = integrator.query_email_content(
    "What did analysts say about NVIDIA last week?",
    mode="hybrid"
)
print(result)
```

### Graph Data Access
Knowledge graph data is stored in:
- `./ice_lightrag/storage/graphs/` - Individual email graphs (JSON)
- `./ice_lightrag/storage/` - LightRAG document storage

## Performance Optimization

### For High Volume (100+ emails/day)
```json
{
  "processing": {
    "max_workers": 8,
    "use_process_pool": true,
    "batch_size": 20
  },
  "email": {
    "max_emails_per_run": 50
  }
}
```

### For Limited Resources
```json
{
  "processing": {
    "max_workers": 2,
    "use_process_pool": false,
    "batch_size": 5
  },
  "storage": {
    "max_attachment_size_mb": 50
  }
}
```

## Troubleshooting

### Common Issues

**IMAP Connection Failed**
- Check email/password credentials
- Verify server settings (outlook.office365.com:993)
- Enable app passwords if using 2FA

**OCR Not Working**
- Install PaddleOCR: `pip install paddlepaddle paddleocr`
- Check system dependencies: `brew install tesseract`
- Verify image preprocessing pipeline

**High Memory Usage**
- Reduce `max_workers` in config
- Enable `cleanup_days` for automatic cleanup
- Limit `max_attachment_size_mb`

**Slow Processing**
- Enable parallel processing: `use_process_pool: true`
- Increase `max_workers` if CPU available
- Optimize OCR settings for speed vs accuracy

### Debug Mode
```bash
python pipeline_orchestrator.py \
  --mode single \
  --email your@email.com \
  --password your-password \
  --log-level DEBUG
```

### Health Check
```python
from pipeline_orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()
orchestrator.initialize_email_connection(email, password)

# Perform health check
healthy = orchestrator._perform_health_check()
print(f"Pipeline health: {'OK' if healthy else 'ISSUES'}")

# Get detailed status
status = orchestrator.get_pipeline_status()
print(json.dumps(status, indent=2))
```

## Security Considerations

- **Credentials**: Use app passwords, not main email passwords
- **Data Privacy**: All processing happens locally
- **Audit Trail**: Complete processing history in state database  
- **Access Control**: Restrict file permissions on data directories
- **Compliance**: Configurable data retention policies

## License

This pipeline is part of the ICE Investment Context Engine project.

## Support

For issues and questions:
1. Check logs in `./data/logs/`  
2. Run health check and integration tests
3. Review configuration settings
4. Consult troubleshooting section above