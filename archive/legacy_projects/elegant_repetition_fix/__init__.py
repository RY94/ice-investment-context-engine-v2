#!/usr/bin/env python3
# elegant_repetition_fix/__init__.py
# Package initialization for elegant repetition fix solution
# Provides convenient imports and setup functions

"""
Elegant Repetition Fix Package

This package provides a comprehensive solution for preventing display content
repetition in Jupyter notebooks, specifically addressing issues identified in
the ICE development notebook.

Quick Setup:
    from elegant_repetition_fix import setup_elegant_repetition_fix
    setup_elegant_repetition_fix()

Key Components:
    - DisplaySectionManager: Core section-based display management
    - EnhancedRichDisplay: Section-aware display components
    - Integration utilities: Seamless notebook integration
    - Comprehensive test suite: Verify all patterns are fixed
"""

__version__ = "1.0.0"
__author__ = "ICE Development Team"
__description__ = "Elegant solution for Jupyter notebook display repetition issues"

# Import main components for easy access
from .enhanced_output_manager import (
    DisplaySectionManager,
    get_display_manager,
    display_section,
    section_guard,
    display_in_section
)

from .enhanced_rich_display import (
    RichDisplay,
    EnhancedRichDisplay,
    display_query_history,
    display_ticker_intelligence_section,
    display_portfolio_section
)

from .integration_guide import (
    setup_elegant_repetition_fix,
    apply_repetition_fix_to_notebook,
    test_repetition_fix,
    get_fix_status
)

# Convenience imports
__all__ = [
    # Core components
    'DisplaySectionManager',
    'get_display_manager',
    'display_section',
    'section_guard', 
    'display_in_section',
    
    # Display components
    'RichDisplay',
    'EnhancedRichDisplay',
    'display_query_history',
    'display_ticker_intelligence_section',
    'display_portfolio_section',
    
    # Setup and integration
    'setup_elegant_repetition_fix',
    'apply_repetition_fix_to_notebook', 
    'test_repetition_fix',
    'get_fix_status',
    
    # Package info
    '__version__',
    '__author__',
    '__description__'
]