# Node: orient

Phase 1 of the framework — pure-LLM audit. Web responsive design has **no automated tooling** in this pipeline (no responsive-design linter is universally reliable; tools like Percy/Chromatic/BrowserStack are visual-regression services that require a deployed app, not source-time SAST). Still create `$AUDIT_DIR/tooling-raw/STATUS.md` so downstream nodes see a consistent shape.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
```

## Steps

### 1. Record the no-tooling status

```bash
cat > "$AUDIT_DIR/tooling-raw/STATUS.md" <<EOF
# tooling-raw — web-responsive

No automated tooling runs in this audit. Web responsive design is a
pure-LLM review.

If the project uses any of the following, reviewers should note their
existence in findings (defer to or reference them, do not duplicate):
- Percy, Chromatic — visual regression on real browsers
- BrowserStack, Sauce Labs, LambdaTest — cross-device test farms
- Storybook with @storybook/addon-viewport — component-level viewport
  preview
- Playwright / Cypress viewport tests — runtime breakpoint assertions
- Lighthouse / WebPageTest mobile audits — performance + responsive
  hints (out of scope for this audit's findings, but worth noting)

These are runtime tools; this audit is source-time and complements,
does not replace, them.
EOF
```

### 2. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious sub-paths (`src/`, `app/`, `components/`, `styles/`)
- Frontend files present: HTML/templates (`.html`, `.htm`, `.erb`, `.haml`, `.slim`, `.jinja`, `.twig`), CSS/preprocessor (`.css`, `.scss`, `.sass`, `.less`, `.styl`), component files (`.jsx`, `.tsx`, `.vue`, `.svelte`, `.astro`)
- Detected CSS framework and version (Bootstrap, Tailwind, Foundation, Bulma, Material UI, Chakra UI, etc.) — affects breakpoint naming conventions
- Custom breakpoint tokens or design-system breakpoints (look for `breakpoints.ts`, Tailwind `theme.screens`, Bootstrap `$grid-breakpoints`, etc.)
- Viewport meta tag presence in primary entry HTML

**If no frontend files found**: notify and stop. Do not create reviewer artifacts. `$AUDIT_DIR/tooling-raw/STATUS.md` should record this. Walker still transitions to `independent_reviews` so the verify gate fires and the user gets a clear "scope had nothing to review" terminal message.

### 3. Persist run-scoped state

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
```

Web responsive design has **no emergency-exit condition** — no equivalent of a live credential leak. The `emergency_exit` outgoing edge from this node is never taken for this audit.

## Outputs

- `$AUDIT_DIR/tooling-raw/STATUS.md` exists
- Walker state has `emergency_exit=0`

## Outgoing edges

- **`proceed`** → `independent_reviews`. The only path. Web responsive has no emergency trigger.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No frontend files at all → STATUS.md records it; proceed to `independent_reviews` anyway. Reviewers will produce a near-empty findings table and the report will surface "scope had no frontend code."
- Mixed monorepo where only part of the scope is frontend → reviewers narrow to the frontend sub-paths in Phase 2; this node doesn't pre-filter.
