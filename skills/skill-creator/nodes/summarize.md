# Node: summarize

Print the hand-off message and route to `terminal`. Reached from any cancel route or from `ask-final-approval` on approve.

## Inputs

- Walker state keys: `new_skill_dir` (may not exist if cancel happened
  before scaffolding), `chosen_pattern`, `files_written`,
  `validation_result`, `skill_name`.
- Walker state's `current_node` history (via `scripts/walk.sh history`)
  reveals which route led here, which determines the message tone.

## Steps

1. **Determine the route.** Three possibilities, each gets a different
   message:

   - **Approved at `ask-final-approval`** — hand-off message: skill is
     created, where it lives, what was written, what to do next.
   - **Cancelled at any earlier gate** (`ask-wrap-up`,
     `decide-pattern`, `ask-topology-approval`) — short bail message:
     no files were created, walker state can be discarded.
   - **Cancelled at `ask-final-approval`** — confirm the directory was
     deleted (in `iterate` / `ask-final-approval` cancel handling), state
     that nothing remains.

2. **Print the appropriate message.**

   For **approved**:
   ```
   ✅ Skill created: {{skill_name}}
   
   Location: $new_skill_dir
   Pattern: {{chosen_pattern}}
   Files written: {{files_written}}
   {{validation_result, if graph-driven}}
   
   Next steps:
   - Skill is auto-symlinked into ~/.claude/skills/ via `make all`.
     If you've run `make all` before, the new skill is already live —
     restart Claude Code to pick it up.
   - Skill is uncommitted. When ready, commit and push.
   - Test the skill: invoke it and walk the happy path. For graph-
     driven skills, also exercise each gate's branches.
   ```

   For **cancelled before scaffolding**:
   ```
   Skill creation cancelled. No files were written.
   ```

   For **cancelled at final approval**:
   ```
   Skill creation cancelled. The directory at {{new_skill_dir}} was deleted.
   Walker state at {{state path}} can be discarded.
   ```

3. **Don't run `git status` or any side-effect commands.** This is a
   pure print-and-exit node.

## Outputs

- Hand-off message printed to the user. No file changes.

## Outgoing edges

Single outgoing edge — no condition needed.

```bash
scripts/walk.sh transition --state "$STATE" --from summarize --to terminal
```

## Failure modes

- **`new_skill_dir` is set but the directory doesn't exist** — the user
  cancelled at `ask-final-approval` and the cleanup ran successfully.
  This is the expected case for that route; just confirm in the message.
