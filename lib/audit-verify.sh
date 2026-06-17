#!/usr/bin/env bash
# Verify that all expected audit artifacts exist and are non-empty.
# Updates MANIFEST.json with completed_at on success.
#
# Usage:
#   audit-verify.sh <audit-dir> [--strict]
#
# --strict  also require devils-advocate.md (not just claude.md +
#           synthesis.md + REPORT.md). Off by default so runs where the
#           devil's-advocate pass was skipped can still pass with a warning.
#
# Exit codes:
#   0   all required artifacts present and non-empty
#   1   one or more artifacts missing or empty
#   2   bad arguments
#
# This is the gate. The subagent's handoff message must include this
# script's output verbatim, and it cannot honestly say "audit complete"
# unless exit code is 0.
set -euo pipefail

AUDIT_DIR="${1:-}"
STRICT=0
shift || true
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    *) echo "audit-verify.sh: unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [[ -z "$AUDIT_DIR" || ! -d "$AUDIT_DIR" ]]; then
  echo "audit-verify.sh: audit dir missing or not a directory: $AUDIT_DIR" >&2
  exit 2
fi

errors=0
warnings=0

check_required() {
  local file="$1"
  local label="$2"
  if [[ ! -s "$AUDIT_DIR/$file" ]]; then
    echo "FAIL: $label missing or empty: $AUDIT_DIR/$file" >&2
    errors=$((errors+1))
  fi
}

check_optional_strict() {
  local file="$1"
  local label="$2"
  if [[ ! -s "$AUDIT_DIR/$file" ]]; then
    if [[ "$STRICT" -eq 1 ]]; then
      echo "FAIL: $label missing or empty (strict mode): $AUDIT_DIR/$file" >&2
      errors=$((errors+1))
    else
      echo "WARN: $label missing — devil's-advocate pass assumed skipped" >&2
      warnings=$((warnings+1))
    fi
  fi
}

check_table() {
  local file="$1"
  local label="$2"
  if [[ -s "$AUDIT_DIR/$file" ]]; then
    if ! grep -qE '^\|.*\|.*\|' "$AUDIT_DIR/$file"; then
      echo "FAIL: $label has no markdown table rows — likely prose instead of findings: $AUDIT_DIR/$file" >&2
      errors=$((errors+1))
    fi
  fi
}

# Emergency exit short-circuits the rest of the gate.
if [[ -s "$AUDIT_DIR/EMERGENCY.md" ]]; then
  echo "EMERGENCY EXIT: $AUDIT_DIR/EMERGENCY.md present — audit halted in Phase 1." >&2
  echo "Hand-off must point user at EMERGENCY.md and confirm no Phase 2+ work ran." >&2
  if grep -qE '^\|.*\|.*\|' "$AUDIT_DIR/EMERGENCY.md" 2>/dev/null \
     || [[ -s "$AUDIT_DIR/EMERGENCY.md" ]]; then
    exit 0
  fi
fi

if [[ ! -s "$AUDIT_DIR/MANIFEST.json" ]]; then
  echo "FAIL: MANIFEST.json missing — audit-runner.sh init never ran" >&2
  exit 1
fi

# Required: the orchestrator-side artifacts.
check_required "claude.md"          "Claude review"
check_required "synthesis.md"       "Synthesis"
check_required "REPORT.md"          "Report"

check_table    "claude.md"          "Claude review"
check_table    "synthesis.md"       "Synthesis"

# Strict-only or warn: the devil's-advocate artifact (a skipped DA pass
# is allowed but loudly noted).
check_optional_strict "devils-advocate.md" "Devil's advocate"

check_table    "devils-advocate.md" "Devil's advocate"

if [[ "$errors" -gt 0 ]]; then
  echo "" >&2
  echo "audit-verify.sh: $errors error(s), $warnings warning(s)." >&2
  exit 1
fi

# Stamp completion. Use a tmp file + mv to keep MANIFEST.json atomic.
COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TMP="$AUDIT_DIR/MANIFEST.json.tmp"
if command -v jq >/dev/null 2>&1; then
  jq --arg ts "$COMPLETED_AT" '. + {completed_at: $ts}' \
    "$AUDIT_DIR/MANIFEST.json" > "$TMP"
  mv "$TMP" "$AUDIT_DIR/MANIFEST.json"
else
  # jq absent — append a sidecar instead of mangling the JSON.
  echo "$COMPLETED_AT" > "$AUDIT_DIR/COMPLETED_AT"
fi

cat <<SUMMARY
audit-verify.sh: OK ($warnings warning(s)).
  AUDIT_DIR: $AUDIT_DIR
  Artifacts:
    claude.md           $(wc -l < "$AUDIT_DIR/claude.md" 2>/dev/null | tr -d ' ') lines
    synthesis.md        $(wc -l < "$AUDIT_DIR/synthesis.md" 2>/dev/null | tr -d ' ') lines
    devils-advocate.md  $([ -s "$AUDIT_DIR/devils-advocate.md" ] && wc -l < "$AUDIT_DIR/devils-advocate.md" | tr -d ' ' || echo "MISSING (DA pass skipped)")
    REPORT.md           $(wc -l < "$AUDIT_DIR/REPORT.md" 2>/dev/null | tr -d ' ') lines
SUMMARY
