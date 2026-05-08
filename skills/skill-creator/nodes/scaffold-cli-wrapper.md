# Node: scaffold-cli-wrapper

Create the new skill's directory tree and an empty `SKILL.md` skeleton. CLI-wrapper skills are far simpler than graph-driven skills — typically a single `SKILL.md` plus optional `references/` files for command tables.

## Inputs

- Walker state keys: `skill_name`, `skills_dir`, `skill_summary`.

## Steps

1. **Validate the target path doesn't already exist:**
   ```bash
   SKILL_DIR="$skills_dir/$skill_name"
   if [ -d "$SKILL_DIR" ]; then
     echo "ERROR: skill directory already exists: $SKILL_DIR" >&2
     exit 1
   fi
   ```

2. **Create the directory tree.** No `nodes/` or `scripts/` for cli-wrappers:
   ```bash
   mkdir -p "$SKILL_DIR/references"
   ```
   Create `references/` even if the skill won't use it — easier to delete
   later than to recreate. If the skill is genuinely tiny (single SKILL.md,
   nothing else), the user can `rmdir` it during `iterate`.

3. **Write the SKILL.md skeleton** with placeholder content. Use this
   template, substituting `{{name}}` and `{{summary}}` from walker state:

   ```markdown
   ---
   name: {{name}}
   description: {{summary}}. Trigger phrases include "...", "...", "...".
   ---

   # {{name}}

   <one-paragraph framing of what the skill does and what makes it distinct>

   ## External Content Handling

   <verbatim block from lib/external-content-handling.md, only if the skill
   fetches external content; remove section if not>

   ## Common Operations

   ```bash
   # <one-line command description>
   <command>
   ```

   ## Tips

   - <tip 1>
   - <tip 2>

   ## Useful flags

   - `--<flag>` — <description>
   ```

4. **Persist the new skill's directory** in walker state:
   ```bash
   scripts/walk.sh set --state "$STATE" --key new_skill_dir --value "$SKILL_DIR"
   ```

5. **Print confirmation** to the user: directory created, skeleton written,
   ready for content authoring.

## Outputs

- New directory at `$skills_dir/$skill_name/` with `references/`
  subdirectory.
- `$skills_dir/$skill_name/SKILL.md` — skeleton with placeholders.
- Walker state key: `new_skill_dir`.

## Outgoing edges

Single outgoing edge — no condition needed.

```bash
scripts/walk.sh transition --state "$STATE" --from scaffold_cli_wrapper --to write_cli_wrapper
```

## Failure modes

- **`mkdir` fails** — likely a permissions problem. Surface verbatim.
- **Skeleton template doesn't fit the skill.** If the user's CLI tool has
  an unusual shape (e.g., interactive REPL rather than command-line invocation),
  adapt the template in `write-cli-wrapper`. The skeleton is a starting point,
  not a contract.

## Notes

- The "External Content Handling" block is only relevant if the wrapped CLI
  fetches content from external systems (e.g., `gh pr view` returns user-
  authored bodies; `linear issue view` returns descriptions). For skills
  that only execute local commands, the block can be omitted. The reference
  template is at `lib/external-content-handling.md`.
