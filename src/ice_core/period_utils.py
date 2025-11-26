# Location: /src/ice_core/period_utils.py
# Purpose: Period arithmetic and manipulation utilities for temporal queries
# Why: Centralizes period calculation logic for consistent temporal operations
# Relevant Files: signal_store.py, temporal_analyzer.py, temporal_enhancer.py

"""
Period Utilities for ICE System

Helper functions for fiscal period arithmetic, date conversions,
and period string manipulations.
"""

from datetime import datetime, timedelta
from typing import Tuple, Optional
import re


def parse_period_string(period: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Parse period string into components.

    Args:
        period: Period string like "Q2 2024", "FY2024", "2024-Q2"

    Returns:
        Tuple of (period_type, year, quarter)
        - period_type: 'quarterly', 'annual', or None
        - year: Fiscal year
        - quarter: Quarter number (1-4) or None for annual
    """
    if not period:
        return None, None, None

    period = period.strip().upper()

    # Match "Q2 2024" format
    match = re.match(r'Q(\d)\s+(\d{4})', period)
    if match:
        return 'quarterly', int(match.group(2)), int(match.group(1))

    # Match "2024-Q2" format (Yahoo)
    match = re.match(r'(\d{4})-Q(\d)', period)
    if match:
        return 'quarterly', int(match.group(1)), int(match.group(2))

    # Match "FY2024" format
    match = re.match(r'FY(\d{4})', period)
    if match:
        return 'annual', int(match.group(1)), None

    return None, None, None


def next_period(period: str) -> Optional[str]:
    """
    Calculate the next fiscal period.

    Args:
        period: Current period string

    Returns:
        Next period string or None if invalid

    Examples:
        >>> next_period("Q1 2024")
        'Q2 2024'
        >>> next_period("Q4 2024")
        'Q1 2025'
    """
    period_type, year, quarter = parse_period_string(period)

    if period_type == 'quarterly' and quarter:
        if quarter == 4:
            return f"Q1 {year + 1}"
        else:
            return f"Q{quarter + 1} {year}"
    elif period_type == 'annual':
        return f"FY{year + 1}"

    return None


def previous_period(period: str) -> Optional[str]:
    """
    Calculate the previous fiscal period.

    Args:
        period: Current period string

    Returns:
        Previous period string or None if invalid
    """
    period_type, year, quarter = parse_period_string(period)

    if period_type == 'quarterly' and quarter:
        if quarter == 1:
            return f"Q4 {year - 1}"
        else:
            return f"Q{quarter - 1} {year}"
    elif period_type == 'annual':
        return f"FY{year - 1}"

    return None


def period_difference(period1: str, period2: str) -> Optional[int]:
    """
    Calculate the number of periods between two period strings.

    Args:
        period1: First period
        period2: Second period

    Returns:
        Number of periods difference (positive if period1 > period2)
    """
    type1, year1, quarter1 = parse_period_string(period1)
    type2, year2, quarter2 = parse_period_string(period2)

    if type1 != type2:
        return None

    if type1 == 'quarterly':
        periods1 = year1 * 4 + (quarter1 - 1)
        periods2 = year2 * 4 + (quarter2 - 1)
        return periods1 - periods2
    elif type1 == 'annual':
        return year1 - year2

    return None


def add_periods(period: str, num_periods: int) -> Optional[str]:
    """
    Add a number of periods to a base period.

    Args:
        period: Base period string
        num_periods: Number of periods to add (negative to subtract)

    Returns:
        Resulting period string
    """
    if num_periods == 0:
        return period

    result = period
    if num_periods > 0:
        for _ in range(num_periods):
            result = next_period(result)
            if not result:
                return None
    else:
        for _ in range(abs(num_periods)):
            result = previous_period(result)
            if not result:
                return None

    return result


def period_to_date_range(period: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Convert period string to date range.

    Args:
        period: Period string

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    period_type, year, quarter = parse_period_string(period)

    if period_type == 'quarterly' and quarter:
        quarter_ranges = {
            1: (f'{year}-01-01', f'{year}-03-31'),
            2: (f'{year}-04-01', f'{year}-06-30'),
            3: (f'{year}-07-01', f'{year}-09-30'),
            4: (f'{year}-10-01', f'{year}-12-31')
        }
        return quarter_ranges.get(quarter, (None, None))
    elif period_type == 'annual':
        return f'{year}-01-01', f'{year}-12-31'

    return None, None


def periods_in_range(start_period: str, end_period: str) -> list:
    """
    Generate all periods between start and end (inclusive).

    Args:
        start_period: Starting period
        end_period: Ending period

    Returns:
        List of period strings
    """
    periods = [start_period]
    current = start_period

    while current != end_period:
        current = next_period(current)
        if not current:
            break
        periods.append(current)
        if len(periods) > 100:  # Safety limit
            break

    return periods if periods[-1] == end_period else []