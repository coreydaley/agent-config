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

Parse the audit summary table to populate the hand-off counts. Pay particular attention to the **Submission Blocker** count — the user's primary concern is whether the build is currently rejectable.

### 2. Print the hand-off

```
> ✅ Apple App Store Review Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Submission Blocker (Will Reject): X, P0 (Likely Reject): Y,
> P1 (Risk): Z, Deferred (Best Practice): W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **App Store Review warnings:**
> - **Submission Blocker findings = do not submit.** If the build has
>   already been submitted to App Review, withdraw it. Submitting with
>   these findings present is near-certain rejection.
> - Many remediations require runtime verification (TestFlight build,
>   App Store Connect metadata review, on-device check); the report's
>   per-task Verification field calls out which.
> - App Review enforcement varies in practice. Treat findings as "high
>   likelihood of rejection" rather than "Apple will definitely reject".
>   The Guidelines update frequently — re-check the current version
>   before submission.
> - Sensitive-content warning: REPORT.md may reference internal file
>   paths, identifiers, and App Store Connect metadata. Treat as
>   confidential before sharing.
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
