#!/usr/bin/env bash
# Shared helpers for the plane-* skills. Analog of audit-runner.sh — owns
# org/repo resolution and the Plane-shaped directory layout under
# ~/Reports/<org>/<repo>/.
#
# Usage:
#   source lib/plane-runner.sh
#   plane_resolve [scope_path]
#   # $ORG, $REPO, $PROJECT_CWD, $WORKSPACE_DIR, $PROJECT_DIR now exported
#
# Or directly:
#   ORG_REPO=$(bash lib/plane-runner.sh resolve [scope])
#   PROJECT_DIR=$(bash lib/plane-runner.sh project-dir [scope])
#
# Owns the side effect of creating ~/Reports/<org>/<repo>/ (idempotent).
# Does NOT create WORKSPACE.md or PROJECT.md — that's plane-init's job.
set -euo pipefail

# Resolve and export ORG, REPO, PROJECT_CWD, WORKSPACE_DIR, PROJECT_DIR.
# Echoes "$ORG/$REPO" to stdout on success.
plane_resolve() {
  local scope="${1:-}"
  PROJECT_CWD="${scope:-$(pwd)}"
  if [[ ! -d "$PROJECT_CWD" ]]; then
    echo "plane_resolve: scope path does not exist: $PROJECT_CWD" >&2
    return 1
  fi

  local remote
  remote=$(git -C "$PROJECT_CWD" remote get-url upstream 2>/dev/null \
        || git -C "$PROJECT_CWD" remote get-url origin   2>/dev/null \
        || echo "")
  if [[ -n "$remote" ]]; then
    local org_repo
    org_repo=$(printf '%s' "$remote" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
    ORG="${org_repo%%/*}"
    REPO="${org_repo##*/}"
  else
    ORG="local"
    REPO=$(basename "$PROJECT_CWD")
  fi

  WORKSPACE_DIR="$HOME/Reports/$ORG"
  PROJECT_DIR="$WORKSPACE_DIR/$REPO"
  mkdir -p "$PROJECT_DIR"

  export ORG REPO PROJECT_CWD WORKSPACE_DIR PROJECT_DIR
  printf '%s/%s\n' "$ORG" "$REPO"
}

# Standard subdirs under PROJECT_DIR. Idempotent.
plane_ensure_project_subdirs() {
  : "${PROJECT_DIR:?plane_ensure_project_subdirs: PROJECT_DIR not set; call plane_resolve first}"
  mkdir -p \
    "$PROJECT_DIR/work-items" \
    "$PROJECT_DIR/cycles" \
    "$PROJECT_DIR/modules" \
    "$PROJECT_DIR/epics" \
    "$PROJECT_DIR/milestones" \
    "$PROJECT_DIR/pages"
}

# Locate the most recent audit dir for an audit-name (e.g. "apple-security").
# Echoes the resolved path or exits non-zero if none found.
plane_latest_audit_dir() {
  : "${PROJECT_DIR:?plane_latest_audit_dir: PROJECT_DIR not set}"
  local audit_name="${1:?plane_latest_audit_dir: missing audit-name}"
  local matches
  matches=$(find "$PROJECT_DIR/audits" -maxdepth 1 -type d \
            -name "*-${audit_name}" 2>/dev/null | sort | tail -n 1)
  if [[ -z "$matches" ]]; then
    echo "plane_latest_audit_dir: no audit dir found for ${audit_name} under $PROJECT_DIR/audits/" >&2
    return 1
  fi
  printf '%s\n' "$matches"
}

# Direct invocation
if [[ "${BASH_SOURCE[0]:-}" == "${0}" ]]; then
  case "${1:-}" in
    resolve)
      shift; plane_resolve "$@"
      ;;
    project-dir)
      shift; plane_resolve "$@" >/dev/null; printf '%s\n' "$PROJECT_DIR"
      ;;
    workspace-dir)
      shift; plane_resolve "$@" >/dev/null; printf '%s\n' "$WORKSPACE_DIR"
      ;;
    ensure-subdirs)
      shift; plane_resolve "$@" >/dev/null; plane_ensure_project_subdirs
      printf '%s\n' "$PROJECT_DIR"
      ;;
    latest-audit-dir)
      shift
      audit_name="${1:?missing audit-name}"; shift || true
      plane_resolve "$@" >/dev/null
      plane_latest_audit_dir "$audit_name"
      ;;
    *)
      cat >&2 <<USAGE
Usage:
  plane-runner.sh resolve [scope]
      Echo org/repo, export ORG/REPO/PROJECT_CWD/WORKSPACE_DIR/PROJECT_DIR.
  plane-runner.sh project-dir [scope]
      Echo \$PROJECT_DIR.
  plane-runner.sh workspace-dir [scope]
      Echo \$WORKSPACE_DIR.
  plane-runner.sh ensure-subdirs [scope]
      Create work-items/, cycles/, modules/, epics/, milestones/, pages/.
  plane-runner.sh latest-audit-dir <audit-name> [scope]
      Echo most recent audit dir for an audit-name (e.g. apple-security).
USAGE
      exit 2
      ;;
  esac
fi
