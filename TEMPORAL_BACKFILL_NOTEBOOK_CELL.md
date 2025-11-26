# Temporal Enhancements - Backfill Cell for Notebook

**Purpose**: Populate `event_date` for existing data inserted before temporal enhancements (2025-11-18)

**Instructions**:
1. Insert this cell in `ice_building_workflow.ipynb` **BEFORE** the temporal test cells (before Cell 54)
2. Run this cell once to backfill event dates
3. Then re-run the temporal test cells (54-57) to verify fixes

---

## Code Cell: Backfill Event Dates

```python
# Cell: Backfill Event Dates for Existing Data
# ══════════════════════════════════════════════════════════════════════════
# FIX: Populate event_date for legacy data (inserted before 2025-11-18)
# WHY: Schema migration added column but didn't backfill existing rows

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
print(f"    With event_date: {fm_result['with_event_date']} ({fm_result['with_event_date']/max(fm_result['total'],1)*100:.1f}%)")

# Check metrics
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN event_date IS NOT NULL THEN 1 ELSE 0 END) as with_event_date
    FROM metrics
""")
m_result = cursor.fetchone()
print(f"  metrics:")
print(f"    Total: {m_result['total']}")
print(f"    With event_date: {m_result['with_event_date']} ({m_result['with_event_date']/max(m_result['total'],1)*100:.1f}%)")

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
print("✅ Backfill complete! Now re-run temporal test cells (54-57)")
print("=" * 70)
```

---

## What This Cell Does

**Step 1: Dry Run Preview**
- Counts how many rows need backfill without making changes
- Helps you understand impact before committing

**Step 2: Actual Backfill**
- Queries all rows with NULL event_date but valid period info
- Calls `_infer_event_date_from_period()` for each row
- Updates event_date via SQL UPDATE
- Commits transaction

**Step 3: Verification**
- Shows before/after statistics
- Percentage of rows with event_date populated
- Confirms backfill worked correctly

**Step 4: Sample Display**
- Shows 5 sample inferred event_dates
- Lets you visually verify inference logic (Q2 2024 → 2024-07-15, etc.)

---

## Expected Output

```
🔧 BACKFILL EVENT DATES FOR LEGACY DATA
======================================================================
📊 Preview (dry run - no changes):
  Would update 34 financial_metrics rows
  Would update 0 metrics rows

🔨 Performing backfill...

✅ Backfill Complete:
  Updated 34 financial_metrics rows
  Updated 0 metrics rows

📈 Verification:
  financial_metrics:
    Total: 34
    With event_date: 34 (100.0%)
  metrics:
    Total: 0
    With event_date: 0 (0.0%)

🔍 Sample Inferred Event Dates (first 5):
  • NVDA - Revenue (Q2 2024)
    event_date=2024-07-15, created_at=2024-11-18
  • NVDA - Net Income (Q2 2024)
    event_date=2024-07-15, created_at=2024-11-18
  ...

======================================================================
✅ Backfill complete! Now re-run temporal test cells (54-57)
======================================================================
```

---

## After Running This Cell

**Next Steps**:

1. ✅ **Backfill complete** - All existing financial_metrics now have event_date
2. 🔄 **Re-run Cell 54** - "Test Event Date Query Fix" should now find metrics in July range
3. 🔄 **Re-run Cell 55** - "Test Recency-Aware Ranking" should work without TypeError
4. 🔄 **Re-run Cell 57** - "Compare Chronological vs Recency Ranking" should work

**Expected Improvements**:

**Cell 54 (Event Date Query Fix)** - Before vs After:
```
BEFORE backfill:
📊 Current Data Status:
  Total financial_metrics: 34
  With event_date populated: 0  ❌

🔍 Metrics Found in July Range:
  No metrics found in July range

AFTER backfill:
📊 Current Data Status:
  Total financial_metrics: 34
  With event_date populated: 34  ✅

🔍 Metrics Found in July Range:
  • NVDA - Revenue (Q2 2024)
    event_date=2024-07-15, created_at=2024-08-01
  ...
✅ Query working! Found X metrics in July range
```

**Cell 55 & 57 (Recency Ranking)** - Before vs After:
```
BEFORE NULL-safe fix:
❌ TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'

AFTER NULL-safe fix:
✅ PASS: Top signal is recent + high confidence (Analyst C)
✅ PASS: All signals have composite_rank
✅ PASS: Signals sorted by composite_rank DESC
```

---

## Troubleshooting

**If backfill shows 0 rows updated**:
- Check that financial_metrics table has data: `SELECT COUNT(*) FROM financial_metrics`
- Check period format: `SELECT DISTINCT period FROM financial_metrics`
- Some rows may not have period info (event_date stays NULL, queries use created_at fallback)

**If TypeError persists after this**:
- Restart kernel to reload updated signal_store.py code
- Verify signal_store.py lines 2063-2076 have the `or` pattern fix

**If event_date queries still don't find metrics**:
- Check event_date values: `SELECT ticker, period, event_date FROM financial_metrics LIMIT 10`
- Verify date range in query matches inferred dates (Q2 2024 → 2024-07-15)
