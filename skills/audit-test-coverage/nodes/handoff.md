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
> ✅ Test Coverage Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Test-coverage warnings:**
> - Line/branch coverage measures execution, not correctness. A line
>   covered by a tautological assertion is still under-tested. Treat
>   the measured % as the floor, not the ceiling.
> - Each P0 task includes a *recommended layer* (unit / integration /
>   e2e) — adding tests at the wrong layer can be worse than no test.
> - Verification steps demand a measurable outcome (coverage number,
>   named scenario, or mutation check). "Tests added" is not sufficient.
> - If CI does not currently fail on coverage regression, integrating
>   that is a worthwhile follow-up beyond this audit's scope.
> - If a `Missing-Layer` finding shipped without that layer being
>   wired into CI, the regression risk re-emerges.
> - For Apple-specific test-design depth (XCTest vs Swift Testing,
>   XCUITest critical-flow coverage, SwiftUI view testing, Preview
>   coverage, snapshot testing strategy, `@MainActor` patterns), run
>   `/audit-apple-testing` — this audit's `tooling-raw/` feeds it.
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
