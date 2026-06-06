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
> ✅ Apple Notifications Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-notifications-specific notes:**
> - Critical findings here block the next Release archive — do not
>   upload to TestFlight or App Store with Immediate Action tasks
>   outstanding. Several Criticals will be rejected by App Review on
>   resubmission (criticalAlert without entitlement); others silently
>   break push on every Release device (`aps-environment` mismatch).
> - Most remediations require a real sandbox APNs push against a real
>   device to confirm — use `apns` CLI or `Knuff` against the device
>   token and watch `Console.app` filtered on `subsystem:
>   com.apple.usernotifications`. "Set the entitlement" isn't a verified
>   fix until a live push lands and `didReceive` fires. Each task's
>   Verification field calls out the specific live-push or codesign
>   step.
> - Entitlement-drift findings between host app and NSE / NCE targets
>   require re-verification on EVERY target via `codesign --display
>   --entitlements -` — automatic signing usually keeps them in sync
>   but manual signing does not.
> - Delegate-lifecycle findings cannot be validated by warm launch in
>   Xcode. Verify with a cold-launch-from-notification-tap test: kill
>   the app, schedule (or send) a notification, tap from the lock
>   screen, confirm the response handler fires.
> - Communication Notification fixes (INSendMessageIntent donation)
>   only render correctly on iOS 15+ with the Communication capability
>   declared; verify the avatar appears on the lock screen for the
>   intended user vs the generic fallback.
> - Sensitive-content warning: REPORT.md may reference push topics
>   (sensitive — matches the bundle id), team IDs, and NSE entitlement
>   contents. Push tokens, APNs `.p8` keys, and server-side push
>   credentials must never appear in the report — redact if they do
>   before sharing.
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
