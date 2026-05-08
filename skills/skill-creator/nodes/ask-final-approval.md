# Node: ask-final-approval

The convergence gate for both branches. The user decides whether the new skill is ready for hand-off, needs more revision, or should be discarded.

## Inputs

- Walker state keys: `new_skill_dir`, `chosen_pattern`, `files_written`,
  `validation_result` (graph-driven only), `smoke_test_routes`
  (graph-driven only).

## Steps

1. **Show the user a summary** of what was created. Be specific:
   - Path to the new skill directory.
   - File count and types (`graph.dot`, N node sidecars, SKILL.md,
     references, scripts).
   - For graph-driven: the validation result (e.g., "OK: 12 nodes, 17
     edges") and the smoke-test routes exercised.
   - Any leftover TODOs or empty `references/` the user might want to
     fill or delete.

2. **Ask the gate question** via `AskUserQuestion`:

   > Skill ready to hand off?
   >
   > - **approve** — looks good; reach `terminal` and stop. The skill is
   >   uncommitted; the user will commit when they're ready.
   > - **iterate** — apply revisions and re-show.
   > - **cancel** — discard the new skill directory and stop.

3. **For `cancel`,** delete the new skill directory before transitioning
   to `summarize`:
   ```bash
   rm -rf "$new_skill_dir"
   ```
   This is destructive — the user explicitly asked to bail. Don't ask
   again. But do confirm the path being deleted before running `rm -rf`.

4. **Record exactly one transition** based on the answer.

## Outputs

- For `cancel`: deleted `$new_skill_dir`. Otherwise: no file changes at
  this node — the skill stays as-is.

## Outgoing edges

- **`user_approve`** → `summarize`. Hand off the new skill.
- **`user_iterate`** → `iterate`. Apply revisions.
- **`user_cancel`** → `summarize`. Discard the directory and exit.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_final_approval --to summarize  --condition user_approve
# or
scripts/walk.sh transition --state "$STATE" --from ask_final_approval --to iterate    --condition user_iterate
# or
scripts/walk.sh transition --state "$STATE" --from ask_final_approval --to summarize  --condition user_cancel
```

## Failure modes

- **`rm -rf` fails on cancel.** If permissions block the cleanup, surface
  the error and the path. Don't transition to `summarize` until the
  directory is gone — leaving a half-written skill in the tree creates
  exactly the drift problem the dot-graph pattern is designed to prevent.
