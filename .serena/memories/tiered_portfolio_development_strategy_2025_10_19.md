# Tiered Portfolio Development Strategy

**Date**: 2025-10-19
**Purpose**: Enable faster development iterations with guaranteed 3-source coverage
**Context**: 178-doc graph takes ~102 minutes to build, blocking rapid dev cycles

## Problem Statement

**Challenge**: `ice_building_workflow.ipynb` processes 178 documents (~102 minutes) during every graph rebuild, making iterative development slow.

**Requirement**: Reduce build time for development WITHOUT sacrificing data source diversity (Email + API/MCP + SEC).

## Solution: Dual-Strategy Approach

### Strategy A: Skip Graph Building (EXISTING)

**Mechanism**: Set `REBUILD_GRAPH = False` in Cell 22

**When to use**:
- Testing query features (90% of development work)
- Analysis workflow modifications
- Query mode tuning
- Validation testing

**Advantages**:
- ⚡ Instant (0 minutes)
- ✅ Full 178-doc graph with all relationships
- ✅ Complete 3-source coverage

**Implementation**: Already exists in notebook (line 1765)

### Strategy B: Tiered Portfolio System (NEW)

**Mechanism**: Portfolio size selector with source-aware limits

**When to use**:
- Testing ingestion changes (10% of development work)
- Data source modifications
- Entity extraction tuning
- Pipeline debugging

**Advantages**:
- ✅ ALL 3 sources guaranteed in every tier
- ⏱️ Configurable speed/coverage tradeoff
- ✅ Maintains architectural integrity

## Implementation Details

### 1. Code Changes

**File**: `ice_simplified.py:876` (2 edits)

**Change 1**: Add parameters to `ingest_portfolio_data()`
```python
def ingest_portfolio_data(self, holdings: List[str], 
                         email_limit: int = 71, 
                         news_limit: int = 5, 
                         sec_limit: int = 3) -> Dict[str, Any]:
```

**Change 2**: Pass parameters to `fetch_comprehensive_data()` (line 911)
```python
documents = self.ingester.fetch_comprehensive_data(
    [symbol], 
    news_limit=news_limit, 
    email_limit=email_limit, 
    sec_limit=sec_limit
)
```

**File**: `ice_building_workflow.ipynb` (1 new cell)

**Change**: Added portfolio selector cell before ingestion (position 23)

### 2. Portfolio Tier Definitions

```python
portfolios = {
    'tiny': {
        'holdings': ['NVDA'],               # 1 ticker
        'email_limit': 10,                  # 10 emails (14% of corpus)
        'news_limit': 2,                    # 2 news/ticker
        'sec_limit': 1,                     # 1 filing/ticker
        'estimated_docs': 16,               # Email(10) + News(2) + Fin(3) + SEC(1)
        'estimated_time': '~10 min'
    },
    'small': {
        'holdings': ['NVDA', 'AMD'],        # 2 tickers
        'email_limit': 25,                  # 25 emails (35% of corpus)
        'news_limit': 3,                    # 3 news/ticker = 6 total
        'sec_limit': 2,                     # 2 filings/ticker = 4 total
        'estimated_docs': 41,               # Email(25) + News(6) + Fin(6) + SEC(4)
        'estimated_time': '~25 min'
    },
    'medium': {
        'holdings': ['NVDA', 'AMD', 'TSMC'], # 3 tickers
        'email_limit': 50,                  # 50 emails (70% of corpus)
        'news_limit': 4,                    # 4 news/ticker = 12 total
        'sec_limit': 3,                     # 3 filings/ticker = 9 total
        'estimated_docs': 80,               # Email(50) + News(12) + Fin(9) + SEC(9)
        'estimated_time': '~48 min'
    },
    'full': {
        'holdings': ['NVDA', 'TSMC', 'AMD', 'ASML'], # 4 tickers
        'email_limit': 71,                  # All 71 emails (100% of corpus)
        'news_limit': 5,                    # 5 news/ticker = 20 total
        'sec_limit': 3,                     # 3 filings/ticker = 12 total
        'estimated_docs': 178,              # Email(71) + News(20) + Fin(12) + SEC(12)
        'estimated_time': '~102 min'
    }
}
```

### 3. Source Coverage Guarantee

**Critical Design Principle**: Every tier maintains representation from ALL 3 sources:

| Tier | Email | API/News | API/Financials | SEC | **Coverage** |
|------|-------|----------|----------------|-----|--------------|
| tiny | 10 docs | 2 docs | 3 docs | 1 doc | ✅ ALL 3 |
| small | 25 docs | 6 docs | 6 docs | 4 docs | ✅ ALL 3 |
| medium | 50 docs | 12 docs | 9 docs | 9 docs | ✅ ALL 3 |
| full | 71 docs | 20 docs | 12 docs | 12 docs | ✅ ALL 3 |

## Architecture Considerations

### Data Source Types

**SOURCE 1: Email** (Shared corpus, called once)
```python
email_docs = fetch_email_documents(tickers=None, limit=email_limit)
```
- NOT scoped to portfolio holdings
- Uses `tickers=None` for "Trust the Graph" strategy
- Enables cross-company relationship discovery
- Sample: First N files from `data/emails_samples/`

**SOURCE 2: API** (Per-ticker, multiple calls)
```python
for symbol in holdings:
    news_docs = fetch_company_news(symbol, limit=news_limit)
    financial_docs = fetch_company_financials(symbol)  # 3 APIs: FMP, Alpha Vantage, Polygon
```
- Scoped to portfolio holdings
- News: Top N most recent articles per ticker
- Financials: 3 documents per ticker (one from each API)

**SOURCE 3: SEC** (Per-ticker, regulatory)
```python
for symbol in holdings:
    sec_docs = fetch_sec_filings(symbol, limit=sec_limit)
```
- Scoped to portfolio holdings
- Top N most recent filings (10-K, 10-Q, 8-K)

### Trade-offs by Tier

**TINY (16 docs, ~10 min)**
- ✅ All 3 sources present
- ⚠️ Only 14% of email corpus (reduced relationship coverage)
- ✅ Good for: Pipeline testing, entity extraction validation
- ❌ Bad for: Multi-hop reasoning, cross-company analysis

**SMALL (41 docs, ~25 min)**
- ✅ All 3 sources present
- ✅ 35% email coverage (basic relationships)
- ✅ 2 tickers (competitor comparisons possible)
- ✅ Good for: Integration testing, workflow validation

**MEDIUM (80 docs, ~48 min)**
- ✅ All 3 sources present
- ✅ 70% email coverage (most relationships)
- ✅ 3 tickers (sector analysis possible)
- ✅ Good for: Full feature testing, pre-production validation

**FULL (178 docs, ~102 min)**
- ✅ Complete coverage
- ✅ 100% email corpus
- ✅ 4 tickers (full portfolio analysis)
- ✅ Good for: Final validation, production testing

## Usage Workflow

### For Query Development (90% of work)

```python
# Cell 22: Set REBUILD_GRAPH = False
REBUILD_GRAPH = False  # Use existing graph
```
**Result**: Instant access to full graph for query testing

### For Ingestion Development (10% of work)

```python
# Portfolio Selector Cell: Change PORTFOLIO_SIZE
PORTFOLIO_SIZE = 'tiny'  # Fast iteration (10 min)

# After basic testing passes, escalate
PORTFOLIO_SIZE = 'small'  # Integration test (25 min)

# Before merging, final validation
PORTFOLIO_SIZE = 'full'  # Full validation (102 min)
```

## Key Learnings

1. **Email corpus is shared**: Reducing tickers doesn't reduce email docs
2. **Source independence**: Each source has independent limit controls
3. **Minimum viable coverage**: Even `tiny` tier has all 3 sources for architectural testing
4. **Speed/Coverage tradeoff**: Configurable via single parameter

## Files Modified

- `ice_simplified.py:876,911` - Added portfolio limit parameters
- `ice_building_workflow.ipynb` - Added portfolio selector cell (position 23)
- `CLAUDE.md:404-430` - Documented development strategies

## Documentation References

- **CLAUDE.md**: Section 5 "Development Workflow Strategies"
- **Serena memory**: This memory
- **Notebook**: `ice_building_workflow.ipynb` Portfolio Selector Cell
