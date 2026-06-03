#!/usr/bin/env bash
# Source resolver + $AUDIT_DIR creator for the audit-prd skill.
#
# The audit-* family audits a *code tree*: audit-runner.sh takes a scope
# directory, derives <org>/<repo> from its git remote, and points codex at
# it. A PRD is a *document* — it can live as a local markdown file, a vault
# note, or a Forgejo wiki page, and may have no repo at all. This script is
# the document-shaped analogue of audit-runner.sh:
#
#   1. Resolve the PRD source (file | wiki) and FETCH its content.
#   2. Resolve <org>/<repo>:
#        - wiki        → the wiki's owning <owner>/<repo>
#        - file in git → that repo's <org>/<repo>
#        - loose file  → prd/<slug>
#   3. Create $AUDIT_DIR under ~/Reports/<org_repo>/audits/<TS>-prd/,
#      stage the PRD as $AUDIT_DIR/prd-source.md, and write MANIFEST.json
#      with project_cwd = $AUDIT_DIR so audit-codex.sh points codex at the
#      directory holding the PRD copy. audit-codex.sh and audit-verify.sh
#      then work unchanged.
#
# Usage:
#   prd-runner.sh init <path-to-prd.md>
#   prd-runner.sh init --wiki <owner>/<repo>:<PageName>
#
# Prints the resolved $AUDIT_DIR to stdout as the sole success signal.
set -euo pipefail

FORGEJO_URL="https://mac-mini.example:3000"
TEA_CONFIG="$HOME/Library/Application Support/tea/config.yml"

slugify() {
  # lower-case, non-alnum → '-', squeeze, trim. Caps length.
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' \
    | cut -c1-60
}

org_repo_from_remote() {
  # Mirror audit-runner.sh's host-agnostic <org>/<repo> extraction.
  local remote="$1"
  printf '%s' "$remote" | sed -E 's|\.git$||' | tr ':' '/' \
    | awk -F/ 'NF>=2 {print $(NF-1)"/"$NF}'
}

forgejo_token() {
  awk '/name: homelab/{f=1} f&&/token:/{print $2; exit}' "$TEA_CONFIG" 2>/dev/null
}

prd_init() {
  local source_kind source_ref org_repo prd_title prd_slug
  local is_vault staged_content report_ts
  is_vault="false"
  # One timestamp per run — names the audit dir under ~/Reports. The audit is
  # read-only on the PRD; the review is the local REPORT.md, nothing is written
  # back to the source.
  report_ts="$(date +%Y-%m-%dT%H-%M-%S)"

  if [[ "${1:-}" == "--wiki" ]]; then
    # ---- Forgejo wiki page ------------------------------------------------
    source_kind="wiki"
    source_ref="${2:?prd-runner: --wiki needs <owner>/<repo>:<PageName>}"
    local owner_repo page owner repo
    owner_repo="${source_ref%%:*}"
    page="${source_ref#*:}"
    owner="${owner_repo%%/*}"
    repo="${owner_repo#*/}"
    if [[ -z "$owner" || -z "$repo" || -z "$page" || "$page" == "$source_ref" ]]; then
      echo "prd-runner: --wiki ref must be <owner>/<repo>:<PageName>, got: $source_ref" >&2
      return 1
    fi
    local token
    token="$(forgejo_token)"
    if [[ -z "$token" ]]; then
      echo "prd-runner: no Forgejo token found in $TEA_CONFIG (see the forgejo skill)" >&2
      return 1
    fi
    # URL-encode spaces in the page name for the path segment.
    local page_enc
    page_enc="${page// /%20}"
    local api="$FORGEJO_URL/api/v1/repos/$owner/$repo/wiki/page/$page_enc"
    local json
    json="$(curl -sk -H "Authorization: token $token" "$api")" || {
      echo "prd-runner: wiki fetch failed: $api" >&2; return 1; }
    if ! printf '%s' "$json" | jq -e '.content_base64 // empty' >/dev/null 2>&1; then
      echo "prd-runner: wiki page not found or empty: $owner/$repo:$page" >&2
      echo "  API said: $(printf '%s' "$json" | jq -r '.message // .' 2>/dev/null | head -1)" >&2
      return 1
    fi
    staged_content="$(printf '%s' "$json" | jq -r '.content_base64' | base64 --decode)"
    org_repo="$owner/$repo"
    prd_title="$page"

  else
    # ---- Local markdown file (loose or vault note) ------------------------
    source_kind="file"
    source_ref="${1:?prd-runner: missing PRD file path}"
    if [[ ! -f "$source_ref" ]]; then
      echo "prd-runner: PRD file does not exist: $source_ref" >&2
      return 1
    fi
    source_ref="$(cd "$(dirname "$source_ref")" && pwd)/$(basename "$source_ref")"  # absolutize
    staged_content="$(cat "$source_ref")"

    # Title: first markdown H1, else the filename sans extension.
    prd_title="$(grep -m1 -E '^# ' "$source_ref" 2>/dev/null | sed -E 's/^#[[:space:]]+//')"
    [[ -z "$prd_title" ]] && prd_title="$(basename "${source_ref%.*}")"

    # Under the vault? Recorded in the manifest as source metadata.
    if [[ "$source_ref" == "$HOME/Vault/"* ]]; then
      is_vault="true"
    fi

    # org/repo: a tracked file uses its repo; a loose/vault file uses prd/<slug>.
    local toplevel remote
    toplevel="$(git -C "$(dirname "$source_ref")" rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -n "$toplevel" && "$is_vault" == "false" ]]; then
      remote="$(git -C "$toplevel" remote get-url upstream 2>/dev/null \
             || git -C "$toplevel" remote get-url origin   2>/dev/null || true)"
    fi
    if [[ -n "${remote:-}" ]]; then
      org_repo="$(org_repo_from_remote "$remote")"
    else
      org_repo="prd/$(slugify "$prd_title")"
    fi
  fi

  prd_slug="$(slugify "$prd_title")"

  local reports_base audit_dir
  reports_base="$HOME/Reports/$org_repo"
  audit_dir="$reports_base/audits/${report_ts}-prd"
  mkdir -p "$audit_dir/tooling-raw"

  # Stage the PRD content as the unit of audit.
  printf '%s\n' "$staged_content" > "$audit_dir/prd-source.md"
  if [[ ! -s "$audit_dir/prd-source.md" ]]; then
    echo "prd-runner: staged PRD is empty: $audit_dir/prd-source.md" >&2
    return 1
  fi

  # MANIFEST.json: same required keys as audit-runner.sh (project_cwd points
  # at the audit dir, which holds prd-source.md) plus PRD-specific extras.
  cat > "$audit_dir/MANIFEST.json" <<EOF
{
  "audit_name": "prd",
  "scope": "$source_ref",
  "org_repo": "$org_repo",
  "report_ts": "$report_ts",
  "audit_dir": "$audit_dir",
  "project_cwd": "$audit_dir",
  "source_kind": "$source_kind",
  "source_ref": "$source_ref",
  "prd_title": "$prd_title",
  "prd_slug": "$prd_slug",
  "is_vault": $is_vault,
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

  printf '%s\n' "$audit_dir"
}

if [[ "${BASH_SOURCE[0]:-}" == "${0}" ]]; then
  case "${1:-}" in
    init)
      shift
      prd_init "$@"
      ;;
    *)
      cat >&2 <<USAGE
Usage:
  prd-runner.sh init <path-to-prd.md>
  prd-runner.sh init --wiki <owner>/<repo>:<PageName>
      Resolves the PRD source, fetches its content into
      \$AUDIT_DIR/prd-source.md, creates \$AUDIT_DIR under
      ~/Reports/<org_repo>/audits/<TS>-prd/, writes MANIFEST.json,
      and prints the AUDIT_DIR path to stdout.
USAGE
      exit 2
      ;;
  esac
fi
