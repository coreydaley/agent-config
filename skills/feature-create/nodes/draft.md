# Node: draft

Assemble the discussion into the **issue body** (the spec), tiered by size, write
it to the local working copy, and render it inline for review. Does **not** file
the issue — that's `create-issue`, after the readiness check and the user's
approval.

## Inputs

- The refined material from `discuss`; `feature_size`, `org_repo`, `session_dir`,
  `feature_outline`

```bash
STATE="$SESSION_DIR/.walk-state.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
FEATURE_SIZE=$(scripts/walk.sh get --state "$STATE" --key feature_size)
```

## Steps

### 1. Derive the issue title

Imperative, completion-framed (*"Add saved-search filters to the inbox"*) — what
the feature delivers. Don't prefix with "Feature:". Keep it tight.

### 2. Assemble the body (tiered)

Write `$SESSION_DIR/FEATURE.md` (the issue body). This is the **spec** — the
what and why, not the how. Forgejo issue bodies render Markdown and auto-link
`#<n>`.

**Small feature** — intent + acceptance criteria only:

```markdown
[One paragraph: what this feature is and why it's worth building.]

## Acceptance Criteria
- [ ] [Concrete, verifiable — "done when …"]
- [ ] [Tests exist for the new behavior]
```

**Large feature / epic** — the engineering surface (omit a section only if it
genuinely doesn't apply, and say so inline):

```markdown
[Short paragraph: what this feature is and why it's worth building.]

## Requirements
- **<capability>** — <what it must do>
  - [ ] <acceptance criterion>

## Edge Cases & Error States
- <input/timing/permission failure → expected behavior>

## Constraints
- <technical limits>
- **Security & Privacy:** <authz, PII, secrets, blast radius — call out
  proactively even if not raised>

## Dependencies & Assumptions
- <what it leans on / what's taken on faith>

## Feasibility
- <is the approach sound for the scope; known hard parts>

## Scope & Non-Goals
- <smallest thing that delivers the value; what's tempting but out of scope>

## Open Questions
- [ ] <genuinely undecided>
```

- **No invented content.** Unknown → Open Questions.
- **A feature issue is the *what*, not the *how* or the *plan*.** No task
  breakdown, no DoD enumeration — that's `/feature-plan`, which writes the task
  breakdown as linked sub-issues. If you're listing implementation steps, pull
  back.

### 3. Confirm priority (optional)

Ask once whether the feature warrants a priority label, default none:

> "Priority on this — P0 (critical), P1 (important), or leave unlabelled?"

```bash
scripts/walk.sh set --state "$STATE" --key priority    --value "<p0|p1|empty>"
scripts/walk.sh set --state "$STATE" --key issue_title --value "<the imperative title>"
```

### 4. Render it inline

Print the title + the full assembled body to the user (not just the path) so they
can read and react before anything is filed.

## Outputs

- `$SESSION_DIR/FEATURE.md` (the issue-body working draft)
- `issue_title`, `priority` in walker state; inline render

## Outgoing edges

- → `readiness-check` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from draft --to readiness_check
```

## Notes

- **Render the full body inline.** The user is about to decide whether to file
  it; show exactly what becomes the issue.
- **Match the tier.** A small feature gets the two-section body, full stop.
