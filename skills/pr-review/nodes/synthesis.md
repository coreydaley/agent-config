# Node: synthesis

Produce a unified, deduplicated finding list with calibrated severity and confidence. The first time any of the review files is read by anyone but its author.

## Who does this

The **`synthesizer`** role, per [`lib/agent-roles.md`](../../../lib/agent-roles.md). The orchestrator may have written the code under review and has watched the reviewer files land. It doesn't merge or calibrate findings about its own work. The orchestrator's part: confirm which review files exist (status keys), launch one Agent call with `subagent_type: synthesizer` whose brief is the Steps section below verbatim plus the absolute paths of every review file, `intent.md`, `metadata.json`, `ci-status.txt`, and `$WORKTREE_PATH` (read-only), with the output contract "write only `$PR_DIR/synthesis.md`" and the closing line from "The brief". Wait for it to return, verify `synthesis.md` has the Unified Findings table and the sections below, transition. Read `synthesis.md` afterward, never edit its judgments.

## Inputs

- `pr_dir`, `pr_number`, `report_ts`, `canon_independent_status`, `canon_adversarial_status` from walker state
- `$PR_DIR/review-independent.md`, `$PR_DIR/review-adversarial.md` (always), `$PR_DIR/canon-independent.md`, `$PR_DIR/canon-adversarial.md` (per status)
- `$PR_DIR/intent.md` — the scope anchor for the Intent & Scope section

```bash
STATE="$PR_DIR/.walk-state.review.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
CANON_INDEPENDENT_STATUS=$(scripts/walk.sh get --state "$STATE" --key canon_independent_status)
CANON_ADVERSARIAL_STATUS=$(scripts/walk.sh get --state "$STATE" --key canon_adversarial_status)
```

## Steps

1. **Verify which reviews exist and are non-empty.** Pool whatever succeeded. Canon files exist only when `--canon` ran; their absence by default is not a warning. If canon ran and one canon review is missing, add at the top of `synthesis.md`:

   > ⚠️ Adversarial canon review unavailable — canon findings are independent-reviewer-only.

   (or the mirror for the independent canon review).

2. **Deduplicate findings across all pooled reviews:**
   - Merge overlapping findings — note all source IDs in the Sources column.
   - Don't flatten findings with different affected lines or distinct remediation paths.
   - Agreement = higher confidence, **not** higher severity.
   - Confidence comes from **cross-role** agreement (the independent and adversarial reviewers both flagged it). One role's dimensions and canon passes agreeing with each other (`IR`+`IG`, or `AR`+`AG`) is one stance saying it twice, not corroboration.
   - Canon-only findings map their principle to a synthesis category: design, complexity → Design; tests → Tests; functionality → Correctness; naming, comments, every-line, documentation → Readability; consistency, style → Style. Keep the principle visible in the Evidence column as `canon: <principle>` — it survives into REVIEW.md so findings stay traceable to the eng-practices guide.

3. **Calibrate severity:**
   - Re-evaluate based on actual user impact, blast radius, likelihood.
   - **Demote** pure style nits; **don't promote** them.
   - Distinguish between subjective preference and objective problem.
   - Scope-category findings keep their severity, but their suggestion
     is **flag for the author / defer to a follow-up**, never "fix in
     this PR" — severity is not scope (see `lib/pr-discipline.md`
     § Scope Discipline).

4. **Write `$PR_DIR/synthesis.md`.** Header by mode — PR mode as shown below; local mode titles it `# Local Review Synthesis: <branch> vs <base> — <REPORT_TS>` and the PR Summary section describes the branch and commit log instead of PR title/author:

   ```markdown
   # PR #<N> Review Synthesis — <REPORT_TS>

   ## PR Summary
   [Title, author, scope]

   ## Intent & Scope
   [What the PR description and linked GitHub issues say this change
   is for — one or two sentences per issue, with numbers. Then: does
   the diff deliver it? Merge the dimensions reviews' Intent gaps
   sections here, deduplicated. If intent.md had no description and no
   issues, say so and note the review is ungrounded on intent.]

   ## CI Status
   [pass / fail / pending — key checks]

   ## Finding Summary
   - Total: N (Blocker: X, High: X, Medium: X, Low: X, Nit: X)
   - Reviews: independent dimensions (IR), adversarial dimensions (AR)<, independent canon (IG), adversarial canon (AG) when --canon ran>

   ## Unified Findings

   | ID | Severity | Category | File:Line | Issue | Suggestion | Evidence | Sources |
   |----|----------|----------|-----------|-------|------------|----------|---------|
   | SR001 | High | Correctness | path/to/file.go:42 | ... | ... | ... | IR003, AR007, AG002 |

   ## Single-Role Findings
   [Findings only one role surfaced (in either of its passes) — note which role and why the other may have missed it]

   ## Dropped
   [Findings whose evidence didn't hold or whose File:Line was malformed, one clause of reason each]

   ## Praise
   [Only when --canon ran: merged from both canon reviews' Praise
   sections, deduplicated, file:line anchors kept. Genuine positives
   only. Omit the section when canon didn't run.]

   ## Overall Assessment
   [2-3 sentences: is this ready to merge, needs changes, or blocked?
   Fold in the canon reviews' Triage notes where they matter —
   split-CL pressure, weak description.]
   ```

## ID prefix convention

Synthesis findings get a fresh `SR` prefix (e.g. `SR001`, `SR002`). The `Sources` column carries the original `IR` / `AR` / `IG` / `AG` IDs for traceability. Downstream nodes (`devils-advocate`, `write-review`, `post`) reference `SR` IDs only.

## Outputs

- `$PR_DIR/synthesis.md`

## Outgoing edges

- → `devils-advocate` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from synthesis --to devils_advocate
```

## Failure modes

- All pooled reviews empty → write a synthesis that says "no findings from either reviewer". Continue to devils-advocate (which becomes a no-op).
- File:Line in one of the reviews is malformed (not `path:line`) → drop those findings during synthesis with a note in Dropped. Don't try to repair.
- The synthesizer fails or writes a file without the Unified Findings table → retry once. Fails again → stop and say so; it's a bug in the brief.
