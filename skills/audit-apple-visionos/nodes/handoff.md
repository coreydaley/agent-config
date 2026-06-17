# Node: handoff

Print the audit hand-off message to the user. **Verify already passed** — this node just communicates the result and the next-step pointer.

## Inputs

- Walker state: `audit_dir`, `verify_output`, `da_status`, `ingest_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
VERIFY_OUTPUT=$(scripts/walk.sh get --state "$STATE" --key verify_output)
DA_STATUS=$(scripts/walk.sh get --state "$STATE" --key da_status)
INGEST_STATUS=$(scripts/walk.sh get --state "$STATE" --key ingest_status)
```

## Steps

### 1. Extract finding counts from REPORT.md

Parse the audit summary table to populate the hand-off counts.

### 2. Print the hand-off

```
> Apple visionOS Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-visionos-specific warnings:**
> - Critical findings here block the next TestFlight build / App Review
>   submission. visionOS apps are scrutinized — hand-tracking without
>   entitlement crashes the app on `ARKitSession.run`; trapped
>   immersion (no dismiss affordance on `.full` `ImmersionStyle`) is a
>   documented rejection reason; large USDZ on main thread terminates
>   the process on the ~8GB-RAM Vision Pro.
> - **Real Vision Pro hardware is required to verify many findings.**
>   The visionOS simulator approximates but does not reproduce eye
>   tracking, hand tracking, `ImmersionStyle` transitions, or spatial
>   audio rendering. Findings marked `Verification=runtime` need a
>   real device pass — gaze targeting / `.hoverEffect` feedback /
>   `HandTrackingProvider` joint behavior / `PHASEEngine`
>   localization cannot be confirmed on simulator alone.
> - **PrivacyInfo.xcprivacy required-reason for hand-tracking must be
>   verified via the App Privacy Report generated on the device.**
>   Settings > Privacy & Security > App Privacy Report on the Vision
>   Pro itself; the simulator does not produce this report.
> - Sensitive-content warning: REPORT.md may reference internal bundle
>   identifiers, entitlement strings, and purpose-string copy. Treat
>   as confidential before sharing.
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

If `INGEST_STATUS` is `failed` or `unavailable`, add:

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
