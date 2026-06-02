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

Parse the audit summary table to populate the hand-off counts.

### 2. Print the hand-off

```
> ✅ Web SEO Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Web-SEO warnings:**
> - This audit does NOT guarantee rankings and is not a substitute for
>   Search Console data. Static code review identifies likely technical
>   issues but cannot fully validate what Googlebot sees after render,
>   actual indexation status, or Core Web Vitals field data.
> - Findings marked `runtime` in the Verification column require a
>   built/rendered page or Search Console / Rich Results Test / PSI to
>   confirm. Plan that verification time into the sprint.
> - Critical **Indexation** findings (noindex / Disallow: / / bad
>   canonical leaking to production) actively de-index the live site —
>   schedule them first, treat as block-deploy / hotfix.
> - The AI-agent / LLM-crawler surface (GPTBot / ClaudeBot directives,
>   llms.txt, no-JS extraction, API/MCP access) is NOT covered here —
>   run /audit-web-agent-accessibility for that.
> - Sensitive-content warning: REPORT.md may reference internal file
>   paths and unpublished URLs. Treat as confidential before sharing.
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
