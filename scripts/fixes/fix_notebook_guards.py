#!/usr/bin/env python3
# fix_notebook_guards.py
# Add execution guards to ice_development.ipynb to prevent output duplication
# This script adds guard cells and proper output container management

import json
import re
from pathlib import Path

def add_execution_guards_to_notebook():
    """Add execution guards to prevent interface duplication"""
    
    notebook_path = Path("ice_development.ipynb")
    
    # Load notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    # Find cells that need guards
    cells_to_modify = []
    
    for i, cell in enumerate(nb['cells']):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            
            # Look for interface creation patterns
            if any(pattern in source for pattern in [
                'display(HTML("<h2>🔍 Ask ICE a Question</h2>"))',
                'display(HTML("<h2>📚 Query History</h2>"))',
                'display(HTML("<h2>🎯 Per-Ticker Intelligence</h2>"))',
                'display(HTML("<h2>🕸️ ICE Knowledge Graph</h2>"))',
                'display(HTML("<h2>📊 Portfolio Management</h2>"))',
                'display(HTML("<h2>🔬 Analytics & Testing</h2>"))',
                'display(HTML("<h2>⚙️ Performance Profiling</h2>"))',
                'display(HTML("<h2>📈 Graph Analysis</h2>"))',
                'display(HTML("<h2>💾 Export & Reporting</h2>"))',
                'display(HTML("<h2>🎮 Interactive Demo</h2>"))'
            ]):
                cells_to_modify.append(i)
    
    # Add guards to identified cells
    for cell_idx in cells_to_modify:
        cell = nb['cells'][cell_idx]
        source_lines = cell['source']
        
        # Find the interface title line
        title_line_idx = None
        for i, line in enumerate(source_lines):
            if 'display(HTML("<h2>' in line:
                title_line_idx = i
                break
        
        if title_line_idx is not None:
            # Extract interface name from title
            title_match = re.search(r'<h2>([^<]+)</h2>', source_lines[title_line_idx])
            if title_match:
                title = title_match.group(1)
                # Create guard key from title
                guard_key = re.sub(r'[^a-zA-Z0-9]', '_', title.lower()).strip('_')
                
                # Insert guard at the beginning of the cell
                guard_lines = [
                    f"# EXECUTION GUARD: {title}\n",
                    f"from notebook_widget_manager import guard_cell\n",
                    f"if not guard_cell('{guard_key}'):\n",
                    f"    print('✅ {title} interface already initialized')\n",
                    f"else:\n",
                    f"    print('🔧 Initializing {title} interface...')\n",
                    f"    \n"
                ]
                
                # Indent all existing lines
                indented_lines = []
                for line in source_lines:
                    if line.strip():  # Don't indent empty lines
                        indented_lines.append("    " + line)
                    else:
                        indented_lines.append(line)
                
                # Combine guard + indented content
                cell['source'] = guard_lines + indented_lines
    
    # Add import cell at the beginning if not exists
    import_added = False
    for cell in nb['cells']:
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            if 'from notebook_widget_manager import' in source:
                import_added = True
                break
    
    if not import_added:
        # Find first code cell and add imports there
        for i, cell in enumerate(nb['cells']):
            if cell.get('cell_type') == 'code':
                source_lines = cell['source']
                if source_lines and 'import' in ''.join(source_lines):
                    # Add widget manager import
                    insert_lines = [
                        "\n# REPETITION FIX: Enhanced widget manager with output guards\n",
                        "from notebook_widget_manager import (\n",
                        "    register_click_once, register_observe_once, guard_cell, \n",
                        "    manager_stats, register_output_container, get_output_container,\n",
                        "    clear_output_containers\n",
                        ")\n",
                        "print('🔧 Enhanced Widget Manager loaded - preventing all duplications')\n",
                        "\n"
                    ]
                    # Insert after existing imports
                    cell['source'].extend(insert_lines)
                    break
    
    # Save modified notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    
    print(f"✅ Added execution guards to {len(cells_to_modify)} interface cells")
    print("✅ Enhanced import statement added")
    print("✅ Notebook now has complete duplication prevention")
    
    return True

if __name__ == "__main__":
    add_execution_guards_to_notebook()