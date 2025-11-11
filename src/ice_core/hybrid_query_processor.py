# Location: /src/ice_core/hybrid_query_processor.py
# Purpose: Hybrid query processor with retrieval-first + tool-augmented fallback
# Why: Combine transparency of Solution 2 with determinism of Solution 3
# Relevant Files: financial_calculator.py, ice_query_processor.py

import logging
import re
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

from src.ice_core.financial_calculator import FinancialCalculator

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Standardized query result with method transparency."""
    answer: str
    method: str  # 'retrieved' or 'calculated'
    confidence: float
    sources: List[str]
    metadata: Dict[str, Any]


class HybridQueryProcessor:
    """
    Hybrid query processor combining retrieval-first with tool-augmented fallback.

    Architecture:
    1. Attempt retrieval from graph (MARGIN tags, TABLE_METRIC tags)
    2. If not found, extract component metrics
    3. Use FinancialCalculator for deterministic calculation
    4. Return unified response with method transparency

    Design Principles (Solution 2 + 3):
    - Prefer retrieval (fast, high confidence, source-attributed)
    - Fallback to calculation (deterministic, auditable, accurate)
    - Full transparency (user knows method used)
    - Consistent output format (same structure regardless of method)
    """

    def __init__(self, rag, calculator: Optional[FinancialCalculator] = None):
        """
        Initialize hybrid processor.

        Args:
            rag: LightRAG instance for graph queries
            calculator: FinancialCalculator instance (creates default if None)
        """
        self.rag = rag
        self.calculator = calculator or FinancialCalculator()
        self.logger = logger

    def query_margin(
        self,
        ticker: str,
        period: str,
        margin_type: str = 'operating'
    ) -> QueryResult:
        """
        Query margin with retrieval-first + calculation fallback.

        Args:
            ticker: Company ticker (e.g., 'TCEHY', 'NVDA')
            period: Time period (e.g., '2Q2025', 'Q2 2024')
            margin_type: Type of margin ('operating', 'gross', 'net')

        Returns:
            QueryResult with answer, method, confidence, sources

        Example:
            >>> processor = HybridQueryProcessor(rag)
            >>> result = processor.query_margin('TCEHY', '2Q2025', 'operating')
            >>> result.answer
            "37.5%"
            >>> result.method
            "retrieved"  # or "calculated" if MARGIN tag not found
        """
        # Normalize inputs
        ticker = ticker.upper()
        period_normalized = self._normalize_period(period)

        # Step 1: Attempt retrieval from MARGIN tags
        retrieved_result = self._attempt_retrieval(ticker, period_normalized, margin_type)

        if retrieved_result:
            self.logger.info(f"[RETRIEVED] {margin_type} margin for {ticker} {period_normalized}")
            return retrieved_result

        # Step 2: Retrieval failed, attempt calculation
        self.logger.info(f"[CALCULATING] {margin_type} margin for {ticker} {period_normalized}")
        calculated_result = self._attempt_calculation(ticker, period_normalized, margin_type)

        if calculated_result:
            return calculated_result

        # Step 3: Both retrieval and calculation failed
        return QueryResult(
            answer="I do not have enough information to answer this query.",
            method="failed",
            confidence=0.0,
            sources=[],
            metadata={'error': 'No data found for retrieval or calculation'}
        )

    def _attempt_retrieval(
        self,
        ticker: str,
        period: str,
        margin_type: str
    ) -> Optional[QueryResult]:
        """
        Attempt to retrieve margin from MARGIN tags in graph.

        Args:
            ticker: Company ticker
            period: Normalized period
            margin_type: Type of margin

        Returns:
            QueryResult if found, None if not found
        """
        # Construct query for LightRAG
        query = f"What is the {margin_type} margin for {ticker} in {period}?"

        try:
            # Query graph
            result = self.rag.query(query, param={'mode': 'hybrid'})

            # Check if result contains MARGIN tag
            margin_tag_pattern = rf'\[MARGIN:{margin_type.title()} Margin\|value:([^\|]+)\|period:{period}\|ticker:{ticker}\|confidence:([\d.]+)\]'
            match = re.search(margin_tag_pattern, result, re.IGNORECASE)

            if match:
                value = match.group(1)
                confidence = float(match.group(2))

                return QueryResult(
                    answer=value,
                    method='retrieved',
                    confidence=confidence,
                    sources=[f"[MARGIN:{margin_type.title()} Margin|value:{value}|period:{period}|ticker:{ticker}]"],
                    metadata={
                        'margin_type': margin_type,
                        'ticker': ticker,
                        'period': period,
                        'raw_result': result
                    }
                )

            # No MARGIN tag found
            return None

        except Exception as e:
            self.logger.error(f"Retrieval error: {e}")
            return None

    def _attempt_calculation(
        self,
        ticker: str,
        period: str,
        margin_type: str
    ) -> Optional[QueryResult]:
        """
        Calculate margin from component metrics using FinancialCalculator.

        Args:
            ticker: Company ticker
            period: Normalized period
            margin_type: Type of margin

        Returns:
            QueryResult if calculation successful, None if failed
        """
        # Step 1: Extract component metrics from graph
        components = self._extract_components(ticker, period, margin_type)

        if not components or 'numerator' not in components or 'denominator' not in components:
            self.logger.warning(f"Missing components for {margin_type} margin calculation")
            return None

        # Step 2: Perform deterministic calculation
        try:
            if margin_type == 'operating':
                calc_result = self.calculator.calculate_operating_margin(
                    operating_profit=components['numerator']['value'],
                    revenue=components['denominator']['value'],
                    sources={
                        'operating_profit': components['numerator']['source'],
                        'revenue': components['denominator']['source']
                    }
                )
            elif margin_type == 'gross':
                calc_result = self.calculator.calculate_gross_margin(
                    gross_profit=components['numerator']['value'],
                    revenue=components['denominator']['value'],
                    sources={
                        'gross_profit': components['numerator']['source'],
                        'revenue': components['denominator']['source']
                    }
                )
            elif margin_type == 'net':
                calc_result = self.calculator.calculate_net_margin(
                    net_income=components['numerator']['value'],
                    revenue=components['denominator']['value'],
                    sources={
                        'net_income': components['numerator']['source'],
                        'revenue': components['denominator']['source']
                    }
                )
            else:
                return None

            # Check if calculation succeeded
            if 'error' in calc_result:
                self.logger.error(f"Calculation failed: {calc_result['error']}")
                return None

            # Format answer with transparency
            answer = f"{calc_result['value']}{calc_result['unit']}"

            return QueryResult(
                answer=answer,
                method='calculated',
                confidence=calc_result['confidence'],
                sources=[
                    components['numerator']['source'],
                    components['denominator']['source']
                ],
                metadata={
                    'formula': calc_result['formula'],
                    'inputs': calc_result['inputs'],
                    'margin_type': margin_type,
                    'ticker': ticker,
                    'period': period
                }
            )

        except Exception as e:
            self.logger.error(f"Calculation error: {e}")
            return None

    def _extract_components(
        self,
        ticker: str,
        period: str,
        margin_type: str
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Extract component metrics (numerator, denominator) from graph.

        Args:
            ticker: Company ticker
            period: Period
            margin_type: Type of margin

        Returns:
            Dict with numerator and denominator info, or None if not found
        """
        # Map margin type to required components
        component_map = {
            'operating': {
                'numerator': 'Operating Profit',
                'denominator': 'Total Revenue'
            },
            'gross': {
                'numerator': 'Gross Profit',
                'denominator': 'Total Revenue'
            },
            'net': {
                'numerator': 'Net Income',
                'denominator': 'Total Revenue'
            }
        }

        if margin_type not in component_map:
            return None

        required = component_map[margin_type]

        # Extract numerator
        numerator_query = f"What is the {required['numerator']} for {ticker} in {period}?"
        numerator_result = self.rag.query(numerator_query, param={'mode': 'hybrid'})

        # Extract denominator
        denominator_query = f"What is the {required['denominator']} for {ticker} in {period}?"
        denominator_result = self.rag.query(denominator_query, param={'mode': 'hybrid'})

        # Parse TABLE_METRIC tags to extract values
        numerator_value = self._parse_metric_value(numerator_result, required['numerator'])
        denominator_value = self._parse_metric_value(denominator_result, required['denominator'])

        if numerator_value is None or denominator_value is None:
            return None

        return {
            'numerator': {
                'value': numerator_value,
                'source': f"[TABLE_METRIC:{required['numerator']}|ticker:{ticker}|period:{period}]"
            },
            'denominator': {
                'value': denominator_value,
                'source': f"[TABLE_METRIC:{required['denominator']}|ticker:{ticker}|period:{period}]"
            }
        }

    def _parse_metric_value(self, result: str, metric_name: str) -> Optional[float]:
        """
        Parse numeric value from TABLE_METRIC tag or natural language.

        Args:
            result: LightRAG query result
            metric_name: Name of metric to extract

        Returns:
            Float value or None if not found
        """
        # Try to find TABLE_METRIC tag
        tag_pattern = rf'\[TABLE_METRIC:{metric_name}\|value:([^\|]+)\|'
        match = re.search(tag_pattern, result, re.IGNORECASE)

        if match:
            value_str = match.group(1)
            # Remove units (B, M, billion, million, etc.)
            value_clean = re.sub(r'[BMK]|billion|million', '', value_str, flags=re.IGNORECASE).strip()
            try:
                return float(value_clean)
            except ValueError:
                pass

        # Fallback: extract from natural language
        # Pattern: "69.2 billion" or "69.2B" or just "69.2"
        number_pattern = r'([\d,.]+)\s*(?:billion|B|million|M)?'
        matches = re.findall(number_pattern, result)

        if matches:
            try:
                return float(matches[0].replace(',', ''))
            except ValueError:
                pass

        return None

    def _normalize_period(self, period: str) -> str:
        """
        Normalize period format.

        Args:
            period: Period string (e.g., 'Q2 2025', '2Q2025', 'Q2 2024')

        Returns:
            Normalized period (e.g., '2Q2025')
        """
        # Remove spaces
        period = period.replace(' ', '')

        # Convert 'Q2 2025' to '2Q2025'
        match = re.match(r'Q(\d)(\d{4})', period, re.IGNORECASE)
        if match:
            return f"{match.group(1)}Q{match.group(2)}"

        return period


# Example usage
if __name__ == '__main__':
    # Mock LightRAG for testing
    class MockRAG:
        def query(self, query, param=None):
            # Simulate graph response with MARGIN tag
            if 'operating margin' in query.lower():
                return "[MARGIN:Operating Margin|value:37.5%|period:2Q2025|ticker:TCEHY|confidence:0.95]"
            return "No data found"

    # Test hybrid processor
    rag = MockRAG()
    processor = HybridQueryProcessor(rag)

    result = processor.query_margin('TCEHY', '2Q2025', 'operating')
    print(f"Answer: {result.answer}")
    print(f"Method: {result.method}")
    print(f"Confidence: {result.confidence}")
    print(f"Sources: {result.sources}")
