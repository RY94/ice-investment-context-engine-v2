# Notebook Financial Limit Bug Fix & Parameter Logic Enhancement (2025-10-22)

## Overview

Fixed critical bug where financial documents bypassed news_limit=0 controls and enhanced ice_building_workflow.ipynb with comprehensive parameter validation, accurate document estimation, and staleness warnings.

## The Bug: Financial Documents Bypassing Limits

### Discovery
User set SOURCE_SELECTOR='email_only' (news_limit=0, sec_limit=0) + EMAIL_SELECTOR='crawl4ai_test' expecting 5 documents (5 emails) but saw 11 documents.

### Root Cause
`fetch_company_financials()` in data_ingestion.py had no limit parameter - always fetched 3 financial documents (Income Statement, Balance Sheet, Cash Flow) regardless of source selection.

### Solution
**File**: `updated_architectures/implementation/data_ingestion.py:408-425`

```python
def fetch_company_financials(self, symbol: str, limit: int = 3) -> List[Dict[str, str]]:
    """
    Fetch company financial data - return source-tagged documents
    
    Args:
        symbol: Stock ticker symbol
        limit: Maximum number of financial documents to fetch (default: 3)
               Set to 0 to skip financial data entirely (e.g., email_only mode)
    """
    # Skip if limit is 0 (e.g., when api=False in Source Selector)
    if limit == 0:
        logger.info(f"⏭️  {symbol}: Skipping financials (limit=0)")
        return []
    
    # ... rest of implementation
```

**Integration**: Updated 3 call sites in `ice_simplified.py` to pass `news_limit`:
- Line 1197: Pre-fetch phase
- Line 1018: Historical data ingestion
- Line 1393: Portfolio data ingestion (uses limit=5, unchanged)

**Rationale**: Financials and news are both API sources, so controlling both with news_limit maintains logical grouping.

## Notebook Enhancements: ice_building_workflow.ipynb

### Issue 1: Inaccurate estimated_docs
**Problem**: Cell 18 calculated estimated_docs BEFORE EMAIL_SELECTOR/SOURCE_SELECTOR precedence applied, showing incorrect counts.

**Solution**: Moved calculation to Cell 26 (after all precedence rules) with breakdown:
```python
# Calculate ACCURATE estimated docs (after ALL overrides and precedence)
estimated_docs = (
    actual_email_count +
    len(test_holdings) * news_limit +
    len(test_holdings) * financial_per_ticker +  # Financials respect news_limit
    len(test_holdings) * sec_limit
)

print(f"\n📊 Estimated Documents: {estimated_docs}")
print(f"  - Email: {actual_email_count}")
print(f"  - News: {len(test_holdings)} tickers × {news_limit} = ...")
print(f"  - Financials: {len(test_holdings)} tickers × {financial_per_ticker} = ...")
print(f"  - SEC: {len(test_holdings)} tickers × {sec_limit} = ...")
```

### Issue 2: Missing Parameter Validation
**Problem**: Typos in selectors caused cryptic KeyErrors instead of helpful messages.

**Solutions**:

**Cell 24 (PORTFOLIO_SIZE)**:
```python
valid_sizes = ['tiny', 'small', 'medium', 'full']
if PORTFOLIO_SIZE not in valid_sizes:
    raise ValueError(f"❌ Invalid PORTFOLIO_SIZE='{PORTFOLIO_SIZE}'. Choose from: {', '.join(valid_sizes)}")

# Dependency check for 'full' option
if PORTFOLIO_SIZE == 'full' and 'holdings' not in dir():
    raise RuntimeError("❌ PORTFOLIO_SIZE='full' requires Cell 16 to run first!")
```

**Cell 25 (EMAIL_SELECTOR)**:
```python
valid_email = ['all', 'crawl4ai_test', 'docling_test', 'custom']
if EMAIL_SELECTOR not in valid_email:
    raise ValueError(f"❌ Invalid EMAIL_SELECTOR='{EMAIL_SELECTOR}'. Choose from: {', '.join(valid_email)}")
```

### Issue 3: EMAIL_SELECTOR Precedence Not Visible
**Problem**: Display always showed email_limit even when EMAIL_SELECTOR='specific' ignored it.

**Solution**: Cell 26 conditional display:
```python
if EMAIL_SELECTOR == 'all':
    email_display = f"{email_limit} emails (up to limit)"
    actual_email_count = email_limit
else:
    actual_email_count = len(email_files_to_process) if email_files_to_process else 0
    email_display = f"{actual_email_count} specific files (EMAIL_SELECTOR ignores email_limit)"
```

### Issue 4: Staleness Risk with REBUILD_GRAPH=False
**Problem**: Users could query stale graph data without realizing selectors changed.

**Solution**: Cell 27 prominent warning:
```python
else:
    print("\n" + "="*70)
    print("⚠️  REBUILD_GRAPH = False")
    print("⚠️  Using existing graph - NOT rebuilding with current selectors!")
    print("⚠️  If you changed PORTFOLIO/EMAIL/SOURCE configuration,")
    print("⚠️  set REBUILD_GRAPH=True to avoid querying STALE DATA!")
    print("="*70 + "\n")
```

## Parameter Semantics (User Clarifications)

### news_limit & sec_limit: PER STOCK
- Called per ticker in loop: `for symbol in symbols: fetch_news(symbol, limit=news_limit)`
- Total count = len(holdings) × news_limit

### email_limit: TOTAL ACROSS PORTFOLIO
- Fetched once with `tickers=None` (trust the graph strategy)
- NOT per stock - emails don't work that way
- Total count = email_limit (if EMAIL_SELECTOR='all')

### EMAIL_SELECTOR Precedence
- 'all' → Uses email_limit
- Any other value ('crawl4ai_test', 'docling_test', 'custom') → IGNORES email_limit, uses specific files

### SOURCE_SELECTOR Logic
- Enables/disables sources by setting limits to 0
- 'email_only' → news_limit=0, sec_limit=0 (financials also skip via news_limit)
- 'all' → All limits from PORTFOLIO_SIZE apply

## Code Footprint
- **Total lines added**: ~52 (34 in notebook + 18 in data_ingestion/ice_simplified)
- **Breaking changes**: Zero
- **Files modified**: 3 (data_ingestion.py, ice_simplified.py, ice_building_workflow.ipynb)
- **Cells modified**: 4 (Cells 24, 25, 26, 27)

## Testing Results
✅ Bug fix validated: 11 docs → 5 docs (email_only mode)
✅ Parameter validation: Clear errors for invalid inputs
✅ Estimated docs accuracy: Matches actual after precedence
✅ Staleness warning: Prominent display when REBUILD_GRAPH=False

## Architecture Principles Followed
- ✅ "Write as little code as possible" (52 total lines)
- ✅ "Simple orchestration" (validation in notebook, logic in modules)
- ✅ "User-directed" (clear warnings, accurate information)
- ✅ "Transparency first" (honest display of document counts)

## Related Files
- `updated_architectures/implementation/data_ingestion.py:408-425`
- `updated_architectures/implementation/ice_simplified.py:1018,1197,1393`
- `ice_building_workflow.ipynb:Cells 24,25,26,27`
- `PROJECT_CHANGELOG.md:Entry #85`

## Future Considerations
- Consider adding similar validation to ice_query_workflow.ipynb if it has configurable parameters
- Pattern can be reused for any notebook with multi-cell parameter configuration
- Staleness warning pattern applicable to any workflow with cached/existing data
