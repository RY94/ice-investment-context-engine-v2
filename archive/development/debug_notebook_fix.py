#!/usr/bin/env python3
# debug_notebook_fix.py
# Add debug instrumentation to understand the repetition issue

import json
from pathlib import Path

def add_debug_instrumentation():
    """Add debug code to the query interface cell to trace execution"""
    
    notebook_path = Path("ice_development.ipynb")
    
    # Load notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    # Find the query interface cell and add debug instrumentation
    for i, cell in enumerate(nb['cells']):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            
            if "section_guard('query_interface')" in source:
                print(f"Adding debug instrumentation to cell {i}")
                
                # Create debug-enhanced version
                debug_source = [
                    "# DEBUG VERSION - Query Interface with instrumentation\n",
                    "from notebook_output_manager import section_guard, get_output, output_stats\n",
                    "from notebook_widget_manager import register_click_once, manager_stats\n",
                    "\n",
                    "# Global debug counters\n",
                    "if 'debug_counters' not in globals():\n",
                    "    debug_counters = {'cell_runs': 0, 'handler_calls': 0, 'interface_inits': 0}\n",
                    "\n",
                    "debug_counters['cell_runs'] += 1\n",
                    "print(f'🔍 DEBUG: Cell execution #{debug_counters[\"cell_runs\"]}')\n",
                    "\n",
                    "# Check section guard status\n",
                    "guard_result = section_guard('query_interface')\n",
                    "print(f'🔍 DEBUG: section_guard result = {guard_result}')\n",
                    "\n",
                    "if guard_result:\n",
                    "    debug_counters['interface_inits'] += 1\n",
                    "    print(f'🔧 DEBUG: Interface initialization #{debug_counters[\"interface_inits\"]}')\n",
                    "    \n",
                    "    # Query controls (simplified for debugging)\n",
                    "    query_input = widgets.Textarea(\n",
                    "        value='Why is NVDA at risk from China trade?',\n",
                    "        description='Question:',\n",
                    "        layout=widgets.Layout(width='100%', height='80px')\n",
                    "    )\n",
                    "\n",
                    "    query_button = widgets.Button(\n",
                    "        description='🔍 Submit Query',\n",
                    "        button_style='primary'\n",
                    "    )\n",
                    "\n",
                    "    # Use managed output container\n",
                    "    output_area = get_output('query_results_debug')\n",
                    "    print(f'🔍 DEBUG: Got output container: {id(output_area)}')\n",
                    "\n",
                    "    def debug_query_handler(b):\n",
                    "        \"\"\"Debug version of query handler\"\"\"\n",
                    "        debug_counters['handler_calls'] += 1\n",
                    "        \n",
                    "        print(f'🔍 DEBUG: Handler called #{debug_counters[\"handler_calls\"]} - Button ID: {id(b)}')\n",
                    "        \n",
                    "        output_area.clear_output(wait=True)\n",
                    "        \n",
                    "        with output_area:\n",
                    "            # Show debug info\n",
                    "            display(HTML(f\"\"\"<div style='background: #e3f2fd; padding: 10px; border-radius: 4px;'>\n",
                    "            <h4>🔍 DEBUG INFO</h4>\n",
                    "            <p><strong>Handler Call:</strong> #{debug_counters['handler_calls']}</p>\n",
                    "            <p><strong>Cell Runs:</strong> {debug_counters['cell_runs']}</p>\n",
                    "            <p><strong>Interface Inits:</strong> {debug_counters['interface_inits']}</p>\n",
                    "            <p><strong>Button ID:</strong> {id(b)}</p>\n",
                    "            <p><strong>Output Container ID:</strong> {id(output_area)}</p>\n",
                    "            </div>\"\"\"))\n",
                    "            \n",
                    "            # Show widget manager stats\n",
                    "            wm_stats = manager_stats()\n",
                    "            display(HTML(f\"\"\"<div style='background: #f3e5f5; padding: 10px; border-radius: 4px;'>\n",
                    "            <h4>📊 Widget Manager Stats</h4>\n",
                    "            <p><strong>Registered Handlers:</strong> {wm_stats['registered_handlers']}</p>\n",
                    "            <p><strong>Registered Widgets:</strong> {wm_stats['registered_widgets']}</p>\n",
                    "            <p><strong>Execution Guards:</strong> {wm_stats['execution_guards']}</p>\n",
                    "            </div>\"\"\"))\n",
                    "            \n",
                    "            # Show output manager stats\n",
                    "            om_stats = output_stats()\n",
                    "            display(HTML(f\"\"\"<div style='background: #e8f5e8; padding: 10px; border-radius: 4px;'>\n",
                    "            <h4>📊 Output Manager Stats</h4>\n",
                    "            <p><strong>Output Containers:</strong> {om_stats['output_containers']}</p>\n",
                    "            <p><strong>Initialized Sections:</strong> {om_stats['initialized_sections']}</p>\n",
                    "            <p><strong>Sections:</strong> {om_stats['sections']}</p>\n",
                    "            </div>\"\"\"))\n",
                    "            \n",
                    "            # Test actual query (simplified)\n",
                    "            question = query_input.value\n",
                    "            try:\n",
                    "                display(HTML(\"<div style='text-align: center; padding: 10px;'>🔄 Processing query...</div>\"))\n",
                    "                result = ice.query(question, mode='hybrid', engine='lightrag')\n",
                    "                \n",
                    "                if result:\n",
                    "                    display(HTML(f\"\"\"<div style='background: #fff3e0; padding: 10px; border-radius: 4px;'>\n",
                    "                    <h4>💡 Query Result</h4>\n",
                    "                    <p><strong>Status:</strong> {result.get('status', 'unknown')}</p>\n",
                    "                    <p><strong>Engine:</strong> {result.get('engine', 'unknown')}</p>\n",
                    "                    <p><strong>Answer:</strong> {result.get('answer', 'No answer')[:200]}...</p>\n",
                    "                    </div>\"\"\"))\n",
                    "                else:\n",
                    "                    display(HTML(\"<div>⚠️ No result returned</div>\"))\n",
                    "                    \n",
                    "            except Exception as e:\n",
                    "                display(HTML(f\"<div style='background: #ffebee; padding: 10px;'>❌ Error: {str(e)}</div>\"))\n",
                    "\n",
                    "    # Register handler with debug\n",
                    "    print(f'🔍 DEBUG: About to register handler for button {id(query_button)}')\n",
                    "    handler_registered = register_click_once(query_button, debug_query_handler, 'debug_query_button')\n",
                    "    print(f'🔍 DEBUG: Handler registration result = {handler_registered}')\n",
                    "\n",
                    "    # Display interface\n",
                    "    display(HTML(\"<h2>🔍 DEBUG: Ask ICE a Question</h2>\"))\n",
                    "    display(widgets.VBox([\n",
                    "        query_input,\n",
                    "        query_button,\n",
                    "        output_area\n",
                    "    ]))\n",
                    "    \n",
                    "else:\n",
                    "    print(f'✅ DEBUG: Query interface already initialized (cell run #{debug_counters[\"cell_runs\"]})')\n",
                    "    \n",
                    "    # Show current stats even when not initializing\n",
                    "    wm_stats = manager_stats()\n",
                    "    om_stats = output_stats()\n",
                    "    print(f'📊 Current handlers: {wm_stats[\"registered_handlers\"]}, containers: {om_stats[\"output_containers\"]}')\n"
                ]
                
                # Replace the cell source
                cell['source'] = debug_source
                break
    
    # Save debug version
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    
    print("✅ Added debug instrumentation to query interface cell")
    print("📋 Now run the notebook to see detailed execution trace")
    
    return True

if __name__ == "__main__":
    add_debug_instrumentation()