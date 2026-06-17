# Node: handoff

Print the audit hand-off message to the user. **Verify already passed** — this node just communicates the result and the next-step pointer.

## Inputs

- Walker state: `audit_dir`, `verify_output`, `da_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
VERIFY_OUTPUT=$(scripts/walk.sh get --state "$STATE" --key verify_output)
DA_STATUS=$(scripts/walk.sh get --state "$STATE" --key da_status)
```

## Steps

### 1. Extract finding counts from REPORT.md

Parse the audit summary table to populate the hand-off counts.

### 2. Print the hand-off

```
> ✅ Apple Adaptivity Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-adaptivity-specific warnings:**
> - Most findings require **runtime Simulator verification** at the
>   configurations called out per task — at minimum: iPhone SE, iPhone
>   Pro Max, iPad mini, iPad Pro 12.9"; AX1 + AX5 Dynamic Type;
>   portrait + landscape; Split View on iPad.
> - For iPadOS findings, re-verify under Stage Manager where the app
>   declares multitasking support — Slide Over / Split View / Stage
>   Manager behave differently.
> - Mac Catalyst / macOS / visionOS findings should be re-verified only
>   when those are declared deployment targets.
> - Static code review cannot validate visual reflow, gesture
>   interaction, or window-management behavior — confirm on a built app
>   before closing P0 tasks.
> - Sensitive-content warning: REPORT.md may reference internal file
>   paths and identifiers. Treat as confidential before sharing.
>
> **Next:** Capture the findings as a feature with `/feature-create`:
>
> ```
> /feature-create   # describe the fixes; report at $AUDIT_DIR/REPORT.md
> ```
```

If `da_status=failed`, add to the warnings:

```
> - **Degraded run**: the devil's-advocate pass was skipped. Consider
>   re-running to get the adversarial check.
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
