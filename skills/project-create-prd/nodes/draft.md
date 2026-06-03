# Node: draft

Assemble the discussion into a structured PRD, write it to the local working
copy, and render it inline for review. Does **not** touch the wiki — that's
`publish`, after the user approves.

## Inputs

- The refined material from `discuss`; `prd_mode`, `org_repo`, `session_dir`,
  `prd_outline`, and (revise mode) the existing `$SESSION_DIR/PRD.md`

```bash
STATE="$SESSION_DIR/.walk-state.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
ORG_REPO=$(scripts/walk.sh get --state "$STATE" --key org_repo)
PRD_MODE=$(scripts/walk.sh get --state "$STATE" --key prd_mode)
```

## Steps

### 1. Assemble the PRD

Write `$SESSION_DIR/PRD.md` from this structure. Omit a section only if it
genuinely has no content (and the user agreed it's N/A); prefer a one-line
"TBD — see Open Questions" over silently dropping a section.

```markdown
# PRD: <Project Name>

> <one-sentence elevator description of what this is>

## Problem & Goal
<the pain, who feels it, and what "solved" looks like>

## Target Users
<primary users; secondary if relevant>

## Goals
- <observable outcome the project is trying to achieve>

## Non-Goals
- <explicitly out of scope — the anti-drift fence>

## Requirements / Core Features
- <capability the product must provide>

## Success Metrics
<how you'll know it's working — quantitative if available, else an honest
qualitative completion signal. Don't fabricate numbers.>

## Phases / Roadmap
1. **<Phase 1 / MVP>** — <what ships, why first>
2. **<Phase 2>** — <…>
3. **<Phase 3>** — <…>

## Constraints & Risks
- <technical / organizational / deadline / dependency>

## Open Questions
- <genuinely undecided items>

---
*Authored via `/project-create-prd` on <YYYY-MM-DD>. Lives on the
`<org>/<repo>` Forgejo wiki (page `PRD`).*
```

- **Revise mode:** start from the existing `PRD.md` and apply the changes
  discussed; preserve sections the user didn't touch. Don't rewrite the whole
  doc unless asked.
- **Phases must be concrete and ordered** — `/sprint-seed` reads them to propose
  next sprints.
- **No invented content.** Undecided → Open Questions.

### 2. Render it inline

Print the full assembled PRD to the user in the conversation (not just the
path) so they can read and react to it before anything is published.

## Outputs

- `$SESSION_DIR/PRD.md` (the working draft)
- Inline render of the PRD

```bash
scripts/walk.sh set --state "$STATE" --key prd_md_path --value "$SESSION_DIR/PRD.md"
```

## Outgoing edges

- → `ask-publish` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from draft --to ask_publish
```

## Notes

- **Render the full Markdown inline.** The user is about to decide whether to
  publish; they need to see exactly what goes to the wiki.
- **A PRD is the what & why, never the how.** If you're listing tasks, files, or
  acceptance criteria, you've drifted into `/sprint-plan`'s territory — pull back.
