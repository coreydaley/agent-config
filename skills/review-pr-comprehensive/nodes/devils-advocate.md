# Node: devils-advocate

Codex attacks the synthesis. Goal: surface false positives, severity miscalibrations, and missing findings — not to "improve" the synthesis. Then incorporate valid challenges.

## Inputs

- `pr_dir`, `pr_number`, `worktree_path` from walker state
- `$PR_DIR/synthesis.md` (the file Codex will attack)

```bash
STATE="$PR_DIR/.walk-state.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
WORKTREE_PATH=$(scripts/walk.sh get --state "$STATE" --key worktree_path)
```

## Step 1 — Run Codex's challenge

Same flag rationale as `independent-reviews` (see [`lib/codex-invocation.md`](../../../lib/codex-invocation.md)).

```bash
codex exec \
  -s workspace-write \
  --add-dir "$PR_DIR" \
  -C "$WORKTREE_PATH" \
  -- "Read $PR_DIR/synthesis.md. This is a synthesized code review \
  for PR #$PR_NUMBER. Your job is to attack it, not improve it. \
  Write your challenge to $PR_DIR/devils-advocate.md covering: \
  (1) False positives — findings that reflect intentional, correct \
  choices rather than actual problems. \
  (2) Severity miscalibrations — findings rated too high or too low \
  given actual impact. \
  (3) Missing findings — real issues both reviewers missed. \
  (4) Suggestions that are impractical or would introduce new problems. \
  Be specific. Every challenge must cite the finding ID." \
  < /dev/null
```

Wait for Codex to finish.

## Step 2 — Incorporate challenges into the synthesis

Read `$PR_DIR/devils-advocate.md`. For each challenge:

- **Confirmed false positive** → remove the finding from the synthesis. Document **why** in a "Removed False Positives" section at the bottom of synthesis.md (or in REVIEW.md when written later).
- **Valid severity recalibration** → change the severity in synthesis.md. Note the change inline.
- **Missing finding raised by devil's advocate** → add as a new SR-prefix entry to synthesis.md, mark its source as "devils-advocate".
- **Rejected challenge** → leave the synthesis as-is, document the rejection inline so the audit trail is intact.

The synthesis.md is the artifact that flows into `write-review`. Don't write a separate "synthesis-v2" — update synthesis.md in place. The devils-advocate.md remains as the audit trail for what was challenged and how each challenge was handled.

## Outputs

- `$PR_DIR/devils-advocate.md` (the raw challenge)
- `$PR_DIR/synthesis.md` (updated in place with valid challenges incorporated)

## Outgoing edges

- → `write-review` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from devils_advocate --to write_review
```

## Failure modes

- Codex fails or returns empty → skip the incorporation step, route to `write-review`. Note "no devil's-advocate challenges" in the final REVIEW.md.
- Codex's challenges are themselves wrong (e.g., misreads the diff) → reject them and document. The whole point is critical evaluation, not blind acceptance.

## Notes

- **Don't capitulate to Codex.** Devil's advocate is a critical pass, not an authority. Reject challenges that don't hold up.
- **Don't escalate severity** based on devil's-advocate alone. Severity bumps need real evidence of impact, not "Codex says so."
