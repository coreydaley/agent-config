# Node: sweep

The two pre-review sweeps from `lib/pr-discipline.md` § PR Pre-Review Procedure, run against the whole branch diff before anyone else sees it: comment noise, and test assertions that don't test anything. Plus the mechanical checks (internal IDs, feature (parent) issue numbers, secrets, stray binaries). Findings are fixed here, in at most one chore commit.

## Who does this

Steps 2 to 4 run in one Agent call with `subagent_type: verifier`, briefed per `lib/agent-roles.md` § The brief. The orchestrator wrote these comments and tests minutes ago and will read every one as necessary. The verifier gets steps 2 to 4 verbatim plus the Comments and Tests sections of `lib/code-hygiene.md` as the contract, absolute paths to `.sweep-diff.patch` and `$WT`, the parent issue number (if any), and permission to edit only lines the diff added or modified, in comment lines and test files. It writes `$PLAN_DIR/sweep.md` listing every edit (file, line, before, after, reason) and every mechanical-check hit, and touches nothing else. Afterward, `git -C "$WT" diff --name-only` must be a subset of the files in `.sweep-diff.patch`; anything else is reverted and noted. The orchestrator does step 1 (the diff), then steps 5 to 7 (build check, commit, targeted tests, persist) on whatever the subagent changed. A secret hit is reported by the subagent and acted on by the orchestrator (stop and ask).

## Inputs

- `worktree`, `base_ref`, `source_id`, `parent_issue` from walker state
- `lib/code-hygiene.md`

```bash
STATE="$PLAN_DIR/.walk-state.build.json"
WT=$(scripts/walk.sh get --state "$STATE" --key worktree)
BASE_REF=$(scripts/walk.sh get --state "$STATE" --key base_ref)
```

## Steps

1. **The diff:**
   ```bash
   git -C "$WT" diff "$BASE_REF...HEAD" > "$PLAN_DIR/.sweep-diff.patch"
   ```
   Only added or modified lines are in scope. Pre-existing comments and tests the branch didn't touch are not this PR's problem.

2. **Comment sweep.** Every added or changed comment line against the Comments section of `lib/code-hygiene.md`. For each: delete, shorten to one line, or keep with a reason. Function doc comments stay. Anything that restates the code, explains the diff, points elsewhere, or opens with an AI tell goes.

3. **Test sweep.** Every added or changed test against the Tests section: tautologies, doubles that mirror the implementation, missing negative cases, assertions on incidental detail, tests that can't run. Fix what's fixable. A missing negative case gets written, not noted.

4. **Mechanical checks** over the diff:
   - Internal IDs: `\b(SR|PA|CR|IR|AR|IG|AG|DA|A)[0-9]{3}\b` in added lines → remove.
   - Feature (parent) issue: if `parent_issue` is set, `#<parent_issue>` must not appear anywhere in the diff or the commit messages (`git log $BASE_REF..HEAD`).
   - Secrets: `password|secret|api[_-]?key|token` with a literal value on the same added line → stop and ask.
   - Stray files: binaries, `.orig`, editor swap files, anything in `git status --porcelain` that isn't tracked and isn't meant to be.

5. **Commit the sweep**, if it changed anything. One commit:
   ```
   chore(<scope>): tighten comments and test assertions
   ```
   Same mechanics as implement. Zero findings → say so in one line and move on. Two or more sweep commits on one branch is a smell that implement's per-task check isn't doing its job. Note it if it happens.

6. **Re-run targeted tests** for any package the sweep touched. Red → fix before transitioning.

7. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key sweep_findings --value "<count>"
   scripts/walk.sh set --state "$STATE" --key sweep_commit   --value "<sha or empty>"
   ```

## Outputs

- At most one `chore` commit
- `$PLAN_DIR/sweep.md`
- `sweep_findings`, `sweep_commit` in walker state

## Outgoing edges

- → `draft-pr-body` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from sweep --to draft_pr_body
```

## Notes

- **This is the same sweep the pre-review procedure asks for by hand.** Doing it here means pr-review reviews code, not comment noise, and the human review ask that follows isn't blocked on cleanup.
- **Don't widen it.** The sweep is comments, tests, IDs, secrets. Refactoring adjacent code is scope creep with a hygiene label on it.
