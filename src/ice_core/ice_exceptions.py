# src/ice_core/ice_exceptions.py
"""
ICE Custom Exceptions with Recovery Suggestions
Provides detailed error messages and actionable recovery steps for all failure modes
Replaces silent failures with explicit, helpful error reporting
Relevant files: ice_system_manager.py, ice_lightrag/ice_rag.py, ice_error_handling.py
"""

from typing import List, Optional, Dict, Any
import traceback
from datetime import datetime


class ICEException(Exception):
    """Base exception for all ICE system errors with recovery guidance"""

    def __init__(
        self,
        message: str,
        error_code: str = "ICE_ERROR",
        recovery_steps: Optional[List[str]] = None,
        technical_details: Optional[str] = None,
        related_docs: Optional[List[str]] = None
    ):
        """
        Initialize ICE exception with comprehensive error information

        Args:
            message: User-friendly error description
            error_code: Unique error identifier for tracking
            recovery_steps: List of actionable steps to fix the issue
            technical_details: Technical information for debugging
            related_docs: Links to relevant documentation
        """
        self.message = message
        self.error_code = error_code
        self.recovery_steps = recovery_steps or []
        self.technical_details = technical_details
        self.related_docs = related_docs or []
        self.timestamp = datetime.now().isoformat()
        self.traceback = traceback.format_exc()
        super().__init__(self.message)

    def get_full_error_report(self) -> str:
        """Generate comprehensive error report with recovery guidance"""
        report = []
        report.append("\n" + "=" * 60)
        report.append(f"❌ ERROR: {self.error_code}")
        report.append("=" * 60)
        report.append(f"\n📝 Description: {self.message}")
        report.append(f"⏰ Time: {self.timestamp}")

        if self.recovery_steps:
            report.append("\n🔧 Recovery Steps:")
            for i, step in enumerate(self.recovery_steps, 1):
                report.append(f"   {i}. {step}")

        if self.technical_details:
            report.append(f"\n🔍 Technical Details:")
            report.append(f"   {self.technical_details}")

        if self.related_docs:
            report.append("\n📚 Related Documentation:")
            for doc in self.related_docs:
                report.append(f"   • {doc}")

        report.append("\n" + "=" * 60)
        return "\n".join(report)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "recovery_steps": self.recovery_steps,
            "technical_details": self.technical_details,
            "related_docs": self.related_docs,
            "timestamp": self.timestamp,
            "traceback": self.traceback
        }


class LightRAGInitializationError(ICEException):
    """Raised when LightRAG fails to initialize"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        recovery_steps = [
            "Verify OPENAI_API_KEY is set in environment or .env file",
            "Check API key validity: python -c \"import openai; openai.api_key='YOUR_KEY'; print('Valid')\"",
            "Ensure LightRAG is installed: pip install lightrag",
            "Verify network connectivity to OpenAI API",
            "Check if API key has sufficient credits/quota",
            "Try reinitializing: rm -rf ./lightrag/storage && retry"
        ]

        technical_details = None
        if cause:
            technical_details = f"Root cause: {type(cause).__name__}: {str(cause)}"

        super().__init__(
            message=message,
            error_code="LIGHTRAG_INIT_ERROR",
            recovery_steps=recovery_steps,
            technical_details=technical_details,
            related_docs=[
                "md_files/LIGHTRAG_SETUP.md",
                "https://github.com/lightrag/docs/initialization"
            ]
        )


class APIKeyError(ICEException):
    """Raised when required API keys are missing or invalid"""

    def __init__(self, service: str, key_name: str):
        recovery_steps = [
            f"Set {key_name} environment variable",
            f"Add to .env file: {key_name}=your_key_here",
            f"Get API key from {service} dashboard",
            f"Verify key format and validity",
            "Restart Python kernel after setting key"
        ]

        service_urls = {
            "OpenAI": "https://platform.openai.com/api-keys",
            "Exa": "https://exa.ai/dashboard",
            "Alpha Vantage": "https://www.alphavantage.co/support/#api-key",
            "Polygon": "https://polygon.io/dashboard/api-keys"
        }

        super().__init__(
            message=f"{service} API key not configured or invalid",
            error_code=f"{service.upper()}_API_KEY_ERROR",
            recovery_steps=recovery_steps,
            technical_details=f"Missing environment variable: {key_name}",
            related_docs=[
                service_urls.get(service, f"https://www.google.com/search?q={service}+api+key")
            ]
        )


class DependencyError(ICEException):
    """Raised when required dependencies are missing"""

    def __init__(self, package: str, purpose: str):
        recovery_steps = [
            f"Install missing package: pip install {package}",
            "Or install all requirements: pip install -r requirements.txt",
            "Verify installation: python -c \"import {package.replace('-', '_')}\"",
            "If in virtual environment, ensure it's activated",
            "Try upgrading pip: pip install --upgrade pip"
        ]

        super().__init__(
            message=f"Required package '{package}' not installed",
            error_code="DEPENDENCY_ERROR",
            recovery_steps=recovery_steps,
            technical_details=f"Package needed for: {purpose}",
            related_docs=["requirements.txt", f"https://pypi.org/project/{package}/"]
        )


class ComponentInitializationError(ICEException):
    """Raised when ICE components fail to initialize"""

    def __init__(self, component: str, reason: str, dependencies: Optional[List[str]] = None):
        recovery_steps = [
            f"Check {component} configuration in ice_core/",
            "Verify all dependencies are initialized",
            "Check system logs for detailed errors",
            "Try reinitializing with ice_initializer.py",
            "Ensure working directory has write permissions"
        ]

        if dependencies:
            recovery_steps.insert(1, f"Ensure these are ready: {', '.join(dependencies)}")

        super().__init__(
            message=f"{component} initialization failed: {reason}",
            error_code=f"{component.upper()}_INIT_ERROR",
            recovery_steps=recovery_steps,
            technical_details=f"Component: {component}, Dependencies: {dependencies}",
            related_docs=["src/ice_core/ice_initializer.py", "md_files/SYSTEM_ARCHITECTURE.md"]
        )


class DataIngestionError(ICEException):
    """Raised when document/data ingestion fails"""

    def __init__(self, source: str, reason: str, document_info: Optional[Dict] = None):
        recovery_steps = [
            "Check document format and encoding",
            "Verify document size (should be < 100KB for optimal processing)",
            "Ensure LightRAG is properly initialized",
            "Check available disk space for storage",
            "Try processing smaller document chunks",
            "Verify OpenAI API is accessible"
        ]

        technical_details = f"Source: {source}, Reason: {reason}"
        if document_info:
            technical_details += f", Doc info: {document_info}"

        super().__init__(
            message=f"Failed to ingest data from {source}",
            error_code="DATA_INGESTION_ERROR",
            recovery_steps=recovery_steps,
            technical_details=technical_details,
            related_docs=["md_files/DATA_INGESTION.md"]
        )


class QueryProcessingError(ICEException):
    """Raised when query processing fails"""

    def __init__(self, query: str, mode: str, reason: str):
        recovery_steps = [
            "Verify knowledge base has documents",
            "Check query syntax and length",
            f"Try different query mode (current: {mode})",
            "Ensure LightRAG indices are built",
            "Check if OpenAI API is responding",
            "Try simpler query first"
        ]

        super().__init__(
            message=f"Query processing failed: {reason}",
            error_code="QUERY_ERROR",
            recovery_steps=recovery_steps,
            technical_details=f"Query: '{query[:100]}...', Mode: {mode}",
            related_docs=["md_files/QUERY_PATTERNS.md"]
        )


class SystemNotReadyError(ICEException):
    """Raised when system is not ready for operations"""

    def __init__(self, components_status: Dict[str, bool], required_components: List[str]):
        not_ready = [c for c in required_components if not components_status.get(c, False)]

        recovery_steps = [
            "Run initialization: python src/ice_core/ice_initializer.py",
            f"Check these components: {', '.join(not_ready)}",
            "Verify all API keys are configured",
            "Check system logs for initialization errors",
            "Try restarting Python kernel"
        ]

        super().__init__(
            message=f"System not ready. Missing: {', '.join(not_ready)}",
            error_code="SYSTEM_NOT_READY",
            recovery_steps=recovery_steps,
            technical_details=f"Component status: {components_status}",
            related_docs=["CLAUDE.md", "README.md"]
        )


class CircularDependencyError(ICEException):
    """Raised when circular dependencies are detected"""

    def __init__(self, module1: str, module2: str):
        recovery_steps = [
            "Use dependency injection pattern",
            "Initialize components separately",
            "Pass dependencies as parameters",
            "Avoid importing at module level",
            "Use lazy imports inside functions"
        ]

        super().__init__(
            message=f"Circular dependency detected between {module1} and {module2}",
            error_code="CIRCULAR_DEPENDENCY",
            recovery_steps=recovery_steps,
            technical_details=f"Modules: {module1} <-> {module2}",
            related_docs=["src/ice_core/ice_initializer.py"]
        )


def handle_exception_with_recovery(func):
    """Decorator to handle exceptions with recovery suggestions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ICEException as e:
            # Already has recovery info
            print(e.get_full_error_report())
            raise
        except ImportError as e:
            package = str(e).split("'")[1] if "'" in str(e) else "unknown"
            ice_error = DependencyError(package, f"Required by {func.__name__}")
            print(ice_error.get_full_error_report())
            raise ice_error
        except KeyError as e:
            if "API" in str(e) or "KEY" in str(e):
                ice_error = APIKeyError("Unknown", str(e))
                print(ice_error.get_full_error_report())
                raise ice_error
            raise
        except Exception as e:
            # Generic exception - wrap with ICE exception
            ice_error = ICEException(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                recovery_steps=[
                    "Check the error details above",
                    "Review recent code changes",
                    "Check system logs for more information",
                    "Try running in debug mode: export ICE_DEBUG=1"
                ],
                technical_details=str(e)
            )
            print(ice_error.get_full_error_report())
            raise ice_error

    return wrapper


# Usage example for error reporting
def raise_helpful_error(error_type: str, **kwargs):
    """Utility function to raise appropriate errors with recovery guidance"""
    error_map = {
        "lightrag": LightRAGInitializationError,
        "api_key": APIKeyError,
        "dependency": DependencyError,
        "component": ComponentInitializationError,
        "ingestion": DataIngestionError,
        "query": QueryProcessingError,
        "not_ready": SystemNotReadyError,
        "circular": CircularDependencyError
    }

    error_class = error_map.get(error_type, ICEException)
    raise error_class(**kwargs)