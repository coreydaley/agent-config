# Node: resolve-target

Resolve the **feature issue** from `target_args`, then expand its native **sub-issues** (the linked work items created by `/feature-plan`). Sets the sub-issue work list and identifiers for downstream nodes.

## Inputs

- `target_args` from walker state

```bash
STATE="<path>"
TARGET=$(scripts/walk.sh get --state "$STATE" --key target_args)
```

## GitHub identifiers

- **Issue ref:** `<owner>/<repo>#<n>` — globally unique. Bare `#<n>` only makes sense inside a known repo; in cwd, resolve `<owner>/<repo>` from the git remote (prefers `upstream`, falls back to `origin`).
- **Issue URL:** `https://github.com/<owner>/<repo>/issues/<n>`.

`gh` is authenticated over HTTPS (`gh auth status`); see the `gh` skill. Most reads use `gh issue ...`; the native sub-issue + dependency reads use `gh api`.

## Resolve the feature issue

`$TARGET` is the **feature** issue. Parse it into `<owner>/<repo>` + `<n>`:

```
If $TARGET is a github.com issue URL (contains "/issues/"):
  → parse owner/repo + number from the URL.
Else if it matches /^[^/]+\/[^/#]+#\d+$/ (e.g. coreydaley/enclave#42):
  → owner/repo + number from the input.
Else if it's a bare #<n>:
  → resolve <owner>/<repo> from the cwd git remote (upstream, then origin),
    then number = <n>. Bail if no remote resolves.
Else:
  → bail: "Couldn't parse a feature-issue ref from '<target>'. Expected a
    URL, <owner>/<repo>#N, or #N in the cwd repo."
```

Fetch the feature issue and confirm it exists:

```bash
gh issue view "<n>" --repo "<owner>/<repo>" --json number,title,body,state,labels,url,assignees
```

Capture `FEATURE_REF` = `<owner>/<repo>#<n>` and the feature title.

## Expand the sub-issues (the work list)

The sub-issues are the feature's **native GitHub sub-issues** written by `/feature-plan`. Enumerate them via the native sub-issue API:

```bash
gh api "repos/<owner>/<repo>/issues/<n>/sub_issues" --jq '.[].number'
```

This returns the feature's child sub-issues. For each returned issue, capture `<owner>/<repo>#<m>` (sub-issues are usually in the same repo, but honor whatever repo each child lives in — `gh api` returns each child's `repository_url` when cross-repo).

**If the sub-issue list is empty**, bail: "No sub-issues linked to <FEATURE_REF>. Run /feature-plan first to decompose this feature into linked work items."

### Order the work list

Walk **only the still-open sub-issues** (closed ones already merged — and git-derived resume in `detect-inflight` filters already-shipped ones). Build the dependency graph from each sub-issue's native **blocked-by** dependencies, read via the API:

```bash
gh api "repos/<owner>/<repo>/issues/<m>/dependencies/blocked_by" --jq '.[].number'
```

A sub-issue is buildable once all the sub-issues it's blocked_by are closed/done. Topologically sort (unblocked first, then dependents), and within a tier sort by priority (P0 before P1, read from the issue body). Store each as `<owner>/<repo>#<m>`.

A feature with a single linked sub-issue resolves to a one-element list — `implement` handles it as the single-sub-issue path.

## Derive the feature slug

The `feature/<slug>` branch name (used by `detect-repo` / `verify-worktree`) derives from the feature issue: slugify the feature title and prefix with the feature number for uniqueness, e.g. `feature/42-saved-search-filters`. Persist `feature_slug` and the full `feature_branch` = `feature/<slug>`.

## Persist the resolved target

```bash
scripts/walk.sh set --state "$STATE" --key feature_ref     --value "<owner>/<repo>#<n>"
scripts/walk.sh set --state "$STATE" --key feature_title   --value "<feature title>"
scripts/walk.sh set --state "$STATE" --key feature_slug    --value "<slug>"
scripts/walk.sh set --state "$STATE" --key feature_branch  --value "feature/<slug>"
scripts/walk.sh set --state "$STATE" --key subissue_ids    --value "<JSON list of owner/repo#m, topo-sorted>"
```

## Outputs

- Feature + sub-issue resolution persisted

## Outgoing edges

- → `load-context` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from resolve_target --to load_context
```

## Failure modes

- Feature ref unparseable / issue not found → bail with the ref echoed.
- No linked sub-issues → bail pointing the user at `/feature-plan`.
- `gh` not authenticated → bail with "run `gh auth login` first — see the `gh` skill."
