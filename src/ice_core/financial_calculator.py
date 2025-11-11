# Location: /src/ice_core/financial_calculator.py
# Purpose: Deterministic financial metric calculations with full audit trail
# Why: Provide fallback calculations when pre-extracted MARGIN tags unavailable
# Relevant Files: ice_query_processor.py, enhanced_doc_creator.py

import logging
from typing import Dict, Optional, Any
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class FinancialCalculator:
    """
    Deterministic financial metric calculations for ICE.

    Provides accurate, auditable calculations as fallback when pre-extracted
    margin tags are unavailable. All calculations use Python Decimal for
    precision and include complete audit trail.

    Design Principles:
    1. Deterministic: Same inputs always produce same output
    2. Auditable: Full formula + inputs + sources preserved
    3. Error-safe: Handles edge cases (division by zero, unit mismatches)
    4. Confidence-scored: Lower than retrieval (0.90 vs 0.95) to reflect derivation
    """

    # Standard financial formulas
    FORMULAS = {
        'operating_margin': 'Operating Margin = (Operating Profit / Revenue) × 100',
        'gross_margin': 'Gross Margin = (Gross Profit / Revenue) × 100',
        'net_margin': 'Net Margin = (Net Income / Revenue) × 100',
        'profit_margin': 'Profit Margin = (Net Income / Revenue) × 100',
        'ebitda_margin': 'EBITDA Margin = (EBITDA / Revenue) × 100',
        'return_on_equity': 'ROE = (Net Income / Shareholders Equity) × 100',
        'return_on_assets': 'ROA = (Net Income / Total Assets) × 100',
        'debt_to_equity': 'Debt-to-Equity = Total Debt / Shareholders Equity',
        'current_ratio': 'Current Ratio = Current Assets / Current Liabilities',
        'quick_ratio': 'Quick Ratio = (Current Assets - Inventory) / Current Liabilities'
    }

    def __init__(self, precision: int = 2):
        """
        Initialize calculator with rounding precision.

        Args:
            precision: Decimal places for rounding (default: 2 for percentages)
        """
        self.precision = precision
        self.logger = logger

    def _safe_divide(self, numerator: float, denominator: float) -> Optional[Decimal]:
        """
        Safe division with error handling.

        Args:
            numerator: Top value
            denominator: Bottom value

        Returns:
            Decimal result or None if division invalid
        """
        if denominator == 0:
            self.logger.warning(f"Division by zero: {numerator} / {denominator}")
            return None

        try:
            # Use Decimal for precision
            num = Decimal(str(numerator))
            den = Decimal(str(denominator))
            result = num / den
            return result
        except Exception as e:
            self.logger.error(f"Division error: {numerator} / {denominator} - {e}")
            return None

    def _format_result(
        self,
        value: Optional[Decimal],
        formula_key: str,
        inputs: Dict[str, Any],
        unit: str = '%'
    ) -> Dict[str, Any]:
        """
        Format calculation result with full audit trail.

        Args:
            value: Calculated value (Decimal or None if error)
            formula_key: Key to lookup formula in FORMULAS dict
            inputs: Input metrics used in calculation
            unit: Unit of result (% for margins, ratio for others)

        Returns:
            Standardized result dict with value, formula, inputs, confidence
        """
        if value is None:
            return {
                'error': 'Calculation failed',
                'formula': self.FORMULAS.get(formula_key, 'Unknown'),
                'inputs': inputs,
                'confidence': 0.0
            }

        # Round to specified precision
        rounded_value = value.quantize(
            Decimal('0.1') ** self.precision,
            rounding=ROUND_HALF_UP
        )

        return {
            'value': float(rounded_value),
            'formula': self.FORMULAS[formula_key],
            'inputs': inputs,
            'confidence': 0.90,  # High confidence (deterministic) but lower than retrieval
            'method': 'calculated',
            'unit': unit,
            'precision': self.precision
        }

    def calculate_operating_margin(
        self,
        operating_profit: float,
        revenue: float,
        sources: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate operating margin percentage.

        Formula: Operating Margin = (Operating Profit / Revenue) × 100

        Args:
            operating_profit: Operating profit value (any currency)
            revenue: Total revenue (same currency as operating_profit)
            sources: Optional dict with source attribution for inputs

        Returns:
            Dict with calculated margin, formula, inputs, confidence

        Example:
            >>> calc = FinancialCalculator()
            >>> result = calc.calculate_operating_margin(69.2, 184.5)
            >>> result['value']
            37.50
            >>> result['formula']
            'Operating Margin = (Operating Profit / Revenue) × 100'
        """
        # Calculate margin percentage
        margin_decimal = self._safe_divide(operating_profit, revenue)

        if margin_decimal is None:
            return self._format_result(None, 'operating_margin', {
                'operating_profit': operating_profit,
                'revenue': revenue,
                'sources': sources or {}
            })

        margin_pct = margin_decimal * 100

        return self._format_result(
            margin_pct,
            'operating_margin',
            {
                'operating_profit': operating_profit,
                'revenue': revenue,
                'sources': sources or {}
            },
            unit='%'
        )

    def calculate_gross_margin(
        self,
        gross_profit: float,
        revenue: float,
        sources: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Calculate gross margin percentage."""
        margin_decimal = self._safe_divide(gross_profit, revenue)

        if margin_decimal is None:
            return self._format_result(None, 'gross_margin', {
                'gross_profit': gross_profit,
                'revenue': revenue,
                'sources': sources or {}
            })

        margin_pct = margin_decimal * 100

        return self._format_result(
            margin_pct,
            'gross_margin',
            {
                'gross_profit': gross_profit,
                'revenue': revenue,
                'sources': sources or {}
            },
            unit='%'
        )

    def calculate_net_margin(
        self,
        net_income: float,
        revenue: float,
        sources: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Calculate net margin (profit margin) percentage."""
        margin_decimal = self._safe_divide(net_income, revenue)

        if margin_decimal is None:
            return self._format_result(None, 'net_margin', {
                'net_income': net_income,
                'revenue': revenue,
                'sources': sources or {}
            })

        margin_pct = margin_decimal * 100

        return self._format_result(
            margin_pct,
            'net_margin',
            {
                'net_income': net_income,
                'revenue': revenue,
                'sources': sources or {}
            },
            unit='%'
        )

    def calculate_return_on_equity(
        self,
        net_income: float,
        shareholders_equity: float,
        sources: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Calculate return on equity (ROE) percentage."""
        roe_decimal = self._safe_divide(net_income, shareholders_equity)

        if roe_decimal is None:
            return self._format_result(None, 'return_on_equity', {
                'net_income': net_income,
                'shareholders_equity': shareholders_equity,
                'sources': sources or {}
            })

        roe_pct = roe_decimal * 100

        return self._format_result(
            roe_pct,
            'return_on_equity',
            {
                'net_income': net_income,
                'shareholders_equity': shareholders_equity,
                'sources': sources or {}
            },
            unit='%'
        )

    def calculate_debt_to_equity(
        self,
        total_debt: float,
        shareholders_equity: float,
        sources: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Calculate debt-to-equity ratio."""
        ratio = self._safe_divide(total_debt, shareholders_equity)

        if ratio is None:
            return self._format_result(None, 'debt_to_equity', {
                'total_debt': total_debt,
                'shareholders_equity': shareholders_equity,
                'sources': sources or {}
            })

        return self._format_result(
            ratio,
            'debt_to_equity',
            {
                'total_debt': total_debt,
                'shareholders_equity': shareholders_equity,
                'sources': sources or {}
            },
            unit='ratio'
        )


# Convenience functions for common calculations

def calculate_margin(numerator: float, denominator: float, margin_type: str = 'operating') -> Dict[str, Any]:
    """
    Convenience function for margin calculations.

    Args:
        numerator: Profit metric (operating profit, gross profit, net income)
        denominator: Revenue
        margin_type: Type of margin ('operating', 'gross', 'net')

    Returns:
        Calculation result dict
    """
    calc = FinancialCalculator()

    if margin_type == 'operating':
        return calc.calculate_operating_margin(numerator, denominator)
    elif margin_type == 'gross':
        return calc.calculate_gross_margin(numerator, denominator)
    elif margin_type == 'net':
        return calc.calculate_net_margin(numerator, denominator)
    else:
        raise ValueError(f"Unknown margin type: {margin_type}")


# Example usage
if __name__ == '__main__':
    # Test operating margin calculation
    calc = FinancialCalculator()

    result = calc.calculate_operating_margin(
        operating_profit=69.2,  # Billion yuan
        revenue=184.5,          # Billion yuan
        sources={
            'operating_profit': '[TABLE_METRIC:Operating Profit|value:69.2B|ticker:TCEHY|period:2Q2025]',
            'revenue': '[TABLE_METRIC:Total Revenue|value:184.5B|ticker:TCEHY|period:2Q2025]'
        }
    )

    print(f"Operating Margin: {result['value']}%")
    print(f"Formula: {result['formula']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Method: {result['method']}")
