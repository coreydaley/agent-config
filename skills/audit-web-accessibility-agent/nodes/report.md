# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` using the baseline P0/P1/Deferred mapping.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Web agent-accessibility sprint mapping (baseline)

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

There is no "Immediate Action" tier. But a Critical finding where a WAF
silently blocks agents the operator *intends* to serve is config-level
and usually a fast fix — call it out as such in the task body.

**Intent gate before any P0/P1 task.** Findings whose `Intent` is
`Ambiguous` (a block that may be deliberate) do NOT become remediation
tasks. They go into a dedicated **"Confirm Operator Intent"** section.
Only after the operator confirms agent access is desired do they
convert to tasks. Never auto-generate a task that opens content the
operator may have deliberately reserved.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 6 (CrawlerDirectives, LlmsTxt, MachineReadable, ProgrammaticAccess, Addressability, Licensing)
- **Intent** — `Blocks` | `Degrades` | `Missing` (Ambiguous items live in the Confirm-Intent section, not here)
- **Location** — `path/to/robots.txt:line`, the WAF/CDN rule, the route/template, or the live URL pattern (never just "the site")
- **Verification mode** — `code` (inspectable from source/repo config) or `runtime` (requires a live fetch as an agent — WAF behavior, no-JS render, what `/llms.txt` serves)
- **Issue** — clear description
- **Remediation** — concrete and specific (never "make it agent-friendly"). Name the file/rule/format. Respect stated licensing — don't recommend opening reserved content.
- **Verification step** — for `code` items: a static check (the directive present, the spec served at the path). For `runtime` items: an explicit live check (e.g. "curl with `-A 'ClaudeBot/1.0'` returns 200, not 403"; "curl with JS disabled shows the article body in the raw HTML"; "`/llms.txt` resolves and its links 200").

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — web-agent-accessibility — <scope>, <date>`
- Task description: scope covered, 6 categories reviewed, tooling that ran, framework + rendering mode, whether agent access is a stated goal, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Web Agent-Accessibility Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, site type, framework + rendering mode
(SSR/SSG/CSR), whether agent/LLM access appears to be a stated goal,
tooling summary (robots / llms.txt / .well-known / no-JS render / UA
probes if they ran, or "no TARGET_URL — source-level only, so WAF and
true render behavior could not be observed"), total findings by
severity, top 3 issues, and the audit's inherent limitation: without a
live fetch, CDN/WAF bot-blocking and the real no-JS render cannot be
confirmed.>

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Intent | Count |
|---|---|
| Blocks | N |
| Degrades | N |
| Missing | N |
| Ambiguous (confirm intent) | N |

| Category | Count |
|---|---|
<non-zero categories only — CrawlerDirectives, LlmsTxt, MachineReadable,
ProgrammaticAccess, Addressability, Licensing>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (robots.txt, llms-txt, well-known, nojs-render, agent-inventory)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Confirm Operator Intent

<Every Ambiguous finding — a block/restriction that may be deliberate.
Phrase each as a question the operator answers before it becomes a task.
Example: "robots.txt Disallows CCBot. Intentional (opt out of Common
Crawl) or accidental? If you want Common Crawl ingestion, this blocks
it.">

## Implementation Plan

### P0 — Must Ship

<one block per Critical and High finding whose intent is confirmed
Blocks/Degrades/Missing>

**Task: S### — <Category> / <Intent> — <Title>**
- Location: `path/to/robots.txt:line` / WAF rule / route / URL pattern
- Category: <one of the 6>
- Intent: <Blocks | Degrades | Missing>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix; name the file/rule/format; respect stated licensing>
- Verification step: <static check for `code`; live UA/no-JS/llms fetch for `runtime`>

### P1 — Ship If Capacity Allows

<one block per Medium finding, same format>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] Operator intent confirmed for every Ambiguous item (each either
      converted to a task or explicitly accepted as deliberate)
- [ ] All P0 tasks completed and verified
- [ ] Each `code`-verification task confirmed via source diff (directive
      present, spec served at the path)
- [ ] Each `runtime`-verification task confirmed via a live fetch with
      the relevant agent user-agent (e.g. ClaudeBot/GPTBot UA returns
      200; no-JS curl shows the content; /llms.txt resolves)
- [ ] No content the operator deliberately reserved was opened by a
      remediation
- [ ] robots.txt, WAF rules, meta directives, and stated terms are
      mutually consistent after the changes

## Sensitive-content warning

This report may reference internal file paths, WAF/CDN rule names, and
unpublished URLs. Treat as confidential before sharing externally.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
- Intermediate files: `$AUDIT_DIR/{claude,synthesis,devils-advocate}.md`

## Hand-off note

Findings marked `runtime` require a live fetch as an agent to confirm —
source inspection alone cannot prove WAF behavior, the real no-JS
render, or what `/llms.txt` serves. And before remediating any block,
confirm the operator actually wants the agent served: blocking AI
crawlers is often a deliberate, legitimate choice.
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
- Every finding is Ambiguous (intent unclear) → the Implementation Plan may be empty while the Confirm-Operator-Intent section is full; that's a valid outcome. Still transition to `verify` (REPORT.md is non-empty).
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body.
