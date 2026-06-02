# Node: emergency-exit

Phase 1 detected a live credential in source. **Halt the audit before Phase 2.** Write `EMERGENCY.md` describing the trigger, what needs to happen, and web-specific rotation procedures.

## Inputs

- `$AUDIT_DIR/tooling-raw/gitleaks.json` (the trigger source)
- Walker state: `audit_dir`

## Steps

### 1. Identify the credential class

For each hit in `gitleaks.json`, classify into one of:

- **Cloud provider access key** (`AKIA*`, `ASIA*`, GCP service account JSON, Azure storage / SAS token) — rotate in the provider's IAM console; revoke compromised key; audit CloudTrail / Cloud Audit Logs / Azure Monitor for use during the exposure window.
- **GitHub token** (`ghp_*`, `gho_*`, `ghu_*`, `ghs_*`, `ghr_*`, fine-grained PAT, GitHub App private key) — revoke at github.com/settings/tokens (PAT) or the App settings page; audit repo and org audit logs for use during the exposure window.
- **Payment provider key** (`sk_live_*` Stripe, Square / Braintree / Adyen secrets) — rotate in the provider dashboard; check for transactions made with the leaked key.
- **Database credential** (connection string with embedded password, MongoDB Atlas URI, Postgres / MySQL URL) — rotate the DB user password; review query logs for the exposure window; consider whether to require a TLS-cert-based auth migration.
- **OAuth client secret** (Google / Okta / Auth0 / Slack app secret) — regenerate in the IdP / app console; reissue affected tokens; review consent grants.
- **Generic API token** (Sendgrid, Twilio, PagerDuty, Datadog, Segment, etc.) — rotate via the issuing service; audit the service's activity log.
- **Private key** (`-----BEGIN ... PRIVATE KEY-----`) — revoke any cert / SSH key derived from it; reissue.
- **Webhook signing secret** (Stripe webhook secret, GitHub webhook secret) — rotate in the issuer; coordinate the cutover with the receiving service to avoid dropped events.

### 2. Write EMERGENCY.md

```bash
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# EMERGENCY EXIT — web-security — $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Trigger

\`gitleaks\` matched on a live credential in the audit scope. The audit
has **halted before Phase 2**. No reviewer artifacts will be produced.

## Hits

<list each gitleaks hit: file:line, rule, redacted-preview>

## Required actions (in order)

1. **Rotate the credential** at the issuing provider. Web-specific
   rotation steps per credential class above. Do NOT just delete the
   file — the secret is already in git history and (if pushed) on
   every clone and on GitHub's servers.
2. **Purge the secret from git history.** Use \`git filter-repo\` or BFG.
   A simple commit deleting the file is insufficient.
3. **Audit usage during the exposure window.** Check the provider's
   audit log / CloudTrail / activity log for actions taken with the
   leaked credential. Assume compromise if the repo was ever public.
4. **Invalidate downstream artifacts.** If the credential was used by a
   deployed service, restart / redeploy that service with the new
   credential and confirm no cached copies persist.
5. **Re-run \`/audit-web-security\`** once rotation is complete.
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
