# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/`, build a brief orientation note. **Web SEO has optional Phase 1 tooling but no emergency-exit gate** — the only outgoing edge that ever fires here is `proceed`.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optional `$TARGET_URL` env var — a running URL of the site under audit. If set, runtime fetches (robots.txt, sitemap.xml, rendered-HTML structured data, Lighthouse SEO category) run against it. If unset, those are skipped and the audit becomes pure source-level.

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Run Phase 1 tooling

Technical SEO is largely render-aware, so the strongest checks need a running target. Run what's available, document what's missing in `STATUS.md`. **Never block on a missing tool.**

```bash
# Lighthouse SEO category (render-aware, requires TARGET_URL).
if [ -n "${TARGET_URL:-}" ] && command -v lighthouse >/dev/null; then
  ${TO:+$TO 600} lighthouse "$TARGET_URL" \
    --only-categories=seo \
    --output=json --output-path="$AUDIT_DIR/tooling-raw/lighthouse-seo.json" \
    --chrome-flags="--headless --no-sandbox" \
    --quiet 2>&1 | tee "$AUDIT_DIR/tooling-raw/lighthouse-seo.log" || true
elif [ -z "${TARGET_URL:-}" ]; then
  echo "⚠️ TARGET_URL not set — Lighthouse SEO scan skipped (set TARGET_URL=https://example.com to enable)" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
else
  echo "⚠️ lighthouse not installed (npm install -g lighthouse) — Lighthouse scan skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# robots.txt + sitemap reachability (requires TARGET_URL).
if [ -n "${TARGET_URL:-}" ] && command -v curl >/dev/null; then
  ORIGIN=$(printf '%s' "$TARGET_URL" | sed -E 's|^(https?://[^/]+).*|\1|')
  ${TO:+$TO 60} curl -fsSL "$ORIGIN/robots.txt" \
    -o "$AUDIT_DIR/tooling-raw/robots.txt" 2> "$AUDIT_DIR/tooling-raw/robots.log" || \
    echo "robots.txt fetch failed or absent at $ORIGIN/robots.txt" >> "$AUDIT_DIR/tooling-raw/robots.log"
  # Head of sitemap.xml (could be large; capture the first chunk for inspection).
  ${TO:+$TO 60} curl -fsSL "$ORIGIN/sitemap.xml" 2>/dev/null \
    | head -c 20000 > "$AUDIT_DIR/tooling-raw/sitemap-head.txt" || \
    echo "sitemap.xml fetch failed or absent at $ORIGIN/sitemap.xml" >> "$AUDIT_DIR/tooling-raw/sitemap-head.txt"
elif [ -z "${TARGET_URL:-}" ]; then
  echo "⚠️ TARGET_URL not set — robots.txt / sitemap.xml fetch skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# Rendered structured-data extraction (requires TARGET_URL).
if [ -n "${TARGET_URL:-}" ] && command -v curl >/dev/null; then
  ${TO:+$TO 60} curl -fsSL "$TARGET_URL" 2>/dev/null \
    | grep -ioE '<script[^>]*type=["'"'"']application/ld\+json["'"'"'][^>]*>.*' \
    > "$AUDIT_DIR/tooling-raw/structured-data.txt" 2>&1 || \
    echo "no JSON-LD found in initial HTML (or fetch failed) — may be JS-injected" \
      >> "$AUDIT_DIR/tooling-raw/structured-data.txt"
fi

# Source-level SEO artifact snapshot — what we're auditing.
{
  echo "=== Template / page files ==="
  find "$PROJECT_CWD" \( -name "*.html" -o -name "*.htm" -o -name "*.jsx" -o -name "*.tsx" \
    -o -name "*.vue" -o -name "*.svelte" -o -name "*.astro" \) \
    -not -path '*/node_modules/*' -not -path '*/.*' 2>/dev/null | head -200
  echo
  echo "=== robots.txt / sitemap sources in repo ==="
  find "$PROJECT_CWD" \( -iname "robots.txt" -o -iname "sitemap*.xml" -o -iname "robots.*" -o -iname "sitemap.*" \) \
    -not -path '*/node_modules/*' -not -path '*/.*' 2>/dev/null | head -50
  echo
  echo "=== Metadata / head management ==="
  grep -r -l -E "(<title|<meta name=\"description\"|og:|twitter:|rel=\"canonical\"|hreflang|application/ld\+json)" "$PROJECT_CWD" \
    --include="*.html" --include="*.jsx" --include="*.tsx" --include="*.vue" --include="*.svelte" --include="*.astro" \
    --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null | head -50
  echo
  echo "=== SEO library / framework metadata references ==="
  grep -r -l -E "(next-seo|react-helmet|@nuxtjs/seo|next/head|generateMetadata|svelte:head|astro-seo|nuxt-simple-sitemap)" "$PROJECT_CWD" \
    --include="*.js" --include="*.ts" --include="*.jsx" --include="*.tsx" --include="*.vue" --include="*.svelte" --include="*.json" \
    --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null | head -50
} > "$AUDIT_DIR/tooling-raw/seo-inventory.txt" 2>&1 || true
```

### 2. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious frontend/site sub-paths
- Framework detection: Next.js, Nuxt, SvelteKit, Astro, Remix, Gatsby, Hugo/Jekyll, plain HTML — and the **rendering mode** (SSR / SSG / CSR), since indexability hinges on it
- Existing SEO infrastructure (next-seo, react-helmet, sitemap/robots generators, structured-data helpers)
- Whether `$TARGET_URL` was set and which runtime fetches ran
- **If no site/frontend files found**: notify the user and bail. A technical-SEO audit on a non-web (e.g. native Apple, backend-only library) repo is a category error; do not continue.

This is for the user's situational awareness, not a persisted artifact.

### 3. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
scripts/walk.sh set --state "$STATE" --key target_url --value "${TARGET_URL:-}"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever tools were available
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools and missing `TARGET_URL`
- `$AUDIT_DIR/tooling-raw/seo-inventory.txt` exists (template/metadata/sitemap/robots inventory + SEO library refs)
- Walker state has `emergency_exit=0` and `target_url` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Always — web SEO has no emergency-exit condition.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- A scanner times out → captured in its `.log` file; orient proceeds. Phase 2 reviewers see the partial output.
- All tooling missing or `TARGET_URL` unset → `STATUS.md` documents the degradation; orient still proceeds. Phase 2 becomes pure source-level review. This is expected for many runs (no deployed/staging URL available).
- No site/frontend files in scope → bail with a category-error message pointing the user at `/audit-apple-*` if the repo is a native Apple project, or noting the audit is a no-op otherwise.
