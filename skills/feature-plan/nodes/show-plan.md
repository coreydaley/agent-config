# Node: show-plan

Render the proposed sub-issue breakdown inline so the user can read
everything in one place before the single approval gate.

## Inputs

- `tasks_plan_path`, `proposed_issue_count`, `feature_title`,
  `feature_number`, `feature_url`, `owner_repo`, `missing_labels`,
  `uncovered_tasks`, `orphan_issues`, `plan_md_path` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
PLAN_PATH=$(scripts/walk.sh get --state "$STATE" --key tasks_plan_path)
```

## Steps

Render inline, in this order:

### 1. Feature context

```
Feature:      <owner_repo>#<feature_number> — <feature title>
              <feature_url>
Repo:         <owner_repo>
Linkage:      native sub-issues (feature↔task hierarchy + progress bar)
Ordering:     native blocked-by dependencies (task-to-task)
```

### 2. Linkage model

State plainly how the sub-issues attach to the feature:

```
Each sub-issue will be self-assigned to coreydaley and attached as a NATIVE
sub-issue of feature #<feature_number> (GitHub renders the child list +
progress bar on the parent). Task-to-task ordering is wired as native
blocked-by dependencies between the sub-issues. No milestone is created; no
manual checklist is written into the feature body. A single comment will be
posted on the feature: "Planned: N sub-issues created (tracked as native
sub-issues)."
```

### 3. Plan summary

Optionally surface a short summary of `PLAN.md` (Overview + Approach) for
context — the verbose plan lives at `$PLAN_MD_PATH` (ephemeral). The
sub-issue table below is what actually gets created.

### 4. Sub-issue list

One row per task (one sub-issue per task). Columns carry the relationships:

```
| # | Title | Priority | Labels        | Files | Depends on | Related |
|---|-------|----------|---------------|-------|------------|---------|
| 1 | ...   | P0       | priority/p0   | a.go  | -          | -       |
| 2 | ...   | P1       | priority/p1   | b.go  | 1          | 3       |
| 3 | ...   | P1       | priority/p1   | c.go  | -          | 2       |
```

`Depends on` is a hard blocker (wired as a native blocked-by dependency);
`Related` is a soft `#N` cross-reference (a `## Related` body line). Both
reference the proposed `#` column (resolved to real issue numbers after
creation).

### 5. Coverage check

Surface the bijection result from `build-tasks`. If everything maps cleanly:

```
Coverage: all <N> P0/P1 tasks mapped to sub-issues; <D> deferred (not created).
```

If `uncovered_tasks` is non-empty, this is a **decomposition error** —
surface it loudly so the user can `discuss` before any issue is created:

```
⚠ These plan tasks did NOT map to any sub-issue (they would be silently lost):
    - <task text>
  Choose "discuss" to fix the decomposition before creating issues.
```

Likewise flag any `orphan_issues` (sub-issues with no source task).

### 6. Missing-label note

`missing_labels` holds **domain / kind** labels desired but not yet in the
repo (priority labels are guaranteed by `create-issues`). If non-empty,
surface once — `create-issues` will create each missing one with a default
colour (never recolouring an existing label):

```
ℹ These labels will be created (they don't exist yet in <owner_repo>):
    <label>, <label>
```

## Outputs

- The full breakdown rendered inline. No file or state changes.

## Outgoing edges

- → `ask-approval` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from show_plan --to ask_approval
```

## Notes

- **Render the sub-issue table inline.** The user is about to approve
  creating these; they need to see them in this conversation.
- **Don't ask anything yet.** The user-input gate is `ask-approval`.
