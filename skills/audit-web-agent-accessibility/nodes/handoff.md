# Node: handoff

Print the audit hand-off message to the user. **Verify already passed** — this node just communicates the result and the next-step pointer.

## Inputs

- Walker state: `audit_dir`, `verify_output`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
VERIFY_OUTPUT=$(scripts/walk.sh get --state "$STATE" --key verify_output)
CODEX_STATUS=$(scripts/walk.sh get --state "$STATE" --key codex_status)
DA_STATUS=$(scripts/walk.sh get --state "$STATE" --key da_status)
```

## Steps

### 1. Extract finding counts from REPORT.md

Parse the audit summary table to populate the hand-off counts, including the count of Ambiguous (confirm-intent) items.

### 2. Print the hand-off

```
> ✅ Web Agent-Accessibility Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Confirm-intent
> items: N. Top finding: <one-line description of the highest-severity
> finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Web agent-accessibility warnings:**
> - Blocking AI crawlers is often a deliberate, legitimate choice. The
>   report separates confirmed defects from "Confirm Operator Intent"
>   items — review the latter and decide before any of them become
>   tasks. The audit does NOT assume you want every agent served.
> - Findings marked `runtime` require a live fetch as an agent to
>   confirm (WAF behavior, the real no-JS render, what /llms.txt
>   serves). If TARGET_URL was unset, CDN/WAF bot-blocking and the true
>   render could not be observed — re-run with TARGET_URL for those.
> - This is the AI-agent / LLM-crawler surface only. The broad
>   technical-SEO surface (Googlebot crawlability, sitemaps, canonicals,
>   Core Web Vitals, hreflang) is /audit-web-seo.
> - Respect stated licensing. Don't open content you deliberately
>   reserved just because a remediation suggests it.
> - Sensitive-content warning: REPORT.md may reference WAF rule names,
>   internal paths, and unpublished URLs. Treat as confidential.
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
>   was not stress-tested. Intent-assumption errors may be present.
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
