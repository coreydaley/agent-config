# Node: handoff

Print the audit hand-off message to the user. **Verify already passed** — this node just communicates the result and the next-step pointer.

## Inputs

- Walker state: `audit_dir`, `verify_output`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
VERIFY_OUTPUT=$(scripts/walk.sh get --state "$STATE" --key verify_output)
CODEX_STATUS=$(scripts/walk.sh get --state "$STATE" --key codex_status)
DA_STATUS=$(scripts/walk.sh get --state "$STATE" --key da_status)
```

## Steps

### 1. Extract finding counts from REPORT.md

Parse the audit summary table to populate the hand-off counts.

### 2. Print the hand-off

```
> ✅ Web Accessibility Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Web-accessibility warnings:**
> - This audit is NOT a WCAG conformance certification. Static code
>   review identifies likely violations against WCAG 2.1/2.2 but
>   cannot fully validate dynamic behavior, screen reader output, or
>   focus management without runtime testing.
> - Findings marked `runtime` in the Verification column require
>   browser and assistive-technology testing (VoiceOver, NVDA, JAWS,
>   TalkBack) to confirm. Plan AT testing time into the sprint that
>   tackles those tasks.
> - If automated tooling (axe-core, pa11y, Lighthouse, jest-axe) is
>   already in CI for this project, prefer adding regression tests
>   to that pipeline over one-off manual remediation.
> - Sensitive-content warning: REPORT.md may reference internal file
>   paths and identifiers. Treat as confidential before sharing.
>
> **Next:** Run `/sprint-plan` against the report:
>
> ```
> /sprint-plan <absolute path to $AUDIT_DIR/REPORT.md>
> ```
```

If `CODEX_STATUS=failed`, add to the warnings:

```
> - **Degraded run**: Codex review unavailable; this was a single-agent
>   audit. Consider re-running once codex is reachable.
```

If `DA_STATUS=failed`, add:

```
> - **Degraded run**: Devil's advocate pass did not complete; synthesis
>   was not stress-tested. False positives may be present.
```

### 3. Mark the audit complete in walker state

```bash
scripts/walk.sh set --state "$STATE" --key handoff_printed --value "yes"
```

## Outputs

- Hand-off message printed to the user
- Walker state updated

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from handoff --to terminal
```

## Failure modes

- REPORT.md unparseable for counts → fall back to "see REPORT.md for findings" without specific numbers.
