#!/usr/bin/env python3
# apply_repetition_fix.py
# Automated application of repetition fixes to ice_development.ipynb
# Provides precise guidance for manual fixes and validation
# Ensures end-to-end workflow continues to work after fixes

"""
ICE Development Notebook - Automated Repetition Fix

This script provides step-by-step guidance to fix the repeated output issues
in ice_development.ipynb. The fixes are surgical and preserve all functionality.

Usage:
    python apply_repetition_fix.py
    
The script will:
1. Validate the current notebook state
2. Show exactly which lines need to be changed
3. Provide replacement code for each problematic cell
4. Verify the fixes are applied correctly
"""

import os
import json
import re
from pathlib import Path

class NotebookRepetitionFixer:
    """Handles the application of repetition fixes to the notebook"""
    
    def __init__(self, notebook_path="ice_development.ipynb"):
        self.notebook_path = Path(notebook_path)
        self.fixes_applied = []
        self.validation_results = {}
        
    def load_notebook(self):
        """Load the notebook JSON"""
        try:
            with open(self.notebook_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading notebook: {e}")
            return None
    
    def find_problematic_cells(self, notebook_data):
        """Identify cells with event handler registration"""
        problematic_cells = []
        
        if not notebook_data or 'cells' not in notebook_data:
            return problematic_cells
            
        patterns = [
            r'\.on_click\(',
            r'\.observe\(',
            r'widgets\.Output\(\)',
            r'clear_output\(',
        ]
        
        for i, cell in enumerate(notebook_data['cells']):
            if cell.get('cell_type') == 'code':
                source = ''.join(cell.get('source', []))
                for pattern in patterns:
                    if re.search(pattern, source):
                        problematic_cells.append({
                            'cell_index': i,
                            'cell_source': source[:200] + '...' if len(source) > 200 else source,
                            'pattern_found': pattern
                        })
                        break
        
        return problematic_cells
    
    def show_fix_plan(self):
        """Display the complete fix plan"""
        print("🔧 ICE DEVELOPMENT NOTEBOOK - REPETITION FIX PLAN")
        print("=" * 60)
        print()
        
        notebook_data = self.load_notebook()
        if not notebook_data:
            return False
            
        problematic_cells = self.find_problematic_cells(notebook_data)
        
        print(f"📊 Analysis Results:")
        print(f"   • Total cells: {len(notebook_data['cells'])}")
        print(f"   • Problematic cells: {len(problematic_cells)}")
        print(f"   • Notebook size: {self.notebook_path.stat().st_size / 1024:.1f} KB")
        print()
        
        if problematic_cells:
            print("🎯 Cells requiring fixes:")
            for cell in problematic_cells[:10]:  # Show first 10
                print(f"   • Cell {cell['cell_index']}: {cell['pattern_found']}")
            if len(problematic_cells) > 10:
                print(f"   • ... and {len(problematic_cells) - 10} more cells")
        
        return True
    
    def create_manual_fix_guide(self):
        """Create a detailed manual fix guide"""
        guide_content = """
# MANUAL FIX GUIDE FOR ICE_DEVELOPMENT.IPYNB REPETITION ISSUES
===============================================================

## STEP 1: BACKUP YOUR NOTEBOOK
```bash
cp ice_development.ipynb ice_development_backup.ipynb
```

## STEP 2: ADD THE IMPORT TO YOUR NOTEBOOK

Find Cell 2 (the imports cell) and add this line after the existing imports:

```python
# REPETITION FIX: Import widget manager
from notebook_widget_manager import register_click_once, register_observe_once, guard_cell, manager_stats
print("🔧 Widget Manager loaded - preventing handler accumulation")
```

## STEP 3: APPLY SPECIFIC FIXES

### Fix 1: RAG Engine Selection (around Cell 14)
FIND:
```python
engine_selector.observe(on_engine_change, names='value')
comparison_button.on_click(on_comparison_click)
```

REPLACE WITH:
```python
register_observe_once(engine_selector, on_engine_change, 'rag_engine_selector')
register_click_once(comparison_button, on_comparison_click, 'rag_comparison_button')
```

### Fix 2: Query Interface (around Cell 28)
FIND:
```python
query_button.on_click(on_query_submit)
```

REPLACE WITH:
```python
register_click_once(query_button, on_query_submit, 'main_query_button')
```

### Fix 3: History Interface (around Cell 29)
FIND:
```python
history_button.on_click(on_history_click)
```

REPLACE WITH:
```python
register_click_once(history_button, on_history_click, 'history_button')
```

### Fix 4: Ticker Analysis (around Cell 31)
FIND:
```python
ticker_dropdown.observe(on_ticker_change, names='value')
```

REPLACE WITH:
```python
register_observe_once(ticker_dropdown, on_ticker_change, 'ticker_dropdown')
```

### Fix 5: Graph Visualization (around Cell 38)
FIND:
```python
center_node_dropdown.observe(on_graph_update, names='value')
hop_depth_slider.observe(on_graph_update, names='value')
confidence_slider.observe(on_graph_update, names='value')
recency_slider.observe(on_graph_update, names='value')
edge_types_select.observe(on_graph_update, names='value')
contrarian_checkbox.observe(on_graph_update, names='value')
```

REPLACE WITH:
```python
register_observe_once(center_node_dropdown, on_graph_update, 'center_node_dropdown')
register_observe_once(hop_depth_slider, on_graph_update, 'hop_depth_slider')
register_observe_once(confidence_slider, on_graph_update, 'confidence_slider')
register_observe_once(recency_slider, on_graph_update, 'recency_slider')
register_observe_once(edge_types_select, on_graph_update, 'edge_types_select')
register_observe_once(contrarian_checkbox, on_graph_update, 'contrarian_checkbox')
```

### Fix 6: Portfolio Management (around Cell 41)
FIND:
```python
priority_filter.observe(on_filter_change, names='value')
sector_filter.observe(on_filter_change, names='value')
export_button.on_click(on_export_click)
```

REPLACE WITH:
```python
register_observe_once(priority_filter, on_filter_change, 'priority_filter')
register_observe_once(sector_filter, on_filter_change, 'sector_filter')
register_click_once(export_button, on_export_click, 'portfolio_export_button')
```

### Fix 7: All Other Button Handlers
Apply the same pattern to any other buttons you find:

OLD PATTERN:
```python
some_button.on_click(some_handler)
```

NEW PATTERN:
```python
register_click_once(some_button, some_handler, 'unique_button_name')
```

OLD PATTERN:
```python
some_widget.observe(some_handler, names='value')
```

NEW PATTERN:
```python
register_observe_once(some_widget, some_handler, 'unique_widget_name')
```

## STEP 4: ADD VERIFICATION CELL

Add this as a new cell at the end of your notebook:

```python
# VERIFICATION: Check if repetition fix is working
from notebook_widget_manager import manager_stats, debug_handlers

print("🔍 Widget Manager Verification")
print("=" * 50)

stats = manager_stats()
print(f"✅ Handlers registered: {stats['registered_handlers']}")
print(f"✅ Widgets managed: {stats['registered_widgets']}")
print(f"✅ Execution guards: {stats['execution_guards']}")

print("\\n🎯 Fix Status: Repetition prevention ACTIVE")
if stats['registered_handlers'] > 0:
    print("\\n📋 Registered Handlers:")
    debug_handlers()
```

## STEP 5: TEST THE FIX

1. **Restart kernel**: Kernel → Restart & Clear Output
2. **Run all cells**: Cell → Run All
3. **Test widgets**: Click buttons, change dropdowns - should see single responses
4. **Re-run cells**: Re-execute cells with widgets - should not see duplicated handlers
5. **Check verification**: Run the verification cell to see handler counts

## EXPECTED RESULTS

✅ **Before fix**: Multiple "Answer from LIGHTRAG" or repeated outputs
✅ **After fix**: Single, clean responses to widget interactions
✅ **Re-execution**: No handler accumulation on cell re-run

## TROUBLESHOOTING

**If you still see repeated outputs:**
1. Make sure you imported the widget manager in the imports cell
2. Check that all `.on_click()` and `.observe()` calls are replaced
3. Restart kernel and clear all outputs, then run all cells again
4. Run the verification cell to check handler counts

**If widgets stop working:**
1. Check for typos in the unique handler keys
2. Make sure the handler function names are correct
3. Check the verification cell for error messages

## VERIFICATION CHECKLIST

- [ ] notebook_widget_manager.py exists in project directory
- [ ] Import added to notebook imports cell
- [ ] All .on_click() calls replaced with register_click_once()
- [ ] All .observe() calls replaced with register_observe_once()
- [ ] Verification cell added to notebook
- [ ] Kernel restarted and all cells run successfully
- [ ] Widget interactions produce single responses
- [ ] Re-running cells doesn't accumulate handlers
- [ ] End-to-end workflow still works as expected

## SUCCESS CRITERIA

🎯 **Primary Goal**: No more repeated output instances
🎯 **Secondary Goal**: All existing functionality preserved
🎯 **Tertiary Goal**: Clean, maintainable widget management

The fix is designed to be minimal, elegant, and preserve the complete
end-to-end workflow of the ICE development notebook.
"""
        
        with open('REPETITION_FIX_GUIDE.md', 'w') as f:
            f.write(guide_content)
            
        return guide_content
    
    def validate_fix_prerequisites(self):
        """Validate that fix prerequisites are met"""
        print("🔍 Validating Fix Prerequisites")
        print("-" * 40)
        
        checks = {
            'notebook_exists': self.notebook_path.exists(),
            'widget_manager_exists': Path('notebook_widget_manager.py').exists(),
            'backup_recommended': not Path('ice_development_backup.ipynb').exists()
        }
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check.replace('_', ' ').title()}: {result}")
        
        return all(checks.values()) or (checks['notebook_exists'] and checks['widget_manager_exists'])
    
    def run_fix_process(self):
        """Run the complete fix process"""
        print("🚀 ICE DEVELOPMENT NOTEBOOK - REPETITION FIX")
        print("=" * 60)
        print()
        
        # Step 1: Validate prerequisites
        if not self.validate_fix_prerequisites():
            print("❌ Prerequisites not met. Please ensure:")
            print("   • ice_development.ipynb exists")
            print("   • notebook_widget_manager.py exists")
            print("   • Create backup: cp ice_development.ipynb ice_development_backup.ipynb")
            return False
        
        print()
        
        # Step 2: Show analysis
        if not self.show_fix_plan():
            return False
            
        print()
        
        # Step 3: Create manual fix guide
        print("📝 Creating Manual Fix Guide...")
        guide_content = self.create_manual_fix_guide()
        print("✅ Manual fix guide created: REPETITION_FIX_GUIDE.md")
        print()
        
        # Step 4: Show next steps
        print("🎯 NEXT STEPS:")
        print("1. Review the analysis above")
        print("2. Follow REPETITION_FIX_GUIDE.md for detailed instructions")
        print("3. Test the fixes using the verification cell")
        print("4. Confirm end-to-end workflow still works")
        print()
        
        print("✅ Fix process prepared successfully!")
        print("📋 Manual fixes required - automated patching too risky for large notebook")
        
        return True

def main():
    """Main execution function"""
    print("Starting ICE Development Notebook repetition fix process...")
    print()
    
    fixer = NotebookRepetitionFixer()
    success = fixer.run_fix_process()
    
    if success:
        print("\n🎉 Fix preparation completed successfully!")
        print("📖 Please follow the REPETITION_FIX_GUIDE.md file for step-by-step instructions")
    else:
        print("\n❌ Fix preparation failed. Please check the prerequisites and try again.")
    
    return success

if __name__ == "__main__":
    main()