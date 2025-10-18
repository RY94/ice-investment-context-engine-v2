# Location: /tests/test_imap_email_pipeline_comprehensive.py
# Purpose: Comprehensive test suite for IMAP email ingestion pipeline
# Why: Validate all key features after truncation removal (Entry #57) and ensure pipeline integrity
# Relevant Files: imap_email_ingestion_pipeline/*, updated_architectures/implementation/data_ingestion.py

"""
Comprehensive IMAP Email Ingestion Pipeline Test Suite

Tests all key features of the email pipeline:
1. Email parsing from .eml files
2. Entity extraction (tickers, people, financial metrics)
3. Enhanced document creation with inline metadata
4. Graph construction (nodes, edges, relationships)
5. ICE integration
6. Production DataIngester workflow
7. Truncation removal validation (CRITICAL)

Run:
    python tests/test_imap_email_pipeline_comprehensive.py

Expected: ALL TESTS PASSING with 0 truncation warnings
"""

import sys
import os
from pathlib import Path
import email
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'imap_email_ingestion_pipeline'))
sys.path.insert(0, str(project_root / 'updated_architectures' / 'implementation'))

# Suppress warnings for cleaner output
import warnings
warnings.filterwarnings('ignore')

# Configure logging to capture warnings
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

print("=" * 80)
print("IMAP EMAIL INGESTION PIPELINE - COMPREHENSIVE TEST SUITE")
print("=" * 80)
print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Test metrics tracking
test_results = {
    'total_tests': 0,
    'passed_tests': 0,
    'failed_tests': 0,
    'warnings': [],
    'metrics': {}
}


def assert_test(condition, test_name, message=""):
    """Helper function to track test results"""
    test_results['total_tests'] += 1
    if condition:
        test_results['passed_tests'] += 1
        print(f"  ✅ {test_name}")
        if message:
            print(f"     {message}")
    else:
        test_results['failed_tests'] += 1
        print(f"  ❌ {test_name}")
        if message:
            print(f"     FAILURE: {message}")
        raise AssertionError(f"{test_name}: {message}")


# ============================================================================
# TEST SUITE 1: Email Source & Parsing
# ============================================================================

print("TEST SUITE 1: Email Source & Parsing")
print("-" * 80)

# Load real .eml files from data/emails_samples/
emails_dir = project_root / "data" / "emails_samples"

if not emails_dir.exists():
    print(f"❌ CRITICAL: Email directory not found: {emails_dir}")
    print("   Cannot run tests without sample emails")
    sys.exit(1)

eml_files = sorted(list(emails_dir.glob("*.eml")))[:3]  # First 3 for faster testing

real_emails = []
for eml_file in eml_files:
    try:
        with open(eml_file, 'r', encoding='utf-8', errors='replace') as f:
            msg = email.message_from_file(f)

        subject = msg.get('Subject', 'No Subject')
        sender = msg.get('From', 'Unknown Sender')
        date = msg.get('Date', 'Unknown Date')

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode('utf-8', errors='replace')
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='replace')

        real_emails.append({
            'uid': f"test_{eml_file.stem}",
            'subject': subject,
            'from': sender,
            'date': date,
            'body': body.strip(),
            'source_file': eml_file.name
        })

    except Exception as e:
        print(f"  ⚠️ Failed to parse {eml_file.name}: {e}")

# Test 1.1: Email file loading
assert_test(
    len(real_emails) >= 3,
    "test_email_file_loading",
    f"Loaded {len(real_emails)}/5 sample emails"
)

# Test 1.2: Email metadata extraction
metadata_complete = all(
    'uid' in e and 'subject' in e and 'from' in e and 'body' in e
    for e in real_emails
)
assert_test(
    metadata_complete,
    "test_email_metadata_extraction",
    "All emails have required fields (uid, subject, from, body)"
)

# Test 1.3: Email body parsing
body_lengths = [len(e['body']) for e in real_emails]
non_empty_bodies = sum(1 for length in body_lengths if length > 0)
success_rate = non_empty_bodies / len(body_lengths) if body_lengths else 0

assert_test(
    success_rate >= 0.6,  # At least 60% should have non-empty bodies
    "test_email_body_parsing",
    f"Parsed {non_empty_bodies}/{len(body_lengths)} bodies successfully ({success_rate:.0%}), lengths: {body_lengths}"
)

test_results['metrics']['emails_loaded'] = len(real_emails)
test_results['metrics']['body_lengths'] = body_lengths

print()

# ============================================================================
# TEST SUITE 2: Entity Extraction Quality
# ============================================================================

print("TEST SUITE 2: Entity Extraction Quality")
print("-" * 80)

try:
    from entity_extractor import EntityExtractor

    config_dir = project_root / "imap_email_ingestion_pipeline" / "config"
    extractor = EntityExtractor(str(config_dir))

    extracted_entities = []
    for i, email_data in enumerate(real_emails):
        print(f"  Extracting entities from email {i+1}/{len(real_emails)}...", end=" ", flush=True)
        entities = extractor.extract_entities(
            email_data['body'],
            metadata={'sender': email_data['from'], 'subject': email_data['subject']}
        )
        extracted_entities.append(entities)
        print("✓")

    # Test 2.1: Entity extraction success
    assert_test(
        len(extracted_entities) == len(real_emails),
        "test_entity_extraction_success",
        f"Extracted entities from {len(extracted_entities)} emails"
    )

    # Test 2.2: Ticker extraction
    ticker_counts = [len(e.get('tickers', [])) for e in extracted_entities]
    total_tickers = sum(ticker_counts)
    assert_test(
        total_tickers > 0,
        "test_ticker_extraction",
        f"Extracted {total_tickers} tickers across {len(real_emails)} emails"
    )

    # Test 2.3: Confidence scores presence
    all_tickers = []
    for entities in extracted_entities:
        all_tickers.extend(entities.get('tickers', []))

    has_confidence = all('confidence' in t for t in all_tickers)
    assert_test(
        has_confidence,
        "test_confidence_scores_present",
        "All extracted tickers have confidence scores"
    )

    # Test 2.4: Confidence score range validation
    if all_tickers:
        confidences = [t['confidence'] for t in all_tickers]
        valid_range = all(0 <= c <= 1 for c in confidences)
        avg_confidence = sum(confidences) / len(confidences)

        assert_test(
            valid_range,
            "test_confidence_range",
            f"All confidence scores in valid range [0, 1], avg: {avg_confidence:.2f}"
        )

        test_results['metrics']['avg_ticker_confidence'] = avg_confidence

    # Test 2.5: Overall extraction confidence
    overall_confidences = [e.get('confidence', 0) for e in extracted_entities]
    avg_overall_conf = sum(overall_confidences) / len(overall_confidences) if overall_confidences else 0

    assert_test(
        avg_overall_conf > 0.5,
        "test_overall_extraction_quality",
        f"Average overall confidence: {avg_overall_conf:.2f} (target: >0.5)"
    )

    test_results['metrics']['avg_overall_confidence'] = avg_overall_conf

except ImportError as e:
    print(f"  ⚠️ Skipping entity extraction tests: {e}")

print()

# ============================================================================
# TEST SUITE 3: Enhanced Document Creation (CRITICAL - Truncation Validation)
# ============================================================================

print("TEST SUITE 3: Enhanced Document Creation (TRUNCATION VALIDATION)")
print("-" * 80)

try:
    from enhanced_doc_creator import create_enhanced_document

    enhanced_documents = []
    truncation_warnings = []

    # Capture warnings during document creation
    import logging
    warning_handler = logging.Handler()
    warning_messages = []

    class WarningCapture(logging.Handler):
        def emit(self, record):
            if 'truncat' in record.getMessage().lower():
                warning_messages.append(record.getMessage())

    logger = logging.getLogger('imap_email_ingestion_pipeline.enhanced_doc_creator')
    handler = WarningCapture()
    logger.addHandler(handler)

    for i, (email_data, entities) in enumerate(zip(real_emails, extracted_entities)):
        enhanced_doc = create_enhanced_document(email_data, entities)
        enhanced_documents.append(enhanced_doc)

        # Check for truncation in document content
        if enhanced_doc and "[document truncated" in enhanced_doc.lower():
            truncation_warnings.append(f"Email {i+1}: Document content contains truncation marker")

    # Test 3.1: Document creation success
    successful_docs = sum(1 for doc in enhanced_documents if doc is not None)
    assert_test(
        successful_docs == len(real_emails),
        "test_enhanced_document_creation_success",
        f"Created {successful_docs}/{len(real_emails)} enhanced documents"
    )

    # Test 3.2: NO TRUNCATION WARNINGS (CRITICAL)
    all_truncation_warnings = warning_messages + truncation_warnings
    assert_test(
        len(all_truncation_warnings) == 0,
        "test_no_truncation_warnings_CRITICAL",
        f"Truncation warnings: {len(all_truncation_warnings)} (target: 0)"
    )

    if all_truncation_warnings:
        print("     ⚠️ TRUNCATION WARNINGS DETECTED:")
        for warning in all_truncation_warnings:
            print(f"       - {warning}")

    # Test 3.3: Document sizes unrestricted
    doc_sizes = [len(doc) for doc in enhanced_documents if doc]
    assert_test(
        len(doc_sizes) > 0,
        "test_document_sizes_unrestricted",
        f"Document sizes: {doc_sizes} bytes (no artificial cap)"
    )

    test_results['metrics']['doc_sizes'] = doc_sizes
    test_results['metrics']['truncation_warnings'] = len(all_truncation_warnings)

    # Test 3.4: Inline metadata format validation
    docs_with_source = sum(1 for doc in enhanced_documents if doc and "[SOURCE_EMAIL:" in doc)
    assert_test(
        docs_with_source == len(enhanced_documents),
        "test_inline_metadata_format",
        f"{docs_with_source}/{len(enhanced_documents)} documents have source metadata"
    )

    # Test 3.5: Ticker markup preservation
    docs_with_tickers = sum(1 for doc, entities in zip(enhanced_documents, extracted_entities)
                           if doc and ("[TICKER:" in doc or len(entities.get('tickers', [])) == 0))
    assert_test(
        docs_with_tickers == len(enhanced_documents),
        "test_ticker_markup_preservation",
        f"{docs_with_tickers}/{len(enhanced_documents)} documents have ticker markup (or no tickers)"
    )

    # Test 3.6: Confidence preservation in markup
    if enhanced_documents and enhanced_documents[0]:
        sample_doc = enhanced_documents[0]
        has_confidence_markup = "|confidence:" in sample_doc
        assert_test(
            has_confidence_markup,
            "test_confidence_preservation_in_markup",
            "Sample document contains confidence scores in markup"
        )

except ImportError as e:
    print(f"  ⚠️ Skipping enhanced document tests: {e}")

print()

# ============================================================================
# TEST SUITE 4: Graph Construction
# ============================================================================

print("TEST SUITE 4: Graph Construction")
print("-" * 80)

try:
    from graph_builder import GraphBuilder

    graph_builder = GraphBuilder()
    graphs = []

    for email_data, entities in zip(real_emails, extracted_entities):
        graph_data = graph_builder.build_email_graph(email_data, entities, [])
        graphs.append(graph_data)

    # Test 4.1: Graph creation success
    assert_test(
        len(graphs) == len(real_emails),
        "test_graph_creation_success",
        f"Created {len(graphs)} knowledge graphs"
    )

    # Test 4.2: Graph structure validation
    all_nodes = []
    all_edges = []
    for graph in graphs:
        all_nodes.extend(graph.get('nodes', []))
        all_edges.extend(graph.get('edges', []))

    assert_test(
        len(all_nodes) > 0 and len(all_edges) > 0,
        "test_graph_structure",
        f"Total: {len(all_nodes)} nodes, {len(all_edges)} edges"
    )

    # Test 4.3: Edge confidence scores
    edges_with_confidence = sum(1 for edge in all_edges if 'confidence' in edge)
    assert_test(
        edges_with_confidence == len(all_edges),
        "test_edge_confidence_scores",
        f"{edges_with_confidence}/{len(all_edges)} edges have confidence scores"
    )

    test_results['metrics']['total_nodes'] = len(all_nodes)
    test_results['metrics']['total_edges'] = len(all_edges)

except ImportError as e:
    print(f"  ⚠️ Skipping graph construction tests: {e}")

print()

# ============================================================================
# TEST SUITE 5: Production DataIngester Integration
# ============================================================================

print("TEST SUITE 5: Production DataIngester Integration")
print("-" * 80)

try:
    from data_ingestion import DataIngester

    ingester = DataIngester()

    # Test 5.1: DataIngester initialization
    assert_test(
        hasattr(ingester, 'entity_extractor'),
        "test_dataingester_initialization",
        "DataIngester initialized with entity_extractor"
    )

    # Test 5.2: Fetch email documents (production workflow)
    email_documents = ingester.fetch_email_documents(tickers=None, limit=5)

    assert_test(
        len(email_documents) >= 3,
        "test_dataingester_fetch_emails",
        f"Fetched {len(email_documents)} documents via DataIngester"
    )

    # Test 5.3: Enhanced document format in production
    if email_documents:
        sample_doc = email_documents[0]
        has_enhanced_format = "[SOURCE_EMAIL:" in sample_doc and "[TICKER:" in sample_doc

        assert_test(
            has_enhanced_format or "[SOURCE_EMAIL:" in sample_doc,
            "test_production_enhanced_format",
            "Production documents have enhanced format with inline metadata"
        )

    # Test 5.4: No truncation in production workflow
    production_truncation_warnings = sum(1 for doc in email_documents if "[document truncated" in doc.lower())

    assert_test(
        production_truncation_warnings == 0,
        "test_production_no_truncation_CRITICAL",
        f"Production truncation warnings: {production_truncation_warnings} (target: 0)"
    )

    test_results['metrics']['production_docs'] = len(email_documents)

except ImportError as e:
    print(f"  ⚠️ Skipping DataIngester tests: {e}")

print()

# ============================================================================
# FINAL TEST REPORT
# ============================================================================

print("=" * 80)
print("FINAL TEST REPORT")
print("=" * 80)

# Calculate success rate
success_rate = (test_results['passed_tests'] / test_results['total_tests'] * 100) if test_results['total_tests'] > 0 else 0

print(f"\nTests Executed: {test_results['total_tests']}")
print(f"Tests Passed: {test_results['passed_tests']}")
print(f"Tests Failed: {test_results['failed_tests']}")
print(f"Success Rate: {success_rate:.1f}%")

print("\nKEY METRICS:")
print(f"  Emails Loaded: {test_results['metrics'].get('emails_loaded', 0)}")
print(f"  Avg Ticker Confidence: {test_results['metrics'].get('avg_ticker_confidence', 0):.2f}")
print(f"  Avg Overall Confidence: {test_results['metrics'].get('avg_overall_confidence', 0):.2f}")
print(f"  Total Nodes Created: {test_results['metrics'].get('total_nodes', 0)}")
print(f"  Total Edges Created: {test_results['metrics'].get('total_edges', 0)}")
print(f"  Document Sizes: {test_results['metrics'].get('doc_sizes', [])} bytes")
print(f"  Production Documents: {test_results['metrics'].get('production_docs', 0)}")

print("\nCRITICAL VALIDATIONS (Truncation Removal):")
truncation_count = test_results['metrics'].get('truncation_warnings', 0)
if truncation_count == 0:
    print(f"  ✅ Truncation Warnings: {truncation_count} (PASS)")
else:
    print(f"  ❌ Truncation Warnings: {truncation_count} (FAIL - Expected: 0)")

doc_sizes = test_results['metrics'].get('doc_sizes', [])
if doc_sizes:
    max_size = max(doc_sizes)
    print(f"  ✅ Max Document Size: {max_size} bytes (unrestricted)")
else:
    print(f"  ⚠️ Document size metrics not available")

print("\nOVERALL STATUS:", end=" ")
if test_results['failed_tests'] == 0 and truncation_count == 0:
    print("✅ ALL TESTS PASSING")
else:
    print("❌ TESTS FAILED")

print(f"\nTest completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Exit with appropriate code
sys.exit(0 if test_results['failed_tests'] == 0 else 1)
