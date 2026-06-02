# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` using the baseline P0/P1/Deferred mapping.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Web-SEO sprint mapping (baseline)

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Web SEO has no "Immediate Action" tier — there's no analog to pulling a TestFlight build. But a Critical **Indexation** finding (e.g. a `noindex` or `Disallow: /` leaking to production) is the closest thing: it actively de-indexes the live site and should be flagged as block-deploy / hotfix in the task body even though it folds into P0. Call this out in the hand-off so it's scheduled first.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 10 (Crawlability, Rendering, Metadata, StructuredData, Social, CoreWebVitals, URLArchitecture, Mobile, International, Duplication)
- **Signal** — `Indexation` | `Ranking` | `RichResult` | `Discovery`
- **Location** — `path/to/template.tsx:line` or `path/to/page.html:line` or the route/URL pattern (never just a page name)
- **Verification mode** — `code` (inspectable from source) or `runtime` (requires a built/rendered page, live URL, or Search Console data)
- **Issue** — clear description of the problem
- **Remediation** — concrete, specific (never "fix SEO"). Cite the tag/config/schema.org type and the Google guideline where applicable.
- **Verification step** — for `code` items: a static check (the tag present in the template, a sitemap-generator test). For `runtime` items: an explicit check (e.g. "Google Rich Results Test on the product URL confirms Product markup validates"; "URL Inspection in Search Console shows the page renders with content"; "PageSpeed Insights field data shows LCP < 2.5s").

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — web-seo — <scope>, <date>`
- Task description: scope covered, 10 categories reviewed, tooling that ran, framework + rendering mode, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Web SEO Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, framework + rendering mode (SSR/SSG/CSR),
tooling summary (Lighthouse SEO / robots / sitemap / structured-data
if they ran, or "no TARGET_URL — source-level audit only"), total
findings by severity, top 3 issues, reminder of audit's inherent
limitations: static code review cannot fully validate what Googlebot
sees after render, actual indexation status, or Core Web Vitals field
data without runtime testing and Search Console; not a guarantee of
rankings.>

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Signal | Count |
|---|---|
| Indexation | N |
| Ranking | N |
| RichResult | N |
| Discovery | N |

| Category | Count |
|---|---|
<non-zero categories only — Crawlability, Rendering, Metadata,
StructuredData, Social, CoreWebVitals, URLArchitecture, Mobile,
International, Duplication>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (lighthouse-seo, robots.txt, sitemap-head, structured-data, seo-inventory)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/codex.md           <or "MISSING — single-agent run" if codex_status=failed>
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding; flag Critical Indexation
findings as block-deploy / hotfix>

**Task: S### — <Category> / <Signal> — <Title>**
- Location: `path/to/template.tsx:line` or route/URL pattern
- Category: <one of the 10>
- Signal: <Indexation | Ranking | RichResult | Discovery>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix; cite tag/config/schema.org type + Google guideline>
- Verification step: <static check for `code`; Rich Results Test / URL Inspection / PSI for `runtime`>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Each `code`-verification task confirmed via source diff or a
      sitemap/metadata generator test
- [ ] Each `runtime`-verification task confirmed via the specified
      tool (Google Rich Results Test, URL Inspection / Search Console,
      PageSpeed Insights field data)
- [ ] No new Indexation regressions introduced by the remediations
      (no accidental noindex / canonical / robots change)
- [ ] Structured-data changes validate in the Rich Results Test with
      no errors
- [ ] If a deployed URL is available, a post-fix crawl confirms the
      previously-failing checks now pass

## Sensitive-content warning

This report may reference internal file paths, route patterns, or
unpublished URLs. Treat as confidential. Some remediation suggestions
may quote user-visible copy or unreleased page structure; check before
sharing externally.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
- Intermediate files: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`

## Hand-off note

Findings marked `runtime` require a built/rendered page or
Search Console data to confirm the fix — source inspection alone is
not sufficient for rendered structured data, soft-404 status, actual
indexation, or Core Web Vitals field data. Schedule Critical
Indexation findings first; they de-index the live site until fixed.
```

## Outputs

- `$AUDIT_DIR/REPORT.md` exists, non-empty, contains the Implementation Plan with appropriate tiers populated

## Outgoing edges

- → `verify` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from report --to verify
```

## Failure modes

- Synthesis has zero findings → produce the single-task no-findings report; still transition to `verify`.
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
