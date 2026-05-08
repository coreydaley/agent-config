# Node: scaffold-graph

Create the new skill's directory tree and copy the template scripts. After this node, the directory exists and the walker scripts are in place — but `graph.dot`, `nodes/*.md`, and `SKILL.md` are still empty.

## Inputs

- Walker state keys: `skill_name`, `skills_dir`, `topology_proposal`.

## Steps

1. **Validate the target path doesn't already exist:**
   ```bash
   SKILL_DIR="$skills_dir/$skill_name"
   if [ -d "$SKILL_DIR" ]; then
     echo "ERROR: skill directory already exists: $SKILL_DIR" >&2
     exit 1
   fi
   ```
   If it exists, surface to the user — don't overwrite. They likely want
   `iterate` on the existing skill, not re-scaffold.

2. **Create the directory tree:**
   ```bash
   mkdir -p "$SKILL_DIR"/{nodes,scripts,references}
   ```
   Keep `references/` even if the skill won't use it — easier to delete
   later than to recreate.

3. **Copy the walker scripts** from `commit/` (smallest reference template):
   ```bash
   COMMIT_DIR="$skills_dir/commit"
   cp "$COMMIT_DIR/scripts/walk.sh"      "$SKILL_DIR/scripts/walk.sh"
   cp "$COMMIT_DIR/scripts/render.sh"    "$SKILL_DIR/scripts/render.sh"
   cp "$COMMIT_DIR/scripts/validate.py"  "$SKILL_DIR/scripts/validate.py"
   chmod +x "$SKILL_DIR/scripts/"*.sh "$SKILL_DIR/scripts/validate.py"
   ```
   `walk.sh` and `render.sh` are skill-agnostic — they resolve paths via
   `${BASH_SOURCE[0]}` so they work without modification. `validate.py`
   has one hardcoded reference to update (the docstring).

4. **Update `validate.py` docstring** to name the new skill:
   ```bash
   sed -i.bak "s/Validate the commit state machine graph./Validate the $skill_name state machine graph./" \
     "$SKILL_DIR/scripts/validate.py"
   rm "$SKILL_DIR/scripts/validate.py.bak"
   ```
   (On macOS `sed -i` requires a backup extension; the `rm` cleans up the
   intermediate file.)

5. **Persist the new skill's directory** in walker state:
   ```bash
   scripts/walk.sh set --state "$STATE" --key new_skill_dir --value "$SKILL_DIR"
   ```

6. **Print a short confirmation** to the user: directory created, scripts
   copied, ready to write content.

## Outputs

- New directory at `$skills_dir/$skill_name/` with `nodes/`, `scripts/`,
  `references/` subdirectories.
- Three executable files: `scripts/walk.sh`, `scripts/render.sh`,
  `scripts/validate.py`.
- Walker state key: `new_skill_dir`.

## Outgoing edges

Single outgoing edge — no condition needed.

```bash
scripts/walk.sh transition --state "$STATE" --from scaffold_graph --to write_graph
```

## Failure modes

- **`commit/` reference template missing.** If the source files don't
  exist in `$skills_dir/commit/scripts/`, fall back to copying from
  `sprint-seed/scripts/` (any graph-driven skill works as a template).
  If neither exists, surface to the user — agent-config is in a broken
  state and the skill-creator can't proceed.
- **`mkdir` or `cp` fails** — likely a permissions problem. Surface the
  error verbatim.

## Notes

- The choice of `commit/` as the template is arbitrary — any graph-driven
  skill's `scripts/` directory has the same three files. Picked `commit/`
  because it's the smallest (5 nodes) and won't collect non-template cruft
  over time.
