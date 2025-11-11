# Location: /imap_email_ingestion_pipeline/ticker_validator.py
# Purpose: Enhanced ticker validation to reduce false positives in entity extraction
# Why: EntityExtractor identifies too many false tickers (I, S, M, etc.) causing graph noise
# Relevant Files: entity_extractor.py, data_ingestion.py

import re
from typing import List, Dict, Set, Any

class TickerValidator:
    """
    Validate and filter ticker symbols to reduce false positives.

    Key strategies:
    1. Length filtering (2-5 chars typical for real tickers)
    2. Pattern matching (alphanumeric, optional dots/dashes)
    3. Blacklist common false positives
    4. Context validation (check surrounding text)
    """

    def __init__(self):
        # Common false positives to filter out
        self.blacklist = {
            # Single letters that are rarely real tickers
            'I', 'A', 'T', 'S', 'M', 'G', 'R', 'U', 'B', 'O', 'C', 'N', 'Q', 'F',

            # Common words mistaken for tickers
            'NOT', 'IF', 'IS', 'BE', 'AD', 'UPON', 'USA', 'CA', 'PO',

            # Date/time abbreviations
            'DATE', 'HKT', 'PT',

            # Rating words (should be in ratings, not tickers)
            'BUY', 'SELL', 'HOLD',

            # Geographic abbreviations (unless context indicates ticker)
            'HONG', 'KONG',

            # Common business abbreviations
            'CEO', 'CFO', 'COO', 'IPO', 'ETF', 'REIT', 'ADR',

            # Financial terms
            'EPS', 'PE', 'PB', 'ROE', 'ROA', 'EBITDA', 'FCF',

            # Currencies
            'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'HKD', 'SGD'
        }

        # Known valid single-letter tickers (exceptions to blacklist)
        self.valid_single_letters = {
            'V',    # Visa
            'X',    # United States Steel
            'K',    # Kellogg
            'E',    # Eni S.p.A
        }

        # Patterns that indicate a valid ticker format
        self.valid_patterns = [
            re.compile(r'^[A-Z]{2,5}$'),           # 2-5 uppercase letters
            re.compile(r'^[A-Z]{2,4}\.[A-Z]$'),    # With exchange suffix (BRK.B)
            re.compile(r'^\d{4}$'),                # 4-digit HK/China tickers
            re.compile(r'^\d{6}$'),                # 6-digit China A-shares
        ]

    def validate_ticker(self, ticker: str, context: str = "", confidence: float = 0.5) -> bool:
        """
        Validate if a string is likely a real ticker symbol.

        Args:
            ticker: The potential ticker symbol
            context: Surrounding text for context analysis
            confidence: Original confidence score from EntityExtractor

        Returns:
            True if likely a valid ticker, False otherwise
        """
        if not ticker:
            return False

        ticker = ticker.upper().strip()

        # Rule 1: Check valid single letters
        if len(ticker) == 1:
            return ticker in self.valid_single_letters

        # Rule 2: Filter blacklisted terms
        if ticker in self.blacklist:
            # Check if explicitly mentioned as ticker in context
            if context:
                ticker_indicators = [
                    f"ticker {ticker}",
                    f"symbol {ticker}",
                    f"({ticker})",
                    f"NYSE:{ticker}",
                    f"NASDAQ:{ticker}",
                    f"HK:{ticker}"
                ]
                context_lower = context.lower()
                for indicator in ticker_indicators:
                    if indicator.lower() in context_lower:
                        return True  # Override blacklist if explicitly mentioned
            return False

        # Rule 3: Check valid patterns
        for pattern in self.valid_patterns:
            if pattern.match(ticker):
                return True

        # Rule 4: Length check (most tickers are 2-5 chars)
        if len(ticker) < 2 or len(ticker) > 6:
            return False

        # Rule 5: Must contain at least one letter (not all numbers unless 4/6 digits)
        if ticker.isdigit() and len(ticker) not in [4, 6]:
            return False

        # Rule 6: High confidence override (trust EntityExtractor if very confident)
        if confidence >= 0.9:
            return True

        return False

    def filter_tickers(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter ticker entities to remove false positives.

        Args:
            entities: EntityExtractor output dictionary

        Returns:
            Filtered entities dictionary with validated tickers only
        """
        if 'tickers' not in entities:
            return entities

        original_tickers = entities['tickers']
        validated_tickers = []

        for ticker_obj in original_tickers:
            if isinstance(ticker_obj, dict):
                ticker_symbol = ticker_obj.get('ticker', '')
                confidence = ticker_obj.get('confidence', 0.5)
                context = ticker_obj.get('context', '')
            else:
                # Handle simple string format
                ticker_symbol = str(ticker_obj)
                confidence = 0.5
                context = ''

            if self.validate_ticker(ticker_symbol, context, confidence):
                validated_tickers.append(ticker_obj)

        # Update entities with filtered tickers
        filtered_entities = entities.copy()
        filtered_entities['tickers'] = validated_tickers

        # Log filtering results
        removed_count = len(original_tickers) - len(validated_tickers)
        if removed_count > 0:
            removed_tickers = [
                t.get('ticker', t) if isinstance(t, dict) else t
                for t in original_tickers
                if t not in validated_tickers
            ]
            print(f"Filtered out {removed_count} false positive tickers: {removed_tickers[:10]}")

        return filtered_entities

    def enhance_ticker_confidence(self, ticker: str, context: str) -> float:
        """
        Adjust confidence score based on contextual clues.

        Args:
            ticker: The ticker symbol
            context: Surrounding text

        Returns:
            Adjusted confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence

        # Boost confidence for explicit mentions
        boost_patterns = [
            (r'\(' + re.escape(ticker) + r'\)', 0.2),  # In parentheses
            (r'ticker:?\s*' + re.escape(ticker), 0.3),  # "ticker: XYZ"
            (r'symbol:?\s*' + re.escape(ticker), 0.3),  # "symbol: XYZ"
            (r'NYSE:' + re.escape(ticker), 0.4),        # Exchange prefix
            (r'NASDAQ:' + re.escape(ticker), 0.4),
            (r'\$' + re.escape(ticker), 0.2),           # $TICKER format
        ]

        context_lower = context.lower()
        ticker_lower = ticker.lower()

        for pattern, boost in boost_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                confidence += boost

        # Penalize if appears in common phrases that aren't tickers
        penalty_phrases = [
            'if', 'is', 'be', 'not', 'and', 'or', 'as', 'at', 'by', 'in', 'on', 'to'
        ]

        if ticker_lower in penalty_phrases:
            confidence -= 0.3

        return max(0.0, min(1.0, confidence))