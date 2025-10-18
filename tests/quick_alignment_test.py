# Quick alignment test for Phase 2.6.1 bug fix validation

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from updated_architectures.implementation.data_ingestion import DataIngester

print("\n" + "="*70)
print("Phase 2.6.1 Alignment Bug Fix Validation")
print("="*70 + "\n")

# Create ingester
ingester = DataIngester()

print("Test 1: Unfiltered alignment (limit=2)")
print("-" * 70)
docs = ingester.fetch_email_documents(limit=2)
ents = ingester.last_extracted_entities

print(f"Documents returned: {len(docs)}")
print(f"Entities stored: {len(ents)}")
assert len(docs) == len(ents), f"❌ FAIL: {len(docs)} docs != {len(ents)} entities"
print(f"✅ PASS: Alignment verified ({len(docs)} == {len(ents)})\n")

print("Test 2: Filtered alignment with tickers (limit=2)")
print("-" * 70)
docs_filt = ingester.fetch_email_documents(tickers=['NVDA', 'AAPL', 'TSLA'], limit=2)
ents_filt = ingester.last_extracted_entities

print(f"Documents returned (filtered): {len(docs_filt)}")
print(f"Entities stored (filtered): {len(ents_filt)}")
assert len(docs_filt) == len(ents_filt), f"❌ FAIL: {len(docs_filt)} docs != {len(ents_filt)} entities"
print(f"✅ PASS: Alignment verified ({len(docs_filt)} == {len(ents_filt)})\n")

print("Test 3: Entity dict structure validation")
print("-" * 70)
if len(ents) > 0:
    sample = ents[0]
    print(f"Sample entity type: {type(sample)}")
    print(f"Sample entity keys: {list(sample.keys()) if isinstance(sample, dict) else 'N/A'}")
    assert isinstance(sample, dict), "❌ FAIL: Entities must be dicts"
    print(f"✅ PASS: Entities are dict objects\n")

print("="*70)
print("✅ All Alignment Tests PASSED - Bug Fix Validated")
print("="*70 + "\n")
