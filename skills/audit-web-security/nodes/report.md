# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with web-security-specific tier mapping (**Immediate Action** above P0 for Critical findings).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Web-security sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next deploy / hotfix / rollback** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

For deployed services, "Immediate Action" frequently means: block the deploy, hotfix, or roll back the offending release. Note this in the artifact's overview.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 17 web-security categories
- **Location** — `path/to/file.ext:line` (never just a function name)
- **CWE/OWASP anchor** — required (`CWE-89 / A03:2021`)
- **Issue** — clear description
- **Remediation** — concrete, specific (never "fix the issue")
- **Verification** — a *negative test* (try the exploit, confirm it fails) plus a regression test

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — web-security — <scope>, <date>`
- Task description: scope covered, 15 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Output template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Web Security Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity, top 3
issues, reminder of audit's inherent limitations — static review cannot
assess runtime exploitability, compensating controls (WAF, network ACLs,
RASP), or deployment-context-specific risk.>

<If Critical findings exist:>
> ⚠️ **Critical findings present.** Web-security Critical = block the
> deploy / hotfix / rollback. See Immediate Action section below.

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Category | Count |
|---|---|
<non-zero categories only>

Intermediate audit artifacts:
- $AUDIT_DIR/tooling-raw/ (gitleaks, semgrep, dep scanners, trivy, actionlint)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — fix before next deploy / hotfix / rollback

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.ext:line`
- CWE/OWASP: <anchor>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <negative test + regression test>
- Operational note: <e.g. "block deploy of v1.2.3", "rotate credential before re-deploy", "incident-report scope: who used the leaked credential">

### P0 — Must Ship

<one block per High finding, same format>

### P1 — Ship If Capacity Allows

<one block per Medium finding>

### Deferred

<one-line per Low finding>

## Compound Findings

<reproduce from synthesis.md if any>

## Definition of Done

- [ ] All Immediate Action and P0 tasks completed and verified
- [ ] Each task's verification step (negative test + regression test) executed
- [ ] No new Critical/High findings introduced by the remediations
- [ ] Deploy-readiness: target environment(s) re-scanned post-fix, no regressions
- [ ] If any task involved credential rotation: rotation confirmed at the provider AND any downstream services restarted/redeployed
- [ ] If any task involved IaC changes: re-validated with trivy / kubeconform / equivalent
- [ ] If any task involved a CI/CD workflow change: workflow re-run on a dummy PR and confirmed no secret leakage
- [ ] If a hotfix or rollback was issued: incident postmortem written

## Sensitive-content warning

This audit output may reference internal file paths, identifiers, fragments
of vendored dependencies, internal hostnames, or environment-variable names
that imply infrastructure topology. Treat as confidential before sharing
externally.

## Dependencies

- Tooling output: `$AUDIT_DIR/tooling-raw/`
- Intermediate files: `$AUDIT_DIR/{claude,synthesis,devils-advocate}.md`
```

## Outputs

- `$AUDIT_DIR/REPORT.md` exists, non-empty, contains the Implementation Plan with appropriate tiers populated

## Outgoing edges

- → `verify` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from report --to verify
```

## Failure modes

- Synthesis has zero findings → produce the single-task no-findings output; still transition to `verify`.
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
