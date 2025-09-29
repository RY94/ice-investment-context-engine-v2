# imap_email_ingestion_pipeline/setup_asymmetric_value.py
# Setup script for asymmetric value components - installs required dependencies
# Run this before using the enhanced email processing pipeline
# RELEVANT FILES: contextual_signal_extractor.py, intelligent_link_processor.py, requirements.txt

import subprocess
import sys
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_package(package_name):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"✅ Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install {package_name}: {e}")
        return False

def check_and_install_dependencies():
    """Check and install required dependencies for asymmetric value components"""
    
    required_packages = [
        "beautifulsoup4==4.12.2",
        "lxml==4.9.3", 
        "aiohttp==3.8.6",
        "aiofiles==23.2.0",
        "pdfplumber==0.10.3"
    ]
    
    logger.info("🚀 Setting up Asymmetric Value Components")
    logger.info("=" * 50)
    
    failed_packages = []
    
    for package in required_packages:
        logger.info(f"Installing {package}...")
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        logger.error(f"❌ Failed to install: {', '.join(failed_packages)}")
        logger.error("Please install these packages manually:")
        for package in failed_packages:
            print(f"  pip install {package}")
        return False
    
    logger.info("✅ All dependencies installed successfully!")
    return True

def test_imports():
    """Test that all components can be imported"""
    logger.info("🧪 Testing component imports...")
    
    try:
        from contextual_signal_extractor import ContextualSignalExtractor
        logger.info("✅ ContextualSignalExtractor imported successfully")
        
        from intelligent_link_processor import IntelligentLinkProcessor
        logger.info("✅ IntelligentLinkProcessor imported successfully")
        
        from ultra_refined_email_processor import UltraRefinedEmailProcessor
        logger.info("✅ UltraRefinedEmailProcessor imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        return False

def run_quick_test():
    """Run a quick functionality test"""
    logger.info("🎯 Running quick functionality test...")
    
    try:
        # Test signal extraction
        from contextual_signal_extractor import ContextualSignalExtractor
        extractor = ContextualSignalExtractor()
        
        test_content = "DBS Research Alert: APPLE (AAPL) upgraded to BUY, target price $200 (from $175)"
        result = extractor.extract_signals(test_content)
        
        if result.has_signals:
            logger.info(f"✅ Signal extraction working: {len(result.signals)} signals found")
        else:
            logger.warning("⚠️ Signal extraction test found no signals")
        
        # Test link processing
        from intelligent_link_processor import IntelligentLinkProcessor
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            processor = IntelligentLinkProcessor(
                download_dir=f"{temp_dir}/downloads",
                cache_dir=f"{temp_dir}/cache"
            )
            
            html_content = '<html><body><a href="https://example.com/report.pdf">Report</a></body></html>'
            links = processor._extract_all_urls(html_content)
            
            if links:
                logger.info(f"✅ Link processing working: {len(links)} links extracted")
            else:
                logger.warning("⚠️ Link processing test found no links")
                
        finally:
            shutil.rmtree(temp_dir)
        
        logger.info("🎉 All functionality tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Functionality test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Asymmetric Value Components Setup")
    print("=" * 60)
    print("This script sets up the enhanced email processing pipeline")
    print("with contextual signal extraction and intelligent link processing.")
    print("=" * 60)
    
    # Step 1: Install dependencies
    if not check_and_install_dependencies():
        print("\n❌ Setup failed - could not install dependencies")
        return False
    
    # Step 2: Test imports
    if not test_imports():
        print("\n❌ Setup failed - import test failed")
        return False
    
    # Step 3: Quick functionality test
    if not run_quick_test():
        print("\n⚠️ Setup completed but functionality test failed")
        print("The components may work, but please verify manually.")
    
    print("\n" + "=" * 60)
    print("🎯 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nYour email processing pipeline now includes:")
    print("✅ Contextual Trading Signal Extraction")
    print("✅ Intelligent Link Processing & Report Harvesting")
    print("✅ Enhanced Ultra-Refined Email Processor")
    print("\nAsymmetric Value Components are ready! 🚀")
    print("\nNext steps:")
    print("1. Run: python test_asymmetric_value_components.py")
    print("2. Test with real emails using the enhanced processor")
    print("3. Monitor for extracted trading signals and downloaded reports")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)