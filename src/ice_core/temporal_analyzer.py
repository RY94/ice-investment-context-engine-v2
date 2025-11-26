# Location: /src/ice_core/temporal_analyzer.py
# Purpose: High-level temporal analysis including trend detection and pattern recognition
# Why: Enables Query Type 7 (Trend Detection) for investment decision support
# Relevant Files: signal_store.py, temporal_enhancer.py, ice_simplified.py

"""
Temporal Analyzer for ICE System

Provides trend detection, momentum analysis, and temporal pattern recognition
for investment signals and financial metrics. Supports multi-period analysis
and statistical trend identification.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class TemporalAnalyzer:
    """
    Analyzes temporal patterns in financial metrics and signals.

    Provides trend detection, momentum calculation, and pattern recognition
    for investment decision support. Uses statistical methods to identify
    significant trends and anomalies.
    """

    def __init__(self, signal_store):
        """
        Initialize the TemporalAnalyzer.

        Args:
            signal_store: SignalStore instance for data access
        """
        self.store = signal_store

    def detect_metric_trend(self, ticker: str, metric_name: str,
                           periods: int = 8,
                           period_type: str = 'quarterly') -> Dict[str, Any]:
        """
        Detect trend in a metric over multiple periods using linear regression.

        Args:
            ticker: Stock ticker symbol
            metric_name: Name of the metric to analyze
            periods: Number of historical periods to analyze
            period_type: 'quarterly' or 'annual'

        Returns:
            Dict containing:
                - trend_direction: 'upward', 'downward', or 'flat'
                - trend_strength: Correlation coefficient (0-1)
                - slope: Rate of change per period
                - p_value: Statistical significance
                - forecast_next_period: Predicted next value
                - data_points: Historical values used
        """
        cursor = self.store.conn.cursor()

        # Get historical data
        if period_type == 'quarterly':
            pattern = 'Q%'
        else:
            pattern = 'FY%'

        data = cursor.execute("""
            SELECT period, metric_value, event_date, created_at
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ? AND period LIKE ?
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT ?
        """, (ticker, metric_name, pattern, periods)).fetchall()

        if len(data) < 3:
            return {
                'trend_direction': 'insufficient_data',
                'data_points': len(data),
                'minimum_required': 3
            }

        # Prepare data for regression
        values = [d['metric_value'] for d in reversed(data) if d['metric_value']]
        if len(values) < 3:
            return {'trend_direction': 'insufficient_valid_data'}

        x = np.arange(len(values))
        y = np.array(values)

        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Determine trend direction and strength
        if p_value < 0.05:  # Statistically significant
            if slope > 0:
                trend_direction = 'upward'
            elif slope < 0:
                trend_direction = 'downward'
            else:
                trend_direction = 'flat'
        else:
            trend_direction = 'no_significant_trend'

        # Forecast next period
        next_x = len(values)
        forecast = slope * next_x + intercept

        # Calculate percentage change per period
        if values[0] != 0:
            avg_pct_change = (slope / values[0]) * 100
        else:
            avg_pct_change = None

        return {
            'ticker': ticker,
            'metric_name': metric_name,
            'trend_direction': trend_direction,
            'trend_strength': abs(r_value),
            'slope': slope,
            'p_value': p_value,
            'avg_pct_change_per_period': avg_pct_change,
            'forecast_next_period': forecast,
            'confidence_interval': (forecast - 2*std_err, forecast + 2*std_err),
            'data_points': len(values),
            'historical_values': values,
            'periods_analyzed': [d['period'] for d in reversed(data)]
        }

    def calculate_momentum(self, ticker: str, metric_name: str,
                         short_periods: int = 3,
                         long_periods: int = 6) -> Dict[str, Any]:
        """
        Calculate momentum indicators for a metric.

        Uses moving averages to identify acceleration/deceleration in growth.

        Args:
            ticker: Stock ticker symbol
            metric_name: Metric to analyze
            short_periods: Periods for short-term average
            long_periods: Periods for long-term average

        Returns:
            Dict with momentum indicators and signals
        """
        cursor = self.store.conn.cursor()

        # Get sufficient historical data
        data = cursor.execute("""
            SELECT period, metric_value, event_date, created_at
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ?
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT ?
        """, (ticker, metric_name, long_periods + 2)).fetchall()

        if len(data) < long_periods:
            return {'momentum': 'insufficient_data'}

        values = [d['metric_value'] for d in data if d['metric_value']]
        values.reverse()  # Oldest first

        if len(values) < long_periods:
            return {'momentum': 'insufficient_valid_data'}

        # Calculate moving averages
        short_ma = np.mean(values[-short_periods:])
        long_ma = np.mean(values[-long_periods:])

        # Calculate momentum
        if long_ma != 0:
            momentum_ratio = short_ma / long_ma
        else:
            momentum_ratio = None

        # Determine signal
        if momentum_ratio:
            if momentum_ratio > 1.1:
                signal = 'strong_positive_momentum'
            elif momentum_ratio > 1.02:
                signal = 'positive_momentum'
            elif momentum_ratio < 0.9:
                signal = 'strong_negative_momentum'
            elif momentum_ratio < 0.98:
                signal = 'negative_momentum'
            else:
                signal = 'neutral'
        else:
            signal = 'undefined'

        # Calculate rate of change
        recent_roc = []
        for i in range(1, min(4, len(values))):
            if values[-i-1] != 0:
                roc = ((values[-i] - values[-i-1]) / values[-i-1]) * 100
                recent_roc.append(roc)

        return {
            'ticker': ticker,
            'metric_name': metric_name,
            'momentum_ratio': momentum_ratio,
            'momentum_signal': signal,
            'short_ma': short_ma,
            'long_ma': long_ma,
            'recent_value': values[-1] if values else None,
            'recent_rate_of_change': recent_roc,
            'accelerating': all(i > 0 for i in recent_roc) if recent_roc else None,
            'periods_analyzed': len(values)
        }

    def detect_seasonality(self, ticker: str, metric_name: str,
                         years: int = 3) -> Dict[str, Any]:
        """
        Detect seasonal patterns in quarterly metrics.

        Args:
            ticker: Stock ticker symbol
            metric_name: Metric to analyze
            years: Number of years to analyze

        Returns:
            Dict with seasonality analysis
        """
        cursor = self.store.conn.cursor()

        # Get quarterly data for multiple years
        data = cursor.execute("""
            SELECT period, metric_value
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ? AND period LIKE 'Q%'
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT ?
        """, (ticker, metric_name, years * 4)).fetchall()

        if len(data) < 8:  # Need at least 2 years
            return {'seasonality': 'insufficient_data'}

        # Organize by quarter
        q1_values, q2_values, q3_values, q4_values = [], [], [], []

        for d in data:
            if d['metric_value'] is None:
                continue
            period = d['period']
            if 'Q1' in period:
                q1_values.append(d['metric_value'])
            elif 'Q2' in period:
                q2_values.append(d['metric_value'])
            elif 'Q3' in period:
                q3_values.append(d['metric_value'])
            elif 'Q4' in period:
                q4_values.append(d['metric_value'])

        # Calculate average by quarter
        quarter_avgs = {
            'Q1': np.mean(q1_values) if q1_values else None,
            'Q2': np.mean(q2_values) if q2_values else None,
            'Q3': np.mean(q3_values) if q3_values else None,
            'Q4': np.mean(q4_values) if q4_values else None
        }

        # Identify strongest/weakest quarters
        valid_quarters = {k: v for k, v in quarter_avgs.items() if v is not None}
        if valid_quarters:
            strongest_quarter = max(valid_quarters, key=valid_quarters.get)
            weakest_quarter = min(valid_quarters, key=valid_quarters.get)
            seasonality_detected = max(valid_quarters.values()) / min(valid_quarters.values()) > 1.15
        else:
            strongest_quarter = None
            weakest_quarter = None
            seasonality_detected = False

        return {
            'ticker': ticker,
            'metric_name': metric_name,
            'seasonality_detected': seasonality_detected,
            'quarter_averages': quarter_avgs,
            'strongest_quarter': strongest_quarter,
            'weakest_quarter': weakest_quarter,
            'years_analyzed': len(data) // 4,
            'data_points': len(data)
        }

    def identify_inflection_points(self, ticker: str, metric_name: str,
                                  threshold_pct: float = 15.0) -> Dict[str, Any]:
        """
        Identify significant inflection points where growth rate changed dramatically.

        Args:
            ticker: Stock ticker symbol
            metric_name: Metric to analyze
            threshold_pct: Percentage change threshold for inflection detection

        Returns:
            Dict with identified inflection points
        """
        cursor = self.store.conn.cursor()

        # Get historical data
        data = cursor.execute("""
            SELECT period, metric_value, event_date, created_at
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ?
            ORDER BY COALESCE(event_date, created_at) ASC
        """, (ticker, metric_name)).fetchall()

        if len(data) < 3:
            return {'inflection_points': [], 'insufficient_data': True}

        inflection_points = []

        # Calculate period-over-period changes
        for i in range(2, len(data)):
            prev2 = data[i-2]['metric_value']
            prev1 = data[i-1]['metric_value']
            curr = data[i]['metric_value']

            if not all([prev2, prev1, curr]):
                continue

            # Calculate growth rates
            growth1 = ((prev1 - prev2) / abs(prev2)) * 100
            growth2 = ((curr - prev1) / abs(prev1)) * 100

            # Check for inflection
            growth_diff = growth2 - growth1

            if abs(growth_diff) > threshold_pct:
                inflection_type = 'acceleration' if growth_diff > 0 else 'deceleration'

                # Check for trend reversal
                if growth1 * growth2 < 0:  # Signs differ
                    inflection_type = 'reversal'

                inflection_points.append({
                    'period': data[i]['period'],
                    'date': data[i]['event_date'] or data[i]['created_at'],
                    'type': inflection_type,
                    'prev_growth': round(growth1, 2),
                    'new_growth': round(growth2, 2),
                    'growth_change': round(growth_diff, 2),
                    'value': curr
                })

        return {
            'ticker': ticker,
            'metric_name': metric_name,
            'inflection_points': inflection_points,
            'total_periods': len(data),
            'threshold_used': threshold_pct
        }

    def analyze_volatility(self, ticker: str, metric_name: str,
                         periods: int = 12) -> Dict[str, Any]:
        """
        Analyze volatility and consistency of a metric over time.

        Args:
            ticker: Stock ticker symbol
            metric_name: Metric to analyze
            periods: Number of periods to analyze

        Returns:
            Dict with volatility metrics
        """
        cursor = self.store.conn.cursor()

        # Get historical data
        data = cursor.execute("""
            SELECT metric_value
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ?
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT ?
        """, (ticker, metric_name, periods)).fetchall()

        values = [d['metric_value'] for d in data if d['metric_value']]

        if len(values) < 3:
            return {'volatility': 'insufficient_data'}

        # Calculate volatility metrics
        mean_val = np.mean(values)
        std_dev = np.std(values)
        cv = (std_dev / mean_val) * 100 if mean_val != 0 else None

        # Calculate period-over-period changes
        changes = []
        for i in range(1, len(values)):
            if values[i] != 0:
                change = ((values[i-1] - values[i]) / abs(values[i])) * 100
                changes.append(change)

        # Classify volatility
        if cv:
            if cv < 10:
                volatility_class = 'very_stable'
            elif cv < 20:
                volatility_class = 'stable'
            elif cv < 30:
                volatility_class = 'moderate'
            elif cv < 50:
                volatility_class = 'volatile'
            else:
                volatility_class = 'highly_volatile'
        else:
            volatility_class = 'undefined'

        return {
            'ticker': ticker,
            'metric_name': metric_name,
            'mean': mean_val,
            'std_deviation': std_dev,
            'coefficient_of_variation': cv,
            'volatility_classification': volatility_class,
            'max_value': max(values),
            'min_value': min(values),
            'range': max(values) - min(values),
            'avg_period_change': np.mean(np.abs(changes)) if changes else None,
            'periods_analyzed': len(values)
        }