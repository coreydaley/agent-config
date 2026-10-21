# Node: write-review

Format `REVIEW.md` from `synthesis.md`. Transcription, not judgment: every finding, severity, claim status, and the verdict come across unchanged.

## Inputs

- `session_dir`, `source_kind`, `source_id`, `grounded`, `defense_status`, `prior_review` from walker state
- `$SESSION_DIR/synthesis.md`, `context.md`
- `references/report-format.md`

```bash
STATE="$SESSION_DIR/.walk-state.review-design.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
```

## Steps

1. **Header table** from walker state and `context.md`. Reviewers: "independent-reviewer and adversarial-reviewer (Fable)". Defense: the ledger line from the end of `synthesis.md`, or "not run (no findings)", or "failed (<what was missing>)".

2. **Body sections** in the order `references/report-format.md` gives, each copied from the matching synthesis section. Omit a section the synthesis has nothing for, except Verdict, Claim ledger, and Findings, which always appear. An ungrounded run's verdict line ends with "(ungrounded)".

3. **Write `$SESSION_DIR/REVIEW.md`.** Verify it has the header table, a Verdict line with one of the four verdicts, and a Findings table.

4. **Print the path** on its own line:

   ```
   📄 <literal session dir>/REVIEW.md
   ```

## Outputs

- `$SESSION_DIR/REVIEW.md`

## Outgoing edges

- → `display` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from write_review --to display
```

## Failure modes

- A synthesis section is missing that the format requires → write the report with that section marked "not produced by synthesis" rather than inventing content.

## Notes

- **Don't fix the synthesis here.** A finding that looks wrong at this stage stays in. The user sees it with its evidence and decides.
