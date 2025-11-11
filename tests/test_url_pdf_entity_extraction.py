# Location: /tests/test_url_pdf_entity_extraction.py
# Purpose: Standalone test for EntityExtractor with URL PDF content
# Why: Diagnose if EntityExtractor works correctly outside full pipeline
# Relevant Files: imap_email_ingestion_pipeline/entity_extractor.py, updated_architectures/implementation/data_ingestion.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from imap_email_ingestion_pipeline.entity_extractor import EntityExtractor

def test_entity_extractor_initialization():
    """Test 1: Verify EntityExtractor can be initialized"""
    print("="*70)
    print("TEST 1: EntityExtractor Initialization")
    print("="*70)

    try:
        extractor = EntityExtractor()
        print("✅ EntityExtractor initialized successfully")

        # Check components
        print(f"\nComponents:")
        print(f"  NLP Model (spaCy): {'✅ Loaded' if extractor.nlp else '❌ Not loaded'}")
        print(f"  Known Tickers: {len(extractor.tickers)} loaded")
        print(f"  Companies: {len(extractor.companies)} loaded")

        if extractor.nlp:
            print(f"  spaCy Model: {extractor.nlp.meta['name']} v{extractor.nlp.meta['version']}")
        else:
            print(f"  ⚠️  spaCy model not loaded - install with:")
            print(f"     python -m spacy download en_core_web_sm")

        return extractor

    except Exception as e:
        print(f"❌ EntityExtractor initialization FAILED")
        print(f"   Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_simple_extraction(extractor):
    """Test 2: Simple entity extraction from sample text"""
    print("\n" + "="*70)
    print("TEST 2: Simple Entity Extraction")
    print("="*70)

    test_text = """
    Tencent Music Entertainment Group (TME) reported strong Q2 2024 results.
    Revenue reached $1.2 billion, up 15% year-over-year.
    Goldman Sachs upgraded TME to BUY with a price target of $15.
    The company's subscriber base grew to 90 million users.
    Operating margin improved to 18.5%, beating expectations.
    """

    print(f"\nTest Text ({len(test_text)} chars):")
    print("-" * 70)
    print(test_text.strip())
    print("-" * 70)

    try:
        entities = extractor.extract_entities(
            test_text,
            metadata={'source': 'test', 'test_type': 'simple'}
        )

        print(f"\n✅ Entity Extraction Successful")
        print(f"\nExtracted Entities:")
        print(f"  Tickers: {len(entities.get('tickers', []))} - {[t['ticker'] for t in entities.get('tickers', [])]}")
        print(f"  Companies: {len(entities.get('companies', []))} - {[c['name'] for c in entities.get('companies', [])[:3]]}")
        print(f"  Ratings: {len(entities.get('ratings', []))} - {[r['rating'] for r in entities.get('ratings', [])]}")
        print(f"  Financial Metrics: {len(entities.get('financial_metrics', []))}")
        print(f"  People: {len(entities.get('people', []))} - {[p['name'] for p in entities.get('people', [])[:3]]}")
        print(f"  Overall Confidence: {entities.get('confidence', 0.0):.2f}")

        # Show sample metrics
        if entities.get('financial_metrics'):
            print(f"\n  Sample Financial Metrics:")
            for i, metric in enumerate(entities['financial_metrics'][:3], 1):
                print(f"    {i}. {metric.get('metric')}: {metric.get('value')} {metric.get('unit', '')}")

        return True

    except Exception as e:
        print(f"❌ Entity Extraction FAILED")
        print(f"   Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_like_extraction(extractor):
    """Test 3: Entity extraction from PDF-like content (longer text, tables)"""
    print("\n" + "="*70)
    print("TEST 3: PDF-Like Content Extraction")
    print("="*70)

    # Simulate PDF content with tables and structured data
    pdf_content = """
    RESEARCH REPORT: Tencent Music Entertainment (TME)

    INVESTMENT RATING: BUY (Upgraded from HOLD)
    PRICE TARGET: $15.00 (from $12.00)
    ANALYST: John Smith, Goldman Sachs
    DATE: August 15, 2024

    EXECUTIVE SUMMARY
    We are upgrading Tencent Music Entertainment (TME) to BUY based on:
    1. Strong Q2 2024 revenue growth (+15% YoY to $1.2B)
    2. Expanding subscriber base (90M users, +12% YoY)
    3. Improving operating margins (18.5%, up from 16.2%)
    4. Positive regulatory environment in China

    FINANCIAL HIGHLIGHTS
    Revenue: $1,200 million (Q2 2024)
    Operating Income: $222 million
    Operating Margin: 18.5%
    Subscriber Base: 90 million
    ARPPU: $2.10 (Average Revenue Per Paying User)

    COMPETITIVE POSITION
    TME maintains market leadership in China's online music streaming market
    with approximately 35% market share. Key competitors include NetEase Cloud
    Music (20% share) and Kuwo Music (12% share).

    VALUATION
    Current Price: $11.50
    Price Target: $15.00
    Upside: 30%
    P/E Ratio: 22.5x (2024E)
    EV/EBITDA: 12.8x

    RISKS
    - Regulatory changes in China
    - Competition from international platforms
    - Content cost inflation
    """

    print(f"\nPDF-Like Content ({len(pdf_content)} chars):")
    print("-" * 70)
    print(pdf_content[:500] + "...")
    print("-" * 70)

    try:
        entities = extractor.extract_entities(
            pdf_content,
            metadata={'source': 'linked_report', 'test_type': 'pdf_like'}
        )

        print(f"\n✅ PDF-Like Entity Extraction Successful")
        print(f"\nExtracted Entities:")
        print(f"  Tickers: {len(entities.get('tickers', []))} - {[t['ticker'] for t in entities.get('tickers', [])]}")
        print(f"  Ratings: {len(entities.get('ratings', []))} - {[r['rating'] for r in entities.get('ratings', [])]}")

        # Check for price targets
        price_targets = [m for m in entities.get('financial_metrics', []) if m.get('metric') == 'price_target']
        price_target_values = [f"${pt['value']}" for pt in price_targets]
        print(f"  Price Targets: {len(price_targets)} - {price_target_values}")

        # Check for revenue/margin metrics
        revenue_metrics = [m for m in entities.get('financial_metrics', []) if 'revenue' in m.get('metric', '').lower()]
        margin_metrics = [m for m in entities.get('financial_metrics', []) if 'margin' in m.get('metric', '').lower()]

        print(f"  Revenue Metrics: {len(revenue_metrics)}")
        print(f"  Margin Metrics: {len(margin_metrics)}")
        print(f"  Total Financial Metrics: {len(entities.get('financial_metrics', []))}")
        print(f"  People/Analysts: {len(entities.get('people', []))}")
        print(f"  Overall Confidence: {entities.get('confidence', 0.0):.2f}")

        # Show all financial metrics
        if entities.get('financial_metrics'):
            print(f"\n  All Financial Metrics:")
            for i, metric in enumerate(entities['financial_metrics'][:10], 1):
                print(f"    {i}. {metric.get('metric')}: {metric.get('value')} {metric.get('unit', '')} (conf: {metric.get('confidence', 0.0):.2f})")

        return True

    except Exception as e:
        print(f"❌ PDF-Like Entity Extraction FAILED")
        print(f"   Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_actual_pdf_file(extractor):
    """Test 4: Extract entities from actual downloaded PDF (if available)"""
    print("\n" + "="*70)
    print("TEST 4: Actual Downloaded PDF Extraction")
    print("="*70)

    download_dir = Path("data/attachments")

    if not download_dir.exists():
        print("⚠️  No download directory found - skipping test")
        return None

    pdfs = list(download_dir.glob("*.pdf"))
    if not pdfs:
        print("⚠️  No PDFs found in download directory - skipping test")
        return None

    # Get latest PDF
    latest_pdf = max(pdfs, key=lambda p: p.stat().st_mtime)
    print(f"\nLatest PDF: {latest_pdf.name} ({latest_pdf.stat().st_size / 1024:.1f} KB)")

    # Extract text using basic PDF reader
    try:
        import pdfplumber

        with pdfplumber.open(latest_pdf) as pdf:
            text_content = ""
            for i, page in enumerate(pdf.pages[:10], 1):  # First 10 pages
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n\n"

        print(f"Extracted Text: {len(text_content)} characters from {len(pdf.pages[:10])} pages")

        if len(text_content) < 100:
            print("⚠️  Extracted text too short - PDF may be image-based or corrupted")
            return None

        # Run entity extraction
        entities = extractor.extract_entities(
            text_content,
            metadata={'source': 'actual_pdf', 'file': latest_pdf.name}
        )

        print(f"\n✅ PDF Entity Extraction Successful")
        print(f"\nExtracted Entities:")
        print(f"  Tickers: {len(entities.get('tickers', []))} - {[t['ticker'] for t in entities.get('tickers', [])]}")
        print(f"  Ratings: {len(entities.get('ratings', []))} - {[r['rating'] for r in entities.get('ratings', [])]}")
        print(f"  Financial Metrics: {len(entities.get('financial_metrics', []))}")
        print(f"  People: {len(entities.get('people', []))}")
        print(f"  Overall Confidence: {entities.get('confidence', 0.0):.2f}")

        return True

    except ImportError:
        print("⚠️  pdfplumber not installed - install with: pip install pdfplumber")
        return None
    except Exception as e:
        print(f"❌ PDF Extraction FAILED")
        print(f"   Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all EntityExtractor tests"""
    print("\n" + "🧪 "*35)
    print("URL PDF ENTITY EXTRACTION DIAGNOSTIC SUITE")
    print("🧪 "*35)

    results = {
        'initialization': False,
        'simple_extraction': False,
        'pdf_like_extraction': False,
        'actual_pdf': None
    }

    # Test 1: Initialization
    extractor = test_entity_extractor_initialization()
    results['initialization'] = (extractor is not None)

    if not extractor:
        print("\n" + "="*70)
        print("❌ CRITICAL FAILURE: Cannot proceed without EntityExtractor")
        print("="*70)
        return results

    # Test 2: Simple extraction
    results['simple_extraction'] = test_simple_extraction(extractor)

    # Test 3: PDF-like extraction
    results['pdf_like_extraction'] = test_pdf_like_extraction(extractor)

    # Test 4: Actual PDF (optional)
    results['actual_pdf'] = test_actual_pdf_file(extractor)

    # Summary
    print("\n" + "="*70)
    print("📋 TEST SUMMARY")
    print("="*70)

    print(f"\n✅ Passed Tests:")
    if results['initialization']:
        print("   1. EntityExtractor Initialization")
    if results['simple_extraction']:
        print("   2. Simple Entity Extraction")
    if results['pdf_like_extraction']:
        print("   3. PDF-Like Content Extraction")
    if results['actual_pdf']:
        print("   4. Actual PDF File Extraction")

    failed = [k for k, v in results.items() if v is False]
    if failed:
        print(f"\n❌ Failed Tests:")
        for i, test in enumerate(failed, 1):
            print(f"   {i}. {test.replace('_', ' ').title()}")

    skipped = [k for k, v in results.items() if v is None]
    if skipped:
        print(f"\n⚠️  Skipped Tests:")
        for i, test in enumerate(skipped, 1):
            print(f"   {i}. {test.replace('_', ' ').title()}")

    # Diagnosis
    print(f"\n💡 DIAGNOSIS:")
    if all(v is not False for v in results.values()):
        print("   ✅ EntityExtractor is WORKING correctly")
        print("   → Issue likely in pipeline integration, not EntityExtractor itself")
        print("   → Check data_ingestion.py logs for integration errors")
    elif not results['initialization']:
        print("   ❌ EntityExtractor cannot initialize")
        print("   → Check dependencies: pip install spacy")
        print("   → Download model: python -m spacy download en_core_web_sm")
    elif not results['simple_extraction'] or not results['pdf_like_extraction']:
        print("   ❌ EntityExtractor initialized but extraction failing")
        print("   → Check spaCy model compatibility")
        print("   → Check entity_extractor.py for bugs")

    print("="*70)

    return results

if __name__ == "__main__":
    main()
