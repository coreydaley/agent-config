# Node: show-plan

Render the proposed plan inline so the user can read everything in one
place before approval.

## Inputs

- `plan_path`, `proposed_issue_count`, `sprint_title`, `primary_repo`,
  `repo_count`, `missing_labels`, `deps_enabled`, `uncovered_tasks`,
  `orphan_issues` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
PLAN_PATH=$(scripts/walk.sh get --state "$STATE" --key plan_path)
```

## Steps

Render inline, in this order:

### 1. Repo context

```
Repo:       <primary_repo>   (https://mac-mini.example:3000/<primary_repo>)
Milestones: <existing count> existing
```

If `repo_count > 1`, add:

```
Note: this sprint's manifest lists <repo_count> repos. All issues are
      being created in <primary_repo> (cross-repo work noted in bodies).
      Re-run with --repo <owner>/<repo> to target a different one.
```

### 2. Milestone (existing — not created here)

```
Milestone:    <sprint_title>   (existing — this skill only adds issues)
Dependencies: on   (native blocker links will be wired)
              — or, if enabling failed —
              off  (couldn't enable the feature; blockers recorded in
                    issue bodies only — enable manually via
                    Settings → Repository → Issues → "Enable Dependencies")
```

The `Dependencies` line reflects `deps_enabled` from `fetch-repo`, which
**enables the feature when it's off** — so this is normally `on`.

### 3. Sprint plan (milestone description)

Render the **full Markdown** of the milestone's description (the SPRINT
doc) inline so the user can read the plan in the conversation, not just a
path. This skill does **not** modify it — it's shown for context.

### 4. Issue list

One row per task (this skill creates **one issue per task**). Columns
carry the relationships:

```
| # | Title | Priority | Labels        | Files | Depends on | Related |
|---|-------|----------|---------------|-------|------------|---------|
| 1 | ...   | P0       | priority/p0   | a.go  | -          | -       |
| 2 | ...   | P1       | priority/p1   | b.go  | 1          | 3       |
| 3 | ...   | P1       | priority/p1   | c.go  | -          | 2       |
```

`Depends on` is a hard blocker (native dependency when `deps_enabled`,
else body ref); `Related` is a soft `#N` cross-reference. Both reference
the proposed `#` column (resolved to real issue numbers after creation).

### 5. Coverage check

Surface the bijection result from `build-plan`. If everything maps
cleanly, one line:

```
Coverage: all <N> P0/P1 tasks mapped to issues; <D> deferred (not created).
```

If `uncovered_tasks` is non-empty, this is a **decomposition error** —
surface it loudly so the user can `discuss` before any issue is created:

```
⚠ These plan tasks did NOT map to any issue (they would be silently lost):
    - <task text>
  Choose "discuss" to fix the decomposition before creating issues.
```

Likewise flag any `orphan_issues` (issues with no source task — invented
work that shouldn't exist).

### 6. Missing-label warning

`missing_labels` holds **kind** labels (`bug`, `enhancement`, …) that
were desired but don't exist — priority labels are not here, since
`fetch-repo` guarantees `priority/p*`. If non-empty, surface once:

```
⚠ These kind labels were desired but don't exist in <primary_repo>:
    <label>, <label>
  They won't be applied (priority/p* labels are applied normally).
  Create them first if you want them on these issues:
    tea labels create --repo <primary_repo> --name "<label>" --color "#rrggbb"
```

## Outputs

- The full plan rendered inline. No file or state changes.

## Outgoing edges

- → `ask-approval` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from show_plan --to ask_approval
```

## Notes

- **Render the description inline as Markdown** (not just a path). The
  user is about to be asked to approve; they need the full content in
  this conversation.
- **Don't ask anything yet.** The user-input gate is `ask-approval`.
