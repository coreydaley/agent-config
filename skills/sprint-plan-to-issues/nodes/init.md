# Node: init

Resolve the **sprint milestone** to decompose, initialize walker state.

The plan already lives in a Forgejo milestone (its description is the SPRINT document, created by `/sprint-plan`). This skill reads the plan out of that milestone and adds issues to it — it does **not** create the milestone.

## Inputs

- The user's arguments: `[<milestone-url> | <query>]`

Argument shape:

- **Milestone URL** — `https://mac-mini.example:3000/<owner>/<repo>/milestone/<id>` (or `…/milestones/<id>`). The most direct input.
- **Sprint query** — a session timestamp / title fragment, resolved to the milestone via `python3 ~/.claude/lib/forgejo_sprints.py --path <query>` + the sprint's repo. If omitted, use the in-progress sprint (`… --current`).

## Steps

1. **Verify `tea` is available:**
   ```bash
   command -v tea >/dev/null || { echo "install tea first (see forgejo skill)"; exit 1; }
   tea login default >/dev/null 2>&1 || { echo "no default tea login — see forgejo skill setup"; exit 1; }
   ```

2. **Resolve the milestone → `REPO`, `MILESTONE_ID`, `SESSION_TS`:**
   - **Milestone URL:** parse `<owner>/<repo>` and `<id>` from the path. Fetch the milestone (`curl … /repos/<owner>/<repo>/milestones/<id>`) and read its `## Sprint metadata` block for `Session` (the sprint timestamp).
   - **Sprint query / current:** resolve the sprint via the tracker (`python3 ~/.claude/lib/forgejo_sprints.py --path <query>` / `--current`) and get its repo + session. The milestone is the one in `<repo>` whose meta `Session` matches — find it via the Forgejo API (`/repos/<repo>/milestones?state=all`, match the meta block), or note that `… --get-doc <query>` already proves a milestone exists.

   Bail if no milestone is found: "No sprint milestone for `<arg>`. Run `/sprint-plan` first — it creates the milestone whose description is the plan."

2a. **Guard: refuse a closed milestone.** A closed milestone is a
   finished sprint — decomposing it into fresh issues is almost always a
   mistake. The milestone JSON from step 2 has a `state` field:

   ```bash
   STATE_FIELD=$(echo "$MILESTONE_JSON" | jq -r '.state')   # "open" | "closed"
   ```

   If `closed`, **bail**: "Milestone `<title>` is closed (a completed
   sprint). Re-open it in Forgejo if you really mean to add issues, or run
   `/sprint-plan` to start a new sprint." Do not proceed.

2b. **Guard: warn if the milestone already has issues.** This skill does
   **not** dedupe — running it twice creates a duplicate issue set. Count
   the milestone's attached issues:

   ```bash
   EXISTING=$(tea issues list --repo "$REPO" --milestones "$MILESTONE_TITLE" \
     --state all --output json | jq 'length')
   ```

   If `EXISTING` > 0, this milestone was very likely already decomposed.
   **Surface a loud warning and ask the user to confirm** before
   continuing (this is the one genuine gate — re-running here is
   destructive-by-duplication, not autonomous-safe):

   ```
   ⚠ Milestone "<title>" already has <EXISTING> issue(s). This skill does
     NOT dedupe — continuing creates a DUPLICATE set. Decompose anyway?
     (Usually you want: no — delete the old issues first, or you're done.)
   ```

   This is **not** a dedupe attempt — issue titles/numbers aren't
   deterministic, so there's nothing reliable to match on. It's an honest
   "you've probably already run this" tripwire. Abort to terminal unless
   the user explicitly confirms.

3. **Set `$SESSION_DIR`** to the sprint's local working folder (`~/Reports/<owner>/<repo>/sprints/<SESSION_TS>/`) — where `FORGEJO.md` will be written. Create it if missing.

4. **Initialize the walker state file:**
   ```bash
   STATE="$SESSION_DIR/.walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

5. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key primary_repo   --value "<owner>/<repo>"
   scripts/walk.sh set --state "$STATE" --key milestone_id   --value "<id>"
   scripts/walk.sh set --state "$STATE" --key milestone_title --value "<milestone title>"
   scripts/walk.sh set --state "$STATE" --key session_ts     --value "<SESSION_TS>"
   scripts/walk.sh set --state "$STATE" --key session_dir    --value "$SESSION_DIR"
   scripts/walk.sh set --state "$STATE" --key query          --value "<the resolving query / URL>"
   ```

6. **Print a brief opening message** — repo, milestone title + URL, session.

## Outputs

- `$SESSION_DIR/.walk-state.json` with the resolved milestone

## Outgoing edges

- → `parse-sprint` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from init --to parse_sprint
```

## Failure modes

- No milestone resolves → bail directing the user to run `/sprint-plan` first.
- Milestone is **closed** (guard 2a) → bail; it's a finished sprint.
- Milestone **already has issues** (guard 2b) and the user doesn't confirm
  → abort; re-running duplicates the issue set (no dedupe).
- `tea` not installed / no default login → bail pointing at the `forgejo` skill setup.

These are hard exits (like the existing no-milestone bail), not graph
transitions — init's only edge is to `parse-sprint`.
