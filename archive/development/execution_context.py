# execution_context.py
# Execution context detection and management for Jupyter notebooks
# Provides intelligent detection of interactive vs batch execution modes
# Enables conditional behavior based on execution environment

import os
import sys
from typing import Optional, Dict, Any
from enum import Enum


class ExecutionMode(Enum):
    """Execution mode enumeration"""
    INTERACTIVE = "interactive"
    BATCH = "batch"
    TEST = "test"
    DEMO = "demo"


class ExecutionContext:
    """
    Smart execution context detection for Jupyter notebooks.
    Provides methods to detect and adapt to different execution environments.
    """
    
    _mode: Optional[ExecutionMode] = None
    _config: Dict[str, Any] = {}
    
    @classmethod
    def detect_mode(cls) -> ExecutionMode:
        """
        Automatically detect the execution mode based on environment indicators.
        
        Returns:
            ExecutionMode: Detected execution mode
        """
        if cls._mode is not None:
            return cls._mode
        
        # Check for explicit mode override
        env_mode = os.getenv('JUPYTER_EXECUTION_MODE', '').lower()
        if env_mode in ['interactive', 'batch', 'test', 'demo']:
            cls._mode = ExecutionMode(env_mode)
            return cls._mode
        
        # Check for batch execution indicators
        if any(arg in sys.argv for arg in ['execute', 'nbconvert', '--execute']):
            cls._mode = ExecutionMode.BATCH
            return cls._mode
        
        # Check for testing environment
        if any(module in sys.modules for module in ['pytest', 'unittest', 'nose']):
            cls._mode = ExecutionMode.TEST
            return cls._mode
        
        # Check for IPython/Jupyter interactive environment
        try:
            from IPython import get_ipython
            if get_ipython() is not None:
                # Check if we're in a notebook vs terminal
                ipython = get_ipython()
                if hasattr(ipython, 'kernel'):
                    cls._mode = ExecutionMode.INTERACTIVE
                else:
                    cls._mode = ExecutionMode.BATCH
            else:
                cls._mode = ExecutionMode.BATCH
        except ImportError:
            cls._mode = ExecutionMode.BATCH
        
        return cls._mode
    
    @classmethod
    def set_mode(cls, mode: ExecutionMode):
        """
        Explicitly set the execution mode.
        
        Args:
            mode: ExecutionMode to set
        """
        cls._mode = mode
    
    @classmethod
    def is_interactive(cls) -> bool:
        """Check if running in interactive mode"""
        return cls.detect_mode() == ExecutionMode.INTERACTIVE
    
    @classmethod
    def is_batch(cls) -> bool:
        """Check if running in batch mode"""
        return cls.detect_mode() == ExecutionMode.BATCH
    
    @classmethod
    def is_test(cls) -> bool:
        """Check if running in test mode"""
        return cls.detect_mode() == ExecutionMode.TEST
    
    @classmethod
    def is_demo(cls) -> bool:
        """Check if running in demo mode"""
        return cls.detect_mode() == ExecutionMode.DEMO
    
    @classmethod
    def get_mode(cls) -> ExecutionMode:
        """Get current execution mode"""
        return cls.detect_mode()
    
    @classmethod
    def configure(cls, **kwargs):
        """
        Configure execution context parameters.
        
        Args:
            **kwargs: Configuration parameters
        """
        cls._config.update(kwargs)
    
    @classmethod
    def get_config(cls, key: str, default: Any = None) -> Any:
        """
        Get configuration parameter.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return cls._config.get(key, default)
    
    @classmethod
    def should_display_widgets(cls) -> bool:
        """
        Determine if widgets should be displayed based on context.
        
        Returns:
            True if widgets should be displayed
        """
        mode = cls.detect_mode()
        return mode == ExecutionMode.INTERACTIVE or (
            mode == ExecutionMode.DEMO and cls.get_config('show_demo_widgets', False)
        )
    
    @classmethod
    def should_show_verbose_output(cls) -> bool:
        """
        Determine if verbose output should be shown.
        
        Returns:
            True if verbose output should be shown
        """
        mode = cls.detect_mode()
        verbose_override = cls.get_config('verbose', None)
        
        if verbose_override is not None:
            return verbose_override
        
        return mode in [ExecutionMode.INTERACTIVE, ExecutionMode.DEMO]
    
    @classmethod
    def get_output_mode(cls) -> str:
        """
        Get appropriate output mode for current context.
        
        Returns:
            Output mode string ('verbose', 'summary', 'minimal')
        """
        mode = cls.detect_mode()
        
        # Check for explicit override
        output_mode = cls.get_config('output_mode')
        if output_mode:
            return output_mode
        
        # Default based on execution mode
        mode_mapping = {
            ExecutionMode.INTERACTIVE: 'verbose',
            ExecutionMode.DEMO: 'verbose', 
            ExecutionMode.BATCH: 'summary',
            ExecutionMode.TEST: 'minimal'
        }
        
        return mode_mapping.get(mode, 'summary')
    
    @classmethod
    def reset(cls):
        """Reset execution context to allow re-detection"""
        cls._mode = None
        cls._config = {}


# Convenience functions for common checks
def is_interactive() -> bool:
    """Check if running in interactive mode"""
    return ExecutionContext.is_interactive()


def is_batch() -> bool:
    """Check if running in batch mode"""  
    return ExecutionContext.is_batch()


def should_display_widgets() -> bool:
    """Check if widgets should be displayed"""
    return ExecutionContext.should_display_widgets()


def get_output_mode() -> str:
    """Get appropriate output mode"""
    return ExecutionContext.get_output_mode()


# Initialize context on import
ExecutionContext.detect_mode()