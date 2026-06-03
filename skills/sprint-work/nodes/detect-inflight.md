# Node: detect-inflight

Phase 5: detect work already done or in flight (issue already closed, in-progress sprint state, uncommitted or unpushed local changes) and decide automatically. Skips finished work; never prompts. Only "every targeted issue is already closed" stops the run here.

## Inputs

- `path_mode`, `repos`, `worktree_paths`, `issue_ids`, `sprint_query`, `session_dir` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
WORKTREE_PATHS=$(scripts/walk.sh get --state "$STATE" --key worktree_paths)
REPORTS_ROOT=$(scripts/walk.sh get --state "$STATE" --key reports_root)
```

## Forgejo paths

**This node is automatic — it never prompts.** There are no PRs in this
flow, so "in flight" is read from the issue's open/closed state (from
`load-context`) plus local git signals, and the node *decides* rather
than asks:

| Signal | Automatic behavior |
|---|---|
| Issue `open`, working tree clean | Fresh start; route via `proceed`. |
| Issue `open`, uncommitted or unpushed local changes on the default branch | Note it briefly, then `proceed` — `implement` layers its work on top and `commit-push` commits everything. |
| Issue `closed` | Already done — its commit landed and Forgejo closed it. Skip it. |

For `forgejo-walk`, check each issue's state and **automatically** filter out any that are already `closed` (don't ask — just skip them). **Persist the filtered list** so `implement` honors the skip:

```bash
scripts/walk.sh set --state "$STATE" --key active_issue_ids --value "<JSON: filtered ref list of still-open issues>"
scripts/walk.sh set --state "$STATE" --key skipped_issue_ids --value "<JSON: skipped ref list, with per-issue reason>"
```

`implement.md`'s forgejo-walk loop reads `active_issue_ids` (not `issue_ids`) so closed-and-skipped issues are excluded. `summarize` reads `skipped_issue_ids` to surface what was skipped and why.

## SPRINT.md path

No issue state; use tracker + git signals. The skill is cwd-independent — the sprint tracker resolves milestones across all repos under `~/Reports/`; check local git state per repo via `worktree_paths`:

```bash
# Sprint tracker status (milestones across all discovered repos):
python3 ~/.claude/lib/forgejo_sprints.py --current
python3 ~/.claude/lib/forgejo_sprints.py --list

# Per repo: uncommitted changes + local commits not yet pushed to the
# default branch's upstream. Iterate the manifest's worktree_paths instead
# of relying on cwd. Each repo's default branch comes from repos[].default_branch.
for ORG_REPO in $(echo "$WORKTREE_PATHS" | jq -r 'keys[]'); do
  WT=$(echo "$WORKTREE_PATHS" | jq -r ".[\"$ORG_REPO\"]")

  # Uncommitted changes:
  git -C "$WT" status --porcelain | head -20

  # Unpushed commits: how far HEAD is ahead of the pushed default branch.
  # @{upstream} is the tracking ref for the checked-out default branch.
  if git -C "$WT" rev-parse --verify '@{upstream}' >/dev/null 2>&1; then
    git -C "$WT" log --oneline '@{upstream}..HEAD' | head -10
  else
    echo "(no upstream set for $ORG_REPO's default branch; skipping ahead-count)"
  fi
done
```

Decide automatically (no prompt):
- **Something to do** (at least one targeted issue still `open`, or sprintmd path) → print a one-line note of any in-flight state found, then route via `proceed`.
- **Nothing to do** (single forgejo-issue already closed, or every forgejo-walk issue already closed) → route via `nothing_to_do`.

## Outputs

- `active_issue_ids` / `skipped_issue_ids` (forgejo-walk) in walker state

## Outgoing edges

- **`proceed`** → `show-plan`. There's work to do; carry on autonomously.
- **`nothing_to_do`** → `terminal`. Every targeted issue is already closed — nothing left to commit.

Record exactly one:

```bash
# Work to do:
scripts/walk.sh transition --state "$STATE" --from detect_inflight --to show_plan --condition proceed

# Nothing left:
scripts/walk.sh transition --state "$STATE" --from detect_inflight --to terminal --condition nothing_to_do
```

## Notes

- **Never prompt here.** The run is autonomous; this node only detects and decides. The only exit is "nothing to do."
- **A closed issue means the work shipped.** Skip it silently (forgejo-walk) or exit with a one-line "already done" note (single issue).
- **In-flight local changes are fine.** Note them and proceed — `implement` layers on top and `commit-push` commits the lot.
