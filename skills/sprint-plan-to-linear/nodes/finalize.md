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

   ## Activity-framed rename

   [Skip section if no rename. Otherwise:]
   - **Original bare title:** <stripped from SPRINT.md heading>
   - **Applied milestone name:** <completion-framed>

   ## Milestone description

   [written fresh / updated / left unchanged — pick based on rerun_mode]

   ## Issues created

   | Linear ID | Title | Priority | SPRINT.md source | Blocked by |
   |-----------|-------|----------|------------------|------------|
   | CON-1234 | ... | High | "Implementation Plan / P0 / Tasks 1-3" | - |

   ## Existing issues touched

   | Linear ID | Action | Notes |
   |-----------|--------|-------|
   | CON-789 | augmented | added milestone context comment |
   | CON-101 | linked as related to CON-1234 | |

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
                   - CON-1234: <title>
                   - CON-1235: <title>
   Existing touched: M
                     - CON-789: augmented (comment posted)
                     - CON-101: linked as related to CON-1234
   Labels applied: eng:<team>
   Sidecar:        $SESSION_DIR/LINEAR.md

   Reminder: any automated quality coaching from Linear arrives async;
             check Linear for suggestions on the milestone or issues.
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

- **LINEAR.md is the canonical mapping.** A future `/sprint-work-linear` (when it exists) reads this to walk back from Linear → SPRINT.md.
- **Don't include automated coaching feedback inline.** Any feedback from Linear's quality tooling arrives async; the user will see it in Linear when it lands.
