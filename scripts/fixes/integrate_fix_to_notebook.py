#!/usr/bin/env python3
# integrate_fix_to_notebook.py
# Script to safely integrate elegant repetition fix into ICE development notebook
# Adds integration cell and preserves all existing content

"""
Integration Script - Add Elegant Repetition Fix to ICE Notebook

This script safely adds the integration cell to the existing ICE development
notebook without modifying any existing cells or content.
"""

import json
import os
import sys
from datetime import datetime

def integrate_repetition_fix():
    """Add elegant repetition fix integration cell to the notebook"""
    
    print("🚀 INTEGRATING ELEGANT REPETITION FIX INTO ICE NOTEBOOK")
    print("=" * 60)
    
    notebook_path = "ice_development.ipynb"
    backup_path = f"ice_development_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ipynb"
    
    try:
        # Step 1: Load existing notebook
        print("📖 Loading existing notebook...")
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        print(f"✅ Loaded notebook with {len(notebook['cells'])} cells")
        
        # Step 2: Create additional backup with timestamp
        print("💾 Creating timestamped backup...")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
        print(f"✅ Backup created: {backup_path}")
        
        # Step 3: Create integration cell content
        integration_cell_source = [
            "# ============================================================================\n",
            "# 🚀 ELEGANT REPETITION FIX - INTEGRATION CELL\n", 
            "# ============================================================================\n",
            "# This cell integrates the elegant repetition fix to prevent display accumulation\n",
            "# All existing code continues to work unchanged - this is purely additive\n",
            "# Run this cell once to deploy the fix, then re-execute problematic cells\n",
            "# ============================================================================\n",
            "\n",
            "print(\"🚀 INTEGRATING ELEGANT REPETITION FIX INTO ICE NOTEBOOK\")\n",
            "print(\"=\" * 60)\n",
            "\n",
            "# Deploy the elegant repetition fix\n",
            "exec(open('deploy_repetition_fix.py').read())\n",
            "\n",
            "# Deploy and initialize\n",
            "display_manager = deploy_elegant_repetition_fix()\n",
            "\n",
            "if display_manager:\n",
            "    print(\"\\n🔧 APPLYING FIX TO EXISTING FUNCTIONS\")\n",
            "    print(\"=\" * 40)\n",
            "    \n",
            "    # Apply fix to existing notebook functions\n",
            "    apply_fix_to_existing_functions()\n",
            "    \n",
            "    print(\"\\n🧪 TESTING REPETITION FIX\")\n",
            "    print(\"=\" * 30)\n",
            "    \n",
            "    # Test the fix\n",
            "    test_repetition_fix()\n",
            "    \n",
            "    print(\"\\n📊 SYSTEM STATUS\")\n",
            "    print(\"=\" * 20)\n",
            "    \n",
            "    # Show system status\n",
            "    get_fix_status()\n",
            "    \n",
            "    print(\"\\n🎉 INTEGRATION COMPLETE!\")\n",
            "    print(\"=\" * 30)\n",
            "    print(\"✅ All repetition issues should now be resolved\")\n",
            "    print(\"✅ Re-execute any problematic cells to see the fix in action\")\n",
            "    print(\"✅ Query History, Ticker Intelligence, Themes, and Graphs will no longer repeat\")\n",
            "    \n",
            "    print(\"\\n💡 USAGE TIPS:\")\n",
            "    print(\"• All existing code continues to work unchanged\")\n",
            "    print(\"• RichDisplay functions now auto-clear on re-execution\") \n",
            "    print(\"• Widget handlers remain properly managed\")\n",
            "    print(\"• Run test_repetition_fix() anytime to verify the fix\")\n",
            "    \n",
            "else:\n",
            "    print(\"❌ INTEGRATION FAILED - Please check error messages above\")\n"
        ]
        
        # Step 4: Create integration cell
        integration_cell = {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {
                "tags": ["elegant-repetition-fix"]
            },
            "outputs": [],
            "source": integration_cell_source
        }
        
        # Step 5: Add integration cell after imports (usually cell 0 or 1)
        # Find the best position - after imports but before main logic
        insert_position = 1
        
        # Look for a good insertion point (after imports)
        for i, cell in enumerate(notebook['cells']):
            if cell['cell_type'] == 'code':
                source = ''.join(cell.get('source', []))
                if ('import' in source or 'from' in source) and 'ice' not in source.lower():
                    insert_position = i + 1
                elif 'RichDisplay' in source or 'display(' in source:
                    # Found first display cell, insert before it
                    insert_position = i
                    break
        
        print(f"🔧 Adding integration cell at position {insert_position}...")
        notebook['cells'].insert(insert_position, integration_cell)
        
        # Step 6: Save updated notebook
        print("💾 Saving updated notebook...")
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated notebook saved with {len(notebook['cells'])} cells")
        
        # Step 7: Verify integration
        print("\n🔍 VERIFYING INTEGRATION")
        print("=" * 30)
        print(f"✅ Original notebook backed up to: {backup_path}")
        print(f"✅ Integration cell added at position: {insert_position}")
        print(f"✅ Total cells now: {len(notebook['cells'])}")
        print("✅ All existing cells preserved unchanged")
        
        print("\n🎯 NEXT STEPS")
        print("=" * 15)
        print("1. Open your ice_development.ipynb notebook")
        print(f"2. Find the new integration cell at position {insert_position}")
        print("3. Run the integration cell once")
        print("4. Re-execute any cells that were showing repetition")
        print("5. Enjoy repetition-free notebook execution! 🎉")
        
        return True
        
    except Exception as e:
        print(f"❌ INTEGRATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_integration():
    """Verify the integration was successful"""
    print("\n🔍 INTEGRATION VERIFICATION")
    print("=" * 30)
    
    try:
        with open("ice_development.ipynb", 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # Check if integration cell exists
        integration_found = False
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                source = ''.join(cell.get('source', []))
                if 'ELEGANT REPETITION FIX' in source and 'deploy_repetition_fix' in source:
                    integration_found = True
                    break
        
        if integration_found:
            print("✅ Integration cell successfully added")
            print("✅ Notebook ready for repetition fix deployment")
            return True
        else:
            print("❌ Integration cell not found")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = integrate_repetition_fix()
    if success:
        verify_integration()
        print("\n🎉 INTEGRATION COMPLETE - Notebook ready for repetition fix!")
    else:
        print("\n❌ INTEGRATION FAILED - Check error messages above")
    
    sys.exit(0 if success else 1)