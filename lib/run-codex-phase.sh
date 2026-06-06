#!/usr/bin/env bash
# Shared codex phase runner with automatic retry on transient failure.
#
# Usage: run-codex-phase.sh <audit-dir> <role> <prompt-file>
#
#   <audit-dir>    path to the audit's working directory (from walker state)
#   <role>         review | devils-advocate
#   <prompt-file>  absolute path to the prompt file
#
# Retries up to 3 times with linear backoff (5s, 10s) on transient failure
# (timeout, non-zero exit from audit-codex.sh). Each attempt is logged to
# stderr so the audit log captures what happened.
#
# Exit codes:
#   0  success (codex ran and produced non-empty output)
#   1  all attempts exhausted
#   2  bad arguments

set -euo pipefail

AUDIT_DIR="${1:-}"
ROLE="${2:-}"
PROMPT_FILE="${3:-}"

if [[ -z "$AUDIT_DIR" || -z "$ROLE" || -z "$PROMPT_FILE" ]]; then
  echo "run-codex-phase: usage: <audit-dir> <role:review|devils-advocate> <prompt-file>" >&2
  exit 2
fi

if [[ ! -d "$AUDIT_DIR" ]]; then
  echo "run-codex-phase: AUDIT_DIR does not exist: $AUDIT_DIR" >&2
  exit 2
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "run-codex-phase: prompt file not found: $PROMPT_FILE" >&2
  exit 2
fi

MAX_ATTEMPTS=3

for attempt in 1 2 3; do
  echo "run-codex-phase: attempt $attempt/$MAX_ATTEMPTS (role=$ROLE)" >&2

  if bash ~/.claude/lib/audit-codex.sh "$AUDIT_DIR" "$ROLE" "$PROMPT_FILE" < /dev/null; then
    echo "run-codex-phase: succeeded on attempt $attempt" >&2
    exit 0
  fi

  if [[ $attempt -lt $MAX_ATTEMPTS ]]; then
    SLEEP=$(( attempt * 5 ))
    echo "run-codex-phase: attempt $attempt failed — retrying in ${SLEEP}s..." >&2
    sleep "$SLEEP"
  fi
done

echo "run-codex-phase: all $MAX_ATTEMPTS attempts failed (role=$ROLE, prompt=$PROMPT_FILE)" >&2
exit 1
