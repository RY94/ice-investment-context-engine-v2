# Location: tests/test_phase1_enhanced_source_markers.py
# Purpose: Validate Phase 1 - Enhanced SOURCE markers with timestamps
# Why: Ensure both email and API SOURCE markers include dates correctly
# Relevant Files: ice_simplified.py, context_parser.py, enhanced_doc_creator.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ice_lightrag.context_parser import LightRAGContextParser


def test_email_source_marker_with_date():
    """Test email SOURCE marker parsing (already had dates)"""
    print("\n" + "="*80)
    print("TEST 1: Email SOURCE Marker with Date")
    print("="*80)

    parser = LightRAGContextParser()

    # Sample context with email SOURCE marker (RFC 2822 date format)
    # LightRAG format: chunks must be in JSON array within -----Document Chunks(DC)----- section
    context = """
-----Document Chunks(DC)-----
```json
[
    {
        "chunk_id": 1,
        "content": "[SOURCE_EMAIL:Tencent Q2 2025 Earnings|sender:Jia Jun (AGT Partners)|date:Thu, 15 Aug 2025 10:30:45 +0800]\\n\\nTencent's Q2 2025 operating margin was 34%, representing strong growth...",
        "file_path": "/emails/tencent_earnings.eml"
    }
]
```
    """

    parsed = parser.parse_context(context)

    print("\n✅ Parsed email SOURCE marker:")
    chunks = parsed.get('chunks', [])

    assert len(chunks) > 0, "Should parse at least one chunk"

    chunk = chunks[0]
    print(f"   Source type: {chunk.get('source_type')}")
    print(f"   Date: {chunk.get('date')}")
    print(f"   Source details: {chunk.get('source_details')}")

    assert chunk['source_type'] == 'email', "Should recognize email source"
    assert chunk['date'] is not None, "Email SOURCE marker should have date"
    assert '2025-08-15' in chunk['date'], "Date should be ISO 8601 format"

    print("\n✅ Email SOURCE marker correctly includes date")
    return True


def test_api_source_marker_with_date():
    """Test enhanced API SOURCE marker parsing (NEW in Phase 1)"""
    print("\n" + "="*80)
    print("TEST 2: Enhanced API SOURCE Marker with Date")
    print("="*80)

    parser = LightRAGContextParser()

    # Sample context with enhanced API SOURCE marker (ISO 8601 retrieval timestamp)
    context = """
-----Document Chunks(DC)-----
```json
[
    {
        "chunk_id": 1,
        "content": "[SOURCE:FMP|SYMBOL:NVDA|DATE:2025-10-29T10:30:00.123456]\\n\\nCompany Profile: NVIDIA Corporation\\nMarket Cap: $2.5T\\nSector: Technology\\nIndustry: Semiconductors",
        "file_path": "/api/fmp/nvda_profile.json"
    }
]
```
    """

    parsed = parser.parse_context(context)

    print("\n✅ Parsed enhanced API SOURCE marker:")
    chunks = parsed.get('chunks', [])

    assert len(chunks) > 0, "Should parse at least one chunk"

    chunk = chunks[0]
    print(f"   Source type: {chunk.get('source_type')}")
    print(f"   Date: {chunk.get('date')}")
    print(f"   Source details: {chunk.get('source_details')}")

    assert chunk['source_type'] == 'api', "Should recognize API source"
    assert chunk['date'] is not None, "Enhanced API SOURCE marker should have date"
    assert '2025-10-29' in chunk['date'], "Date should be ISO 8601 format"
    assert chunk['source_details']['api'] == 'fmp', "Should extract API type"
    assert chunk['source_details']['symbol'] == 'NVDA', "Should extract symbol"

    print("\n✅ Enhanced API SOURCE marker correctly includes date")
    return True


def test_legacy_api_source_marker_backward_compatible():
    """Test legacy API SOURCE marker still works (backward compatibility)"""
    print("\n" + "="*80)
    print("TEST 3: Legacy API SOURCE Marker (Backward Compatibility)")
    print("="*80)

    parser = LightRAGContextParser()

    # Sample context with legacy API SOURCE marker (no DATE field)
    context = """
-----Document Chunks(DC)-----
```json
[
    {
        "chunk_id": 1,
        "content": "[SOURCE:NEWSAPI|SYMBOL:AAPL]\\n\\nNews Article: Apple announces new product line...",
        "file_path": "/api/newsapi/aapl_news.json"
    }
]
```
    """

    parsed = parser.parse_context(context)

    print("\n✅ Parsed legacy API SOURCE marker:")
    chunks = parsed.get('chunks', [])

    assert len(chunks) > 0, "Should parse at least one chunk"

    chunk = chunks[0]
    print(f"   Source type: {chunk.get('source_type')}")
    print(f"   Date: {chunk.get('date')}")
    print(f"   Source details: {chunk.get('source_details')}")

    assert chunk['source_type'] == 'api', "Should recognize API source"
    assert chunk['date'] is None, "Legacy API SOURCE marker should have date=None"
    assert chunk['source_details']['api'] == 'newsapi', "Should extract API type"
    assert chunk['source_details']['symbol'] == 'AAPL', "Should extract symbol"

    print("\n✅ Legacy API SOURCE marker still works (backward compatible)")
    return True


def test_multiple_source_types_with_dates():
    """Test parsing multiple chunks with different source types"""
    print("\n" + "="*80)
    print("TEST 4: Multiple Source Types with Dates")
    print("="*80)

    parser = LightRAGContextParser()

    # Sample context with mixed source types
    context = """
-----Document Chunks(DC)-----
```json
[
    {
        "chunk_id": 1,
        "content": "[SOURCE:FMP|SYMBOL:NVDA|DATE:2025-10-29T10:00:00]\\n\\nFinancial data for NVDA...",
        "file_path": "/api/fmp/nvda.json"
    },
    {
        "chunk_id": 2,
        "content": "[SOURCE_EMAIL:Market Update|sender:analyst@firm.com|date:Mon, 28 Oct 2025 15:30:00 +0000]\\n\\nMarket analysis email...",
        "file_path": "/emails/market_update.eml"
    },
    {
        "chunk_id": 3,
        "content": "[SOURCE:SEC_EDGAR|SYMBOL:TSLA|DATE:2025-10-28T09:15:00]\\n\\nSEC filing for TSLA...",
        "file_path": "/sec/tsla_10k.json"
    }
]
```
    """

    parsed = parser.parse_context(context)

    print("\n✅ Parsed multiple source types:")
    chunks = parsed.get('chunks', [])

    assert len(chunks) == 3, f"Should parse 3 chunks, got {len(chunks)}"

    # Chunk 1: Enhanced API (FMP)
    chunk1 = chunks[0]
    print(f"\n   Chunk 1:")
    print(f"      Type: {chunk1['source_type']}")
    print(f"      Date: {chunk1['date']}")
    assert chunk1['source_type'] == 'api'
    assert chunk1['date'] is not None
    assert '2025-10-29' in chunk1['date']

    # Chunk 2: Email
    chunk2 = chunks[1]
    print(f"\n   Chunk 2:")
    print(f"      Type: {chunk2['source_type']}")
    print(f"      Date: {chunk2['date']}")
    assert chunk2['source_type'] == 'email'
    assert chunk2['date'] is not None
    assert '2025-10-28' in chunk2['date']

    # Chunk 3: Enhanced API (SEC EDGAR)
    chunk3 = chunks[2]
    print(f"\n   Chunk 3:")
    print(f"      Type: {chunk3['source_type']}")
    print(f"      Date: {chunk3['date']}")
    assert chunk3['source_type'] == 'api'
    assert chunk3['date'] is not None
    assert '2025-10-28' in chunk3['date']

    print("\n✅ All source types correctly parsed with dates")
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("PHASE 1 - ENHANCED SOURCE MARKERS VALIDATION")
    print("="*80)
    print("\nValidating Phase 1: Enhanced SOURCE markers with timestamps...")

    # Run all tests
    test1_result = test_email_source_marker_with_date()
    test2_result = test_api_source_marker_with_date()
    test3_result = test_legacy_api_source_marker_backward_compatible()
    test4_result = test_multiple_source_types_with_dates()

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    tests_passed = sum([
        test1_result is not None,
        test2_result is not None,
        test3_result is not None,
        test4_result is not None
    ])

    print(f"\nTests Passed: {tests_passed}/4")

    if tests_passed == 4:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("   Phase 1: Enhanced SOURCE markers ready for data re-ingestion")
        print("\nChanges Summary:")
        print("   • Email SOURCE markers: Already had dates (RFC 2822 format)")
        print("   • API SOURCE markers: NOW include dates (ISO 8601 retrieval timestamp)")
        print("   • Context parser: Updated to parse DATE field from API markers")
        print("   • Backward compatibility: Legacy markers without DATE still work")
    else:
        print(f"\n⚠️  {4 - tests_passed} tests failed")
        print("   Review failures before proceeding")
