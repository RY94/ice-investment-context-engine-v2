# ice_core/__init__.py
"""
ICE Core Integration Module for Investment Context Engine
Main module orchestrating LightRAG, Exa MCP, and graph-based intelligence
Provides unified interface for all ICE functionality across the application
Relevant files: ice_lightrag/ice_rag.py, ui_mockups/ice_ui_v17.py, ice_data_ingestion/
"""

from .ice_system_manager import ICESystemManager
from .ice_graph_builder import ICEGraphBuilder
from .ice_query_processor import ICEQueryProcessor

__all__ = [
    'ICESystemManager',
    'ICEGraphBuilder', 
    'ICEQueryProcessor'
]

# Version info for integration tracking
__version__ = "0.1.0"
__integration_date__ = "2025-01-09"