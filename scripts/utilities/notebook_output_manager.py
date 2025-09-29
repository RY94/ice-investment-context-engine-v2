#!/usr/bin/env python3
# notebook_output_manager.py
# Simple output container management for ice_development.ipynb
# Prevents output accumulation by managing single instances of output widgets

from typing import Dict, Any
import ipywidgets as widgets

class OutputManager:
    """Manages output containers to prevent duplication"""
    
    def __init__(self):
        self.containers: Dict[str, widgets.Output] = {}
        self.initialized_sections: set = set()
    
    def get_or_create_output(self, key: str) -> widgets.Output:
        """Get existing output container or create new one"""
        if key not in self.containers:
            self.containers[key] = widgets.Output()
        return self.containers[key]
    
    def clear_output(self, key: str):
        """Clear specific output container"""
        if key in self.containers:
            self.containers[key].clear_output(wait=True)
    
    def clear_all_outputs(self):
        """Clear all output containers"""
        for container in self.containers.values():
            container.clear_output(wait=True)
    
    def is_section_initialized(self, section: str) -> bool:
        """Check if section is already initialized"""
        return section in self.initialized_sections
    
    def mark_section_initialized(self, section: str):
        """Mark section as initialized"""
        self.initialized_sections.add(section)
    
    def reset_section(self, section: str):
        """Reset section initialization status"""
        if section in self.initialized_sections:
            self.initialized_sections.remove(section)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get output manager statistics"""
        return {
            'output_containers': len(self.containers),
            'initialized_sections': len(self.initialized_sections),
            'containers': list(self.containers.keys()),
            'sections': list(self.initialized_sections)
        }

# Global output manager instance
_output_manager = OutputManager()

# Convenience functions
def get_output(key: str) -> widgets.Output:
    """Get or create output container"""
    return _output_manager.get_or_create_output(key)

def clear_output(key: str):
    """Clear specific output"""
    _output_manager.clear_output(key)

def clear_all_outputs():
    """Clear all outputs"""
    _output_manager.clear_all_outputs()

def section_guard(section: str) -> bool:
    """Guard against duplicate section initialization"""
    if _output_manager.is_section_initialized(section):
        return False  # Already initialized
    else:
        _output_manager.mark_section_initialized(section)
        return True  # First initialization

def reset_section(section: str):
    """Reset section for re-initialization"""
    _output_manager.reset_section(section)

def output_stats():
    """Get output manager statistics"""
    return _output_manager.get_stats()

# Simple integration pattern for notebook cells:
"""
# At the start of interface cells, use:
from notebook_output_manager import section_guard, get_output

if section_guard('query_interface'):
    # Your interface initialization code here
    output_area = get_output('query_output')
    # ... rest of interface setup
    
    # Display interface
    display(output_area)
else:
    print("✅ Query interface already initialized")
"""