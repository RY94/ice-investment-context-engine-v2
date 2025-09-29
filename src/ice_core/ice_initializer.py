# ice_core/ice_initializer.py
"""
ICE System Initializer - Ensures proper initialization of all components
Handles environment validation, dependency checking, and proper startup sequence
Provides clear error messages and recovery suggestions for initialization failures
Relevant files: ice_lightrag/ice_rag.py, ice_system_manager.py, ice_error_handling.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ICEInitializationError(Exception):
    """Custom exception for ICE initialization failures with recovery suggestions"""

    def __init__(self, message: str, recovery_steps: list = None, missing_deps: list = None):
        self.message = message
        self.recovery_steps = recovery_steps or []
        self.missing_deps = missing_deps or []
        super().__init__(self.message)

    def get_recovery_guide(self) -> str:
        """Get formatted recovery guide"""
        guide = f"\n❌ ERROR: {self.message}\n"

        if self.missing_deps:
            guide += "\n📦 Missing Dependencies:\n"
            for dep in self.missing_deps:
                guide += f"   • {dep}\n"
            guide += "\n   Run: pip install " + " ".join(self.missing_deps) + "\n"

        if self.recovery_steps:
            guide += "\n🔧 Recovery Steps:\n"
            for i, step in enumerate(self.recovery_steps, 1):
                guide += f"   {i}. {step}\n"

        return guide


class ICESystemInitializer:
    """
    Comprehensive system initializer for ICE Investment Context Engine

    Ensures proper initialization sequence:
    1. Validate environment and dependencies
    2. Check API keys and configuration
    3. Initialize core components in correct order
    4. Validate system readiness
    5. Provide clear error messages and recovery paths
    """

    def __init__(self, working_dir: str = "./ice_lightrag/storage"):
        """Initialize the system initializer"""
        self.working_dir = Path(working_dir)
        self.validation_results = {}
        self.initialized_components = {}
        self.start_time = datetime.now()

    def validate_environment(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Comprehensive environment validation with detailed checks

        Returns:
            Tuple of (success, validation_details)
        """
        validation = {
            "python_version": sys.version,
            "working_directory": str(Path.cwd()),
            "dependencies": {},
            "api_keys": {},
            "system_resources": {},
            "file_permissions": {},
            "network_connectivity": {},
            "issues": [],
            "warnings": []
        }

        # Check Python version
        if sys.version_info < (3, 8):
            validation["issues"].append("Python 3.8+ required")
        elif sys.version_info < (3, 9):
            validation["warnings"].append("Python 3.9+ recommended for best performance")

        # Check critical dependencies with version requirements
        required_packages = {
            "lightrag": ("LightRAG for knowledge graph", ">=0.1.0"),
            "openai": ("OpenAI API client", ">=1.0.0"),
            "nest_asyncio": ("Jupyter notebook compatibility", ">=1.5.8"),
            "networkx": ("Graph operations", ">=3.1"),
            "pandas": ("Data processing", ">=2.0.0"),
            "numpy": ("Numerical operations", ">=1.24.0"),
            "aiohttp": ("Async HTTP client", ">=3.8.0")
        }

        missing_deps = []
        outdated_deps = []

        for package, (description, min_version) in required_packages.items():
            try:
                module = __import__(package)
                validation["dependencies"][package] = "✅ Available"

                # Check version if available
                if hasattr(module, '__version__'):
                    version = module.__version__
                    validation["dependencies"][package] += f" (v{version})"

                    # Simple version check (could be enhanced)
                    if min_version and version < min_version.replace(">=", ""):
                        outdated_deps.append(f"{package}>={min_version}")
                        validation["warnings"].append(f"{package} version {version} < {min_version}")

            except ImportError:
                validation["dependencies"][package] = "❌ Missing"
                missing_deps.append(package)
                validation["issues"].append(f"Missing {package}: {description}")

        # Check API keys with validation
        api_key_checks = {
            "OPENAI_API_KEY": ("OpenAI", True, "sk-"),  # Required, starts with sk-
            "EXA_API_KEY": ("Exa Search", False, None),  # Optional
            "ALPHA_VANTAGE_API_KEY": ("Alpha Vantage", False, None),  # Optional
            "POLYGON_API_KEY": ("Polygon.io", False, None),  # Optional
            "FINNHUB_API_KEY": ("Finnhub", False, None)  # Optional
        }

        for key_name, (service, required, prefix) in api_key_checks.items():
            key_value = os.getenv(key_name)
            if key_value:
                # Validate key format if prefix specified
                if prefix and not key_value.startswith(prefix):
                    validation["api_keys"][service] = "⚠️ Invalid format"
                    validation["warnings"].append(f"{key_name} doesn't match expected format")
                else:
                    validation["api_keys"][service] = "✅ Configured"
                    # Mask the key for security
                    masked_key = key_value[:10] + "..." if len(key_value) > 10 else "***"
                    validation["api_keys"][service] += f" ({masked_key})"
            else:
                validation["api_keys"][service] = "❌ Not configured"
                if required:
                    validation["issues"].append(f"Required: {key_name} not set")

        # Check system resources
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            validation["system_resources"] = {
                "cpu_usage": f"{cpu_percent}%",
                "memory_available": f"{memory.available / (1024**3):.1f} GB",
                "memory_percent": f"{memory.percent}%",
                "disk_free": f"{disk.free / (1024**3):.1f} GB",
                "disk_percent": f"{disk.percent}%"
            }

            # Warnings for resource constraints
            if memory.percent > 90:
                validation["warnings"].append("Low memory available (>90% used)")
            if disk.percent > 90:
                validation["warnings"].append("Low disk space (>90% used)")

        except ImportError:
            validation["system_resources"] = {"status": "psutil not available"}

        # Check file permissions
        test_paths = [
            self.working_dir,
            self.working_dir / "test_write.tmp",
            Path.cwd() / ".env"
        ]

        for path in test_paths:
            try:
                if path.suffix == ".tmp":
                    # Test write permission
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.touch()
                    path.unlink()
                    validation["file_permissions"][str(path.parent)] = "✅ Writable"
                elif path.exists():
                    validation["file_permissions"][str(path)] = "✅ Exists"
                else:
                    validation["file_permissions"][str(path)] = "⚠️ Not found"
            except Exception as e:
                validation["file_permissions"][str(path)] = f"❌ Error: {e}"
                if "test_write" not in str(path):
                    validation["warnings"].append(f"Cannot access {path}")

        # Check network connectivity
        import socket
        test_hosts = [
            ("OpenAI API", "api.openai.com", 443),
            ("GitHub", "github.com", 443),
            ("PyPI", "pypi.org", 443)
        ]

        for service, host, port in test_hosts:
            try:
                socket.create_connection((host, port), timeout=5).close()
                validation["network_connectivity"][service] = "✅ Reachable"
            except (socket.timeout, socket.error) as e:
                validation["network_connectivity"][service] = "❌ Unreachable"
                validation["warnings"].append(f"Cannot reach {service} ({host})")

        # Determine overall success
        success = len(validation["issues"]) == 0
        self.validation_results = validation

        # Raise detailed error if critical issues found
        if not success:
            if missing_deps:
                raise ICEInitializationError(
                    "Missing required dependencies",
                    recovery_steps=[
                        f"Install missing packages: pip install {' '.join(missing_deps)}",
                        "Or install all requirements: pip install -r requirements.txt",
                        "Restart your Python kernel/environment",
                        "Re-run the initialization"
                    ],
                    missing_deps=missing_deps
                )
            else:
                # Other critical issues
                raise ICEInitializationError(
                    f"Environment validation failed: {', '.join(validation['issues'])}",
                    recovery_steps=[
                        "Review the issues listed above",
                        "Fix each issue step by step",
                        "Re-run validation after fixes"
                    ]
                )

        return success, validation

    def initialize_lightrag(self) -> Any:
        """
        Initialize LightRAG with proper error handling

        Returns:
            Initialized SimpleICERAG instance

        Raises:
            ICEInitializationError: If initialization fails
        """
        try:
            # Import with proper error handling
            try:
                from src.ice_lightrag.ice_rag import SimpleICERAG
            except ImportError:
                # Try alternative import path
                sys.path.insert(0, str(Path.cwd() / 'src'))
                from ice_lightrag.ice_rag import SimpleICERAG

            # Initialize with explicit working directory
            storage_dir = self.working_dir / "lightrag"
            storage_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Initializing LightRAG with storage: {storage_dir}")
            ice_rag = SimpleICERAG(working_dir=str(storage_dir))

            # Validate initialization
            if not ice_rag.is_ready():
                raise ICEInitializationError(
                    "LightRAG failed to initialize properly",
                    recovery_steps=[
                        "Check that OPENAI_API_KEY is set correctly",
                        "Verify your OpenAI API key is valid and has credits",
                        "Check network connectivity to OpenAI API",
                        "Review logs for detailed error messages"
                    ]
                )

            self.initialized_components["lightrag"] = ice_rag
            logger.info("✅ LightRAG initialized successfully")
            return ice_rag

        except ImportError as e:
            raise ICEInitializationError(
                f"Cannot import LightRAG module: {e}",
                recovery_steps=[
                    "Install LightRAG: pip install lightrag",
                    "Verify installation: python -c 'import lightrag'",
                    "Check Python path includes project directory"
                ],
                missing_deps=["lightrag"]
            )

        except Exception as e:
            raise ICEInitializationError(
                f"LightRAG initialization failed: {e}",
                recovery_steps=[
                    "Check error details above",
                    "Verify all dependencies are installed",
                    "Ensure API keys are configured",
                    "Try running in a fresh Python environment"
                ]
            )

    def initialize_system_manager(self, lightrag_instance=None) -> Any:
        """
        Initialize ICE System Manager

        Args:
            lightrag_instance: Optional pre-initialized LightRAG instance

        Returns:
            Initialized ICESystemManager

        Raises:
            ICEInitializationError: If initialization fails
        """
        try:
            from src.ice_core.ice_system_manager import ICESystemManager

            # Use provided instance or initialize new one
            if lightrag_instance is None:
                lightrag_instance = self.initialize_lightrag()

            # Create system manager
            manager = ICESystemManager(working_dir=str(self.working_dir))

            # Inject the initialized LightRAG instance
            manager._lightrag = lightrag_instance

            # Validate system manager
            if not manager.is_ready():
                status = manager.get_system_status()
                raise ICEInitializationError(
                    "System manager not ready",
                    recovery_steps=[
                        "Check component errors in status report",
                        "Verify all required services are running",
                        "Review initialization logs"
                    ]
                )

            self.initialized_components["system_manager"] = manager
            logger.info("✅ System Manager initialized successfully")
            return manager

        except ImportError as e:
            raise ICEInitializationError(
                f"Cannot import System Manager: {e}",
                recovery_steps=[
                    "Verify ice_core module exists",
                    "Check for circular import issues",
                    "Ensure project structure is intact"
                ]
            )

        except Exception as e:
            raise ICEInitializationError(
                f"System Manager initialization failed: {e}",
                recovery_steps=[
                    "Check error details above",
                    "Verify LightRAG is initialized",
                    "Review system logs for details"
                ]
            )

    def initialize_full_system(self) -> Dict[str, Any]:
        """
        Initialize the complete ICE system with all components

        Returns:
            Dictionary with all initialized components

        Raises:
            ICEInitializationError: If any critical component fails
        """
        print("🚀 === ICE SYSTEM INITIALIZATION ===")
        print(f"📅 Started: {self.start_time}")

        # Step 1: Validate environment
        print("\n📋 Step 1: Validating environment...")
        try:
            success, validation = self.validate_environment()
            if success:
                print("✅ Environment validation passed")
            else:
                print("⚠️ Environment has issues:")
                for issue in validation["issues"]:
                    print(f"   • {issue}")
        except ICEInitializationError as e:
            print(e.get_recovery_guide())
            raise

        # Step 2: Initialize LightRAG
        print("\n🤖 Step 2: Initializing LightRAG...")
        try:
            lightrag = self.initialize_lightrag()
            print("✅ LightRAG ready")
        except ICEInitializationError as e:
            print(e.get_recovery_guide())
            raise

        # Step 3: Initialize System Manager
        print("\n🎯 Step 3: Initializing System Manager...")
        try:
            manager = self.initialize_system_manager(lightrag)
            print("✅ System Manager ready")
        except ICEInitializationError as e:
            print(e.get_recovery_guide())
            raise

        # Step 4: System status report
        print("\n📊 Step 4: System Status Report")
        status = manager.get_system_status()
        print(f"   • Ready: {'✅' if status['ready'] else '❌'}")
        print(f"   • Components initialized: {sum(1 for v in status['components'].values() if v)}/{len(status['components'])}")
        print(f"   • Errors: {len(status['errors'])}")

        initialization_time = (datetime.now() - self.start_time).total_seconds()
        print(f"\n✅ === INITIALIZATION COMPLETE ===")
        print(f"⏱️ Total time: {initialization_time:.2f} seconds")

        return {
            "lightrag": lightrag,
            "system_manager": manager,
            "validation": validation,
            "status": status,
            "initialization_time": initialization_time
        }


def initialize_ice_system(working_dir: str = "./ice_lightrag/storage") -> Dict[str, Any]:
    """
    Convenience function to initialize the complete ICE system

    Args:
        working_dir: Working directory for system storage

    Returns:
        Dictionary with initialized components

    Raises:
        ICEInitializationError: If initialization fails
    """
    initializer = ICESystemInitializer(working_dir)
    return initializer.initialize_full_system()


if __name__ == "__main__":
    # Test initialization when run directly
    try:
        components = initialize_ice_system()
        print("\n🎉 ICE System successfully initialized!")
        print(f"   • LightRAG: {components['lightrag'].is_ready()}")
        print(f"   • System Manager: {components['system_manager'].is_ready()}")
    except ICEInitializationError as e:
        print(e.get_recovery_guide())
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)