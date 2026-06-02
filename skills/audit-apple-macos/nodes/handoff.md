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
> Apple macOS Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-macos-specific notes:**
> - Critical findings here block the next Mac App Store submission or
>   will cause `xcrun notarytool submit` to return `Invalid`. Do not
>   submit until the Immediate Action tasks are resolved.
> - Most remediations require a real `xcodebuild archive` +
>   `codesign --display --entitlements -` + (for Developer ID)
>   `xcrun notarytool submit --wait` round-trip to confirm. "Set the
>   entitlement" is not a verified fix until the archive is rebuilt
>   and re-checked with codesign / notarytool / spctl.
> - **Gatekeeper traps**: `spctl --assess` on the developer Mac will
>   PASS for the developer's own signing identity even when other
>   users' Macs will block the app. Verify Gatekeeper on a clean Mac
>   (no developer cert in Keychain) before declaring a Notarization
>   fix complete. Useful: `spctl --assess --type execute --verbose=4`
>   and inspecting the `source=` line in the output.
> - **Notarization diagnostics**: when `notarytool submit` returns
>   `Invalid`, the response only includes the submission ID. Pull the
>   full diagnostic with `xcrun notarytool log <submission-id>
>   --keychain-profile <profile>`. Common causes are surfaced as
>   specific rule names (e.g. `The executable does not have the
>   hardened runtime enabled`, `The signature of the binary is invalid`,
>   or `The binary uses an SDK older than the 10.9 SDK`).
> - **Mac Catalyst** pointer + keyboard findings cannot be validated
>   in the iPad simulator — the simulator runs UIKit-on-iPad behavior,
>   not UIKit-on-Mac. Verify on a real Mac with a hardware keyboard
>   and pointer device.
> - **Sparkle**: end-to-end test via a staging appcast against the
>   built+signed app, not a unit test. Confirm `SUPublicEDKey` matches
>   the EdDSA key used to sign the appcast entries.
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
