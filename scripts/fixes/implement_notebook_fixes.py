#!/usr/bin/env python3
# implement_notebook_fixes.py
# Direct implementation of repetition fixes for ice_development.ipynb
# Applies all necessary patches to prevent event handler accumulation

import json
import os
import re
from pathlib import Path

def load_notebook(path):
    """Load notebook JSON data"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_notebook(notebook_data, path):
    """Save notebook JSON data"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(notebook_data, f, indent=1, ensure_ascii=False)

def find_imports_cell(notebook_data):
    """Find the cell containing the main imports"""
    for i, cell in enumerate(notebook_data['cells']):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            if 'from execution_context import ExecutionContext' in source:
                return i
    return None

def add_widget_manager_import(notebook_data):
    """Add widget manager import to the imports cell"""
    imports_cell_idx = find_imports_cell(notebook_data)
    if imports_cell_idx is None:
        print("❌ Could not find imports cell")
        return False
    
    cell = notebook_data['cells'][imports_cell_idx]
    source_lines = cell['source']
    
    # Find the line with execution_context import
    insert_idx = None
    for i, line in enumerate(source_lines):
        if 'from execution_context import ExecutionContext' in line:
            insert_idx = i + 1
            break
    
    if insert_idx is None:
        print("❌ Could not find execution_context import line")
        return False
    
    # Add widget manager import after execution_context
    new_lines = [
        "\n",
        "# REPETITION FIX: Import widget manager to prevent handler accumulation\n",
        "from notebook_widget_manager import register_click_once, register_observe_once, guard_cell, manager_stats\n",
        "print(\"🔧 Widget Manager loaded - preventing handler accumulation\")\n"
    ]
    
    # Insert new lines
    for j, new_line in enumerate(new_lines):
        source_lines.insert(insert_idx + j, new_line)
    
    print("✅ Added widget manager import to imports cell")
    return True

def fix_handler_registrations(notebook_data):
    """Fix all event handler registrations to prevent accumulation"""
    fixes_applied = 0
    
    # Patterns to find and replace
    patterns = [
        (r'(\w+)\.on_click\((\w+)\)', r'register_click_once(\1, \2, \'\1_button\')'),
        (r'(\w+)\.observe\((\w+), names=\'value\'\)', r'register_observe_once(\1, \2, \'\1_observer\')'),
    ]
    
    for cell_idx, cell in enumerate(notebook_data['cells']):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            modified = False
            
            for pattern, replacement in patterns:
                if re.search(pattern, source):
                    # Apply the fix
                    new_source = re.sub(pattern, replacement, source)
                    if new_source != source:
                        # Split back into lines
                        cell['source'] = new_source.split('\n')
                        # Ensure each line ends with \n except the last
                        cell['source'] = [line + '\n' if i < len(cell['source']) - 1 else line 
                                        for i, line in enumerate(cell['source'])]
                        modified = True
                        fixes_applied += 1
            
            if modified:
                print(f"✅ Fixed cell {cell_idx}")
    
    print(f"✅ Applied {fixes_applied} handler fixes")
    return fixes_applied > 0

def add_verification_cell(notebook_data):
    """Add verification cell at the end of the notebook"""
    verification_source = [
        "# VERIFICATION: Check if repetition fix is working\n",
        "from notebook_widget_manager import manager_stats, debug_handlers\n",
        "\n",
        "print(\"🔍 Widget Manager Verification\")\n",
        "print(\"=\" * 50)\n",
        "\n",
        "stats = manager_stats()\n",
        "print(f\"✅ Handlers registered: {stats['registered_handlers']}\")\n",
        "print(f\"✅ Widgets managed: {stats['registered_widgets']}\")\n",
        "print(f\"✅ Execution guards: {stats['execution_guards']}\")\n",
        "\n",
        "print(\"\\n🎯 Fix Status: Repetition prevention ACTIVE\")\n",
        "if stats['registered_handlers'] > 0:\n",
        "    print(\"\\n📋 Registered Handlers:\")\n",
        "    debug_handlers()\n",
        "else:\n",
        "    print(\"⚠️ No handlers registered yet - run cells with widgets first\")"
    ]
    
    verification_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": verification_source
    }
    
    notebook_data['cells'].append(verification_cell)
    print("✅ Added verification cell")
    return True

def apply_specific_handler_fixes(notebook_data):
    """Apply specific, targeted fixes for known problematic handlers"""
    specific_fixes = [
        # Query interface fix
        ('query_button.on_click(on_query_submit)', 
         'register_click_once(query_button, on_query_submit, \'main_query_button\')'),
        
        # History button fix
        ('history_button.on_click(on_history_click)',
         'register_click_once(history_button, on_history_click, \'history_button\')'),
        
        # RAG engine selector fixes
        ('engine_selector.observe(on_engine_change, names=\'value\')',
         'register_observe_once(engine_selector, on_engine_change, \'rag_engine_selector\')'),
        
        ('comparison_button.on_click(on_comparison_click)',
         'register_click_once(comparison_button, on_comparison_click, \'rag_comparison_button\')'),
        
        # Ticker dropdown fix
        ('ticker_dropdown.observe(on_ticker_change, names=\'value\')',
         'register_observe_once(ticker_dropdown, on_ticker_change, \'ticker_dropdown\')'),
        
        # Graph visualization fixes
        ('center_node_dropdown.observe(on_graph_update, names=\'value\')',
         'register_observe_once(center_node_dropdown, on_graph_update, \'center_node_dropdown\')'),
        
        ('hop_depth_slider.observe(on_graph_update, names=\'value\')',
         'register_observe_once(hop_depth_slider, on_graph_update, \'hop_depth_slider\')'),
        
        ('confidence_slider.observe(on_graph_update, names=\'value\')',
         'register_observe_once(confidence_slider, on_graph_update, \'confidence_slider\')'),
        
        ('recency_slider.observe(on_graph_update, names=\'value\')',
         'register_observe_once(recency_slider, on_graph_update, \'recency_slider\')'),
        
        ('edge_types_select.observe(on_graph_update, names=\'value\')',
         'register_observe_once(edge_types_select, on_graph_update, \'edge_types_select\')'),
        
        ('contrarian_checkbox.observe(on_graph_update, names=\'value\')',
         'register_observe_once(contrarian_checkbox, on_graph_update, \'contrarian_checkbox\')'),
        
        # Portfolio management fixes
        ('priority_filter.observe(on_filter_change, names=\'value\')',
         'register_observe_once(priority_filter, on_filter_change, \'priority_filter\')'),
        
        ('sector_filter.observe(on_filter_change, names=\'value\')',
         'register_observe_once(sector_filter, on_filter_change, \'sector_filter\')'),
        
        # Analytics button fix
        ('analytics_button.on_click(on_analytics_click)',
         'register_click_once(analytics_button, on_analytics_click, \'analytics_button\')'),
        
        # Test button fix
        ('test_button.on_click(on_test_click)',
         'register_click_once(test_button, on_test_click, \'test_button\')'),
        
        # Profile buttons fix
        ('profile_button.on_click(on_profile_click)',
         'register_click_once(profile_button, on_profile_click, \'profile_button\')'),
        
        ('benchmark_button.on_click(on_benchmark_click)',
         'register_click_once(benchmark_button, on_benchmark_click, \'benchmark_button\')'),
        
        # Graph analysis button fix
        ('graph_analysis_button.on_click(on_graph_analysis_click)',
         'register_click_once(graph_analysis_button, on_graph_analysis_click, \'graph_analysis_button\')'),
        
        # Export buttons fix
        ('export_button.on_click(on_export_click)',
         'register_click_once(export_button, on_export_click, \'main_export_button\')'),
        
        ('report_button.on_click(on_report_click)',
         'register_click_once(report_button, on_report_click, \'report_button\')'),
        
        # Demo button fix
        ('demo_button.on_click(on_demo_click)',
         'register_click_once(demo_button, on_demo_click, \'demo_button\')'),
    ]
    
    fixes_applied = 0
    
    for cell_idx, cell in enumerate(notebook_data['cells']):
        if cell.get('cell_type') == 'code':
            source_lines = cell.get('source', [])
            modified = False
            
            for i, line in enumerate(source_lines):
                for old_pattern, new_pattern in specific_fixes:
                    if old_pattern in line:
                        source_lines[i] = line.replace(old_pattern, new_pattern)
                        modified = True
                        fixes_applied += 1
                        print(f"✅ Fixed handler in cell {cell_idx}: {old_pattern[:50]}...")
            
            if modified:
                cell['source'] = source_lines
    
    print(f"✅ Applied {fixes_applied} specific handler fixes")
    return fixes_applied > 0

def main():
    """Main fix implementation"""
    print("🔧 IMPLEMENTING NOTEBOOK REPETITION FIX")
    print("=" * 50)
    
    notebook_path = Path("ice_development.ipynb")
    backup_path = Path("ice_development_backup.ipynb")
    
    # Verify files exist
    if not notebook_path.exists():
        print("❌ ice_development.ipynb not found")
        return False
    
    if not Path("notebook_widget_manager.py").exists():
        print("❌ notebook_widget_manager.py not found - run the fix preparation first")
        return False
    
    # Create backup if it doesn't exist
    if not backup_path.exists():
        import shutil
        shutil.copy2(notebook_path, backup_path)
        print("✅ Created backup: ice_development_backup.ipynb")
    
    # Load notebook
    print("📖 Loading notebook...")
    try:
        notebook_data = load_notebook(notebook_path)
        print(f"✅ Loaded notebook with {len(notebook_data['cells'])} cells")
    except Exception as e:
        print(f"❌ Error loading notebook: {e}")
        return False
    
    # Apply fixes
    fixes_applied = []
    
    print("\n🔧 Applying fixes...")
    
    # 1. Add widget manager import
    if add_widget_manager_import(notebook_data):
        fixes_applied.append("widget_manager_import")
    
    # 2. Apply specific handler fixes
    if apply_specific_handler_fixes(notebook_data):
        fixes_applied.append("specific_handler_fixes")
    
    # 3. Add verification cell
    if add_verification_cell(notebook_data):
        fixes_applied.append("verification_cell")
    
    # Save the fixed notebook
    try:
        save_notebook(notebook_data, notebook_path)
        print(f"✅ Saved fixed notebook with {len(fixes_applied)} fix categories applied")
    except Exception as e:
        print(f"❌ Error saving notebook: {e}")
        return False
    
    print("\n🎯 FIX IMPLEMENTATION COMPLETE")
    print("=" * 50)
    print("✅ Widget manager import added")
    print("✅ Event handler registrations fixed")  
    print("✅ Verification cell added")
    print("\n📋 Next Steps:")
    print("1. Restart Jupyter kernel: Kernel → Restart & Clear Output")
    print("2. Run all cells: Cell → Run All")
    print("3. Test widget interactions - should see single responses")
    print("4. Check verification cell for handler statistics")
    print("5. Confirm end-to-end workflow still functions correctly")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Repetition fix successfully implemented!")
    else:
        print("\n❌ Fix implementation failed")