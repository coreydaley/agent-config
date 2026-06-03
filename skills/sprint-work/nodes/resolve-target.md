# Node: resolve-target

Apply the detection logic from SKILL.md's Arguments section to determine the path mode and resolve the target. Sets the `path_mode` and target identifiers for downstream nodes.

## Inputs

- `target_args` from walker state

```bash
STATE="<path>"
TARGET=$(scripts/walk.sh get --state "$STATE" --key target_args)
```

## Forgejo identifiers

- **Instance:** `https://mac-mini.example:3000` (see the `forgejo` skill).
- **Issue ref:** `<owner>/<repo>#<n>` — globally unique. Bare `#<n>` only makes sense inside a known repo; require the `<owner>/<repo>` prefix on the command line.
- **Issue URL:** `https://mac-mini.example:3000/<owner>/<repo>/issues/<n>`.
- **Branch convention** (from `/sprint-plan-to-issues`): `coreydaley/<repo>-<n>-<slug>`.

Read the token once for raw-API calls (the `forgejo` skill documents this; `tea` covers most needs):

```bash
TOKEN=$(awk '/name: homelab/{f=1} f&&/token:/{print $2; exit}' "$HOME/Library/Application Support/tea/config.yml")
BASE=https://mac-mini.example:3000/api/v1   # curl with -k (self-signed cert)
```

## Detection logic

Apply this dispatch (mirrors SKILL.md):

**A sprint is a Forgejo milestone, and the milestone is the primary target.** Pointing `sprint-work` at a milestone walks its attached issues (`forgejo-walk`).

```
Else if $TARGET is a MILESTONE URL — starts with the instance URL and
       contains "/milestone/<id>" (or "/milestones"):
  → forgejo-walk. Parse <owner>/<repo> + <id>; fetch the milestone
    (GET /repos/<owner>/<repo>/milestones/<id>) for its title + the
    `## Sprint metadata` footer (the session timestamp lives there).

Else if matches /^[^/]+\/[^/#]+#\d+$/  (e.g. coreydaley/enclave#42):
  → forgejo-issue (a single issue), owner/repo + number from input.

Else if starts with the instance URL and contains "/issues/":
  → forgejo-issue, parse owner/repo + number from the URL.

Else if $TARGET is empty:
  → the in-progress sprint's milestone, via
    `python3 ~/.claude/lib/forgejo_sprints.py --current` (returns the
    open milestone with Status: in_progress). forgejo-walk.
    If none is in_progress, fall back to `… --next` (a planned
    milestone) and confirm before starting.

Else (a sprint reference — milestone name, session timestamp, prefix,
      or title fragment):
  → Resolve it to a milestone via
    `python3 ~/.claude/lib/forgejo_sprints.py --path <query>` (which
    matches a milestone by session/title across the repos). forgejo-walk.
    If nothing resolves, fail loudly: "No sprint milestone for <query>.
    Run /sprint-plan first." If it resolved a repo-less / untracked
    SPRINT.md-only sprint (no milestone), use the sprintmd path against
    its local SPRINT.md.
```

## Steps

1. **Run the dispatch** above to determine `path_mode` ∈ `{sprintmd, forgejo-issue, forgejo-walk}`.

2. **Resolve issue list / session dir:**
   - For `sprintmd`: resolve `$SESSION_DIR` and verify `$SESSION_DIR/SPRINT.md` exists. Bail if not.
   - For `forgejo-issue`: capture the single `ISSUE_REF` as `<owner>/<repo>#<n>`.
   - For `forgejo-walk`: expand the milestone into its attached issues. Milestones are repo-scoped, so the `(repo, milestone)` pair identifies the set:
     ```bash
     tea issues list --repo <owner>/<repo> --milestones "<milestone-title>" \
       --state all --output json
     ```
     Walk **only the open issues** (closed ones already shipped — see `detect-inflight`). Build the dependency graph from each issue's **Blocked by** `#<n>` references in its body (written by `/sprint-plan-to-issues`), topologically sort (unblocked first, then dependents), and within a tier sort by priority (P0 before P1, read from the issue body). Walk the resulting list in `implement` (which runs validate-success + commit-push per issue). Store each issue as `<owner>/<repo>#<n>`.

3. **Conflict handling.** If two or more in-progress states are surfaced (an in-progress milestone AND an explicit different `$ARGUMENTS`), surface the conflict — explicit argument wins, but tell the user what was overridden.

4. **Persist the resolved target:**
   ```bash
   scripts/walk.sh set --state "$STATE" --key path_mode    --value "<sprintmd|forgejo-issue|forgejo-walk>"
   scripts/walk.sh set --state "$STATE" --key session_dir  --value "<path or empty>"
   # Persist reports_root once, derived from session_dir (<root>/sprints/<TS>/).
   # Downstream nodes (implement, write-retro, detect-inflight) read this rather
   # than re-deriving via dirname-dirname, which is fragile across path edge cases.
   if [ -n "$SESSION_DIR" ]; then
     scripts/walk.sh set --state "$STATE" --key reports_root --value "$(dirname "$(dirname "$SESSION_DIR")")"
   fi
   # Two distinct query fields with different consumers:
   #
   # sprint_query: user-facing context. May be a Forgejo issue ref
   #   (owner/repo#n), a session timestamp/title fragment, or empty.
   #   Display only — don't pass to the tracker's --set-fit / --complete
   #   unconditionally because issue refs don't resolve there
   #   (the tracker is keyed by session timestamp + title).
   #
   # ledger_query: the canonical sprint-tracker key. Always set to the
   #   session basename (timestamp) when session_dir is known — that's
   #   what the tracker matches on. If session_dir is empty
   #   (some Forgejo paths before load-context resolves it), persist empty
   #   and let downstream callers fall back.
   scripts/walk.sh set --state "$STATE" --key sprint_query --value "<original target_args>"
   if [ -n "$SESSION_DIR" ]; then
     scripts/walk.sh set --state "$STATE" --key ledger_query --value "$(basename "$SESSION_DIR")"
   else
     scripts/walk.sh set --state "$STATE" --key ledger_query --value ""
   fi
   scripts/walk.sh set --state "$STATE" --key issue_ids      --value "<JSON list of owner/repo#n>"
   scripts/walk.sh set --state "$STATE" --key milestone_name --value "<name or empty>"
   scripts/walk.sh set --state "$STATE" --key milestone_repo --value "<owner/repo or empty>"
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
- `tea` not authenticated (no default login) → bail with "configure the `homelab` tea login first — see the `forgejo` skill."
