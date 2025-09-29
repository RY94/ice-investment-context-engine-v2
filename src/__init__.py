# /src/__init__.py
# ICE (Investment Context Engine) - Main Application Package
# This marks the src directory as a Python package containing production-ready code
# RELEVANT FILES: ice_lightrag/__init__.py, ice_core/__init__.py, setup.py

"""
Investment Context Engine (ICE) - Core Application Package

This package contains the production-ready implementation of ICE,
a Graph-RAG based AI system for investment intelligence and portfolio analysis.

Key Modules:
- ice_lightrag: LightRAG integration and AI processing engine
- ice_core: Core system management and orchestration
- simple_demo: Standalone demonstration script
"""

__version__ = "0.2.0"
__author__ = "Roy Yeo Fu Qiang"
__email__ = "A0280541L@u.nus.edu"

# Export main classes for easy imports
try:
    from .ice_lightrag.ice_rag import ICELightRAG
    from .ice_core.ice_system_manager import ICESystemManager
    from .ice_core.ice_unified_rag import ICEUnifiedRAG
except ImportError:
    # Handle import errors gracefully during development
    pass

__all__ = ['ICELightRAG', 'ICESystemManager', 'ICEUnifiedRAG']