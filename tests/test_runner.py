# tests/test_runner.py
# Comprehensive test runner for all ICE RAG systems
# Orchestrates testing of LightRAG, LazyGraphRAG, and Unified RAG
# Provides detailed reporting, performance analysis, and system validation

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import argparse
import traceback

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import test suites
from tests.test_lightrag import run_lightrag_tests, TestICELightRAG
from tests.test_lazygraphrag import run_lazygraphrag_tests, TestICELazyGraphRAG
from tests.test_unified_rag import run_unified_rag_tests, TestICEUnifiedRAG
from tests.test_fixtures import TestDataFixtures, create_test_config


class ICETestRunner:
    """Comprehensive test runner for all ICE RAG systems"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or create_test_config()
        self.fixtures = TestDataFixtures()
        self.start_time = None
        self.results = {}
        self.summary = {}
        
        # Test suite mapping
        self.test_suites = {
            "lightrag": {
                "name": "ICE LightRAG",
                "runner": run_lightrag_tests,
                "class": TestICELightRAG,
                "description": "Traditional knowledge graph RAG with OpenAI integration"
            },
            "lazygraphrag": {
                "name": "ICE LazyGraphRAG", 
                "runner": run_lazygraphrag_tests,
                "class": TestICELazyGraphRAG,
                "description": "Dynamic lazy graph construction with multi-hop reasoning"
            },
            "unified": {
                "name": "ICE Unified RAG",
                "runner": run_unified_rag_tests,
                "class": TestICEUnifiedRAG,
                "description": "Unified interface supporting multiple RAG engines"
            }
        }
    
    def run_system_check(self) -> Dict[str, Any]:
        """Run comprehensive system availability check"""
        print("🔍 Running System Availability Check...")
        print("=" * 60)
        
        system_info = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "environment_variables": {
                "OPENAI_API_KEY": "***SET***" if os.getenv("OPENAI_API_KEY") else "NOT SET",
                "JUPYTER_EXECUTION_MODE": os.getenv("JUPYTER_EXECUTION_MODE", "NOT SET"),
                "ICE_DEBUG": os.getenv("ICE_DEBUG", "NOT SET")
            },
            "dependencies": {}
        }
        
        # Check critical dependencies
        critical_imports = [
            "pandas", "numpy", "networkx", "pathlib", "json", "datetime",
            "asyncio", "tempfile", "shutil", "typing"
        ]
        
        print("📦 Checking critical dependencies...")
        for module in critical_imports:
            try:
                __import__(module)
                system_info["dependencies"][module] = {"available": True}
                print(f"  ✅ {module}")
            except ImportError as e:
                system_info["dependencies"][module] = {"available": False, "error": str(e)}
                print(f"  ❌ {module}: {e}")
        
        # Check optional dependencies
        optional_imports = [
            ("openai", "OpenAI API client"),
            ("lightrag", "LightRAG system"),
            ("pytest", "Testing framework")
        ]
        
        print("\n📦 Checking optional dependencies...")
        for module, description in optional_imports:
            try:
                __import__(module)
                system_info["dependencies"][module] = {"available": True, "description": description}
                print(f"  ✅ {module}: {description}")
            except ImportError:
                system_info["dependencies"][module] = {"available": False, "description": description}
                print(f"  ⚠️ {module}: {description} (optional)")
        
        # Check file system access
        print("\n📁 Checking file system access...")
        test_paths = ["./tests", "./ice_lightrag", "./ice_lazyrag", "./unified_storage"]
        
        for path in test_paths:
            path_obj = Path(path)
            if path_obj.exists():
                readable = os.access(path, os.R_OK)
                writable = os.access(path, os.W_OK)
                print(f"  ✅ {path}: {'R' if readable else ''}{'W' if writable else ''}")
                system_info[f"path_{path.replace('./', '').replace('/', '_')}"] = {
                    "exists": True, "readable": readable, "writable": writable
                }
            else:
                print(f"  ⚠️ {path}: Not found")
                system_info[f"path_{path.replace('./', '').replace('/', '_')}"] = {"exists": False}
        
        return system_info
    
    def run_individual_suite(self, suite_name: str, verbose: bool = False) -> Dict[str, Any]:
        """Run individual test suite with error handling"""
        suite_info = self.test_suites.get(suite_name)
        if not suite_info:
            return {"status": "error", "message": f"Unknown test suite: {suite_name}"}
        
        print(f"\n🧪 Running {suite_info['name']} Test Suite...")
        print(f"📝 {suite_info['description']}")
        print("=" * 60)
        
        suite_start_time = time.time()
        
        try:
            # Run the test suite
            test_results = suite_info["runner"]()
            suite_end_time = time.time()
            
            # Calculate metrics
            total_tests = len(test_results)
            passed_tests = sum(1 for result in test_results.values() if result)
            failed_tests = total_tests - passed_tests
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            duration = suite_end_time - suite_start_time
            
            suite_summary = {
                "status": "completed",
                "suite_name": suite_name,
                "display_name": suite_info["name"],
                "description": suite_info["description"],
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "duration": duration,
                "test_results": test_results,
                "timestamp": datetime.now().isoformat()
            }
            
            # Print summary
            print(f"\n📊 {suite_info['name']} Results:")
            print(f"   Tests: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            print(f"   Duration: {duration:.2f} seconds")
            
            if verbose:
                print(f"   Detailed Results:")
                for test_name, result in test_results.items():
                    status = "✅ PASS" if result else "❌ FAIL"
                    print(f"     {status} - {test_name}")
            
            return suite_summary
            
        except Exception as e:
            suite_end_time = time.time()
            duration = suite_end_time - suite_start_time
            
            error_summary = {
                "status": "error",
                "suite_name": suite_name,
                "display_name": suite_info["name"],
                "error_message": str(e),
                "error_type": type(e).__name__,
                "duration": duration,
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\n❌ {suite_info['name']} failed with error:")
            print(f"   Error: {e}")
            print(f"   Duration: {duration:.2f} seconds")
            
            if verbose:
                print(f"   Traceback:")
                print(traceback.format_exc())
            
            return error_summary
    
    def run_all_suites(self, suites: Optional[List[str]] = None, verbose: bool = False) -> Dict[str, Any]:
        """Run all or selected test suites"""
        self.start_time = time.time()
        
        # Determine which suites to run
        suites_to_run = suites or list(self.test_suites.keys())
        
        print("🚀 ICE RAG Systems - Comprehensive Test Runner")
        print("=" * 60)
        print(f"Running {len(suites_to_run)} test suite(s): {', '.join(suites_to_run)}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run system check first
        system_info = self.run_system_check()
        
        # Run each test suite
        suite_results = {}
        for suite_name in suites_to_run:
            if suite_name in self.test_suites:
                suite_results[suite_name] = self.run_individual_suite(suite_name, verbose)
            else:
                print(f"⚠️ Unknown test suite: {suite_name}")
                suite_results[suite_name] = {
                    "status": "error",
                    "message": f"Unknown test suite: {suite_name}"
                }
        
        # Calculate overall metrics
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        overall_stats = self._calculate_overall_stats(suite_results)
        
        # Generate comprehensive results
        comprehensive_results = {
            "test_run_info": {
                "timestamp": datetime.now().isoformat(),
                "total_duration": total_duration,
                "suites_requested": suites_to_run,
                "suites_completed": len([r for r in suite_results.values() if r["status"] == "completed"]),
                "config": self.config
            },
            "system_info": system_info,
            "overall_stats": overall_stats,
            "suite_results": suite_results
        }
        
        # Print final summary
        self._print_final_summary(comprehensive_results, verbose)
        
        return comprehensive_results
    
    def _calculate_overall_stats(self, suite_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall statistics across all test suites"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        completed_suites = 0
        failed_suites = 0
        
        for suite_result in suite_results.values():
            if suite_result["status"] == "completed":
                completed_suites += 1
                total_tests += suite_result.get("total_tests", 0)
                total_passed += suite_result.get("passed_tests", 0)
                total_failed += suite_result.get("failed_tests", 0)
            else:
                failed_suites += 1
                total_errors += 1
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        suite_success_rate = (completed_suites / len(suite_results) * 100) if suite_results else 0
        
        return {
            "total_suites": len(suite_results),
            "completed_suites": completed_suites,
            "failed_suites": failed_suites,
            "suite_success_rate": suite_success_rate,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_errors": total_errors,
            "overall_success_rate": overall_success_rate
        }
    
    def _print_final_summary(self, results: Dict[str, Any], verbose: bool = False):
        """Print comprehensive final summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        overall = results["overall_stats"]
        test_info = results["test_run_info"]
        
        # Overall metrics
        print(f"⏱️ Total Duration: {test_info['total_duration']:.2f} seconds")
        print(f"🏗️ Test Suites: {overall['completed_suites']}/{overall['total_suites']} completed ({overall['suite_success_rate']:.1f}%)")
        print(f"🧪 Individual Tests: {overall['total_passed']}/{overall['total_tests']} passed ({overall['overall_success_rate']:.1f}%)")
        
        if overall['total_errors'] > 0:
            print(f"⚠️ Errors: {overall['total_errors']} suite-level errors")
        
        # Per-suite breakdown
        print(f"\n📋 Suite-by-Suite Results:")
        for suite_name, suite_result in results["suite_results"].items():
            if suite_result["status"] == "completed":
                display_name = suite_result["display_name"]
                passed = suite_result["passed_tests"]
                total = suite_result["total_tests"]
                rate = suite_result["success_rate"]
                duration = suite_result["duration"]
                
                status_icon = "✅" if rate >= 80 else "⚠️" if rate >= 60 else "❌"
                print(f"  {status_icon} {display_name}: {passed}/{total} tests ({rate:.1f}%) in {duration:.2f}s")
            else:
                display_name = suite_result.get("display_name", suite_name)
                error_msg = suite_result.get("error_message", "Unknown error")
                print(f"  ❌ {display_name}: FAILED - {error_msg}")
        
        # System health assessment
        print(f"\n🏥 System Health Assessment:")
        
        api_key_available = results["system_info"]["environment_variables"]["OPENAI_API_KEY"] == "***SET***"
        critical_deps = results["system_info"]["dependencies"]
        critical_available = sum(1 for dep, info in critical_deps.items() if info["available"])
        
        print(f"  🔑 API Key: {'✅ Available' if api_key_available else '❌ Missing (some features limited)'}")
        print(f"  📦 Dependencies: {critical_available}/{len(critical_deps)} available")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if overall["overall_success_rate"] >= 90:
            print("  🎉 Excellent! All systems are highly functional and ready for production use.")
        elif overall["overall_success_rate"] >= 75:
            print("  ✅ Good! Systems are functional with minor limitations. Consider addressing failed tests.")
        elif overall["overall_success_rate"] >= 50:
            print("  ⚠️ Moderate functionality. Several issues need attention before production use.")
        else:
            print("  ❌ Significant issues detected. Review system configuration and dependencies.")
        
        if not api_key_available:
            print("  🔑 Set OPENAI_API_KEY environment variable for full LightRAG functionality.")
        
        if overall["failed_suites"] > 0:
            print(f"  🔧 {overall['failed_suites']} test suite(s) failed to run - check dependencies and configuration.")
        
        # Performance insights
        fastest_suite = None
        slowest_suite = None
        
        for suite_name, suite_result in results["suite_results"].items():
            if suite_result["status"] == "completed":
                duration = suite_result["duration"]
                if fastest_suite is None or duration < fastest_suite[1]:
                    fastest_suite = (suite_result["display_name"], duration)
                if slowest_suite is None or duration > slowest_suite[1]:
                    slowest_suite = (suite_result["display_name"], duration)
        
        if fastest_suite and slowest_suite and len(results["suite_results"]) > 1:
            print(f"\n⚡ Performance Insights:")
            print(f"  🚀 Fastest: {fastest_suite[0]} ({fastest_suite[1]:.2f}s)")
            print(f"  🐌 Slowest: {slowest_suite[0]} ({slowest_suite[1]:.2f}s)")
    
    def save_results(self, results: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Save test results to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"ice_test_results_{timestamp}.json"
        
        output_path = Path("tests") / "results" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare results for serialization
        serializable_results = self._make_serializable(results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Results saved to: {output_path}")
        return str(output_path)
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)


def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(
        description="ICE RAG Systems Comprehensive Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py                    # Run all test suites
  python test_runner.py --suites lightrag  # Run only LightRAG tests
  python test_runner.py --verbose         # Show detailed output
  python test_runner.py --save results.json --verbose  # Save results and show details
        """
    )
    
    parser.add_argument(
        "--suites",
        nargs="+",
        choices=["lightrag", "lazygraphrag", "unified"],
        help="Test suites to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed test output"
    )
    
    parser.add_argument(
        "--save",
        metavar="FILENAME",
        help="Save results to JSON file"
    )
    
    parser.add_argument(
        "--config",
        metavar="CONFIG_FILE",
        help="Load test configuration from JSON file"
    )
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
            print(f"📝 Loaded configuration from {args.config}")
        except Exception as e:
            print(f"⚠️ Failed to load configuration: {e}")
            config = None
    
    # Create test runner
    runner = ICETestRunner(config=config)
    
    # Run tests
    results = runner.run_all_suites(
        suites=args.suites,
        verbose=args.verbose
    )
    
    # Save results if requested
    if args.save:
        runner.save_results(results, args.save)
    
    # Return appropriate exit code
    overall_stats = results["overall_stats"]
    if overall_stats["suite_success_rate"] >= 100 and overall_stats["overall_success_rate"] >= 80:
        exit_code = 0  # All good
    elif overall_stats["suite_success_rate"] >= 50:
        exit_code = 1  # Some issues
    else:
        exit_code = 2  # Major issues
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)