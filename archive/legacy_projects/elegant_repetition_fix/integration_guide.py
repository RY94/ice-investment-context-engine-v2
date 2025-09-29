#!/usr/bin/env python3
# elegant_repetition_fix/integration_guide.py
# Complete integration guide and examples for elegant repetition fix
# Shows how to integrate the enhanced components into existing ICE notebook
# Provides specific solutions for patterns identified in user screenshots

"""
Integration Guide - Elegant Repetition Fix for ICE Development Notebook

This guide provides complete examples and integration patterns for implementing
the elegant repetition fix in the ICE development notebook. It addresses the
specific repetition patterns identified in the user's screenshots.

Integration Strategy:
1. Import enhanced components alongside existing modules
2. Add section decorators to problematic display functions  
3. Use context managers for grouped displays
4. Maintain backward compatibility with existing code

Specific Fixes:
- Query History repetition (identical timestamps)
- Per-Ticker Intelligence repetition (NVDA entries)
- Theme repetition (China Risk, AI Infrastructure chips)  
- Knowledge Graph repetition (duplicate visualizations)
"""

# Example integration patterns for ICE development notebook

# =============================================================================
# STEP 1: Import Enhanced Components (Add to notebook imports section)
# =============================================================================

"""
# Add these imports to the beginning of ice_development.ipynb
from elegant_repetition_fix.enhanced_output_manager import (
    get_display_manager, 
    display_section, 
    section_guard,
    display_in_section
)
from elegant_repetition_fix.enhanced_rich_display import (
    RichDisplay,  # Drop-in replacement
    display_query_history,
    display_ticker_intelligence_section,
    display_portfolio_section
)

# Initialize display manager
display_manager = get_display_manager()
print("✅ Elegant repetition fix loaded - section-based display management enabled")
"""

# =============================================================================
# STEP 2: Fix Query History Repetition
# =============================================================================

@section_guard("query_history")  
def show_query_history_fixed():
    """
    Fixed version of show_query_history() function.
    Automatically clears previous history display before showing new content.
    
    This addresses the repeated timestamp issue seen in the screenshots.
    """
    # Get query history from ICE system
    if not hasattr(ice, 'query_history') or not ice.query_history:
        RichDisplay.alert("No query history available", "info")
        return
    
    # Convert to DataFrame format
    history_df = pd.DataFrame([
        {
            'Timestamp': record.timestamp,
            'Question': record.question,
            'Mode': record.mode,
            'Success': record.success,
            'Query Time': f"{record.query_time:.3f}s"
        } for record in ice.query_history
    ])
    
    # Display with automatic clearing (section decorator handles this)
    RichDisplay.enhanced_dataframe(history_df, title="📋 Query History")

# =============================================================================
# STEP 3: Fix Per-Ticker Intelligence Repetition  
# =============================================================================

@section_guard("ticker_intelligence")
def display_ticker_intelligence_fixed(ticker):
    """
    Fixed version of display_ticker_intelligence() function.
    Automatically clears previous ticker display before showing new content.
    
    This addresses the repeated "NVDA — NVIDIA • Semis" entries.
    """
    if ticker not in TICKER_BUNDLE:
        RichDisplay.alert(f"No data available for {ticker}", "warning")
        return
    
    bundle = TICKER_BUNDLE[ticker]
    
    # All content within this function will be in the same section
    # and will automatically clear on re-execution
    
    # Header with ticker info
    display(HTML(f"<h2>{ticker} — {bundle['meta']['name']} · {bundle['meta']['sector']}</h2>"))
    display(HTML(f"<p><strong>TL;DR:</strong> {bundle['tldr']}</p>"))
    
    # Metrics cards (grouped to prevent individual accumulation)
    with display_manager.section("ticker_metrics", auto_clear=False):
        display(HTML("<div style='display: flex; gap: 10px; margin: 20px 0;'>"))
        RichDisplay.card("Priority", bundle['priority'])
        RichDisplay.card("Recency", f"{bundle['recency_hours']}h")
        RichDisplay.card("Confidence", f"{bundle['confidence']:.2f}")
        display(HTML("</div>"))
    
    # Themes section (addresses repeated "China Risk • 0.87" chips)
    with display_manager.section("ticker_themes", auto_clear=False):
        display(HTML("<h4>🏷️ Themes</h4>"))
        for theme in bundle['themes']:
            RichDisplay.chip(f"{theme['name']} • {theme['confidence']:.2f}")
    
    # KPIs, paths, and other sections follow similar pattern
    # Each logical group gets its own subsection to prevent accumulation

# =============================================================================
# STEP 4: Fix Knowledge Graph Repetition
# =============================================================================

@section_guard("knowledge_graph")
def display_knowledge_graph_fixed(center_node, max_hops=2, min_confidence=0.6, edge_types=None):
    """
    Fixed version of knowledge graph display.
    Automatically clears previous graph before showing new visualization.
    
    This addresses the duplicate knowledge graph visualizations.
    """
    try:
        # Build graph from edge records
        G = nx.Graph()
        
        # Add edges based on filtering criteria
        for source, target, edge_type, weight, days_ago, is_positive in EDGE_RECORDS:
            if edge_types and edge_type not in edge_types:
                continue
            if weight < min_confidence:
                continue
                
            G.add_edge(source, target, 
                      edge_type=edge_type, 
                      weight=weight,
                      days_ago=days_ago,
                      is_positive=is_positive)
        
        # Get subgraph around center node
        if center_node in G:
            if max_hops == 1:
                subgraph_nodes = [center_node] + list(G.neighbors(center_node))
            else:
                subgraph_nodes = []
                visited = {center_node}
                current_level = {center_node}
                
                for hop in range(max_hops):
                    next_level = set()
                    for node in current_level:
                        subgraph_nodes.append(node)
                        for neighbor in G.neighbors(node):
                            if neighbor not in visited:
                                next_level.add(neighbor)
                                visited.add(neighbor)
                    current_level = next_level
                
                subgraph_nodes.extend(current_level)
            
            subgraph = G.subgraph(subgraph_nodes)
        else:
            subgraph = G
        
        # Create visualization (this content will auto-clear due to section decorator)
        display(HTML(f"<h3>ICE Knowledge Graph - {center_node} ({max_hops} hops)</h3>"))
        
        # Create pyvis network
        net = Network(height="400px", width="100%", bgcolor="#f8f9fa")
        
        # Add nodes and edges with proper styling
        edge_colors = {
            'depends_on': '#e74c3c',
            'sells_to': '#2ecc71', 
            'manufactures_in': '#f39c12',
            'serves': '#3498db'
        }
        
        for node in subgraph.nodes():
            net.add_node(node, label=node, color='#34495e')
        
        for source, target, data in subgraph.edges(data=True):
            color = edge_colors.get(data.get('edge_type', 'unknown'), '#95a5a6')
            net.add_edge(source, target, color=color, title=data.get('edge_type', ''))
        
        # Generate HTML and display
        net.set_options("""
        var options = {
          "physics": {"enabled": true, "barnesHut": {"gravitationalConstant": -2000}},
          "edges": {"smooth": false}
        }
        """)
        
        html_content = net.generate_html()
        display(HTML(html_content))
        
        # Show graph stats
        display(HTML(f"<p><small>Nodes: {len(subgraph.nodes())}, Edges: {len(subgraph.edges())}</small></p>"))
        
    except Exception as e:
        RichDisplay.alert(f"Error generating knowledge graph: {str(e)}", "error")

# =============================================================================
# STEP 5: Portfolio and Watchlist Fix
# =============================================================================

@section_guard("portfolio_view")
def display_portfolio_fixed(portfolio_data, priority_threshold=70):
    """
    Fixed portfolio display with automatic section clearing.
    """
    if not portfolio_data:
        RichDisplay.alert("No portfolio data available", "info")
        return
    
    # Filter by priority if specified
    if priority_threshold:
        filtered_data = [row for row in portfolio_data if row.get('Alert Priority', 0) >= priority_threshold]
    else:
        filtered_data = portfolio_data
    
    if filtered_data:
        df = pd.DataFrame(filtered_data)
        RichDisplay.enhanced_dataframe(
            df,
            highlight_cols=['Alert Priority'],
            title="📈 Portfolio Summary"
        )
    else:
        RichDisplay.alert(f"No portfolio items above priority {priority_threshold}", "info")

# =============================================================================
# STEP 6: Integration Helper Functions
# =============================================================================

def apply_repetition_fix_to_notebook():
    """
    Helper function to apply repetition fix to common notebook functions.
    
    Call this after importing the enhanced components to replace
    problematic functions with fixed versions.
    """
    # Replace global functions with fixed versions
    globals()['show_query_history'] = show_query_history_fixed
    globals()['display_ticker_intelligence'] = display_ticker_intelligence_fixed
    globals()['display_knowledge_graph'] = display_knowledge_graph_fixed
    globals()['display_portfolio'] = display_portfolio_fixed
    
    print("✅ Repetition fix applied to notebook functions")
    print("📊 Display sections will now auto-clear on cell re-execution")

def test_repetition_fix():
    """
    Test function to verify the repetition fix is working correctly.
    
    This function should be able to run multiple times without
    creating duplicate outputs.
    """
    print("🧪 Testing repetition fix...")
    
    # Test 1: Section-based display
    with display_manager.section("test_section"):
        display(HTML("<h4>Test Section Display</h4>"))
        display(HTML("<p>This content should replace itself on re-execution</p>"))
    
    # Test 2: Decorator-based display
    @section_guard("test_decorator")
    def test_display():
        display(HTML("<h4>Decorator Test</h4>"))
        display(HTML("<p>This should also auto-clear</p>"))
    
    test_display()
    
    # Test 3: RichDisplay components
    with display_manager.section("test_components"):
        RichDisplay.card("Test Metric", "42", delta=2.5)
        RichDisplay.chip("Test Chip", "#4caf50")
        RichDisplay.alert("Test alert message", "success")
    
    print("✅ Repetition fix test completed")
    print("📋 Check above - content should replace itself on re-execution")

def get_fix_status():
    """Get status of the repetition fix system"""
    stats = display_manager.get_stats()
    
    status_info = f"""
🔧 REPETITION FIX STATUS
========================
Total Sections: {stats['total_sections']}
Active Sections: {stats['active_sections']}  
Section Names: {', '.join(stats['section_names']) if stats['section_names'] else 'None'}
Active Now: {', '.join(stats['active_section_names']) if stats['active_section_names'] else 'None'}
Execution Guards: {stats['execution_guards']}

✅ System Status: {'Active' if stats['total_sections'] > 0 else 'Inactive'}
"""
    
    print(status_info)
    return stats

# =============================================================================
# STEP 7: Widget Handler Integration (Leverage Existing Fix)
# =============================================================================

def integrate_with_existing_widget_manager():
    """
    Integration helper to work with existing notebook_widget_manager.py
    
    The existing widget manager already handles event handler accumulation.
    This function ensures compatibility between the two systems.
    """
    try:
        from notebook_widget_manager import register_click_once, register_observe_once, manager_stats
        
        # Create enhanced click handler that also uses section clearing
        def enhanced_click_handler(widget, handler, handler_key, section_name=None):
            """Enhanced click handler with optional section clearing"""
            
            def section_aware_handler(*args, **kwargs):
                if section_name:
                    with display_manager.section(section_name):
                        return handler(*args, **kwargs)
                else:
                    return handler(*args, **kwargs)
            
            return register_click_once(widget, section_aware_handler, handler_key)
        
        # Add to global namespace
        globals()['register_click_with_section'] = enhanced_click_handler
        
        print("✅ Enhanced widget handler integration ready")
        print("💡 Use register_click_with_section() for handlers that need display clearing")
        
    except ImportError:
        print("⚠️ Existing notebook_widget_manager not found")
        print("💡 Enhanced display manager can work independently")

# =============================================================================
# STEP 8: Quick Setup Function
# =============================================================================

def setup_elegant_repetition_fix():
    """
    One-line setup function to initialize all components.
    
    Add this to the top of your notebook after imports:
    setup_elegant_repetition_fix()
    """
    # Apply function replacements
    apply_repetition_fix_to_notebook()
    
    # Integrate with existing systems
    integrate_with_existing_widget_manager()
    
    # Show system status
    print("\n🎉 ELEGANT REPETITION FIX SETUP COMPLETE")
    print("=" * 50)
    get_fix_status()
    
    print("\n📋 USAGE EXAMPLES:")
    print("- @section_guard('my_section') - Auto-clear decorator")
    print("- with display_manager.section('name'): - Context manager") 
    print("- RichDisplay.card() - Enhanced display components")
    print("- test_repetition_fix() - Test the fix")
    
    return display_manager

# Export all components
__all__ = [
    'show_query_history_fixed',
    'display_ticker_intelligence_fixed', 
    'display_knowledge_graph_fixed',
    'display_portfolio_fixed',
    'apply_repetition_fix_to_notebook',
    'test_repetition_fix',
    'get_fix_status',
    'setup_elegant_repetition_fix'
]