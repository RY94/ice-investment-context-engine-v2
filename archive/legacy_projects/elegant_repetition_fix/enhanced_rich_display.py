#!/usr/bin/env python3
# elegant_repetition_fix/enhanced_rich_display.py
# Enhanced RichDisplay class with section-aware automatic clearing
# Prevents display content accumulation while preserving all existing functionality
# Integrates seamlessly with existing execution context awareness

"""
Enhanced RichDisplay Class - Section-Aware Display Management

This module provides an enhanced version of the RichDisplay class that integrates
with the DisplaySectionManager for automatic content clearing and section management.

Key Enhancements:
- Section-aware display methods with automatic clearing
- Backward compatibility with existing RichDisplay usage
- Integration with execution context for batch/interactive modes
- Grouped display operations for logical content sections
- Minimal changes to existing code patterns

Design Philosophy:
- Preserve all existing RichDisplay functionality
- Add optional section management without breaking existing code
- Leverage existing execution context infrastructure
- Clean integration with enhanced output manager
"""

from typing import Optional, List, Dict, Any
from IPython.display import display, HTML
import pandas as pd
from enhanced_output_manager import get_display_manager, display_section, display_in_section

# Import existing execution context (assumed to exist)
try:
    from execution_context import should_display_widgets, get_output_mode
except ImportError:
    # Fallback if execution context not available
    def should_display_widgets():
        return True
    def get_output_mode():
        return "interactive"

class EnhancedRichDisplay:
    """
    Enhanced display utilities with section-aware automatic clearing.
    
    Builds upon the existing RichDisplay class to add section management
    while preserving all existing functionality and patterns.
    """
    
    @staticmethod
    def card(title: str, value: Any, delta: Optional[float] = None, 
             color: str = "#1f77b4", section: Optional[str] = None):
        """
        Display metric card with optional section management.
        
        Args:
            title: Card title
            value: Card value to display
            delta: Optional delta value
            color: Card color
            section: Optional section name for automatic clearing
        """
        if not should_display_widgets():
            # Batch mode: simple text output
            delta_str = f" ({delta:+.2f})" if delta is not None else ""
            print(f"{title}: {value}{delta_str}")
            return None
        
        # Create card HTML
        delta_html = ""
        if delta is not None:
            delta_color = "#4caf50" if delta > 0 else "#f44336"
            delta_html = f"<div style='font-size: 0.8rem; color: {delta_color};'>{delta:+.2f}</div>"
        
        html = f"""
        <div style='
            padding: 15px;
            margin: 5px;
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: inline-block;
            min-width: 150px;
        '>
            <div style='color: {color}; font-weight: bold; font-size: 1.2rem;'>{value}</div>
            <div style='color: #666; font-size: 0.9rem;'>{title}</div>
            {delta_html}
        </div>
        """
        
        if section:
            display_in_section(section, html, clear_first=False)
        else:
            display(HTML(html))
    
    @staticmethod
    def chip(text: str, color: str = "#263238", section: Optional[str] = None):
        """
        Display chip/badge with optional section management.
        
        Args:
            text: Chip text
            color: Chip color
            section: Optional section name for grouping
        """
        if not should_display_widgets():
            print(f"[{text}]")
            return None
        
        html = f"""
        <span style='
            background: {color};
            color: white;
            padding: 4px 12px;
            border-radius: 16px;
            margin-right: 6px;
            font-size: 0.8rem;
            display: inline-block;
        '>{text}</span>
        """
        
        if section:
            display_in_section(section, html, clear_first=False)
        else:
            display(HTML(html))
    
    @staticmethod
    def alert(message: str, level: str = "info", section: Optional[str] = None):
        """
        Display alert notification with optional section management.
        
        Args:
            message: Alert message
            level: Alert level (info, success, warning, error)
            section: Optional section name for grouping
        """
        if not should_display_widgets():
            level_symbols = {
                "info": "ℹ️",
                "success": "✅", 
                "warning": "⚠️",
                "error": "❌"
            }
            print(f"{level_symbols.get(level, 'ℹ️')} {message}")
            return None
        
        level_colors = {
            "info": "#2196f3",
            "success": "#4caf50",
            "warning": "#ff9800", 
            "error": "#f44336"
        }
        
        html = f"""
        <div style='
            padding: 10px 15px;
            border-radius: 4px;
            background: {level_colors.get(level, "#2196f3")}22;
            border-left: 4px solid {level_colors.get(level, "#2196f3")};
            margin: 10px 0;
        '>{message}</div>
        """
        
        if section:
            display_in_section(section, html, clear_first=False)
        else:
            display(HTML(html))
    
    @staticmethod
    def enhanced_dataframe(df: pd.DataFrame, highlight_cols: Optional[List[str]] = None, 
                          title: Optional[str] = None, section: Optional[str] = None):
        """
        Enhanced DataFrame display with optional section management.
        
        Args:
            df: DataFrame to display
            highlight_cols: Columns to highlight with gradient
            title: Optional title
            section: Optional section name for automatic clearing
        """
        def _display_content():
            if title:
                if should_display_widgets():
                    display(HTML(f"<h4>{title}</h4>"))
                else:
                    print(f"\n{title}")
            
            if not should_display_widgets():
                print(df.to_string())
                return None
            
            # Apply styling
            styled = df.style.set_table_styles([
                {'selector': 'thead th', 'props': [
                    ('background-color', '#f5f5f5'),
                    ('color', '#333'),
                    ('font-weight', 'bold')
                ]}
            ])
            
            if highlight_cols:
                for col in highlight_cols:
                    if col in df.columns:
                        styled = styled.background_gradient(subset=[col], cmap='Reds')
            
            return display(styled)
        
        if section:
            with get_display_manager().section(section, auto_clear=True):
                _display_content()
        else:
            _display_content()
    
    @staticmethod
    @display_section("card_group")
    def card_group(cards: List[Dict[str, Any]], section: str = "card_group"):
        """
        Display a group of cards with automatic section clearing.
        
        Args:
            cards: List of card dictionaries with title, value, delta, color
            section: Section name for grouping (default: "card_group")
        """
        display(HTML("<div style='display: flex; gap: 10px; margin: 20px 0;'>"))
        for card in cards:
            EnhancedRichDisplay.card(
                title=card.get('title', ''),
                value=card.get('value', ''),
                delta=card.get('delta'),
                color=card.get('color', '#1f77b4'),
                section=None  # Don't create nested sections
            )
        display(HTML("</div>"))
    
    @staticmethod
    @display_section("chip_group")
    def chip_group(chips: List[Dict[str, Any]], section: str = "chip_group"):
        """
        Display a group of chips with automatic section clearing.
        
        Args:
            chips: List of chip dictionaries with text and color
            section: Section name for grouping (default: "chip_group")
        """
        for chip in chips:
            EnhancedRichDisplay.chip(
                text=chip.get('text', ''),
                color=chip.get('color', '#263238'),
                section=None  # Don't create nested sections
            )

# Backward compatibility - provide original RichDisplay interface
class RichDisplay(EnhancedRichDisplay):
    """Backward compatible RichDisplay class with enhanced capabilities"""
    pass

# Section-aware display functions for common patterns
@display_section("query_history")
def display_query_history(history_data: List[Dict[str, Any]]):
    """Display query history with automatic section clearing"""
    if not history_data:
        RichDisplay.alert("No query history available", "info")
        return
    
    df = pd.DataFrame(history_data)
    RichDisplay.enhanced_dataframe(df, title="📋 Query History")

@display_section("ticker_intelligence")
def display_ticker_intelligence_section(ticker: str, bundle: Dict[str, Any]):
    """Display ticker intelligence with automatic section clearing"""
    # Header with ticker info
    display(HTML(f"<h2>{ticker} — {bundle['meta']['name']} · {bundle['meta']['sector']}</h2>"))
    display(HTML(f"<p><strong>TL;DR:</strong> {bundle['tldr']}</p>"))
    
    # Metrics cards
    cards = [
        {"title": "Priority", "value": bundle['priority']},
        {"title": "Recency", "value": f"{bundle['recency_hours']}h"},
        {"title": "Confidence", "value": f"{bundle['confidence']:.2f}"}
    ]
    RichDisplay.card_group(cards)
    
    # Themes as chips
    if bundle.get('themes'):
        display(HTML("<h4>🏷️ Themes</h4>"))
        theme_chips = [
            {"text": f"{theme['name']} • {theme['confidence']:.2f}", "color": "#263238"}
            for theme in bundle['themes']
        ]
        RichDisplay.chip_group(theme_chips)

@display_section("portfolio_summary")
def display_portfolio_section(portfolio_data: List[Dict[str, Any]]):
    """Display portfolio summary with automatic section clearing"""
    if not portfolio_data:
        RichDisplay.alert("No portfolio data available", "info")
        return
    
    df = pd.DataFrame(portfolio_data)
    RichDisplay.enhanced_dataframe(
        df, 
        highlight_cols=['Alert Priority'],
        title="📈 Portfolio Summary"
    )

# Export main components
__all__ = [
    'EnhancedRichDisplay',
    'RichDisplay',
    'display_query_history',
    'display_ticker_intelligence_section', 
    'display_portfolio_section'
]