# Location: tests/test_context_parser.py
# Purpose: Validate LightRAGContextParser with real context format
# Why: Ensure parser correctly extracts source attribution from context
# Relevant Files: src/ice_lightrag/context_parser.py, ice_rag_fixed.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ice_lightrag.context_parser import LightRAGContextParser


def test_parse_sample_context():
    """Test parser with sample LightRAG context (matches actual format)"""
    print("\n" + "="*80)
    print("TEST 1: Parse Sample Context")
    print("="*80)

    # Sample context (based on validation findings)
    sample_context = '''-----Entities(KG)-----

```json
[
  {
    "id": 1,
    "entity": "TENCENT",
    "type": "ORGANIZATION",
    "description": "Chinese technology company",
    "created_at": "2025-08-15 10:30:00",
    "file_path": "email_12345.txt"
  },
  {
    "id": 2,
    "entity": "Operating_Margin",
    "type": "METRIC",
    "description": "Financial metric",
    "created_at": "2025-08-15 10:30:00",
    "file_path": "email_12345.txt"
  }
]
```

-----Relationships(KG)-----

```json
[
  {
    "id": 1,
    "entity1": "TENCENT",
    "entity2": "Operating_Margin",
    "description": "HAS_METRIC",
    "created_at": "2025-08-15 10:30:00",
    "file_path": "email_12345.txt"
  }
]
```

-----Document Chunks(DC)-----

```json
[
  {
    "id": 1,
    "content": "[SOURCE_EMAIL:Tencent Q2 2025 Earnings|sender:\\"Jia Jun (AGT Partners)\\" <jiajun@agtpartners.com.sg>|date:Sun, 17 Aug 2025 10:59:59 +0800]\\n\\nQ2 2025 operating margin: 34%...",
    "file_path": "email_12345.txt"
  },
  {
    "id": 2,
    "content": "[SOURCE:FMP|SYMBOL:TENCENT]\\n\\nRevenue: $50B, Net Income: $15B",
    "file_path": "fmp_data.txt"
  },
  {
    "id": 3,
    "content": "[TICKER:TENCENT|confidence:0.95]\\n\\nAnalyst upgrade...",
    "file_path": "research_note.txt"
  }
]
```
'''

    parser = LightRAGContextParser()
    result = parser.parse_context(sample_context)

    # Validate entities
    entities = result['entities']
    print(f"\n✅ Entities parsed: {len(entities)}")
    assert len(entities) == 2, f"Expected 2 entities, got {len(entities)}"
    print(f"   Entities: {[e['entity'] for e in entities]}")

    # Validate relationships
    relationships = result['relationships']
    print(f"\n✅ Relationships parsed: {len(relationships)}")
    assert len(relationships) == 1, f"Expected 1 relationship, got {len(relationships)}"
    print(f"   Relationship: {relationships[0]['entity1']} --{relationships[0]['description']}--> {relationships[0]['entity2']}")

    # Validate chunks
    chunks = result['chunks']
    print(f"\n✅ Chunks parsed: {len(chunks)}")
    assert len(chunks) == 3, f"Expected 3 chunks, got {len(chunks)}"

    # Check chunk 1 (email source)
    chunk1 = chunks[0]
    print(f"\nChunk 1 (Email):")
    print(f"   Source type: {chunk1['source_type']}")
    print(f"   Confidence: {chunk1['confidence']}")
    print(f"   Date: {chunk1['date']}")
    print(f"   Relevance rank: {chunk1['relevance_rank']}")
    print(f"   Subject: {chunk1['source_details'].get('subject', 'N/A')}")
    assert chunk1['source_type'] == 'email', f"Expected email, got {chunk1['source_type']}"
    assert chunk1['confidence'] == 0.90, f"Expected 0.90, got {chunk1['confidence']}"
    assert chunk1['relevance_rank'] == 1, "Expected rank 1 for first chunk"

    # Check chunk 2 (API source)
    chunk2 = chunks[1]
    print(f"\nChunk 2 (API):")
    print(f"   Source type: {chunk2['source_type']}")
    print(f"   API: {chunk2['source_details'].get('api', 'N/A')}")
    print(f"   Symbol: {chunk2['source_details'].get('symbol', 'N/A')}")
    print(f"   Relevance rank: {chunk2['relevance_rank']}")
    assert chunk2['source_type'] == 'api', f"Expected api, got {chunk2['source_type']}"
    assert chunk2['source_details']['api'] == 'fmp', f"Expected fmp"
    assert chunk2['relevance_rank'] == 2, "Expected rank 2 for second chunk"

    # Check chunk 3 (entity source)
    chunk3 = chunks[2]
    print(f"\nChunk 3 (Entity):")
    print(f"   Source type: {chunk3['source_type']}")
    print(f"   Ticker: {chunk3['source_details'].get('ticker', 'N/A')}")
    print(f"   Confidence: {chunk3['confidence']}")
    print(f"   Relevance rank: {chunk3['relevance_rank']}")
    assert chunk3['source_type'] == 'entity_extraction', f"Expected entity_extraction"
    assert chunk3['confidence'] == 0.95, f"Expected 0.95"
    assert chunk3['relevance_rank'] == 3, "Expected rank 3 for third chunk"

    # Validate summary
    summary = result['summary']
    print(f"\n✅ Summary generated:")
    print(f"   Total entities: {summary['total_entities']}")
    print(f"   Total relationships: {summary['total_relationships']}")
    print(f"   Total chunks: {summary['total_chunks']}")
    print(f"   Sources by type: {summary['sources_by_type']}")

    assert summary['sources_by_type']['email'] == 1
    assert summary['sources_by_type']['api'] == 1
    assert summary['sources_by_type']['entity_extraction'] == 1

    return result


def test_filter_by_source_type():
    """Test filtering chunks by source type"""
    print("\n" + "="*80)
    print("TEST 2: Filter Chunks by Source Type")
    print("="*80)

    # Use result from previous test
    sample_context = '''-----Entities(KG)-----

```json
[{"id": 1, "entity": "TENCENT"}]
```

-----Relationships(KG)-----

```json
[{"id": 1, "entity1": "TENCENT", "entity2": "Revenue"}]
```

-----Document Chunks(DC)-----

```json
[
  {"id": 1, "content": "[SOURCE_EMAIL:Test|sender:test|date:2025-08-15]", "file_path": "email.txt"},
  {"id": 2, "content": "[SOURCE:FMP|SYMBOL:TEST]", "file_path": "fmp.txt"},
  {"id": 3, "content": "[SOURCE_EMAIL:Test2|sender:test2|date:2025-08-16]", "file_path": "email2.txt"}
]
```
'''

    parser = LightRAGContextParser()
    result = parser.parse_context(sample_context)

    # Filter email sources
    email_chunks = parser.get_chunks_by_source_type(result, 'email')
    print(f"\n✅ Email chunks: {len(email_chunks)}")
    assert len(email_chunks) == 2, f"Expected 2 email chunks, got {len(email_chunks)}"

    # Filter API sources
    api_chunks = parser.get_chunks_by_source_type(result, 'api')
    print(f"✅ API chunks: {len(api_chunks)}")
    assert len(api_chunks) == 1, f"Expected 1 API chunk, got {len(api_chunks)}"

    return result


def test_top_n_chunks():
    """Test getting top N chunks by relevance"""
    print("\n" + "="*80)
    print("TEST 3: Get Top N Chunks")
    print("="*80)

    sample_context = '''-----Entities(KG)-----

```json
[{"id": 1, "entity": "TENCENT"}]
```

-----Relationships(KG)-----

```json
[{"id": 1, "entity1": "TENCENT", "entity2": "Revenue"}]
```

-----Document Chunks(DC)-----

```json
[
  {"id": 1, "content": "First chunk", "file_path": "file1.txt"},
  {"id": 2, "content": "Second chunk", "file_path": "file2.txt"},
  {"id": 3, "content": "Third chunk", "file_path": "file3.txt"},
  {"id": 4, "content": "Fourth chunk", "file_path": "file4.txt"},
  {"id": 5, "content": "Fifth chunk", "file_path": "file5.txt"}
]
```
'''

    parser = LightRAGContextParser()
    result = parser.parse_context(sample_context)

    # Get top 3 chunks
    top_3 = parser.get_top_n_chunks(result, n=3)
    print(f"\n✅ Top 3 chunks retrieved")
    assert len(top_3) == 3, f"Expected 3 chunks, got {len(top_3)}"

    # Verify order (should be 1, 2, 3 by relevance_rank)
    for i, chunk in enumerate(top_3, start=1):
        print(f"   Rank {i}: chunk_id={chunk['chunk_id']}, relevance_rank={chunk['relevance_rank']}")
        assert chunk['relevance_rank'] == i, f"Expected rank {i}, got {chunk['relevance_rank']}"

    return result


def test_real_context_integration():
    """Test with real context from LightRAG"""
    print("\n" + "="*80)
    print("TEST 4: Real Context Integration (If Available)")
    print("="*80)

    try:
        from src.ice_lightrag.ice_rag_fixed import JupyterSyncWrapper

        # Initialize LightRAG wrapper
        rag = JupyterSyncWrapper(working_dir="./ice_lightrag/storage")

        # Test query
        test_query = "What is Tencent operating margin in Q2 2025?"
        print(f"\nQuery: {test_query}")

        result = rag.query(test_query, mode='hybrid')

        if result.get('status') == 'success' and result.get('context'):
            context = result['context']
            print(f"\n✅ Real context retrieved: {len(context)} characters")

            # Parse with our new parser
            parser = LightRAGContextParser()
            parsed = parser.parse_context(context)

            print(f"\n✅ Parsed real context:")
            print(f"   Entities: {parsed['summary']['total_entities']}")
            print(f"   Relationships: {parsed['summary']['total_relationships']}")
            print(f"   Chunks: {parsed['summary']['total_chunks']}")
            print(f"   Sources by type: {parsed['summary']['sources_by_type']}")

            # Show top 3 chunks
            top_3 = parser.get_top_n_chunks(parsed, n=3)
            print(f"\n✅ Top 3 chunks by relevance:")
            for i, chunk in enumerate(top_3, start=1):
                print(f"\n   Chunk {i}:")
                print(f"      Source: {chunk['source_type']}")
                print(f"      Confidence: {chunk['confidence']}")
                print(f"      Date: {chunk.get('date', 'N/A')}")
                print(f"      Relevance rank: {chunk['relevance_rank']}")
                if chunk['source_type'] == 'email':
                    print(f"      Subject: {chunk['source_details'].get('subject', 'N/A')[:50]}...")
                elif chunk['source_type'] == 'api':
                    print(f"      API: {chunk['source_details'].get('api', 'N/A')}")

            return parsed
        else:
            print("⚠️  Real context not available (graph may not be built yet)")
            return None

    except Exception as e:
        print(f"⚠️  Real context test skipped: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "="*80)
    print("LIGHTRAG CONTEXT PARSER - VALIDATION TESTS")
    print("="*80)
    print("\nValidating Phase 2: Context Parser implementation...")

    # Run all tests
    test1_result = test_parse_sample_context()
    test2_result = test_filter_by_source_type()
    test3_result = test_top_n_chunks()
    test4_result = test_real_context_integration()

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    tests_passed = sum([
        test1_result is not None,
        test2_result is not None,
        test3_result is not None,
        # test4 is optional (may not have real context)
    ])

    print(f"\nCore Tests Passed: {tests_passed}/3")

    if test4_result:
        print("Real Context Test: ✅ PASSED")
    else:
        print("Real Context Test: ⚠️  SKIPPED (optional)")

    if tests_passed == 3:
        print("\n✅ ALL CORE VALIDATIONS PASSED")
        print("   Phase 2: Context Parser ready for integration")
    else:
        print(f"\n⚠️  {3 - tests_passed} tests failed")
        print("   Review failures before proceeding")
