# Audit Framework

Canonical 5-phase pattern shared by every `audit-*` subagent. Each
audit's own SKILL file specifies only the audit-specific bits
(categories, severity rubric, Phase 1 tooling, Phase 2 review prompts,
schema extensions, sprint-mapping overrides). Everything common —
codex flags, output directory layout, dual-agent verification, synthesis
shape, devil's advocate shape, report shape, hand-off — lives here.

If you're authoring or modifying an audit subagent, this file is the
source of truth. The audit file lists only its deltas from this
baseline.

If you're modifying this file, also re-check that every audit subagent
still reads sensibly when combined with the framework. The drift list
in [`codex-invocation.md`](codex-invocation.md) names them all.

---

## Naming convention

| Prefix | Meaning |
|---|---|
| `audit-apple-<topic>` | Specific to native Apple platforms (iOS, iPadOS, macOS, watchOS, tvOS, visionOS, Mac Catalyst). Anchored to Apple HIG / Apple developer docs / App Review Guidelines |
| `audit-web-<topic>` | Specific to web frontends and/or backend services that serve HTTP. Anchored to WCAG / OWASP / web standards |
| `audit-<topic>` (no platform) | Platform-agnostic. Works for any codebase regardless of stack |

When a new audit could plausibly apply to either platform, prefer
splitting into `audit-apple-<topic>` and `audit-web-<topic>` rather
than one diluted audit covering both. The vocabularies, tooling, and
review standards are usually different enough that a unified audit
under-serves both sides.

---

## The 5-phase pattern

Every audit follows this shape:

| Phase | Goal | Output |
|---|---|---|
| 1. Orient | Validate scope, determine output location, optionally run tooling, optionally emergency-exit, survey the scope | Orientation note (3-8 bullets) + populated `$AUDIT_DIR` with `tooling-raw/` (if applicable) and `EMERGENCY.md` (if triggered) |
| 2. Independent Reviews | Claude and Codex review in parallel without cross-contamination, both grounded in tooling output if present | `$AUDIT_DIR/claude.md` and `$AUDIT_DIR/codex.md` |
| 3. Synthesis | Deduplicate findings; agreement raises confidence (not severity); calibrate severity; identify compound findings | `$AUDIT_DIR/synthesis.md` |
| 4. Devil's Advocate | Codex attacks the synthesis for false positives, severity miscalibrations, missing findings | `$AUDIT_DIR/devils-advocate.md` + incorporated challenges in synthesis |
| 5. Report Output | Produce sprint-able findings report with P0/P1/Deferred tiering (and `Immediate Action` above P0 for audits where it applies) | `$AUDIT_DIR/REPORT.md` + user hand-off |

---

## What each audit specifies

The audit's SKILL file must specify:

| Section | What it adds |
|---|---|
| `name`, `description` | Frontmatter. Description must include cross-references to sibling audits where overlap exists |
| **Schema extensions** | Columns added to the baseline finding schema (e.g. `WCAG`/`Level` for accessibility-web, `CWE/OWASP` for security-web, `Platform` for apple-*) |
| **Categories** | Named buckets findings fall into. Used for grouping in the report |
| **Severity calibration** | Anchored examples per severity tier specific to this audit's domain |
| **Phase 1 tooling** | Tools to run in `$AUDIT_DIR/tooling-raw/` (optional — some audits are LLM-only) |
| **Emergency-exit conditions** | When Phase 1 should halt the audit (optional — only for security/privacy audits) |
| **Phase 2 review prompts** | The Codex prompt body + the Claude review checklist (mirrors of each other in content, different in framing) |
| **Compound findings patterns** | Examples of chained exploits / interactions that the synthesis should look for (optional — primarily security/privacy) |
| **Sprint mapping overrides** | If the audit's domain treats Critical differently (e.g. security uses "Immediate Action" above P0) |
| **Output checklist additions** | Audit-specific verifications beyond the framework baseline |
| **References** | Standards, specs, tooling docs |

Everything else inherits this file.

---

## Finding schema baseline

Every audit's intermediate files (`claude.md`, `codex.md`,
`synthesis.md`) use a table with **at minimum** these columns:

```
| ID | Severity | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes |
```

Individual audits add extension columns to anchor findings to a
standard (e.g. `WCAG` + `Level` + `Verification` for accessibility-web;
`CWE/OWASP` + `Category` for security-web; `API/Standard` + `Platform`
for accessibility-apple).

`synthesis.md` additionally has a `Sources` column listing the source
review IDs each unified finding merges (e.g. `A002, C003`).

### ID prefix convention

| Prefix | Source |
|---|---|
| `A001`, `A002`... | Claude's independent review (Audit) |
| `C001`, `C002`... | Codex's independent review |
| `S001`, `S002`... | Synthesis canonical IDs |

### Severity levels

All audits use the same four-tier severity scale:

| Severity | Meaning (general) |
|---|---|
| Critical | Stop-the-line; out-of-band fix; cannot ship |
| High | Must ship in the next planned release |
| Medium | Ship if capacity allows |
| Low | Defer; informational; defense-in-depth |

Severity is assessed on **evidence**, not impression:

- **Impact** — what does an exploit / failure achieve?
- **Exploitability** / **Reachability** — what attacker capability /
  user journey is required?
- **Blast radius** — how many users / systems / records are affected?
- **Compensating controls** — what's already mitigating this?

Agreement between reviewers raises **confidence**, not severity.
Severity is also independent of remediation cost.

Each audit's SKILL file provides anchored examples per tier specific
to its domain. The anchors are starting points; reviewers override
based on the four factors above.

---

## Phase 1: Orient

### Step 1 — Validate and resolve scope

The audit subagent receives a scope path (or paths) in its input
prompt. The orchestrator (Claude running the audit) must:

- If no path is specified: scope is the current working directory
- If a path is provided: verify it exists via filesystem check
- Multiple space-separated paths supported; store each resolved
- If `--diff-only` is in the prompt: scope is files changed in
  `git diff main...HEAD` (or `upstream/main...HEAD` if `upstream`
  remote exists)
- Exclude common build/dependency directories unless the audit's SKILL
  file explicitly includes them (audits specify their own exclude lists
  but always exclude at minimum: `build/`, `dist/`, `node_modules/`,
  `vendor/`, `.build/`, `DerivedData/`, generated files, binary assets)
- **Store the resolved scope path** — never use raw input text in any
  Codex exec prompt string

### Step 2 — Determine output location

```bash
REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
REPORTS_BASE="$HOME/Reports/$ORG_REPO"
REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
AUDIT_DIR="$REPORTS_BASE/audits/$REPORT_TS-<AUDIT_NAME>"
PROJECT_CWD="$(pwd)"
mkdir -p "$AUDIT_DIR"
```

`<AUDIT_NAME>` is the audit's short identifier (e.g. `security-web`,
`apple-accessibility`, `test-coverage`). Each audit specifies its own.

`$AUDIT_DIR` holds every artifact for this run. `$PROJECT_CWD` is what
Codex uses as `-C` — the project root, regardless of which sub-path is
in scope.

### Step 3 — Tooling (optional, per-audit)

Audits that benefit from real tooling (security, test-coverage,
privacy) include a Phase 1 tooling step that runs language- or
domain-appropriate tools and writes raw output to
`$AUDIT_DIR/tooling-raw/` plus a `STATUS.md` documenting what ran and
what didn't.

Pattern:

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"

command -v <tool> >/dev/null && \
  timeout <seconds> <tool> <args> \
    > "$AUDIT_DIR/tooling-raw/<tool>.log" 2>&1
```

Tools that aren't installed, aren't applicable, or fail: record a line
in `$AUDIT_DIR/tooling-raw/STATUS.md` and continue. **Never block the
audit on a missing tool** — reviewers must be told what's missing but
proceed.

Audits document the specific tools they attempt in their own SKILL
file. Pure-LLM audits (architecture, design) skip this step.

### Step 4 — Emergency exit (optional, per-audit)

Some audits have conditions that warrant halting the audit before
Phase 2:

- **`audit-web-security` / `audit-apple-security`**: live credentials
  found in source (`gitleaks` match on a recognized prefix like `ghp_`,
  `sk_live_`, `AKIA`, private key blocks)
- **`audit-apple-privacy`**: third-party SDK detected that ships
  without a Privacy Manifest while accessing tracked data (App Store
  rejection imminent — fix before continuing)

When triggered:

1. **HALT the audit immediately**. Do not proceed to Phase 2.
2. Write `$AUDIT_DIR/EMERGENCY.md` describing what triggered the
   exit, what needs to happen, and any rotation/remediation steps.
3. Tell the user out-of-band — this is not a finding for the next
   sprint; this is a "now" event.
4. Only resume the full audit after the user confirms remediation is
   underway.

Audits without emergency-exit conditions skip this step.

### Step 5 — Survey

Audit-specific survey of the scope:

- Recent changes: `git log --oneline -10` (or `-20` for security audits
  where recent changes are weighted heavily)
- Trust boundaries and entry points (per audit's domain)
- Files of special interest (config, manifests, entitlements, etc.)

### Orient deliverable

A brief orientation note (3-8 bullets) covering:

- Resolved scope and what it includes/excludes
- Detected languages, frameworks, target platforms
- Tooling that ran successfully vs. tooling missing (if Phase 1 ran tools)
- Whether the emergency-exit triggered (if applicable)
- Audit output directory (`$AUDIT_DIR`)
- Any immediately obvious high-priority areas

---

## Phase 2: Independent Reviews (Parallel)

Two reviewers, in parallel, with no cross-contamination. Codex runs in
a background `codex exec` invocation; Claude (the orchestrator
walking the audit) runs the same review concurrently. Both write to
separate files; Claude does not read Codex's file until Phase 3.

### Step 1 — Launch Codex in background

The canonical Codex invocation pattern — non-negotiable, see
[`codex-invocation.md`](codex-invocation.md) for per-flag rationale:

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "<audit-specific review prompt>" \
  < /dev/null
```

- `-s workspace-write` — codex needs write access to its sub-process
  sandbox
- `--add-dir "$AUDIT_DIR"` — `$AUDIT_DIR` lives under `~/Reports/`,
  outside the workspace, so it needs explicit write access
- `-C "$PROJECT_CWD"` — codex reads code from the project root, not
  whatever subdir is in scope
- `--` — end option processing; the prompt is the next positional arg
- `< /dev/null` — codex's `exec` mode reads stdin even when a prompt
  is provided; without `< /dev/null` in non-TTY contexts (the Agent
  tool is one), codex hangs forever waiting for stdin

Each audit's SKILL file specifies the prompt body (categories,
severity rubric, schema columns). The framework provides the
invocation shell.

### Step 2 — Verify the Codex artifact

The most common Codex failure mode is silent (sandbox denial, missing
flag, prompt parse error). After the background Codex job returns,
verify the artifact:

```bash
[[ -s "$AUDIT_DIR/codex.md" ]] && grep -q '|.*|.*|' "$AUDIT_DIR/codex.md" \
  || echo "⚠️ Codex did not produce a usable $AUDIT_DIR/codex.md"
```

If verification fails: inspect the Codex stderr output, fix the issue
if identifiable, and re-run the command **once**. Only after a second
failure should you accept the single-agent degradation documented in
Phase 3.

### Step 3 — Claude's independent review (simultaneous)

While Codex runs, Claude writes its own independent review to
`$AUDIT_DIR/claude.md` using the same finding schema (ID prefix `A`).
Each audit's SKILL file specifies the review categories — Claude's
checklist mirrors Codex's prompt in content.

If `$AUDIT_DIR/tooling-raw/` is present, Claude reads it first.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

### Synthesis steps

1. **Verify both reviews exist and are non-empty**
   - If Phase 2 Step 2 already triggered a single-agent fallback, the
     synthesis warning was already decided there
   - Otherwise: check both files contain at least one finding row
   - If one is missing or empty: add a warning at the top of
     `$AUDIT_DIR/synthesis.md`:
     `⚠️ Single-agent synthesis — [agent] review was unavailable. Coverage may be incomplete.`

2. **Deduplicate findings**
   - Compare both reviews for overlapping findings
   - When the same issue appears in both, merge into one synthesis row
     and note both source IDs in the `Sources` column (e.g. `A002, C003`)
   - When merging: preserve the most specific `Location` and the best
     `Evidence/Notes`. Preserve the most specific extension-column
     values (e.g. if one says `iOS,iPadOS` and the other says `iOS`,
     keep the broader)
   - Do not flatten two findings into one if they have different
     exploit preconditions or affected assets
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity**
   - Re-evaluate severity using the audit's anchored examples plus the
     four factors (impact, exploitability, blast radius, compensating
     controls)
   - Do not automatically escalate severity because both reviewers
     flagged the same issue

4. **Identify compound findings** (audits that opt in)
   - Scan unified findings for pairs/chains that combine into a worse
     exploit than any single finding represents
   - Add a `Compound Findings` section to `synthesis.md` documenting
     which IDs compound, the resulting impact, and the effective
     combined severity

5. **Write synthesis** to `$AUDIT_DIR/synthesis.md`:

   ```markdown
   # <Audit Name> Synthesis — [REPORT_TS]

   ## Scope
   [Resolved scope path(s); note --diff-only if used]

   [Optional: audit-specific context section — Target Platforms,
   Tooling Summary, Capability Surfaces, etc.]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - By category: [non-zero categories only]
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | [extension columns] | Title | Location | Why It Matters | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|---------------------|-------|----------|----------------|-----------------|----------------|---------|
   | S001 | ... | ... | ... | ... | ... | ... | ... | A001, C002 |

   [Optional: Compound Findings section]

   ## Findings Present in Only One Review
   [Uncorroborated findings with rationale for retaining or dropping]
   ```

Phase 3 is complete when `$AUDIT_DIR/synthesis.md` is written.

---

## Phase 4: Devil's Advocate

Codex attacks the synthesis for false positives, severity
miscalibrations, missed findings, and (where applicable) missed
compound paths.

### Step 1 — Launch Codex devil's advocate

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "<audit-specific devil's advocate prompt>" \
  < /dev/null
```

Each audit's SKILL file specifies the prompt body — what categories of
attack to consider, what false-positive shapes are common in the
domain, what missed-finding types to look for, what makes a remediation
incomplete in this domain.

After the call, verify the artifact:

```bash
[[ -s "$AUDIT_DIR/devils-advocate.md" ]] || echo "⚠️ Codex devil's advocate produced no output"
```

### Step 2 — Incorporate valid challenges

Once `$AUDIT_DIR/devils-advocate.md` is written, the orchestrator:

- **Removes** confirmed false positives from the working finding list
- **Recalibrates** severity where the challenge is valid
- **Adds** genuinely missed findings with new synthesis IDs
- **Adds** missed compound paths (audits that opt in)
- **Documents every rejected challenge** in a section at the bottom
  of `synthesis.md`:

  ```markdown
  ## Rejected Devil's Advocate Challenges

  | Finding/Claim | Reason Rejected |
  |---|---|
  | [Claim from devil's advocate] | [Why it was not accepted] |
  ```

Phase 4 is complete when challenges are incorporated and rejections
are documented.

---

## Phase 5: Report Output

### Sprint mapping baseline

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Audits whose domains treat Critical operationally differently from
High **override** this with their own table. Currently:

- **`audit-web-security`** / **`audit-apple-security`** /
  **`audit-apple-privacy`**: Critical → "**Immediate Action — fix
  before next deploy / out-of-band patch**" (separate section above
  P0), High → P0
- **`audit-apple-app-store-review`**: any finding that triggers App
  Review rejection → "**Submission Blocker**" section above P0

### Per-task contents

Each sprint task must include:

- Finding ID (from synthesis)
- File and line reference where applicable
- All audit-specific anchor columns (CWE / WCAG / API/Standard /
  Pattern/Principle / Platform / etc.)
- Clear description of the issue
- Concrete, specific remediation step (never just "fix the issue")
- **Verification step**: how to confirm the fix is correct. For
  security/privacy audits this should be a *negative test* (try the
  exploit / unsupported behavior, confirm it fails). For accessibility
  this often requires runtime tooling. "Manual review confirms" is
  insufficient for any audit.

### No-findings case

If the synthesis contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — [scope], [date]`
- The task description must document: scope covered, categories
  reviewed, tooling that ran (if applicable), date of review, reviewer
  agents
- Do not produce an empty sprint

### Report template

```markdown
# <Audit Name> — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: scope, tooling summary if applicable, total findings
by severity, top 3 issues. Remind the reader of the audit's inherent
limitations.]

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

[Optional: Category breakdown table]

Intermediate audit artifacts: [list of $AUDIT_DIR/*.md files]

## Implementation Plan

[Section per priority tier, including the audit's override sections
where applicable]

**Task: [Finding ID] — [Category] — [Title]**
- Location: `path/to/file:line`
- [Audit-specific anchor columns]
- Issue: [description]
- Remediation: [specific fix]
- Verification: [how to confirm]
[Optional: Operational note]

## Compound Findings (if applicable)

[Reproduce from synthesis]

## Definition of Done

- [ ] All P0 (and Critical/Immediate Action where applicable) tasks
      completed and verified
- [ ] Each task's verification step executed
- [ ] No new Critical/High findings introduced by the remediations
- [ ] [Audit-specific verifications]

## [Audit-specific] Considerations

[Sensitive-content warnings, task-ordering notes, runtime-verification
reminders, App Store rejection callouts, etc.]

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/` (if applicable)
- Audit intermediate files: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`
- Emergency-exit document: `$AUDIT_DIR/EMERGENCY.md` (if applicable)
```

### Hand-off

```
> ✅ <Audit Name> complete.
>
> **Report:** <literal absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** <Critical: X, High: Y, Medium: Z, Low: W>; top finding:
> <one-line description>
>
> [Audit-specific warnings — sensitive content, App Store rejection
> risk, runtime verification required, etc.]
>
> **Next:** Run `/sprint-plan` against the report:
>
> ```
> /sprint-plan <literal absolute path>
> ```
>
> [Audit-specific guidance — out-of-band patching, task ordering, etc.]
```

If emergency-exit triggered in Phase 1, the hand-off points the user
at `$AUDIT_DIR/EMERGENCY.md` instead and confirms the audit did not
proceed past Phase 1.

---

## Output checklist baseline

At the end of every audit, verify:

- [ ] `$AUDIT_DIR/tooling-raw/` populated (if audit ran tooling) with
      `STATUS.md` documenting skipped tools
- [ ] `$AUDIT_DIR/claude.md` — schema with audit-specific extension
      columns, ID prefix A
- [ ] `$AUDIT_DIR/codex.md` — schema with audit-specific extension
      columns, ID prefix C
- [ ] Both review files non-empty (or single-agent warning added to
      synthesis after Phase 2 Step 2 retry failure)
- [ ] `$AUDIT_DIR/synthesis.md` — canonical S-prefix IDs, all extension
      columns preserved, Compound Findings section (if applicable)
- [ ] `$AUDIT_DIR/devils-advocate.md` — Codex challenge complete
- [ ] Valid devil's advocate challenges incorporated into synthesis
- [ ] Rejected challenges documented with reasoning
- [ ] `$AUDIT_DIR/REPORT.md` — P0/P1/Deferred tiering (with audit's
      override sections where applicable)
- [ ] Each task has location, issue, remediation, verification
- [ ] No-findings case handled if applicable
- [ ] Audit-specific output-checklist items satisfied
- [ ] User hand-off message includes audit-specific warnings

Each audit's SKILL file adds its own checklist items beyond this
baseline.

---

## Inherent limitations (all audits)

Static review by LLM + automated tooling cannot assess:

- Runtime behavior (does this code path actually execute? does the
  exploit actually work?)
- Compensating controls (WAF, network ACLs, App Sandbox effective
  behavior, etc.)
- Deployment-context-specific risk (internet-exposed vs internal-only,
  high-traffic vs low-traffic, regulated-data vs not)
- User-perceptible behavior (visual rendering, screen reader output,
  perceived performance) without runtime testing

Treat any audit's output as a structured starting point for human
judgment, not a guarantee of full coverage. Each audit's SKILL file
adds domain-specific limitations.

---

## Drift detection

Every `audit-*` subagent in `subagents/` should reference this file
and follow its 5-phase pattern. The drift-detection list in
[`codex-invocation.md`](codex-invocation.md) names them all — keep
that list in sync when audits are added or renamed.

When this framework changes (new phase semantics, new schema baseline,
new sprint-mapping defaults), update every audit subagent that
overrides the changed section.
