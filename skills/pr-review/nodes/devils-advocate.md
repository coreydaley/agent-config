# Node: devils-advocate

The devil's advocate attacks the synthesis. Goal: surface false positives, severity miscalibrations, and missing findings — not to "improve" the synthesis. Then an adjudicator rules on each challenge and incorporates the ones that hold.

## Who does this

Two fresh role subagents, one per step, per [`lib/agent-roles.md`](../../../lib/agent-roles.md), as separate Agent calls in sequence:

- **Step 1**: `subagent_type: devils-advocate`. Reads the synthesis and the code, writes `devils-advocate.md`.
- **Step 2**: `subagent_type: adjudicator`, launched only after Step 1 returns. Not the orchestrator: the orchestrator may have written the code the findings are about, and adjudicating an attack on findings about your own code is the exact conflict this pattern exists to remove. The adjudicator never sees the conversation in which the challenge was written, only the synthesis, the challenges, and the evidence.

Each brief follows "The brief" in `lib/agent-roles.md`: the step's rubric below verbatim, absolute paths, the output contract, the untrusted-data line, and the closing line. The orchestrator verifies the artifacts and the ledger line, then transitions.

## Inputs

- `pr_dir`, `pr_number`, `worktree_path` from walker state
- `$PR_DIR/synthesis.md` (the file the devil's advocate will attack)

```bash
STATE="$PR_DIR/.walk-state.review.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
WORKTREE_PATH=$(scripts/walk.sh get --state "$STATE" --key worktree_path)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number || true)  # unset in local mode
```

In local mode, adjust the rubric's first sentence the same way as `independent-reviews`: the synthesis is "for the changes on branch `$BRANCH`" rather than "for PR #N".

## Step 1 — The challenge

Brief for the `devils-advocate` role. Inputs: `$PR_DIR/synthesis.md`, `$PR_DIR/diff.patch`, `$WORKTREE_PATH` (read-only). Writes only `$PR_DIR/devils-advocate.md`.

> Read $PR_DIR/synthesis.md. This is a synthesized code review
> for PR #$PR_NUMBER. Your job is to attack it, not improve it.
> Write your challenge to $PR_DIR/devils-advocate.md covering:
> (1) False positives — findings that reflect intentional, correct
> choices rather than actual problems.
> (2) Severity miscalibrations — findings rated too high or too low
> given actual impact.
> (3) Missing findings — real issues the reviews missed.
> (4) Suggestions that are impractical or would introduce new problems.
> Number each challenge (DA001, DA002, ...). Be specific. Every
> challenge must cite the finding ID AND concrete, checkable evidence:
> a file:line in the codebase at $WORKTREE_PATH, a documented contract,
> an existing test, or a reproduction of the claimed misreading. A
> challenge that is only a counter-assertion ('this is fine', 'this is
> intentional') without evidence will be rejected.

Wait for the Agent call to return. Verify `devils-advocate.md` exists and is non-empty (zero challenges, stated plainly, is a valid result).

## Step 2 — Adjudicate challenges

Brief for the `adjudicator` role. Inputs: `$PR_DIR/synthesis.md`, `$PR_DIR/devils-advocate.md`, `$PR_DIR/diff.patch`, `$WORKTREE_PATH` (read-only). Writes `$PR_DIR/adjudication.md` and may edit `$PR_DIR/synthesis.md` in place, the finding rows and the sections named below, and nothing else.

> Read $PR_DIR/devils-advocate.md. The devil's advocate is one-sided — a single role attacking, with no defender — so the structural bias here is toward killing findings. You neither wrote the code nor the synthesis, and the burden of proof is on the challenge:
>
> - **A challenge with no checkable evidence is rejected**, whatever its confidence. Counter-assertion isn't refutation.
> - **Verify before you drop.** Before removing any finding, open the cited evidence in $WORKTREE_PATH yourself and confirm the challenge holds. If you can't reproduce the refutation, the finding stays.
> - **Cross-role findings get extra protection.** A finding whose Sources span both reviewer roles (e.g. `IR`+`AG`) was independently reached twice. Never drop it on the challenge text alone — only after your own verification decisively confirms the false positive. When in doubt, keep it and note the dispute.
> - **Prefer demote over drop.** A challenge with merit that isn't decisive (real issue, overstated impact) lowers severity; it doesn't delete.
> - **Don't escalate severity** on the challenge alone. Severity bumps need real evidence of impact.
>
> Write $PR_DIR/adjudication.md: one row per challenge, `| Challenge | Finding | Ruling | Reason | Evidence |`, Ruling one of upheld, partly upheld, rejected, reason one clause.
>
> Then apply the dispositions to $PR_DIR/synthesis.md in place:
>
> - **Verified false positive** → remove the finding. Document **why**, with the evidence you verified, in a "Removed False Positives" section at the bottom of synthesis.md.
> - **Valid severity recalibration** → change the severity in synthesis.md. Note the change inline.
> - **Missing finding raised by the devil's advocate** → add as a new SR-prefix entry, mark its source as "devils-advocate". It gets the same evidence bar: verify before adding.
> - **Rejected challenge** → leave the synthesis as-is, document the rejection inline so the audit trail is intact.
>
> End the pass by appending a one-line ledger to synthesis.md so strike-downs are auditable at a glance: `Devil's advocate: N challenges — X rejected, Y demoted, Z removed, W added.`

The synthesis.md is the artifact that flows into `write-review`. Don't write a separate "synthesis-v2" — it's updated in place. `devils-advocate.md` and `adjudication.md` remain as the audit trail for what was challenged and how each challenge was ruled.

After the call returns, verify `adjudication.md` has a row per challenge and synthesis.md ends with the ledger line. Retry once on a missing or malformed artifact; a second failure is a bug in the brief, so stop and say so.

## Outputs

- `$PR_DIR/devils-advocate.md` (the raw challenge)
- `$PR_DIR/adjudication.md` (one ruling per challenge)
- `$PR_DIR/synthesis.md` (updated in place with upheld challenges incorporated)

## Outgoing edges

- → `write-review` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from devils_advocate --to write_review
```

## Failure modes

- The devil's advocate fails or returns empty after its retry → skip Step 2, route to `write-review`. Note "no devil's-advocate challenges" in the final REVIEW.md.
- Zero challenges → skip Step 2 and append the ledger line yourself (`Devil's advocate: 0 challenges.`); that's transcription, not judgment.
- The challenges are themselves wrong (e.g., misread the diff) → the adjudicator rejects them and documents why. The whole point is critical evaluation, not blind acceptance.

## Notes

- **Don't capitulate to the devil's advocate.** It's a critical pass, not an authority. The adjudicator rejects challenges that don't hold up.
- **A removed finding is unrecoverable downstream** — the user never sees it in REVIEW.md, only in the Removed False Positives ledger. That asymmetry is why the evidence bar for dropping is higher than for keeping: a kept false positive costs the user a minute of reading; a dropped true positive can cost a shipped bug.
