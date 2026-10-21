# Node: finalize

Set the plan's status, pin the base, append the Log line, print the next step. Stop.

## Inputs

- `plan_dir`, `repo_root`, `default_branch`, `approval_choice`, `no_build_reason`, `branch_state` from walker state
- `$PLAN_DIR/PLAN.md`

```bash
STATE="$PLAN_DIR/.walk-state.plan.json"
PLAN_DIR=$(scripts/walk.sh get --state "$STATE" --key plan_dir)
REPO_ROOT=$(scripts/walk.sh get --state "$STATE" --key repo_root)
DEFAULT=$(scripts/walk.sh get --state "$STATE" --key default_branch)
CHOICE=$(scripts/walk.sh get --state "$STATE" --key approval_choice)
```

## Steps

### approve

1. **Pin the base.** Fetch so the SHA is current, then record it:
   ```bash
   REMOTE=$(git -C "$REPO_ROOT" remote | grep -qx upstream && echo upstream || echo origin)
   git -C "$REPO_ROOT" fetch "$REMOTE" "$DEFAULT" --quiet
   BASE_SHA=$(git -C "$REPO_ROOT" rev-parse --short "$REMOTE/$DEFAULT")
   ```
   Header table: `Base | <default_branch> @ <BASE_SHA>`. pr-build branches from here (or verifies an existing branch is rebased near it).

2. **Status → `approved`.** Header table only.

3. **Log:** append `<date> approved`.

4. **Print:**
   ```
   Plan approved: ~/Reports/<org>/<repo>/prs/<key>/PLAN.md
   Next: /pr-build (on an Opus session; switch in the model picker first if this one isn't)
   ```
   If `branch_state=proposed`, add: "pr-build will create `<branch>` from `<default>` @ `<sha>`." If a design-review ceremony was approved anyway, add: "Approved at design-review ceremony without a design review. That's recorded in Log."

### no_build

1. **Status → `no-build`.**

2. **Log:** append `<date> no-build: <no_build_reason>`.

3. **Print:**
   ```
   Recorded no-build: <reason>
   Plan kept at ~/Reports/<org>/<repo>/prs/<key>/PLAN.md
   ```
   If the reason was "routed to design review," add: "Next: run /review-design on this PLAN.md, or on a fuller written design. Re-run /pr-plan afterward and it will revise this plan."

## Outputs

- PLAN.md header and Log updated
- Nothing else. No branch, no worktree, no GitHub write.

## Outgoing edges

- → `terminal` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to terminal
```

## Failure modes

- Fetch fails (offline) → pin `Base` as `<default_branch> @ unknown (offline)` and say so. pr-build re-resolves.
- PLAN.md missing or unparseable at this point → something upstream went wrong. Stop and surface rather than writing a header onto a broken file.

## Notes

- **No "shall I start building?"** The next step is printed. The user invokes `/pr-build` when they want it.
- **Open questions can survive approval.** If the user approved with questions still listed, leave them. pr-build treats them as things to resolve before touching the affected files.
