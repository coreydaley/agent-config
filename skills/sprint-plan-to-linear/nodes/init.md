# Node: init

Parse arguments, resolve the Linear project ID and the sprint reference, set up `$SESSION_DIR`, initialize walker state.

## Inputs

- The user's arguments to the skill: `<project-url> [<query> | path/to/SPRINT.md]`

Argument shape:

- **Project URL** — required. Linear project URL. Extract the slug (last path segment); use it as `project_id`.
- **Sprint reference** — optional. Either a session timestamp / title query (resolved via `/sprints --path <query>`) or a direct path to a `SPRINT.md`. If omitted, use the in-progress sprint via `/sprints --current`.

## Steps

1. **Parse `$ARGUMENTS`.** Bail if the project URL is missing.

2. **Resolve the Linear project ID:**
   - URL form: `https://linear.app/<workspace>/project/<slug>`
   - Project slug = last path segment, used as `project_id` for `linear project view` and `linear milestone create --project <id>`.

3. **Resolve the sprint reference to a `SPRINT.md` path:**
   - If a path is given, verify it exists and ends in `.md`.
   - If a query is given, run `/sprints --path <query>` (or call the helper directly) to resolve to the matching session's SPRINT.md.
   - If empty, use `/sprints --current`.

4. **Set `$SESSION_DIR`** to the parent of the resolved SPRINT.md path. This is where `LINEAR.md` will be written.

5. **Initialize the walker state file:**
   ```bash
   STATE="$SESSION_DIR/.walk-state.json"
   scripts/walk.sh init --state "$STATE"
   ```

6. **Persist run-scoped state:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key project_url    --value "<URL>"
   scripts/walk.sh set --state "$STATE" --key project_id     --value "<slug>"
   scripts/walk.sh set --state "$STATE" --key sprint_path    --value "<path to SPRINT.md>"
   scripts/walk.sh set --state "$STATE" --key session_dir    --value "$SESSION_DIR"
   ```

7. **Print a brief opening message** — project URL, sprint path, session dir.

## Outputs

- `$SESSION_DIR/.walk-state.json` exists with run-scoped fields

## Outgoing edges

- → `parse-sprint` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from init --to parse_sprint
```

## Failure modes

- Missing project URL → bail with usage hint.
- Sprint path doesn't exist / can't be resolved → bail with the resolution error.
- `linear` CLI not available → bail with "install linear CLI first."
