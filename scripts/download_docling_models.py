# Location: scripts/download_docling_models.py
# Purpose: Pre-download docling AI models before first use
# Why: Avoid timeout/network issues during production PDF conversion
# Relevant Files: src/ice_docling/sec_filing_processor.py, docling_processor.py

"""
Docling Model Pre-Loader

Downloads docling AI models (~500MB) to local cache before first use.
Run this once after installing docling to avoid conversion timeouts.

Models Downloaded:
- DocLayNet: Layout analysis model (~100MB)
- TableFormer: Table extraction model (~150MB)
- Granite-Docling VLM: Vision-language model (~250MB)

Total Size: ~500MB
Cache Location: ~/.cache/huggingface/hub/

Usage:
    python scripts/download_docling_models.py

First Run: Downloads models (5-10 minutes)
Subsequent Runs: Verifies models already cached
"""

import sys
from pathlib import Path
import tempfile
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def download_models():
    """Download docling models by converting a dummy document"""

    logger.info("=" * 60)
    logger.info("📦 Docling Model Pre-Loader")
    logger.info("=" * 60)
    logger.info("")
    logger.info("This script will download docling AI models (~500MB)")
    logger.info("Cache location: ~/.cache/huggingface/hub/")
    logger.info("Estimated time: 5-10 minutes on first run")
    logger.info("")

    try:
        # Check if docling is installed
        logger.info("[1/4] Checking docling installation...")
        try:
            from docling.document_converter import DocumentConverter
            logger.info("✅ Docling is installed")
        except ImportError as e:
            logger.error("❌ Docling not installed")
            logger.error("Install with: pip install docling")
            return False

        # Create converter (triggers model download if not cached)
        logger.info("")
        logger.info("[2/4] Initializing DocumentConverter...")
        logger.info("      (This will download models if not already cached)")
        converter = DocumentConverter()
        logger.info("✅ DocumentConverter initialized")

        # Create dummy test file (markdown format - supported by docling)
        logger.info("")
        logger.info("[3/4] Creating test document...")
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w') as f:
            f.write("# Test Document\n\n")
            f.write("This is a test document for docling model download verification.\n\n")
            f.write("This file will be deleted after model download is complete.\n")
            test_file = f.name
        logger.info(f"✅ Test file created: {test_file}")

        # Convert test file (downloads models on first run, uses cache on subsequent runs)
        logger.info("")
        logger.info("[4/4] Converting test document...")
        logger.info("      (Models will be downloaded now if not cached)")
        logger.info("")

        result = converter.convert(test_file)

        logger.info("")
        logger.info("✅ Test conversion complete!")

        # Cleanup
        Path(test_file).unlink()
        logger.info("✅ Test file cleaned up")

        # Success message
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎉 SUCCESS: Docling models ready!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Models cached at: ~/.cache/huggingface/hub/")
        logger.info("Total cache size: ~500MB")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. You can now use docling in ICE without download delays")
        logger.info("  2. Toggle via: export USE_DOCLING_SEC=true (default)")
        logger.info("  3. Toggle via: export USE_DOCLING_EMAIL=true (default)")
        logger.info("")

        return True

    except Exception as e:
        logger.error("")
        logger.error("=" * 60)
        logger.error("❌ Model download failed")
        logger.error("=" * 60)
        logger.error(f"Error: {str(e)}")
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("  1. Check internet connection")
        logger.error("  2. Verify disk space (need ~1GB free)")
        logger.error("  3. Check Hugging Face access: https://huggingface.co")
        logger.error("  4. Try again with: python scripts/download_docling_models.py")
        logger.error("")
        return False

if __name__ == "__main__":
    logger.info("")
    success = download_models()
    logger.info("")

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
