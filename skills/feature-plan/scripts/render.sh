#!/usr/bin/env bash
# Render the state machine graph to SVG.
# Run from the skill directory or anywhere — paths are resolved relative
# to this script.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

dot -Tsvg "$SKILL_DIR/graph.dot" -o "$SKILL_DIR/graph.svg"
echo "Rendered: $SKILL_DIR/graph.svg"
