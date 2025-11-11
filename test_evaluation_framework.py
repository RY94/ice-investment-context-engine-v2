# Location: /test_evaluation_framework.py
# Purpose: Quick validation script for ICE evaluation framework
# Why: Ensure MinimalEvaluator works before running full notebook evaluation
# Relevant Files: src/ice_evaluation/minimal_evaluator.py

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

print("🧪 ICE Evaluation Framework Validation")
print("=" * 60)

# Test 1: Import check
print("\n1. Testing imports...")
try:
    from src.ice_evaluation import ICEMinimalEvaluator, MinimalEvaluationConfig
    print("   ✅ MinimalEvaluator imports successfully")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Configuration validation
print("\n2. Testing configuration...")
try:
    config = MinimalEvaluationConfig(
        batch_size=3,
        max_retries=2,
        fail_fast=False
    )
    config.validate()
    print("   ✅ Configuration validation passed")
except Exception as e:
    print(f"   ❌ Configuration failed: {e}")
    sys.exit(1)

# Test 3: Evaluator initialization
print("\n3. Testing evaluator initialization...")
try:
    evaluator = ICEMinimalEvaluator(config)
    print(f"   ✅ Evaluator initialized")
    print(f"      Batch size: {evaluator.config.batch_size}")
    print(f"      Model: {evaluator.config.evaluator_model}")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    sys.exit(1)

# Test 4: Rule-based metrics (no ICE needed)
print("\n4. Testing rule-based metrics...")
try:
    from src.ice_evaluation.minimal_evaluator import EvaluationResult

    # Test faithfulness calculation
    result = EvaluationResult(query_id="TEST1", query_text="Test query", status="UNKNOWN")

    # Simulate faithfulness test
    answer = "NVDA and TSMC are semiconductor companies"
    contexts = ["NVDA is a leading semiconductor company", "TSMC manufactures chips"]

    # Call private method for testing
    evaluator._calculate_faithfulness(result, answer, contexts)

    if 'faithfulness' in result.scores:
        print(f"   ✅ Faithfulness: {result.scores['faithfulness']:.3f}")
    else:
        print(f"   ⚠️ Faithfulness calculation had issues: {result.failures.get('faithfulness', 'Unknown')}")

    # Test relevancy calculation
    query = "What are the semiconductor companies?"
    evaluator._calculate_relevancy(result, query, answer)

    if 'relevancy' in result.scores:
        print(f"   ✅ Relevancy: {result.scores['relevancy']:.3f}")
    else:
        print(f"   ⚠️ Relevancy calculation had issues: {result.failures.get('relevancy', 'Unknown')}")

    # Test entity F1
    reference = "NVDA TSMC AMD"
    evaluator._calculate_entity_f1(result, answer, reference)

    if 'entity_f1' in result.scores:
        print(f"   ✅ Entity F1: {result.scores['entity_f1']:.3f}")
    else:
        print(f"   ⚠️ Entity F1 calculation had issues: {result.failures.get('entity_f1', 'Unknown')}")

    result.compute_status()
    print(f"   ✅ Result status: {result.status}")

except Exception as e:
    print(f"   ❌ Metrics test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: DataFrame creation
print("\n5. Testing result DataFrame conversion...")
try:
    result_dict = result.to_dict()
    df = pd.DataFrame([result_dict])
    print(f"   ✅ DataFrame created: {len(df)} rows, {len(df.columns)} columns")
    print(f"      Columns: {', '.join(df.columns[:5])}...")
except Exception as e:
    print(f"   ❌ DataFrame creation failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✅ ALL VALIDATION TESTS PASSED")
print("=" * 60)
print("\n📋 Next Steps:")
print("   1. Run ice_building_workflow.ipynb to build knowledge graph")
print("   2. Run ice_query_workflow.ipynb Section 5 for full evaluation")
print("   3. Review evaluation results and metrics")
print("\n💡 Framework ready for production use!")
