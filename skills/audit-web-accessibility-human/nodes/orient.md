# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/`, build a brief orientation note. **Web accessibility has optional Phase 1 tooling but no emergency-exit gate** — the only outgoing edge that ever fires here is `proceed`.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optional `$TARGET_URL` env var — a running URL of the app under audit. If set, automated DOM-aware scanners (axe-core, pa11y, Lighthouse) run against it. If unset, scanners are skipped and the audit becomes pure source-level.

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Run Phase 1 tooling

Web-a11y SAST is largely DOM-aware, so the strongest tools need a running target. Run what's available, document what's missing in `STATUS.md`. **Never block on a missing tool.**

```bash
# axe-core CLI (DOM-aware, requires TARGET_URL). Best-in-class for runtime a11y.
if [ -n "${TARGET_URL:-}" ] && command -v axe >/dev/null; then
  ${TO:+$TO 300} axe "$TARGET_URL" \
    --save "$AUDIT_DIR/tooling-raw/axe.json" \
    --tags wcag2a,wcag2aa,wcag21a,wcag21aa,wcag22aa \
    2>&1 | tee "$AUDIT_DIR/tooling-raw/axe.log" || true
elif [ -z "${TARGET_URL:-}" ]; then
  echo "⚠️ TARGET_URL not set — axe-core scan skipped (set TARGET_URL=http://localhost:3000 to enable)" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
else
  echo "⚠️ axe CLI not installed (npm install -g @axe-core/cli) — axe scan skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# pa11y (DOM-aware, requires TARGET_URL). HTML_CodeSniffer + axe rules.
if [ -n "${TARGET_URL:-}" ] && command -v pa11y >/dev/null; then
  ${TO:+$TO 300} pa11y --reporter json --standard WCAG2AA "$TARGET_URL" \
    > "$AUDIT_DIR/tooling-raw/pa11y.json" 2> "$AUDIT_DIR/tooling-raw/pa11y.log" || true
elif [ -z "${TARGET_URL:-}" ]; then
  : # already noted under axe
else
  echo "⚠️ pa11y not installed (npm install -g pa11y) — pa11y scan skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# Lighthouse (DOM-aware, requires TARGET_URL). Captures the accessibility category.
if [ -n "${TARGET_URL:-}" ] && command -v lighthouse >/dev/null; then
  ${TO:+$TO 600} lighthouse "$TARGET_URL" \
    --only-categories=accessibility \
    --output=json --output-path="$AUDIT_DIR/tooling-raw/lighthouse.json" \
    --chrome-flags="--headless --no-sandbox" \
    --quiet 2>&1 | tee "$AUDIT_DIR/tooling-raw/lighthouse.log" || true
elif [ -z "${TARGET_URL:-}" ]; then
  : # already noted under axe
else
  echo "⚠️ lighthouse not installed (npm install -g lighthouse) — lighthouse scan skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# Source-level frontend artifact snapshot — what we're auditing.
{
  echo "=== HTML files ==="
  find "$PROJECT_CWD" \( -name "*.html" -o -name "*.htm" \) -not -path '*/node_modules/*' -not -path '*/.*' 2>/dev/null
  echo
  echo "=== Component files ==="
  find "$PROJECT_CWD" \( -name "*.jsx" -o -name "*.tsx" -o -name "*.vue" -o -name "*.svelte" -o -name "*.astro" \) \
    -not -path '*/node_modules/*' -not -path '*/.*' 2>/dev/null
  echo
  echo "=== Existing a11y tooling references ==="
  grep -r -l -E "(axe-core|jest-axe|cypress-axe|pa11y|lighthouse|@axe-core)" "$PROJECT_CWD" \
    --include="*.json" --include="*.js" --include="*.ts" --include="*.yml" --include="*.yaml" \
    --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null | head -50
} > "$AUDIT_DIR/tooling-raw/frontend-inventory.txt" 2>&1 || true
```

### 2. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious frontend sub-paths
- Framework detection: React, Vue, Svelte, Angular, Astro, Next.js, Remix, plain HTML
- Existing a11y test infrastructure (jest-axe, cypress-axe, axe playwright, Storybook a11y addon)
- Whether `$TARGET_URL` was set and which DOM scanners ran
- **If no frontend files found**: notify the user and bail. Web accessibility audit on a non-frontend repo is a category error; do not continue.

This is for the user's situational awareness, not a persisted artifact.

### 3. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
scripts/walk.sh set --state "$STATE" --key target_url --value "${TARGET_URL:-}"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever tools were available
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools and missing `TARGET_URL`
- `$AUDIT_DIR/tooling-raw/frontend-inventory.txt` exists (HTML/component file list + existing a11y tooling refs)
- Walker state has `emergency_exit=0` and `target_url` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Always — web-a11y has no emergency-exit condition.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- A scanner times out → captured in its `.log` file; orient proceeds. Phase 2 reviewers see the partial output.
- All tooling missing or `TARGET_URL` unset → `STATUS.md` documents the degradation; orient still proceeds. Phase 2 becomes pure source-level review. This is expected for many runs (no dev server available, audit happening offline).
- No frontend files in scope → bail with a category-error message pointing the user at `/audit-apple-accessibility` if the repo is a native Apple project, or noting the audit is a no-op otherwise.
