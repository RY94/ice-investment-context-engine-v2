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
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class IngestionManifest:
    """
    Document tracking manifest for intelligent incremental updates.

    Prevents duplicate ingestion and tracks portfolio evolution.
    """

    VERSION = "2.0"  # Manifest schema version

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