#!/usr/bin/env python3
# run_tests.py
# Simple entry point for running ICE RAG system tests
# Provides easy access to comprehensive test suite from project root
# Supports both individual and complete system testing

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Simple test runner entry point"""
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print("❌ Tests directory not found!")
        print(f"Expected: {tests_dir}")
        return 1
    
    # Change to project directory
    os.chdir(project_root)
    
    # Add current directory to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    print("🚀 ICE RAG Systems - Quick Test Runner")
    print("=" * 50)
    print(f"Project Root: {project_root}")
    print(f"Tests Directory: {tests_dir}")
    
    # Check for test runner
    test_runner = tests_dir / "test_runner.py"
    if not test_runner.exists():
        print("❌ Test runner not found!")
        print(f"Expected: {test_runner}")
        return 1
    
    try:
        # Import and run test runner
        sys.path.insert(0, str(tests_dir))
        from test_runner import ICETestRunner
        
        # Create and run test suite
        runner = ICETestRunner()
        results = runner.run_all_suites(verbose=True)
        
        # Return appropriate exit code based on results
        overall_stats = results["overall_stats"]
        if overall_stats["suite_success_rate"] >= 100 and overall_stats["overall_success_rate"] >= 80:
            return 0  # All good
        elif overall_stats["suite_success_rate"] >= 50:
            return 1  # Some issues
        else:
            return 2  # Major issues
            
    except ImportError as e:
        print(f"❌ Failed to import test runner: {e}")
        print("\n💡 Trying alternative Python execution...")
        
        # Fall back to subprocess execution
        try:
            cmd = [sys.executable, str(test_runner), "--verbose"]
            result = subprocess.run(cmd, cwd=project_root)
            return result.returncode
        except Exception as e2:
            print(f"❌ Subprocess execution failed: {e2}")
            return 1
    
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)