#!/bin/bash

echo "Running make optimize-images..."
make optimize-images

# Check if there are any unstaged changes after running make optimize-images
if ! git diff --quiet; then
    echo ""
    echo "❌ ERROR: make optimize-images produced changes that are not staged."
    echo ""
    echo "Modified files:"
    git status --short
    echo ""
    echo "Please review and stage these changes, then commit again."
    exit 1
fi

echo "✅ No image resizing needed - proceeding with commit"
exit 0
