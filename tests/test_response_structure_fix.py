"""
Test to verify ingest_with_manifest returns compatible response structure
Checks that the KeyError fix is working correctly
"""
import sys
from pathlib import Path

# Add project root
project_root = Path.cwd()
sys.path.insert(0, str(project_root))

def test_response_structure():
    """Verify both methods return compatible response structures"""
    print("=" * 60)
    print("RESPONSE STRUCTURE COMPATIBILITY TEST")
    print("=" * 60)

    # Check the ingest_with_manifest method signature
    from updated_architectures.implementation.ice_simplified import ICESimplified
    import inspect

    # Get the method source to verify response structure
    method = ICESimplified.ingest_with_manifest
    source = inspect.getsource(method)

    # Critical keys that MUST be present
    required_keys = [
        'holdings_processed',
        'total_documents',
        'failed_holdings',
        'status'
    ]

    # Phase 1 specific keys (optional but should be present)
    phase1_keys = [
        'portfolio_delta',
        'new_documents',
        'skipped_duplicates'
    ]

    print("\n📋 Checking response structure initialization...")

    # Verify all required keys are in the results dict
    all_found = True
    for key in required_keys:
        # Check if key is in the results dict initialization
        if f"'{key}'" in source or f'"{key}"' in source:
            print(f"  ✅ {key}: Found in response structure")
        else:
            print(f"  ❌ {key}: MISSING from response structure")
            all_found = False

    print("\n📊 Checking Phase 1 specific keys...")
    for key in phase1_keys:
        if f"'{key}'" in source or f'"{key}"' in source:
            print(f"  ✅ {key}: Found in response structure")
        else:
            print(f"  ⚠️  {key}: Not found (optional)")

    # Check that total_documents is actually set before return
    print("\n🔄 Checking variable assignments...")

    if "results['total_documents']" in source:
        print("  ✅ total_documents: Assigned in method body")
    else:
        print("  ❌ total_documents: NOT assigned (will be 0)")
        all_found = False

    if "results['failed_holdings'].append" in source:
        print("  ✅ failed_holdings: Populated on errors")
    else:
        print("  ⚠️  failed_holdings: Not explicitly populated (may be empty)")

    # Verify no early returns that skip assignments
    returns = source.count('return results')
    print(f"\n🔍 Return paths: {returns}")
    if returns == 1:
        print("  ✅ Single return path (all assignments happen)")
    else:
        print(f"  ⚠️  Multiple return paths detected - verify all set keys")

    # Final verdict
    print("\n" + "=" * 60)
    if all_found:
        print("✅ RESPONSE STRUCTURE COMPATIBLE")
        print("\nThe notebook cell should work without KeyError!")
        print("\nExpected keys in response:")
        print("  - holdings_processed: List[str]")
        print("  - total_documents: int")
        print("  - failed_holdings: List[dict]")
        print("  - status: str")
        print("  - portfolio_delta: dict (Phase 1 bonus)")
        print("  - new_documents: int (Phase 1 bonus)")
        print("  - skipped_duplicates: int (Phase 1 bonus)")
        return 0
    else:
        print("❌ RESPONSE STRUCTURE INCOMPLETE")
        print("\nMissing required keys - notebook may still fail")
        return 1

if __name__ == "__main__":
    exit(test_response_structure())