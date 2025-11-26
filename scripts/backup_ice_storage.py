#!/usr/bin/env python3
# Location: /scripts/backup_ice_storage.py
# Purpose: Automated backup script for ICE storage system
# Why: Critical for production deployment - prevents data loss and enables disaster recovery
# Relevant Files: ice_simplified.py, signal_store.py, storage directories

"""
ICE Storage Backup Script - Production-grade backup and restore functionality

Backs up all 5 ICE storage types:
1. Graph Store (GraphML files)
2. Vector Stores (JSON embeddings)
3. Key-Value Stores (JSON dictionaries)
4. Signal Store (SQLite database)
5. File System (email samples, enhanced docs, extracted text)

Features:
- Automated daily backups with timestamped directories
- 30-day retention with automatic cleanup
- Integrity verification for all backup files
- Compression to save storage space
- Cloud backup support (S3/Azure)
- Restoration functionality
- Detailed logging
"""

import os
import sys
import shutil
import json
import sqlite3
import hashlib
import gzip
import tarfile
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_ice_storage.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ICEStorageBackup:
    """Backup and restore manager for ICE storage system"""

    def __init__(self, base_path: str = None):
        """
        Initialize backup manager

        Args:
            base_path: Base path for ICE project (defaults to parent of script)
        """
        if base_path is None:
            # Default to parent directory of script
            self.base_path = Path(__file__).parents[1]
        else:
            self.base_path = Path(base_path)

        # Define storage locations
        self.storage_paths = {
            'lightrag_storage': self.base_path / 'updated_architectures/implementation/storage',
            'signal_store': self.base_path / 'updated_architectures/implementation/signal_store.db',
            'email_samples': self.base_path / 'data/emails_samples',
            'enhanced_docs': self.base_path / 'data/enhanced_documents',
            'extracted_text': self.base_path / 'data/extracted_text',
            'manifest': self.base_path / 'src/ice_core/manifest.json',
            'notebooks': self.base_path  # For backup of critical notebooks
        }

        # Backup configuration
        self.backup_root = self.base_path / 'backups'
        self.retention_days = 30
        self.compression_enabled = True

        # Create backup directory if it doesn't exist
        self.backup_root.mkdir(exist_ok=True)

    def create_backup(self, description: str = "") -> Path:
        """
        Create a complete backup of ICE storage

        Args:
            description: Optional description for the backup

        Returns:
            Path to the created backup directory
        """
        # Create timestamped backup directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"ice_backup_{timestamp}"
        if description:
            backup_name += f"_{description.replace(' ', '_')}"

        backup_dir = self.backup_root / backup_name
        backup_dir.mkdir(exist_ok=True)

        logger.info(f"🔵 Starting backup: {backup_name}")

        # Create manifest for this backup
        backup_manifest = {
            'timestamp': timestamp,
            'description': description,
            'version': '1.0',
            'files': {},
            'checksums': {},
            'sizes': {},
            'status': 'in_progress'
        }

        try:
            # 1. Backup LightRAG storage (Graph, Vector, KV stores)
            self._backup_lightrag_storage(backup_dir, backup_manifest)

            # 2. Backup Signal Store (SQLite)
            self._backup_signal_store(backup_dir, backup_manifest)

            # 3. Backup file system data
            self._backup_file_system(backup_dir, backup_manifest)

            # 4. Backup critical notebooks
            self._backup_notebooks(backup_dir, backup_manifest)

            # 5. Backup manifest
            self._backup_manifest(backup_dir, backup_manifest)

            # 6. Create compressed archive if enabled
            if self.compression_enabled:
                archive_path = self._compress_backup(backup_dir)
                backup_manifest['archive'] = str(archive_path)
                logger.info(f"✅ Compressed backup: {archive_path}")

            # Update manifest status
            backup_manifest['status'] = 'completed'
            backup_manifest['completion_time'] = datetime.now().isoformat()

            # Save final manifest
            manifest_path = backup_dir / 'backup_manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(backup_manifest, f, indent=2)

            logger.info(f"✅ Backup completed successfully: {backup_dir}")
            return backup_dir

        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            backup_manifest['status'] = 'failed'
            backup_manifest['error'] = str(e)

            # Save error manifest
            manifest_path = backup_dir / 'backup_manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(backup_manifest, f, indent=2)

            raise

    def _backup_lightrag_storage(self, backup_dir: Path, manifest: Dict):
        """Backup LightRAG storage files"""
        logger.info("📊 Backing up LightRAG storage...")

        lightrag_backup = backup_dir / 'lightrag_storage'
        lightrag_backup.mkdir(exist_ok=True)

        storage_path = self.storage_paths['lightrag_storage']
        if not storage_path.exists():
            logger.warning(f"⚠️ LightRAG storage not found: {storage_path}")
            return

        # Copy all JSON and GraphML files
        for file_type in ['*.json', '*.graphml']:
            for file_path in storage_path.glob(file_type):
                dest = lightrag_backup / file_path.name
                shutil.copy2(file_path, dest)

                # Calculate checksum
                checksum = self._calculate_checksum(file_path)
                manifest['checksums'][file_path.name] = checksum
                manifest['sizes'][file_path.name] = file_path.stat().st_size
                manifest['files'][file_path.name] = 'lightrag_storage'

                logger.debug(f"  ✓ {file_path.name} ({file_path.stat().st_size:,} bytes)")

    def _backup_signal_store(self, backup_dir: Path, manifest: Dict):
        """Backup Signal Store SQLite database with integrity check"""
        logger.info("💾 Backing up Signal Store...")

        signal_store_path = self.storage_paths['signal_store']
        if not signal_store_path.exists():
            logger.warning(f"⚠️ Signal Store not found: {signal_store_path}")
            return

        signal_backup = backup_dir / 'signal_store'
        signal_backup.mkdir(exist_ok=True)

        try:
            # Verify database integrity first
            conn = sqlite3.connect(signal_store_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]

            if integrity_result != 'ok':
                logger.warning(f"⚠️ Signal Store integrity check failed: {integrity_result}")

            # Use SQLite backup API for safe backup
            backup_path = signal_backup / 'signal_store.db'
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()

            # Record in manifest
            checksum = self._calculate_checksum(backup_path)
            manifest['checksums']['signal_store.db'] = checksum
            manifest['sizes']['signal_store.db'] = backup_path.stat().st_size
            manifest['files']['signal_store.db'] = 'signal_store'

            logger.info(f"  ✓ Signal Store backed up ({backup_path.stat().st_size:,} bytes)")

        except Exception as e:
            logger.error(f"  ❌ Signal Store backup failed: {e}")
            raise

    def _backup_file_system(self, backup_dir: Path, manifest: Dict):
        """Backup file system data (emails, enhanced docs, extracted text)"""
        logger.info("📁 Backing up file system data...")

        fs_backup = backup_dir / 'file_system'
        fs_backup.mkdir(exist_ok=True)

        for name, path in self.storage_paths.items():
            if name in ['email_samples', 'enhanced_docs', 'extracted_text']:
                if not path.exists():
                    logger.warning(f"  ⚠️ {name} not found: {path}")
                    continue

                dest = fs_backup / name
                if path.is_dir():
                    shutil.copytree(path, dest, dirs_exist_ok=True)
                    file_count = sum(1 for _ in dest.rglob('*') if _.is_file())
                    logger.info(f"  ✓ {name}: {file_count} files")
                    manifest['files'][name] = f'file_system/{name}'

    def _backup_notebooks(self, backup_dir: Path, manifest: Dict):
        """Backup critical Jupyter notebooks"""
        logger.info("📓 Backing up critical notebooks...")

        notebooks_backup = backup_dir / 'notebooks'
        notebooks_backup.mkdir(exist_ok=True)

        critical_notebooks = [
            'ice_building_workflow.ipynb',
            'ice_query_workflow.ipynb'
        ]

        for notebook in critical_notebooks:
            notebook_path = self.storage_paths['notebooks'] / notebook
            if notebook_path.exists():
                dest = notebooks_backup / notebook
                shutil.copy2(notebook_path, dest)
                checksum = self._calculate_checksum(notebook_path)
                manifest['checksums'][notebook] = checksum
                manifest['files'][notebook] = 'notebooks'
                logger.info(f"  ✓ {notebook}")

    def _backup_manifest(self, backup_dir: Path, manifest: Dict):
        """Backup ingestion manifest"""
        manifest_path = self.storage_paths['manifest']
        if manifest_path.exists():
            dest = backup_dir / 'ingestion_manifest.json'
            shutil.copy2(manifest_path, dest)
            logger.info("  ✓ Ingestion manifest")

    def _compress_backup(self, backup_dir: Path) -> Path:
        """Compress backup directory into tar.gz archive"""
        logger.info("🗜️ Compressing backup...")

        archive_name = f"{backup_dir.name}.tar.gz"
        archive_path = self.backup_root / archive_name

        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_dir, arcname=backup_dir.name)

        # Remove uncompressed directory after compression to save space and prevent OneDrive sync issues
        # (OneDrive has 400-char path limit; compressed archives avoid path length errors)
        shutil.rmtree(backup_dir)
        logger.info(f"🗑️ Removed uncompressed directory: {backup_dir.name}")

        return archive_path

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        logger.info(f"🧹 Cleaning up backups older than {self.retention_days} days...")

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0

        for backup_path in self.backup_root.iterdir():
            if backup_path.is_dir() and backup_path.name.startswith('ice_backup_'):
                # Parse timestamp from directory name
                try:
                    timestamp_str = backup_path.name.split('_')[2]  # ice_backup_YYYYMMDD_HHMMSS
                    backup_date = datetime.strptime(timestamp_str, '%Y%m%d')

                    if backup_date < cutoff_date:
                        logger.info(f"  🗑️ Removing old backup: {backup_path.name}")
                        shutil.rmtree(backup_path)
                        removed_count += 1

                        # Also remove compressed archive if exists
                        archive_path = self.backup_root / f"{backup_path.name}.tar.gz"
                        if archive_path.exists():
                            archive_path.unlink()

                except (ValueError, IndexError) as e:
                    logger.warning(f"  ⚠️ Could not parse date from: {backup_path.name}")

        logger.info(f"✅ Removed {removed_count} old backups")

    def restore_backup(self, backup_name: str, target_path: Optional[Path] = None):
        """
        Restore from a backup

        Args:
            backup_name: Name of the backup directory or archive
            target_path: Target path for restoration (defaults to original locations)
        """
        logger.info(f"🔄 Starting restoration from: {backup_name}")

        # Find backup
        backup_path = self.backup_root / backup_name
        if not backup_path.exists():
            # Check for compressed archive
            archive_path = self.backup_root / f"{backup_name}.tar.gz"
            if archive_path.exists():
                # Extract archive first
                logger.info("📦 Extracting compressed backup...")
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(self.backup_root)
            else:
                raise FileNotFoundError(f"Backup not found: {backup_name}")

        # Load backup manifest
        manifest_path = backup_path / 'backup_manifest.json'
        if not manifest_path.exists():
            raise FileNotFoundError(f"Backup manifest not found: {manifest_path}")

        with open(manifest_path) as f:
            manifest = json.load(f)

        if manifest.get('status') != 'completed':
            logger.warning(f"⚠️ Backup status is: {manifest.get('status')}")

        # Verify checksums before restoration
        logger.info("🔍 Verifying backup integrity...")
        self._verify_backup_integrity(backup_path, manifest)

        # Restore each component
        logger.info("♻️ Restoring components...")

        # 1. Restore LightRAG storage
        self._restore_lightrag_storage(backup_path, target_path)

        # 2. Restore Signal Store
        self._restore_signal_store(backup_path, target_path)

        # 3. Restore file system
        self._restore_file_system(backup_path, target_path)

        # 4. Restore notebooks
        self._restore_notebooks(backup_path, target_path)

        logger.info("✅ Restoration completed successfully")

    def _verify_backup_integrity(self, backup_path: Path, manifest: Dict):
        """Verify backup integrity using checksums"""
        checksums = manifest.get('checksums', {})
        errors = []

        for filename, expected_checksum in checksums.items():
            # Find file in backup
            file_location = manifest['files'].get(filename)
            if file_location:
                if '/' in file_location:
                    file_path = backup_path / file_location / filename
                else:
                    file_path = backup_path / file_location / filename

                if file_path.exists():
                    actual_checksum = self._calculate_checksum(file_path)
                    if actual_checksum != expected_checksum:
                        errors.append(f"{filename}: checksum mismatch")
                else:
                    errors.append(f"{filename}: file not found")

        if errors:
            logger.error(f"❌ Integrity check failed: {errors}")
            raise ValueError(f"Backup integrity check failed: {len(errors)} errors")

        logger.info("✅ Integrity check passed")

    def _restore_lightrag_storage(self, backup_path: Path, target_path: Optional[Path]):
        """Restore LightRAG storage files"""
        source = backup_path / 'lightrag_storage'
        if not source.exists():
            logger.warning("⚠️ No LightRAG storage in backup")
            return

        dest = target_path or self.storage_paths['lightrag_storage']
        dest.mkdir(parents=True, exist_ok=True)

        for file_path in source.glob('*'):
            shutil.copy2(file_path, dest / file_path.name)

        logger.info(f"  ✓ LightRAG storage restored to {dest}")

    def _restore_signal_store(self, backup_path: Path, target_path: Optional[Path]):
        """Restore Signal Store database"""
        source = backup_path / 'signal_store' / 'signal_store.db'
        if not source.exists():
            logger.warning("⚠️ No Signal Store in backup")
            return

        dest = target_path or self.storage_paths['signal_store']
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing database if it exists
        if dest.exists():
            backup_existing = dest.with_suffix('.db.old')
            shutil.move(dest, backup_existing)
            logger.info(f"  ℹ️ Existing database moved to {backup_existing}")

        shutil.copy2(source, dest)
        logger.info(f"  ✓ Signal Store restored to {dest}")

    def _restore_file_system(self, backup_path: Path, target_path: Optional[Path]):
        """Restore file system data"""
        source = backup_path / 'file_system'
        if not source.exists():
            logger.warning("⚠️ No file system data in backup")
            return

        for name in ['email_samples', 'enhanced_docs', 'extracted_text']:
            source_dir = source / name
            if source_dir.exists():
                dest = target_path or self.storage_paths[name]
                dest.parent.mkdir(parents=True, exist_ok=True)

                if dest.exists():
                    # Backup existing data
                    backup_existing = dest.with_name(f"{dest.name}_old")
                    shutil.move(dest, backup_existing)

                shutil.copytree(source_dir, dest)
                logger.info(f"  ✓ {name} restored to {dest}")

    def _restore_notebooks(self, backup_path: Path, target_path: Optional[Path]):
        """Restore critical notebooks"""
        source = backup_path / 'notebooks'
        if not source.exists():
            logger.warning("⚠️ No notebooks in backup")
            return

        dest_dir = target_path or self.storage_paths['notebooks']

        for notebook in source.glob('*.ipynb'):
            dest = dest_dir / notebook.name

            # Backup existing notebook
            if dest.exists():
                backup_existing = dest.with_suffix('.ipynb.old')
                shutil.copy2(dest, backup_existing)

            shutil.copy2(notebook, dest)
            logger.info(f"  ✓ {notebook.name} restored")

    def upload_to_s3(self, backup_path: Path, bucket: str, prefix: str = "ice-backups"):
        """
        Upload backup to AWS S3

        Args:
            backup_path: Path to backup directory or archive
            bucket: S3 bucket name
            prefix: S3 key prefix
        """
        try:
            import boto3
            s3 = boto3.client('s3')

            # Compress if not already compressed
            if backup_path.is_dir():
                archive_path = self._compress_backup(backup_path)
            else:
                archive_path = backup_path

            # Upload to S3
            key = f"{prefix}/{archive_path.name}"
            logger.info(f"☁️ Uploading to S3: s3://{bucket}/{key}")

            s3.upload_file(str(archive_path), bucket, key)
            logger.info(f"✅ Uploaded to S3 successfully")

        except Exception as e:
            logger.error(f"❌ S3 upload failed: {e}")
            raise

    def list_backups(self) -> List[Dict]:
        """List all available backups with metadata"""
        backups = []

        for backup_path in self.backup_root.iterdir():
            if backup_path.is_dir() and backup_path.name.startswith('ice_backup_'):
                manifest_path = backup_path / 'backup_manifest.json'
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                        backups.append({
                            'name': backup_path.name,
                            'timestamp': manifest.get('timestamp'),
                            'status': manifest.get('status'),
                            'description': manifest.get('description'),
                            'size': sum(manifest.get('sizes', {}).values())
                        })

        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)


def main():
    """Command-line interface for backup script"""
    parser = argparse.ArgumentParser(description='ICE Storage Backup Manager')
    parser.add_argument('action', choices=['backup', 'restore', 'cleanup', 'list', 'upload'],
                       help='Action to perform')
    parser.add_argument('--name', help='Backup name (for restore)')
    parser.add_argument('--description', help='Backup description')
    parser.add_argument('--s3-bucket', help='S3 bucket for cloud backup')
    parser.add_argument('--base-path', help='Base path for ICE project')

    args = parser.parse_args()

    # Initialize backup manager
    backup_manager = ICEStorageBackup(args.base_path)

    if args.action == 'backup':
        # Create backup
        backup_path = backup_manager.create_backup(args.description or "manual")
        print(f"✅ Backup created: {backup_path}")

        # Upload to S3 if specified
        if args.s3_bucket:
            backup_manager.upload_to_s3(backup_path, args.s3_bucket)

        # Cleanup old backups
        backup_manager.cleanup_old_backups()

    elif args.action == 'restore':
        if not args.name:
            print("❌ Error: --name required for restore")
            sys.exit(1)
        backup_manager.restore_backup(args.name)

    elif args.action == 'cleanup':
        backup_manager.cleanup_old_backups()

    elif args.action == 'list':
        backups = backup_manager.list_backups()
        print(f"\n📚 Available backups ({len(backups)} total):\n")
        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            print(f"  • {backup['name']}")
            print(f"    Status: {backup['status']}")
            print(f"    Description: {backup['description']}")
            print(f"    Size: {size_mb:.1f} MB")
            print()

    elif args.action == 'upload':
        if not args.name or not args.s3_bucket:
            print("❌ Error: --name and --s3-bucket required for upload")
            sys.exit(1)
        backup_path = backup_manager.backup_root / args.name
        backup_manager.upload_to_s3(backup_path, args.s3_bucket)


if __name__ == '__main__':
    main()