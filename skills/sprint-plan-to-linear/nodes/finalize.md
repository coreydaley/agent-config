# Node: finalize

Write the `LINEAR.md` sidecar (the canonical mapping from SPRINT.md → Linear) and print a concise summary. Sole writer of the artifact.

## Inputs

- All run-scoped state and the `issue_results` from `create-issues`
- `session_dir`, `milestone_name`, `milestone_id`, `project_url`, `team_key`, `bare_title`, `proposed_title`, `rerun_mode` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
```

## Steps

1. **Compute today's date:**
   ```bash
   TODAY=$(date +%Y-%m-%d)
   ```

2. **Write `$SESSION_DIR/LINEAR.md`** from this template:

   ```markdown
   # Linear Mapping — <Milestone Name>

   **Project:** <Project URL>
   **Milestone:** <Milestone Name> — <milestone URL or ID>
   **Team:** <team-key>
   **Created:** <YYYY-MM-DD>
   **Source:** $SESSION_DIR/SPRINT.md

   ## Repositories

   Read `repositories` from walker state (set by `parse-sprint`) and render each entry verbatim. **Pin the rendering** — don't rely on the agent reading SPRINT.md and re-paraphrasing. Concretely:

   ```python
   for entry in repositories:
       primary = " (primary)" if entry["primary"] else ""
       print(f"- {entry['org']}/{entry['repo']}{primary}")
   ```

   Order matches `parse-sprint`'s parse order; primary-tagged entry stays in its original position. Example output:

   - <org>/<repo> (primary)
   - <org>/<repo2>

   ## Activity-framed rename

   [Skip section if no rename. Otherwise:]
   - **Original bare title:** <stripped from SPRINT.md heading>
   - **Applied milestone name:** <completion-framed>

   ## Milestone description

   [written fresh / updated / left unchanged — pick based on rerun_mode]

   ## Issues created

   | Linear ID | Title | Priority | branchName | Files (repos) | SPRINT.md source | Blocked by |
   |-----------|-------|----------|------------|---------------|------------------|------------|
   | PROJ-1234 | ... | High | `coreydaley/proj-1234-add-foo` | acme/web-app; acme/api | "Implementation Plan / P0 / Tasks 1-3" | - |

   The `branchName` and `Files (repos)` columns are required for downstream consumers:
   - `/sprint-self-review`'s PR-shortcut search matches `branchName` against `headRefName` (PR-shortcut → sprint resolution).
   - `/sprint-work/verify-merged`'s expected-PR matrix (linear-walk) uses `Files (repos)` to know which (issue, repo) cells should produce a PR.
   - `/sprint-self-review/init.md` (linear-issue mode) narrows worktree resolution to the issue's actual repos.

   `Files (repos)` is the deduplicated set of `<org>/<repo>` prefixes from each issue's Files section, joined by `; `.

   ## Existing issues touched

   | Linear ID | Action | Notes |
   |-----------|--------|-------|
   | PROJ-789 | augmented | added milestone context comment |
   | PROJ-101 | linked as related to PROJ-1234 | |

   ## Labels applied

   - eng:<team>

   ---

   *Re-running `/sprint-plan-to-linear` on this SPRINT.md will detect this file
   and offer to create-only-new (default) / update / start fresh.*
   ```

3. **Skip empty sections.** If no rename, drop the rename section. If no augment/replace/link actions happened, drop the "Existing issues touched" table. The artifact reflects what actually happened.

4. **Print a concise summary inline:**

   ```
   Project:        <name> — <URL>     (unchanged — for reference only)
   Milestone:      <name> — <URL>
                   <created / updated / re-used>
   Issues created: N
                   - PROJ-1234: <title>
                   - PROJ-1235: <title>
   Existing touched: M
                     - PROJ-789: augmented (comment posted)
                     - PROJ-101: linked as related to PROJ-1234
   Labels applied: eng:<team>
   Sidecar:        $SESSION_DIR/LINEAR.md

   Reminder: any automated coaching bots in Linear will post feedback async;
             check Linear for quality suggestions on the milestone or issues.
   ```

5. **Don't run `git commit` or `git push`.** This skill doesn't touch git. Linear is the artifact system.

6. **Don't comment on SPRINT.md.** The mapping is in LINEAR.md.

## Outputs

- `$SESSION_DIR/LINEAR.md`
- Printed summary

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to terminal
```

## Failure modes

- Disk full / permissions on `$SESSION_DIR` → surface error, route to terminal. The Linear mutations already happened; the sidecar is informational. The user can retrieve the issue list from Linear directly if LINEAR.md fails to write.

## Notes

- **LINEAR.md is the canonical mapping.** A future `/sprint-work` (when it exists) reads this to walk back from Linear → SPRINT.md.
- **Don't include automated coaching feedback inline.** That's async; the user will see it on Linear when it lands.
