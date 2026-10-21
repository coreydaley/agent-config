# Node: display

Show the drafted PR and the state of the branch, then ask in plain text whether to open it. One final message, no tool call after it. The transition to `ask-open` is recorded at the start of the next turn.

## Inputs

- `plan_dir`, `worktree`, `base_ref`, `tests_passed`, `sweep_findings`, `pr_number`, `pr_url` from walker state
- `$PLAN_DIR/pr-body.md`

## Steps

1. **Branch summary**, a few lines:
   ```
   Branch: fix/gh-123-retry-budget (5 commits ahead of upstream/main)
     a1b2c3d fix(client): stop retrying on 4xx responses
     ...
   Tests: PASS (go test ./..., 212 tests)   Sweep: 2 comments tightened, 1 negative case added
   ```
   Existing PR: add its URL and "this will push N new commits to it and replace the body."

2. **The PR, inline.** Title as a heading, then the body as markdown, rendered exactly as it will be posted.

3. **Path line:**
   ```
   📄 ~/Reports/<org>/<repo>/prs/<key>/pr-body.md
   ```

4. **Close with the question**, plain text:

   > Next: **open** as a draft PR (pushes the branch to origin), **edit** the title or body, or **stop** and leave the commits local?

   Existing PR: "**push** the new commits and update the body" replaces "open."

5. **End the turn.** Nothing after the question. No `AskUserQuestion`, no transition.

## Outputs

- The PR draft and branch state are in the conversation

## Outgoing edges

- → `ask-open` (always, single outgoing edge, recorded next turn)

```bash
scripts/walk.sh transition --state "$STATE" --from display --to ask_open
```

## Notes

- **The body is what gets approved.** Render it as it will post. Don't summarize it.
- **Say what "open" does.** It pushes. The user should know a network write is about to happen before saying yes.
