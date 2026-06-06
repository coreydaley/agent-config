#!/usr/bin/env bash
# Zero-arg codex review launcher. Called from independent-reviews node as:
#   bash scripts/run-review.sh "$AUDIT_DIR"
# Do NOT call codex exec directly — this script owns the invocation.
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec bash ~/.claude/lib/run-codex-phase.sh "$1" review "$SKILL_DIR/prompts/codex-review.md"
