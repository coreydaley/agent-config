#!/usr/bin/env bash
# Launch codex exec for an audit phase. Owns the canonical invocation
# (see lib/codex-invocation.md) plus output verification.
#
# Usage:
#   audit-codex.sh <audit-dir> <role> <prompt-file> [--skip-git-repo-check]
#
#   <role>                   review | devils-advocate
#   <prompt-file>            path to a file containing the full codex prompt
#   --skip-git-repo-check    pass codex's --skip-git-repo-check flag. Needed
#                            when -C points outside a git repo (e.g. audit-prd
#                            runs codex against the PRD staged under
#                            ~/Reports/...). Code-tree audits omit it.
#
# Outputs (in $AUDIT_DIR):
#   review            → codex.md           + codex.stdout.log
#   devils-advocate   → devils-advocate.md + devils-advocate.stdout.log
#
# Exit codes:
#   0  output file exists and is non-empty
#   1  invocation failed or output file is empty/missing
#   2  bad arguments
#
# This script is the structural enforcement point. If the subagent
# claims it ran the parallel codex review, this script's exit code
# proves it — the output file has to be on disk to exit 0.
set -euo pipefail

AUDIT_DIR="${1:-}"
ROLE="${2:-}"
PROMPT_FILE="${3:-}"

# Optional 4th arg: --skip-git-repo-check (only flag accepted here).
SKIP_GIT_REPO_CHECK=0
if [[ -n "${4:-}" ]]; then
  if [[ "$4" == "--skip-git-repo-check" ]]; then
    SKIP_GIT_REPO_CHECK=1
  else
    echo "audit-codex.sh: unknown 4th arg: $4 (only --skip-git-repo-check)" >&2
    exit 2
  fi
fi

if [[ -z "$AUDIT_DIR" || -z "$ROLE" || -z "$PROMPT_FILE" ]]; then
  echo "audit-codex.sh: usage: <audit-dir> <role:review|devils-advocate> <prompt-file>" >&2
  exit 2
fi

if [[ ! -d "$AUDIT_DIR" ]]; then
  echo "audit-codex.sh: AUDIT_DIR does not exist: $AUDIT_DIR" >&2
  exit 2
fi

if [[ ! -s "$PROMPT_FILE" ]]; then
  echo "audit-codex.sh: prompt file missing or empty: $PROMPT_FILE" >&2
  exit 2
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "audit-codex.sh: codex CLI not installed" >&2
  exit 1
fi

if [[ ! -s "$AUDIT_DIR/MANIFEST.json" ]]; then
  echo "audit-codex.sh: MANIFEST.json missing in $AUDIT_DIR — did audit-runner.sh init run?" >&2
  exit 1
fi

PROJECT_CWD=$(awk -F'"' '/"project_cwd"/{print $4}' "$AUDIT_DIR/MANIFEST.json")
if [[ -z "$PROJECT_CWD" || ! -d "$PROJECT_CWD" ]]; then
  echo "audit-codex.sh: project_cwd from MANIFEST is invalid: $PROJECT_CWD" >&2
  exit 1
fi

case "$ROLE" in
  review)
    OUTPUT_FILE="$AUDIT_DIR/codex.md"
    STDOUT_LOG="$AUDIT_DIR/codex.stdout.log"
    ;;
  devils-advocate)
    OUTPUT_FILE="$AUDIT_DIR/devils-advocate.md"
    STDOUT_LOG="$AUDIT_DIR/devils-advocate.stdout.log"
    ;;
  *)
    echo "audit-codex.sh: role must be 'review' or 'devils-advocate', got: $ROLE" >&2
    exit 2
    ;;
esac

# Pre-clear any stale output so the post-run check can't be fooled by
# a leftover file from a prior run.
rm -f "$OUTPUT_FILE"

PROMPT_BODY=$(cat "$PROMPT_FILE")

# Canonical codex exec invocation. Every flag is load-bearing — see
# lib/codex-invocation.md for the per-flag rationale. Drift here causes
# silent hangs or silent write failures.
GIT_CHECK_FLAG=()
if [[ "$SKIP_GIT_REPO_CHECK" -eq 1 ]]; then
  GIT_CHECK_FLAG=(--skip-git-repo-check)
fi
codex exec \
  -s workspace-write \
  "${GIT_CHECK_FLAG[@]}" \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "$PROMPT_BODY" \
  < /dev/null \
  > "$STDOUT_LOG" 2>&1 \
  || {
    echo "audit-codex.sh: codex exec returned non-zero. See $STDOUT_LOG" >&2
    exit 1
  }

# Hard gate: the output file must exist and be non-empty.
if [[ ! -s "$OUTPUT_FILE" ]]; then
  echo "audit-codex.sh: codex did not produce $OUTPUT_FILE (or produced empty file). See $STDOUT_LOG" >&2
  exit 1
fi

# Soft gate: a findings file should contain at least one table row.
# This catches the "codex wrote a chatty summary instead of a table"
# failure mode that's been seen in the wild.
if ! grep -qE '^\|.*\|.*\|' "$OUTPUT_FILE"; then
  echo "audit-codex.sh: $OUTPUT_FILE has no markdown table rows — codex may have produced prose instead of findings" >&2
  exit 1
fi

printf '%s\n' "$OUTPUT_FILE"
