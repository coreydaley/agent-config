# Node: resolve-target

Apply the detection logic from SKILL.md's Arguments section to determine the path mode and resolve the target. Sets the `path_mode` and target identifiers for downstream nodes.

## Inputs

- `target_args` from walker state

```bash
STATE="<path>"
TARGET=$(scripts/walk.sh get --state "$STATE" --key target_args)
```

## Detection logic

Apply this dispatch (mirrors SKILL.md):

```
If $TARGET is empty:
  branch=$(git branch --show-current)
  if branch matches /[A-Z]+-\d+/i:
    → linear-issue, ID = uppercase match
  else:
    → sprintmd path; resolve via /sprints --current
       (fall through to /sprints --next if no in-progress sprint).

Else if matches /^[A-Z]+-\d+$/i:
  → linear-issue, ID = uppercased input.

Else if starts with "https://linear.app/" and contains "/issue/":
  → linear-issue, ID = parse from URL.

Else if starts with "https://linear.app/" and contains "/project/":
  → list milestones in that project, pick → linear-walk.

Else (sprint reference — timestamp, prefix, or title fragment, OR a
       milestone name):
  → First, try /sprints --path <query>. The CLI auto-detects the
    right root across all four scoping layers (multi-root default).
    If a unique sprint matches:
      If $SESSION_DIR/LINEAR.md exists → linear-walk against the
         milestone recorded there.
      Else → sprintmd path with $SESSION_DIR/SPRINT.md.
    If no sprint matches, fall through to milestone-name search:
      → search active projects in default team for a milestone with
        that name. Unique match → linear-walk. Multiple → ask user.
        Zero → fail loudly with both lookup attempts surfaced
        (sprint-not-found AND milestone-not-found, so the user can
        diagnose).
```

## Steps

1. **Run the dispatch** above to determine `path_mode` ∈ `{sprintmd, linear-issue, linear-walk}`.

2. **Resolve issue list / session dir:**
   - For `sprintmd`: resolve `$SESSION_DIR` and verify `$SESSION_DIR/SPRINT.md` exists. Bail if not.
   - For `linear-issue`: capture the single `ISSUE_ID`.
   - For `linear-walk`: expand the milestone into its issues:
     ```bash
     linear issue query --team <team> --project <project-id> \
       --milestone "<milestone-name>" --sort priority -j
     ```
     Build the dependency graph from each issue's Blocked-by relationships, topologically sort (unblocked first, then dependents), within a tier sort by priority. Walk the resulting list in `implement` / `validate-success` / `open-prs` (each loops internally).

3. **Conflict handling.** If two or more in-progress states are surfaced (in-progress sprint in the ledger AND an explicit different `$ARGUMENTS`), surface the conflict — explicit argument wins, but tell the user what was overridden.

4. **Persist the resolved target:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key path_mode    --value "<sprintmd|linear-issue|linear-walk>"
   scripts/walk.sh set --state "$STATE" --key session_dir  --value "<path or empty>"
   # Persist reports_root once, derived from session_dir (<root>/sprints/<TS>/).
   # Downstream nodes (implement, write-retro, detect-inflight) read this rather
   # than re-deriving via dirname-dirname, which is fragile across path edge cases.
   if [ -n "$SESSION_DIR" ]; then
     scripts/walk.sh set --state "$STATE" --key reports_root --value "$(dirname "$(dirname "$SESSION_DIR")")"
   fi
   # Two distinct query fields with different consumers:
   #
   # sprint_query: user-facing context. May be a Linear ID (PROJ-1234), a
   #   session timestamp/title fragment, or empty. Display only — don't
   #   pass to /sprints --set-fit / --complete unconditionally because
   #   Linear IDs don't resolve in the ledger (which is keyed by session
   #   timestamp + title).
   #
   # ledger_query: the canonical /sprints CLI key. Always set to the
   #   session basename (timestamp) when session_dir is known — that's
   #   what the ledger's session column matches. If session_dir is empty
   #   (some Linear paths before load-context resolves it), persist empty
   #   and let downstream callers fall back.
   scripts/walk.sh set --state "$STATE" --key sprint_query --value "<original target_args>"
   if [ -n "$SESSION_DIR" ]; then
     scripts/walk.sh set --state "$STATE" --key ledger_query --value "$(basename "$SESSION_DIR")"
   else
     scripts/walk.sh set --state "$STATE" --key ledger_query --value ""
   fi
   scripts/walk.sh set --state "$STATE" --key issue_ids    --value "<JSON list>"
   scripts/walk.sh set --state "$STATE" --key milestone_id --value "<id or empty>"
   ```

## Outputs

- All target-resolution state persisted

## Outgoing edges

- → `load-context` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from resolve_target --to load_context
```

## Failure modes

- `sprintmd` path with no SPRINT.md → bail with "no SPRINT.md at `<path>` — re-run /sprint-plan."
- Milestone-name search returns zero → bail with the search query echoed.
- Milestone-name search returns multiple → AskUserQuestion to disambiguate.
- `linear` CLI not authenticated → bail with "run `linear auth` first."
