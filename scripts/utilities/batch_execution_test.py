# batch_execution_test.py
# Test script to execute notebook cells sequentially in batch mode
# Helps identify which cells are still causing blocking issues

import os
import json
import sys

# Set batch execution mode
os.environ['JUPYTER_EXECUTION_MODE'] = 'batch'

def test_notebook_execution():
    """Execute notebook cells one by one to identify blocking cells"""
    
    print("🧪 Testing ICE Development Notebook Execution")
    print("=" * 60)
    
    try:
        with open('ice_development.ipynb', 'r') as f:
            nb = json.load(f)
        
        print(f"📊 Total cells: {len(nb['cells'])}")
        
        successful_cells = 0
        failed_cells = 0
        
        for i, cell in enumerate(nb['cells']):
            if cell['cell_type'] != 'code':
                continue
                
            cell_num = i + 1
            source = ''.join(cell.get('source', []))
            
            # Skip empty cells
            if not source.strip():
                continue
            
            # Show cell preview
            preview = source[:100].replace('\n', ' ')
            print(f"\n📋 Cell {cell_num}: {preview}...")
            
            try:
                # Execute cell
                exec(source, globals())
                print(f"✅ Cell {cell_num} executed successfully")
                successful_cells += 1
                
            except Exception as e:
                print(f"❌ Cell {cell_num} failed: {str(e)}")
                failed_cells += 1
                
                # Show the problematic code
                if len(source) < 500:
                    print(f"   Code: {source[:200]}...")
                
                # Stop on first failure for debugging
                break
        
        print(f"\n📊 Results: {successful_cells} successful, {failed_cells} failed")
        
        if failed_cells == 0:
            print("🎉 All cells executed successfully!")
            return True
        else:
            print("⚠️ Some cells failed - notebook needs more fixes")
            return False
            
    except Exception as e:
        print(f"❌ Error loading notebook: {e}")
        return False

if __name__ == "__main__":
    success = test_notebook_execution()
    sys.exit(0 if success else 1)