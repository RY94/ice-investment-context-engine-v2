#!/usr/bin/env python3
# elegant_repetition_fix/enhanced_output_manager.py
# Enhanced output container management with section-based automatic clearing
# Builds upon existing notebook_output_manager.py with elegant section management
# Prevents display content accumulation in Jupyter notebook cell re-execution

"""
Enhanced Output Manager - Elegant Fix for Display Content Accumulation

This module provides an enhanced version of the output manager that adds
section-based display management with automatic clearing capabilities.

Key Features:
- Section-based display management with automatic clearing
- Context manager support for grouped displays  
- Decorator patterns for seamless integration
- Backward compatibility with existing output manager
- Minimal code changes required for integration

Design Philosophy:
- Leverage existing infrastructure rather than replacing it
- Use clean decorator and context manager patterns
- Automatic clearing without manual intervention
- Preserve all existing functionality
"""

from typing import Dict, Any, Optional, Set
from contextlib import contextmanager
from functools import wraps
import ipywidgets as widgets
from IPython.display import clear_output, display, HTML

class DisplaySectionManager:
    """
    Enhanced display manager with section-based automatic clearing.
    
    Manages display sections that automatically clear their content before
    showing new content, preventing accumulation on notebook cell re-execution.
    """
    
    def __init__(self):
        self.containers: Dict[str, widgets.Output] = {}
        self.section_states: Dict[str, Dict[str, Any]] = {}
        self.active_sections: Set[str] = set()
        self.execution_guards: Dict[str, bool] = {}
        
    def get_or_create_output(self, section_name: str) -> widgets.Output:
        """Get existing output container or create new one for section"""
        if section_name not in self.containers:
            self.containers[section_name] = widgets.Output()
            self.section_states[section_name] = {
                'created_at': 0,
                'last_cleared': 0,
                'display_count': 0,
                'auto_clear': True
            }
        return self.containers[section_name]
    
    def clear_section(self, section_name: str, wait: bool = True):
        """Clear specific section container"""
        if section_name in self.containers:
            self.containers[section_name].clear_output(wait=wait)
            self.section_states[section_name]['last_cleared'] = self._get_timestamp()
            self.section_states[section_name]['display_count'] = 0
    
    def clear_all_sections(self, wait: bool = True):
        """Clear all section containers"""
        for container in self.containers.values():
            container.clear_output(wait=wait)
        for state in self.section_states.values():
            state['last_cleared'] = self._get_timestamp()
            state['display_count'] = 0
    
    @contextmanager
    def section(self, section_name: str, auto_clear: bool = True, 
                display_container: bool = True):
        """
        Context manager for section-based display with automatic clearing.
        
        Args:
            section_name: Unique name for the display section
            auto_clear: Whether to automatically clear before displaying
            display_container: Whether to display the container widget
            
        Usage:
            with display_manager.section("query_results"):
                display(HTML("<h3>Query Results</h3>"))
                display(DataFrame(...))
        """
        # Get or create output container
        container = self.get_or_create_output(section_name)
        
        # Auto-clear if enabled
        if auto_clear and section_name not in self.active_sections:
            self.clear_section(section_name)
        
        # Mark section as active
        self.active_sections.add(section_name)
        
        try:
            # Display container if requested
            if display_container and section_name not in self.execution_guards:
                display(container)
                self.execution_guards[section_name] = True
            
            # Context for all display operations within this section
            with container:
                yield container
                
        finally:
            # Track display completion
            self.section_states[section_name]['display_count'] += 1
            self.active_sections.discard(section_name)
    
    def is_section_active(self, section_name: str) -> bool:
        """Check if section is currently active"""
        return section_name in self.active_sections
    
    def get_section_stats(self, section_name: str) -> Dict[str, Any]:
        """Get statistics for specific section"""
        if section_name in self.section_states:
            return self.section_states[section_name].copy()
        return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall display manager statistics"""
        return {
            'total_sections': len(self.containers),
            'active_sections': len(self.active_sections),
            'section_names': list(self.containers.keys()),
            'active_section_names': list(self.active_sections),
            'execution_guards': len(self.execution_guards)
        }
    
    def reset_section_guard(self, section_name: str):
        """Reset execution guard for section (for testing)"""
        if section_name in self.execution_guards:
            del self.execution_guards[section_name]
    
    def reset_all_guards(self):
        """Reset all execution guards (for testing)"""
        self.execution_guards.clear()
    
    @staticmethod
    def _get_timestamp() -> int:
        """Get current timestamp for tracking"""
        import time
        return int(time.time() * 1000)

# Global display manager instance
_display_manager = DisplaySectionManager()

def get_display_manager() -> DisplaySectionManager:
    """Get the global display manager instance"""
    return _display_manager

def display_section(section_name: str, auto_clear: bool = True, 
                   display_container: bool = True):
    """
    Decorator for automatic section-based display management.
    
    Args:
        section_name: Unique name for the display section
        auto_clear: Whether to automatically clear before displaying
        display_container: Whether to display the container widget
        
    Usage:
        @display_section("query_history")
        def show_query_history():
            # Content automatically clears before display
            display(HTML("<h3>Query History</h3>"))
            # ... rest of function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with _display_manager.section(section_name, auto_clear, display_container):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Convenience functions for common patterns
def section_guard(section_name: str):
    """Simple section guard decorator - auto-clear enabled by default"""
    return display_section(section_name, auto_clear=True, display_container=True)

def display_in_section(section_name: str, content, clear_first: bool = True):
    """Display content in specific section with optional clearing"""
    manager = get_display_manager()
    container = manager.get_or_create_output(section_name)
    
    if clear_first:
        manager.clear_section(section_name)
    
    with container:
        if isinstance(content, str):
            display(HTML(content))
        else:
            display(content)

# Legacy compatibility functions
def get_output(key: str) -> widgets.Output:
    """Legacy compatibility - get output container"""
    return _display_manager.get_or_create_output(key)

def output_stats() -> Dict[str, Any]:
    """Legacy compatibility - get output statistics"""
    return _display_manager.get_stats()

def clear_all_outputs():
    """Legacy compatibility - clear all outputs"""
    _display_manager.clear_all_sections()

# Export main components
__all__ = [
    'DisplaySectionManager',
    'get_display_manager', 
    'display_section',
    'section_guard',
    'display_in_section',
    'get_output',
    'output_stats', 
    'clear_all_outputs'
]