#!/usr/bin/env bash
# Zero-arg codex devils-advocate launcher. Called from devils-advocate node as:
#   bash scripts/run-devils-advocate.sh "$AUDIT_DIR"
# Do NOT call codex exec directly — this script owns the invocation.
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec bash ~/.claude/lib/run-codex-phase.sh "$1" devils-advocate "$SKILL_DIR/prompts/codex-devils-advocate.md"
