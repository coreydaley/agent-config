# Node: address

Work through findings per the chosen strategy. Apply fixes, run targeted tests, route deferrals, record outcomes. This node holds the per-finding loop internally — the graph captures macro flow, not per-finding actions.

## Inputs

- `strategy`, `plan_path`, `findings_count`, `pr_number`, `pr_head`, `session_dir`, `mode` from walker state
- Findings from `$SESSION_DIR/findings.json` (or in-memory)

```bash
STATE="$SESSION_DIR/.walk-state.json"
STRATEGY=$(scripts/walk.sh get --state "$STATE" --key strategy)
PLAN_PATH=$(scripts/walk.sh get --state "$STATE" --key plan_path)
```

## Per-finding contract

For each finding (or finding-group, depending on strategy), do:

1. **Show context.** Print the issue (and suggestion in Mode B), then `Read` the file at the cited line range from the *current* checkout — show live code, not the stale review snippet. Code may have moved; if line numbers don't match anymore, find the closest equivalent and flag the drift to the user.

2. **Decide the action.**
   - In `walk` strategy → ask explicitly via `AskUserQuestion`: fix / skip / won't-fix / defer / discuss.
   - In `fix_all` → action is `fix` for everything.
   - In `group` / `severity` / `pick` → action comes from `plan.json`.
   - In *any* strategy, the user can interject and override mid-stream. If they say "actually skip that," honor it.

3. **Apply the fix** with `Edit` (or `Write` only when creating a new file). Keep changes minimal — address only what the finding describes. **No internal finding IDs in code, comments, or commit messages.** Apply the Comment Hygiene Rule when adding/changing comments: only when the *why* is non-obvious, one line by default, no AI-flavored preambles.

4. **Run targeted tests.** Detect project type and run the narrowest scope that covers the change:
   - Go: `go test ./<package-dir>/...`
   - Python: `pytest <test-dir-or-file>`
   - Node: `npm test -- <pattern>` or framework equivalent
   - Other: ask the user for the right command, or skip with a recorded note.

   Surface failures immediately. If the fix broke a test, work with the user before continuing — don't silently move on.

5. **Defer routing** (when action is `defer`):
   - **Linear issue** — use the `linear` skill. Title and description describe the problem in its own terms (no internal review IDs). Capture the resulting issue ID (e.g. `CON-1234`).

     After the issue is created, ask whether to leave a code marker:
     ```
     // TODO(CON-1234): <one-line reason — what's missing and why deferred>
     ```

     Match the comment style to the language (`//` for Go/JS, `#` for Python/Bash, etc.). Linear issue IDs are public team identifiers and are **explicitly allowed in code** — the ID Suppression Rule applies only to internal review artifacts (`R001`, `SR042`, `CR007`, etc.).

   - **Obsidian task** — use the `vault` skill to create a task note in `Tasks/`.

   - **Just record** — note in the addressed list, no external system.

6. **Record the outcome** in the in-memory addressed list. Schema per row:
   ```json
   {
     "id": "<internal id from finding>",
     "severity": "...",
     "file_line": "path/to/file.go:42",
     "action": "fixed|won't-fix|deferred|skipped",
     "note": "<one short line>",
     "defer_target": "linear:CON-1234 | vault:Tasks/foo.md | record-only",
     "linear_id": "CON-1234"
   }
   ```

   The list is held in memory and written to `ADDRESSED.md` by the `persist` node. Don't write it here — `persist` is the single writer.

## Loop control

The loop terminates when every finding (or every plan entry) has an action recorded. There's no sub-graph for the per-finding loop — it's an internal `for` loop in this node's prose.

In `walk` strategy, the user can say "stop" mid-loop. Treat that as: mark the rest as `skipped`, exit the loop, transition.

## ID Suppression Rule (load-bearing here)

Internal IDs (`R001`, `SR042`, `CR007`, `CX012`, GitHub comment IDs) **never appear in**:

- code or code comments
- commit messages
- PR replies or top-level PR comments
- any user-facing summary

The IDs exist only in `ADDRESSED.md` for traceability. Describe each fix in its own terms.

Linear IDs (`CON-1234`) are an exception — they're public team identifiers and are explicitly allowed in code.

## Outputs

- Code edits applied via `Edit` / `Write`
- An in-memory addressed list (consumed by `persist`)
- Targeted-test results surfaced to the user

Persist the addressed list as JSON for resume safety:
```bash
scripts/walk.sh set --state "$STATE" --key addressed_path --value "$SESSION_DIR/addressed.json"
# Write the JSON file directly (not via walker — it's not walker state, it's a finding-set artifact).
```

## Outgoing edges

- → `ask-replies` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from address --to ask_replies
```

## Failure modes

- A test fails after a fix → stop the loop, surface the failure, work with the user. Don't blindly continue and don't commit anything (the skill never commits).
- `Edit` can't find the cited line (file shifted) → flag the drift, find the closest equivalent, confirm with the user before editing.
- `linear` or `vault` skill fails → fall back to `record-only` for that finding and continue.
- User aborts mid-loop → mark unprocessed findings as `skipped` and route to `ask-replies` so they can still post replies for what got done.
