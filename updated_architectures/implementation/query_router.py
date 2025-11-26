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
    STRUCTURED_RATING = "structured_rating"          # "What's NVDA's latest rating?"
    STRUCTURED_METRIC = "structured_metric"          # "Show NVDA's operating margin"
    STRUCTURED_PRICE = "structured_price"            # "What's the price target for AAPL?"
    STRUCTURED_PRICING_HISTORY = "structured_pricing_history"  # "Show NVDA's 52-week high"
    STRUCTURED_CALENDAR = "structured_calendar"      # "When is NVDA's next earnings?"
    SEMANTIC_WHY = "semantic_why"                    # "Why did Goldman upgrade NVDA?"
    SEMANTIC_HOW = "semantic_how"                    # "How does China risk impact NVDA?"
    SEMANTIC_EXPLAIN = "semantic_explain"            # "Explain the AI chip market dynamics"
    HYBRID = "hybrid"                                # Needs both layers


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

    # Phase 3: Metric query patterns (enhanced for Categories 1 & 4 - financial metrics)
    METRIC_PATTERNS = [
        # General metric keywords
        r'\b(what|what\'s|whats)\b.*\b(margin|revenue|earnings|eps|profit|sales|beta|roe|roa)\b',
        r'\b(show|list|get)\b.*\b(margin|revenue|earnings|eps|profit|sales|beta|roe|roa)\b',

        # Specific financial metrics (Category 4: Income/Balance/Cash Flow)
        r'\b(operating|gross|net)\b.*\bmargin\b',
        r'\b(revenue|earnings|profit)\b.*\b(growth|yoy|qoq)\b',
        r'\bearnings per share\b',
        r'\beps\b',
        r'\b(total\s+)?(assets|liabilities|equity)\b',
        r'\bcash\s+flow\b',
        r'\bcapital\s+expenditure\b',
        r'\bcapex\b',

        # Risk metrics (Category 1: Market Data enhancements)
        r'\bbeta\b',
        r'\bshort\s+(interest|percent|ratio)\b',
        r'\bfloat\b.*\bshares\b',
        r'\breturn\s+on\s+(assets|equity)\b',
        r'\b(roe|roa)\b',
        r'\bdebt\s+to\s+equity\b',
        r'\bd/e\b.*\bratio\b',

        # Comparative patterns
        r'\bcompare\b.*\b(margin|revenue|earnings|beta|roe|roa)\b',
        r'\b(margin|revenue|earnings|beta|roe|roa)\b.*\b(vs|versus|compared to)\b',

        # Temporal patterns
        r'\b(q1|q2|q3|q4|quarterly|annual|fy|ttm)\b.*\b(margin|revenue|earnings)\b',
        r'\b(margin|revenue|earnings)\b.*\b(q1|q2|q3|q4|quarterly|annual|fy|ttm)\b',

        # Threshold patterns (computational queries)
        r'\b(margin|revenue|earnings|beta|roe|roa)\b.*\b(above|below|greater|less|over|under)\b',
        r'\b(margin|revenue|earnings|beta|roe|roa)\b.*\b>\b',
        r'\b(margin|revenue|earnings|beta|roe|roa)\b.*\b<\b'
    ]

    # Phase 4: Historical pricing patterns (Category 6 - OHLCV time-series)
    PRICING_HISTORY_PATTERNS = [
        # Price movement queries
        r'\b(price|stock)\b.*\b(history|historical|trend|performance)\b',
        r'\b(52\s*week|one\s*year|ytd)\b.*\b(high|low|range|performance)\b',
        r'\b(ohlc|ohlcv|candlestick)\b',

        # Specific price metrics
        r'\b(opening|closing|high|low)\b.*\bprice\b',
        r'\bprice\b.*\b(open|close|high|low)\b',
        r'\bvolume\b.*\b(history|trend|average)\b',

        # Temporal price queries
        r'\bprice\b.*\b(last\s+(week|month|quarter|year)|ytd|mtd)\b',
        r'\b(daily|weekly|monthly)\b.*\bprice\b',

        # Price comparison
        r'\bprice\b.*\b(above|below|over|under)\b',
        r'\b(rallied|dropped|gained|lost)\b.*\b(percent|%|points)\b'
    ]

    # Phase 4b: Price target patterns (analyst consensus price targets)
    PRICE_TARGET_PATTERNS = [
        # Direct price target queries
        r'\b(price\s*target|target\s*price)\b',
        r'\b(analyst|consensus)\b.*\bprice\b',
        r'\bwhat.*price.*target\b',
        r'\btarget\b.*\b(for|on)\b.*\b[A-Z]{1,5}\b',

        # Analyst valuation queries
        r'\b(analysts?|consensus)\b.*\b(valuation|target|estimate)\b',
        r'\bfair\s*value\b',
        r'\bprice\b.*\bestimate\b'
    ]

    # Phase 5: Calendar event patterns (Category 7 - Earnings/Dividend calendar)
    # NOTE: Order matters - calendar checked before metrics to handle "earnings" keyword overlap
    CALENDAR_EVENT_PATTERNS = [
        # Earnings date queries
        r'\b(when|what)\b.*\b(earnings|earnings\s+date|earnings\s+call)\b',
        r'\bnext\b.*\bearnings\b',
        r'\bearnings\b.*\b(schedule|calendar|upcoming|date)\b',
        r'\b(upcoming|future|show)\b.*\bearnings\b',  # "upcoming earnings", "show earnings"

        # Dividend date queries
        r'\b(when|what)\b.*\b(dividend|dividend\s+date|ex-dividend)\b',
        r'\bnext\b.*\bdividend\b',
        r'\bdividend\b.*\b(schedule|calendar|upcoming|date)\b',
        r'\b(upcoming|future|show)\b.*\bdividend\b',  # "upcoming dividend", "show dividend"

        # General calendar queries
        r'\b(upcoming|future)\b.*\b(events|dates)\b',
        r'\b(earnings|dividend)\b.*\b(this\s+(week|month|quarter))\b',

        # Schedule-based queries
        r'\bearnings\s+schedule\b',
        r'\bdividend\s+schedule\b',
        r'\bearnings\s+calendar\b',
        r'\bdividend\s+calendar\b'
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
        self.company_aliases = self._load_company_aliases()

    def _load_company_aliases(self) -> Dict[str, str]:
        """Load company name → ticker mappings from config file"""
        import json
        from pathlib import Path

        try:
            config_path = Path(__file__).parent / 'config' / 'company_aliases.json'
            with open(config_path, 'r') as f:
                aliases = json.load(f)
            # Filter out comment keys
            return {k: v for k, v in aliases.items() if not k.startswith('_')}
        except Exception as e:
            logger.warning(f"Could not load company aliases: {e}")
            return {}

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

        # Check for structured patterns (Phases 2-5)
        has_rating_pattern = self.signal_store and any(
            re.search(p, query_lower) for p in self.RATING_PATTERNS
        )
        has_metric_pattern = self.signal_store and any(
            re.search(p, query_lower) for p in self.METRIC_PATTERNS
        )
        has_pricing_history_pattern = self.signal_store and any(
            re.search(p, query_lower) for p in self.PRICING_HISTORY_PATTERNS
        )
        has_price_target_pattern = self.signal_store and any(
            re.search(p, query_lower) for p in self.PRICE_TARGET_PATTERNS
        )
        has_calendar_pattern = self.signal_store and any(
            re.search(p, query_lower) for p in self.CALENDAR_EVENT_PATTERNS
        )

        # Check for semantic patterns
        has_why_pattern = any(re.search(p, query_lower) for p in self.SEMANTIC_WHY_PATTERNS)
        has_how_pattern = any(re.search(p, query_lower) for p in self.SEMANTIC_HOW_PATTERNS)
        has_explain_pattern = any(re.search(p, query_lower) for p in self.SEMANTIC_EXPLAIN_PATTERNS)

        has_semantic = has_why_pattern or has_how_pattern or has_explain_pattern
        has_structured = has_rating_pattern or has_metric_pattern or has_pricing_history_pattern or has_price_target_pattern or has_calendar_pattern

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
        # NOTE: Calendar patterns checked BEFORE metrics because they're more specific
        # (calendar queries ask about dates/schedule, not values, but may contain "earnings")
        if has_rating_pattern:
            return (QueryType.STRUCTURED_RATING, 0.90)
        if has_calendar_pattern:
            return (QueryType.STRUCTURED_CALENDAR, 0.90)
        if has_price_target_pattern:
            return (QueryType.STRUCTURED_PRICE, 0.90)
        if has_metric_pattern:
            return (QueryType.STRUCTURED_METRIC, 0.90)
        if has_pricing_history_pattern:
            return (QueryType.STRUCTURED_PRICING_HISTORY, 0.90)

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
            QueryType.STRUCTURED_PRICING_HISTORY,
            QueryType.STRUCTURED_CALENDAR,
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

    def extract_tickers(self, query: str) -> List[str]:
        """
        Extract ALL ticker symbols from query (multi-ticker support with company name resolution).

        Args:
            query: User query string

        Returns:
            List of ticker symbols found (may be empty)

        Examples:
            >>> extract_tickers("What's NVDA's latest rating?")
            ['NVDA']

            >>> extract_tickers("Compare NVDA and AMD")
            ['NVDA', 'AMD']

            >>> extract_tickers("Show me Apple's recommendation")
            ['AAPL']  # Phase 2: Company name resolution works

            >>> extract_tickers("Compare Apple and Microsoft")
            ['AAPL', 'MSFT']
        """
        tickers = set()

        # Step 1: Extract explicit ticker symbols (uppercase regex)
        ticker_pattern = r'\b([A-Z]{2,5}(?:\.[A-Z]{1,2})?)\b'
        matches = re.findall(ticker_pattern, query)

        # Filter out common English words
        common_words = {'THE', 'FOR', 'AND', 'BUT', 'NOT', 'ARE', 'WAS', 'WERE',
                        'CEO', 'CFO', 'CTO', 'IPO', 'USA', 'NYSE', 'SEC', 'ETF'}
        tickers.update(m for m in matches if m not in common_words)

        # Step 2: Resolve company names to tickers
        if self.company_aliases:
            query_lower = query.lower()
            for company_name, ticker in self.company_aliases.items():
                if company_name in query_lower:
                    tickers.add(ticker)

        # Step 3: Remove duplicates while preserving order (tickers from regex first)
        seen = set()
        result = []
        for ticker in list(tickers):
            if ticker not in seen:
                seen.add(ticker)
                result.append(ticker)

        return result

    def extract_ticker(self, query: str) -> Optional[str]:
        """
        DEPRECATED: Use extract_tickers() for multi-ticker support.

        Extract single ticker symbol from query (returns first match only).

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
        tickers = self.extract_tickers(query)
        return tickers[0] if tickers else None

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

    def extract_event_info(self, query: str) -> Tuple[Optional[str], Optional[bool]]:
        """
        Extract event type and temporal direction from calendar query.

        Phase 2.7B Option 5: Parses calendar event queries to extract structured
        parameters for Signal Store lookup.

        Args:
            query: User query string

        Returns:
            Tuple of (event_type, is_future):
            - event_type: 'earnings', 'dividend', 'ex-dividend', or None
            - is_future: True (upcoming), False (past), None (both)

        Examples:
            >>> extract_event_info("When is NVDA's next earnings?")
            ('earnings', True)

            >>> extract_event_info("Show AAPL's last dividend date")
            ('dividend', False)

            >>> extract_event_info("What events are coming for MSFT?")
            (None, True)
        """
        query_lower = query.lower()

        # Detect event type
        event_type = None
        if any(w in query_lower for w in ['earning', 'earnings']):
            event_type = 'earnings'
        elif 'ex-dividend' in query_lower or 'ex dividend' in query_lower:
            event_type = 'ex-dividend'
        elif 'dividend' in query_lower:
            event_type = 'dividend'

        # Detect temporal direction
        is_future = None
        future_keywords = ['next', 'upcoming', 'future', 'when is', 'when are', 'coming']
        past_keywords = ['last', 'previous', 'past', 'recent', 'was']

        if any(w in query_lower for w in future_keywords):
            is_future = True
        elif any(w in query_lower for w in past_keywords):
            is_future = False

        return (event_type, is_future)

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

    def format_calendar_result(
        self,
        calendar_data: Dict[str, Any],
        query: str
    ) -> str:
        """
        Format calendar event query result for human-readable output.

        Phase 2.7B Option 5: Formats calendar events from Signal Store
        for user display.

        Args:
            calendar_data: Data from query_calendar_events()
            query: Original user query

        Returns:
            Formatted response string with calendar events

        Examples:
            >>> format_calendar_result({'ticker': 'NVDA', 'next_event': {...}, ...}, query)
            "**Next Event for NVDA**: earnings on 2025-02-21\\n\\n**Calendar (3 events)**:..."
        """
        ticker = calendar_data.get('ticker', 'Unknown')
        events = calendar_data.get('events', [])
        next_event = calendar_data.get('next_event')

        lines = []

        # Display next upcoming event prominently
        if next_event:
            event_type = next_event.get('event_type', 'Event')
            event_date = next_event.get('event_date', 'TBD')
            lines.append(f"**Next Event for {ticker}**: {event_type} on {event_date}")

        # Display event list (max 5 for readability)
        if events:
            lines.append(f"\n**Calendar ({len(events)} events)**:")
            for e in events[:5]:
                date = e.get('event_date', 'TBD')
                etype = e.get('event_type', 'event')
                value = e.get('event_value', '')
                if value:
                    lines.append(f"- {date}: {etype} ({value})")
                else:
                    lines.append(f"- {date}: {etype}")

            if len(events) > 5:
                lines.append(f"  ... and {len(events) - 5} more events")
        else:
            lines.append(f"No calendar events found for {ticker}.")
            lines.append("Run data ingestion with Yahoo Finance enabled to populate calendar data.")

        return "\n".join(lines)

    def format_price_target_result(
        self,
        price_target_data: Dict[str, Any],
        query: str
    ) -> str:
        """
        Format price target query result for human-readable output.

        Args:
            price_target_data: Data from query_price() containing price targets
            query: Original user query

        Returns:
            Formatted response string with price target information
        """
        ticker = price_target_data.get('ticker', 'Unknown')
        latest = price_target_data.get('latest_price_target')
        history = price_target_data.get('price_target_history', [])

        lines = []

        # Display latest price target prominently
        if latest:
            target = latest.get('target_price', 'N/A')
            firm = latest.get('firm', 'Unknown')
            analyst = latest.get('analyst', 'Unknown')
            currency = latest.get('currency', 'USD')
            timestamp = latest.get('timestamp', '')[:10] if latest.get('timestamp') else ''

            lines.append(f"**Latest Price Target for {ticker}**: {currency} {target}")
            lines.append(f"  Analyst: {analyst} ({firm})")
            if timestamp:
                lines.append(f"  Date: {timestamp}")
        else:
            lines.append(f"No price target found for {ticker}.")

        # Display recent price target history (max 5)
        if history and len(history) > 1:
            lines.append(f"\n**Recent Price Targets ({len(history)} total)**:")
            for pt in history[:5]:
                target = pt.get('target_price', 'N/A')
                firm = pt.get('firm', 'Unknown')
                timestamp = pt.get('timestamp', '')[:10] if pt.get('timestamp') else ''
                lines.append(f"- {timestamp}: ${target} ({firm})")

        return "\n".join(lines)

    def format_pricing_history_result(
        self,
        pricing_data: Dict[str, Any],
        query: str
    ) -> str:
        """
        Format pricing history query result for human-readable output.

        Args:
            pricing_data: Data from query_pricing_history() containing OHLCV data
            query: Original user query

        Returns:
            Formatted response string with pricing history and 52-week stats
        """
        ticker = pricing_data.get('ticker', 'Unknown')
        week_52 = pricing_data.get('52_week_stats')
        recent_prices = pricing_data.get('recent_prices', [])

        lines = []

        # Display 52-week statistics prominently
        if week_52:
            high = week_52.get('52_week_high', 'N/A')
            high_date = week_52.get('52_week_high_date', '')
            low = week_52.get('52_week_low', 'N/A')
            low_date = week_52.get('52_week_low_date', '')
            current = week_52.get('current_price', 'N/A')
            pct_from_high = week_52.get('pct_from_high', 0)
            pct_from_low = week_52.get('pct_from_low', 0)

            lines.append(f"**52-Week Range for {ticker}**:")
            lines.append(f"  High: ${high} ({high_date})")
            lines.append(f"  Low: ${low} ({low_date})")
            lines.append(f"  Current: ${current}")
            lines.append(f"  From High: {pct_from_high}% | From Low: +{pct_from_low}%")
        else:
            lines.append(f"No 52-week data available for {ticker}.")

        # Display recent price action (last 5 trading days)
        if recent_prices:
            lines.append(f"\n**Recent Prices ({len(recent_prices)} days)**:")
            for p in recent_prices[:5]:
                date = p.get('date', '')
                close = p.get('close_price', 'N/A')
                volume = p.get('volume', 0)
                vol_str = f"{volume:,}" if volume else 'N/A'
                lines.append(f"- {date}: ${close} (Vol: {vol_str})")

        return "\n".join(lines)
