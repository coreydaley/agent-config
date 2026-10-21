# Node: init

Locate the approved plan, validate it can be built, set paths, initialize walker state. No git or filesystem changes outside the plan directory.

## Inputs

- `$ARGUMENTS`: optional `<key | branch | path to PLAN.md>` and `--help`
- Current git checkout

## Steps

1. **`--help` anywhere in args** → print the help blurb from SKILL.md verbatim and stop.

2. **Session model.** This phase runs on Opus. Read the current session with the `get_session` tool (session `self`) and check `model`. A `model` that doesn't start with `claude-opus-` → stop before creating any state. Name the model the session is on and tell the user to switch to Opus in the model picker and re-run. A skill can read its session's model but not change it. Planning (`/pr-plan`) may run on any model. This phase doesn't.

3. **Resolve the repo.** Must be inside a git checkout, else bail. Derive `<org>/<repo>` with `python3 "$HOME/.claude/lib/paths.py" org-repo` (`upstream`, falling back to `origin`). Record the bare-clone or repo root: for a worktree, `git rev-parse --git-common-dir` resolved to its parent is the bare clone. For a regular clone, `git rev-parse --show-toplevel`.

4. **Locate PLAN.md.** Resolve the plans directory first, never a hand-built path (see `lib/pr-artifacts.md`):

   ```bash
   PRS_BASE="$(python3 "$HOME/.claude/lib/paths.py" reports-base)/prs" || exit 1
   ```

   - Path argument ending in `PLAN.md` that exists → use it.
   - Key or branch argument → `$PRS_BASE/<arg with / → ->/PLAN.md`.
   - No argument → current branch. On the default branch or detached with no argument, bail: "pass the plan's key, branch, or path. Run `ls $PRS_BASE` to see them."

   Missing file → bail: "no plan at `<path>`. Run /pr-plan first."

5. **Validate the plan.** Parse the header table.
   - `Status` must be `approved`, `building`, or `in-review`. `draft` → bail: "plan isn't approved yet, finish /pr-plan." `no-build` → bail with the recorded reason. `merged` → bail.
   - `Repo` must match the resolved repo.
   - `Branch` is the branch to build on. Strip a trailing `(proposed)` marker and note `branch_proposed=true` when it was there.
   - `Base` gives `<default> @ <sha>`. Record both. `@ pending` or `@ unknown` → setup-worktree re-resolves.
   - `Tasks` section must exist with at least one item. A plan from before the Tasks section existed → bail: "plan has no Tasks section, re-run /pr-plan to revise it."

6. **Initialize walker state:**
   ```bash
   STATE="$PLAN_DIR/.walk-state.build.json"
   scripts/walk.sh init --state "$STATE"
   scripts/walk.sh set --state "$STATE" --key repo           --value "$ORG_REPO"
   scripts/walk.sh set --state "$STATE" --key repo_root      --value "<bare clone or regular-clone root>"
   scripts/walk.sh set --state "$STATE" --key plan_dir       --value "$PLAN_DIR"
   scripts/walk.sh set --state "$STATE" --key plan_path      --value "$PLAN_DIR/PLAN.md"
   scripts/walk.sh set --state "$STATE" --key branch         --value "$BRANCH"
   scripts/walk.sh set --state "$STATE" --key branch_proposed --value "<true|false>"
   scripts/walk.sh set --state "$STATE" --key default_branch --value "$DEFAULT"
   scripts/walk.sh set --state "$STATE" --key base_sha       --value "<sha or empty>"
   scripts/walk.sh set --state "$STATE" --key source_id      --value "<from the plan's Source row: org/repo#N, a PR url, a file path, or none>"
   scripts/walk.sh set --state "$STATE" --key parent_issue   --value "<feature (parent) issue number from source.md, or empty>"
   scripts/walk.sh set --state "$STATE" --key plan_status    --value "<approved|building|in-review>"
   ```

7. **Print a two-line opening:** plan title, branch, task count, status. Example:

   > Building "Stop retrying on 4xx responses" on `fix/gh-123-retry-budget` (4 tasks, plan approved 2026-09-11).

## Outputs

- `$PLAN_DIR/.walk-state.build.json` with the keys above

## Outgoing edges

- → `setup-worktree` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from init --to setup_worktree
```

## Failure modes

- Session not on Opus → bail before anything else, naming the model.
- Not in a checkout, no plan, wrong status, repo mismatch, no Tasks → bail before creating state.
- Header table unparseable → bail and name the row. Don't guess a branch.
