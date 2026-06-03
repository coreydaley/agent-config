# Node: finalize

Write the local `FORGEJO.md` sidecar (a convenience record of the
milestone → issues mapping) and print a concise summary. The canonical
record is the **milestone and its issues** in Forgejo; `FORGEJO.md` is a
local working copy for downstream tooling.

## Inputs

- All run-scoped state and `issue_results` from `create-issues`
- `session_dir`, `sprint_title`, `milestone_title`, `primary_repo`,
  `repositories` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
PRIMARY_REPO=$(scripts/walk.sh get --state "$STATE" --key primary_repo)
```

## Steps

1. **Compute today's date:**
   ```bash
   TODAY=$(date +%Y-%m-%d)
   ```

2. **Write `$SESSION_DIR/FORGEJO.md`** from this template:

   ```markdown
   # Forgejo Mapping — <Milestone Title>

   **Repo:** <primary_repo> — https://mac-mini.example:3000/<primary_repo>
   **Milestone:** <Milestone Title> — https://mac-mini.example:3000/<primary_repo>/milestones
   **Created:** <YYYY-MM-DD>
   **Source:** $SESSION_DIR/SPRINT.md

   ## Repositories

   [Render each entry from the `repositories` walker-state list verbatim.
   Pin the rendering — don't re-paraphrase from SPRINT.md:]

   - <org>/<repo> (primary)
   - <org>/<repo2>

   [If repo_count > 1, add a note that all issues were created in
   <primary_repo>; cross-repo work is noted in issue bodies.]

   ## Milestone description

   Unchanged by this skill — it's the SPRINT plan, owned by `/sprint-plan`.

   ## Issues created

   One issue per task, all self-assigned to `coreydaley`.

   | # | Title | Priority | Files | SPRINT.md task | Depends on | Related |
   |---|-------|----------|-------|----------------|------------|---------|
   | 7 | ... | P0 | api/foo.go | "Implementation Plan / P0 / item 1" | - | - |
   | 8 | ... | P1 | api/cache.go | "Implementation Plan / P1 / item 4" | #7 | #9 |

   The `#` column is the Forgejo issue number. `Files` and the task
   reference are recorded for downstream consumers (e.g. `/sprint-work`
   resolving issues back to repos). `Depends on` notes whether the link
   was wired as a **native** Forgejo dependency (deps feature on) or a
   body-only ref (off) — e.g. `#7 (native)` vs `#7 (body)`.

   ## Labels applied

   Every issue carries its `priority/p*` label. Kind labels applied:
   <label>, <label>   (or "none").

   [If any kind labels were desired but missing, note them here too.]

   ---

   *Created by `/sprint-plan-to-issues`. Run it ONCE per milestone — it
   does not dedupe; re-running creates a duplicate issue set.*
   ```

3. **Skip empty sections.** If no labels were applied, say so. The
   artifact reflects what actually happened.

4. **Print a concise summary inline:**

   ```
   Repo:           <primary_repo>
   Milestone:      <title> — <milestone URL>   (the plan lives in its description)
   Issues created: N   (one per task, self-assigned to coreydaley)
                   - #7:  <title>  [priority/p0]
                   - #8:  <title>  [priority/p1, depends on #7, related #9]
   Dependencies:   <native links wired | body-only — repo deps feature off>
   Kind labels:    <list or none>
   Sidecar:        $SESSION_DIR/FORGEJO.md   (local record of the issue mapping)
   ```

5. **Don't run `git commit` or `git push`.** This skill doesn't touch
   git. Issue creation goes through the Forgejo API / `tea`.

6. **Don't rewrite the milestone description.** The plan (the SPRINT doc)
   and the `## Sprint metadata` footer live there and belong to
   `/sprint-plan` + `/sprints`. This skill only adds issues to the
   milestone.

## Outputs

- N issues attached to the existing milestone (the canonical record)
- `$SESSION_DIR/FORGEJO.md` (local convenience record of the mapping)
- Printed summary

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to terminal
```

## Failure modes

- Disk full / permissions on `$SESSION_DIR` → surface error, route to
  terminal. The Forgejo mutations already happened; the sidecar is
  informational. The user can retrieve the issue list from Forgejo
  directly if FORGEJO.md fails to write.

## Notes

- **The milestone + its issues are canonical.** `FORGEJO.md` is a local
  convenience record; `/sprint-work` reads the milestone and its issues
  directly from Forgejo.
