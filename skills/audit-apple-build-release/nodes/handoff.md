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
> ✅ Apple Build & Release Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-build-release-specific notes:**
> - Critical findings here block the next Release archive — do not
>   upload to TestFlight or App Store with Immediate Action tasks
>   outstanding.
> - Most remediations require a real `xcodebuild archive` + `codesign
>   --display --entitlements -` to confirm; "set the setting" isn't a
>   verified fix until the archive is rebuilt clean. The report's
>   per-task Verification field calls out which steps need the build.
> - Capability-drift findings (Push, App Groups, iCloud, HealthKit,
>   etc.) require re-syncing the provisioning profile after the
>   entitlements file changes; automatic signing usually handles this,
>   manual signing does not.
> - If signing is in CI: verify against a clean CI run (cleared
>   DerivedData) — local Xcode often masks CI-only signing failures
>   because the dev cert is in your local Keychain.
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
