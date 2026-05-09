# Node: detect-repo

Phase 3: build the repo manifest and resolve the sprint's branch name. The result drives `verify-worktree`, `implement`, and `open-prs`.

## Inputs

- `path_mode`, `context_dir`, `sprint_md_path` from walker state

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
SPRINT_MD=$(scripts/walk.sh get --state "$STATE" --key sprint_md_path)
```

## Repository manifest

The **Repositories** section in SPRINT.md is the authoritative source. Format:

```markdown
## Repositories
- acme/web-app (primary)
- acme/api
```

Each entry is `<org>/<repo>` matching the GitHub path. The first entry (or one tagged `(primary)`) is the primary repo for cross-link ordering in `open-prs`.

### Resolution order

1. **`Repositories` section in SPRINT.md** — preferred source. Single entry → single-repo. Multiple → multi-repo.
2. **`Repositories` section in LINEAR.md** — `/sprint-plan-to-linear/finalize.md` carries the manifest into LINEAR.md verbatim so the Linear path can resolve repos without depending on SPRINT.md being reachable. Read `linear_md_path` from walker state (set by `load-context`) and parse its `## Repositories` section.
3. **Linear issue body** — for `linear-issue` / `linear-walk`, fall back to the issue's Files section and any GitHub URLs in the description if neither SPRINT.md nor LINEAR.md has a Repositories section.
4. **Files Summary in SPRINT.md** — last-resort inference for older SPRINT.md files that predate the Repositories section.

If multiple sources are present, prefer (1). If (1) is missing, log a note for `recommend-execution`'s DoR check (it'll surface as a missing-manifest warning on the next plan run) but continue with (2)/(3) for this run.

## Branch name

For each branch unit (one Linear issue, or one SPRINT.md sprint) the **same branch name applies to every repo it touches**. This is what makes the change set discoverable across repos by branch name.

- **`linear-issue` / `linear-walk` (per issue):** use Linear's `branchName` field (e.g., `coreydaley/proj-1148-add-full-tag-support-for-python`). For `linear-walk`, this is per-issue and resolved inside `implement`'s loop, not here. Persist the milestone-level branch list as `issue_branches`.
- **`sprintmd`:** resolve in this order:
  1. **Sidecar**: if `$SESSION_DIR/.branch` exists from a prior run, read it. This makes the branch durable across `/sprint-work` invocations on the same sprint.
  2. **Current branch**: if the user is in a worktree on a feature branch (not `main` / default), use that.
  3. **Prompt once**: ask "What branch name for this sprint?".

After resolution, **always persist** `branch_name` to `$SESSION_DIR/.branch` — regardless of whether it came from the sidecar (no-op write), current-branch detection, or the prompt. This guarantees subsequent runs find the same branch even if the user switched cwd or the worktree's branch since.

```bash
echo "$BRANCH_NAME" > "$SESSION_DIR/.branch"
```

If the sidecar already exists with a *different* value than the resolved branch (e.g., user switched the worktree's branch since the prior run), surface a warning before overwriting:

```
Sprint's recorded branch is <prior>; current resolution picked <new>.
Update .branch to <new>? (yes / cancel)
```

On cancel, bail to terminal — the user resolves the discrepancy manually.

The sidecar is plain text, one line, the branch name. Subsequent steps read `branch_name` from walker state, which is loaded from the sidecar on entry.

## Persist results

```bash
scripts/walk.sh set --state "$STATE" --key repo_mode    --value "<single|multi>"
scripts/walk.sh set --state "$STATE" --key repos        --value "<JSON list of {org, repo, primary} entries>"
scripts/walk.sh set --state "$STATE" --key branch_name  --value "<branch>"           # sprintmd / single-issue
scripts/walk.sh set --state "$STATE" --key issue_branches --value "<JSON: issue_id → branchName>"  # linear-walk only
scripts/walk.sh set --state "$STATE" --key merge_order  --value "<JSON list or empty>"
```

`repos` example:

```json
[
  {"org": "acme", "repo": "web-app", "primary": true},
  {"org": "acme",    "repo": "api",           "primary": false}
]
```

## Outputs

- `repo_mode`, `repos`, `branch_name` (or `issue_branches`), `merge_order` in walker state

## Outgoing edges

- → `verify-worktree` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from detect_repo --to verify_worktree
```

## Notes

- **The Repositories manifest is what makes cwd-independence work.** Without it, the skill has to infer repo intent from cwd or file paths. With it, the skill knows where to operate before any worktree work happens.
- **For multi-repo with no explicit merge order**, default to alphabetical by `org/repo`. `open-prs` will surface this in cross-links.
- **Don't pick a primary** silently when SPRINT.md doesn't tag one. Default to alphabetical-first and note it in walker state for `summarize` to surface.
