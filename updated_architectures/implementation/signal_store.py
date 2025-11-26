# Location: updated_architectures/implementation/signal_store.py
# Purpose: SQLite-based Signal Store for structured investment intelligence queries
# Why: Enable fast (<1s) lookups for ratings, price targets, and financial metrics vs LightRAG semantic search (~12s)
# Relevant Files: data_ingestion.py, ice_simplified.py, query_router.py

import sqlite3
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Use try/except for robust import handling
try:
    from src.ice_core.temporal_enhancer import TemporalEnhancer
except ImportError:
    # Fall back to adding to path if necessary (but log warning)
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
    try:
        from src.ice_core.temporal_enhancer import TemporalEnhancer
    except ImportError:
        logging.warning("Failed to import TemporalEnhancer - freshness features disabled")
        TemporalEnhancer = None


class SignalStore:
    """
    SQLite-based storage for structured investment intelligence.

    Provides fast (<1s) lookups for:
    - Analyst ratings (BUY/SELL/HOLD)
    - Price targets
    - Financial metrics (revenue, margins, EPS)
    - Entity relationships

    Designed to complement LightRAG (not replace):
    - Signal Store: Structured queries (What/Which/Show + numerical filters)
    - LightRAG: Semantic queries (Why/How/Explain + reasoning)

    Architecture: Dual-write pattern
    - Same data written to both Signal Store and LightRAG
    - Transaction-based (both succeed or both fail)
    - Graceful degradation (falls back to LightRAG if Signal Store fails)
    """

    def __init__(self, db_path: str = "data/signal_store/signal_store.db"):
        """
        Initialize Signal Store with SQLite database.

        Args:
            db_path: Path to SQLite database file (default: data/signal_store/signal_store.db)
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path

        # Ensure directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database connection
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name

        # Create tables if they don't exist
        self._create_tables()

        self.logger.info(f"Signal Store initialized at {db_path}")

    def _create_tables(self):
        """Create all Signal Store tables with proper indexes."""
        cursor = self.conn.cursor()

        # Table 1: ratings (analyst ratings: BUY/SELL/HOLD)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                analyst TEXT,
                firm TEXT,
                rating TEXT NOT NULL,
                confidence REAL,
                timestamp TEXT NOT NULL,
                source_document_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add event_date column to ratings if it doesn't exist (for announcement date)
        try:
            cursor.execute("SELECT event_date FROM ratings LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE ratings ADD COLUMN event_date TEXT")
            self.logger.info("Added event_date column to ratings table")

        # Indexes for ratings table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_ticker ON ratings(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_timestamp ON ratings(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_ticker_timestamp ON ratings(ticker, timestamp DESC)")

        # Table 2: metrics (financial metrics from table extractions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_value TEXT NOT NULL,
                period TEXT,
                confidence REAL,
                source_document_id TEXT NOT NULL,
                table_index INTEGER,
                row_index INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add event_date column to metrics if it doesn't exist (for reporting period date)
        try:
            cursor.execute("SELECT event_date FROM metrics LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE metrics ADD COLUMN event_date TEXT")
            self.logger.info("Added event_date column to metrics table")

        # Indexes for metrics table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ticker ON metrics(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ticker_type ON metrics(ticker, metric_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ticker_period ON metrics(ticker, period)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_event_date ON metrics(event_date DESC)")

        # Table 3: price_targets (analyst price targets)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                analyst TEXT,
                firm TEXT,
                target_price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                confidence REAL,
                timestamp TEXT NOT NULL,
                source_document_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for price_targets table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_targets_ticker ON price_targets(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_targets_timestamp ON price_targets(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_targets_ticker_timestamp ON price_targets(ticker, timestamp DESC)")

        # Table 4: entities (extracted entities from documents)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT UNIQUE NOT NULL,
                entity_type TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                confidence REAL,
                source_document_id TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for entities table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_entity_id ON entities(entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(entity_name)")

        # Table 5: relationships (entity relationships/edges)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                confidence REAL,
                source_document_id TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for relationships table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source_target ON relationships(source_entity, target_entity)")

        # Table 6: table_metadata (tracks extracted tables for quantitative queries)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS table_metadata (
                table_id TEXT PRIMARY KEY,
                source_document TEXT NOT NULL,
                source_page INTEGER,
                table_type TEXT,
                extraction_confidence REAL,
                row_count INTEGER,
                col_count INTEGER,
                extracted_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for table_metadata
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_table_metadata_source ON table_metadata(source_document)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_table_metadata_type ON table_metadata(table_type)")

        # Table 7: table_cells (normalized cell storage for SQL-based quantitative queries)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS table_cells (
                cell_id TEXT PRIMARY KEY,
                table_id TEXT NOT NULL,
                row_index INTEGER NOT NULL,
                col_index INTEGER NOT NULL,
                cell_value TEXT,
                cell_type TEXT,
                normalized_value REAL,
                column_header TEXT,
                row_label TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (table_id) REFERENCES table_metadata(table_id)
            )
        """)

        # Indexes for table_cells (optimized for quantitative filtering)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_table_cells_table ON table_cells(table_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_table_cells_type ON table_cells(cell_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_table_cells_normalized ON table_cells(normalized_value)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_table_cells_header ON table_cells(column_header)")

        # ========== YAHOO FINANCE ENHANCEMENT TABLES ==========

        # Table 8: financial_metrics (Yahoo Categories 1 & 4 - numerical metrics with REAL type)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                metric_category TEXT,
                period TEXT,
                fiscal_year INTEGER,
                fiscal_quarter INTEGER,
                source_document_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, metric_name, period)
            )
        """)

        # Add event_date column to financial_metrics if it doesn't exist
        try:
            cursor.execute("SELECT event_date FROM financial_metrics LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE financial_metrics ADD COLUMN event_date TEXT")
            self.logger.info("Added event_date column to financial_metrics table")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_metrics_ticker ON financial_metrics(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_metrics_name ON financial_metrics(metric_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_metrics_value ON financial_metrics(metric_value)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_metrics_ticker_period ON financial_metrics(ticker, period)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_metrics_event_date ON financial_metrics(event_date DESC)")

        # Table 9: price_history (Yahoo Category 6 - OHLCV time-series data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                source_document_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, date)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_ticker_date ON price_history(ticker, date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_high ON price_history(high_price DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_volume ON price_history(volume DESC)")

        # Table 10: calendar_events (Yahoo Categories 5 & 7 - earnings/dividend events)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_value REAL,
                estimate_high REAL,
                estimate_low REAL,
                estimate_avg REAL,
                is_future INTEGER DEFAULT 0,
                source_document_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, event_type, event_date)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_events_ticker ON calendar_events(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_events_type ON calendar_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_events_date ON calendar_events(event_date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_events_future ON calendar_events(is_future, event_date)")

        self.conn.commit()
        self.logger.info("Signal Store tables created successfully (10 tables including Yahoo Finance enhancements)")

    @staticmethod
    def _infer_event_date_from_period(period: Optional[str], fiscal_year: Optional[int],
                                       fiscal_quarter: Optional[int]) -> Optional[str]:
        """
        Infer approximate event date from fiscal period information.

        For investment workflows, event date (when earnings announced) is more important than
        ingestion date. This method provides reasonable approximations for date-based queries.

        Args:
            period: Period string like "Q2 2024", "FY2024", "TTM"
            fiscal_year: Fiscal year as integer (e.g., 2024)
            fiscal_quarter: Fiscal quarter 1-4

        Returns:
            ISO date string (YYYY-MM-DD) representing approximate event date, or None if cannot infer

        Heuristics:
            - Q1 (Jan-Mar): Announced ~mid-April
            - Q2 (Apr-Jun): Announced ~mid-July
            - Q3 (Jul-Sep): Announced ~mid-October
            - Q4 (Oct-Dec): Announced ~mid-January (next year)
            - Annual/FY: Announced ~mid-February (next year)
            - TTM: Use current date

        Note:
            These are approximations. Actual announcement dates vary by company.
            For precise dates, use calendar_events table which has exact dates.
        """
        if not period and not (fiscal_year and fiscal_quarter):
            return None

        # Quarterly earnings announcement dates (approximate: quarter_end + 15 days)
        quarter_announcement_months = {
            1: (4, 15),   # Q1 ends Mar 31, announced ~Apr 15
            2: (7, 15),   # Q2 ends Jun 30, announced ~Jul 15
            3: (10, 15),  # Q3 ends Sep 30, announced ~Oct 15
            4: (1, 15)    # Q4 ends Dec 31, announced ~Jan 15 (next year)
        }

        # Try to extract from period string first
        if period:
            period_upper = period.upper().strip()

            # TTM or trailing periods use current date
            if 'TTM' in period_upper or 'TRAILING' in period_upper:
                return datetime.now().strftime('%Y-%m-%d')

            # Handle "current" period
            if period_upper == 'CURRENT':
                return datetime.now().strftime('%Y-%m-%d')

            import re

            # Parse Yahoo Finance "YYYY-Qq" format (quarterly data, no specific quarter)
            # Default to Q4 (most conservative assumption for annual data)
            yahoo_quarterly_match = re.search(r'(\d{4})-QQ', period_upper)
            if yahoo_quarterly_match:
                year = int(yahoo_quarterly_match.group(1))
                # Default to Q4 announcement (January 15 of next year)
                return f"{year + 1}-01-15"

            # Parse Yahoo Finance "YYYY-Qy" format (yearly/annual data)
            yahoo_annual_match = re.search(r'(\d{4})-QY', period_upper)
            if yahoo_annual_match:
                year = int(yahoo_annual_match.group(1))
                # Annual reports announced ~mid-February of next year
                return f"{year + 1}-02-15"

            # Parse "Q# YYYY" format
            quarter_match = re.search(r'Q([1-4])\s+(\d{4})', period_upper)
            if quarter_match:
                q = int(quarter_match.group(1))
                year = int(quarter_match.group(2))
                month, day = quarter_announcement_months[q]
                # Q4 announcement is in January of next year
                if q == 4:
                    year += 1
                return f"{year}-{month:02d}-{day:02d}"

            # Parse "FY####" or "Annual ####" format
            fy_match = re.search(r'(?:FY|ANNUAL)\s*(\d{4})', period_upper)
            if fy_match:
                year = int(fy_match.group(1))
                # Annual reports announced ~mid-February of next year
                return f"{year + 1}-02-15"

        # Fallback: Use fiscal_year and fiscal_quarter if available
        if fiscal_year and fiscal_quarter and fiscal_quarter in quarter_announcement_months:
            month, day = quarter_announcement_months[fiscal_quarter]
            year = fiscal_year
            if fiscal_quarter == 4:
                year += 1
            return f"{year}-{month:02d}-{day:02d}"

        # Cannot infer - return None
        return None

    def _add_freshness_metadata(self, result: Dict[str, Any], timestamp_field: str = 'timestamp') -> Dict[str, Any]:
        """
        Add freshness score and category to a result dictionary with timestamp.

        Args:
            result: Dict with timestamp field
            timestamp_field: Name of the timestamp field (default: 'timestamp')

        Returns:
            The same dict with freshness_score and freshness_category added
        """
        if not result or not TemporalEnhancer:
            return result

        timestamp = result.get(timestamp_field)
        if timestamp:
            try:
                freshness_score, freshness_category = TemporalEnhancer.calculate_freshness_from_timestamp(timestamp)
                result['freshness_score'] = freshness_score
                result['freshness_category'] = freshness_category
            except Exception as e:
                self.logger.debug(f"Failed to calculate freshness for timestamp {timestamp}: {e}")
                # Add neutral values on error
                result['freshness_score'] = 0.5
                result['freshness_category'] = 'unknown'

        # Normalize confidence (handle NULL database values)
        # Ensures consistent data contract for all methods using freshness metadata
        if result.get('confidence') is None:
            result['confidence'] = 0.5  # Default confidence for ratings/signals without explicit confidence

        return result

    def _add_freshness_to_results(self, results: List[Dict[str, Any]], timestamp_field: str = 'timestamp') -> List[Dict[str, Any]]:
        """
        Add freshness metadata to a list of results.

        Args:
            results: List of result dicts with timestamps
            timestamp_field: Name of the timestamp field (default: 'timestamp')

        Returns:
            The same list with freshness metadata added to each result
        """
        for result in results:
            self._add_freshness_metadata(result, timestamp_field)
        return results

    def _validate_date_range(self, start_date: str, end_date: str) -> bool:
        """
        Validate that date range is valid and start_date <= end_date.

        Args:
            start_date: ISO format start date
            end_date: ISO format end date

        Returns:
            True if valid, False otherwise
        """
        try:
            from datetime import datetime
            # Handle both full ISO format and date-only format
            if 'T' in start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                start_dt = datetime.fromisoformat(start_date + 'T00:00:00+00:00')

            if 'T' in end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            else:
                end_dt = datetime.fromisoformat(end_date + 'T23:59:59+00:00')

            if start_dt > end_dt:
                self.logger.warning(f"Invalid date range: start_date ({start_date}) > end_date ({end_date})")
                return False

            return True
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"Invalid date format in range validation: {e}")
            return False

    # ==================== RATINGS TABLE OPERATIONS ====================

    def insert_rating(
        self,
        ticker: str,
        rating: str,
        timestamp: str,
        source_document_id: str,
        analyst: Optional[str] = None,
        firm: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> int:
        """
        Insert analyst rating into Signal Store.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            rating: Analyst rating (BUY/SELL/HOLD/OUTPERFORM/UNDERPERFORM)
            timestamp: ISO format timestamp (e.g., '2024-03-15T10:30:00Z')
            source_document_id: Source document reference (e.g., 'email_12345')
            analyst: Analyst name (optional)
            firm: Analyst firm (optional, e.g., 'Goldman Sachs')
            confidence: Confidence score 0.0-1.0 (optional)

        Returns:
            Row ID of inserted rating
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ratings (ticker, analyst, firm, rating, confidence, timestamp, source_document_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ticker, analyst, firm, rating, confidence, timestamp, source_document_id))

        self.conn.commit()
        row_id = cursor.lastrowid

        self.logger.debug(f"Inserted rating: {ticker} {rating} (id={row_id})")
        return row_id

    def insert_ratings_batch(self, ratings: List[Dict[str, Any]]) -> int:
        """
        Insert multiple ratings in a single transaction.

        Args:
            ratings: List of rating dicts with keys: ticker, rating, timestamp, source_document_id,
                     analyst (optional), firm (optional), confidence (optional)

        Returns:
            Number of ratings inserted
        """
        cursor = self.conn.cursor()

        for rating in ratings:
            cursor.execute("""
                INSERT INTO ratings (ticker, analyst, firm, rating, confidence, timestamp, source_document_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                rating['ticker'],
                rating.get('analyst'),
                rating.get('firm'),
                rating['rating'],
                rating.get('confidence'),
                rating['timestamp'],
                rating['source_document_id']
            ))

        self.conn.commit()
        count = len(ratings)
        self.logger.info(f"Inserted {count} ratings in batch")
        return count

    def get_latest_rating(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent rating for a ticker with freshness score.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')

        Returns:
            Dict with rating details or None if no rating found
            {
                'ticker': 'NVDA',
                'rating': 'BUY',
                'analyst': 'John Doe',
                'firm': 'Goldman Sachs',
                'confidence': 0.87,
                'timestamp': '2024-03-15T10:30:00Z',
                'source_document_id': 'email_12345',
                'freshness_score': 0.25,
                'freshness_category': 'fresh'
            }
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, analyst, firm, rating, confidence, timestamp, source_document_id
            FROM ratings
            WHERE ticker = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (ticker,))

        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Add freshness metadata using helper method
            return self._add_freshness_metadata(result)
        return None

    def get_rating_history(
        self,
        ticker: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get rating history for a ticker with freshness scores (most recent first).

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of ratings to return (default: 10)

        Returns:
            List of rating dicts with freshness scores, sorted by timestamp descending
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, analyst, firm, rating, confidence, timestamp, source_document_id
            FROM ratings
            WHERE ticker = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (ticker, limit))

        results = [dict(row) for row in cursor.fetchall()]
        # Add freshness metadata to all results
        return self._add_freshness_to_results(results)

    def get_ratings_by_firm(
        self,
        firm: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all ratings from a specific firm (most recent first).

        Args:
            firm: Analyst firm name (e.g., 'Goldman Sachs')
            limit: Maximum number of ratings to return (default: 50)

        Returns:
            List of rating dicts sorted by timestamp descending
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, analyst, firm, rating, confidence, timestamp, source_document_id
            FROM ratings
            WHERE firm = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (firm, limit))

        return [dict(row) for row in cursor.fetchall()]

    def count_ratings(self) -> int:
        """
        Count total number of ratings in Signal Store.

        Returns:
            Total rating count
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ratings")
        return cursor.fetchone()[0]

    def get_ratings_by_date_range(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get ratings for a ticker within a date range.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            start_date: ISO format start date (e.g., '2024-01-01T00:00:00Z')
            end_date: ISO format end date (e.g., '2024-06-30T23:59:59Z')
            limit: Maximum number of ratings to return (default: 100)

        Returns:
            List of rating dicts within the date range, sorted by timestamp DESC

        Example:
            >>> store.get_ratings_by_date_range('NVDA', '2024-04-01', '2024-06-30')
            [{'ticker': 'NVDA', 'rating': 'BUY', 'timestamp': '2024-06-15T10:30:00Z', ...},
             {'ticker': 'NVDA', 'rating': 'HOLD', 'timestamp': '2024-05-20T14:00:00Z', ...}]
        """
        # Validate date range
        if not self._validate_date_range(start_date, end_date):
            return []  # Return empty list for invalid dates

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, analyst, firm, rating, confidence, timestamp, source_document_id
            FROM ratings
            WHERE ticker = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (ticker, start_date, end_date, limit))

        results = [dict(row) for row in cursor.fetchall()]
        # Add freshness metadata to all results
        return self._add_freshness_to_results(results)

    # ==================== METRICS TABLE OPERATIONS ====================

    def insert_metric(
        self,
        ticker: str,
        metric_type: str,
        metric_value: str,
        source_document_id: str,
        period: Optional[str] = None,
        confidence: Optional[float] = None,
        table_index: Optional[int] = None,
        row_index: Optional[int] = None
    ) -> int:
        """
        Insert financial metric into Signal Store.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            metric_type: Type of metric (e.g., 'Operating Margin', 'Revenue', 'EPS')
            metric_value: Metric value as string (e.g., '62.3%', '$26.97B', '5.16')
            source_document_id: Source document reference (e.g., 'email_12345')
            period: Time period (e.g., 'Q2 2024', 'FY2024', 'TTM')
            confidence: Confidence score 0.0-1.0 (optional)
            table_index: Index of table in attachment (optional)
            row_index: Row index in table (optional)

        Returns:
            Row ID of inserted metric
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO metrics (ticker, metric_type, metric_value, period, confidence, 
                                source_document_id, table_index, row_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ticker, metric_type, metric_value, period, confidence, 
              source_document_id, table_index, row_index))

        self.conn.commit()
        row_id = cursor.lastrowid

        self.logger.debug(f"Inserted metric: {ticker} {metric_type}={metric_value} (id={row_id})")
        return row_id

    def insert_metrics_batch(self, metrics: List[Dict[str, Any]]) -> int:
        """
        Insert multiple metrics in a single transaction.

        Args:
            metrics: List of metric dicts with keys: ticker, metric_type, metric_value, 
                     source_document_id, period (optional), confidence (optional),
                     table_index (optional), row_index (optional)

        Returns:
            Number of metrics inserted
        """
        cursor = self.conn.cursor()

        for metric in metrics:
            cursor.execute("""
                INSERT INTO metrics (ticker, metric_type, metric_value, period, confidence,
                                   source_document_id, table_index, row_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric['ticker'],
                metric['metric_type'],
                metric['metric_value'],
                metric.get('period'),
                metric.get('confidence'),
                metric['source_document_id'],
                metric.get('table_index'),
                metric.get('row_index')
            ))

        self.conn.commit()
        count = len(metrics)
        self.logger.info(f"Inserted {count} metrics in batch")
        return count

    def get_metric(
        self,
        ticker: str,
        metric_type: str,
        period: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific metric for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            metric_type: Type of metric (e.g., 'Operating Margin')
            period: Time period filter (optional, e.g., 'Q2 2024')

        Returns:
            Dict with metric details or None if not found
            {
                'ticker': 'NVDA',
                'metric_type': 'Operating Margin',
                'metric_value': '62.3%',
                'period': 'Q2 2024',
                'confidence': 0.95,
                'source_document_id': 'email_12345'
            }
        """
        cursor = self.conn.cursor()

        if period:
            cursor.execute("""
                SELECT ticker, metric_type, metric_value, period, confidence, source_document_id
                FROM metrics
                WHERE ticker = ? AND metric_type = ? AND period = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (ticker, metric_type, period))
        else:
            cursor.execute("""
                SELECT ticker, metric_type, metric_value, period, confidence, source_document_id
                FROM metrics
                WHERE ticker = ? AND metric_type = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (ticker, metric_type))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_metrics_by_ticker(
        self,
        ticker: str,
        period: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all metrics for a ticker, optionally filtered by period.

        Args:
            ticker: Stock ticker symbol
            period: Time period filter (optional)
            limit: Maximum number of metrics to return (default: 50)

        Returns:
            List of metric dicts sorted by metric_type
        """
        cursor = self.conn.cursor()

        if period:
            cursor.execute("""
                SELECT ticker, metric_type, metric_value, period, confidence, source_document_id
                FROM metrics
                WHERE ticker = ? AND period = ?
                ORDER BY metric_type
                LIMIT ?
            """, (ticker, period, limit))
        else:
            cursor.execute("""
                SELECT ticker, metric_type, metric_value, period, confidence, source_document_id
                FROM metrics
                WHERE ticker = ?
                ORDER BY metric_type
                LIMIT ?
            """, (ticker, limit))

        return [dict(row) for row in cursor.fetchall()]

    def compare_metrics(
        self,
        ticker: str,
        metric_type: str,
        periods: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Compare a metric across multiple periods for trend analysis.

        Args:
            ticker: Stock ticker symbol
            metric_type: Type of metric to compare
            periods: List of periods to compare (e.g., ['Q1 2024', 'Q2 2024'])

        Returns:
            List of metric dicts for each period
        """
        cursor = self.conn.cursor()

        # Use parameterized query with IN clause
        placeholders = ','.join('?' * len(periods))
        query = f"""
            SELECT ticker, metric_type, metric_value, period, confidence, source_document_id
            FROM metrics
            WHERE ticker = ? AND metric_type = ? AND period IN ({placeholders})
            ORDER BY period
        """

        params = [ticker, metric_type] + periods
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def count_metrics(self) -> int:
        """
        Count total number of metrics in Signal Store.

        Returns:
            Total metric count
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM metrics")
        return cursor.fetchone()[0]

    def get_metrics_by_date_range(
        self,
        ticker: str,
        metric_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get metrics for a ticker within a date range.

        CRITICAL FIX (2025-11-18): Now uses event_date instead of created_at for filtering.
        This ensures Q2 2024 earnings announced on July 15 (but ingested Aug 1) will appear
        in queries for July date ranges.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            metric_type: Optional filter for specific metric type
            start_date: ISO format start date (optional, e.g., '2024-07-01')
            end_date: ISO format end date (optional, e.g., '2024-07-31')
            limit: Maximum number of metrics to return (default: 100)

        Returns:
            List of metric dicts within the date range, sorted by event_date DESC

        Example:
            >>> # Q2 2024 metrics (announced ~July 15)
            >>> store.get_metrics_by_date_range('NVDA', 'Revenue', '2024-07-01', '2024-07-31')
            [{'ticker': 'NVDA', 'metric_type': 'Revenue', 'metric_value': '$26.97B',
              'period': 'Q2 2024', 'event_date': '2024-07-15', ...}]
        """
        # Validate date range
        self._validate_date_range(start_date, end_date)

        cursor = self.conn.cursor()

        # Build query dynamically - use event_date for date filtering (NOT created_at)
        query = """
            SELECT ticker, metric_type, metric_value, period, confidence,
                   source_document_id, event_date, created_at
            FROM metrics
            WHERE ticker = ?
        """
        params = [ticker]

        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type)

        if start_date:
            # CRITICAL: Filter by event_date (when earnings announced) not created_at (when ingested)
            query += " AND (event_date >= ? OR (event_date IS NULL AND created_at >= ?))"
            params.extend([start_date, start_date])

        if end_date:
            query += " AND (event_date <= ? OR (event_date IS NULL AND created_at <= ?))"
            params.extend([end_date, end_date])

        # Sort by event_date (fallback to created_at for legacy data without event_date)
        query += " ORDER BY COALESCE(event_date, created_at) DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        results = [dict(row) for row in cursor.fetchall()]
        # Add freshness metadata using event_date (fallback to created_at)
        for result in results:
            timestamp_field = 'event_date' if result.get('event_date') else 'created_at'
            result = self._add_freshness_metadata(result, timestamp_field=timestamp_field)

        return results

    # ==================== PRICE TARGETS TABLE OPERATIONS ====================

    def insert_price_target(
        self,
        ticker: str,
        target_price: float,
        timestamp: str,
        source_document_id: str,
        analyst: Optional[str] = None,
        firm: Optional[str] = None,
        currency: str = 'USD',
        confidence: Optional[float] = None
    ) -> int:
        """
        Insert analyst price target into Signal Store.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            target_price: Price target as float (e.g., 500.0)
            timestamp: ISO format timestamp (e.g., '2024-03-15T10:30:00Z')
            source_document_id: Source document reference (e.g., 'email_12345')
            analyst: Analyst name (optional)
            firm: Analyst firm (optional, e.g., 'Goldman Sachs')
            currency: Currency code (default: 'USD')
            confidence: Confidence score 0.0-1.0 (optional)

        Returns:
            Row ID of inserted price target
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO price_targets (ticker, analyst, firm, target_price, currency, confidence, timestamp, source_document_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ticker, analyst, firm, target_price, currency, confidence, timestamp, source_document_id))

        self.conn.commit()
        row_id = cursor.lastrowid

        self.logger.debug(f"Inserted price target: {ticker} ${target_price} (id={row_id})")
        return row_id

    def get_latest_price_target(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent price target for a ticker with freshness score.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')

        Returns:
            Dict with price target details or None if not found
            {
                'ticker': 'NVDA',
                'target_price': 500.0,
                'analyst': 'John Doe',
                'firm': 'Goldman Sachs',
                'currency': 'USD',
                'confidence': 0.92,
                'timestamp': '2024-03-15T10:30:00Z',
                'source_document_id': 'email_12345',
                'freshness_score': 0.25,
                'freshness_category': 'fresh'
            }
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, analyst, firm, target_price, currency, confidence, timestamp, source_document_id
            FROM price_targets
            WHERE ticker = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (ticker,))

        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Add freshness metadata using helper method
            return self._add_freshness_metadata(result)
        return None

    def get_price_target_history(
        self,
        ticker: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get price target history for a ticker with freshness scores (most recent first).

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of targets to return (default: 10)

        Returns:
            List of price target dicts with freshness scores, sorted by timestamp descending
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, analyst, firm, target_price, currency, confidence, timestamp, source_document_id
            FROM price_targets
            WHERE ticker = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (ticker, limit))

        results = [dict(row) for row in cursor.fetchall()]
        # Add freshness metadata to all results
        return self._add_freshness_to_results(results)

    def count_price_targets(self) -> int:
        """
        Count total number of price targets in Signal Store.

        Returns:
            Total price target count
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM price_targets")
        return cursor.fetchone()[0]

    def get_price_targets_by_date_range(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get price targets for a ticker within a date range.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            start_date: ISO format start date (e.g., '2024-01-01T00:00:00Z')
            end_date: ISO format end date (e.g., '2024-06-30T23:59:59Z')
            limit: Maximum number of targets to return (default: 100)

        Returns:
            List of price target dicts within the date range, sorted by timestamp DESC

        Example:
            >>> store.get_price_targets_by_date_range('NVDA', '2024-04-01', '2024-06-30')
            [{'ticker': 'NVDA', 'target_price': 850.0, 'timestamp': '2024-06-15T10:30:00Z', ...},
             {'ticker': 'NVDA', 'target_price': 750.0, 'timestamp': '2024-05-20T14:00:00Z', ...}]
        """
        # Validate date range
        if not self._validate_date_range(start_date, end_date):
            return []  # Return empty list for invalid dates

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, analyst, firm, target_price, currency, confidence,
                   timestamp, source_document_id
            FROM price_targets
            WHERE ticker = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (ticker, start_date, end_date, limit))

        results = [dict(row) for row in cursor.fetchall()]
        # Add freshness metadata to all results
        return self._add_freshness_to_results(results)

    # ==================== ENTITIES TABLE OPERATIONS ====================

    def insert_entity(
        self,
        entity_id: str,
        entity_type: str,
        entity_name: str,
        source_document_id: str,
        confidence: Optional[float] = None,
        metadata: Optional[str] = None
    ) -> int:
        """
        Insert entity into Signal Store.

        Args:
            entity_id: Unique entity identifier (e.g., 'TICKER:NVDA', 'PERSON:John_Doe')
            entity_type: Type of entity (e.g., 'TICKER', 'PERSON', 'COMPANY', 'TECHNOLOGY')
            entity_name: Human-readable entity name (e.g., 'NVDA', 'John Doe', 'NVIDIA')
            source_document_id: Source document reference
            confidence: Confidence score 0.0-1.0 (optional)
            metadata: JSON metadata (optional)

        Returns:
            Row ID of inserted entity

        Examples:
            >>> store.insert_entity('TICKER:NVDA', 'TICKER', 'NVDA', 'email_123', 0.98)
            >>> store.insert_entity('PERSON:Jensen_Huang', 'PERSON', 'Jensen Huang', 'email_123', 0.95)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO entities (
                entity_id, entity_type, entity_name, confidence, source_document_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (entity_id, entity_type, entity_name, confidence, source_document_id, metadata))

        self.conn.commit()
        row_id = cursor.lastrowid
        self.logger.debug(f"Inserted entity: {entity_id} ({entity_type})")
        return row_id

    def insert_entities_batch(self, entities: List[Dict[str, Any]]) -> int:
        """
        Insert multiple entities in batch (transaction-based).

        Args:
            entities: List of entity dicts with keys:
                - entity_id (required)
                - entity_type (required)
                - entity_name (required)
                - source_document_id (required)
                - confidence (optional)
                - metadata (optional)

        Returns:
            Number of entities inserted

        Examples:
            >>> entities = [
            ...     {'entity_id': 'TICKER:NVDA', 'entity_type': 'TICKER', 'entity_name': 'NVDA', 'source_document_id': 'email_123'},
            ...     {'entity_id': 'TICKER:TSMC', 'entity_type': 'TICKER', 'entity_name': 'TSMC', 'source_document_id': 'email_123'}
            ... ]
            >>> store.insert_entities_batch(entities)
            2
        """
        cursor = self.conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        try:
            for entity in entities:
                cursor.execute("""
                    INSERT OR REPLACE INTO entities (
                        entity_id, entity_type, entity_name, confidence, source_document_id, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entity['entity_id'],
                    entity['entity_type'],
                    entity['entity_name'],
                    entity.get('confidence'),
                    entity['source_document_id'],
                    entity.get('metadata')
                ))

            self.conn.commit()
            count = len(entities)
            self.logger.info(f"Batch inserted {count} entities")
            return count

        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Batch entity insert failed: {e}")
            raise

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get entity by ID.

        Args:
            entity_id: Unique entity identifier

        Returns:
            Entity dict or None if not found

        Examples:
            >>> store.get_entity('TICKER:NVDA')
            {'entity_id': 'TICKER:NVDA', 'entity_type': 'TICKER', 'entity_name': 'NVDA', ...}
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT entity_id, entity_type, entity_name, confidence, source_document_id, metadata, created_at
            FROM entities
            WHERE entity_id = ?
        """, (entity_id,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_entities_by_type(
        self,
        entity_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all entities of a specific type.

        Args:
            entity_type: Type of entity to retrieve
            limit: Maximum number of entities to return (default: 100)

        Returns:
            List of entity dicts

        Examples:
            >>> store.get_entities_by_type('TICKER', limit=10)
            [{'entity_id': 'TICKER:NVDA', ...}, {'entity_id': 'TICKER:TSMC', ...}]
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT entity_id, entity_type, entity_name, confidence, source_document_id, metadata, created_at
            FROM entities
            WHERE entity_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (entity_type, limit))

        return [dict(row) for row in cursor.fetchall()]

    def count_entities(self) -> int:
        """Count total number of entities in Signal Store."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entities")
        return cursor.fetchone()[0]

    # ==================== RELATIONSHIPS TABLE OPERATIONS ====================

    def insert_relationship(
        self,
        source_entity: str,
        target_entity: str,
        relationship_type: str,
        source_document_id: str,
        confidence: Optional[float] = None,
        metadata: Optional[str] = None
    ) -> int:
        """
        Insert relationship between entities into Signal Store.

        Args:
            source_entity: Source entity ID
            target_entity: Target entity ID
            relationship_type: Type of relationship (e.g., 'WORKS_AT', 'SUPPLIES_TO', 'COMPETES_WITH')
            source_document_id: Source document reference
            confidence: Confidence score 0.0-1.0 (optional)
            metadata: JSON metadata (optional)

        Returns:
            Row ID of inserted relationship

        Examples:
            >>> store.insert_relationship('PERSON:Jensen_Huang', 'COMPANY:NVIDIA', 'CEO_OF', 'email_123', 0.98)
            >>> store.insert_relationship('COMPANY:TSMC', 'COMPANY:NVIDIA', 'SUPPLIES_TO', 'email_456', 0.92)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO relationships (
                source_entity, target_entity, relationship_type, confidence, source_document_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (source_entity, target_entity, relationship_type, confidence, source_document_id, metadata))

        self.conn.commit()
        row_id = cursor.lastrowid
        self.logger.debug(f"Inserted relationship: {source_entity} -> {relationship_type} -> {target_entity}")
        return row_id

    def insert_relationships_batch(self, relationships: List[Dict[str, Any]]) -> int:
        """
        Insert multiple relationships in batch (transaction-based).

        Args:
            relationships: List of relationship dicts with keys:
                - source_entity (required)
                - target_entity (required)
                - relationship_type (required)
                - source_document_id (required)
                - confidence (optional)
                - metadata (optional)

        Returns:
            Number of relationships inserted

        Examples:
            >>> relationships = [
            ...     {'source_entity': 'TICKER:NVDA', 'target_entity': 'TICKER:TSMC', 'relationship_type': 'DEPENDS_ON', 'source_document_id': 'email_123'},
            ...     {'source_entity': 'TICKER:NVDA', 'target_entity': 'TECH:AI', 'relationship_type': 'OPERATES_IN', 'source_document_id': 'email_123'}
            ... ]
            >>> store.insert_relationships_batch(relationships)
            2
        """
        cursor = self.conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        try:
            for rel in relationships:
                cursor.execute("""
                    INSERT INTO relationships (
                        source_entity, target_entity, relationship_type, confidence, source_document_id, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    rel['source_entity'],
                    rel['target_entity'],
                    rel['relationship_type'],
                    rel.get('confidence'),
                    rel['source_document_id'],
                    rel.get('metadata')
                ))

            self.conn.commit()
            count = len(relationships)
            self.logger.info(f"Batch inserted {count} relationships")
            return count

        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Batch relationship insert failed: {e}")
            raise

    def get_relationships(
        self,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
        relationship_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get relationships with optional filters.

        Args:
            source_entity: Filter by source entity ID (optional)
            target_entity: Filter by target entity ID (optional)
            relationship_type: Filter by relationship type (optional)
            limit: Maximum number of relationships to return (default: 100)

        Returns:
            List of relationship dicts

        Examples:
            >>> store.get_relationships(source_entity='TICKER:NVDA')
            [{'source_entity': 'TICKER:NVDA', 'target_entity': 'TICKER:TSMC', ...}]

            >>> store.get_relationships(relationship_type='SUPPLIES_TO')
            [{'source_entity': 'TICKER:TSMC', 'target_entity': 'TICKER:NVDA', ...}]
        """
        cursor = self.conn.cursor()

        # Build dynamic query based on filters
        query = """
            SELECT source_entity, target_entity, relationship_type, confidence, source_document_id, metadata, created_at
            FROM relationships
            WHERE 1=1
        """
        params = []

        if source_entity:
            query += " AND source_entity = ?"
            params.append(source_entity)

        if target_entity:
            query += " AND target_entity = ?"
            params.append(target_entity)

        if relationship_type:
            query += " AND relationship_type = ?"
            params.append(relationship_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def count_relationships(self) -> int:
        """Count total number of relationships in Signal Store."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM relationships")
        return cursor.fetchone()[0]

    # ==================== TABLE STORAGE METHODS ====================

    def insert_table_metadata(self, table_id: str, source_document: str,
                              source_page: Optional[int], table_type: str,
                              extraction_confidence: float, row_count: int,
                              col_count: int) -> bool:
        """
        Insert table metadata for extracted tables.

        Args:
            table_id: Unique table identifier (SHA256-based)
            source_document: Source document path
            source_page: Page number where table appears
            table_type: Classification (financial_statement, insider_transactions, etc.)
            extraction_confidence: Docling extraction confidence (0.0-1.0)
            row_count: Number of rows in table
            col_count: Number of columns in table

        Returns:
            True if inserted successfully, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO table_metadata
                (table_id, source_document, source_page, table_type, extraction_confidence, row_count, col_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (table_id, source_document, source_page, table_type, extraction_confidence, row_count, col_count))

            self.conn.commit()
            self.logger.debug(f"Inserted table metadata: {table_id} ({row_count}x{col_count}, type={table_type})")
            return True

        except sqlite3.Error as e:
            self.logger.error(f"Failed to insert table metadata {table_id}: {e}")
            return False

    def insert_table_cells(self, cells: List[Dict[str, Any]]) -> int:
        """
        Batch insert table cells (optimized for performance).

        Args:
            cells: List of cell dicts with keys: cell_id, table_id, row_index, col_index,
                   cell_value, cell_type, normalized_value, column_header, row_label, confidence

        Returns:
            Number of cells successfully inserted
        """
        if not cells:
            return 0

        try:
            cursor = self.conn.cursor()

            # Prepare batch insert data (use parameterized queries to prevent SQL injection)
            insert_data = [
                (
                    cell['cell_id'],
                    cell['table_id'],
                    cell['row_index'],
                    cell['col_index'],
                    cell.get('cell_value'),
                    cell.get('cell_type'),
                    cell.get('normalized_value'),
                    cell.get('column_header'),
                    cell.get('row_label'),
                    cell.get('confidence')
                )
                for cell in cells
            ]

            cursor.executemany("""
                INSERT OR REPLACE INTO table_cells
                (cell_id, table_id, row_index, col_index, cell_value, cell_type,
                 normalized_value, column_header, row_label, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, insert_data)

            self.conn.commit()
            self.logger.info(f"Inserted {len(cells)} table cells in batch")
            return len(cells)

        except sqlite3.Error as e:
            self.logger.error(f"Failed to batch insert table cells: {e}")
            return 0

    def insert_table_with_cells_atomic(self, table_id: str, source_document: str,
                                       source_page: Optional[int], table_type: str,
                                       extraction_confidence: float, row_count: int,
                                       col_count: int, cells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Atomically insert table metadata and cells in a single transaction (Fix #1).

        ACID guarantees: Either both inserts succeed or neither does.
        Prevents orphaned metadata when cell insertion fails.

        Args:
            table_id: Unique table identifier (SHA256-based)
            source_document: Source document path
            source_page: Page number where table appears
            table_type: Classification (financial_statement, insider_transactions, etc.)
            extraction_confidence: Docling extraction confidence (0.0-1.0)
            row_count: Number of rows in table
            col_count: Number of columns in table
            cells: List of cell dicts (see insert_table_cells for format)

        Returns:
            Dict with:
                - success: bool
                - cells_stored: int (0 if failed)
                - error: Optional[str]
        """
        cursor = self.conn.cursor()

        try:
            # Validate cell data has required fields (defensive programming)
            if cells:
                required_fields = {'cell_id', 'table_id', 'row_index', 'col_index'}
                for i, cell in enumerate(cells):
                    missing = required_fields - set(cell.keys())
                    if missing:
                        raise ValueError(
                            f"Cell {i} missing required fields: {missing}. "
                            f"Required: {required_fields}"
                        )

            # BEGIN TRANSACTION (explicit for clarity, though SQLite has implicit transactions)
            cursor.execute("BEGIN TRANSACTION")

            # 1. Insert metadata (without auto-commit)
            cursor.execute("""
                INSERT OR REPLACE INTO table_metadata
                (table_id, source_document, source_page, table_type, extraction_confidence, row_count, col_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (table_id, source_document, source_page, table_type, extraction_confidence, row_count, col_count))

            # 2. Batch insert cells (without auto-commit)
            if cells:
                insert_data = [
                    (
                        cell['cell_id'],
                        cell['table_id'],
                        cell['row_index'],
                        cell['col_index'],
                        cell.get('cell_value'),
                        cell.get('cell_type'),
                        cell.get('normalized_value'),
                        cell.get('column_header'),
                        cell.get('row_label'),
                        cell.get('confidence')
                    )
                    for cell in cells
                ]

                cursor.executemany("""
                    INSERT OR REPLACE INTO table_cells
                    (cell_id, table_id, row_index, col_index, cell_value, cell_type,
                     normalized_value, column_header, row_label, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_data)

            # COMMIT TRANSACTION (only if both inserts succeeded)
            self.conn.commit()

            self.logger.info(
                f"Atomically inserted table {table_id}: {len(cells)} cells "
                f"({row_count}x{col_count}, type={table_type})"
            )

            return {
                'success': True,
                'cells_stored': len(cells),
                'error': None
            }

        except (sqlite3.Error, ValueError, KeyError) as e:
            # ROLLBACK on any error (prevents orphaned metadata)
            self.conn.rollback()
            self.logger.error(
                f"Atomic table insert failed for {table_id}, transaction rolled back: {e}"
            )

            return {
                'success': False,
                'cells_stored': 0,
                'error': str(e)
            }

    def query_tables_by_source(self, source_document: str) -> List[Dict[str, Any]]:
        """
        Retrieve all tables from a specific source document.

        Args:
            source_document: Source document path

        Returns:
            List of table metadata dicts
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT table_id, source_document, source_page, table_type,
                       extraction_confidence, row_count, col_count, extracted_at
                FROM table_metadata
                WHERE source_document = ?
                ORDER BY source_page, extracted_at
            """, (source_document,))

            results = [dict(row) for row in cursor.fetchall()]
            self.logger.debug(f"Retrieved {len(results)} tables from {source_document}")
            return results

        except sqlite3.Error as e:
            self.logger.error(f"Failed to query tables by source: {e}")
            return []

    def query_table_cells(self, table_id: str,
                         column_header: Optional[str] = None,
                         cell_type: Optional[str] = None,
                         min_value: Optional[float] = None,
                         max_value: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Query table cells with optional filters (enables quantitative queries).

        Args:
            table_id: Table identifier to query
            column_header: Filter by column name (e.g., "Revenue")
            cell_type: Filter by cell type (numeric, date, text, currency)
            min_value: Minimum normalized value (for quantitative filtering)
            max_value: Maximum normalized value (for quantitative filtering)

        Returns:
            List of cell dicts matching criteria

        Example:
            # Get all revenue cells > $1B
            cells = query_table_cells(table_id, column_header="Revenue",
                                     cell_type="numeric", min_value=1000000000)
        """
        try:
            cursor = self.conn.cursor()

            # Build dynamic query with filters (parameterized to prevent SQL injection)
            query = """
                SELECT cell_id, table_id, row_index, col_index, cell_value, cell_type,
                       normalized_value, column_header, row_label, confidence, created_at
                FROM table_cells
                WHERE table_id = ?
            """
            params = [table_id]

            if column_header:
                query += " AND column_header = ?"
                params.append(column_header)

            if cell_type:
                query += " AND cell_type = ?"
                params.append(cell_type)

            if min_value is not None:
                query += " AND normalized_value >= ?"
                params.append(min_value)

            if max_value is not None:
                query += " AND normalized_value <= ?"
                params.append(max_value)

            query += " ORDER BY row_index, col_index"

            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]

            self.logger.debug(f"Retrieved {len(results)} cells from table {table_id} with filters")
            return results

        except sqlite3.Error as e:
            self.logger.error(f"Failed to query table cells: {e}")
            return []

    def query_tables_by_type(self, table_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve tables by classification type.

        Args:
            table_type: Table classification (financial_statement, insider_transactions, etc.)
            limit: Maximum number of results

        Returns:
            List of table metadata dicts
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT table_id, source_document, source_page, table_type,
                       extraction_confidence, row_count, col_count, extracted_at
                FROM table_metadata
                WHERE table_type = ?
                ORDER BY extracted_at DESC
                LIMIT ?
            """, (table_type, limit))

            results = [dict(row) for row in cursor.fetchall()]
            self.logger.debug(f"Retrieved {len(results)} tables of type {table_type}")
            return results

        except sqlite3.Error as e:
            self.logger.error(f"Failed to query tables by type: {e}")
            return []

    # ==================== TRANSACTION MANAGEMENT ====================

    def begin_transaction(self):
        """Begin a database transaction."""
        self.conn.execute("BEGIN TRANSACTION")

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.conn.rollback()

    # ==================== YAHOO FINANCE ENHANCEMENT METHODS ====================

    def insert_financial_metrics_batch(self, metrics: List[Dict[str, Any]]) -> int:
        """
        Batch insert financial metrics (Categories 1 & 4: market data + financials)

        Args:
            metrics: List of metric dicts with keys: ticker, metric_name, metric_value,
                    metric_category, period, fiscal_year, fiscal_quarter, source_document_id

        Returns:
            Number of metrics inserted
        """
        if not metrics:
            return 0

        cursor = self.conn.cursor()
        count = 0

        for metric in metrics:
            try:
                # Infer event_date from fiscal period (for date-based queries)
                event_date = self._infer_event_date_from_period(
                    metric.get('period'),
                    metric.get('fiscal_year'),
                    metric.get('fiscal_quarter')
                )

                cursor.execute("""
                    INSERT OR REPLACE INTO financial_metrics
                    (ticker, metric_name, metric_value, metric_category, period,
                     fiscal_year, fiscal_quarter, source_document_id, event_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric['ticker'],
                    metric['metric_name'],
                    metric.get('metric_value'),
                    metric.get('metric_category', 'market'),
                    metric.get('period'),
                    metric.get('fiscal_year'),
                    metric.get('fiscal_quarter'),
                    metric['source_document_id'],
                    event_date
                ))
                count += 1
            except Exception as e:
                self.logger.debug(f"Failed to insert metric {metric.get('metric_name')}: {e}")

        self.conn.commit()
        self.logger.info(f"Inserted {count} financial metrics")
        return count

    def insert_price_history_batch(self, price_records: List[Dict[str, Any]]) -> int:
        """
        Batch insert historical OHLCV data (Category 6: historical pricing)

        Args:
            price_records: List of price dicts with keys: ticker, date, open_price,
                          high_price, low_price, close_price, volume, source_document_id

        Returns:
            Number of price records inserted
        """
        if not price_records:
            return 0

        cursor = self.conn.cursor()

        try:
            # Use executemany for bulk insert performance (250 rows at once)
            cursor.executemany("""
                INSERT OR REPLACE INTO price_history
                (ticker, date, open_price, high_price, low_price, close_price,
                 volume, source_document_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    rec['ticker'],
                    rec['date'],
                    rec.get('open_price'),
                    rec.get('high_price'),
                    rec.get('low_price'),
                    rec.get('close_price'),
                    rec.get('volume'),
                    rec['source_document_id']
                )
                for rec in price_records
            ])

            self.conn.commit()
            count = len(price_records)
            self.logger.info(f"Inserted {count} price history records")
            return count

        except Exception as e:
            self.logger.error(f"Batch price insert failed: {e}")
            self.conn.rollback()
            return 0

    def get_price_history(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get historical OHLCV price data for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            start_date: Optional start date (YYYY-MM-DD format)
            end_date: Optional end date (YYYY-MM-DD format)
            limit: Maximum records to return (default: 90 days)

        Returns:
            List of price dicts sorted by date descending:
            [{'ticker': 'NVDA', 'date': '2024-03-15', 'open_price': 850.0,
              'high_price': 875.0, 'low_price': 840.0, 'close_price': 870.0,
              'volume': 15000000, 'source_document_id': 'yahoo_...'}, ...]
        """
        cursor = self.conn.cursor()

        # Build query with optional date filters
        query = """
            SELECT ticker, date, open_price, high_price, low_price, close_price,
                   volume, source_document_id
            FROM price_history
            WHERE ticker = ?
        """
        params = [ticker]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        return self._add_freshness_to_results(results)

    def get_52_week_high_low(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get 52-week high and low prices for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')

        Returns:
            Dict with 52-week statistics or None if no data:
            {
                'ticker': 'NVDA',
                '52_week_high': 950.0,
                '52_week_high_date': '2024-02-01',
                '52_week_low': 450.0,
                '52_week_low_date': '2023-05-15',
                'current_price': 870.0,
                'current_date': '2024-03-15',
                'pct_from_high': -8.4,
                'pct_from_low': 93.3,
                'data_points': 252,
                'source': 'Signal Store price_history'
            }
        """
        cursor = self.conn.cursor()

        # Calculate date 52 weeks ago
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(weeks=52)).strftime('%Y-%m-%d')

        # Get 52-week high with date
        cursor.execute("""
            SELECT high_price, date FROM price_history
            WHERE ticker = ? AND date >= ?
            ORDER BY high_price DESC LIMIT 1
        """, (ticker, cutoff_date))
        high_row = cursor.fetchone()

        # Get 52-week low with date
        cursor.execute("""
            SELECT low_price, date FROM price_history
            WHERE ticker = ? AND date >= ?
            ORDER BY low_price ASC LIMIT 1
        """, (ticker, cutoff_date))
        low_row = cursor.fetchone()

        # Get most recent price
        cursor.execute("""
            SELECT close_price, date FROM price_history
            WHERE ticker = ? ORDER BY date DESC LIMIT 1
        """, (ticker,))
        current_row = cursor.fetchone()

        # Count data points
        cursor.execute("""
            SELECT COUNT(*) FROM price_history
            WHERE ticker = ? AND date >= ?
        """, (ticker, cutoff_date))
        count = cursor.fetchone()[0]

        if not high_row or not low_row or not current_row:
            return None

        high_price = high_row['high_price']
        low_price = low_row['low_price']
        current_price = current_row['close_price']

        # Calculate percentage from high/low
        pct_from_high = ((current_price - high_price) / high_price * 100) if high_price else 0
        pct_from_low = ((current_price - low_price) / low_price * 100) if low_price else 0

        return {
            'ticker': ticker,
            '52_week_high': high_price,
            '52_week_high_date': high_row['date'],
            '52_week_low': low_price,
            '52_week_low_date': low_row['date'],
            'current_price': current_price,
            'current_date': current_row['date'],
            'pct_from_high': round(pct_from_high, 2),
            'pct_from_low': round(pct_from_low, 2),
            'data_points': count,
            'source': 'Signal Store price_history'
        }

    def insert_calendar_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Batch insert calendar events (Categories 5 & 7: earnings/dividend events)

        Args:
            events: List of event dicts with keys: ticker, event_type, event_date,
                   event_value, estimate_high, estimate_low, estimate_avg,
                   is_future, source_document_id

        Returns:
            Number of events inserted
        """
        if not events:
            return 0

        cursor = self.conn.cursor()
        count = 0

        for event in events:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO calendar_events
                    (ticker, event_type, event_date, event_value, estimate_high,
                     estimate_low, estimate_avg, is_future, source_document_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event['ticker'],
                    event['event_type'],
                    event['event_date'],
                    event.get('event_value'),
                    event.get('estimate_high'),
                    event.get('estimate_low'),
                    event.get('estimate_avg'),
                    event.get('is_future', 0),
                    event['source_document_id']
                ))
                count += 1
            except Exception as e:
                self.logger.debug(f"Failed to insert event {event.get('event_type')}: {e}")

        self.conn.commit()
        self.logger.info(f"Inserted {count} calendar events")
        return count

    # ==================== CALENDAR EVENTS QUERY METHODS ====================
    # Critical for event-driven investment analysis (Query Type 5)

    def get_events_in_date_range(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        event_type: Optional[str] = None,
        is_future: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Query calendar events within a date range for a ticker.

        Critical for investment workflows: Find earnings, dividends, and other
        catalysts within specific time windows.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            event_type: Optional filter by event type ('earnings', 'dividend', etc.)
            is_future: Optional filter for future events only

        Returns:
            List of event dictionaries with all calendar_events fields

        Example:
            >>> # Get all NVDA events in Q1 2024
            >>> events = store.get_events_in_date_range('NVDA', '2024-01-01', '2024-03-31')
            >>> # Get only earnings events
            >>> earnings = store.get_events_in_date_range('NVDA', '2024-01-01', '2024-12-31',
            ...                                          event_type='earnings')
        """
        # Validate date range
        if not self._validate_date_range(start_date, end_date):
            self.logger.warning(f"Invalid date range: {start_date} to {end_date}")
            return []

        cursor = self.conn.cursor()
        query = """
            SELECT
                id, ticker, event_type, event_date, event_value,
                estimate_high, estimate_low, estimate_avg,
                is_future, source_document_id, created_at
            FROM calendar_events
            WHERE ticker = ?
                AND event_date >= ?
                AND event_date <= ?
        """
        params = [ticker, start_date, end_date]

        # Add optional filters
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if is_future is not None:
            query += " AND is_future = ?"
            params.append(1 if is_future else 0)

        query += " ORDER BY event_date DESC"

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            event = dict(row)
            # Add temporal metadata
            event = self._add_freshness_metadata(event, timestamp_field='event_date')
            results.append(event)

        self.logger.info(f"Found {len(results)} calendar events for {ticker} between {start_date} and {end_date}")
        return results

    def get_events_near_date(
        self,
        ticker: str,
        target_date: str,
        window_days: int = 7,
        event_type: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query events within ±N days of a target date.

        Critical for analyzing market reactions around specific events.

        Args:
            ticker: Stock ticker symbol
            target_date: Target date (YYYY-MM-DD format)
            window_days: Number of days before/after target date (default: 7)
            event_type: Optional filter by event type

        Returns:
            Dict with 'before' and 'after' lists of events

        Example:
            >>> # Get events around Q2 earnings announcement
            >>> events = store.get_events_near_date('NVDA', '2024-07-15', window_days=7)
            >>> print(f"Events before: {len(events['before'])}")
            >>> print(f"Events after: {len(events['after'])}")
        """
        try:
            from datetime import datetime, timedelta

            # Parse target date
            target = datetime.strptime(target_date, '%Y-%m-%d')

            # Calculate window boundaries
            start_date = (target - timedelta(days=window_days)).strftime('%Y-%m-%d')
            end_date = (target + timedelta(days=window_days)).strftime('%Y-%m-%d')

            # Get all events in window
            all_events = self.get_events_in_date_range(
                ticker, start_date, end_date, event_type=event_type
            )

            # Split into before/after
            results = {
                'before': [],
                'after': [],
                'on_date': []
            }

            for event in all_events:
                event_dt = datetime.strptime(event['event_date'], '%Y-%m-%d')
                if event_dt < target:
                    results['before'].append(event)
                elif event_dt > target:
                    results['after'].append(event)
                else:
                    results['on_date'].append(event)

            # Sort chronologically
            results['before'].sort(key=lambda x: x['event_date'], reverse=True)  # Most recent first
            results['after'].sort(key=lambda x: x['event_date'])  # Earliest first

            self.logger.info(f"Found {len(all_events)} events near {target_date} "
                           f"(before: {len(results['before'])}, on: {len(results['on_date'])}, "
                           f"after: {len(results['after'])})")

            return results

        except ValueError as e:
            self.logger.error(f"Invalid date format: {e}")
            return {'before': [], 'on_date': [], 'after': []}

    def get_signals_around_event(
        self,
        ticker: str,
        event_date: str,
        days_before: int = 7,
        days_after: int = 7,
        signal_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get all signals (ratings, price targets, metrics) within a window around an event.

        Critical for event-driven investment analysis: How did analyst sentiment,
        price targets, and metrics change around earnings announcements?

        Args:
            ticker: Stock ticker symbol
            event_date: Event date (YYYY-MM-DD format)
            days_before: Days before event to include (default: 7)
            days_after: Days after event to include (default: 7)
            signal_types: Optional list of signal types to include
                         ['rating', 'price_target', 'metric', 'calendar_event']
                         If None, includes all types

        Returns:
            Dict with signals organized by type and temporal position:
            {
                'before': {'ratings': [...], 'price_targets': [...], ...},
                'on_date': {...},
                'after': {...},
                'summary': {
                    'rating_changes': [...],
                    'target_changes': [...],
                    'metric_changes': [...]
                }
            }

        Example:
            >>> # Analyze signals around Q2 earnings
            >>> signals = store.get_signals_around_event('NVDA', '2024-07-15')
            >>> print(f"Ratings before: {len(signals['before']['ratings'])}")
            >>> print(f"Ratings after: {len(signals['after']['ratings'])}")
            >>> # Check for upgrades/downgrades
            >>> for change in signals['summary']['rating_changes']:
            ...     print(f"{change['date']}: {change['old']} → {change['new']}")
        """
        try:
            from datetime import datetime, timedelta

            # Parse event date
            event_dt = datetime.strptime(event_date, '%Y-%m-%d')

            # Calculate window boundaries
            start_date = (event_dt - timedelta(days=days_before)).strftime('%Y-%m-%d')
            end_date = (event_dt + timedelta(days=days_after)).strftime('%Y-%m-%d')

            # Default to all signal types if not specified
            if signal_types is None:
                signal_types = ['rating', 'price_target', 'metric', 'calendar_event']

            # Initialize results structure
            results = {
                'before': {},
                'on_date': {},
                'after': {},
                'summary': {
                    'rating_changes': [],
                    'target_changes': [],
                    'metric_changes': []
                }
            }

            # Gather each signal type
            all_signals = []

            # Get ratings
            if 'rating' in signal_types:
                ratings = self.get_ratings_by_date_range(ticker, start_date, end_date)
                for rating in ratings:
                    rating['signal_type'] = 'rating'
                    rating['signal_date'] = rating.get('timestamp', rating.get('created_at'))
                    all_signals.append(rating)

            # Get price targets
            if 'price_target' in signal_types:
                targets = self.get_price_targets_by_date_range(ticker, start_date, end_date)
                for target in targets:
                    target['signal_type'] = 'price_target'
                    target['signal_date'] = target.get('timestamp', target.get('created_at'))
                    all_signals.append(target)

            # Get metrics
            if 'metric' in signal_types:
                metrics = self.get_metrics_by_date_range(ticker, start_date, end_date)
                for metric in metrics:
                    metric['signal_type'] = 'metric'
                    # Use event_date if available, otherwise created_at
                    metric['signal_date'] = metric.get('event_date', metric.get('created_at'))
                    all_signals.append(metric)

            # Get calendar events
            if 'calendar_event' in signal_types:
                events = self.get_events_in_date_range(ticker, start_date, end_date)
                for event in events:
                    event['signal_type'] = 'calendar_event'
                    event['signal_date'] = event['event_date']
                    all_signals.append(event)

            # Organize signals by temporal position
            for signal in all_signals:
                # Parse signal date
                signal_date_str = signal['signal_date']
                if signal_date_str:
                    # Handle datetime strings (remove time component)
                    if 'T' in signal_date_str or ' ' in signal_date_str:
                        signal_date_str = signal_date_str.split('T')[0].split(' ')[0]

                    try:
                        signal_dt = datetime.strptime(signal_date_str, '%Y-%m-%d')

                        # Determine temporal position
                        if signal_dt < event_dt:
                            position = 'before'
                        elif signal_dt > event_dt:
                            position = 'after'
                        else:
                            position = 'on_date'

                        # Initialize signal type list if needed
                        signal_type = signal['signal_type'] + 's'  # Pluralize
                        if signal_type not in results[position]:
                            results[position][signal_type] = []

                        results[position][signal_type].append(signal)
                    except ValueError:
                        self.logger.warning(f"Could not parse signal date: {signal_date_str}")

            # Analyze changes (simplified - can be enhanced)
            self._analyze_signal_changes(results, event_dt)

            # Count totals
            total_before = sum(len(v) for v in results['before'].values() if isinstance(v, list))
            total_on = sum(len(v) for v in results['on_date'].values() if isinstance(v, list))
            total_after = sum(len(v) for v in results['after'].values() if isinstance(v, list))

            self.logger.info(f"Found {total_before + total_on + total_after} signals around {event_date} "
                           f"(before: {total_before}, on: {total_on}, after: {total_after})")

            return results

        except ValueError as e:
            self.logger.error(f"Invalid date format: {e}")
            return {
                'before': {}, 'on_date': {}, 'after': {},
                'summary': {'rating_changes': [], 'target_changes': [], 'metric_changes': []}
            }

    def _analyze_signal_changes(self, results: Dict, event_dt: datetime) -> None:
        """
        Analyze how signals changed around the event.
        Helper method for get_signals_around_event.
        """
        # Analyze rating changes
        before_ratings = results['before'].get('ratings', [])
        after_ratings = results['after'].get('ratings', [])

        if before_ratings and after_ratings:
            # Get most recent before and after
            last_before = before_ratings[0] if before_ratings else None
            first_after = after_ratings[0] if after_ratings else None

            if last_before and first_after:
                if last_before.get('rating') != first_after.get('rating'):
                    results['summary']['rating_changes'].append({
                        'date': first_after.get('signal_date'),
                        'old': last_before.get('rating'),
                        'new': first_after.get('rating'),
                        'analyst': first_after.get('analyst'),
                        'firm': first_after.get('firm')
                    })

        # Analyze price target changes
        before_targets = results['before'].get('price_targets', [])
        after_targets = results['after'].get('price_targets', [])

        if before_targets and after_targets:
            last_target = before_targets[0] if before_targets else None
            first_after = after_targets[0] if after_targets else None

            if last_target and first_after:
                old_price = last_target.get('target_price', 0)
                new_price = first_after.get('target_price', 0)

                if old_price and new_price and old_price != new_price:
                    pct_change = ((new_price - old_price) / old_price) * 100
                    results['summary']['target_changes'].append({
                        'date': first_after.get('signal_date'),
                        'old': old_price,
                        'new': new_price,
                        'pct_change': round(pct_change, 2),
                        'analyst': first_after.get('analyst'),
                        'firm': first_after.get('firm')
                    })

    # ==================== TEMPORAL COMPARISON METHODS ====================

    def compare_yoy(self, ticker: str, metric_name: str,
                    year: int, quarter: Optional[int] = None) -> Dict[str, Any]:
        """
        Compare year-over-year (YoY) metrics for a ticker.

        Compares metrics from the specified period with the same period
        in the previous year. Supports both quarterly and annual comparisons.

        Args:
            ticker: Stock ticker symbol
            metric_name: Name of the metric to compare (e.g., 'Revenue', 'Net Income')
            year: The current year to compare
            quarter: Optional quarter (1-4). If None, compares full years

        Returns:
            Dict containing:
                - current_period: Current period data and value
                - previous_period: Previous period data and value
                - absolute_change: Absolute difference
                - percent_change: Percentage change
                - growth_rate: Annualized growth rate for multi-year

        Example:
            >>> store = SignalStore()
            >>> # Compare Q2 2024 vs Q2 2023 revenue
            >>> yoy = store.compare_yoy('FICO', 'Revenue', 2024, 2)
            >>> print(f"YoY Growth: {yoy['percent_change']:.1f}%")
        """
        cursor = self.conn.cursor()

        # Construct period strings
        if quarter:
            current_period = f"Q{quarter} {year}"
            previous_period = f"Q{quarter} {year - 1}"
            period_label = f"Q{quarter}"
        else:
            current_period = f"FY{year}"
            previous_period = f"FY{year - 1}"
            period_label = "Annual"

        # Query current period (financial_metrics doesn't have source/confidence columns)
        current_data = cursor.execute("""
            SELECT metric_value, period, event_date, created_at, source_document_id
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ? AND period = ?
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT 1
        """, (ticker, metric_name, current_period)).fetchone()

        # Query previous period
        previous_data = cursor.execute("""
            SELECT metric_value, period, event_date, created_at, source_document_id
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ? AND period = ?
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT 1
        """, (ticker, metric_name, previous_period)).fetchone()

        result = {
            'ticker': ticker,
            'metric_name': metric_name,
            'comparison_type': 'YoY',
            'period_label': period_label,
            'current_period': None,
            'previous_period': None,
            'absolute_change': None,
            'percent_change': None,
            'growth_direction': None
        }

        if current_data:
            result['current_period'] = {
                'period': current_period,
                'value': current_data['metric_value'],
                'date': current_data['event_date'] or current_data['created_at'],
                'source_document_id': current_data.get('source_document_id'),
                'confidence': 0.8  # Default confidence for financial metrics
            }

        if previous_data:
            result['previous_period'] = {
                'period': previous_period,
                'value': previous_data['metric_value'],
                'date': previous_data['event_date'] or previous_data['created_at'],
                'source_document_id': previous_data.get('source_document_id'),
                'confidence': 0.8  # Default confidence for financial metrics
            }

        # Calculate changes if both periods have data
        if current_data and previous_data:
            current_val = current_data['metric_value']
            previous_val = previous_data['metric_value']

            # Always calculate absolute change
            result['absolute_change'] = current_val - previous_val

            # Percentage change only meaningful when signs don't change and denominator != 0
            if previous_val != 0:
                # Check for sign change (undefined percentage growth)
                if (previous_val < 0 and current_val > 0) or (previous_val > 0 and current_val < 0):
                    result['percent_change'] = None  # Sign change makes percentage undefined
                    result['note'] = 'turnaround' if previous_val < 0 else 'turned_to_loss'
                else:
                    # No sign change - calculate percentage normally (without abs())
                    result['percent_change'] = ((current_val - previous_val) / previous_val) * 100

                result['growth_direction'] = 'up' if current_val > previous_val else 'down' if current_val < previous_val else 'flat'

        return result

    def compare_qoq(self, ticker: str, metric_name: str,
                    year: int, quarter: int) -> Dict[str, Any]:
        """
        Compare quarter-over-quarter (QoQ) metrics for a ticker.

        Compares metrics from the specified quarter with the previous quarter,
        handling year boundaries appropriately.

        Args:
            ticker: Stock ticker symbol
            metric_name: Name of the metric to compare
            year: Year of the current quarter
            quarter: Current quarter (1-4)

        Returns:
            Dict containing QoQ comparison data similar to compare_yoy

        Example:
            >>> store = SignalStore()
            >>> # Compare Q2 2024 vs Q1 2024 revenue
            >>> qoq = store.compare_qoq('FICO', 'Revenue', 2024, 2)
            >>> print(f"QoQ Growth: {qoq['percent_change']:.1f}%")
        """
        cursor = self.conn.cursor()

        # Calculate previous quarter
        if quarter == 1:
            prev_quarter = 4
            prev_year = year - 1
        else:
            prev_quarter = quarter - 1
            prev_year = year

        current_period = f"Q{quarter} {year}"
        previous_period = f"Q{prev_quarter} {prev_year}"

        # Query current quarter (financial_metrics doesn't have source/confidence columns)
        current_data = cursor.execute("""
            SELECT metric_value, period, event_date, created_at, source_document_id
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ? AND period = ?
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT 1
        """, (ticker, metric_name, current_period)).fetchone()

        # Query previous quarter
        previous_data = cursor.execute("""
            SELECT metric_value, period, event_date, created_at, source_document_id
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ? AND period = ?
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT 1
        """, (ticker, metric_name, previous_period)).fetchone()

        result = {
            'ticker': ticker,
            'metric_name': metric_name,
            'comparison_type': 'QoQ',
            'current_quarter': f"Q{quarter} {year}",
            'previous_quarter': f"Q{prev_quarter} {prev_year}",
            'current_period': None,
            'previous_period': None,
            'absolute_change': None,
            'percent_change': None,
            'growth_direction': None,
            'seasonality_note': None
        }

        # Add seasonality note for Q4 to Q1 transitions
        if quarter == 1:
            result['seasonality_note'] = 'Year-end to Q1 transition - seasonality effects possible'

        if current_data:
            result['current_period'] = {
                'period': current_period,
                'value': current_data['metric_value'],
                'date': current_data['event_date'] or current_data['created_at'],
                'source_document_id': current_data.get('source_document_id'),
                'confidence': 0.8  # Default confidence for financial metrics
            }

        if previous_data:
            result['previous_period'] = {
                'period': previous_period,
                'value': previous_data['metric_value'],
                'date': previous_data['event_date'] or previous_data['created_at'],
                'source_document_id': previous_data.get('source_document_id'),
                'confidence': 0.8  # Default confidence for financial metrics
            }

        # Calculate changes
        if current_data and previous_data:
            current_val = current_data['metric_value']
            previous_val = previous_data['metric_value']

            # Always calculate absolute change
            result['absolute_change'] = current_val - previous_val

            # Percentage change only meaningful when signs don't change and denominator != 0
            if previous_val != 0:
                # Check for sign change (undefined percentage growth)
                if (previous_val < 0 and current_val > 0) or (previous_val > 0 and current_val < 0):
                    result['percent_change'] = None  # Sign change makes percentage undefined
                    result['note'] = 'turnaround' if previous_val < 0 else 'turned_to_loss'
                else:
                    # No sign change - calculate percentage normally (without abs())
                    result['percent_change'] = ((current_val - previous_val) / previous_val) * 100

                result['growth_direction'] = 'up' if current_val > previous_val else 'down' if current_val < previous_val else 'flat'

        return result

    def calculate_growth_rate(self, ticker: str, metric_name: str,
                             start_year: int, end_year: int,
                             quarter: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate compound annual growth rate (CAGR) for a metric over multiple periods.

        Args:
            ticker: Stock ticker symbol
            metric_name: Name of the metric to analyze
            start_year: Starting year for calculation
            end_year: Ending year for calculation
            quarter: Optional quarter for quarterly CAGR

        Returns:
            Dict containing:
                - cagr: Compound annual growth rate (percentage)
                - total_growth: Total growth percentage
                - periods: Number of periods analyzed
                - start_value: Starting value
                - end_value: Ending value

        Example:
            >>> store = SignalStore()
            >>> # Calculate 3-year revenue CAGR
            >>> growth = store.calculate_growth_rate('FICO', 'Revenue', 2021, 2024)
            >>> print(f"3-Year CAGR: {growth['cagr']:.1f}%")
        """
        cursor = self.conn.cursor()

        # Construct period strings
        if quarter:
            start_period = f"Q{quarter} {start_year}"
            end_period = f"Q{quarter} {end_year}"
        else:
            start_period = f"FY{start_year}"
            end_period = f"FY{end_year}"

        # Get start value
        start_data = cursor.execute("""
            SELECT metric_value, period, event_date, created_at
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ? AND period = ?
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT 1
        """, (ticker, metric_name, start_period)).fetchone()

        # Get end value
        end_data = cursor.execute("""
            SELECT metric_value, period, event_date, created_at
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ? AND period = ?
            ORDER BY COALESCE(event_date, created_at) DESC
            LIMIT 1
        """, (ticker, metric_name, end_period)).fetchone()

        result = {
            'ticker': ticker,
            'metric_name': metric_name,
            'start_period': start_period,
            'end_period': end_period,
            'years': end_year - start_year,
            'cagr': None,
            'total_growth': None,
            'start_value': None,
            'end_value': None,
            'data_availability': 'incomplete'
        }

        if start_data:
            result['start_value'] = start_data['metric_value']

        if end_data:
            result['end_value'] = end_data['metric_value']

        # Calculate CAGR if both values exist
        if start_data and end_data:
            start_val = start_data['metric_value']
            end_val = end_data['metric_value']
            years = end_year - start_year

            # CAGR only valid for positive values (compound growth undefined for negatives)
            if start_val and start_val > 0 and end_val and end_val > 0 and years > 0:
                # CAGR = (End Value / Start Value)^(1 / Years) - 1
                cagr = (pow(end_val / start_val, 1 / years) - 1) * 100
                total_growth = ((end_val - start_val) / start_val) * 100

                result['cagr'] = round(cagr, 2)
                result['total_growth'] = round(total_growth, 2)
                result['data_availability'] = 'complete'

                # Add growth classification
                if cagr > 20:
                    result['growth_classification'] = 'high_growth'
                elif cagr > 10:
                    result['growth_classification'] = 'moderate_growth'
                elif cagr > 0:
                    result['growth_classification'] = 'low_growth'
                elif cagr == 0:
                    result['growth_classification'] = 'flat'
                else:
                    result['growth_classification'] = 'declining'
            else:
                # CAGR cannot be calculated - provide absolute metrics instead
                result['data_availability'] = 'partial'
                if start_val and end_val:
                    result['absolute_change'] = end_val - start_val
                    if start_val <= 0 or end_val <= 0:
                        result['note'] = 'CAGR undefined for non-positive values - use absolute_change'

        return result

    # ==================== PERIOD GENERATION UTILITIES ====================

    def get_trailing_quarters(self, num_quarters: int = 4,
                            from_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate list of trailing quarters from a given date.

        Args:
            num_quarters: Number of quarters to generate
            from_date: Reference date (defaults to today)

        Returns:
            List of dicts with quarter info (period, start_date, end_date)

        Example:
            >>> store = SignalStore()
            >>> quarters = store.get_trailing_quarters(4)
            >>> # Returns: [{'period': 'Q3 2024', 'start': '2024-07-01', ...}, ...]
        """
        if from_date:
            ref_date = datetime.strptime(from_date, '%Y-%m-%d')
        else:
            ref_date = datetime.now()

        quarters = []
        current_quarter = (ref_date.month - 1) // 3 + 1
        current_year = ref_date.year

        for i in range(num_quarters):
            # Calculate quarter and year
            q = current_quarter - i
            y = current_year

            while q <= 0:
                q += 4
                y -= 1

            # Determine quarter dates
            quarter_starts = {1: '-01-01', 2: '-04-01', 3: '-07-01', 4: '-10-01'}
            quarter_ends = {1: '-03-31', 2: '-06-30', 3: '-09-30', 4: '-12-31'}

            quarters.append({
                'period': f'Q{q} {y}',
                'quarter': q,
                'year': y,
                'start_date': f'{y}{quarter_starts[q]}',
                'end_date': f'{y}{quarter_ends[q]}',
                'announcement_date': self._infer_event_date_from_period(f'Q{q} {y}')
            })

        return quarters

    def get_fiscal_years(self, num_years: int = 3,
                        from_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate list of fiscal years.

        Args:
            num_years: Number of years to generate
            from_year: Starting year (defaults to current year)

        Returns:
            List of dicts with fiscal year info

        Example:
            >>> store = SignalStore()
            >>> years = store.get_fiscal_years(3)
            >>> # Returns: [{'period': 'FY2024', ...}, {'period': 'FY2023', ...}, ...]
        """
        if from_year:
            start_year = from_year
        else:
            start_year = datetime.now().year

        years = []
        for i in range(num_years):
            year = start_year - i
            years.append({
                'period': f'FY{year}',
                'year': year,
                'start_date': f'{year}-01-01',
                'end_date': f'{year}-12-31',
                'announcement_date': f'{year + 1}-02-15'  # Typical annual report date
            })

        return years

    def generate_comparison_periods(self, ticker: str, metric_name: str,
                                   comparison_type: str = 'yoy',
                                   lookback_periods: int = 4) -> List[Dict[str, Any]]:
        """
        Generate period pairs for systematic comparison analysis.

        Args:
            ticker: Stock ticker symbol
            metric_name: Metric to compare
            comparison_type: 'yoy', 'qoq', or 'sequential'
            lookback_periods: Number of comparison pairs to generate

        Returns:
            List of comparison period pairs with actual data availability

        Example:
            >>> store = SignalStore()
            >>> comparisons = store.generate_comparison_periods('FICO', 'Revenue', 'yoy', 4)
            >>> for comp in comparisons:
            >>>     print(f"{comp['current']} vs {comp['previous']}: {comp['has_data']}")
        """
        cursor = self.conn.cursor()
        comparisons = []

        # Get available periods from database
        available_periods = cursor.execute("""
            SELECT DISTINCT period
            FROM financial_metrics
            WHERE ticker = ? AND metric_name = ?
            ORDER BY COALESCE(event_date, created_at) DESC
        """, (ticker, metric_name)).fetchall()

        period_set = {p['period'] for p in available_periods}

        if comparison_type == 'yoy':
            quarters = self.get_trailing_quarters(lookback_periods * 4)
            for i in range(0, len(quarters) - 4, 4):
                current = quarters[i]['period']
                previous = quarters[i + 4]['period']
                comparisons.append({
                    'current_period': current,
                    'previous_period': previous,
                    'comparison_type': 'YoY',
                    'has_current_data': current in period_set,
                    'has_previous_data': previous in period_set,
                    'has_both': current in period_set and previous in period_set
                })

        elif comparison_type == 'qoq':
            quarters = self.get_trailing_quarters(lookback_periods + 1)
            for i in range(len(quarters) - 1):
                current = quarters[i]['period']
                previous = quarters[i + 1]['period']
                comparisons.append({
                    'current_period': current,
                    'previous_period': previous,
                    'comparison_type': 'QoQ',
                    'has_current_data': current in period_set,
                    'has_previous_data': previous in period_set,
                    'has_both': current in period_set and previous in period_set
                })

        elif comparison_type == 'sequential':
            # Get all periods and create sequential pairs
            if len(available_periods) >= 2:
                for i in range(len(available_periods) - 1):
                    comparisons.append({
                        'current_period': available_periods[i]['period'],
                        'previous_period': available_periods[i + 1]['period'],
                        'comparison_type': 'Sequential',
                        'has_both': True  # By definition from database
                    })

        return comparisons

    # ==================== DATA MIGRATION & BACKFILL UTILITIES ====================

    def backfill_event_dates(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Backfill event_date for existing financial_metrics and metrics rows.

        For legacy data inserted before temporal enhancements (2025-11-18),
        this method infers and populates event_date from fiscal period information.

        Args:
            dry_run: If True, only count rows that would be updated (no actual changes)

        Returns:
            Dict with counts of rows updated per table

        Example:
            >>> store = SignalStore()
            >>> # Preview what would be updated
            >>> preview = store.backfill_event_dates(dry_run=True)
            >>> print(f"Would update {preview['financial_metrics']} financial_metrics")
            >>> # Actually update
            >>> result = store.backfill_event_dates(dry_run=False)
            >>> print(f"Updated {result['financial_metrics']} rows")
        """
        cursor = self.conn.cursor()
        results = {}

        # Backfill financial_metrics table
        if dry_run:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM financial_metrics
                WHERE event_date IS NULL
                  AND (period IS NOT NULL OR (fiscal_year IS NOT NULL AND fiscal_quarter IS NOT NULL))
            """)
            results['financial_metrics'] = cursor.fetchone()['count']
        else:
            # Atomic transaction wraps both table updates
            with self.conn:
                # Process financial_metrics in batches to avoid memory issues
                cursor.execute("""
                    SELECT id, period, fiscal_year, fiscal_quarter
                    FROM financial_metrics
                    WHERE event_date IS NULL
                      AND (period IS NOT NULL OR (fiscal_year IS NOT NULL AND fiscal_quarter IS NOT NULL))
                """)

                updated_fm = 0
                while True:
                    batch = cursor.fetchmany(1000)
                    if not batch:
                        break

                    for row in batch:
                        inferred_date = self._infer_event_date_from_period(
                            row['period'],
                            row['fiscal_year'],
                            row['fiscal_quarter']
                        )

                        if inferred_date:
                            cursor.execute("""
                                UPDATE financial_metrics
                                SET event_date = ?
                                WHERE id = ?
                            """, (inferred_date, row['id']))
                            updated_fm += 1

                results['financial_metrics'] = updated_fm
                self.logger.info(f"Backfilled event_date for {updated_fm} financial_metrics rows")

                # Process metrics table in same transaction
                cursor.execute("""
                    SELECT id, period
                    FROM metrics
                    WHERE event_date IS NULL AND period IS NOT NULL
                """)

                updated_m = 0
                while True:
                    batch = cursor.fetchmany(1000)
                    if not batch:
                        break

                    for row in batch:
                        inferred_date = self._infer_event_date_from_period(row['period'], None, None)

                        if inferred_date:
                            cursor.execute("""
                                UPDATE metrics
                                SET event_date = ?
                                WHERE id = ?
                            """, (inferred_date, row['id']))
                            updated_m += 1

                results['metrics'] = updated_m
                self.logger.info(f"Backfilled event_date for {updated_m} metrics rows")

        # Backfill metrics table (if period info available)
        if dry_run:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM metrics
                WHERE event_date IS NULL AND period IS NOT NULL
            """)
            results['metrics'] = cursor.fetchone()['count']

        return results

    # ==================== RECENCY-AWARE RANKING METHODS ====================

    def get_latest_signals_ranked(
        self,
        ticker: str,
        signal_types: Optional[List[str]] = None,
        limit: int = 20,
        freshness_weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get latest signals for a ticker ranked by composite of freshness + confidence.

        CRITICAL FOR INVESTMENT WORKFLOWS: Surfaces most relevant RECENT signals first.
        Unlike chronological sorting, this prevents missing important fresh signals buried
        in history.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            signal_types: Filter by signal types: ['rating', 'price_target', 'metric']
                         If None, returns all signal types
            limit: Maximum number of signals to return (default: 20)
            freshness_weight: Weight for freshness vs confidence (default: 0.5)
                             0.0 = pure confidence ranking
                             0.5 = balanced (recommended for investment decisions)
                             1.0 = pure recency ranking

        Returns:
            List of signals sorted by composite_rank DESC, with ranking metadata

        Example:
            >>> # Get top 10 most relevant recent signals for NVDA
            >>> signals = store.get_latest_signals_ranked('NVDA', limit=10, freshness_weight=0.6)
            >>> for sig in signals:
            ...     print(f"{sig['signal_type']}: {sig['composite_rank']:.3f} "
            ...           f"(fresh={sig['freshness_score']:.3f}, conf={sig['confidence']:.3f})")
            rating: 0.875 (fresh=0.95, conf=0.80)
            price_target: 0.820 (fresh=0.92, conf=0.72)
        """
        if signal_types is None:
            signal_types = ['rating', 'price_target', 'metric']

        all_signals = []

        # Collect ratings
        if 'rating' in signal_types:
            ratings = self.get_rating_history(ticker, limit=limit * 2)  # Get more than needed
            for r in ratings:
                r['signal_type'] = 'rating'
                r['signal_value'] = r.get('rating', 'N/A')
            all_signals.extend(ratings)

        # Collect price targets
        if 'price_target' in signal_types:
            targets = self.get_price_target_history(ticker, limit=limit * 2)
            for t in targets:
                t['signal_type'] = 'price_target'
                t['signal_value'] = f"${t.get('target_price', 0):.2f}"
            all_signals.extend(targets)

        # Collect metrics
        if 'metric' in signal_types:
            metrics = self.get_metrics_by_ticker(ticker, limit=limit * 2)
            for m in metrics:
                m['signal_type'] = 'metric'
                m['signal_value'] = f"{m.get('metric_type', 'N/A')}: {m.get('metric_value', 'N/A')}"
            all_signals.extend(metrics)

        # Calculate composite rank for each signal
        for signal in all_signals:
            # Robust NULL handling: .get() returns None if value is NULL in DB
            # Use 'or' pattern to provide fallback for None values
            freshness = signal.get('freshness_score') or 0.0
            confidence = signal.get('confidence') or 0.5  # Default 0.5 for NULL/missing

            # Log warning if confidence was NULL (data quality issue)
            if signal.get('confidence') is None:
                self.logger.debug(f"NULL confidence for {signal.get('signal_type')} signal, using default 0.5")

            # Preserve calculated fallback values back to signal dict
            signal['freshness_score'] = freshness  # Ensures non-None freshness
            signal['confidence'] = confidence      # Ensures non-None confidence (0.5 for NULL)

            # Composite rank: weighted average of freshness + confidence
            signal['composite_rank'] = (
                freshness_weight * freshness +
                (1 - freshness_weight) * confidence
            )

        # Sort by composite rank (highest first) and limit
        ranked_signals = sorted(all_signals, key=lambda x: x['composite_rank'], reverse=True)[:limit]

        self.logger.info(f"Ranked {len(ranked_signals)} signals for {ticker} "
                        f"(freshness_weight={freshness_weight:.2f})")

        return ranked_signals

    # ==================== UTILITY METHODS ====================

    def close(self):
        """Close database connection."""
        self.conn.close()
        self.logger.info("Signal Store connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            try:
                self.rollback()
            except Exception:
                pass  # Rollback might fail if no transaction started
        else:
            try:
                self.commit()  # Commit successful operations
            except Exception:
                pass
        self.close()
