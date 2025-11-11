#!/bin/bash
# Location: /scripts/patch_lightrag_distance_complete.sh
# Purpose: Apply COMPLETE distance field exposure patch to LightRAG (utils.py + operate.py)
# Why: Future pip upgrades of lightrag will overwrite our modifications
# Relevant Files: utils.py:2929, operate.py:3797,3812,3827

set -e  # Exit on error

UTILS_FILE="/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/utils.py"
OPERATE_FILE="/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/operate.py"
BACKUP_DIR="/Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/archive/backups"

echo "🔧 LightRAG Complete Distance Field Patch Script"
echo "=================================================="
echo ""
echo "This script applies THREE critical modifications:"
echo "  1. utils.py:2929 - Expose distance in convert_to_user_format()"
echo "  2. operate.py:3797,3812,3827 - Preserve distance in _merge_all_chunks() [hybrid/local/global]"
echo "  3. operate.py:3385 - Preserve distance in _get_vector_context() [naive mode]"
echo ""

# Check if files exist
if [ ! -f "$UTILS_FILE" ]; then
    echo "❌ Error: LightRAG utils.py not found at: $UTILS_FILE"
    echo "   Make sure LightRAG is installed: pip install lightrag"
    exit 1
fi

if [ ! -f "$OPERATE_FILE" ]; then
    echo "❌ Error: LightRAG operate.py not found at: $OPERATE_FILE"
    echo "   Make sure LightRAG is installed: pip install lightrag"
    exit 1
fi

echo "✅ LightRAG installation found"
echo ""

# ============================================================================
# PATCH 1: utils.py (expose distance field in output format)
# ============================================================================

echo "📦 Checking PATCH 1: utils.py (distance field exposure)"
echo "   Location: $UTILS_FILE:2929"
echo ""

if grep -q '"distance": chunk.get("distance")' "$UTILS_FILE"; then
    echo "✅ PATCH 1 already applied (utils.py)"
else
    echo "🔨 Applying PATCH 1..."

    # Create backup
    UTILS_BACKUP="$BACKUP_DIR/lightrag_utils_before_patch_$(date +%Y%m%d_%H%M%S).py"
    cp "$UTILS_FILE" "$UTILS_BACKUP"
    echo "   💾 Backup created: $UTILS_BACKUP"

    # Apply patch using sed (macOS syntax)
    sed -i '' '2928 a\
            "distance": chunk.get("distance"),  # Cosine similarity score (0.0-1.0, lower = more similar)
' "$UTILS_FILE"

    # Verify
    if grep -q '"distance": chunk.get("distance")' "$UTILS_FILE"; then
        echo "   ✅ PATCH 1 applied successfully"
    else
        echo "   ❌ PATCH 1 failed - restoring backup"
        cp "$UTILS_BACKUP" "$UTILS_FILE"
        exit 1
    fi
fi

echo ""

# ============================================================================
# PATCH 2: operate.py (_merge_all_chunks - preserve distance during chunk merging)
# ============================================================================

echo "📦 Checking PATCH 2: operate.py (_merge_all_chunks - hybrid/local/global modes)"
echo "   Locations: $OPERATE_FILE:3797,3812,3827"
echo ""

# Check if all 3 locations are patched
MERGE_PATCHED=$(grep -c '"distance": chunk.get("distance"),  # Cosine similarity score' "$OPERATE_FILE" || true)

if [ "$MERGE_PATCHED" -eq 3 ]; then
    echo "✅ PATCH 2 already applied (all 3 locations in _merge_all_chunks)"
elif [ "$MERGE_PATCHED" -eq 0 ]; then
    echo "🔨 Applying PATCH 2 to all 3 locations..."

    # Create backup
    OPERATE_BACKUP="$BACKUP_DIR/lightrag_operate_before_patch_$(date +%Y%m%d_%H%M%S).py"
    cp "$OPERATE_FILE" "$OPERATE_BACKUP"
    echo "   💾 Backup created: $OPERATE_BACKUP"

    # Apply patch using Python for precision
    python3 << 'PYTHON_PATCH_SCRIPT'
import re

operate_file = "/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/operate.py"

with open(operate_file, 'r') as f:
    content = f.read()

# Pattern to match the dict creation in merged_chunks.append()
pattern = r'(merged_chunks\.append\(\s*\{\s*"content": chunk\["content"\],\s*"file_path": chunk\.get\("file_path", "unknown_source"\),\s*"chunk_id": chunk_id,)\s*(\}\s*\))'

# Replacement adds distance field before closing brace
replacement = r'\1\n                        "distance": chunk.get("distance"),  # Cosine similarity score (0.0-1.0, lower = more similar)\n                    \2'

# Apply replacement (should match 3 times)
new_content, count = re.subn(pattern, replacement, content)

if count == 3:
    with open(operate_file, 'w') as f:
        f.write(new_content)
    print(f"   ✅ Successfully patched {count} locations")
else:
    print(f"   ❌ Expected 3 matches, found {count}")
    exit(1)
PYTHON_PATCH_SCRIPT

    # Verify
    MERGE_PATCHED=$(grep -c '"distance": chunk.get("distance"),  # Cosine similarity score' "$OPERATE_FILE" || true)
    if [ "$MERGE_PATCHED" -eq 3 ]; then
        echo "   ✅ PATCH 2 applied successfully (all 3 locations)"
    else
        echo "   ❌ PATCH 2 failed (found $MERGE_PATCHED/3 patches) - restoring backup"
        cp "$OPERATE_BACKUP" "$OPERATE_FILE"
        exit 1
    fi
else
    echo "⚠️  PATCH 2 partially applied ($MERGE_PATCHED/3 locations)"
    echo "   This is an unexpected state. Manual inspection recommended."
    echo "   File: $OPERATE_FILE"
    exit 1
fi

echo ""

# ============================================================================
# PATCH 3: operate.py (_get_vector_context - preserve distance in naive mode)
# ============================================================================

echo "📦 Checking PATCH 3: operate.py (_get_vector_context - naive mode)"
echo "   Location: $OPERATE_FILE:3385"
echo ""

# Check if patch is applied (look for distance conversion logic)
if grep -q 'distance = float(distance)' "$OPERATE_FILE"; then
    echo "✅ PATCH 3 already applied (_get_vector_context)"
else
    echo "🔨 Applying PATCH 3..."

    # Create backup if not already created
    if [ ! -f "$OPERATE_BACKUP" ]; then
        OPERATE_BACKUP="$BACKUP_DIR/lightrag_operate_before_patch_$(date +%Y%m%d_%H%M%S).py"
        cp "$OPERATE_FILE" "$OPERATE_BACKUP"
        echo "   💾 Backup created: $OPERATE_BACKUP"
    fi

    # Apply patch using Python for precision
    python3 << 'PYTHON_PATCH_NAIVE'
import re

operate_file = "/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/operate.py"

with open(operate_file, 'r') as f:
    content = f.read()

# Find the _get_vector_context function and add distance field with conversion
old_pattern = r'(\s+if "content" in result:\n)(\s+chunk_with_metadata = \{\n\s+"content": result\["content"\],\n\s+"created_at": result\.get\("created_at", None\),\n\s+"file_path": result\.get\("file_path", "unknown_source"\),\n\s+"source_type": "vector",  # Mark the source type\n\s+"chunk_id": result\.get\("id"\),  # Add chunk_id for deduplication\n\s+\})'

new_pattern = r'\1                # Convert distance to float if present (handles numpy types)\n                distance = result.get("distance")\n                if distance is not None:\n                    distance = float(distance)\n\n                chunk_with_metadata = {\n                    "content": result["content"],\n                    "created_at": result.get("created_at", None),\n                    "file_path": result.get("file_path", "unknown_source"),\n                    "source_type": "vector",  # Mark the source type\n                    "chunk_id": result.get("id"),  # Add chunk_id for deduplication\n                    "distance": distance,  # Cosine similarity score (0.0-1.0, lower = more similar)\n                }'

new_content = re.sub(old_pattern, new_pattern, content)

# Check if modification was made
if new_content != content:
    with open(operate_file, 'w') as f:
        f.write(new_content)
    print("   ✅ Successfully patched _get_vector_context")
else:
    # Patch may already be partially applied, check for distance field
    if '"distance": distance,' in content or '"distance": result.get("distance"),' in content:
        print("   ✅ Distance field already present in _get_vector_context")
    else:
        print("   ❌ Failed to apply patch - pattern not found")
        exit(1)
PYTHON_PATCH_NAIVE

    # Verify
    if grep -q 'distance = float(distance)' "$OPERATE_FILE"; then
        echo "   ✅ PATCH 3 applied successfully"
    else
        echo "   ❌ PATCH 3 failed - restoring backup"
        cp "$OPERATE_BACKUP" "$OPERATE_FILE"
        exit 1
    fi
fi

echo ""
echo "================================================================"
echo "✅ ALL PATCHES APPLIED SUCCESSFULLY"
echo "================================================================"
echo ""
echo "Modified files:"
echo "  1. $UTILS_FILE:2929"
echo "  2. $OPERATE_FILE:3797,3812,3827 (_merge_all_chunks)"
echo "  3. $OPERATE_FILE:3374-3387 (_get_vector_context)"
echo ""
echo "📊 What was fixed:"
echo "  - Distance field EXPOSED in final chunk format (utils.py)"
echo "  - Distance field PRESERVED during chunk merging for hybrid/local/global (operate.py)"
echo "  - Distance field PRESERVED in naive mode vector retrieval (operate.py)"
echo "  - Numpy float32 conversion to Python float for JSON serialization"
echo ""
echo "🔄 Next steps:"
echo "  1. Restart any Jupyter kernels to reload LightRAG module"
echo "  2. Run ice_building_workflow.ipynb Cell 33"
echo "  3. Verify chunks include non-None 'distance' values"
echo "  4. Check Cell 34 for detailed distance score breakdown"
echo ""
echo "🎯 Expected behavior:"
echo "  - Naive mode: ALL chunks have distance scores (0.0-1.0)"
echo "  - Hybrid/local/global: Vector chunks have distance, entity/relation chunks have None"
echo "  - Lower distance = more similar (0.0 = identical, 1.0 = orthogonal)"
echo ""
