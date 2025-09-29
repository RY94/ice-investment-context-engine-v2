#!/usr/bin/env python3
# fix_notebook_outputs.py
# Comprehensive fix for output duplication in ice_development.ipynb
# Adds proper output management and interface reuse logic

import json
import re
from pathlib import Path

def fix_notebook_output_management():
    """Apply comprehensive output management fixes to the notebook"""
    
    notebook_path = Path("ice_development.ipynb")
    
    # Load notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    fixes_applied = []
    
    # 1. Add enhanced imports to first code cell
    for i, cell in enumerate(nb['cells']):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            if 'from notebook_widget_manager import' in source:
                # Enhance existing import
                source_lines = cell['source']
                for j, line in enumerate(source_lines):
                    if 'from notebook_widget_manager import' in line:
                        source_lines[j] = "from notebook_widget_manager import register_click_once, register_observe_once, guard_cell, manager_stats\n"
                        source_lines.insert(j+1, "from notebook_output_manager import section_guard, get_output, output_stats, clear_all_outputs\n")
                        source_lines.insert(j+2, "print('🔧 Enhanced output management loaded')\n")
                        fixes_applied.append("Enhanced imports")
                        break
                break
    
    # 2. Fix the main query interface cell
    for i, cell in enumerate(nb['cells']):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            
            # Find the cell with query interface
            if 'output_area = widgets.Output()' in source and 'on_query_submit' in source:
                print(f"Fixing query interface cell {i}")
                
                # Replace the cell content with proper output management
                new_source = [
                    "# QUERY INTERFACE - Fixed Output Management\n",
                    "from notebook_output_manager import section_guard, get_output\n",
                    "from notebook_widget_manager import register_click_once\n",
                    "\n",
                    "if section_guard('query_interface'):\n",
                    "    print('🔧 Initializing Query Interface...')\n",
                    "    \n",
                    "    # Query controls\n",
                    "    query_input = widgets.Textarea(\n",
                    "        value='Why is NVDA at risk from China trade?',\n",
                    "        placeholder='Enter your investment question...',\n",
                    "        description='Question:',\n",
                    "        layout=widgets.Layout(width='100%', height='100px'),\n",
                    "        style={'description_width': 'initial'}\n",
                    "    )\n",
                    "\n",
                    "    query_mode = widgets.Dropdown(\n",
                    "        options=['hybrid', 'local', 'global', 'naive'],\n",
                    "        value='hybrid',\n",
                    "        description='Query Mode:',\n",
                    "        style={'description_width': 'initial'}\n",
                    "    )\n",
                    "\n",
                    "    query_engine = widgets.Dropdown(\n",
                    "        options=['lightrag', 'lazyrag'],\n",
                    "        value='lightrag',\n",
                    "        description='Engine:',\n",
                    "        style={'description_width': 'initial'}\n",
                    "    )\n",
                    "\n",
                    "    max_hops_slider = widgets.IntSlider(\n",
                    "        value=3,\n",
                    "        min=1,\n",
                    "        max=5,\n",
                    "        description='Max Hops:',\n",
                    "        style={'description_width': 'initial'}\n",
                    "    )\n",
                    "\n",
                    "    confidence_threshold = widgets.FloatSlider(\n",
                    "        value=0.60,\n",
                    "        min=0.1,\n",
                    "        max=1.0,\n",
                    "        step=0.05,\n",
                    "        description='Confidence:',\n",
                    "        style={'description_width': 'initial'}\n",
                    "    )\n",
                    "\n",
                    "    comparison_mode = widgets.Checkbox(\n",
                    "        value=False,\n",
                    "        description='Compare Both Engines',\n",
                    "        style={'description_width': 'initial'}\n",
                    "    )\n",
                    "\n",
                    "    query_button = widgets.Button(\n",
                    "        description='🔍 Submit Query',\n",
                    "        button_style='primary',\n",
                    "        layout=widgets.Layout(width='150px')\n",
                    "    )\n",
                    "\n",
                    "    # FIXED: Use managed output container\n",
                    "    output_area = get_output('query_results')\n",
                    "\n",
                    "    def display_query_results_fixed(result, title=None):\n",
                    "        \"\"\"FIXED: Single consolidated output display\"\"\"\n",
                    "        if not result or not isinstance(result, dict):\n",
                    "            return \"<div><h3>❌ Invalid Result</h3><p>Query returned invalid result</p></div>\"\n",
                    "        \n",
                    "        # Build single consolidated HTML\n",
                    "        html_parts = []\n",
                    "        \n",
                    "        # Header\n",
                    "        if title:\n",
                    "            html_parts.append(f\"<h3>{title}</h3>\")\n",
                    "        else:\n",
                    "            engine_name = result.get('engine', 'unknown')\n",
                    "            html_parts.append(f\"<h3>💡 Answer from {engine_name.upper()}</h3>\")\n",
                    "        \n",
                    "        # Status and timing\n",
                    "        status = result.get('status', 'unknown')\n",
                    "        status_icon = \"✅\" if status == 'success' else \"❌\"\n",
                    "        engine_name = result.get('engine', 'unknown')\n",
                    "        query_time = result.get('query_time', 0)\n",
                    "        \n",
                    "        html_parts.append(f\"\"\"<div style='background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0;'>\n",
                    "        {status_icon} <strong>Engine:</strong> {engine_name} | <strong>Status:</strong> {status} | <strong>Time:</strong> {query_time:.3f}s\n",
                    "        </div>\"\"\")\n",
                    "        \n",
                    "        # Answer\n",
                    "        answer = result.get('answer', 'No answer provided')\n",
                    "        html_parts.append(f\"<div style='margin: 15px 0;'><strong>Answer:</strong> {answer}</div>\")\n",
                    "        \n",
                    "        # Confidence scores\n",
                    "        if 'confidence_scores' in result:\n",
                    "            html_parts.append(\"<h4>📊 Confidence Analysis</h4>\")\n",
                    "            html_parts.append(\"<ul>\")\n",
                    "            for metric, score in result['confidence_scores'].items():\n",
                    "                html_parts.append(f\"<li><strong>{metric.replace('_', ' ').title()}:</strong> {score:.2f}</li>\")\n",
                    "            html_parts.append(\"</ul>\")\n",
                    "        \n",
                    "        return ''.join(html_parts)\n",
                    "\n",
                    "    def on_query_submit_fixed(b):\n",
                    "        \"\"\"FIXED: Single output query submission\"\"\"\n",
                    "        output_area.clear_output(wait=True)\n",
                    "        \n",
                    "        with output_area:\n",
                    "            question = query_input.value\n",
                    "            mode = query_mode.value\n",
                    "            engine = query_engine.value\n",
                    "            \n",
                    "            try:\n",
                    "                display(HTML(\"<div style='text-align: center; padding: 20px;'>🔄 Processing query...</div>\"))\n",
                    "                \n",
                    "                # Execute query\n",
                    "                result = ice.query(question, mode=mode, engine=engine)\n",
                    "                \n",
                    "                # Clear and show single result\n",
                    "                output_area.clear_output(wait=True)\n",
                    "                \n",
                    "                if result:\n",
                    "                    consolidated_html = display_query_results_fixed(result)\n",
                    "                    display(HTML(consolidated_html))\n",
                    "                else:\n",
                    "                    display(HTML(\"<h3>⚠️ No Result</h3><p>Query returned empty result.</p>\"))\n",
                    "                    \n",
                    "            except Exception as e:\n",
                    "                output_area.clear_output(wait=True)\n",
                    "                display(HTML(f\"<h3>❌ Query Failed</h3><p><strong>Error:</strong> {str(e)}</p>\"))\n",
                    "\n",
                    "    # Register handler once\n",
                    "    register_click_once(query_button, on_query_submit_fixed, 'main_query_button')\n",
                    "\n",
                    "    # Display interface\n",
                    "    display(HTML(\"<h2>🔍 Ask ICE a Question</h2>\"))\n",
                    "    \n",
                    "    # Layout\n",
                    "    basic_controls = widgets.VBox([\n",
                    "        query_input,\n",
                    "        widgets.HBox([query_mode, query_engine]),\n",
                    "    ])\n",
                    "\n",
                    "    advanced_controls = widgets.VBox([\n",
                    "        widgets.HTML(\"<h4>🔧 LazyRAG Parameters</h4>\"),\n",
                    "        max_hops_slider,\n",
                    "        confidence_threshold,\n",
                    "        comparison_mode\n",
                    "    ])\n",
                    "\n",
                    "    controls_layout = widgets.HBox([\n",
                    "        basic_controls,\n",
                    "        advanced_controls\n",
                    "    ], layout=widgets.Layout(width='100%'))\n",
                    "\n",
                    "    display(widgets.VBox([\n",
                    "        controls_layout,\n",
                    "        query_button,\n",
                    "        output_area\n",
                    "    ]))\n",
                    "    \n",
                    "else:\n",
                    "    print('✅ Query interface already initialized')\n"
                ]
                
                # Replace the cell source
                cell['source'] = new_source
                fixes_applied.append(f"Fixed query interface cell {i}")
                break
    
    # Save modified notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    
    print(f"✅ Applied {len(fixes_applied)} fixes to notebook:")
    for fix in fixes_applied:
        print(f"  - {fix}")
    
    return True

if __name__ == "__main__":
    fix_notebook_output_management()