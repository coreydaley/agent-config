# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/`, build a brief orientation note. **Web agent-accessibility has optional Phase 1 tooling but no emergency-exit gate** — the only outgoing edge that ever fires here is `proceed`.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)
- Optional `$TARGET_URL` env var — a running URL of the site under audit. If set, runtime fetches (robots.txt, `.well-known/*`, `/llms.txt`, no-JS HTML render) run against it as an agent would. If unset, those are skipped and the audit becomes pure source-level.

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Run Phase 1 tooling

This audit is about what an agent fetching the live site actually
receives, so the strongest signals need a running target. Run what's
available, document what's missing in `STATUS.md`. **Never block on a
missing tool.** Crucially, fetch **as a non-JS agent** (plain curl, no
browser) — that's the contract many crawlers operate under.

```bash
if [ -n "${TARGET_URL:-}" ] && command -v curl >/dev/null; then
  ORIGIN=$(printf '%s' "$TARGET_URL" | sed -E 's|^(https?://[^/]+).*|\1|')

  # robots.txt — the AI-crawler directive surface.
  ${TO:+$TO 60} curl -fsSL "$ORIGIN/robots.txt" \
    -o "$AUDIT_DIR/tooling-raw/robots.txt" 2> "$AUDIT_DIR/tooling-raw/robots.log" || \
    echo "robots.txt fetch failed or absent at $ORIGIN/robots.txt" >> "$AUDIT_DIR/tooling-raw/robots.log"

  # /llms.txt and /llms-full.txt — the emerging agent-manifest convention.
  {
    echo "=== /llms.txt ==="
    ${TO:+$TO 60} curl -fsSL "$ORIGIN/llms.txt" 2>/dev/null || echo "(absent or fetch failed)"
    echo
    echo "=== /llms-full.txt (head) ==="
    ${TO:+$TO 60} curl -fsSL "$ORIGIN/llms-full.txt" 2>/dev/null | head -c 8000 || echo "(absent or fetch failed)"
  } > "$AUDIT_DIR/tooling-raw/llms-txt.txt" 2>&1

  # .well-known descriptors agents look for.
  {
    for wk in security.txt ai-plugin.json mcp tdmrep.json host-meta; do
      echo "=== /.well-known/$wk ==="
      ${TO:+$TO 30} curl -fsSL "$ORIGIN/.well-known/$wk" 2>/dev/null | head -c 2000 || echo "(absent or fetch failed)"
      echo
    done
  } > "$AUDIT_DIR/tooling-raw/well-known.txt" 2>&1

  # What a non-JS agent sees: raw HTML, no browser execution.
  {
    echo "=== Raw HTML as fetched (no JS execution), first 30k chars ==="
    ${TO:+$TO 60} curl -fsSL -A "Mozilla/5.0 (compatible; agent-accessibility-audit)" "$TARGET_URL" 2>/dev/null | head -c 30000
  } > "$AUDIT_DIR/tooling-raw/nojs-render.txt" 2>&1 || \
    echo "live fetch failed for $TARGET_URL" >> "$AUDIT_DIR/tooling-raw/nojs-render.txt"

  # Probe whether a bot user-agent is treated differently (WAF / bot-management).
  {
    echo "=== Status with a generic UA ==="
    ${TO:+$TO 30} curl -s -o /dev/null -w "%{http_code}\n" -A "Mozilla/5.0" "$TARGET_URL" 2>/dev/null || echo "fetch failed"
    echo "=== Status with an AI-crawler UA (GPTBot) ==="
    ${TO:+$TO 30} curl -s -o /dev/null -w "%{http_code}\n" -A "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)" "$TARGET_URL" 2>/dev/null || echo "fetch failed"
    echo "=== Status with ClaudeBot UA ==="
    ${TO:+$TO 30} curl -s -o /dev/null -w "%{http_code}\n" -A "Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://www.anthropic.com/claude-bot)" "$TARGET_URL" 2>/dev/null || echo "fetch failed"
  } >> "$AUDIT_DIR/tooling-raw/nojs-render.txt" 2>&1
elif [ -z "${TARGET_URL:-}" ]; then
  echo "⚠️ TARGET_URL not set — robots.txt / .well-known / llms.txt / no-JS render fetches skipped (set TARGET_URL=https://example.com to enable; without it, WAF/render behavior cannot be observed)" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# Source-level inventory — what the repo declares.
{
  echo "=== robots / llms / ai.txt / tdmrep sources in repo ==="
  find "$PROJECT_CWD" \( -iname "robots.txt" -o -iname "robots.*" -o -iname "llms.txt" -o -iname "llms-full.txt" \
    -o -iname "ai.txt" -o -iname "tdmrep.json" -o -iname "security.txt" -o -iname "ai-plugin.json" \) \
    -not -path '*/node_modules/*' -not -path '*/.*/cache/*' 2>/dev/null | head -50
  echo
  echo "=== Feeds (RSS / Atom / JSON Feed) ==="
  find "$PROJECT_CWD" \( -iname "*.rss" -o -iname "feed.xml" -o -iname "atom.xml" -o -iname "feed.json" -o -iname "rss.xml" \) \
    -not -path '*/node_modules/*' 2>/dev/null | head -30
  grep -r -l -E "(application/rss\+xml|application/atom\+xml|application/feed\+json)" "$PROJECT_CWD" \
    --include="*.html" --include="*.tsx" --include="*.jsx" --include="*.vue" --include="*.svelte" --include="*.astro" \
    --exclude-dir=node_modules 2>/dev/null | head -20
  echo
  echo "=== API specs / programmatic surface (OpenAPI / GraphQL / MCP) ==="
  find "$PROJECT_CWD" \( -iname "openapi*.y*ml" -o -iname "openapi*.json" -o -iname "swagger*.y*ml" -o -iname "swagger*.json" \
    -o -iname "*.graphql" -o -iname "schema.graphql" -o -iname "mcp.json" \) \
    -not -path '*/node_modules/*' 2>/dev/null | head -30
  echo
  echo "=== Rendering mode signals (SSR vs CSR) ==="
  grep -r -l -E "(getServerSideProps|generateStaticParams|generateMetadata|renderToString|ReactDOMServer|astro|nuxt|sveltekit|next/document|prerender)" "$PROJECT_CWD" \
    --include="*.js" --include="*.ts" --include="*.tsx" --include="*.jsx" --include="*.vue" --include="*.svelte" --include="*.json" \
    --exclude-dir=node_modules 2>/dev/null | head -30
  echo
  echo "=== Licensing / content-use metadata ==="
  grep -r -l -E "(schema.org.*license|\"license\"|tdmrep|tdm-reservation|Google-Extended|noai|noimageai)" "$PROJECT_CWD" \
    --include="*.html" --include="*.json" --include="*.txt" --include="*.tsx" --include="*.jsx" \
    --exclude-dir=node_modules 2>/dev/null | head -30
} > "$AUDIT_DIR/tooling-raw/agent-inventory.txt" 2>&1 || true
```

### 2. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and the kind of site (content/marketing/docs/app/data)
- Framework + **rendering mode** (SSR / SSG / CSR) — the single biggest determinant of no-JS agent access
- What the repo declares: robots.txt AI directives, llms.txt, feeds, API spec, licensing files
- If `$TARGET_URL` was set: what the no-JS fetch returned (content vs empty shell), and whether the GPTBot/ClaudeBot UA probes returned a different status than a generic UA (a WAF signal)
- **Operator intent is not assumed.** If AI crawlers appear blocked, flag it as something to confirm, not automatically a defect.
- **If no site/frontend files found**: notify the user and bail. An agent-accessibility audit on a non-web repo is a category error; do not continue.

This is for the user's situational awareness, not a persisted artifact.

### 3. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
scripts/walk.sh set --state "$STATE" --key target_url --value "${TARGET_URL:-}"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever fetches/inventory ran
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped fetches and missing `TARGET_URL`
- `$AUDIT_DIR/tooling-raw/agent-inventory.txt` exists (robots/llms/feeds/API/licensing inventory + rendering-mode signals)
- Walker state has `emergency_exit=0` and `target_url` set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Always — web agent-accessibility has no emergency-exit condition.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- A fetch times out → captured in its `.log` / output file; orient proceeds. Phase 2 reviewers see the partial output.
- `TARGET_URL` unset → `STATUS.md` documents the degradation; orient still proceeds. Phase 2 becomes source-level only — but note that WAF/CDN bot-blocking and the true no-JS render **cannot** be observed without a live fetch, so flag that limitation prominently.
- No site/frontend files in scope → bail with a category-error message.
