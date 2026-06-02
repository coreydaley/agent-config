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
> ✅ Apple Observability Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-observability-specific notes:**
> - Critical findings here are **privacy incidents** — PII /
>   credentials / tokens are already in Console.app on every device
>   the build ran on, plus every sysdiagnose ever submitted from
>   those devices. Code fix alone is not sufficient; rotate the
>   leaked credentials and consider whether affected TestFlight
>   builds need to be expired.
> - On-device verification is mandatory for Critical findings. Plug
>   the device into a Mac, open Console.app, filter on the app's
>   subsystem (`com.org.app.*`), reproduce the scenario, and confirm
>   every formerly-`.public` value renders as `<private>`. The
>   audit's code-side fix can be undone by a third-party SDK still
>   logging plaintext through its own Logger; only on-device review
>   catches that.
> - Capture a fresh sysdiagnose (Settings → Privacy & Security →
>   Analytics & Improvements → tap Privacy → Analytics Data, or
>   trigger via Volume Up + Volume Down + Side button on iOS) and
>   grep the resulting bundle for the leaked value before signing
>   off — sysdiagnose pulls from the unified-logging persistent
>   store, which retains entries for hours to days.
> - MetricKit findings have a slow verification loop: payloads are
>   emitted ~once every 24 hours. A `MXMetricManager` fix can only be
>   confirmed by waiting for the next emit cycle on a real device.
> - **Sensitive-content warning**: REPORT.md references actual leaked
>   values. Treat as confidential at the same level as a credentials
>   file — do not paste into Slack, do not attach to public issues.
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
> - **Plane ingest**: <failed | unavailable>. Audit artifacts are
>   complete; only the work-item generation failed. Re-run with
>   `/plane-audit-ingest <audit-dir>` after fixing the underlying issue.
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
