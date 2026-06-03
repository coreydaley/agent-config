# Node: handoff

Print the audit hand-off message to the user. **Verify already passed** — this node just communicates the result and the next-step pointer.

## Inputs

- Walker state: `audit_dir`, `verify_output`, `da_status`, `codex_status`, `ingest_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
VERIFY_OUTPUT=$(scripts/walk.sh get --state "$STATE" --key verify_output)
CODEX_STATUS=$(scripts/walk.sh get --state "$STATE" --key codex_status)
DA_STATUS=$(scripts/walk.sh get --state "$STATE" --key da_status)
INGEST_STATUS=$(scripts/walk.sh get --state "$STATE" --key ingest_status)
```

## Steps

### 1. Extract finding counts from REPORT.md

Parse the audit summary table to populate the hand-off counts.

### 2. Print the hand-off

```
> ✅ Apple Extensions Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-extensions-specific notes:**
> - Critical findings here block the next TestFlight build — do not
>   promote a build to Internal / External or App Store with Immediate
>   Action tasks outstanding. NSE 24MB cap is the canonical example:
>   a single payload that pushes the extension over the cap silently
>   reverts the push to its unmodified server-sent form for every
>   affected user.
> - Memory-budget findings (NSE 24MB, Widget ~30MB, watchOS complications
>   on the watch's tiny budget) require Instruments (Allocations) on
>   the extension process — file-time review can only spot the risk,
>   not confirm the magnitude. The Verification field of each Critical
>   task points to the specific runtime check.
> - Entitlement-drift findings (Push / App Groups / iCloud / HealthKit
>   present on host but not on extension) are only confirmable via
>   `codesign --display --entitlements -` against the built `.appex`
>   bundle, NOT against the .entitlements file alone — Xcode can drop
>   the entitlement at signing time even when the file is correct.
> - App Group IPC findings need write-from-one-side / read-from-the-other
>   verification on a real device; Simulator behavior diverges.
> - App Intent findings need a real Siri invocation (XCUITest with
>   `Siri.invoke(phrase:)` or manual "Hey Siri, <phrase>") — Spotlight
>   testing alone misses the strict perform()-budget enforcement Siri
>   applies.
> - Sensitive-content warning: REPORT.md may reference bundle IDs,
>   App Group IDs, team IDs, and APNs payload shapes. Treat as
>   confidential before sharing.
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
