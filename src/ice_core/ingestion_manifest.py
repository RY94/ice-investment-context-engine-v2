# Location: /src/ice_core/ingestion_manifest.py
# Purpose: Document deduplication manifest for tracking ingested content and preventing duplicates
# Why: Enables incremental updates without re-processing existing documents when portfolio changes
# Relevant Files: ice_simplified.py, data_ingestion.py, ice_building_workflow.ipynb

"""
Ingestion Manifest System for ICE

Tracks all ingested documents with content hashing to prevent duplicate processing.
Supports incremental updates and portfolio change tracking.

Key Features:
- Content-based deduplication using SHA256 hashing
- Portfolio history tracking
- Temporal metadata for time-based queries
- API data coverage tracking
- Automatic backup and recovery
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class IngestionManifest:
    """
    Document tracking manifest for intelligent incremental updates.

    Prevents duplicate ingestion and tracks portfolio evolution.
    """

    VERSION = "2.1"  # Manifest schema version (2.1: added fetch_history for incremental updates)

    def __init__(self, storage_dir: Path):
        """
        Initialize manifest with storage directory.

        Args:
            storage_dir: Directory to store manifest file (e.g., src/ice_lightrag/storage)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.manifest_path = self.storage_dir / ".ingestion_manifest.json"
        self.backup_path = self.storage_dir / ".ingestion_manifest.json.bak"

        self.manifest = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        """Load existing manifest or create new one."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r') as f:
                    manifest = json.load(f)

                # Validate and potentially migrate schema
                if manifest.get('version') != self.VERSION:
                    manifest = self._migrate_manifest(manifest)

                logger.info(f"Loaded manifest with {len(manifest['documents'])} documents")
                return manifest

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Corrupt manifest, attempting backup recovery: {e}")

                # Try backup
                if self.backup_path.exists():
                    with open(self.backup_path, 'r') as f:
                        manifest = json.load(f)
                        logger.info("Recovered from backup manifest")
                        return manifest

        # Create new manifest
        logger.info("Creating new ingestion manifest")
        return self._create_empty_manifest()

    def _create_empty_manifest(self) -> Dict[str, Any]:
        """Create empty manifest with current schema."""
        return {
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "documents": {},
            "portfolio_history": [],
            "api_data_coverage": {},
            "fetch_history": {},  # NEW v2.1: Track (ticker, source, data_type) → fetch metadata
            "statistics": {
                "total_documents": 0,
                "total_emails": 0,
                "total_api_documents": 0,
                "unique_tickers": []
            }
        }

    def _migrate_manifest(self, old_manifest: Dict) -> Dict:
        """Migrate old manifest schema to current version."""
        logger.info(f"Migrating manifest from v{old_manifest.get('version', '1.0')} to v{self.VERSION}")

        # Handle v1.0 → v2.0 migration
        if not old_manifest.get('version') or old_manifest.get('version') == "1.0":
            # Add temporal metadata to documents
            for doc_id, doc_meta in old_manifest.get('documents', {}).items():
                if 'email_date' not in doc_meta:
                    doc_meta['email_date'] = doc_meta.get('ingested_at')
                if 'portfolio_relevance' not in doc_meta:
                    doc_meta['portfolio_relevance'] = 0.5

            # Add statistics section
            old_manifest['statistics'] = self._calculate_statistics(old_manifest)

        # Handle v2.0 → v2.1 migration
        if old_manifest.get('version') in ["2.0", "1.0", None]:
            # Add fetch_history for incremental updates
            if 'fetch_history' not in old_manifest:
                old_manifest['fetch_history'] = {}
                logger.info("Added fetch_history tracking for incremental updates")

        old_manifest['version'] = self.VERSION
        return old_manifest

    def compute_content_hash(self, content: str) -> str:
        """
        Compute SHA256 hash of content for deduplication.

        Args:
            content: Document content to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_document_id(self, source_type: str, identifier: str) -> str:
        """
        Generate consistent document ID.

        Args:
            source_type: Type of source (email, api, url, sec)
            identifier: Unique identifier (filename, URL, API call ID)

        Returns:
            Standardized document ID
        """
        return f"{source_type}:{identifier}"

    def is_document_ingested(self, doc_id: str) -> bool:
        """Check if document has been ingested."""
        return doc_id in self.manifest['documents']

    def is_content_duplicate(self, content: str) -> bool:
        """Check if content (by hash) already exists."""
        content_hash = self.compute_content_hash(content)

        for doc_meta in self.manifest['documents'].values():
            if doc_meta.get('content_hash') == content_hash:
                return True
        return False

    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add document to manifest.

        Args:
            doc_id: Document identifier
            content: Document content (for hashing)
            metadata: Optional metadata (source_type, ticker, email_date, etc.)

        Returns:
            Document entry that was added
        """
        content_hash = self.compute_content_hash(content)

        # Check for duplicate content with different ID
        for existing_id, existing_meta in self.manifest['documents'].items():
            if existing_meta.get('content_hash') == content_hash and existing_id != doc_id:
                logger.warning(f"Content duplicate detected: {doc_id} has same content as {existing_id}")

        now = datetime.now(timezone.utc).isoformat()

        doc_entry = {
            "ingested_at": now,
            "content_hash": content_hash,
            "source_type": metadata.get('source_type', 'unknown'),
            "metadata": metadata or {}
        }

        # Add temporal metadata if available
        if 'email_date' in metadata:
            doc_entry['email_date'] = metadata['email_date']
        if 'ticker' in metadata:
            doc_entry['ticker'] = metadata['ticker']
        if 'portfolio_relevance' in metadata:
            doc_entry['portfolio_relevance'] = metadata['portfolio_relevance']

        self.manifest['documents'][doc_id] = doc_entry
        self.manifest['last_updated'] = now

        # Update statistics
        self._update_statistics()

        logger.debug(f"Added document to manifest: {doc_id}")
        return doc_entry

    def get_portfolio_delta(self, new_holdings: List[str]) -> Dict[str, Any]:
        """
        Calculate portfolio changes.

        Args:
            new_holdings: New portfolio holdings

        Returns:
            Delta information including added/removed tickers
        """
        if not self.manifest['portfolio_history']:
            # First portfolio
            return {
                'added': new_holdings,
                'removed': [],
                'kept': [],
                'is_first': True
            }

        last_portfolio = self.manifest['portfolio_history'][-1]['holdings']

        return {
            'added': list(set(new_holdings) - set(last_portfolio)),
            'removed': list(set(last_portfolio) - set(new_holdings)),
            'kept': list(set(new_holdings) & set(last_portfolio)),
            'is_first': False
        }

    def update_portfolio(self, holdings: List[str]) -> None:
        """Record portfolio snapshot."""
        entry = {
            "date": datetime.now(timezone.utc).isoformat(),
            "holdings": holdings
        }

        self.manifest['portfolio_history'].append(entry)
        self.manifest['last_updated'] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Updated portfolio: {holdings}")

    def update_api_coverage(self, ticker: str, data_types: Dict[str, int]) -> None:
        """
        Track API data fetched per ticker.

        Args:
            ticker: Stock ticker
            data_types: Dict of data type to count (e.g., {'news': 2, 'financial': 2})
        """
        if ticker not in self.manifest['api_data_coverage']:
            self.manifest['api_data_coverage'][ticker] = {}

        for data_type, count in data_types.items():
            current = self.manifest['api_data_coverage'][ticker].get(data_type, 0)
            self.manifest['api_data_coverage'][ticker][data_type] = current + count

    def get_new_documents(
        self,
        available_docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter documents to only new ones not in manifest.

        Args:
            available_docs: List of documents with 'id' and 'content' fields

        Returns:
            Only documents not yet ingested
        """
        new_docs = []

        for doc in available_docs:
            doc_id = doc.get('id')
            content = doc.get('content', '')

            if not doc_id:
                logger.warning("Document missing ID, skipping")
                continue

            # Check both ID and content hash
            if not self.is_document_ingested(doc_id):
                # Also check if content is duplicate
                if not self.is_content_duplicate(content):
                    new_docs.append(doc)
                else:
                    logger.info(f"Skipping {doc_id} - content already ingested")
            else:
                logger.debug(f"Skipping {doc_id} - already in manifest")

        logger.info(f"Filtered to {len(new_docs)} new documents from {len(available_docs)} available")
        return new_docs

    def get_updated_documents(
        self,
        available_docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find documents whose content has changed.

        Args:
            available_docs: List of documents to check

        Returns:
            Documents with updated content
        """
        updated_docs = []

        for doc in available_docs:
            doc_id = doc.get('id')
            content = doc.get('content', '')

            if doc_id in self.manifest['documents']:
                old_hash = self.manifest['documents'][doc_id].get('content_hash')
                new_hash = self.compute_content_hash(content)

                if old_hash != new_hash:
                    logger.info(f"Document {doc_id} content has changed")
                    updated_docs.append(doc)

        return updated_docs

    def _update_statistics(self) -> None:
        """Update manifest statistics."""
        stats = self.manifest['statistics']

        stats['total_documents'] = len(self.manifest['documents'])

        # Count by type
        email_count = sum(
            1 for d in self.manifest['documents'].values()
            if d.get('source_type') == 'email'
        )
        api_count = sum(
            1 for d in self.manifest['documents'].values()
            if d.get('source_type') in ['api', 'api_news', 'api_financial', 'api_sec']
        )

        stats['total_emails'] = email_count
        stats['total_api_documents'] = api_count

        # Unique tickers
        tickers = set()
        for doc_meta in self.manifest['documents'].values():
            if 'ticker' in doc_meta:
                tickers.add(doc_meta['ticker'])
        stats['unique_tickers'] = sorted(list(tickers))

    def _calculate_statistics(self, manifest: Dict) -> Dict[str, Any]:
        """Calculate statistics for migration."""
        return {
            "total_documents": len(manifest.get('documents', {})),
            "total_emails": 0,
            "total_api_documents": 0,
            "unique_tickers": []
        }

    def get_fetch_key(self, ticker: str, source: str, data_type: str) -> str:
        """Generate consistent key for fetch_history tracking."""
        return f"{ticker}:{source}:{data_type}"

    def get_last_fetch(self, ticker: str, source: str, data_type: str) -> Optional[Dict[str, Any]]:
        """
        Get last fetch metadata for incremental updates.

        Args:
            ticker: Stock ticker
            source: Data source (newsapi, finnhub, yahoo, sec)
            data_type: Type of data (news, financial, filings)

        Returns:
            Fetch metadata dict with last_fetch_date, date_range_start, date_range_end, document_count
            or None if never fetched
        """
        fetch_key = self.get_fetch_key(ticker, source, data_type)
        return self.manifest['fetch_history'].get(fetch_key)

    def update_fetch_history(
        self,
        ticker: str,
        source: str,
        data_type: str,
        date_range_start: str,
        date_range_end: str,
        document_count: int,
        requested_lookback_days: Optional[int] = None
    ) -> None:
        """
        Record fetch metadata for incremental update tracking.

        Args:
            ticker: Stock ticker
            source: Data source (newsapi, finnhub, yahoo, sec)
            data_type: Type of data (news, financial, filings)
            date_range_start: ISO date string for range start
            date_range_end: ISO date string for range end
            document_count: Number of documents fetched
            requested_lookback_days: Original lookback period requested
        """
        fetch_key = self.get_fetch_key(ticker, source, data_type)
        now = datetime.now(timezone.utc).isoformat()

        fetch_entry = {
            "last_fetch_date": now,
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
            "document_count": document_count,
            "requested_lookback_days": requested_lookback_days,
            "fetch_count": self.manifest['fetch_history'].get(fetch_key, {}).get('fetch_count', 0) + 1
        }

        self.manifest['fetch_history'][fetch_key] = fetch_entry
        self.manifest['last_updated'] = now

        logger.debug(f"Updated fetch history: {fetch_key} → {document_count} docs in {date_range_start} to {date_range_end}")

    def get_coverage_status(
        self,
        ticker: str,
        source: str,
        data_type: str,
        requested_lookback_days: int
    ) -> Dict[str, Any]:
        """
        Check coverage completeness for validation.

        Args:
            ticker: Stock ticker
            source: Data source
            data_type: Type of data
            requested_lookback_days: Desired lookback period

        Returns:
            Coverage status dict with completeness ratio and gap information
        """
        fetch_meta = self.get_last_fetch(ticker, source, data_type)

        if not fetch_meta:
            return {
                "has_coverage": False,
                "completeness": 0.0,
                "gap_days": requested_lookback_days,
                "message": "No previous fetch"
            }

        # Parse dates
        try:
            # Ensure dates are timezone-aware (UTC)
            date_end_str = fetch_meta['date_range_end']
            date_start_str = fetch_meta['date_range_start']

            # Parse dates as naive then make timezone-aware
            if 'T' in date_end_str:
                date_end = datetime.fromisoformat(date_end_str.replace('Z', '+00:00'))
                date_start = datetime.fromisoformat(date_start_str.replace('Z', '+00:00'))
            else:
                # Date-only strings (YYYY-MM-DD) - parse and make timezone-aware
                date_end = datetime.strptime(date_end_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                date_start = datetime.strptime(date_start_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)

            # Calculate coverage
            coverage_days = (date_end - date_start).days
            gap_days = (now - date_end).days  # Days since last fetch

            # Completeness: How much of requested lookback is covered
            completeness = min(1.0, coverage_days / requested_lookback_days) if requested_lookback_days > 0 else 1.0

            return {
                "has_coverage": True,
                "completeness": completeness,
                "gap_days": gap_days,
                "coverage_days": coverage_days,
                "last_fetch_date": fetch_meta['last_fetch_date'],
                "document_count": fetch_meta['document_count'],
                "message": f"{completeness*100:.0f}% coverage, {gap_days} days since last fetch"
            }

        except (ValueError, KeyError) as e:
            logger.warning(f"Error parsing fetch metadata: {e}")
            return {
                "has_coverage": False,
                "completeness": 0.0,
                "gap_days": requested_lookback_days,
                "message": "Error parsing metadata"
            }

    def get_fetch_window(
        self,
        ticker: str,
        source: str,
        data_type: str,
        requested_lookback_days: int,
        current_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal fetch window for incremental updates (KEY METHOD FOR 80% API REDUCTION).

        Args:
            ticker: Stock ticker
            source: Data source
            data_type: Type of data
            requested_lookback_days: Desired total lookback period
            current_date: Current date (defaults to now)

        Returns:
            Dict with fetch_start, fetch_end, is_incremental, and strategy
        """
        # Ensure current_date is timezone-aware
        if current_date is None:
            current_date = datetime.now(timezone.utc)
        elif current_date.tzinfo is None:
            current_date = current_date.replace(tzinfo=timezone.utc)

        fetch_meta = self.get_last_fetch(ticker, source, data_type)

        if not fetch_meta:
            # First fetch - full window
            fetch_start = current_date - timedelta(days=requested_lookback_days)
            fetch_end = current_date
            return {
                "fetch_start": fetch_start.strftime('%Y-%m-%d'),
                "fetch_end": fetch_end.strftime('%Y-%m-%d'),
                "is_incremental": False,
                "strategy": "full_initial",
                "savings_percent": 0
            }

        # Parse last fetch metadata
        try:
            # Ensure dates are timezone-aware (UTC)
            date_end_str = fetch_meta['date_range_end']
            date_start_str = fetch_meta['date_range_start']

            # Parse dates and ensure timezone-aware
            if 'T' in date_end_str:
                last_end = datetime.fromisoformat(date_end_str.replace('Z', '+00:00'))
                last_start = datetime.fromisoformat(date_start_str.replace('Z', '+00:00'))
            else:
                # Date-only strings (YYYY-MM-DD) - parse and make timezone-aware
                last_end = datetime.strptime(date_end_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                last_start = datetime.strptime(date_start_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

            # Calculate desired full window
            desired_start = current_date - timedelta(days=requested_lookback_days)

            # Incremental strategy: Only fetch gap from last_end to current_date
            if last_end >= desired_start:
                # We have sufficient historical coverage, just fetch new data
                fetch_start = last_end  # Start where we left off
                fetch_end = current_date

                days_to_fetch = (fetch_end - fetch_start).days
                savings_percent = (1 - days_to_fetch / requested_lookback_days) * 100 if requested_lookback_days > 0 else 0

                return {
                    "fetch_start": fetch_start.strftime('%Y-%m-%d'),
                    "fetch_end": fetch_end.strftime('%Y-%m-%d'),
                    "is_incremental": True,
                    "strategy": "incremental_gap",
                    "days_to_fetch": days_to_fetch,
                    "savings_percent": savings_percent,
                    "message": f"Incremental: Fetching {days_to_fetch} new days (saving {savings_percent:.0f}%)"
                }
            else:
                # Historical coverage insufficient, need full refetch
                fetch_start = desired_start
                fetch_end = current_date
                return {
                    "fetch_start": fetch_start.strftime('%Y-%m-%d'),
                    "fetch_end": fetch_end.strftime('%Y-%m-%d'),
                    "is_incremental": False,
                    "strategy": "full_refetch",
                    "savings_percent": 0,
                    "message": "Full refetch needed (last fetch too old)"
                }

        except (ValueError, KeyError) as e:
            logger.warning(f"Error calculating fetch window: {e}, falling back to full fetch")
            fetch_start = current_date - timedelta(days=requested_lookback_days)
            fetch_end = current_date
            return {
                "fetch_start": fetch_start.strftime('%Y-%m-%d'),
                "fetch_end": fetch_end.strftime('%Y-%m-%d'),
                "is_incremental": False,
                "strategy": "full_fallback",
                "savings_percent": 0
            }

    def save(self) -> None:
        """Save manifest to disk with backup."""
        try:
            # Create backup first
            if self.manifest_path.exists():
                import shutil
                shutil.copy(self.manifest_path, self.backup_path)
                logger.debug("Created manifest backup")

            # Save manifest
            with open(self.manifest_path, 'w') as f:
                json.dump(self.manifest, f, indent=2, default=str)

            logger.info(f"Saved manifest with {len(self.manifest['documents'])} documents")

        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
            raise

    def get_summary(self) -> Dict[str, Any]:
        """Get manifest summary for reporting."""
        return {
            "total_documents": len(self.manifest['documents']),
            "statistics": self.manifest['statistics'],
            "portfolio_history": self.manifest['portfolio_history'],
            "api_coverage": self.manifest['api_data_coverage'],
            "last_updated": self.manifest['last_updated']
        }

    def rebuild_from_sources(self) -> None:
        """
        Rebuild manifest by re-scanning source directories.

        Used for recovery if manifest becomes corrupted.
        """
        logger.warning("Rebuilding manifest from sources - this may take time")

        # Reset manifest
        self.manifest = self._create_empty_manifest()

        # TODO: Implement source scanning logic based on your data directories
        # This would scan:
        # - data/emails_samples/*.eml
        # - API cache files
        # - Downloaded documents

        logger.info("Manifest rebuild complete")
        self.save()