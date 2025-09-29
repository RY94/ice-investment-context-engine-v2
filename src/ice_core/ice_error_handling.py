# ice_error_handling.py
# Comprehensive error handling and health checks for ICE Development Environment
# Provides robust error recovery and system health monitoring
# Enables graceful degradation and helpful error messages

import os
import sys
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class ICEException(Exception):
    """Base exception class for ICE system errors with recovery suggestions"""
    
    def __init__(self, message: str, error_code: str = None, recovery_suggestion: str = None, cause: Exception = None):
        self.message = message
        self.error_code = error_code or "ICE_ERROR"
        self.recovery_suggestion = recovery_suggestion or "Please check the documentation or contact support"
        self.cause = cause
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"
    
    def get_full_details(self) -> Dict[str, Any]:
        """Get comprehensive error details"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "recovery_suggestion": self.recovery_suggestion,
            "timestamp": self.timestamp,
            "cause": str(self.cause) if self.cause else None,
            "traceback": traceback.format_exc() if self.cause else None
        }


class ICESystemHealthCheck:
    """Comprehensive system health monitoring and diagnostics"""
    
    @staticmethod
    def check_python_environment() -> Dict[str, Any]:
        """Check Python environment and dependencies"""
        results = {
            "python_version": sys.version,
            "python_executable": sys.executable,
            "platform": sys.platform,
            "working_directory": os.getcwd(),
            "pythonpath": sys.path[:3]  # First 3 entries only
        }
        
        # Check critical imports
        critical_imports = [
            "pandas", "numpy", "networkx", "plotly", 
            "ipywidgets", "streamlit", "json", "datetime"
        ]
        
        import_results = {}
        for module in critical_imports:
            try:
                __import__(module)
                import_results[module] = {"available": True, "version": "unknown"}
                
                # Try to get version
                try:
                    mod = sys.modules[module]
                    if hasattr(mod, '__version__'):
                        import_results[module]["version"] = mod.__version__
                except:
                    pass
                    
            except ImportError as e:
                import_results[module] = {"available": False, "error": str(e)}
        
        results["imports"] = import_results
        return results
    
    @staticmethod
    def check_file_system() -> Dict[str, Any]:
        """Check file system access and required directories"""
        results = {}
        
        # Check critical directories
        dirs_to_check = [
            "./ice_lightrag/storage",
            "./ice_lazyrag/storage",
            "./unified_storage",
            "./storage/cache"
        ]
        
        for dir_path in dirs_to_check:
            path = Path(dir_path)
            results[dir_path] = {
                "exists": path.exists(),
                "is_directory": path.is_dir() if path.exists() else False,
                "readable": os.access(path, os.R_OK) if path.exists() else False,
                "writable": os.access(path, os.W_OK) if path.exists() else False
            }
        
        # Check critical files
        files_to_check = [
            "execution_context.py",
            "sample_data.py", 
            "ice_unified_rag.py",
            "ice_development.ipynb"
        ]
        
        for file_path in files_to_check:
            path = Path(file_path)
            results[file_path] = {
                "exists": path.exists(),
                "readable": os.access(path, os.R_OK) if path.exists() else False,
                "size_bytes": path.stat().st_size if path.exists() else 0
            }
        
        return results
    
    @staticmethod
    def check_api_configuration() -> Dict[str, Any]:
        """Check API keys and external service configuration"""
        results = {}
        
        # OpenAI API Key
        openai_key = os.getenv('OPENAI_API_KEY')
        results["openai"] = {
            "configured": bool(openai_key),
            "key_length": len(openai_key) if openai_key else 0,
            "key_prefix": openai_key[:10] + "..." if openai_key and len(openai_key) > 10 else None
        }
        
        # Other environment variables
        env_vars_to_check = [
            "JUPYTER_EXECUTION_MODE",
            "ICE_DEBUG",
            "NUMEXPR_MAX_THREADS",
            "PYTHONPATH"
        ]
        
        results["environment"] = {}
        for var in env_vars_to_check:
            value = os.getenv(var)
            results["environment"][var] = {
                "configured": bool(value),
                "value": value[:50] + "..." if value and len(value) > 50 else value
            }
        
        return results
    
    @staticmethod
    def check_rag_engines() -> Dict[str, Any]:
        """Check RAG engine availability and health"""
        results = {}
        
        # Check unified RAG
        try:
            from ice_unified_rag import ICEUnifiedRAG
            unified = ICEUnifiedRAG()
            results["unified_rag"] = {
                "available": True,
                "engines": {name: info.available for name, info in unified.get_available_engines().items()},
                "current_engine": unified.get_current_engine(),
                "ready": unified.is_ready()
            }
        except Exception as e:
            results["unified_rag"] = {"available": False, "error": str(e)}
        
        # Check individual engines
        engines_to_check = [
            ("lightrag", "ice_rag", "ICELightRAG"),
            ("lazyrag", "ice_lazyrag.lazy_rag", "SimpleLazyRAG")
        ]
        
        for name, module, class_name in engines_to_check:
            try:
                mod = __import__(module, fromlist=[class_name])
                cls = getattr(mod, class_name)
                results[name] = {"available": True, "class": f"{module}.{class_name}"}
            except Exception as e:
                results[name] = {"available": False, "error": str(e)}
        
        return results
    
    @staticmethod
    def run_comprehensive_health_check() -> Dict[str, Any]:
        """Run all health checks and return comprehensive report"""
        start_time = datetime.now()
        
        health_report = {
            "timestamp": start_time.isoformat(),
            "overall_status": "unknown",
            "checks": {}
        }
        
        checks = [
            ("python_environment", ICESystemHealthCheck.check_python_environment),
            ("file_system", ICESystemHealthCheck.check_file_system),
            ("api_configuration", ICESystemHealthCheck.check_api_configuration),
            ("rag_engines", ICESystemHealthCheck.check_rag_engines)
        ]
        
        failed_checks = 0
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                health_report["checks"][check_name] = {
                    "status": "passed",
                    "result": result
                }
            except Exception as e:
                health_report["checks"][check_name] = {
                    "status": "failed",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                failed_checks += 1
        
        # Determine overall status
        if failed_checks == 0:
            health_report["overall_status"] = "healthy"
        elif failed_checks < len(checks) / 2:
            health_report["overall_status"] = "degraded"
        else:
            health_report["overall_status"] = "critical"
        
        end_time = datetime.now()
        health_report["duration_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        return health_report


class ICEErrorHandler:
    """Centralized error handling with recovery suggestions"""
    
    def __init__(self, enable_logging: bool = True):
        self.enable_logging = enable_logging
        self.error_history: List[Dict[str, Any]] = []
        
        if enable_logging:
            self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "ice_development.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("ICE")
    
    def handle_error(self, error: Exception, context: str = None, recovery_action: str = None) -> ICEException:
        """Handle error with context and recovery suggestions"""
        
        # Determine error type and recovery suggestion
        error_mapping = {
            ImportError: ("IMPORT_ERROR", "Install missing dependencies with: pip install <package>"),
            FileNotFoundError: ("FILE_NOT_FOUND", "Check file path and ensure file exists"),
            PermissionError: ("PERMISSION_ERROR", "Check file permissions and access rights"),
            KeyError: ("KEY_ERROR", "Verify data structure and key names"),
            ValueError: ("VALUE_ERROR", "Check input values and data types"),
            ConnectionError: ("CONNECTION_ERROR", "Check network connection and API endpoints")
        }
        
        error_code, default_recovery = error_mapping.get(type(error), ("UNKNOWN_ERROR", "Contact support for assistance"))
        recovery_suggestion = recovery_action or default_recovery
        
        ice_error = ICEException(
            message=f"{context}: {str(error)}" if context else str(error),
            error_code=error_code,
            recovery_suggestion=recovery_suggestion,
            cause=error
        )
        
        # Log error
        if self.enable_logging and hasattr(self, 'logger'):
            self.logger.error(f"[{error_code}] {ice_error.message}")
            if recovery_suggestion:
                self.logger.info(f"Recovery suggestion: {recovery_suggestion}")
        
        # Store in history
        self.error_history.append(ice_error.get_full_details())
        
        return ice_error
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        if not self.error_history:
            return {"total_errors": 0, "recent_errors": []}
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": self.error_history[-5:],  # Last 5 errors
            "error_types": {}
        }


# Global error handler instance
error_handler = ICEErrorHandler()


def safe_execute(func, *args, context: str = None, fallback_value=None, **kwargs):
    """Safely execute function with error handling and fallback"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        ice_error = error_handler.handle_error(e, context=context)
        print(f"⚠️ Error in {context or 'function execution'}: {ice_error}")
        print(f"💡 Recovery suggestion: {ice_error.recovery_suggestion}")
        return fallback_value


def validate_system_requirements() -> bool:
    """Validate system meets ICE requirements"""
    print("🔍 Validating ICE system requirements...")
    
    health_check = ICESystemHealthCheck.run_comprehensive_health_check()
    
    if health_check["overall_status"] == "healthy":
        print("✅ All system requirements met")
        return True
    elif health_check["overall_status"] == "degraded":
        print("⚠️ System requirements partially met - some features may be limited")
        return True
    else:
        print("❌ Critical system requirements not met")
        print("📋 Health check details:")
        for check_name, check_result in health_check["checks"].items():
            status_icon = "✅" if check_result["status"] == "passed" else "❌"
            print(f"  {status_icon} {check_name}: {check_result['status']}")
        return False


def run_system_diagnostics() -> Dict[str, Any]:
    """Run comprehensive system diagnostics"""
    print("🔧 Running ICE system diagnostics...")
    
    diagnostics = {
        "health_check": ICESystemHealthCheck.run_comprehensive_health_check(),
        "error_summary": error_handler.get_error_summary(),
        "timestamp": datetime.now().isoformat()
    }
    
    # Save diagnostics report
    reports_dir = Path("./reports")
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / f"ice_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        import json
        with open(report_file, 'w') as f:
            json.dump(diagnostics, f, indent=2, default=str)
        print(f"📄 Diagnostics report saved to {report_file}")
    except Exception as e:
        print(f"⚠️ Failed to save diagnostics report: {e}")
    
    return diagnostics


if __name__ == "__main__":
    # Run diagnostics when script is executed directly
    validate_system_requirements()
    run_system_diagnostics()