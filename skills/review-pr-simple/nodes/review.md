# Node: review

Read the diff carefully and write a structured `REVIEW.md`.

## Inputs

- `$PR_DIR/diff.patch` (the source under review)
- `$PR_DIR/metadata.json` (PR title, author, base, head SHA — for the review header)
- `$PR_DIR/ci-status.txt` (for the CI summary section)

```bash
STATE="$PR_DIR/.walk-state.json"
PR_DIR=$(scripts/walk.sh get --state "$STATE" --key pr_dir)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
```

## Steps

1. **Read the diff carefully.** Don't just scan — read every hunk. Open files in the working tree as needed for context (callers, surrounding code, contracts).
2. **Cover all five dimensions:**
   - **Correctness** — logic errors, edge cases, API misuse, incorrect assumptions
   - **Security** — injection risks, credential handling, trust boundary violations
   - **Design** — pattern adherence, unnecessary complexity, abstraction quality
   - **Tests** — missing coverage, weak assertions, test data quality
   - **Readability** — unclear names, missing non-obvious comments, dead code
3. **Use the canonical finding schema** for the table:

   ```
   | ID | Severity | Category | File:Line | Issue | Suggestion |
   |----|----------|----------|-----------|-------|------------|
   | R001 | High | Correctness | path/to/file.go:42 | What is wrong | What to do instead |
   ```

   ID prefix: `R`. Severity: Blocker, High, Medium, Low, Nit. Category: Correctness, Security, Design, Tests, Readability, Style.

   **File:Line is required and must be real.** Always `path/to/file.go:42` or `path/to/file.go:42-55` — never a function name. Derive line numbers from hunk headers (`@@ -old +NEW @@` — `NEW` is the starting line in the new file). If you can't determine an exact line, drop the finding.

4. **Write `$PR_DIR/REVIEW.md`** with this shape:

   ```markdown
   # Code Review: PR #<N> — <Title>

   **Author**: <author> | **Base**: <base> | **Date**: <ISO date>

   ## Summary

   <1 paragraph — ready to merge / needs changes / blocked, and why.>

   ## CI Status

   <pass / fail / pending — key checks summarized.>

   ## Findings

   <table; Blocker through Medium go here>

   ## Nits

   <Low / Nit findings here, kept separate to keep the main table clean>

   ## What's Well Done

   <2–4 bullets on what the PR does right. Required, not optional.>

   ---
   *Reviewed by Claude.*
   *Diff: `$PR_DIR/diff.patch`*
   ```

5. **"What's Well Done" is mandatory.** Reviews that only list problems read as adversarial. The section is short — two to four sentences — but balances the tone and gives the author something to anchor on.

## Outputs

- `$PR_DIR/REVIEW.md` exists and is well-formed

## Outgoing edges

- → `display` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from review --to display
```

## Failure modes

- Diff is too large to review in one pass: write a partial REVIEW.md scoped to what you read, with a clear note in the Summary section about the unreviewed portion. Don't guess at hunks you didn't read.
- Cannot determine an exact line number for a finding: drop the finding rather than approximate.
- File:Line points at a deleted line: that's fine for findings about removal — anchor at the deletion point's old/new line.
