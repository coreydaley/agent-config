# Node: detect-repo

Phase 3: determine whether this sprint is single-repo or multi-repo. The result drives `verify-worktree`, `implement`, and `open-prs`.

## Inputs

- `path_mode`, `context_dir`, `sprint_md_path` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
```

## Steps

### Linear paths

Parse the issue description's **Files** section and any GitHub URLs in the body. Multi-repo when:

- Files span repos (e.g., one repo's path + another's).
- The body explicitly calls out work in multiple repos.
- An explicit **Merge order** section names PRs across repos.

### SPRINT.md path

Parse the SPRINT.md **Files Summary** table and any GitHub URLs. Multi-repo is rare for SPRINT.md sprints but possible if the plan explicitly says so.

**Default to single-repo unless evidence indicates otherwise.**

## Persist results

```bash
scripts/walk.sh set --state "$STATE" --key repo_mode  --value "<single|multi>"
scripts/walk.sh set --state "$STATE" --key repos      --value "<JSON list of repo paths>"
scripts/walk.sh set --state "$STATE" --key merge_order --value "<JSON list or empty>"
```

`repos` is a list of `{repo_dir, branch}` entries. For single-repo, length 1.

## Outputs

- `repo_mode`, `repos`, `merge_order` in walker state

## Outgoing edges

- → `verify-worktree` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from detect_repo --to verify_worktree
```

## Notes

- **Don't auto-create or auto-cd.** Worktree management lives in `verify-worktree` and remains user-driven.
- **For multi-repo with no explicit merge order**, default to alphabetical. `open-prs` will surface this.
