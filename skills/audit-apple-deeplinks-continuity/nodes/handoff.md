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
> Apple Deep Links & Continuity Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-deeplinks-continuity-specific notes:**
> - Critical findings here block reliance on the deep-link surface.
>   For RCE-class deep-link handlers, treat as ship-blocking. For
>   AASA / entitlement mismatches, treat as marketing-blocking until
>   resolved.
> - The audit catches the configuration; it does NOT catch the
>   on-device behavior. Every Critical and High finding needs a real
>   on-device test before sign-off:
>     - AASA reachability: `curl -I https://<domain>/.well-known/apple-app-site-association`
>       (must return 200, no redirect, Content-Type application/json).
>     - On-device AASA registration: enable Developer mode on the iOS
>       device, then `swcutil dl -d <domain>` shows the AASA that the
>       system actually fetched for the installed build.
>     - Universal Link tap: open Notes on the device, paste the
>       marketing URL, long-press → Open in <App>. If "Open in <App>"
>       isn't an option, the Universal Link is broken regardless of
>       what the AASA file says.
>     - Custom URL scheme: `xcrun simctl openurl booted <url>` against
>       a Simulator running the build, plus a state-changing scenario
>       to confirm re-auth / confirmation requirement.
>     - Spotlight: Settings → Siri & Search → <App> shows the indexed
>       items; sign in as a different user and confirm the previous
>       user's content is not queryable.
> - URL-scheme handler RCE / WKWebView bridge findings should be
>   cross-referenced with `/audit-apple-security` for the runtime
>   exploit-chain depth. This audit flags the discipline; the
>   security audit owns the exploit-chain proof.
> - App Intent donation lifecycle inside Widget / Live Activity /
>   App Shortcuts targets is owned by `/audit-apple-extensions`.
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
