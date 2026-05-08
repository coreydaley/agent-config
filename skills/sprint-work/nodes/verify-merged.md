# Node: verify-merged

`--retro` mode: confirm the sprint's PRs have actually merged before writing a retrospective. User can override "write retro anyway" if the check is inconclusive.

## Inputs

- `path_mode`, `session_dir`, `issue_ids` from walker state
- `$SESSION_DIR/LINEAR.md` (if present)

```bash
STATE="<path>"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
```

## Steps

1. **Locate the sprint's PRs.** Use whichever source applies:

   - **`LINEAR.md` sidecar at `$SESSION_DIR/LINEAR.md`:** parse the "Issues created" table for IDs, then `gh pr list --search "<ID> in:title" --state all` per ID.
   - **GitHub fallback** (no LINEAR.md): `gh pr list --head <branch>` for the sprint's feature branch.
   - **Last resort:** ask the user to confirm.

2. **Check merged status.** For each found PR:
   - Merged → good.
   - Open → warn.
   - Closed without merge → flag.

3. **Decide:**
   - All PRs merged → route via `proceed` automatically (no user prompt needed; this is the happy path).
   - Some PRs not merged → AskUserQuestion: "PR X is still open. Write retro anyway?" → user picks proceed / cancel.
   - No PRs found via either source → AskUserQuestion: "Couldn't locate PRs for this sprint. Write retro anyway?"

4. **Persist results** for `write-retro`:
   ```bash
   scripts/walk.sh set --state "$STATE" --key merged_pr_count --value "<N>"
   scripts/walk.sh set --state "$STATE" --key unmerged_warnings --value "<JSON or empty>"
   ```

## Outputs

- `merged_pr_count`, `unmerged_warnings` in walker state

## Outgoing edges

- **`proceed`** → `write-retro`. All merged, or user said "write retro anyway."
- **`user_cancel`** → `terminal`. User backed out at the warning prompt.

Record exactly one:

```bash
# Proceed to write the retro:
scripts/walk.sh transition --state "$STATE" --from verify_merged --to write_retro --condition proceed

# Cancel:
scripts/walk.sh transition --state "$STATE" --from verify_merged --to terminal --condition user_cancel
```

## Notes

- **Default to proceed when ambiguous (no PRs found).** Retros are useful even when the artifact trail is incomplete; the user can capture lessons regardless.
- **Surface the unmerged warnings clearly** in the prompt — they should appear in RETRO.md too.
