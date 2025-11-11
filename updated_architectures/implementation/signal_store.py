# Location: updated_architectures/implementation/signal_store.py
# Purpose: SQLite-based Signal Store for structured investment intelligence queries
# Why: Enable fast (<1s) lookups for ratings, price targets, and financial metrics vs LightRAG semantic search (~12s)
# Relevant Files: data_ingestion.py, ice_simplified.py, query_router.py

import sqlite3
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


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

        # Indexes for metrics table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ticker ON metrics(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ticker_type ON metrics(ticker, metric_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ticker_period ON metrics(ticker, period)")

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

        self.conn.commit()
        self.logger.info("Signal Store tables created successfully")

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
        Get the most recent rating for a ticker.

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
                'source_document_id': 'email_12345'
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
            return dict(row)
        return None

    def get_rating_history(
        self,
        ticker: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get rating history for a ticker (most recent first).

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of ratings to return (default: 10)

        Returns:
            List of rating dicts sorted by timestamp descending
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, analyst, firm, rating, confidence, timestamp, source_document_id
            FROM ratings
            WHERE ticker = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (ticker, limit))

        return [dict(row) for row in cursor.fetchall()]

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
        Get the most recent price target for a ticker.

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
                'source_document_id': 'email_12345'
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
            return dict(row)
        return None

    def get_price_target_history(
        self,
        ticker: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get price target history for a ticker (most recent first).

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of targets to return (default: 10)

        Returns:
            List of price target dicts sorted by timestamp descending
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ticker, analyst, firm, target_price, currency, confidence, timestamp, source_document_id
            FROM price_targets
            WHERE ticker = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (ticker, limit))

        return [dict(row) for row in cursor.fetchall()]

    def count_price_targets(self) -> int:
        """
        Count total number of price targets in Signal Store.

        Returns:
            Total price target count
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM price_targets")
        return cursor.fetchone()[0]

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
