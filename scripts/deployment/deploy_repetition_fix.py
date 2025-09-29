#!/usr/bin/env python3
# deploy_repetition_fix.py
# Deployment script for elegant repetition fix integration
# Safely integrates the fix into existing ICE development notebook
# Preserves all existing functionality while preventing repetition

"""
Deployment Script - Elegant Repetition Fix Integration

This script deploys the elegant repetition fix to the existing ICE development
notebook by safely integrating the enhanced components while preserving all
existing functionality.

Deployment Strategy:
1. Import enhanced components alongside existing modules
2. Replace RichDisplay class with enhanced version (drop-in replacement)
3. Add section decorators to problematic display functions
4. Integrate with existing widget manager system
5. Test integration and verify fix works

Usage:
    # In notebook cell, run:
    exec(open('deploy_repetition_fix.py').read())
"""

import sys
import os

def deploy_elegant_repetition_fix():
    """
    Main deployment function to integrate elegant repetition fix.
    
    This function safely deploys all components while maintaining
    backward compatibility with existing notebook code.
    """
    print("🚀 DEPLOYING ELEGANT REPETITION FIX")
    print("=" * 50)
    
    try:
        # Step 1: Import enhanced components
        print("📦 Step 1: Importing enhanced components...")
        
        # Add elegant_repetition_fix to path if not already there
        fix_path = os.path.join(os.getcwd(), 'elegant_repetition_fix')
        if fix_path not in sys.path:
            sys.path.insert(0, fix_path)
        
        # Import core components
        from enhanced_output_manager import (
            DisplaySectionManager, get_display_manager, 
            display_section, section_guard, display_in_section
        )
        
        from enhanced_rich_display import (
            RichDisplay as EnhancedRichDisplay,
            display_query_history,
            display_ticker_intelligence_section,
            display_portfolio_section
        )
        
        print("✅ Enhanced components imported successfully")
        
        # Step 2: Initialize display manager
        print("🔧 Step 2: Initializing display manager...")
        display_manager = get_display_manager()
        print(f"✅ Display manager initialized - {display_manager.get_stats()['total_sections']} sections ready")
        
        # Step 3: Replace existing RichDisplay with enhanced version
        print("🔄 Step 3: Upgrading RichDisplay class...")
        
        # Store reference to enhanced version globally
        globals()['OriginalRichDisplay'] = globals().get('RichDisplay', None)
        globals()['RichDisplay'] = EnhancedRichDisplay
        globals()['display_manager'] = display_manager
        
        print("✅ RichDisplay upgraded to enhanced version (backward compatible)")
        
        # Step 4: Create section-aware wrapper functions for problematic patterns
        print("🎯 Step 4: Creating section-aware display functions...")
        
        @section_guard("query_history_section")
        def show_query_history_fixed():
            """Fixed query history display with automatic section clearing"""
            if not hasattr(ice, 'query_history') or not ice.query_history:
                RichDisplay.alert("No query history available", "info")
                return
            
            # Convert query history to DataFrame
            history_data = []
            for record in ice.query_history:
                history_data.append({
                    'Timestamp': getattr(record, 'timestamp', 'N/A'),
                    'Question': getattr(record, 'question', 'N/A'),  
                    'Mode': getattr(record, 'mode', 'N/A'),
                    'Success': getattr(record, 'success', True),
                    'Query Time': f"{getattr(record, 'query_time', 0):.3f}s"
                })
            
            import pandas as pd
            history_df = pd.DataFrame(history_data)
            RichDisplay.enhanced_dataframe(history_df, title="📋 Query History")
        
        @section_guard("ticker_intelligence_section")
        def display_ticker_intelligence_fixed(ticker):
            """Fixed ticker intelligence display with automatic section clearing"""
            if ticker not in globals().get('TICKER_BUNDLE', {}):
                RichDisplay.alert(f"No data available for {ticker}", "warning")
                return
                
            bundle = TICKER_BUNDLE[ticker]
            
            # Header with ticker info (will auto-clear due to section decorator)
            from IPython.display import display, HTML
            display(HTML(f"<h2>{ticker} — {bundle['meta']['name']} · {bundle['meta']['sector']}</h2>"))
            display(HTML(f"<p><strong>TL;DR:</strong> {bundle['tldr']}</p>"))
            
            # Metrics row with section grouping
            with display_manager.section("ticker_metrics", auto_clear=False):
                display(HTML("<div style='display: flex; gap: 10px; margin: 20px 0;'>"))
                RichDisplay.card("Priority", bundle['priority'])
                RichDisplay.card("Recency", f"{bundle['recency_hours']}h")
                RichDisplay.card("Confidence", f"{bundle['confidence']:.2f}")
                display(HTML("</div>"))
            
            # Themes section (fixes repeated chip issue)
            with display_manager.section("ticker_themes", auto_clear=False):
                display(HTML("<h4>🏷️ Themes</h4>"))
                for theme in bundle['themes']:
                    RichDisplay.chip(f"{theme['name']} • {theme['confidence']:.2f}")
            
            # KPIs section
            with display_manager.section("ticker_kpis", auto_clear=False):
                display(HTML("<h4>📈 KPI Watchlist</h4>"))
                for kpi in bundle['kpis']:
                    display(HTML(f"""
                    <div style='margin: 10px 0; padding: 10px; border-left: 3px solid #2196f3; background: #f5f5f5;'>
                        <strong>{kpi['name']}</strong><br>
                        <small>Evidence: {kpi['evidence_count']} sources</small>
                    </div>
                    """))
        
        @section_guard("portfolio_display_section") 
        def display_portfolio_fixed(portfolio_data, priority_threshold=70):
            """Fixed portfolio display with automatic section clearing"""
            if not portfolio_data:
                RichDisplay.alert("No portfolio data available", "info")
                return
            
            # Filter by priority if specified
            if priority_threshold:
                filtered_data = [row for row in portfolio_data 
                               if row.get('Alert Priority', 0) >= priority_threshold]
            else:
                filtered_data = portfolio_data
            
            if filtered_data:
                import pandas as pd
                df = pd.DataFrame(filtered_data)
                RichDisplay.enhanced_dataframe(
                    df,
                    highlight_cols=['Alert Priority'],
                    title="📈 Portfolio Summary"
                )
            else:
                RichDisplay.alert(f"No portfolio items above priority {priority_threshold}", "info")
        
        # Store fixed functions globally
        globals()['show_query_history_fixed'] = show_query_history_fixed
        globals()['display_ticker_intelligence_fixed'] = display_ticker_intelligence_fixed
        globals()['display_portfolio_fixed'] = display_portfolio_fixed
        
        print("✅ Section-aware display functions created")
        
        # Step 5: Create enhanced widget integration
        print("🔗 Step 5: Integrating with existing widget manager...")
        
        def register_click_with_section(widget, handler, handler_key, section_name=None):
            """Enhanced click handler with optional section clearing"""
            try:
                from notebook_widget_manager import register_click_once
                
                def section_aware_handler(*args, **kwargs):
                    if section_name:
                        with display_manager.section(section_name):
                            return handler(*args, **kwargs)
                    else:
                        return handler(*args, **kwargs)
                
                return register_click_once(widget, section_aware_handler, handler_key)
            except ImportError:
                # Fallback if notebook_widget_manager not available
                widget.on_click(handler)
                return True
        
        globals()['register_click_with_section'] = register_click_with_section
        print("✅ Enhanced widget integration ready")
        
        # Step 6: Provide utility functions
        print("🛠️ Step 6: Setting up utility functions...")
        
        def test_repetition_fix():
            """Test function to verify the fix works"""
            print("🧪 Testing repetition fix...")
            
            with display_manager.section("test_section"):
                RichDisplay.alert("Test: This content should replace itself on re-execution", "info")
                RichDisplay.card("Test Metric", "42")
                RichDisplay.chip("Test Chip")
            
            print("✅ Test complete - content should auto-clear on re-execution")
        
        def get_fix_status():
            """Get status of the repetition fix system"""
            stats = display_manager.get_stats()
            print(f"""
🔧 REPETITION FIX STATUS
========================
Total Sections: {stats['total_sections']}
Active Sections: {stats['active_sections']}
Section Names: {', '.join(stats['section_names']) if stats['section_names'] else 'None'}
Active Now: {', '.join(stats['active_section_names']) if stats['active_section_names'] else 'None'}
            """)
            return stats
        
        def apply_fix_to_existing_functions():
            """Replace existing problematic functions with fixed versions"""
            # Replace existing functions if they exist
            if 'show_query_history' in globals():
                globals()['show_query_history_original'] = globals()['show_query_history']
                globals()['show_query_history'] = show_query_history_fixed
                print("✅ show_query_history replaced with fixed version")
            
            if 'display_ticker_intelligence' in globals():
                globals()['display_ticker_intelligence_original'] = globals()['display_ticker_intelligence']
                globals()['display_ticker_intelligence'] = display_ticker_intelligence_fixed
                print("✅ display_ticker_intelligence replaced with fixed version")
            
            print("🔄 Existing functions upgraded with repetition fix")
        
        globals()['test_repetition_fix'] = test_repetition_fix
        globals()['get_fix_status'] = get_fix_status
        globals()['apply_fix_to_existing_functions'] = apply_fix_to_existing_functions
        
        print("✅ Utility functions ready")
        
        # Step 7: Integration complete
        print("\n🎉 DEPLOYMENT COMPLETE!")
        print("=" * 30)
        print("✅ Enhanced components integrated")
        print("✅ RichDisplay upgraded (backward compatible)")
        print("✅ Section-aware functions ready")
        print("✅ Widget integration enhanced")
        print("✅ Utility functions available")
        
        print("\n📋 AVAILABLE FUNCTIONS:")
        print("• test_repetition_fix() - Test the fix")
        print("• get_fix_status() - Check system status")  
        print("• apply_fix_to_existing_functions() - Replace existing functions")
        print("• show_query_history_fixed() - Fixed query history")
        print("• display_ticker_intelligence_fixed() - Fixed ticker display")
        print("• display_portfolio_fixed() - Fixed portfolio display")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Run test_repetition_fix() to verify")
        print("2. Run apply_fix_to_existing_functions() to upgrade existing functions")
        print("3. Re-execute problematic cells to see fix in action")
        
        return display_manager
        
    except Exception as e:
        print(f"❌ DEPLOYMENT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def quick_test():
    """Quick test to verify deployment worked"""
    try:
        print("🧪 QUICK DEPLOYMENT TEST")
        print("=" * 30)
        
        # Test RichDisplay
        if 'RichDisplay' in globals():
            print("✅ RichDisplay available")
        else:
            print("❌ RichDisplay not found")
        
        # Test display manager
        if 'display_manager' in globals():
            stats = display_manager.get_stats()
            print(f"✅ Display manager active - {stats['total_sections']} sections")
        else:
            print("❌ Display manager not found")
        
        # Test section functionality
        try:
            with display_manager.section("quick_test"):
                RichDisplay.alert("Quick test successful!", "success")
            print("✅ Section functionality working")
        except Exception as e:
            print(f"❌ Section functionality failed: {e}")
        
        print("\n🎉 Deployment verification complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

# Auto-deploy when script is imported
if __name__ == "__main__":
    # Direct execution
    manager = deploy_elegant_repetition_fix()
    if manager:
        quick_test()
else:
    # Imported execution
    print("📦 Elegant Repetition Fix deployment script loaded")
    print("💡 Run deploy_elegant_repetition_fix() to deploy")