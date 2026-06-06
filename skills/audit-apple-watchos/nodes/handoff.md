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
> Apple watchOS Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-watchOS-specific warnings:**
> - **Verify on real watch hardware, not the simulator.** The watchOS
>   simulator lies about memory pressure (the ~24MB active-app budget
>   isn't enforced), lies about always-on rendering (it renders the
>   active state regardless of wrist-down), and cannot reproduce paired
>   iPhone reachability transitions (locked phone, phone out of range,
>   Wi-Fi-only watch). Any finding marked `Verification=runtime` needs
>   a real watch on the wrist paired to a real iPhone before sign-off.
> - **Critical findings here block the next watch app release** — a
>   single bad release where the app OOMs on cold launch or loses
>   workout data leads to uninstalls that don't come back.
> - **Complication migration is one-way and time-boxed**: if findings
>   include `Apple:CLKComplicationDataSource` on watchOS 10+, plan the
>   WidgetKit migration soon. Apple has not given a specific deletion
>   date, but each watchOS release tightens ClockKit support.
> - **WCSession activation must happen on both sides**. A finding that
>   looks watch-side-only often has a paired iPhone-side gap that the
>   audit catches via `Platform=Multi`.
> - **HealthKit workout data loss is mostly silent**: there's no
>   error callback when `HKLiveWorkoutBuilder` dies mid-session under
>   memory pressure. Verify by running an actual workout to completion.
> - **Always-on PII leaks are a glance attack**: a sleeping device on
>   a desk reveals everything `.privacySensitive()` would have redacted.
>   Verify with the watch wrist-down for >5 seconds.
> - Sensitive-content warning: REPORT.md may reference paired-device
>   identifiers, complication push tokens, and HealthKit-protected data
>   categories. Treat as confidential.
>
> **Next:** Capture the findings as a feature with `/feature-create`:
>
> ```
> /feature-create   # describe the fixes; report at $AUDIT_DIR/REPORT.md
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
