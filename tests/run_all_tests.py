# tests/run_all_tests.py
"""
Comprehensive test runner for ICE integration
Runs all tests and provides summary of results
"""

import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_test_file(test_file: Path) -> tuple[bool, str]:
    """
    Run a test file and return success status and output
    
    Args:
        test_file: Path to test file
        
    Returns:
        Tuple of (success, output)
    """
    print(f"\n🧪 Running {test_file.name}...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return True, result.stdout
        else:
            print(f"❌ Test failed with exit code {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, "Test timed out after 60 seconds"
    except Exception as e:
        return False, f"Test execution failed: {e}"


def main():
    """Run all ICE integration tests"""
    print("🚀 ICE Integration Test Suite")
    print("=" * 60)
    
    test_dir = Path(__file__).parent
    
    # Define test files in order of execution
    test_files = [
        test_dir / "test_ice_imports.py",
        test_dir / "test_ice_components.py", 
        test_dir / "test_streamlit_integration.py"
    ]
    
    # Track results
    results = {}
    passed = 0
    failed = 0
    
    # Run each test file
    for test_file in test_files:
        if not test_file.exists():
            print(f"⚠️ Test file not found: {test_file}")
            continue
            
        success, output = run_test_file(test_file)
        results[test_file.name] = {"success": success, "output": output}
        
        if success:
            passed += 1
            print(f"✅ {test_file.name} PASSED")
        else:
            failed += 1
            print(f"❌ {test_file.name} FAILED")
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏆 TEST SUMMARY")
    print("=" * 60)
    
    total = passed + failed
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! ✨")
        print("\n✅ ICE integration is ready for commit")
        
        # Print deployment readiness checklist
        print("\n📋 DEPLOYMENT READINESS:")
        print("✅ All imports work without errors")
        print("✅ Components handle missing dependencies gracefully")
        print("✅ Streamlit app starts successfully")
        print("✅ Core functionality tested with mock data")
        print("✅ Error handling and fallbacks verified")
        
        print("\n📝 NEXT STEPS:")
        print("1. Commit the working integration")
        print("2. Test with real API keys (optional)")
        print("3. Add sample documents for demonstration")
        print("4. Push to repository when satisfied")
        
        return True
    else:
        print(f"\n❌ {failed} test(s) failed!")
        print("\n🔧 FAILED TESTS:")
        for test_name, result in results.items():
            if not result["success"]:
                print(f"- {test_name}: {result['output'][:100]}...")
        
        print("\n⚠️ Fix failing tests before committing")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)