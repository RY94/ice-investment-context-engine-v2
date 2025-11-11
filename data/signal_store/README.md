# Signal Store - Structured Investment Intelligence Storage

**Location**: `data/signal_store/`
**Purpose**: SQLite database for fast (<1s) structured queries on investment intelligence
**Architecture**: Dual-layer (Signal Store + LightRAG) for complementary query patterns

---

## What is Signal Store?

Signal Store is a SQLite-based storage layer that complements LightRAG by enabling fast structured queries:

- **Signal Store** (<1s): "What/Which/Show" queries with numerical filters
  - Examples: "What's NVDA's latest rating?", "Show tickers where margin > 50%"

- **LightRAG** (~12s): "Why/How/Explain" queries requiring semantic reasoning
  - Examples: "Why did Goldman upgrade NVDA?", "How does China risk impact NVDA?"

## Database Schema

The Signal Store contains 5 tables:

### 1. ratings
Analyst ratings (BUY/SELL/HOLD) with confidence scores and source attribution.

### 2. price_targets
Analyst price targets with firm/analyst attribution.

### 3. metrics
Financial metrics from tables (revenue, margins, EPS, etc.) with temporal tracking.

### 4. entities
Investment entities (companies, analysts, firms) with confidence scores.

### 5. relationships
Typed relationships between entities for graph queries via SQL JOIN.

## Usage

Signal Store is automatically initialized when ICE starts (if `USE_SIGNAL_STORE=true`).

### Environment Variables

```bash
# Enable/disable Signal Store (default: true)
export USE_SIGNAL_STORE=true

# Custom database location (default: data/signal_store/signal_store.db)
export SIGNAL_STORE_PATH=/custom/path/signal_store.db

# Query timeout in milliseconds (default: 5000ms)
export SIGNAL_STORE_TIMEOUT=10000

# Debug mode (default: false)
export SIGNAL_STORE_DEBUG=true
```

### Programmatic Access

```python
from updated_architectures.implementation.signal_store import SignalStore

# Initialize
store = SignalStore()

# Insert rating
store.insert_rating(
    ticker='NVDA',
    rating='BUY',
    timestamp='2024-03-15T10:30:00Z',
    source_document_id='email_12345',
    analyst='John Doe',
    firm='Goldman Sachs',
    confidence=0.87
)

# Query latest rating
latest = store.get_latest_rating('NVDA')
print(latest)  # {'ticker': 'NVDA', 'rating': 'BUY', ...}

# Close connection
store.close()
```

## Data Flow

```
Email/SEC/API
   ↓
EntityExtractor / TableEntityExtractor
   ↓
Structured Entities Dict
   ↓
DUAL WRITE (transaction-based)
   ├─→ Signal Store (SQL INSERT)
   └─→ LightRAG (enhanced document with inline tags)
```

## Performance

- **Indexed queries**: <100ms for single-ticker lookups
- **Complex joins**: <1s for multi-entity relationship queries
- **Aggregations**: <500ms for portfolio-level calculations

## Maintenance

### Backup

```bash
# Backup database
cp data/signal_store/signal_store.db data/signal_store/signal_store_backup_$(date +%Y%m%d).db
```

### Reset

```bash
# Delete database (will be recreated on next ICE start)
rm data/signal_store/signal_store.db
```

### Inspect

```bash
# Open database with SQLite CLI
sqlite3 data/signal_store/signal_store.db

# Example queries
SELECT COUNT(*) FROM ratings;
SELECT * FROM ratings WHERE ticker = 'NVDA' ORDER BY timestamp DESC LIMIT 5;
```

## Architecture Decisions

### Why SQLite?

1. **Zero-config**: Embedded, no server setup
2. **ACID guarantees**: Transaction-based dual-write
3. **Battle-tested**: 40+ years, in Python stdlib
4. **Fast**: Indexed queries <100ms
5. **Portable**: Single file database

### Why Dual-Layer?

Signal Store and LightRAG serve **different architectural purposes**:

| Query Type | Best Layer | Latency | Why |
|-----------|------------|---------|-----|
| "What's NVDA's latest rating?" | Signal Store | <1s | Exact lookup, indexed query |
| "Why did Goldman upgrade NVDA?" | LightRAG | ~12s | Semantic reasoning, context synthesis |
| "Show tickers where margin > 50%" | Signal Store | <100ms | SQL WHERE clause, aggregation |
| "How does China risk impact NVDA?" | LightRAG | ~12s | Multi-hop graph traversal |

They're **complementary**, not alternatives!

## Related Files

- `updated_architectures/implementation/signal_store.py` - SQLite wrapper
- `updated_architectures/implementation/query_router.py` - Smart routing
- `updated_architectures/implementation/config.py` - Configuration
- `tests/test_signal_store.py` - Unit tests
- `tests/test_dual_layer_integration.py` - Integration tests

---

**Last Updated**: 2025-10-26
**Status**: Phase 1 implementation (ratings table operational)
