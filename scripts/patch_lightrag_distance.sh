#!/bin/bash
# Location: /scripts/patch_lightrag_distance.sh
# Purpose: Apply distance field exposure patch to LightRAG utils.py after upgrades
# Why: Future pip upgrades of lightrag will overwrite our modification
# Relevant Files: /Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/utils.py

set -e  # Exit on error

UTILS_FILE="/Users/royyeo/anaconda3/lib/python3.11/site-packages/lightrag/utils.py"

echo "🔧 LightRAG Distance Field Patch Script"
echo "========================================"
echo ""

# Check if utils.py exists
if [ ! -f "$UTILS_FILE" ]; then
    echo "❌ Error: LightRAG utils.py not found at: $UTILS_FILE"
    echo "   Make sure LightRAG is installed: pip install lightrag"
    exit 1
fi

# Check if already patched
if grep -q '"distance": chunk.get("distance")' "$UTILS_FILE"; then
    echo "✅ LightRAG is already patched with distance field exposure"
    echo "   No action needed."
    exit 0
fi

echo "📦 LightRAG utils.py found (not yet patched)"
echo "   Location: $UTILS_FILE"
echo ""

# Create backup
BACKUP_DIR="/Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/archive/backups"
BACKUP_FILE="$BACKUP_DIR/lightrag_utils_before_patch_$(date +%Y%m%d_%H%M%S).py"

echo "💾 Creating backup..."
cp "$UTILS_FILE" "$BACKUP_FILE"
echo "   Backup created: $BACKUP_FILE"
echo ""

# Apply patch
echo "🔨 Applying patch..."
echo "   Adding distance field to convert_to_user_format() at line 2929"

# Use sed to insert line after line 2928
# The -i '' syntax is for macOS (empty string for in-place without backup suffix)
sed -i '' '2928 a\
            "distance": chunk.get("distance"),  # Cosine similarity score (0.0-1.0, lower = more similar)
' "$UTILS_FILE"

# Verify patch applied
if grep -q '"distance": chunk.get("distance")' "$UTILS_FILE"; then
    echo "✅ Patch applied successfully!"
    echo ""
    echo "📊 Verification:"
    echo "   Modified section (lines 2924-2931):"
    sed -n '2924,2931p' "$UTILS_FILE" | cat -n
    echo ""
    echo "✅ Distance field is now exposed in LightRAG query results"
    echo ""
    echo "🔄 Next steps:"
    echo "   1. Restart Jupyter kernels to reload LightRAG module"
    echo "   2. Run ice_building_workflow.ipynb to test"
    echo "   3. Verify chunks include 'distance' field"
else
    echo "❌ Patch failed - distance field not found in modified file"
    echo "   Restoring from backup..."
    cp "$BACKUP_FILE" "$UTILS_FILE"
    echo "   Backup restored. Please apply patch manually."
    exit 1
fi
