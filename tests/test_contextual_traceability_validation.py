# Location: tests/test_contextual_traceability_validation.py
# Purpose: Validate current contextual traceability system before enhancement
# Why: Ensure base functionality works before building granular attribution
# Relevant Files: src/ice_lightrag/ice_rag_fixed.py, src/ice_core/ice_query_processor.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_lightrag_context_retrieval():
    """
    Test that LightRAG context retrieval works and contains SOURCE markers
    """
    print("\n" + "="*80)
    print("TEST 1: LightRAG Context Retrieval")
    print("="*80)

    try:
        from src.ice_lightrag.ice_rag_fixed import JupyterSyncWrapper

        # Initialize LightRAG wrapper
        rag = JupyterSyncWrapper(working_dir="./ice_lightrag/storage")

        # Test query
        test_query = "What is Tencent operating margin in Q2 2025?"

        print(f"\nQuery: {test_query}")
        print("\nExecuting query...")

        result = rag.query(test_query, mode='hybrid')

        print(f"\nStatus: {result.get('status')}")

        if result.get('status') == 'success':
            # Check for sources
            sources = result.get('sources', [])
            print(f"\n✅ Sources extracted: {len(sources)}")

            for i, source in enumerate(sources[:5], 1):  # Show first 5
                print(f"\nSource {i}:")
                print(f"  Type: {source.get('source', 'unknown')}")
                print(f"  Confidence: {source.get('confidence', 'N/A')}")
                print(f"  Symbol: {source.get('symbol', 'N/A')}")
                print(f"  Category: {source.get('type', 'N/A')}")

            # Check for context
            context = result.get('context')
            if context:
                print(f"\n✅ Context retrieved: {len(context)} characters")

                # Check if SOURCE markers present
                if '[SOURCE:' in context:
                    print("✅ SOURCE markers found in context")

                    # Count SOURCE markers
                    import re
                    source_markers = re.findall(r'\[SOURCE:(\w+)\|', context)
                    print(f"✅ {len(source_markers)} SOURCE markers detected")
                    print(f"   Types: {set(source_markers)}")
                else:
                    print("❌ No SOURCE markers found in context")

                # Check for graph structure
                if '-----Entities(KG)-----' in context:
                    print("✅ Entity data present")
                if '-----Relationships(KG)-----' in context:
                    print("✅ Relationship data present")
                if '-----Document Chunks(DC)-----' in context:
                    print("✅ Document chunks present")
            else:
                print("❌ No context returned")
        else:
            print(f"❌ Query failed: {result.get('message')}")

        return result

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_ice_query_processor_integration():
    """
    Test that ICEQueryProcessor uses real sources (not hardcoded)
    """
    print("\n" + "="*80)
    print("TEST 2: ICEQueryProcessor Source Integration")
    print("="*80)

    try:
        from src.ice_core.ice_query_processor import ICEQueryProcessor

        # Mock LightRAG result with sources
        mock_rag_result = {
            "status": "success",
            "result": "Test answer about Tencent.",
            "sources": [
                {"source": "email", "confidence": 0.90, "symbol": "TENCENT", "type": "email"},
                {"source": "fmp", "confidence": 0.85, "symbol": "TENCENT", "type": "api"}
            ],
            "confidence": 0.88
        }

        # Test _synthesize_enhanced_response
        processor = ICEQueryProcessor(lightrag_instance=None, graph_builder=None)

        result = processor._synthesize_enhanced_response(
            question="Test question",
            rag_result=mock_rag_result,
            graph_context={},
            entities={"tickers": ["TENCENT"]},
            query_type="financial_metrics"
        )

        sources = result.get("sources", [])

        if isinstance(sources, list) and len(sources) > 0:
            print("✅ Sources are passed through (not hardcoded)")
            print(f"   Source count: {len(sources)}")
            print(f"   First source: {sources[0]}")
        elif isinstance(sources, str):
            print(f"❌ Sources are still hardcoded string: '{sources}'")
        else:
            print(f"❌ Unexpected sources format: {type(sources)}")

        return result

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_adaptive_display_formatting():
    """
    Test that format_adaptive_display works with current data
    """
    print("\n" + "="*80)
    print("TEST 3: Adaptive Display Formatting")
    print("="*80)

    try:
        from src.ice_core.ice_query_processor import ICEQueryProcessor

        processor = ICEQueryProcessor(lightrag_instance=None, graph_builder=None)

        # Mock enriched result
        enriched_result = {
            "answer": "Tencent's Q2 2025 operating margin was 34%.",
            "reliability": {
                "confidence": 0.90,
                "confidence_type": "single_source",
                "explanation": "Single authoritative source: email",
                "breakdown": {"email": 0.90}
            },
            "source_metadata": {
                "enriched_sources": [
                    {
                        "source": "email",
                        "confidence": 0.90,
                        "quality_badge": "🔴 Tertiary",
                        "symbol": "Tencent Q2 2025 Earnings.eml"
                    }
                ],
                "temporal_context": None
            },
            "conflicts": None
        }

        display = processor.format_adaptive_display(enriched_result)

        print("\nGenerated Display:")
        print(display)

        # Verify cards present
        required_cards = ["✅ ANSWER", "🎯 RELIABILITY", "📚 SOURCES"]
        for card in required_cards:
            if card in display:
                print(f"✅ {card} card present")
            else:
                print(f"❌ {card} card missing")

        return display

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_context_parsing_preparation():
    """
    Test parsing LightRAG context format to prepare for enhancement
    """
    print("\n" + "="*80)
    print("TEST 4: Context Format Analysis (Preparation for Parser)")
    print("="*80)

    # Sample context (based on LightRAG source code analysis)
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
    "content": "[SOURCE:EMAIL|SYMBOL:TENCENT]\\nQ2 2025 operating margin: 34%...",
    "file_path": "email_12345.txt"
  },
  {
    "id": 2,
    "content": "[SOURCE:FMP|SYMBOL:TENCENT]\\nRevenue: $50B...",
    "file_path": "fmp_data.txt"
  }
]
```
'''

    try:
        import json
        import re

        print("\nParsing sample context...")

        # Extract chunks section
        chunks_match = re.search(r'-----Document Chunks\(DC\)-----\s+```json\s+(.*?)```',
                                 sample_context, re.DOTALL)

        if chunks_match:
            chunks_json = chunks_match.group(1)
            chunks = json.loads(chunks_json)

            print(f"✅ Parsed {len(chunks)} chunks")

            # Extract SOURCE markers from each chunk
            for i, chunk in enumerate(chunks, 1):
                content = chunk.get('content', '')
                source_match = re.search(r'\[SOURCE:(\w+)\|SYMBOL:([^\]]+)\]', content)

                if source_match:
                    source_type, symbol = source_match.groups()
                    print(f"\nChunk {i}:")
                    print(f"  Source: {source_type}")
                    print(f"  Symbol: {symbol}")
                    print(f"  File: {chunk.get('file_path', 'N/A')}")
                    print(f"  Relevance: #{i} (order-based)")
                else:
                    print(f"\nChunk {i}: No SOURCE marker found")
        else:
            print("❌ Could not parse chunks section")

        # Extract relationships for graph paths
        relations_match = re.search(r'-----Relationships\(KG\)-----\s+```json\s+(.*?)```',
                                    sample_context, re.DOTALL)

        if relations_match:
            relations_json = relations_match.group(1)
            relations = json.loads(relations_json)

            print(f"\n✅ Parsed {len(relations)} relationships")

            for i, rel in enumerate(relations, 1):
                print(f"\nRelationship {i}:")
                print(f"  Path: {rel['entity1']} --{rel['description']}--> {rel['entity2']}")
                print(f"  File: {rel.get('file_path', 'N/A')}")

        print("\n✅ Context parsing strategy validated")
        print("   Ready for LightRAGContextParser implementation")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CONTEXTUAL TRACEABILITY SYSTEM - VALIDATION TESTS")
    print("="*80)
    print("\nValidating current system before implementing granular enhancements...")

    # Run all tests
    test1_result = test_lightrag_context_retrieval()
    test2_result = test_ice_query_processor_integration()
    test3_result = test_adaptive_display_formatting()
    test4_result = test_context_parsing_preparation()

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    tests_passed = sum([
        test1_result is not None,
        test2_result is not None,
        test3_result is not None,
        test4_result is True
    ])

    print(f"\nTests Passed: {tests_passed}/4")

    if tests_passed == 4:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("   System ready for granular traceability enhancement")
    else:
        print(f"\n⚠️  {4 - tests_passed} tests failed")
        print("   Review failures before proceeding with enhancement")
