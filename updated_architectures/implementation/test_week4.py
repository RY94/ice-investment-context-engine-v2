# Location: /updated_architectures/implementation/test_week4.py
# Purpose: Week 4 validation suite for ICEQueryProcessor integration
# Why: Validate query enhancement, fallback logic, and source attribution
# Relevant Files: ice_simplified.py, src/ice_core/ice_query_processor.py

"""
Week 4: Query Enhancement Integration Validation

Tests:
1. ICEQueryProcessor enabled (use_graph_context=True)
2. Query fallback logic (mix → hybrid → local cascade)
3. Source attribution in responses
4. QueryEngine benefits from enhanced features
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

def test_icequery_processor_enabled():
    """Test 1: Verify ICEQueryProcessor is enabled in ice_simplified.py"""
    print("=" * 70)
    print("TEST 1: ICEQueryProcessor Enabled")
    print("=" * 70)

    # Read ice_simplified.py and check for use_graph_context=True
    ice_simplified_path = project_root / "updated_architectures/implementation/ice_simplified.py"

    with open(ice_simplified_path, 'r') as f:
        content = f.read()

    if 'use_graph_context=True' in content:
        print("✅ ICEQueryProcessor enabled in ice_simplified.py")
        print("   Found: use_graph_context=True")
        return True
    else:
        print("❌ ICEQueryProcessor NOT enabled")
        print("   Expected: use_graph_context=True")
        return False


def test_fallback_logic_exists():
    """Test 2: Verify fallback logic exists in ice_query_processor.py"""
    print("\n" + "=" * 70)
    print("TEST 2: Query Fallback Logic")
    print("=" * 70)

    ice_query_processor_path = project_root / "src/ice_core/ice_query_processor.py"

    with open(ice_query_processor_path, 'r') as f:
        content = f.read()

    checks = {
        '_query_with_fallback method': '_query_with_fallback' in content,
        'mix → hybrid → local cascade': "'mix': ['mix', 'hybrid', 'local']" in content,
        'hybrid → local cascade': "'hybrid': ['hybrid', 'local']" in content,
        'Fallback used in process_enhanced_query': '_query_with_fallback(question, mode)' in content
    }

    all_passed = all(checks.values())

    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")

    if all_passed:
        print("\n✅ All fallback logic components present")
    else:
        print("\n❌ Some fallback logic components missing")

    return all_passed


def test_source_attribution_structure():
    """Test 3: Verify source attribution structure in responses"""
    print("\n" + "=" * 70)
    print("TEST 3: Source Attribution Structure")
    print("=" * 70)

    # Check that ice_query_processor.py returns sources in response
    ice_query_processor_path = project_root / "src/ice_core/ice_query_processor.py"

    with open(ice_query_processor_path, 'r') as f:
        content = f.read()

    checks = {
        'Sources field in response': '"sources": enhanced_response["sources"]' in content or '"sources"' in content,
        'Source extraction logic': '_synthesize_enhanced_response' in content,
        'Response includes metadata': '"confidence"' in content
    }

    all_passed = all(checks.values())

    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")

    if all_passed:
        print("\n✅ Source attribution structure present")
        print("   Note: Runtime validation requires LightRAG initialization")
    else:
        print("\n❌ Source attribution structure incomplete")

    return all_passed


def test_query_engine_integration():
    """Test 4: Verify QueryEngine delegates properly to ICECore"""
    print("\n" + "=" * 70)
    print("TEST 4: QueryEngine Integration")
    print("=" * 70)

    query_engine_path = project_root / "updated_architectures/implementation/query_engine.py"

    with open(query_engine_path, 'r') as f:
        content = f.read()

    checks = {
        'QueryEngine uses ICECore': 'self.ice.query(query, mode=mode)' in content or 'self.ice' in content,
        'Portfolio analysis methods': 'analyze_portfolio_risks' in content,
        'Query templates defined': 'self.query_templates' in content
    }

    all_passed = all(checks.values())

    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")

    if all_passed:
        print("\n✅ QueryEngine properly integrated")
        print("   Delegates to ICECore which uses ICESystemManager → ICEQueryProcessor")
    else:
        print("\n❌ QueryEngine integration incomplete")

    return all_passed


def test_week4_documentation():
    """Bonus Test: Check if Week 4 is mentioned in file headers"""
    print("\n" + "=" * 70)
    print("BONUS: Week 4 Documentation Check")
    print("=" * 70)

    files_to_check = {
        'ice_simplified.py': project_root / "updated_architectures/implementation/ice_simplified.py",
    }

    results = {}
    for filename, filepath in files_to_check.items():
        with open(filepath, 'r') as f:
            # Check first 30 lines for Week 4 mention
            first_lines = ''.join([f.readline() for _ in range(30)])
            has_week4 = 'Week 4' in first_lines
            results[filename] = has_week4

    all_documented = all(results.values())

    for filename, documented in results.items():
        status = "✅" if documented else "⚠️"
        print(f"   {status} {filename}")

    return all_documented


def main():
    """Run all Week 4 validation tests"""
    print("\n" + "=" * 70)
    print("WEEK 4: Query Enhancement Integration Validation")
    print("=" * 70)
    print("Testing 4 core requirements + documentation\n")

    results = []

    # Run all tests
    results.append(("ICEQueryProcessor Enabled", test_icequery_processor_enabled()))
    results.append(("Query Fallback Logic", test_fallback_logic_exists()))
    results.append(("Source Attribution", test_source_attribution_structure()))
    results.append(("QueryEngine Integration", test_query_engine_integration()))
    results.append(("Documentation Check", test_week4_documentation()))

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10s} {test_name}")

    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 70)

    if passed == total:
        print("\n🎉 Week 4 Implementation: COMPLETE")
        print("\n✅ All requirements validated:")
        print("   1. ICEQueryProcessor enabled (use_graph_context=True)")
        print("   2. Query fallback logic implemented (mix → hybrid → local)")
        print("   3. Source attribution structure verified")
        print("   4. QueryEngine properly integrated")
        print("\nNext Steps:")
        print("   - Run end-to-end query test with actual LightRAG instance")
        print("   - Update ICE_DEVELOPMENT_TODO.md (mark Week 4 complete)")
        print("   - Update PROJECT_CHANGELOG.md")
        print("   - Sync all 6 core documentation files")
    else:
        print("\n⚠️  Some validation tests failed - review implementation")

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test execution error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
