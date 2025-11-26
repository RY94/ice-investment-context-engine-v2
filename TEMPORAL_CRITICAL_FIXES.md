# Critical Temporal Architecture Fixes Required

## Priority 1: Data Integrity Fixes

### Fix 1: Atomic Backfill Operations
```python
def backfill_event_dates(self, dry_run: bool = False) -> Dict[str, int]:
    """Fixed version with atomic transaction"""
    cursor = self.conn.cursor()
    results = {}

    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # Update financial_metrics
        # ... existing update logic ...
        results['financial_metrics'] = updated_fm

        # Update metrics
        # ... existing update logic ...
        results['metrics'] = updated_m

        # Commit only if both succeed
        self.conn.commit()

    except Exception as e:
        # Rollback on any error
        self.conn.rollback()
        self.logger.error(f"Backfill failed: {e}")
        raise

    return results
```

### Fix 2: Correct Percentage Change Calculation
```python
def _calculate_percentage_change(self, old_value: float, new_value: float) -> Optional[float]:
    """Handle negative values correctly"""
    # Case 1: Division by zero
    if old_value == 0:
        if new_value == 0:
            return 0.0
        else:
            return None  # Undefined (infinite growth)

    # Case 2: Sign change (loss to profit or vice versa)
    if old_value < 0 and new_value > 0:
        return None  # Undefined (turnaround)
    if old_value > 0 and new_value < 0:
        return None  # Undefined (turned to loss)

    # Case 3: Both negative (improving or worsening loss)
    if old_value < 0 and new_value < 0:
        # Use absolute values but invert result
        return -((new_value - old_value) / abs(old_value)) * 100

    # Case 4: Both positive (normal case)
    return ((new_value - old_value) / old_value) * 100
```

### Fix 3: Safe CAGR Calculation
```python
def calculate_growth_rate(self, ticker: str, metric_name: str,
                         start_year: int, end_year: int,
                         quarter: Optional[int] = None) -> Dict[str, Any]:
    """Fixed CAGR handling negative values"""
    # ... existing data fetching ...

    if start_val and end_val and years > 0:
        # Check for sign change
        if start_val < 0 and end_val > 0:
            result['cagr'] = None
            result['growth_type'] = 'turnaround_to_profit'
        elif start_val > 0 and end_val < 0:
            result['cagr'] = None
            result['growth_type'] = 'turned_to_loss'
        elif start_val < 0 and end_val < 0:
            # Both negative - use absolute value ratio inverted
            abs_ratio = abs(end_val) / abs(start_val)
            if abs_ratio < 1:  # Loss improved
                cagr = (1 - pow(abs_ratio, 1/years)) * 100
                result['cagr'] = cagr
                result['growth_type'] = 'loss_improvement'
            else:  # Loss worsened
                cagr = -(pow(abs_ratio, 1/years) - 1) * 100
                result['cagr'] = cagr
                result['growth_type'] = 'loss_deterioration'
        else:
            # Normal positive case
            cagr = (pow(end_val / start_val, 1 / years) - 1) * 100
            result['cagr'] = round(cagr, 2)
            result['growth_type'] = 'normal_growth'
```

## Priority 2: Error Handling Fixes

### Fix 4: Proper Exception Handling
```python
def get_events_in_date_range(self, ticker: str, start_date: str, end_date: str,
                            event_type: Optional[str] = None,
                            is_future: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Raise exceptions instead of silent failures"""
    # Validate date range - raise on invalid
    if not self._validate_date_range(start_date, end_date):
        raise ValueError(f"Invalid date range: {start_date} to {end_date}")

    # Continue with query...
```

### Fix 5: Chronological Validation
```python
def backfill_event_dates(self, dry_run: bool = False) -> Dict[str, int]:
    """Add chronological validation"""
    # ... existing logic ...

    for row in rows_to_update:
        inferred_date = self._infer_event_date_from_period(...)

        if inferred_date:
            # Validate chronologically
            if row.get('created_at'):
                created_dt = datetime.fromisoformat(row['created_at'])
                inferred_dt = datetime.fromisoformat(inferred_date)

                if inferred_dt > created_dt:
                    self.logger.warning(
                        f"Skipping paradox: event_date {inferred_date} > "
                        f"created_at {row['created_at']} for period {row['period']}"
                    )
                    continue

            # Update only if valid
            cursor.execute("UPDATE financial_metrics SET event_date = ? WHERE id = ?",
                         (inferred_date, row['id']))
```

## Priority 3: Performance Fixes

### Fix 6: Efficient Period Generation
```python
def generate_comparison_periods(self, ticker: str, metric_name: str,
                               comparison_type: str = 'yoy',
                               lookback_periods: int = 4) -> List[Dict[str, Any]]:
    """Optimized O(n) instead of O(4n)"""
    comparisons = []

    if comparison_type == 'yoy':
        # Generate only what we need
        current_quarters = self.get_trailing_quarters(lookback_periods)

        for q in current_quarters:
            current = q['period']
            # Calculate previous year's same quarter directly
            previous = f"Q{q['quarter']} {q['year'] - 1}"

            comparisons.append({
                'current_period': current,
                'previous_period': previous,
                'comparison_type': 'YoY',
                # Check data availability...
            })
```

### Fix 7: Input Validation
```python
def parse_period_string(period: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """Add year range validation"""
    # ... existing parsing ...

    # Validate year is reasonable
    if year and (year < 1900 or year > 2100):
        raise ValueError(f"Invalid year {year} - must be between 1900-2100")

    return period_type, year, quarter
```

## Testing Requirements

1. **Test negative value handling**:
   - Company with losses improving
   - Company turning from profit to loss
   - Percentage calculations with negative denominators

2. **Test edge cases**:
   - Zero denominators
   - NULL values in calculations
   - Invalid date ranges
   - Future dates

3. **Test transaction atomicity**:
   - Simulate failure in second table update
   - Verify rollback works correctly

4. **Test chronological validation**:
   - Event dates must be <= created_at
   - Period dates must make sense

## Summary

The temporal architecture has valuable functionality but needs these critical fixes before production use:

1. **Data Integrity**: Atomic transactions, chronological validation
2. **Mathematical Correctness**: Handle negative values, sign changes
3. **Error Transparency**: Raise exceptions instead of silent failures
4. **Performance**: Remove brute force approaches
5. **Input Validation**: Validate years, dates, ranges

Estimated effort: 2-3 days for fixes + 1 day for comprehensive testing