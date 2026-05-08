# Node: address

The work-doing node. For each new finding in this iteration's REVIEW.md, dedup against the ledger, apply a fix if possible, verify it, and update the ledger. Findings the agent can't resolve get marked for escalation and routed via `decide`.

## Inputs

- `$ITER_DIR/REVIEW.md` (this iteration's findings)
- `$FINDINGS` (rolling ledger across all runs on this PR)
- The project manifest (for test/lint command detection)
- The local checkout

## Test/lint detection

Detect once per session, cache. Order:

1. **Project doc** — if the project root has `CLAUDE.md` or `AGENTS.md`, read it. Look for canonical commands (most repos document them).
2. **Manifest heuristics** — fall back to:
   - `go.mod` → `go test ./...`, `go vet ./...`, `golangci-lint run` (if `.golangci.yml` exists or the binary is on PATH)
   - `package.json` → `npm test`, `npm run lint` (only if those scripts exist)
   - `pyproject.toml` / `pytest.ini` → `pytest`, `ruff check`, `mypy` (if configured)
   - `Makefile` with `test:` / `lint:` targets → `make test`, `make lint`
3. **No detection** — surface to the user once, ask for the canonical command, cache the answer.

## Steps

For each new finding (CR-NNN) in this iteration's REVIEW.md:

1. **Dedup against the ledger.** Look for existing ledger entries (LR-NNN) where:
   - File:Line matches exactly, AND
   - Issue text Jaccard similarity > ~0.6 over normalized tokens (lowercase, drop punctuation)

   - **Match found, ledger entry was `fixed`** → this is a regression. Update the ledger entry: status to `*regression after iter-<prior>*`, append current iter to `Seen in:`, reopen checkbox. Process this finding (apply a fresh fix attempt) but flag it as a regression in ADDRESSED.md.
   - **Match found, ledger entry was `won't-fix` / `deferred` / `skipped`** → user already decided. Append current iter to `Seen in:`, leave decision in place, skip processing.
   - **Match found, ledger entry was `escalated, awaiting user`** → still awaiting. Append current iter to `Seen in:`, route this finding to escalation again via decide → escalate.
   - **Ambiguous match** (two or more candidates score similarly) → mark this finding as `pending-dedup-check`, route to escalation. Don't process until the user resolves.
   - **No match** → new ledger entry, next `LR-NNN` ID, status `*open*`, populate fields from the CR-NNN.

2. **Apply the fix** (only for findings the agent can confidently fix):
   - Use `Edit` (preferred) or `Write` to apply the change.
   - For findings requiring user judgment (ambiguous diagnosis, design choice, can't determine root cause from the diff alone): mark the ledger entry status as `*escalated, awaiting user*` and skip applying. Decide will route to escalate.

3. **Verify each fix.** After applying a fix:
   - Run the detected test command(s) scoped to the touched files when possible (e.g. `go test ./pkg/...` not `go test ./...` if only one package was edited). Fall back to full suite if scoping isn't reliable.
   - Run the linter on touched files.
   - **If verification passes**: commit the fix with a short message (`fix: <ledger ID> — <issue summary>`), record the SHA in the ledger entry's `Commits:` field, set status to `*fixed in iter-<N>*`, check the box.
   - **If verification fails**: revert the working-tree change (`git checkout -- <files>`), set the ledger entry to `*escalated: fix failed verification*`, record the failure detail in the entry's notes. Decide will route to escalate.

4. **Skip auto-fixes for these classes**: even when "addressable" by the agent, route to escalation instead:
   - Test removals or weakenings (might be intentional)
   - Public API changes
   - Configuration / schema changes
   - Anything the finding's Suggestion field marks with words like "consider", "discuss", "may want to" — those flag user judgment

5. **Write `$ITER_DIR/ADDRESSED.md`** as the audit trail. One entry per finding processed in this iteration:

   ```markdown
   - **CR007 → LR042** — fixed
     - File:Line: pkg/foo/bar.go:88
     - Action: added nil guard before deref
     - Verification: `go test ./pkg/foo/...` passed
     - Commit: abc1234
   ```

   Statuses to record: `fixed`, `escalated`, `dedup-pending`, `regression-detected`, `skipped (user-prior-decision)`.

6. **Update `$FINDINGS`** with the merged ledger state. This is the source of truth — `decide` reads it next.

## Outputs

- `$ITER_DIR/ADDRESSED.md`
- Updated `$FINDINGS` (new entries appended, existing entries updated)
- New commits in working tree (one per fix)

## Outgoing edges

- → `decide` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$PR_DIR/.walk-state.json" --from address --to decide
```

## Failure modes

- Fix attempt corrupts the working tree (e.g. partial Edit, syntax error): revert the file, mark the finding `*escalated: fix failed verification*`, continue processing the rest of the findings.
- Test/lint command not detected and user can't be prompted (skill running unattended): treat verification as inconclusive and mark the finding `*escalated: cannot verify fix*`. Do not commit unverified fixes.
- Multiple fixes touch the same lines and conflict: process serially, re-evaluate after each commit; if the second fix can no longer be applied cleanly, escalate it.
