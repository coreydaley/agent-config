# Node: draft

Assemble the issue body from the discussion into `ISSUE.md` and render it inline for
review. Local only — nothing is filed here.

## Inputs

- `issue_type`, `issue_title`, `issue_outline`, `session_dir` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
ISSUE_TYPE=$(scripts/walk.sh get --state "$STATE" --key issue_type)
TITLE=$(scripts/walk.sh get --state "$STATE" --key issue_title)
```

## Steps

### 1. Assemble the body

Compose `ISSUE.md` using the section headings that match the type's template from
`gather` (Markdown `##` headings). Examples:

- **bug** → `## Summary` · `## Steps to reproduce` · `## Expected` · `## Actual` ·
  `## Environment` · `## Frequency` · `## Evidence` (omit empty sections).
- **enhancement** → `## Problem` · `## Proposed change` · `## Acceptance criteria` ·
  `## Out of scope`.
- (and so on per type — keep only the sections that carry content.)

Keep it tight and skimmable. Don't invent content the user didn't give; an omitted
section is better than a padded one.

```bash
cat > "$SESSION_DIR/ISSUE.md" <<'BODY'
<the assembled markdown body>
BODY
```

### 2. Render it inline

Show the user the **title** and the full body so they can eyeball it before any
priority decision or filing. Note that priority comes next (it isn't in the body —
it's a label).

## Outputs

- `$SESSION_DIR/ISSUE.md` (the body)
- `issue_title` confirmed in state

## Outgoing edges

- → `decide-priority` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from draft --to decide_priority
```

## Notes

- **Body only — no priority, no labels here.** Priority is a label set after this,
  via `decide-priority`.
- **Faithful assembly.** The body is the user's report, structured; don't add
  scope or claims they didn't make.
