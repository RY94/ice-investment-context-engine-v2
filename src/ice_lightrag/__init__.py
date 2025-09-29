# src/ice_lightrag/__init__.py
"""
ICE LightRAG Integration Package
Single unified interface for financial document processing
Uses the Jupyter-compatible wrapper that works in all environments
"""

# Import ONLY the working wrapper
from .ice_rag_fixed import JupyterSyncWrapper as ICELightRAG

# Backwards compatibility warning
def _deprecated_wrapper(*args, **kwargs):
    import warnings
    warnings.warn(
        "SimpleICERAG is deprecated. Use ICELightRAG instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return ICELightRAG(*args, **kwargs)

SimpleICERAG = _deprecated_wrapper

__all__ = ['ICELightRAG']
