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
   - Graph metadata storage

8. **PipelineOrchestrator** (`pipeline_orchestrator.py`)
   - Main controller with parallel processing
   - Health monitoring and error recovery
   - Scheduling and continuous operation

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