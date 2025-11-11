#!/usr/bin/env python3
# Location: /scripts/backfill_metadata.py
# Purpose: Backfill metadata.json for existing documents in data/attachments/
# Why: Adds origin tracking to 95+ existing documents without metadata.json
# Relevant Files: attachment_processor.py, intelligent_link_processor.py

import json
import logging
from pathlib import Path
from datetime import datetime
import magic

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def infer_source_type(email_uid: str, filename: str) -> str:
    """
    Infer source type from filename patterns.

    URL PDFs: Filenames like abc123def456_1730716800.pdf (hash_timestamp.pdf)
    Email Attachments: Regular filenames like "Quarterly Report.pdf"
    """
    import re

    # Pattern: {12-char hash}_{unix timestamp}.{extension}
    url_pattern = r'^[a-f0-9]{12}_\d{10}\.\w+$'

    if re.match(url_pattern, filename):
        return "url_pdf"
    else:
        return "email_attachment"

def get_mime_type(file_path: Path) -> str:
    """Get MIME type using python-magic"""
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(str(file_path))
    except Exception as e:
        logger.warning(f"Failed to detect MIME type for {file_path}: {e}")
        # Fallback based on extension
        ext = file_path.suffix.lower()
        mime_map = {
            '.pdf': 'application/pdf',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
        }
        return mime_map.get(ext, 'application/octet-stream')

def create_metadata_for_document(storage_dir: Path, email_uid: str, file_hash: str) -> bool:
    """
    Create metadata.json for a single document.

    Returns True if metadata was created, False if it already existed or failed.
    """
    metadata_path = storage_dir / 'metadata.json'

    # Skip if metadata already exists
    if metadata_path.exists():
        logger.debug(f"Skipping {storage_dir} - metadata.json already exists")
        return False

    # Find the original file
    original_dir = storage_dir / 'original'
    if not original_dir.exists():
        logger.warning(f"Skipping {storage_dir} - no original/ directory")
        return False

    # Get the first file in original/ directory
    original_files = list(original_dir.iterdir())
    if not original_files:
        logger.warning(f"Skipping {storage_dir} - original/ directory is empty")
        return False

    original_file = original_files[0]
    filename = original_file.name

    # Infer source type
    source_type = infer_source_type(email_uid, filename)

    # Get file info
    file_size = original_file.stat().st_size
    mime_type = get_mime_type(original_file)

    # Check for extracted.txt
    extracted_path = storage_dir / 'extracted.txt'
    text_chars = 0
    has_extracted_text = False

    if extracted_path.exists():
        try:
            with open(extracted_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
                text_chars = len(text_content)
                has_extracted_text = True
        except Exception as e:
            logger.warning(f"Failed to read extracted.txt in {storage_dir}: {e}")

    # Build metadata structure
    metadata = {
        "source_type": source_type,
        "source_context": {
            "email_uid": email_uid,
        },
        "file_info": {
            "original_filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "mime_type": mime_type
        },
        "processing": {
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "text_chars": text_chars,
            "backfilled": True,
            "backfill_timestamp": datetime.now().isoformat()
        },
        "storage": {
            "original_path": f"original/{filename}",
            "extracted_text_path": "extracted.txt" if has_extracted_text else None,
            "created_at": datetime.now().isoformat()
        }
    }

    # Add source-specific context
    if source_type == "url_pdf":
        metadata["source_context"]["download_method"] = "unknown"
        metadata["source_context"]["note"] = "Backfilled from existing file - original URL not available"
    else:
        metadata["source_context"]["email_subject"] = "Unknown"
        metadata["source_context"]["email_date"] = "Unknown"
        metadata["source_context"]["note"] = "Backfilled from existing file - original email metadata not available"

    # Write metadata.json
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✅ Created metadata for {source_type}: {email_uid}/{file_hash[:8]}... ({filename})")
        return True
    except Exception as e:
        logger.error(f"Failed to create metadata.json for {storage_dir}: {e}")
        return False

def backfill_all_metadata(attachments_dir: Path) -> dict:
    """
    Backfill metadata.json for all documents in data/attachments/.

    Returns statistics about the backfill operation.
    """
    stats = {
        'total_scanned': 0,
        'already_had_metadata': 0,
        'created_metadata': 0,
        'failed': 0,
        'by_source_type': {
            'email_attachment': 0,
            'url_pdf': 0
        }
    }

    # Scan all email_uid directories
    for email_uid_dir in attachments_dir.iterdir():
        if not email_uid_dir.is_dir():
            continue

        email_uid = email_uid_dir.name

        # Scan all file_hash directories
        for file_hash_dir in email_uid_dir.iterdir():
            if not file_hash_dir.is_dir():
                continue

            file_hash = file_hash_dir.name
            stats['total_scanned'] += 1

            # Check if metadata already exists
            metadata_path = file_hash_dir / 'metadata.json'
            if metadata_path.exists():
                stats['already_had_metadata'] += 1
                continue

            # Create metadata
            success = create_metadata_for_document(file_hash_dir, email_uid, file_hash)

            if success:
                stats['created_metadata'] += 1

                # Update source type stats
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        source_type = metadata.get('source_type', 'unknown')
                        if source_type in stats['by_source_type']:
                            stats['by_source_type'][source_type] += 1
                except:
                    pass
            else:
                stats['failed'] += 1

    return stats

def main():
    """Main entry point for backfill script"""
    # Get attachments directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    attachments_dir = project_root / 'data' / 'attachments'

    if not attachments_dir.exists():
        logger.error(f"Attachments directory not found: {attachments_dir}")
        return

    logger.info(f"Starting backfill of metadata.json in {attachments_dir}")
    logger.info("=" * 60)

    # Run backfill
    stats = backfill_all_metadata(attachments_dir)

    # Print summary
    logger.info("=" * 60)
    logger.info("Backfill Summary:")
    logger.info(f"  Total documents scanned: {stats['total_scanned']}")
    logger.info(f"  Already had metadata: {stats['already_had_metadata']}")
    logger.info(f"  Created metadata: {stats['created_metadata']}")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info("")
    logger.info("By source type:")
    logger.info(f"  Email attachments: {stats['by_source_type']['email_attachment']}")
    logger.info(f"  URL PDFs: {stats['by_source_type']['url_pdf']}")
    logger.info("=" * 60)

    if stats['created_metadata'] > 0:
        logger.info(f"✅ Successfully backfilled {stats['created_metadata']} documents")
    else:
        logger.info("ℹ️  No documents needed backfilling")

if __name__ == '__main__':
    main()
