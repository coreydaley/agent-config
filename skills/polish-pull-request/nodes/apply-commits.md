# Node: apply-commits

History rewrite and force-push. Per-PR, sequential. **`--force-with-lease` only**, never `--force`.

## Inputs

- `pr_set`, `proposals_path`, `cleanup_decisions` from walker state
- The proposed commit groups from `analyze`

```bash
STATE="<path>"
PROPOSALS=$(scripts/walk.sh get --state "$STATE" --key proposals_path)
CLEANUP_DECISIONS=$(scripts/walk.sh get --state "$STATE" --key cleanup_decisions)
```

## Steps

For each PR (sequential — don't parallelize history rewrites across PRs):

1. **Find the base ref:**
   ```bash
   BASE=$(gh pr view "$PR" --json baseRefName -q .baseRefName)
   HEAD_REF=$(gh pr view "$PR" --json headRefName -q .headRefName)
   ```

2. **Reset and re-commit.** Use `--soft` so all changes (including any staged comment edits from `apply-comments`) become uncommitted-but-staged:
   ```bash
   git reset --soft "origin/$BASE"
   ```

3. **For each proposed group** (in foundational-first order from the proposal):
   ```bash
   git restore --staged .
   git add <explicit-file-list-for-this-group>
   git commit -m "$(cat <<'EOF'
   <type>(<scope>): <summary>

   <optional body — only if why is non-obvious>

   Addresses <LINEAR-ID>
   Co-authored-by: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

   Format rules (mirrors `~/.claude/skills/commit/SKILL.md`):

   - Conventional Commits types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci`
   - Summary: imperative, lowercase, no trailing period; `type(scope): summary` line ≤72 chars
   - Body explains *why*, not *what*; omit when self-evident
   - `Addresses <LINEAR-ID>` only when the original commit had it
   - Stage explicit file lists; **never `git add -A` or `git add .`**
   - **Never `--no-verify`, never `--amend`**

4. **Force-push** with `--force-with-lease`:
   ```bash
   git push --force-with-lease origin "HEAD:$HEAD_REF"
   ```

   If the push is rejected (someone pushed to the branch since we fetched in `preflight-cleanup`):

   - **Stop the entire run.** Don't retry. Don't `--force`.
   - The local branch is now in a rewritten state, ahead of and divergent from remote.
   - Surface the conflict. Tell the user: their local SHAs no longer match remote, and they need to decide (typical resolutions: re-fetch and re-run polish, or `git reset --hard origin/<head-ref>` to throw the rewrite away).
   - Route to `summarize` so the user sees what other PRs (if any) were processed before this one.

5. **Persist results:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key commit_results --value "<JSON: per-PR applied/failed>"
   ```

## Outputs

- Rewritten branch history on the local clone
- Force-pushed remote head
- `commit_results` in walker state

## Outgoing edges

- → `summarize` (always — single outgoing edge, success or fail)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from apply_commits --to summarize
```

## Constraints

- **Never `git push --force`.** `--force-with-lease` only.
- **Never rewrite collaborator commits.** Pre-flight catches this; if somehow we got here with collaborator commits, **stop** and surface.
- **Never push to a remote branch other than the PR's head ref.**
- **Never merge.** That's the user's call after polish.
- **Never `--no-verify`** on commits or pushes.

## Failure modes

- `git reset --soft` fails (somehow not in a git repo by this point) → impossible-but-handle: surface error, route to summary.
- A `git commit` fails on a hook → don't `--no-verify`. Surface the hook error, stop the loop, route to summary. The local branch is in a partially-rewritten state — the summary needs to flag this clearly so the user can recover.
- `git push --force-with-lease` rejected → see step 4 above. Don't retry, don't `--force`.
