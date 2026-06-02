# Node: emergency-exit

Phase 1 detected a live credential in source. **Halt the audit before Phase 2.** Write `EMERGENCY.md` describing the trigger, what needs to happen, and Apple-specific rotation procedures.

## Inputs

- `$AUDIT_DIR/tooling-raw/gitleaks.json` (the trigger source)
- Walker state: `audit_dir`

## Steps

### 1. Identify the credential class

For each hit in `gitleaks.json`, classify into one of:

- **Code-signing certificate** (`.p12`, `.cer`, `.pem` with `BEGIN CERTIFICATE` or `BEGIN PRIVATE KEY`) — rotate via Apple Developer portal; revoke compromised cert.
- **App Store Connect API key** (`.p8` named `AuthKey_*.p8`) — revoke in App Store Connect → Users and Access → Keys.
- **APNs / push notification certificate or auth key** (`.p12`, `.p8`) — revoke in Apple Developer portal → Keys; rotate at the server side.
- **Service-side key** (Firebase, Sentry, Datadog, etc.) — rotate via the service provider's console.
- **Generic API token** (`ghp_`, `sk_live_`, `AKIA*`, etc.) — rotate via the issuing service.

### 2. Write EMERGENCY.md

```bash
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# EMERGENCY EXIT — apple-security — $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Trigger

\`gitleaks\` matched on a live credential in the audit scope. The audit
has **halted before Phase 2**. No reviewer artifacts will be produced.

## Hits

<list each gitleaks hit: file:line, rule, redacted-preview>

## Required actions (in order)

1. **Rotate the credential.** <Apple-specific rotation steps per
   credential class above.>
2. **Purge the secret from git history.** Use \`git filter-repo\` or BFG.
   A simple commit deleting the file is insufficient — the secret is
   still in the history.
3. **Audit who had access.** If this credential was in a public repo,
   assume compromise.
4. **Re-run \`/audit-apple-security\`** once rotation is complete.
EOF
```

### 3. Tell the user out-of-band

This is not a finding for the next sprint — it's a "now" event. Print a stark message to the conversation and point at `$AUDIT_DIR/EMERGENCY.md`.

## Outputs

- `$AUDIT_DIR/EMERGENCY.md` written
- No reviewer artifacts will be produced for this run

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- False positive (gitleaks matched on a doc example or vendored test fixture) → still produce `EMERGENCY.md` with the user-visible "if this is a false positive, re-run with `SKIP_GITLEAKS=1`" note. Better to over-alert than miss a real leak.

## Notes

- This node is **terminal-bound**. The handoff message format is different: point the user at `EMERGENCY.md` and confirm no Phase 2+ work ran. `audit-verify.sh` handles this case (an `EMERGENCY.md` present in `$AUDIT_DIR` short-circuits the artifact gate).
