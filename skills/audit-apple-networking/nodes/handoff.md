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
> ✅ Apple Networking Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-networking warnings:**
> - Most network-layer findings need a proxy-driven reproduction to
>   confirm the fix. Set up Charles Proxy or mitmproxy with the
>   device's debug cert installed, then replay the affected request.
>   "Set the config value" isn't a verified fix until the capture
>   confirms the behavior on the wire. The deliverable's per-task
>   Verification field calls out which steps need the proxy.
> - For lossy / slow-network behavior, use **Network Link Conditioner**
>   (System Settings > Developer on macOS; Settings > Developer on
>   iOS device). Profiles like "100% Loss", "3G", "LTE" exercise the
>   retry-backoff and reconnect-with-jitter paths.
> - For cellular-state-driven UI affordances, **xcrun simctl status_bar
>   override** sets the Simulator status bar to any cellular state
>   without changing real network behavior — useful for UI checks but
>   does NOT reproduce real radio-state transitions; pair with NLC.
> - **Cert pinning during proxy testing:** if Charles / mitmproxy
>   can't see traffic, pinning is on and the debug CA isn't trusted.
>   That's a finding (NetworkLogging category), not a workflow
>   problem to bypass silently — fix the conditional-pinning code
>   so Debug builds trust the proxy CA, not "disable pinning for the
>   test session."
> - **Cert-pinning expiration:** if the deliverable's Immediate Action
>   section is populated, the cert expires inside the audit window
>   with no fallback pin. Treat the cert's `notAfter` date as the
>   release deadline, not a sprint boundary; budget App Review
>   turnaround into the timeline.
> - Sensitive-content warning: the deliverable may reference internal
>   API endpoints, OAuth client IDs, and pinned-cert fingerprints.
>   Proxy captures generated during verification may contain auth
>   tokens; redact before sharing.
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
