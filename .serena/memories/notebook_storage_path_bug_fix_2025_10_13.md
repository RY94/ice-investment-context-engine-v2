# Cell 13 Storage Path Bug Fix - 2025-10-13

## Problem
Cell 13 attempts to delete storage directory but fails with `NotADirectoryError` because `storage_path` was redefined to point to a file in Cell 12.

**Cell 12** redefines to FILE:
```python
storage_path = Path(ice.config.working_dir) / "vdb_entities.json"
```

**Cell 13** expects DIRECTORY:
```python
shutil.rmtree(storage_path)  # ERROR: Tries to delete file as directory
```

## Solution
Cell 13 must reset `storage_path` to directory before deletion:

```python
# Reset storage_path to directory (not file from Cell 12)
storage_path = Path(ice.config.working_dir)

if storage_path.exists():
    print("📊 PRE-DELETION CHECK")
    check_storage(storage_path)
    
    shutil.rmtree(storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    print("\n✅ POST-DELETION CHECK")
    check_storage(storage_path)
    print("\n✅ Graph cleared - will rebuild from scratch")
else:
    print("⚠️  Storage path doesn't exist - nothing to clear")
```

## Files Affected
- `ice_building_workflow.ipynb` Cell 13

## Testing
Uncomment Cell 13 and run to verify deletion works correctly.