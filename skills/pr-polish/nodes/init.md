# Node: init

Resolve the PR, confirm it's ours, find its worktree and plan, work out the commit regime, and check whether it already merged. Set paths, initialize walker state.

## Inputs

- `$ARGUMENTS`: optional PR number or URL, `--help`
- Current git checkout

## Steps

1. **`--help` anywhere** → print the help blurb from SKILL.md verbatim and stop.

2. **Session model.** This phase runs on Opus. Read the current session with the `get_session` tool (session `self`) and check `model`. A `model` that doesn't start with `claude-opus-` → stop before creating any state. Name the model the session is on and tell the user to switch to Opus in the model picker and re-run. A skill can read its session's model but not change it. Planning (`/pr-plan`) may run on any model. This phase doesn't.

3. **The PR.** From the argument, or `gh pr view` on the current branch. None → bail. Fetch:
   ```bash
   gh pr view "$PR" --json number,url,title,body,state,isDraft,author,baseRefName,headRefName,headRefOid,mergedAt,reviews,comments,reviewThreads,commits,statusCheckRollup > "$POLISH_DIR/pr.json"
   ```
   (Create `$POLISH_DIR` first, see step 7.)

   Ours only: `.author.login` must equal `gh api user -q .login`. Otherwise bail, "pr-polish tidies our own PRs."

4. **Merged or closed?**
   - `state=MERGED` → route `already_merged`. finalize records it in PLAN.md and stops. Nothing else to do.
   - `state=CLOSED` (not merged) → bail. Nothing to polish on a closed PR.
   - `OPEN` → continue.

5. **Worktree.** The branch's own worktree must exist (never a `pr-review-<N>/`). Same lookup as pr-fix. Dirty tree → show it and ask keep / stash / cancel. Local HEAD must equal `headRefOid`. Ahead → bail, "push first, polish tidies what's on the PR." Behind → bail, "pull first."

6. **Plan and regime.** `KEY` from `headRefName` (`/` → `-`), with the plan directory from the shared resolver rather than a hand-built path (see `lib/pr-artifacts.md`):

   ```bash
   REPORTS_BASE=$(python3 "$HOME/.claude/lib/paths.py" reports-base) || exit 1
   KEY=$(gh pr view "$PR" --json headRefName -q .headRefName | tr '/' '-')
   PLAN_DIR="$REPORTS_BASE/prs/$KEY"
   ```

   `plan_available` if `PLAN.md` exists. `human_review_started` is true when any review or comment on the PR is from a non-bot author who isn't us. This decides whether the commit history may be rewritten at all:

   | Human review started | Commit cleanup |
   |---|---|
   | no | offered: regroup, scrub internal artifacts, tighten messages, `--force-with-lease` |
   | yes | not offered. analyze proposes a squash-merge commit message instead |

7. **Paths and state.**
   ```bash
   TS=$(date +%Y-%m-%dT%H-%M-%S)
   POLISH_DIR="$PLAN_DIR/polish/$TS"
   mkdir -p "$POLISH_DIR"
   STATE="$PLAN_DIR/.walk-state.polish.json"
   scripts/walk.sh init --state "$STATE"
   scripts/walk.sh set --state "$STATE" --key pr_number            --value "<N>"
   scripts/walk.sh set --state "$STATE" --key pr_url               --value "<url>"
   scripts/walk.sh set --state "$STATE" --key pr_state             --value "<OPEN|MERGED>"
   scripts/walk.sh set --state "$STATE" --key repo                 --value "$ORG_REPO"
   scripts/walk.sh set --state "$STATE" --key branch               --value "<headRefName>"
   scripts/walk.sh set --state "$STATE" --key base_branch          --value "<baseRefName>"
   scripts/walk.sh set --state "$STATE" --key worktree             --value "$WT"
   scripts/walk.sh set --state "$STATE" --key plan_dir             --value "$PLAN_DIR"
   scripts/walk.sh set --state "$STATE" --key plan_available       --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key polish_dir           --value "$POLISH_DIR"
   scripts/walk.sh set --state "$STATE" --key human_review_started --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key head_at_init         --value "<headRefOid>"
   ```
   Fetch the base fresh (`git -C "$WT" fetch <upstream|origin> <base> --quiet`, `upstream` when that remote exists, since origin is then the fork) and record `base_ref`.

8. **Opening lines:** PR, draft or not, regime in one sentence ("no human review yet, commit cleanup is on the table" or "reviewed by @x on <date>, history is append-only from here"), plan found or not.

## Outputs

- `$POLISH_DIR/pr.json`
- `$PLAN_DIR/.walk-state.polish.json`

## Outgoing edges

- **`pr_open`** → `analyze`
- **`already_merged`** → `finalize`

```bash
scripts/walk.sh transition --state "$STATE" --from init --to analyze  --condition pr_open
scripts/walk.sh transition --state "$STATE" --from init --to finalize --condition already_merged
```

## Failure modes

- Session not on Opus → bail before anything else, naming the model.
- No PR, not ours, closed, worktree missing, local out of sync → bail before state exists (merged is the one non-open state that continues).
- `gh` unauthenticated → bail.
