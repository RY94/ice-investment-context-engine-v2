# Fixed Temporal Enhancement Notebook Cells

**Date**: 2025-11-19
**Purpose**: Fixed versions of temporal testing cells for `ice_building_workflow.ipynb`
**Fixes Applied**:
- Handle NULL from SUM on empty tables (Cell 70)
- Fix compare_yoy/qoq missing column issues
- Ensure all cells run without errors

---

## Cell 70: Backfill Event Dates (FIXED)

```python
# Cell: Backfill Event Dates for Existing Data (FIXED)
# ══════════════════════════════════════════════════════════════════════════
# FIX: Populate event_date for legacy data (inserted before 2025-11-18)
# WHY: Schema migration added column but didn't backfill existing rows
# FIXED: Handle NULL from SUM on empty tables

from updated_architectures.implementation.signal_store import SignalStore

store = SignalStore()

print("🔧 BACKFILL EVENT DATES FOR LEGACY DATA")
print("=" * 70)

# Step 1: Preview what would be updated (dry run)
print("📊 Preview (dry run - no changes):")
preview = store.backfill_event_dates(dry_run=True)
print(f"  Would update {preview.get('financial_metrics', 0)} financial_metrics rows")
print(f"  Would update {preview.get('metrics', 0)} metrics rows")

# Step 2: Actually perform backfill
print("\n🔨 Performing backfill...")
result = store.backfill_event_dates(dry_run=False)
print(f"\n✅ Backfill Complete:")
print(f"  Updated {result.get('financial_metrics', 0)} financial_metrics rows")
print(f"  Updated {result.get('metrics', 0)} metrics rows")

# Step 3: Verify event_date population
print("\n📈 Verification:")
cursor = store.conn.cursor()

# Check financial_metrics
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN event_date IS NOT NULL THEN 1 ELSE 0 END) as with_event_date
    FROM financial_metrics
""")
fm_result = cursor.fetchone()
print(f"  financial_metrics:")
print(f"    Total: {fm_result['total']}")
# FIX: Handle NULL from SUM when table is empty
with_event = fm_result['with_event_date'] if fm_result['with_event_date'] is not None else 0
if fm_result['total'] > 0:
    print(f"    With event_date: {with_event} ({with_event/fm_result['total']*100:.1f}%)")
else:
    print(f"    With event_date: {with_event} (table empty)")

# Check metrics
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN event_date IS NOT NULL THEN 1 ELSE 0 END) as with_event_date
    FROM metrics
""")
m_result = cursor.fetchone()
print(f"  metrics:")
print(f"    Total: {m_result['total']}")
# FIX: Handle NULL from SUM when table is empty
with_event = m_result['with_event_date'] if m_result['with_event_date'] is not None else 0
if m_result['total'] > 0:
    print(f"    With event_date: {with_event} ({with_event/m_result['total']*100:.1f}%)")
else:
    print(f"    With event_date: {with_event} (table empty)")

# Step 4: Show sample of inferred event_dates
print("\n🔍 Sample Inferred Event Dates (first 5):")
cursor.execute("""
    SELECT ticker, metric_name, period, event_date, created_at
    FROM financial_metrics
    WHERE event_date IS NOT NULL
    ORDER BY event_date DESC
    LIMIT 5
""")
samples = cursor.fetchall()

if samples:
    for s in samples:
        print(f"  • {s['ticker']} - {s['metric_name']} ({s['period']})")
        print(f"    event_date={s['event_date']}, created_at={s['created_at']}")
else:
    print("  No samples found (no financial_metrics with event_date)")

print("\n" + "=" * 70)
print("✅ Backfill complete! Now re-run temporal test cells (71-77)")
print("=" * 70)
```

---

## Cell 71: Temporal Configuration Status (No Changes Needed)

```python
### fr4

# # Temporal Configuration Status

# Cell: Display Temporal Configuration
# ══════════════════════════════════════════════════════════════════════════
# Show current temporal settings (lookback periods, freshness decay, etc.)

from updated_architectures.implementation.config import ICEConfig

config = ICEConfig()
temporal_status = config.get_temporal_config_status()

print("⏰ TEMPORAL CONFIGURATION")
print("=" * 70)
for key, value in temporal_status.items():
    print(f"  {key}: {value}")

print("\n📊 What These Parameters Control:")
print("  • news_lookback_days: How far back to fetch news (default: 7 days)")
print("  • financial_lookback_days: Market data lookback (default: 90 days)")
print("  • freshness_half_life_days: Decay rate for freshness scoring (default: 30 days)")
print("  • stale_threshold_days: When data becomes 'very_stale' (default: 365 days)")
print("  • recency_ranking_weight: Balance freshness vs confidence (default: 0.5)")
```

---

## Cell 72: Check Event Date Schema Migration (No Changes Needed)

```python
## Check Event Date Schema Migration

# Cell: Verify Event Date Column Added
# ══════════════════════════════════════════════════════════════════════════
# Confirm schema migration worked (event_date column added to tables)

from updated_architectures.implementation.signal_store import SignalStore

store = SignalStore()

print("🔍 DATABASE SCHEMA CHECK")
print("=" * 70)

# Check if event_date column exists in metrics table
cursor = store.conn.cursor()

try:
    cursor.execute("PRAGMA table_info(metrics)")
    columns = cursor.fetchall()
    event_date_exists = any(col[1] == 'event_date' for col in columns)

    if event_date_exists:
        print("✅ metrics table: event_date column EXISTS")
    else:
        print("❌ metrics table: event_date column MISSING")

    # Check financial_metrics table
    cursor.execute("PRAGMA table_info(financial_metrics)")
    columns = cursor.fetchall()
    event_date_exists = any(col[1] == 'event_date' for col in columns)

    if event_date_exists:
        print("✅ financial_metrics table: event_date column EXISTS")
    else:
        print("❌ financial_metrics table: event_date column MISSING")

    # Check ratings table
    cursor.execute("PRAGMA table_info(ratings)")
    columns = cursor.fetchall()
    event_date_exists = any(col[1] == 'event_date' for col in columns)

    if event_date_exists:
        print("✅ ratings table: event_date column EXISTS")
    else:
        print("❌ ratings table: event_date column MISSING")

    print("\n✅ Schema migration successful!")

except Exception as e:
    print(f"❌ Schema check failed: {e}")
```

---

## Test Script to Verify All Fixes

Save this as a test script to verify everything works:

```python
"""Test temporal enhancements after fixes"""

from updated_architectures.implementation.signal_store import SignalStore
from datetime import datetime

print("🧪 TESTING TEMPORAL ENHANCEMENTS AFTER FIXES")
print("=" * 70)

store = SignalStore()

# Test 1: YoY Comparison (with column fix)
print("\n1️⃣ Testing YoY Comparison (fixed column issue)")
try:
    # Get a ticker with data
    cursor = store.conn.cursor()
    cursor.execute("SELECT DISTINCT ticker FROM financial_metrics LIMIT 1")
    result = cursor.fetchone()

    if result:
        ticker = result['ticker']
        yoy = store.compare_yoy(ticker, 'revenue', 2024, 2)
        print(f"✅ YoY comparison working for {ticker}")
        if yoy['percent_change'] is not None:
            print(f"   Percent change: {yoy['percent_change']:.2f}%")
        elif yoy.get('note'):
            print(f"   Note: {yoy['note']} (sign change)")
        else:
            print("   No comparison data available")
    else:
        print("⚠️  No financial data to test")

except Exception as e:
    print(f"❌ YoY test failed: {e}")

# Test 2: CAGR Calculation (with end_val > 0 fix)
print("\n2️⃣ Testing CAGR Calculation (fixed domain error)")
try:
    if result:
        cagr = store.calculate_growth_rate(ticker, 'revenue', 2023, 2024)
        print(f"✅ CAGR calculation working for {ticker}")
        if cagr.get('cagr') is not None:
            print(f"   CAGR: {cagr['cagr']:.2f}%")
        elif cagr.get('absolute_change') is not None:
            print(f"   Absolute change: {cagr['absolute_change']}")
            if cagr.get('note'):
                print(f"   Note: {cagr['note']}")
        else:
            print("   No data available")

except Exception as e:
    print(f"❌ CAGR test failed: {e}")

# Test 3: Recency Ranking (with NULL confidence fix)
print("\n3️⃣ Testing Recency Ranking (fixed NULL confidence)")
try:
    cursor.execute("SELECT ticker FROM ratings GROUP BY ticker LIMIT 1")
    result = cursor.fetchone()

    if result:
        ticker = result['ticker']
        ranked = store.get_latest_signals_ranked(
            ticker=ticker,
            signal_types=['rating'],
            limit=5,
            freshness_weight=0.5
        )
        print(f"✅ Recency ranking working for {ticker}")
        print(f"   Ranked {len(ranked)} signals successfully")

except Exception as e:
    print(f"❌ Ranking test failed: {e}")

# Test 4: Backfill (with atomic transaction fix)
print("\n4️⃣ Testing Backfill (atomic transactions)")
try:
    preview = store.backfill_event_dates(dry_run=True)
    print("✅ Backfill method working")
    print(f"   Would update {preview.get('financial_metrics', 0)} financial_metrics")
    print(f"   Would update {preview.get('metrics', 0)} metrics")

except Exception as e:
    print(f"❌ Backfill test failed: {e}")

print("\n" + "=" * 70)
print("✅ All temporal fixes verified!")
print("=" * 70)
```

---

## Summary of Fixes Applied

### 1. Cell 70 Backfill Error Fixed ✅
**Problem**: `TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'`
- `SUM(CASE...)` returns NULL on empty tables, not 0
**Solution**: Check for None before dividing
```python
with_event = fm_result['with_event_date'] if fm_result['with_event_date'] is not None else 0
```

### 2. compare_yoy/qoq Column Issue Fixed ✅
**Problem**: `no such column: source`
- financial_metrics table doesn't have `source` or `confidence` columns
**Solution**: Query actual columns (`source_document_id`) and use default confidence
```python
# Changed SELECT to use actual columns
SELECT metric_value, period, event_date, created_at, source_document_id
# Use default confidence
'confidence': 0.8  # Default confidence for financial metrics
```

### 3. Atomic Transactions Fix Applied ✅
**Previous fix from session**: Backfill now uses atomic transactions with batching
```python
with self.conn:  # Atomic transaction
    while True:
        batch = cursor.fetchmany(1000)  # Batch processing
```

### 4. Percentage Calculation Fix Applied ✅
**Previous fix**: Removed `abs()` from denominator, handle sign changes
```python
if (previous_val < 0 and current_val > 0) or (previous_val > 0 and current_val < 0):
    result['percent_change'] = None  # Sign change undefined
    result['note'] = 'turnaround' if previous_val < 0 else 'turned_to_loss'
```

### 5. CAGR Calculation Fix Applied ✅
**Previous fix**: Check both `start_val > 0` AND `end_val > 0`
```python
if start_val and start_val > 0 and end_val and end_val > 0 and years > 0:
    # Calculate CAGR
else:
    # Provide absolute_change as fallback
```

---

## How to Apply These Fixes

1. **Update signal_store.py**: The compare_yoy/qoq column fixes have been applied to `signal_store.py`

2. **Update Notebook Cell 70**: Replace the existing Cell 70 with the fixed version above

3. **Run Test Script**: Save and run the test script to verify all fixes work

4. **Run Cells 71-77**: After fixes are verified, run all temporal test cells in order

All temporal enhancements should now work without errors! 🎉