# notebook_repetition_fix.py
# Comprehensive fix for ice_development.ipynb repeated output issues
# Addresses event handler accumulation and widget state management
# Provides targeted patches for problematic notebook cells

"""
ICE Development Notebook - Repetition Fix

This file contains the targeted fixes for the repeated output issues in 
ice_development.ipynb. The root cause is event handler accumulation when 
notebook cells are re-executed.

PROBLEM: Each cell re-execution registers new event handlers without removing 
old ones, causing multiple callbacks for single user actions.

SOLUTION: Use notebook_widget_manager to prevent handler re-registration
while maintaining all existing functionality.

Apply these patches to the corresponding cells in ice_development.ipynb
"""

# =============================================================================
# PATCH 1: RAG Engine Selection (Cell ~14)
# Lines 465-466: engine_selector.observe + comparison_button.on_click
# =============================================================================

patch_1_rag_engine_selection = """
# FIXED: RAG Engine Selection - Prevent handler accumulation
from notebook_widget_manager import register_observe_once, register_click_once

# Replace these lines:
# engine_selector.observe(on_engine_change, names='value')  
# comparison_button.on_click(on_comparison_click)

# With these fixed versions:
register_observe_once(engine_selector, on_engine_change, 'rag_engine_selector')
register_click_once(comparison_button, on_comparison_click, 'rag_comparison_button')
"""

# =============================================================================
# PATCH 2: Query Interface (Cell ~28) 
# Line 1200: query_button.on_click(on_query_submit) - ALREADY PARTIALLY FIXED
# =============================================================================

patch_2_query_interface = """
# FIXED: Query Interface - Prevent handler accumulation  
from notebook_widget_manager import register_click_once

# Replace this line:
# query_button.on_click(on_query_submit)

# With this fixed version:
register_click_once(query_button, on_query_submit, 'main_query_button')
"""

# =============================================================================
# PATCH 3: History Interface (Cell ~29)
# Line 1282: history_button.on_click(on_history_click)
# =============================================================================

patch_3_history_interface = """
# FIXED: History Interface - Prevent handler accumulation
from notebook_widget_manager import register_click_once

# Replace this line:
# history_button.on_click(on_history_click)

# With this fixed version:
register_click_once(history_button, on_history_click, 'history_button')
"""

# =============================================================================
# PATCH 4: Ticker Analysis Interface (Cell ~31)
# Line 1447: ticker_dropdown.observe(on_ticker_change, names='value')
# =============================================================================

patch_4_ticker_interface = """
# FIXED: Ticker Analysis - Prevent handler accumulation
from notebook_widget_manager import register_observe_once

# Replace this line:
# ticker_dropdown.observe(on_ticker_change, names='value')

# With this fixed version:
register_observe_once(ticker_dropdown, on_ticker_change, 'ticker_dropdown')
"""

# =============================================================================
# PATCH 5: Graph Visualization (Cell ~38)
# Lines 1732-1737: Multiple graph widget observers
# =============================================================================

patch_5_graph_visualization = """
# FIXED: Graph Visualization - Prevent handler accumulation
from notebook_widget_manager import register_observe_once

# Replace these lines:
# center_node_dropdown.observe(on_graph_update, names='value')
# hop_depth_slider.observe(on_graph_update, names='value')  
# confidence_slider.observe(on_graph_update, names='value')
# recency_slider.observe(on_graph_update, names='value')
# edge_types_select.observe(on_graph_update, names='value')
# contrarian_checkbox.observe(on_graph_update, names='value')

# With these fixed versions:
register_observe_once(center_node_dropdown, on_graph_update, 'center_node_dropdown')
register_observe_once(hop_depth_slider, on_graph_update, 'hop_depth_slider')
register_observe_once(confidence_slider, on_graph_update, 'confidence_slider') 
register_observe_once(recency_slider, on_graph_update, 'recency_slider')
register_observe_once(edge_types_select, on_graph_update, 'edge_types_select')
register_observe_once(contrarian_checkbox, on_graph_update, 'contrarian_checkbox')
"""

# =============================================================================
# PATCH 6: Portfolio Management (Cell ~41)
# Lines 1934-1936: Filter observers and export button
# =============================================================================

patch_6_portfolio_management = """
# FIXED: Portfolio Management - Prevent handler accumulation
from notebook_widget_manager import register_observe_once, register_click_once

# Replace these lines:
# priority_filter.observe(on_filter_change, names='value')
# sector_filter.observe(on_filter_change, names='value') 
# export_button.on_click(on_export_click)

# With these fixed versions:
register_observe_once(priority_filter, on_filter_change, 'priority_filter')
register_observe_once(sector_filter, on_filter_change, 'sector_filter')
register_click_once(export_button, on_export_click, 'portfolio_export_button')
"""

# =============================================================================
# PATCH 7: Analytics Interface (Cell ~44)
# Line 2059: analytics_button.on_click(on_analytics_click)
# =============================================================================

patch_7_analytics_interface = """
# FIXED: Analytics Interface - Prevent handler accumulation
from notebook_widget_manager import register_click_once

# Replace this line:
# analytics_button.on_click(on_analytics_click)

# With this fixed version:
register_click_once(analytics_button, on_analytics_click, 'analytics_button')
"""

# =============================================================================
# PATCH 8: Test Interface (Cell ~49)
# Line 2450: test_button.on_click(on_test_click)
# =============================================================================

patch_8_test_interface = """
# FIXED: Test Interface - Prevent handler accumulation
from notebook_widget_manager import register_click_once

# Replace this line:
# test_button.on_click(on_test_click)

# With this fixed version:
register_click_once(test_button, on_test_click, 'test_button')
"""

# =============================================================================
# PATCH 9: Profiling Interface (Cell ~52)
# Lines 2620-2621: Profile and benchmark buttons
# =============================================================================

patch_9_profiling_interface = """
# FIXED: Profiling Interface - Prevent handler accumulation
from notebook_widget_manager import register_click_once

# Replace these lines:
# profile_button.on_click(on_profile_click)
# benchmark_button.on_click(on_benchmark_click)

# With these fixed versions:
register_click_once(profile_button, on_profile_click, 'profile_button')
register_click_once(benchmark_button, on_benchmark_click, 'benchmark_button')
"""

# =============================================================================
# PATCH 10: Graph Analysis Interface (Cell ~55)
# Line 2760: graph_analysis_button.on_click(on_graph_analysis_click)
# =============================================================================

patch_10_graph_analysis = """
# FIXED: Graph Analysis - Prevent handler accumulation
from notebook_widget_manager import register_click_once

# Replace this line:
# graph_analysis_button.on_click(on_graph_analysis_click)

# With this fixed version:
register_click_once(graph_analysis_button, on_graph_analysis_click, 'graph_analysis_button')
"""

# =============================================================================
# PATCH 11: Export Interface (Cell ~58)
# Lines 2958-2959: Export and report buttons
# =============================================================================

patch_11_export_interface = """
# FIXED: Export Interface - Prevent handler accumulation  
from notebook_widget_manager import register_click_once

# Replace these lines:
# export_button.on_click(on_export_click)
# report_button.on_click(on_report_click)

# With these fixed versions:
register_click_once(export_button, on_export_click, 'main_export_button')
register_click_once(report_button, on_report_click, 'report_button')
"""

# =============================================================================
# PATCH 12: Demo Interface (Cell ~67) 
# Line 3608: demo_button.on_click(on_demo_click)
# =============================================================================

patch_12_demo_interface = """
# FIXED: Demo Interface - Prevent handler accumulation
from notebook_widget_manager import register_click_once

# Replace this line:
# demo_button.on_click(on_demo_click)

# With this fixed version:
register_click_once(demo_button, on_demo_click, 'demo_button')
"""

# =============================================================================
# INITIALIZATION PATCH: Add to imports cell (Cell ~2)
# =============================================================================

initialization_patch = """
# REPETITION FIX: Add this import to the main imports cell
from notebook_widget_manager import (
    register_click_once, 
    register_observe_once, 
    guard_cell, 
    manager_stats,
    debug_handlers
)

# Optional: Debug manager status
print("🔧 Widget Manager loaded - preventing handler accumulation")
"""

# =============================================================================
# VERIFICATION PATCH: Add debug cell at end
# =============================================================================

verification_patch = """
# VERIFICATION: Add this as a new cell to verify the fix works
from notebook_widget_manager import manager_stats, debug_handlers

print("🔍 Widget Manager Verification")
print("=" * 50)

stats = manager_stats()
print(f"✅ Handlers registered: {stats['registered_handlers']}")
print(f"✅ Widgets managed: {stats['registered_widgets']}")
print(f"✅ Execution guards: {stats['execution_guards']}")

if stats['registered_handlers'] > 0:
    print("\\n📋 Active Handlers:")
    debug_handlers()
else:
    print("⚠️ No handlers registered yet - run cells with widgets first")

print("\\n🎯 Fix Status: Repetition prevention ACTIVE")
"""

# =============================================================================
# SUMMARY AND INSTRUCTIONS
# =============================================================================

def apply_fix_instructions():
    """Instructions for applying the repetition fix"""
    instructions = """
    🔧 ICE DEVELOPMENT NOTEBOOK - REPETITION FIX INSTRUCTIONS
    ========================================================
    
    PROBLEM: Repeated output instances when cells are re-executed
    ROOT CAUSE: Event handler accumulation on widget re-creation
    SOLUTION: Use notebook_widget_manager to prevent re-registration
    
    STEP 1: Add the initialization patch to your imports cell (Cell ~2)
    -------
    Add this import after the existing imports:
    
    from notebook_widget_manager import (
        register_click_once, 
        register_observe_once, 
        guard_cell, 
        manager_stats
    )
    
    STEP 2: Apply patches to cells with event handlers
    -------
    Find and replace the following patterns in your notebook:
    
    OLD: button.on_click(handler)
    NEW: register_click_once(button, handler, 'unique_key')
    
    OLD: widget.observe(handler, names='value')
    NEW: register_observe_once(widget, handler, 'unique_key')
    
    STEP 3: Specific cell updates
    -------
    Apply the patches from this file to their corresponding cells.
    Each patch is clearly labeled with the cell number and line numbers.
    
    STEP 4: Add verification cell
    -------
    Add the verification_patch as a new cell at the end of your notebook
    to monitor the fix effectiveness.
    
    STEP 5: Test the fix
    -------
    1. Restart kernel and clear all outputs
    2. Run all cells
    3. Try interacting with widgets - should see single responses
    4. Re-run cells with widgets - should not accumulate handlers
    5. Check verification cell for handler count
    
    RESULT: Clean, single-response widget interactions without repetition
    """
    return instructions

if __name__ == "__main__":
    print(apply_fix_instructions())