# Node: synthesis

Produce a unified, deduplicated finding list with calibrated severity and confidence. Reads both review files for the first time.

## Inputs

- `pr_dir`, `pr_number`, `report_ts`, `codex_status` from walker state
- `$PR_DIR/claude-review.md` and `$PR_DIR/codex-review.md` (latter optional)

```bash
STATE="$PR_DIR/.walk-state.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
CODEX_STATUS=$(scripts/walk.sh get --state "$STATE" --key codex_status)
```

## Steps

1. **Verify both reviews exist and are non-empty.** If `codex_status` is `failed` or `empty`, proceed with single-agent synthesis and add a warning at the top of `synthesis.md`:

   > ⚠️ Single-agent synthesis — Codex review was unavailable.

2. **Deduplicate findings:**
   - Merge overlapping findings — note both source IDs in the Sources column.
   - Don't flatten findings with different affected lines or distinct remediation paths.
   - Agreement = higher confidence, **not** higher severity.

3. **Calibrate severity:**
   - Re-evaluate based on actual user impact, blast radius, likelihood.
   - **Demote** pure style nits; **don't promote** them.
   - Distinguish between subjective preference and objective problem.

4. **Write `$PR_DIR/synthesis.md`:**

   ```markdown
   # PR #<N> Review Synthesis — <REPORT_TS>

   ## PR Summary
   [Title, author, scope]

   ## CI Status
   [pass / fail / pending — key checks]

   ## Finding Summary
   - Total: N (Blocker: X, High: X, Medium: X, Low: X, Nit: X)
   - Reviewers: Claude (CR-prefix), Codex (CX-prefix)

   ## Unified Findings

   | ID | Severity | Category | File:Line | Issue | Suggestion | Evidence | Sources |
   |----|----------|----------|-----------|-------|------------|----------|---------|
   | SR001 | High | Correctness | path/to/file.go:42 | ... | ... | ... | CR003, CX007 |

   ## Single-Reviewer Findings
   [Findings present in only one review — note which agent and why it may have been missed]

   ## Overall Assessment
   [2-3 sentences: is this ready to merge, needs changes, or blocked?]
   ```

## ID prefix convention

Synthesis findings get a fresh `SR` prefix (e.g. `SR001`, `SR002`). The `Sources` column carries the original `CR` / `CX` IDs for traceability. Downstream nodes (`devils-advocate`, `write-review`, `post`) reference `SR` IDs only.

## Outputs

- `$PR_DIR/synthesis.md`

## Outgoing edges

- → `devils-advocate` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from synthesis --to devils_advocate
```

## Failure modes

- Both reviews empty → write a synthesis that says "no findings from either reviewer" with the warning prepended. Continue to devils-advocate (which becomes a no-op).
- File:Line in one of the reviews is malformed (not `path:line`) → drop those findings during synthesis with a note. Don't try to repair.
