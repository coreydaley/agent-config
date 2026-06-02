#!/usr/bin/env bash
# Shared helpers for the audit-* skills. Sourced (or directly invoked) by
# nodes that need to resolve the canonical audit output directory, run
# tooling, or check a timeout binary.
#
# This file owns the side effects that the framework prose used to merely
# describe. If a node calls audit_init and the directory isn't created,
# subsequent nodes can't write to $AUDIT_DIR and the walker will refuse
# to transition. The contract is structural, not prose.
#
# Usage:
#   source lib/audit-runner.sh
#   audit_init <audit-name> [scope_path]
#   # $AUDIT_DIR, $PROJECT_CWD, $ORG_REPO, $REPORT_TS now exported
set -euo pipefail

# Resolve the canonical $AUDIT_DIR for a given audit-name and (optional)
# scope path. Prints the resolved $AUDIT_DIR to stdout as the sole
# success signal. Sets $AUDIT_DIR, $PROJECT_CWD, $ORG_REPO, $REPORT_TS
# in the calling shell when sourced.
audit_init() {
  local audit_name="${1:?audit_init: missing audit-name}"
  local scope="${2:-}"

  # Scope defaults to cwd; honored verbatim when provided.
  PROJECT_CWD="${scope:-$(pwd)}"
  if [[ ! -d "$PROJECT_CWD" ]]; then
    echo "audit_init: scope path does not exist: $PROJECT_CWD" >&2
    return 1
  fi

  # Org/repo resolution: upstream beats origin. If neither remote exists
  # (e.g. agent-config running from a non-git dir), fall back to the
  # basename of $PROJECT_CWD prefixed with "local/".
  local remote
  remote=$(git -C "$PROJECT_CWD" remote get-url upstream 2>/dev/null \
        || git -C "$PROJECT_CWD" remote get-url origin   2>/dev/null \
        || echo "")
  if [[ -n "$remote" ]]; then
    # Host-agnostic: strip a trailing .git, normalize scp/ssh/https
    # separators to '/', then take the last two path segments as
    # <org>/<repo>. Works for github.com, self-hosted Forgejo
    # (https://host:port/org/repo.git and ssh://git@host:port/org/repo.git),
    # and scp-style git@host:org/repo.git alike.
    ORG_REPO=$(printf '%s' "$remote" | sed -E 's|\.git$||' | tr ':' '/' \
      | awk -F/ 'NF>=2 {print $(NF-1)"/"$NF}')
  else
    ORG_REPO="local/$(basename "$PROJECT_CWD")"
  fi

  REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
  local reports_base="$HOME/Reports/$ORG_REPO"
  AUDIT_DIR="$reports_base/audits/${REPORT_TS}-${audit_name}"

  mkdir -p "$AUDIT_DIR/tooling-raw"

  # Manifest is the structural receipt that init ran. Subsequent nodes
  # read it; audit-verify.sh checks for it. Never edit by hand.
  cat > "$AUDIT_DIR/MANIFEST.json" <<EOF
{
  "audit_name": "$audit_name",
  "scope": "$PROJECT_CWD",
  "org_repo": "$ORG_REPO",
  "report_ts": "$REPORT_TS",
  "audit_dir": "$AUDIT_DIR",
  "project_cwd": "$PROJECT_CWD",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "expected_artifacts": [
    "claude.md",
    "codex.md",
    "synthesis.md",
    "devils-advocate.md",
    "REPORT.md"
  ]
}
EOF

  export AUDIT_DIR PROJECT_CWD ORG_REPO REPORT_TS

  # Sole stdout output is the AUDIT_DIR — callers capture this.
  printf '%s\n' "$AUDIT_DIR"
}

# Detect a timeout binary; macOS doesn't ship one. Echoes the path or
# empty string. Callers use:  ${TO:+$TO 300} <cmd>
audit_timeout_bin() {
  command -v timeout 2>/dev/null \
    || command -v gtimeout 2>/dev/null \
    || true
}

# Direct invocation: print $AUDIT_DIR to stdout and exit 0. Lets nodes
# do:  AUDIT_DIR=$(bash lib/audit-runner.sh init <name> [scope])
# without sourcing.
if [[ "${BASH_SOURCE[0]:-}" == "${0}" ]]; then
  case "${1:-}" in
    init)
      shift
      audit_init "$@"
      ;;
    timeout-bin)
      audit_timeout_bin
      ;;
    *)
      cat >&2 <<USAGE
Usage:
  audit-runner.sh init <audit-name> [scope-path]
      Resolves and creates \$AUDIT_DIR under ~/Reports/<org>/<repo>/audits/,
      writes MANIFEST.json, prints the AUDIT_DIR path to stdout.

  audit-runner.sh timeout-bin
      Echoes the path to a timeout binary (timeout or gtimeout), or empty.
USAGE
      exit 2
      ;;
  esac
fi
