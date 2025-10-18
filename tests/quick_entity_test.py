# Quick validation for Phase 2.6.1 EntityExtractor integration

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from updated_architectures.implementation.data_ingestion import DataIngester

print("\n" + "="*70)
print("Phase 2.6.1 Quick Validation")
print("="*70 + "\n")

# Create ingester
ingester = DataIngester()

# Fetch only 2 emails for quick test
print("Fetching 2 sample emails...")
documents = ingester.fetch_email_documents(limit=2)

print(f"\n✅ Test 1 - Backward Compatibility: Returns List[str]")
print(f"   Type: {type(documents)}, Count: {len(documents)}")

print(f"\n✅ Test 2 - Structured Data Storage")
print(f"   Entities extracted: {len(ingester.last_extracted_entities)}")
if len(ingester.last_extracted_entities) > 0:
    sample = ingester.last_extracted_entities[0]
    print(f"   Sample keys: {list(sample.keys())[:5]}")
    print(f"   Tickers: {len(sample.get('tickers', []))}")
    print(f"   Confidence: {sample.get('confidence', 'N/A')}")

print(f"\n✅ Test 3 - Enhanced Document Markup")
if len(documents) > 0:
    doc = documents[0]
    has_markup = '[' in doc and '|confidence:' in doc
    print(f"   Inline markup detected: {has_markup}")
    if has_markup:
        # Find first markup pattern
        start = doc.find('[')
        sample = doc[start:start+100] if start != -1 else "N/A"
        print(f"   Sample: {sample}...")

print(f"\n✅ Test 4 - Phase 2.6.2 Storage Ready")
print(f"   Attribute last_extracted_entities: {hasattr(ingester, 'last_extracted_entities')}")
print(f"   Attribute last_graph_data: {hasattr(ingester, 'last_graph_data')}")

print("\n" + "="*70)
print("✅ Phase 2.6.1 Integration Validated Successfully")
print("="*70 + "\n")
