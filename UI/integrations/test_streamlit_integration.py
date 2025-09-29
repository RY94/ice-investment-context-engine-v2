# tests/test_streamlit_integration.py
"""
Streamlit integration tests for ICE UI
Tests that the Streamlit app can start without crashing and handles edge cases
"""

import sys
import os
import subprocess
import time
import signal
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_streamlit_app_startup():
    """
    Test that Streamlit app can start without immediate crashes
    This is a basic smoke test - doesn't test full functionality
    """
    print("🚀 Testing Streamlit app startup...")
    
    ui_file = project_root / "ui_mockups" / "ice_ui_v17.py"
    
    if not ui_file.exists():
        raise FileNotFoundError(f"UI file not found: {ui_file}")
    
    # Start Streamlit in a subprocess with timeout
    try:
        # Use a non-standard port to avoid conflicts
        cmd = [
            sys.executable, "-m", "streamlit", "run", str(ui_file),
            "--server.port", "8503",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        print(f"Starting: {' '.join(cmd)}")
        
        # Set environment variables to avoid issues
        env = os.environ.copy()
        env.update({
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
            "STREAMLIT_SERVER_HEADLESS": "true"
        })
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(project_root)
        )
        
        # Wait a few seconds for startup
        startup_timeout = 15
        print(f"Waiting {startup_timeout}s for Streamlit to start...")
        
        for i in range(startup_timeout):
            if process.poll() is not None:
                # Process ended - check if it was an error
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    print(f"❌ Streamlit failed to start (exit code {process.returncode})")
                    print(f"STDOUT: {stdout}")
                    print(f"STDERR: {stderr}")
                    raise RuntimeError(f"Streamlit startup failed: {stderr}")
                else:
                    print("✅ Streamlit started and stopped cleanly")
                    return
            
            time.sleep(1)
            
        # If we get here, Streamlit is still running - that's good!
        print("✅ Streamlit app started successfully!")
        
        # Clean shutdown
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        print("✅ Streamlit app shut down cleanly")
        
    except Exception as e:
        print(f"❌ Streamlit startup test failed: {e}")
        raise


def test_streamlit_app_import_modules():
    """Test that all required modules for Streamlit can be imported"""
    print("📦 Testing Streamlit module imports...")
    
    required_modules = [
        'streamlit',
        'networkx', 
        'pandas',
        'pyvis'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} available")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} missing")
    
    if missing_modules:
        print(f"⚠️ Missing required modules: {missing_modules}")
        print("Install with: pip install streamlit networkx pandas pyvis")
    else:
        print("✅ All required modules available")
    
    return len(missing_modules) == 0


if __name__ == "__main__":
    print("🧪 Running Streamlit Integration Tests...")
    
    try:
        # Test module availability first
        modules_ok = test_streamlit_app_import_modules()
        
        if modules_ok:
            # Only test startup if modules are available
            test_streamlit_app_startup()
            print("\n🎉 All Streamlit tests passed!")
        else:
            print("\n⚠️ Streamlit tests skipped due to missing modules")
        
    except Exception as e:
        print(f"\n❌ Streamlit test failed: {e}")
        sys.exit(1)