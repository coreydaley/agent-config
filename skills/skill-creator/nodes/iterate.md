# Node: iterate

Apply user-requested revisions to the new skill, then loop back to `ask-final-approval` for re-evaluation. Functions as the post-scaffold revision loop, regardless of which branch (graph-driven or cli-wrapper) produced the skill.

## Inputs

- Walker state keys: `new_skill_dir`, `chosen_pattern`, `files_written`.
- The user's revision request — captured in conversation, not state.

## Steps

1. **Ask the user what specifically to revise.** Common requests:
   - **Content tweaks** — wording in `SKILL.md` description, additional
     command examples, missing tip.
   - **Structural changes** (graph-driven) — split a node, merge two
     nodes, rename a condition label, add a back-edge. These ripple into
     `graph.dot` + the affected sidecars.
   - **Move content to references** — `SKILL.md` is too long; move a
     section into `references/<topic>.md`.
   - **Delete unused folders** — empty `references/` or `scripts/` that
     the skill doesn't need.

2. **For graph-driven structural changes**, re-validate after applying:
   ```bash
   cd "$new_skill_dir" && python3 scripts/validate.py
   ```
   And re-render if `dot` is installed:
   ```bash
   bash scripts/render.sh
   ```
   If the validator now fails, surface the error and fix before looping.
   Don't transition with a known-broken graph.

3. **For cli-wrapper content changes**, no validator runs — just edit the
   files in place and verify the frontmatter still parses (no malformed
   YAML).

4. **Update walker state** with what changed:
   ```bash
   scripts/walk.sh set --state "$STATE" --key last_revision --value "<short description>"
   ```
   This is informational; `ask-final-approval` can show the user what was
   changed since last review.

5. **Loop back.** This node has a single back-edge to
   `ask-final-approval` — apply the revisions, then transition.

## Outputs

- Modified files in `$new_skill_dir` (which files depend on the request).
- Walker state key: `last_revision`.

## Outgoing edges

Single outgoing edge — no condition needed.

```bash
scripts/walk.sh transition --state "$STATE" --from iterate --to ask_final_approval --condition revisions_applied
```

(The condition label `revisions_applied` is only required because the
graph declares it on the back-edge; the walker treats single-outgoing-edge
nodes as unconditional but the label is preserved here for graph
readability.)

## Failure modes

- **User keeps iterating without converging.** If the revision loop
  exceeds 5-6 cycles, prompt explicitly: "Is the underlying skill design
  wrong, or is this a content issue? If design, cancel and re-run
  `/skill-creator` from a fresh frame." Loops can mask scope problems.
- **Structural change to the graph creates an orphan or dangling edge.**
  The validator catches it. Don't transition until clean.
