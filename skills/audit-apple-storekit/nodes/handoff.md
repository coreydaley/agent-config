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
> ✅ Apple StoreKit Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-StoreKit-specific notes:**
> - Critical findings here are revenue-impacting OR App-Review-blocking.
>   Do not submit a new build, and audit production for the same defect
>   if the bug already shipped — every existing install with the
>   `.unverified` bug or missing `Transaction.updates` observer is
>   exploitable until updated.
> - **Sandbox testing is mandatory for verification.** The audit caught
>   the misuse pattern; only an actual sandbox purchase + `.storekit`
>   test session confirms the fix. Configure a Sandbox tester in App
>   Store Connect (Users and Access → Sandbox Testers), sign out of the
>   Sandbox account on the device after each test cycle.
> - **App Store Connect setup is a prerequisite for sandbox testing.**
>   Each in-app purchase product must exist in App Store Connect with
>   matching identifiers, and (for promotional offers) a server-side
>   signing key must be configured under In-App Purchase → Keys.
> - **Server-side validation pointer.** For any non-consumable or
>   subscription with a backing server, the server should validate
>   `Transaction.jwsRepresentation` via Apple's App Store Server API
>   public keys (`/inApps/v1/...`) rather than trusting the client.
>   Apple publishes a Swift package (`apple/app-store-server-library-swift`)
>   and reference servers in Python / Java / Node — use them rather
>   than rolling your own JWS verifier.
> - **Promotional offer private key handling.** The promotional offer
>   signing private key must live server-side (env var, secrets manager,
>   Keychain on a dedicated machine). If the key has ever been bundled
>   into a shipped App Store binary, rotate it via App Store Connect
>   immediately and treat the old key as compromised.
> - Sensitive-content warning: REPORT.md may reference bundle IDs,
>   product IDs, and subscription group identifiers. Treat as
>   confidential before sharing.
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
