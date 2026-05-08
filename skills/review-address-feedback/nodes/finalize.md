# Node: finalize

Run the full project test suite, print a concise summary, draft a Conventional Commit message. Stop. Do not commit, do not push.

## Inputs

- `pr_number`, `session_dir`, `addressed_path` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
```

## Steps

1. **Run the full project test suite.** Detect project type and run the canonical command:
   - Go: `go test ./...`
   - Python: `pytest` (or `make test` if a Makefile defines it)
   - Node: `npm test` (or yarn / pnpm equivalent)
   - Multi-language / monorepo: ask the user for the right top-level command if it's not obvious.

   Capture pass/fail and surface failures verbatim. Save full output to `$SESSION_DIR/final-test.log`.

   If anything is red, **do not draft a commit message**. Tell the user what failed and let them decide whether to fix, skip, or commit anyway with `--no-verify` (their call, not yours).

2. **Print a concise summary:**

   ```
   Files changed: <git diff --stat first line>
   Findings: <N> fixed, <N> won't-fix, <N> deferred, <N> skipped
   GitHub: <N> replies posted, <N> threads resolved
   Tests: <PASS|FAIL>
   Artifacts:
     $SESSION_DIR/ADDRESSED.md
     $SESSION_DIR/final-test.log
   ```

3. **Draft a Conventional Commit message** (only if tests passed). No internal review IDs in the message. Format:

   ```
   <type>(<scope>): <short summary>

   - <bullet describing fix 1>
   - <bullet describing fix 2>

   Co-authored-by: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
   ```

   Pick `<type>` from `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci` based on the actual changes. Imperative mood, lowercase, no trailing period, summary line ≤72 chars.

   Show the draft. **Do not run `git add`, `git commit`, or `git push`.** The user runs those when they're ready.

## Outputs

- `$SESSION_DIR/final-test.log`
- Printed summary
- Drafted commit message (if tests passed)

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to terminal
```

## Notes

- **Tests fail → no commit draft.** Don't draft a commit message and put the user in the awkward position of either committing red code or having to manually rewrite. Surface the failure cleanly and let them drive.
- **Linear IDs in the commit body are fine** when relevant ("Fixes the issue tracked in CON-1234"). Internal review IDs (`R001` etc.) are not.
- **Don't commit, don't push.** Per the global git rule, those wait for the user's explicit "commit" / "push."
