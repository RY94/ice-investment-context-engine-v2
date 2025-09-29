# notebook_widget_manager.py
# Lightweight widget lifecycle manager for Jupyter notebooks
# Prevents event handler accumulation on cell re-execution
# Ensures clean notebook execution without repeated outputs

"""
Notebook Widget Manager - Elegant Fix for Handler Accumulation

This module provides a simple solution to prevent repeated output instances
when Jupyter notebook cells are re-executed. The core issue is that event
handlers (like button clicks and dropdown changes) accumulate on re-execution,
causing multiple callbacks for a single user action.

Key Features:
- Prevents handler re-registration on cell re-execution
- Maintains notebook's natural execution flow
- Minimal code changes required
- Preserves all existing functionality
"""

class NotebookWidgetManager:
    """Manages widget lifecycle and prevents handler accumulation"""
    
    def __init__(self):
        self.registered_handlers = set()
        self.widget_registry = {}
        self.execution_guards = {}
        self.output_containers = {}  # Track output containers
    
    def register_handler_once(self, widget, handler, handler_type='click', handler_key=None):
        """Register event handler only if not already registered"""
        # Create unique key for this handler
        widget_id = id(widget)
        handler_name = handler.__name__ if hasattr(handler, '__name__') else str(handler)
        key = handler_key or f"{widget_id}_{handler_type}_{handler_name}"
        
        # Only register if not already done
        if key not in self.registered_handlers:
            if handler_type == 'click':
                widget.on_click(handler)
            elif handler_type == 'observe':
                widget.observe(handler, names='value')
            else:
                # Custom handler types
                getattr(widget, f'on_{handler_type}')(handler)
            
            self.registered_handlers.add(key)
            return True
        return False
    
    def guard_cell_execution(self, cell_id):
        """Prevent multiple executions of initialization code"""
        if cell_id not in self.execution_guards:
            self.execution_guards[cell_id] = True
            return True  # First execution
        return False  # Already executed
    
    def register_widget(self, widget_key, widget):
        """Register widget in global registry"""
        self.widget_registry[widget_key] = widget
    
    def get_widget(self, widget_key):
        """Get widget from registry"""
        return self.widget_registry.get(widget_key)
    
    def is_handler_registered(self, widget, handler_type='click', handler_key=None):
        """Check if handler is already registered"""
        widget_id = id(widget)
        key = handler_key or f"{widget_id}_{handler_type}"
        return any(k.startswith(key) for k in self.registered_handlers)
    
    def reset_handlers(self):
        """Reset all handler registrations (for debugging)"""
        self.registered_handlers.clear()
    
    def register_output_container(self, container_key, container):
        """Register output container to prevent duplication"""
        if container_key not in self.output_containers:
            self.output_containers[container_key] = container
            return True
        return False
    
    def get_output_container(self, container_key):
        """Get registered output container"""
        return self.output_containers.get(container_key)
    
    def clear_output_containers(self):
        """Clear all output containers"""
        for container in self.output_containers.values():
            if hasattr(container, 'clear_output'):
                container.clear_output()
    
    def get_stats(self):
        """Get manager statistics"""
        return {
            'registered_handlers': len(self.registered_handlers),
            'registered_widgets': len(self.widget_registry),
            'execution_guards': len(self.execution_guards),
            'output_containers': len(self.output_containers),
            'handlers': list(self.registered_handlers)
        }

# Global manager instance
_notebook_manager = NotebookWidgetManager()

# Convenience functions for notebook use
def register_click_once(widget, handler, handler_key=None):
    """Register click handler only once"""
    return _notebook_manager.register_handler_once(widget, handler, 'click', handler_key)

def register_observe_once(widget, handler, handler_key=None):
    """Register observe handler only once"""
    return _notebook_manager.register_handler_once(widget, handler, 'observe', handler_key)

def guard_cell(cell_id):
    """Guard against multiple cell executions"""
    return _notebook_manager.guard_cell_execution(cell_id)

def register_widget(widget_key, widget):
    """Register widget globally"""
    _notebook_manager.register_widget(widget_key, widget)

def get_widget(widget_key):
    """Get registered widget"""
    return _notebook_manager.get_widget(widget_key)

def manager_stats():
    """Get manager statistics"""
    return _notebook_manager.get_stats()

def register_output_container(container_key, container):
    """Register output container globally"""
    return _notebook_manager.register_output_container(container_key, container)

def get_output_container(container_key):
    """Get registered output container"""
    return _notebook_manager.get_output_container(container_key)

def clear_output_containers():
    """Clear all output containers"""
    _notebook_manager.clear_output_containers()

def reset_manager():
    """Reset manager (for debugging)"""
    _notebook_manager.reset_handlers()
    _notebook_manager.widget_registry.clear()
    _notebook_manager.execution_guards.clear()
    _notebook_manager.output_containers.clear()

# Debug helpers
def debug_handlers():
    """Print all registered handlers"""
    stats = manager_stats()
    print(f"📊 Widget Manager Stats:")
    print(f"  Handlers: {stats['registered_handlers']}")
    print(f"  Widgets: {stats['registered_widgets']}")
    print(f"  Guards: {stats['execution_guards']}")
    if stats['handlers']:
        print("  Handler List:")
        for handler in stats['handlers']:
            print(f"    • {handler}")

# Usage example for notebook cells:
"""
# Before (causes accumulation):
query_button.on_click(on_query_submit)

# After (prevents accumulation):
from notebook_widget_manager import register_click_once
register_click_once(query_button, on_query_submit)

# For dropdown observers:
from notebook_widget_manager import register_observe_once  
register_observe_once(ticker_dropdown, on_ticker_change)

# For cell execution guards:
from notebook_widget_manager import guard_cell
if guard_cell('query_interface'):
    # Initialize widgets and handlers
    pass

# For output containers:
from notebook_widget_manager import register_output_container, get_output_container
if register_output_container('query_output', output_area):
    # First time - create and register
    pass
else:
    # Already exists - get existing
    output_area = get_output_container('query_output')
"""