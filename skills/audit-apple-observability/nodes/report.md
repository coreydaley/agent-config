# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able `REPORT.md` with observability-specific tier mapping (**Immediate Action** above P0 for Critical findings — PII leak via Console.app / sysdiagnose is a privacy incident, not a quality-of-life issue).

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-observability sprint mapping override

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — treat as privacy incident** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

"Immediate Action" here means: a Critical finding (PII / token / credential leak via Console.app, sysdiagnose, or TestFlight diagnostics) is a **privacy incident** — the data is already on every device the build ran on and in every sysdiagnose ever submitted from those devices. Remediation includes:

1. Land the code fix.
2. Rotate any credentials that may have leaked (refresh tokens, API keys, session cookies).
3. Notify the privacy/security team if the team has an incident-response process.
4. For severe cases, consider whether an in-the-wild TestFlight build needs to be expired and a fresh build pushed.

Treating it as a "we'll get to it" task is the wrong response.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 observability categories
- **Location** — `path/to/file.swift:line` (never just a function name)
- **Anchor** — required (`Apple:Logger`, `Apple:MetricKit`, `Apple:OSSignposter`, `Apple:OSLogStore`, `File:...`)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Verification** — `code` (inspectable from source / tooling-raw) or `runtime` (requires Console.app on a real device, sysdiagnose review, or a MetricKit-emit cycle to confirm)
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `Change \(url, privacy: .public) → \(url.host ?? "?", privacy: .public), \(url.path, privacy: .public) — strip query params; or replace the URL log entirely with a structured Logger call that omits credentials`)
- **Verification step** — for `code` findings: re-grep `privacy-specifiers.txt` and confirm the offending line is gone. For `runtime` findings: run the app on a real device, reproduce the scenario, open Console.app filtered by subsystem, and confirm the value renders as `<private>` rather than plaintext; or capture a fresh sysdiagnose via Settings → Privacy & Security → Analytics & Improvements and grep the bundle for the value.

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-observability — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Report template

Write to `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Observability Audit — <scope> (<YYYY-MM-DD>)

## Overview

<1-2 paragraphs: scope, tooling summary, total findings by severity,
top 3 issues, reminder of audit's inherent limitations — code-only
review catches the obvious `.public`-on-token patterns; only a
Console.app session on a real device with the scenario reproduced
will confirm third-party SDKs (analytics, crash reporting,
networking) aren't also leaking. The audit catches the misconfig but
only an on-device verification confirms the fix.>

<If Critical findings exist:>
> ⚠️ **Critical findings present — privacy incident posture.** A
> Critical observability finding means PII / credentials / tokens are
> already in Console.app on every device the build ran on, and in
> every sysdiagnose ever taken from those devices. See Immediate
> Action below — code fix alone is not sufficient; rotate the leaked
> credentials.

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
- $AUDIT_DIR/tooling-raw/ (logger / signpost / MetricKit / print / privacy-specifier captures)
- $AUDIT_DIR/claude.md
- $AUDIT_DIR/synthesis.md
- $AUDIT_DIR/devils-advocate.md <or "MISSING — DA failed" if da_status=failed>

## Implementation Plan

### Immediate Action — treat as privacy incident

<one block per Critical finding>

**Task: S### — <Category> — <Title>**
- Location: `path/to/file.swift:line`
- Anchor: <anchor>
- Platform: <platform>
- Verification: <code | runtime>
- Issue: <description>
- Remediation: <specific fix>
- Verification step: <re-grep tooling-raw / Console.app filter on subsystem / sysdiagnose bundle inspection / etc.>
- Operational note: <e.g. "rotate leaked refresh tokens" / "expire affected TestFlight builds" / "notify privacy team">

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
- [ ] Each task's verification step executed
- [ ] No new Critical/High findings introduced by the remediations
- [ ] For every Critical finding: leaked credentials rotated (refresh tokens, API keys, session cookies)
- [ ] For every Critical finding: on-device Console.app verification on a real device shows the value rendering as `<private>`
- [ ] For every Critical finding: a fresh sysdiagnose taken post-fix has been grepped for the leaked value and shows zero hits
- [ ] If any task touched `MXMetricManager`: a real diagnostic-payload delivery cycle (24h) has been observed
- [ ] If any task added `OSSignposter` coverage: confirmed visible in Instruments under the expected category

## Sensitive-content warning

This deliverable references actual leaked-credential locations and may
contain fragments of the values themselves. **Treat as confidential at
the same level as a credentials file** — do not paste into Slack
channels, do not attach to public issues, do not ingest into external
analytics. If the leaked values include long-lived secrets, rotate
them before the deliverable is filed even internally.

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

- Synthesis has zero findings → produce the single-task no-findings deliverable; still transition to `verify`.
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
