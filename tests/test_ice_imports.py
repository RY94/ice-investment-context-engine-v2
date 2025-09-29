# tests/test_ice_imports.py
"""
Basic import tests for ICE integration components
Tests that all modules can be imported without external dependencies
"""

import sys
import os
import pytest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_ice_core_init_import():
    """Test that ice_core module can be imported"""
    try:
        import ice_core
        assert hasattr(ice_core, '__version__')
        print("✅ ice_core module imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import ice_core: {e}")


def test_ice_system_manager_import():
    """Test ICESystemManager can be imported without external dependencies"""
    try:
        from ice_core.ice_system_manager import ICESystemManager, get_ice_system_manager
        
        # Test basic class structure
        assert ICESystemManager is not None
        assert get_ice_system_manager is not None
        print("✅ ICESystemManager imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import ICESystemManager: {e}")


def test_ice_graph_builder_import():
    """Test ICEGraphBuilder can be imported"""
    try:
        from ice_core.ice_graph_builder import ICEGraphBuilder
        
        # Test basic class structure
        assert ICEGraphBuilder is not None
        assert hasattr(ICEGraphBuilder, 'EDGE_TYPE_MAPPING')
        print("✅ ICEGraphBuilder imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import ICEGraphBuilder: {e}")


def test_ice_query_processor_import():
    """Test ICEQueryProcessor can be imported"""
    try:
        from ice_core.ice_query_processor import ICEQueryProcessor
        
        # Test basic class structure
        assert ICEQueryProcessor is not None
        print("✅ ICEQueryProcessor imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import ICEQueryProcessor: {e}")


def test_ice_data_manager_import():
    """Test ICEDataManager can be imported"""
    try:
        from ice_core.ice_data_manager import ICEDataManager
        
        # Test basic class structure
        assert ICEDataManager is not None
        print("✅ ICEDataManager imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import ICEDataManager: {e}")


def test_ice_system_manager_initialization_without_dependencies():
    """Test ICESystemManager can be initialized even without LightRAG"""
    try:
        from ice_core.ice_system_manager import ICESystemManager
        
        # Should initialize without crashing, even if components unavailable
        system = ICESystemManager()
        
        # Should have proper attributes
        assert hasattr(system, 'working_dir')
        assert hasattr(system, 'initialization_status')
        assert hasattr(system, 'component_errors')
        
        # Get status (should not crash even if components unavailable)
        status = system.get_system_status()
        assert isinstance(status, dict)
        assert 'ready' in status
        assert 'components' in status
        
        print("✅ ICESystemManager initializes gracefully without dependencies")
        
    except Exception as e:
        pytest.fail(f"ICESystemManager initialization failed: {e}")


def test_graceful_lightrag_unavailable():
    """Test components handle missing LightRAG gracefully"""
    try:
        from ice_core.ice_system_manager import ICESystemManager
        
        system = ICESystemManager()
        
        # LightRAG property should return None gracefully if unavailable
        lightrag = system.lightrag
        
        # Should handle unavailability without crashing
        ready = system.is_ready()
        assert isinstance(ready, bool)
        
        print("✅ System handles missing LightRAG gracefully")
        
    except Exception as e:
        pytest.fail(f"Failed to handle missing LightRAG: {e}")


def test_ui_import_without_crash():
    """Test that the UI file can be imported without crashing"""
    try:
        # Import the UI module (but don't run streamlit)
        ui_path = project_root / "ui_mockups" / "ice_ui_v17.py"
        
        # Basic syntax check by compilation
        with open(ui_path, 'r') as f:
            ui_code = f.read()
        
        # Should compile without syntax errors
        compile(ui_code, str(ui_path), 'exec')
        
        print("✅ UI file compiles without syntax errors")
        
    except SyntaxError as e:
        pytest.fail(f"UI file has syntax error: {e}")
    except Exception as e:
        pytest.fail(f"UI file import test failed: {e}")


if __name__ == "__main__":
    # Run tests individually for debugging
    print("🧪 Running ICE Import Tests...")
    
    try:
        test_ice_core_init_import()
        test_ice_system_manager_import()
        test_ice_graph_builder_import()
        test_ice_query_processor_import()
        test_ice_data_manager_import()
        test_ice_system_manager_initialization_without_dependencies()
        test_graceful_lightrag_unavailable()
        test_ui_import_without_crash()
        
        print("\n🎉 All import tests passed!")
        
    except Exception as e:
        print(f"\n❌ Import test failed: {e}")
        sys.exit(1)