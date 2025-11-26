# Real-Time Monitor Integration Guide

**Created**: 2025-11-19
**Purpose**: Document integration points and usage of the real-time monitoring daemon
**Status**: Phase 2.7A Day 5-6 COMPLETE ✅

## Overview

The Real-Time Monitor provides continuous market intelligence gathering for hedge fund PMs through:
- NewsAPI polling (5-minute intervals)
- SEC EDGAR polling (15-minute intervals)
- Priority-based alert classification
- Multi-channel alert delivery
- Incremental knowledge graph updates

## Architecture Components

### 1. Core Classes

#### RealTimeMonitor (`src/ice_core/real_time_monitor.py`)
- Main orchestrator
- Manages pollers, classifier, and delivery
- Configuration-driven design

#### NewsAPIPoller
- 5-minute interval polling
- Deduplication of seen articles
- Integration with DataIngester

#### SECEdgarPoller
- 15-minute interval polling
- Tracks critical filing types (8-K, 10-Q, 10-K)
- Automatic priority elevation for 8-K filings

#### AlertClassifier
- 4-tier priority system (CRITICAL/HIGH/MEDIUM/LOW)
- Portfolio-aware classification
- Sector exposure sensitivity

#### AlertDelivery
- Multi-channel support (Email/Slack/Webhook/Log)
- Async queue-based delivery
- Channel selection by priority

### 2. Alert Priority Logic

```python
CRITICAL (🚨):
- Portfolio holdings with negative impact >5%
- Portfolio holdings with positive impact >10%
- Major earnings miss/beat for holdings

HIGH (⚠️):
- Any portfolio event
- Sector exposure >10% affected
- 8-K SEC filings

MEDIUM (📊):
- Regulatory actions
- Management changes
- Lawsuits

LOW (ℹ️):
- General market intelligence
- Industry trends
```

## Integration Points

### 1. With EventExtractor
```python
# In _process_news_article()
events = self.event_extractor.extract_events(
    text=article_text,
    ticker=ticker,
    document_date=article_date
)
```

### 2. With SignalStore
```python
# Persistent storage of events
self.signal_store.add_signal(
    signal_type='event',
    ticker=event.ticker,
    data={event_details},
    source=source_url
)
```

### 3. With DataIngester
```python
# News fetching
articles = self.data_ingestion.fetch_company_news_concurrent(
    symbol=ticker,
    limit=10
)

# SEC filings
filings = self.data_ingestion.fetch_sec_filings(
    symbol=ticker,
    limit=5
)
```

## Configuration

### monitor.json Structure
```json
{
  "portfolio_tickers": ["NVDA", "AAPL", "MSFT"],
  "sector_exposures": {
    "AI": 0.35,
    "Cloud": 0.25
  },
  "news_interval": 300,    // 5 minutes
  "sec_interval": 900,     // 15 minutes
  "delivery": {
    "email_enabled": false,
    "slack_enabled": false,
    "log_enabled": true
  }
}
```

## Usage

### Start Monitor
```bash
# Production mode (daemon)
python scripts/run_monitor.py start

# Test mode (foreground with debug)
python scripts/run_monitor.py test

# Check status
python scripts/run_monitor.py status

# Stop daemon
python scripts/run_monitor.py stop
```

### Programmatic Usage
```python
import asyncio
from src.ice_core.real_time_monitor import RealTimeMonitor

# Create and configure
monitor = RealTimeMonitor('config/monitor.json')

# Run
asyncio.run(monitor.start())
```

## Testing

### Test Coverage (100% - 18/18 tests passing)

1. **NewsAPIPoller Tests**
   - Polling interval enforcement ✅
   - Article deduplication ✅
   - Ticker context addition ✅

2. **SECEdgarPoller Tests**
   - 15-minute interval enforcement ✅
   - Filing deduplication ✅

3. **AlertClassifier Tests**
   - CRITICAL priority for portfolio negatives ✅
   - CRITICAL priority for portfolio positives ✅
   - HIGH priority for portfolio events ✅
   - HIGH priority for sector exposure ✅
   - MEDIUM priority for regulatory ✅
   - LOW priority for general events ✅
   - Delivery channel selection ✅

4. **AlertDelivery Tests**
   - Queue management ✅
   - Thread lifecycle ✅

5. **RealTimeMonitor Tests**
   - Component initialization ✅
   - Configuration loading ✅
   - News processing ✅
   - Signal storage ✅

### Run Tests
```bash
python tests/test_real_time_monitor.py
```

## Integration Checklist

- [x] EventExtractor integration
- [x] SignalStore persistence
- [x] DataIngester news/SEC fetching
- [x] Alert classification logic
- [x] Multi-channel delivery framework
- [x] Configuration management
- [x] Launcher script
- [x] Comprehensive tests (100% pass)
- [ ] Production deployment config
- [ ] Slack webhook setup
- [ ] Email SMTP configuration
- [ ] Monitor dashboard (future)

## Key Files

| File | Purpose |
|------|---------|
| `src/ice_core/real_time_monitor.py` | Core monitoring daemon (660 lines) |
| `tests/test_real_time_monitor.py` | Comprehensive test suite (380 lines) |
| `config/monitor.json` | Configuration template |
| `scripts/run_monitor.py` | Launcher/management script |

## Next Steps

1. **Phase 2.7A Day 7**: Integrate FinBERT sentiment analysis
2. **Phase 2.7A Day 8-9**: Validate F1 scores and alert precision
3. **Phase 2.7A Day 10**: Update ARCHITECTURE.md

## Performance Characteristics

- **Memory**: ~100MB baseline + cache growth
- **CPU**: <5% idle, spikes during processing
- **Network**: ~10 requests/minute at peak
- **Storage**: ~1MB/day for alerts and signals

## Security Considerations

- API keys via environment variables
- No credentials in config files
- Webhook URLs validated
- Email authentication required
- Signal store encryption (future)

## Monitoring the Monitor

```bash
# Check logs
tail -f logs/monitor.log

# Check alerts
tail -f logs/ice_alerts.log

# System resources
ps aux | grep run_monitor.py

# Database growth
du -h data/signal_store/signal_store.db
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure PYTHONPATH includes project root
2. **API rate limits**: Adjust polling intervals
3. **Memory growth**: Implement cache cleanup (see config)
4. **Stale PID file**: Delete `logs/monitor.pid` and restart

### Debug Mode

```bash
export ICE_DEBUG=1
python scripts/run_monitor.py test
```

---

**Status**: Phase 2.7A Day 5-6 successfully completed with real-time monitoring daemon operational and tested at 100% success rate.