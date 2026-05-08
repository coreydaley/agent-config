# Node: dry-exit

`--dry` mode: print the dry-run preview inline and stop. No drafts commissioned, no SPRINT.md written.

## Inputs

- `session_dir`, `intent_path`, `phase_selections` from walker state
- `$SESSION_DIR/.dry-preview.md` (written by `intent` when `--dry`)

```bash
STATE="<path>"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
```

## Steps

1. **Print the preview inline.** Render `$SESSION_DIR/.dry-preview.md` directly so the user sees:
   - Phase selections with tiers
   - Intent summary
   - Estimated cost / token impact (if computable)
   - Pointers to `intent.md` and the session dir

2. **Append the absolute paths** so the user can re-run without `--dry` against the same session:
   ```
   📄 intent.md:        <path>
   📄 Session:          $SESSION_DIR
   📄 Re-run without --dry to commission drafts:
       /sprint-plan <seed>          # fresh
       (or rerun in-place: not currently supported — re-run picks new $REPORT_TS)
   ```

## Outputs

- The preview rendered inline. No additional file changes.

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from dry_exit --to terminal
```

## Notes

- **`intent.md` was written** even in dry mode. That's intentional — the user can review it and re-run from scratch later if they want.
- **Don't commission any workers.** No `Agent` calls, no `codex exec`. Pure orchestrator render-and-stop.
