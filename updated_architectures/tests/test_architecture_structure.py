# test_architecture_structure.py
"""
Test ICE Simplified Architecture Structure (without API keys)
Validates that the simplified architecture components are correctly structured
Tests imports, class definitions, and basic functionality without requiring API keys
Relevant files: ice_simplified.py, ice_core.py, data_ingestion.py, query_engine.py, config.py
"""

import os
import sys
import inspect
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path.cwd()))

def test_imports():
    """Test that all modules can be imported correctly"""
    print("📦 Testing Module Imports...")

    results = {}

    # Test individual modules
    modules_to_test = [
        ('ice_simplified', 'ICESimplified'),
        ('ice_core', 'ICECore'),
        ('data_ingestion', 'DataIngester'),
        ('query_engine', 'QueryEngine'),
        ('config', 'ICEConfig')
    ]

    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name)
            main_class = getattr(module, class_name)

            # Check class structure
            methods = [method for method in dir(main_class) if not method.startswith('_')]

            results[module_name] = {
                'status': 'success',
                'class': class_name,
                'methods': len(methods),
                'module_size': len(inspect.getsource(module))
            }

            print(f"   ✅ {module_name}: {class_name} with {len(methods)} public methods")

        except Exception as e:
            results[module_name] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ {module_name}: Import failed - {e}")

    return results

def test_code_metrics():
    """Test code size and complexity metrics"""
    print("\n📏 Testing Code Metrics...")

    files_to_measure = [
        'ice_simplified.py',
        'ice_core.py',
        'data_ingestion.py',
        'query_engine.py',
        'config.py'
    ]

    total_lines = 0
    total_size = 0

    for filename in files_to_measure:
        filepath = Path(filename)
        if filepath.exists():
            content = filepath.read_text()
            lines = len(content.splitlines())
            size = len(content)

            total_lines += lines
            total_size += size

            print(f"   📄 {filename}: {lines} lines ({size:,} chars)")
        else:
            print(f"   ❌ {filename}: File not found")

    print(f"\n📊 Total Metrics:")
    print(f"   📝 Total Lines: {total_lines}")
    print(f"   💾 Total Size: {total_size:,} characters")
    print(f"   🎯 Target: <3000 lines (achieved: {total_lines < 3000})")

    return {
        'total_lines': total_lines,
        'total_size': total_size,
        'target_achieved': total_lines < 3000,  # Realistic target for 5 files
        'complexity_reduction': ((15000 - total_lines) / 15000) * 100
    }

def test_architecture_principles():
    """Test that architecture follows simplified principles"""
    print("\n🏗️ Testing Architecture Principles...")

    principles_met = []

    # Principle 1: Direct LightRAG integration
    try:
        from ice_core import ICECore
        # Check that ICECore imports JupyterSyncWrapper
        import inspect
        source = inspect.getsource(ICECore)
        if 'JupyterSyncWrapper' in source:
            principles_met.append("Direct LightRAG integration via JupyterSyncWrapper")
            print("   ✅ Direct LightRAG integration")
        else:
            print("   ❌ Missing direct LightRAG integration")
    except Exception as e:
        print(f"   ❌ Could not verify LightRAG integration: {e}")

    # Principle 2: Simple data ingestion
    try:
        from data_ingestion import DataIngester
        # Check for simple API calls without transformation
        source = inspect.getsource(DataIngester)
        if 'requests.get' in source and 'transformation' not in source.lower():
            principles_met.append("Simple API calls without transformation layers")
            print("   ✅ Simple data ingestion without transformation layers")
        else:
            print("   ❌ Data ingestion may be too complex")
    except Exception as e:
        print(f"   ❌ Could not verify data ingestion simplicity: {e}")

    # Principle 3: Thin query wrapper
    try:
        from query_engine import QueryEngine
        # Check for direct passthrough to ICE core
        source = inspect.getsource(QueryEngine)
        if 'self.ice.query' in source:
            principles_met.append("Thin query wrapper with direct passthrough")
            print("   ✅ Thin query wrapper with direct passthrough")
        else:
            print("   ❌ Query engine may not be thin enough")
    except Exception as e:
        print(f"   ❌ Could not verify query engine simplicity: {e}")

    # Principle 4: No complex orchestration
    try:
        from ice_simplified import ICESimplified
        source = inspect.getsource(ICESimplified)
        complex_keywords = ['orchestrator', 'pipeline', 'transformation', 'validation']
        has_complex_orchestration = any(keyword in source.lower() for keyword in complex_keywords)

        if not has_complex_orchestration:
            principles_met.append("No complex orchestration layers")
            print("   ✅ No complex orchestration layers")
        else:
            print("   ❌ May contain complex orchestration")
    except Exception as e:
        print(f"   ❌ Could not verify orchestration simplicity: {e}")

    # Principle 5: Minimal configuration
    try:
        from config import ICEConfig
        source = inspect.getsource(ICEConfig)
        if 'os.getenv' in source and 'complex' not in source.lower():
            principles_met.append("Environment-based configuration with defaults")
            print("   ✅ Simple environment-based configuration")
        else:
            print("   ❌ Configuration may be too complex")
    except Exception as e:
        print(f"   ❌ Could not verify configuration simplicity: {e}")

    return principles_met

def test_existing_integration():
    """Test integration with existing working components"""
    print("\n🔗 Testing Existing Component Integration...")

    integration_tests = []

    # Test 1: JupyterSyncWrapper import
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parents[2]  # Go up 2 levels from updated_architectures/tests/
        sys.path.insert(0, str(project_root))
        from src.ice_lightrag.ice_rag_fixed import JupyterSyncWrapper
        integration_tests.append("JupyterSyncWrapper import successful")
        print("   ✅ Can import existing JupyterSyncWrapper")
    except Exception as e:
        print(f"   ❌ Cannot import JupyterSyncWrapper: {e}")

    # Test 2: ICECore uses JupyterSyncWrapper
    try:
        from ice_core import ICECore
        import inspect
        source = inspect.getsource(ICECore.__init__)
        if 'JupyterSyncWrapper' in source:
            integration_tests.append("ICECore integrates with JupyterSyncWrapper")
            print("   ✅ ICECore properly integrates with JupyterSyncWrapper")
        else:
            print("   ❌ ICECore does not integrate with JupyterSyncWrapper")
    except Exception as e:
        print(f"   ❌ Could not verify ICECore integration: {e}")

    # Test 3: No circular dependencies
    try:
        # Simple check - if we can import all modules without errors, no circular deps
        from ice_simplified import ICESimplified
        from ice_core import ICECore
        from data_ingestion import DataIngester
        from query_engine import QueryEngine
        from config import ICEConfig

        integration_tests.append("No circular dependencies detected")
        print("   ✅ No circular dependencies detected")
    except Exception as e:
        print(f"   ❌ Possible circular dependency: {e}")

    return integration_tests

def generate_structure_report(import_results, metrics_results, principles_met, integration_tests):
    """Generate comprehensive structure test report"""
    print("\n" + "=" * 70)
    print("📋 ICE SIMPLIFIED ARCHITECTURE STRUCTURE REPORT")
    print("=" * 70)

    # Import success rate
    successful_imports = sum(1 for r in import_results.values() if r['status'] == 'success')
    total_imports = len(import_results)

    print(f"\n📦 Module Import Results:")
    print(f"   Successful: {successful_imports}/{total_imports} modules")
    print(f"   Success Rate: {successful_imports/total_imports*100:.1f}%")

    # Code metrics
    print(f"\n📏 Code Complexity Metrics:")
    print(f"   Total Lines: {metrics_results['total_lines']}")
    print(f"   Total Size: {metrics_results['total_size']:,} characters")
    print(f"   Complexity Reduction: {metrics_results['complexity_reduction']:.1f}% vs original")
    print(f"   Target Achievement: {'✅' if metrics_results['target_achieved'] else '❌'}")

    # Architecture principles
    print(f"\n🏗️ Architecture Principles:")
    print(f"   Principles Met: {len(principles_met)}/5")
    for principle in principles_met:
        print(f"   ✅ {principle}")

    # Integration tests
    print(f"\n🔗 Integration Tests:")
    print(f"   Tests Passed: {len(integration_tests)}/3")
    for test in integration_tests:
        print(f"   ✅ {test}")

    # Overall assessment
    structure_score = (
        (successful_imports / total_imports) * 0.3 +
        (1 if metrics_results['target_achieved'] else 0) * 0.2 +
        (len(principles_met) / 5) * 0.3 +
        (len(integration_tests) / 3) * 0.2
    ) * 100

    print(f"\n🎯 Overall Structure Assessment:")
    print(f"   Structure Score: {structure_score:.1f}/100")

    if structure_score >= 90:
        print(f"   🏆 EXCELLENT: Architecture is well-structured and simplified")
    elif structure_score >= 75:
        print(f"   ✅ GOOD: Architecture meets most simplification goals")
    elif structure_score >= 60:
        print(f"   ⚠️ ACCEPTABLE: Architecture needs some refinement")
    else:
        print(f"   ❌ NEEDS WORK: Architecture requires significant improvements")

    # Key achievements
    print(f"\n🎉 Key Achievements:")
    if metrics_results['complexity_reduction'] > 90:
        print(f"   🎯 Massive complexity reduction: {metrics_results['complexity_reduction']:.1f}%")
    if successful_imports == total_imports:
        print(f"   📦 All modules import correctly")
    if len(principles_met) >= 4:
        print(f"   🏗️ Architecture principles well-implemented")
    if len(integration_tests) >= 2:
        print(f"   🔗 Good integration with existing components")

def main():
    """Main structure test execution"""
    print("🏗️ ICE SIMPLIFIED ARCHITECTURE STRUCTURE TEST")
    print("=" * 70)
    print("Testing structure, imports, and complexity without requiring API keys")

    # Test imports
    import_results = test_imports()

    # Test code metrics
    metrics_results = test_code_metrics()

    # Test architecture principles
    principles_met = test_architecture_principles()

    # Test existing integration
    integration_tests = test_existing_integration()

    # Generate report
    generate_structure_report(import_results, metrics_results, principles_met, integration_tests)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Structure test execution failed: {e}")
        print(f"Check file paths and module structure")