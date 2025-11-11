# Location: updated_architectures/implementation/query_router.py
# Purpose: Smart query router for dual-layer architecture (Signal Store + LightRAG)
# Why: Route structured queries to Signal Store (<1s) and semantic queries to LightRAG (~12s)
# Relevant Files: signal_store.py, ice_simplified.py, data_ingestion.py

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query classification for routing decision"""
    STRUCTURED_RATING = "structured_rating"      # "What's NVDA's latest rating?"
    STRUCTURED_METRIC = "structured_metric"      # "Show NVDA's operating margin"
    STRUCTURED_PRICE = "structured_price"        # "What's the price target for AAPL?"
    SEMANTIC_WHY = "semantic_why"                # "Why did Goldman upgrade NVDA?"
    SEMANTIC_HOW = "semantic_how"                # "How does China risk impact NVDA?"
    SEMANTIC_EXPLAIN = "semantic_explain"        # "Explain the AI chip market dynamics"
    HYBRID = "hybrid"                            # Needs both layers


class QueryRouter:
    """
    Route queries to optimal layer (Signal Store vs LightRAG).

    Design Philosophy:
    - Signal Store (<1s): Structured queries with exact lookups (What/Which/Show)
    - LightRAG (~12s): Semantic queries requiring reasoning (Why/How/Explain)
    - Hybrid: Queries needing both structured data + semantic context

    Routing Strategy:
    1. Pattern matching: Detect query intent from keywords/structure
    2. Confidence scoring: Assign confidence to routing decision
    3. Fallback: Route to LightRAG if uncertain (safe default)

    Performance Target:
    - Router accuracy: ≥95% (measured on labeled test set)
    - Router latency: <50ms (pattern matching only, no LLM)
    - False positive rate: <5% (avoid routing semantic queries to Signal Store)
    """

    # Phase 2: Rating query patterns (only ratings implemented)
    RATING_PATTERNS = [
        r'\b(what|what\'s|whats)\b.*\b(rating|recommendation)\b',
        r'\b(show|list|get)\b.*\b(ratings?|recommendations?)\b',
        r'\b(latest|current|recent)\b.*\b(rating|recommendation)\b',
        r'\brating\b.*\bfor\b.*\b([A-Z]{1,5})\b',  # "rating for NVDA"
        r'\b([A-Z]{1,5})\b.*\brating\b',           # "NVDA rating"
        r'\b(buy|sell|hold)\b.*\b(recommendation|rating)\b'
    ]

    # Phase 3: Metric query patterns (financial metrics from tables)
    METRIC_PATTERNS = [
        # General metric keywords
        r'\b(what|what\'s|whats)\b.*\b(margin|revenue|earnings|eps|profit|sales)\b',
        r'\b(show|list|get)\b.*\b(margin|revenue|earnings|eps|profit|sales)\b',

        # Specific financial metrics
        r'\b(operating|gross|net)\b.*\bmargin\b',
        r'\b(revenue|earnings|profit)\b.*\b(growth|yoy|qoq)\b',
        r'\bearnings per share\b',
        r'\beps\b',

        # Comparative patterns
        r'\bcompare\b.*\b(margin|revenue|earnings)\b',
        r'\b(margin|revenue|earnings)\b.*\b(vs|versus|compared to)\b',

        # Temporal patterns
        r'\b(q1|q2|q3|q4|quarterly|annual|fy|ttm)\b.*\b(margin|revenue|earnings)\b',
        r'\b(margin|revenue|earnings)\b.*\b(q1|q2|q3|q4|quarterly|annual|fy|ttm)\b',

        # Threshold patterns (computational queries)
        r'\b(margin|revenue|earnings)\b.*\b(above|below|greater|less|over|under)\b',
        r'\b(margin|revenue|earnings)\b.*\b>\b',
        r'\b(margin|revenue|earnings)\b.*\b<\b'
    ]

    # Semantic query patterns (route to LightRAG)
    SEMANTIC_WHY_PATTERNS = [
        r'\bwhy\b',
        r'\breason\b.*\bfor\b',
        r'\bexplain\b.*\bwhy\b'
    ]

    SEMANTIC_HOW_PATTERNS = [
        r'\bhow\b.*\bimpact\b',
        r'\bhow\b.*\baffect\b',
        r'\bhow\b.*\binfluence\b'
    ]

    SEMANTIC_EXPLAIN_PATTERNS = [
        r'\bexplain\b',
        r'\bdescribe\b',
        r'\bsummarize\b',
        r'\bwhat are the\b.*\bfactors\b'
    ]

    def __init__(self, signal_store: Optional[Any] = None):
        """
        Initialize query router.

        Args:
            signal_store: SignalStore instance (if enabled)
        """
        self.signal_store = signal_store
        self.logger = logging.getLogger(__name__)

    def route_query(self, query: str) -> Tuple[QueryType, float]:
        """
        Classify query and determine routing layer.

        Args:
            query: User query string

        Returns:
            Tuple of (QueryType, confidence_score)
            - QueryType: Enum indicating query classification
            - confidence_score: 0.0-1.0 indicating routing confidence

        Examples:
            >>> route_query("What's NVDA's latest rating?")
            (QueryType.STRUCTURED_RATING, 0.95)

            >>> route_query("Why did Goldman upgrade NVDA?")
            (QueryType.SEMANTIC_WHY, 0.90)

            >>> route_query("How does NVDA's rating compare to industry?")
            (QueryType.HYBRID, 0.85)
        """
        query_lower = query.lower()

        # Check for structured patterns (Phase 2 + Phase 3)
        has_rating_pattern = self.signal_store and any(
            re.search(p, query_lower) for p in self.RATING_PATTERNS
        )
        has_metric_pattern = self.signal_store and any(
            re.search(p, query_lower) for p in self.METRIC_PATTERNS
        )

        # Check for semantic patterns
        has_why_pattern = any(re.search(p, query_lower) for p in self.SEMANTIC_WHY_PATTERNS)
        has_how_pattern = any(re.search(p, query_lower) for p in self.SEMANTIC_HOW_PATTERNS)
        has_explain_pattern = any(re.search(p, query_lower) for p in self.SEMANTIC_EXPLAIN_PATTERNS)

        has_semantic = has_why_pattern or has_how_pattern or has_explain_pattern
        has_structured = has_rating_pattern or has_metric_pattern

        # Priority 1: Hybrid queries (both structured AND semantic keywords)
        if has_structured and has_semantic:
            return (QueryType.HYBRID, 0.85)

        # Priority 2: Pure semantic queries (route to LightRAG)
        if has_why_pattern:
            return (QueryType.SEMANTIC_WHY, 0.90)
        if has_how_pattern:
            return (QueryType.SEMANTIC_HOW, 0.90)
        if has_explain_pattern:
            return (QueryType.SEMANTIC_EXPLAIN, 0.85)

        # Priority 3: Pure structured queries (route to Signal Store)
        if has_rating_pattern:
            return (QueryType.STRUCTURED_RATING, 0.90)
        if has_metric_pattern:
            return (QueryType.STRUCTURED_METRIC, 0.90)

        # Default: Route to LightRAG (safe fallback for uncertain queries)
        return (QueryType.SEMANTIC_EXPLAIN, 0.50)

    def should_use_signal_store(self, query_type: QueryType) -> bool:
        """
        Determine if Signal Store should be used for this query type.

        Args:
            query_type: QueryType enum

        Returns:
            True if Signal Store should be used (exclusively or as part of hybrid)
        """
        return query_type in (
            QueryType.STRUCTURED_RATING,
            QueryType.STRUCTURED_METRIC,
            QueryType.STRUCTURED_PRICE,
            QueryType.HYBRID
        )

    def should_use_lightrag(self, query_type: QueryType) -> bool:
        """
        Determine if LightRAG should be used for this query type.

        Args:
            query_type: QueryType enum

        Returns:
            True if LightRAG should be used (exclusively or as part of hybrid)
        """
        return query_type in (
            QueryType.SEMANTIC_WHY,
            QueryType.SEMANTIC_HOW,
            QueryType.SEMANTIC_EXPLAIN,
            QueryType.HYBRID
        )

    def extract_ticker(self, query: str) -> Optional[str]:
        """
        Extract ticker symbol from query.

        Args:
            query: User query string

        Returns:
            Ticker symbol (uppercase) or None if not found

        Examples:
            >>> extract_ticker("What's NVDA's latest rating?")
            'NVDA'

            >>> extract_ticker("Show me Apple's recommendation")
            None  # Company name, not ticker
        """
        # Match 1-5 uppercase letters (typical ticker format)
        # Avoid matching common English words (THE, FOR, etc.)
        ticker_pattern = r'\b([A-Z]{2,5})\b'
        matches = re.findall(ticker_pattern, query)

        # Filter out common English words
        common_words = {'THE', 'FOR', 'AND', 'BUT', 'NOT', 'ARE', 'WAS', 'WERE'}
        valid_tickers = [m for m in matches if m not in common_words]

        return valid_tickers[0] if valid_tickers else None

    def extract_metric_info(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract metric type and period from query.

        Args:
            query: User query string

        Returns:
            Tuple of (metric_type, period) or (None, None) if not found

        Examples:
            >>> extract_metric_info("What's NVDA's operating margin?")
            ('Operating Margin', None)

            >>> extract_metric_info("Show me Q2 2024 revenue for AAPL")
            ('Revenue', 'Q2 2024')

            >>> extract_metric_info("What's the gross margin in FY2024?")
            ('Gross Margin', 'FY2024')
        """
        query_lower = query.lower()
        metric_type = None
        period = None

        # Extract metric type
        metric_keywords = {
            'operating margin': 'Operating Margin',
            'gross margin': 'Gross Margin',
            'net margin': 'Net Margin',
            'profit margin': 'Profit Margin',
            'revenue': 'Revenue',
            'earnings': 'Earnings',
            'eps': 'EPS',
            'earnings per share': 'EPS',
            'profit': 'Profit',
            'sales': 'Sales'
        }

        for keyword, normalized_name in metric_keywords.items():
            if keyword in query_lower:
                metric_type = normalized_name
                break

        # Extract period (quarterly, annual, specific quarters)
        period_patterns = [
            (r'\b(q[1-4]\s+\d{4})\b', 'Q{} {}'),  # Q2 2024
            (r'\b(fy\s*\d{4})\b', 'FY{}'),        # FY2024
            (r'\b(ttm)\b', 'TTM'),                 # Trailing Twelve Months
            (r'\b(quarterly)\b', 'Quarterly'),     # Generic quarterly
            (r'\b(annual)\b', 'Annual')            # Generic annual
        ]

        for pattern, _ in period_patterns:
            match = re.search(pattern, query_lower)
            if match:
                period = match.group(1).upper()
                # Normalize format
                if 'Q' in period and len(period.split()) == 2:
                    q, year = period.split()
                    period = f"{q} {year}"
                elif 'FY' in period:
                    period = period.replace(' ', '')
                break

        return (metric_type, period)

    def format_signal_store_result(
        self,
        signal_store_data: Optional[Dict[str, Any]],
        query: str
    ) -> str:
        """
        Format Signal Store query result for user display.

        Args:
            signal_store_data: Data from Signal Store query (or None if not found)
            query: Original user query

        Returns:
            Formatted response string

        Examples:
            >>> format_signal_store_result({'ticker': 'NVDA', 'rating': 'BUY', ...}, "What's NVDA's rating?")
            "NVDA Latest Rating: BUY\\nFirm: Goldman Sachs\\nAnalyst: John Doe\\nConfidence: 0.87\\nTimestamp: 2024-03-15T10:30:00Z"
        """
        if not signal_store_data:
            return f"No Signal Store data found for query: {query}"

        # Format based on data type
        if 'rating' in signal_store_data:
            # Rating query result
            lines = [
                f"{signal_store_data['ticker']} Latest Rating: {signal_store_data['rating']}"
            ]

            if signal_store_data.get('firm'):
                lines.append(f"Firm: {signal_store_data['firm']}")
            if signal_store_data.get('analyst'):
                lines.append(f"Analyst: {signal_store_data['analyst']}")
            if signal_store_data.get('confidence'):
                lines.append(f"Confidence: {signal_store_data['confidence']:.2f}")
            if signal_store_data.get('timestamp'):
                lines.append(f"Timestamp: {signal_store_data['timestamp']}")

            return "\n".join(lines)

        elif 'metric_type' in signal_store_data:
            # Metric query result
            lines = [
                f"{signal_store_data['ticker']} {signal_store_data['metric_type']}: {signal_store_data['metric_value']}"
            ]

            if signal_store_data.get('period'):
                lines.append(f"Period: {signal_store_data['period']}")
            if signal_store_data.get('confidence'):
                lines.append(f"Confidence: {signal_store_data['confidence']:.2f}")
            if signal_store_data.get('source_document_id'):
                lines.append(f"Source: {signal_store_data['source_document_id']}")

            return "\n".join(lines)

        # Generic fallback
        return str(signal_store_data)
