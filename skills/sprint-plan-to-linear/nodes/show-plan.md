# Node: show-plan

Render the proposed plan inline so the user can read everything in one place before approval.

## Inputs

- `plan_path`, `match_count`, `proposed_issue_count`, `milestone_name`, `project_url`, `rerun_mode`, `matching_milestone_name` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
PLAN_PATH=$(scripts/walk.sh get --state "$STATE" --key plan_path)
MATCH_COUNT=$(scripts/walk.sh get --state "$STATE" --key match_count)
```

## Steps

Render inline, in this order:

### 1. Project context

```
Project: <name> — <project URL>
Milestones: <existing count> existing
Issues: <existing count> existing
```

So the user can sanity-check the target project.

### 2. Milestone name

```
Milestone:
  Name:    <milestone_name>
  Rename:  <bare title> → <milestone_name>     (skip if no rename applied)
  Mode:    <create / create_only_new / update / start_fresh>   (skip if not a re-run)
```

### 3. Milestone description

Render the **full markdown** of the proposed description inline so the user can read it in the conversation, not just see a path. Include all sections (outcome, acceptance criteria, open questions, considerations, footer).

### 4. Issue list

Render as a table:

```
| # | Title | Priority | Files | Blocked by |
|---|-------|----------|-------|------------|
| 1 | ...   | High     | a.go  | -          |
| 2 | ...   | Normal   | b.go  | 1          |
```

### 5. Existing-issue match summary

If `match_count > 0`, render the matches:

```
Matches found:
  proposed "Add full tag support for python"
    ↔ existing CON-1148 "Add full tag support for python" (sim 0.92)
  proposed "Wire up cache warmer"
    ↔ existing CON-1162 "Cache warmer scaffolding" (sim 0.61)
```

Per-match decisions happen in `ask-per-match-decisions`, not here.

### 6. Existing-milestone similarity

If `decide-rerun` flagged a similar existing milestone (and the user didn't pick "start_fresh" yet), surface it here:

```
Note: a milestone "<matching name>" already exists in this project
      with high similarity to the chosen "<milestone_name>".
      You picked "<rerun_mode>" — that means: <one-line consequence>
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

- **Render the description inline as markdown** (not just a path). The user is going to be asked to approve in the next node; they need the full content in this conversation.
- **Don't ask anything yet.** The user-input gate is `ask-approval`.
- **Don't show post-creation coaching feedback.** Any automated quality feedback from Linear arrives async after creation; orient the user to the plan, not to coaching.
