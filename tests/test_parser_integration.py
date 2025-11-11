# Location: tests/test_parser_integration.py
# Purpose: Validate context parser integration into LightRAG query workflow
# Why: Ensure parsed_context is correctly returned from queries
# Relevant Files: src/ice_lightrag/ice_rag_fixed.py, context_parser.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_query_returns_parsed_context():
    """Test that LightRAG query now returns parsed_context field"""
    print("\n" + "="*80)
    print("TEST: Context Parser Integration")
    print("="*80)

    try:
        from src.ice_lightrag.ice_rag_fixed import JupyterSyncWrapper

        # Initialize LightRAG wrapper
        rag = JupyterSyncWrapper(working_dir="./ice_lightrag/storage")

        # Test query
        test_query = "What is Tencent operating margin in Q2 2025?"
        print(f"\nQuery: {test_query}")
        print("\nExecuting query with context parser...")

        result = rag.query(test_query, mode='hybrid')

        print(f"\nStatus: {result.get('status')}")

        if result.get('status') == 'success':
            # Check for parsed_context field (NEW in Phase 2)
            if 'parsed_context' in result:
                parsed_context = result['parsed_context']
                print("\n✅ parsed_context field present")

                if parsed_context:
                    summary = parsed_context.get('summary', {})
                    print(f"\n✅ Context parsing successful:")
                    print(f"   Entities: {summary.get('total_entities', 0)}")
                    print(f"   Relationships: {summary.get('total_relationships', 0)}")
                    print(f"   Chunks: {summary.get('total_chunks', 0)}")
                    print(f"   Sources by type: {summary.get('sources_by_type', {})}")

                    # Show top 3 chunks with attribution
                    chunks = parsed_context.get('chunks', [])
                    if chunks:
                        print(f"\n✅ Top 3 chunks with structured attribution:")
                        for i, chunk in enumerate(chunks[:3], 1):
                            print(f"\n   Chunk {i}:")
                            print(f"      Source type: {chunk.get('source_type', 'unknown')}")
                            print(f"      Confidence: {chunk.get('confidence', 'N/A')}")
                            print(f"      Date: {chunk.get('date', 'N/A')}")
                            print(f"      Relevance rank: {chunk.get('relevance_rank', 'N/A')}")

                            # Type-specific details
                            source_details = chunk.get('source_details', {})
                            if chunk['source_type'] == 'email':
                                subject = source_details.get('subject', 'N/A')
                                print(f"      Email subject: {subject[:50]}...")
                            elif chunk['source_type'] == 'api':
                                api_name = source_details.get('api', 'N/A')
                                symbol = source_details.get('symbol', 'N/A')
                                print(f"      API: {api_name}, Symbol: {symbol}")
                else:
                    print("\n⚠️  parsed_context is None (context may be empty)")
            else:
                print("\n❌ parsed_context field missing")
                print("   Integration may have failed")

            # Compare legacy sources vs structured chunks
            legacy_sources = result.get('sources', [])
            print(f"\n✅ Legacy sources field: {len(legacy_sources)} sources")
            print(f"   Sources: {[s.get('source', 'unknown') for s in legacy_sources]}")

            return result
        else:
            print(f"❌ Query failed: {result.get('message')}")
            return None

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CONTEXT PARSER INTEGRATION - VALIDATION TEST")
    print("="*80)
    print("\nValidating Phase 2 integration into LightRAG query workflow...")

    result = test_query_returns_parsed_context()

    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    if result and result.get('parsed_context'):
        print("\n✅ INTEGRATION SUCCESSFUL")
        print("   Context parser successfully integrated into query workflow")
        print("   Queries now return structured attribution data")
    elif result:
        print("\n⚠️  PARTIAL SUCCESS")
        print("   Query succeeded but parsed_context may be empty")
        print("   Check if graph is built and contains data")
    else:
        print("\n❌ INTEGRATION FAILED")
        print("   Review error messages above")
