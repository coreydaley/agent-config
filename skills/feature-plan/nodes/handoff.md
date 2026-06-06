# Node: handoff

Print what landed — the created sub-issues and their links — and the **next
step** `/feature-work`, but don't execute it. The user drives what happens
next.

## Inputs

- `owner_repo`, `feature_number`, `feature_title`, `feature_url`,
  `issue_results`, `feature_links_set`, `deps_enabled`, `session_dir` from
  walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
OWNER_REPO=$(scripts/walk.sh get --state "$STATE" --key owner_repo)
FEATURE_URL=$(scripts/walk.sh get --state "$STATE" --key feature_url)
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
```

## Steps

### On success (sub-issues were created)

```
Feature planned: <owner_repo>#<feature_number> — <feature title>
                 <feature_url>

Sub-issues created (one per task, self-assigned to coreydaley):
  - #7:  <title>  [priority/p0]
  - #8:  <title>  [priority/p1, blocked by #7, related #9]
  ...

Linkage:    feature #<feature_number> is "blocked by" each sub-issue
            (native dependencies)   — or, if deps couldn't be enabled —
            ordering recorded in issue bodies only; enable the repo's
            Dependencies feature and re-link to get the native feature links
Comment:    posted on the feature — "Planned: N sub-issues created"
Working doc: $SESSION_DIR/PLAN.md   (ephemeral — the sub-issues are the plan)

Next (your call — nothing runs automatically):
  /feature-work <feature_url>   →  build the linked sub-issues, then finish
```

The feature's task breakdown is now tracked sub-issues. `/feature-work`
reads the feature, walks its dependency-linked sub-issues, and builds them.

### On partial / failed creation

If `tea issues create` failed partway, be honest about what exists:

```
⚠ Creation stopped partway (see the error above).
Created so far:  <list of #N from issue_results>
Not created:     <the remaining tasks>
Working doc:     $SESSION_DIR/PLAN.md
Because this skill is one-shot and the feature now has partial sub-issues,
do NOT simply re-run /feature-plan (it will STOP on the idempotency guard).
Finish the remaining tasks by hand with `tea issues create`, or delete the
partial sub-issues and re-plan.
```

That's it — no closing summary, no "let me know if you have questions."

## Outputs

- Inline printed output. No file changes, **nothing executed**.

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from handoff --to terminal
```

## Notes

- **Print the chain, don't run it.** This skill stops at the created
  sub-issues; the user invokes `/feature-work` when ready.
- **Be honest about failure.** If creation was partial, say exactly what
  exists — never imply a full set when some tasks didn't file.
- **Don't duplicate downstream work.** No implementation here — that's
  `/feature-work`, surfaced as the next step only.
