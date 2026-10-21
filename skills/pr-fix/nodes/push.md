# Node: push

Get the fixes onto the PR in the right regime, with a gate before the network write. Pre-review: autosquash the fixups into their originals and force-with-lease. Post-review: plain push, append-only. Or leave everything local.

## Inputs

- `worktree`, `branch`, `base_ref`, `regime`, `fix_commits`, `pr_number`, `human_review_started` from walker state

```bash
STATE="$PLAN_DIR/.walk-state.fix.json"
WT=$(scripts/walk.sh get --state "$STATE" --key worktree)
BASE_REF=$(scripts/walk.sh get --state "$STATE" --key base_ref)
REGIME=$(scripts/walk.sh get --state "$STATE" --key regime)
```

## Steps

1. **Nothing committed** (`fix_commits=0`) → say so, `push_result=nothing`, transition.

2. **Re-check the regime right now.** Time has passed since init. Re-query the PR's reviews and comments. If a human has commented since init and `regime=squash`, the regime flipped: the fixups must not be squashed. Say so, and treat as `append` (fixup commits stay as-is, which is ugly but honest. Offer to reword them into normal commits before pushing).

3. **Ask** with `AskUserQuestion` (nothing deliverable was displayed this turn):

   **squash regime:**
   1. **Squash and push**: autosquash the fixups into their commits, `--force-with-lease`.
   2. **Push as-is**: fixup commits pushed unsquashed (you'll squash later, or pr-polish will).
   3. **Leave local**: nothing pushed.

   **append regime:**
   1. **Push**: new commits on top, normal push.
   2. **Leave local**.

   No PR yet (`review` mode before the branch was ever pushed) → only "leave local" makes sense. pr-build's open-pr is the path to a PR. Say so and skip the question.

4. **Squash and push.** Preflight, then act:
   ```bash
   [ -z "$(git -C "$WT" status --porcelain)" ] || bail "tree dirty"
   git -C "$WT" fetch origin "$BRANCH" --quiet
   [ "$(git -C "$WT" rev-parse "origin/$BRANCH")" = "$(git -C "$WT" merge-base "origin/$BRANCH" HEAD)" ] || bail "remote has commits we don't; pull first"
   git -C "$WT" log --format=%ae "$BASE_REF..HEAD" | sort -u   # must be only us
   GIT_SEQUENCE_EDITOR=true git -C "$WT" rebase -i --autosquash "$BASE_REF" > /tmp/pr-fix-rebase.out 2>&1; EXIT=$?
   ```
   Rebase conflict → `git rebase --abort`, show the output, fall back to offering "push as-is." Then:
   ```bash
   git -C "$WT" push --force-with-lease origin "$BRANCH" > /tmp/pr-fix-push.out 2>&1; EXIT=$?
   ```
   Lease rejected → someone pushed. Don't retry with `--force`. Show it and stop with `push_result=rejected`.

5. **Push as-is / append push:**
   ```bash
   git -C "$WT" push origin "$BRANCH" > /tmp/pr-fix-push.out 2>&1; EXIT=$?
   ```

6. **Persist:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key push_result --value "<squashed|pushed|local|rejected|nothing>"
   ```

## Outputs

- Branch pushed (or not), history squashed (or not)
- `push_result` in walker state

## Outgoing edges

- → `draft-replies` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from push --to draft_replies
```

## Notes

- **`--force-with-lease` only, and only in squash regime.** A plain `--force` is never typed by this skill.
- **The regime is re-checked at push time, not trusted from init.** The window between triage and push is exactly when a reviewer shows up.
- **The user's reply to the question is the authorization.** Approving the triage table did not authorize a push.
- **`origin` is the push target either way.** With an `upstream` remote, origin is the fork the PR's head lives on. Without one, origin is the repo the PR is on.
