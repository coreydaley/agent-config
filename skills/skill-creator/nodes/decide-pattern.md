# Node: decide-pattern

Pick the authoring pattern. The two supported patterns are **graph-driven** (multi-phase workflow with a `graph.dot` and per-node sidecars) and **cli-wrapper** (cheat sheet for a CLI tool, single SKILL.md with optional references/).

## Inputs

- Walker state keys: `skill_name`, `skill_summary`, `suspected_pattern`,
  `freedom_level`, plus everything else captured in `discuss-skill`.

## Steps

1. **Make a recommendation.** Based on the discussion, propose one of the
   two patterns with a short rationale. The patterns map roughly to:

   - **graph-driven** — the skill has 4+ phases, user-input gates that
     affect routing, loops or conditional branches, per-run artifacts, or a
     need to resume from a crash. Examples: `/sprint-plan`, `/review-pr-*`,
     `/sprint-self-review`, `/polish-pull-request`. Reference:
     `docs/DOT-GRAPH-SKILL-PATTERN.md`.
   - **cli-wrapper** — the skill is a one-shot operation or a thin cheat
     sheet for a CLI tool. No internal state machine, no user gates.
     Examples: `gh`, `gws`, `linear`, `obsidian`, `orbstack`. Single
     `SKILL.md` plus optional `references/` for command tables.

   The "useful test" from `docs/DOT-GRAPH-SKILL-PATTERN.md`: if you'd be
   tempted to write the SKILL.md as a flowchart anyway (phases with decision
   points), the graph-driven pattern fits. If the SKILL.md would be a list
   of independent commands, leave it procedural / cli-wrapper.

2. **Ask the gate question** via `AskUserQuestion`. Make the recommendation
   the first option and tag it `(Recommended)`:

   > Which pattern fits best?
   >
   > - **graph-driven** — multi-phase workflow walked deterministically by
   >   `lib/graph_walker.py`. State machine in `graph.dot`, prose in
   >   `nodes/<id>.md`. Best for 4+ phases, gates, loops.
   > - **cli-wrapper** — single SKILL.md, optionally with `references/`. Best
   >   for one-shot operations and CLI cheat sheets.
   > - **cancel** — don't create the skill.

3. **Persist the choice.**
   ```bash
   scripts/walk.sh set --state "$STATE" --key chosen_pattern --value "graph_driven"  # or cli_wrapper
   ```

4. **Confirm or correct the skill name.** Before transitioning, validate that
   the running `skill_name` is kebab-case, doesn't collide with an existing
   skill in `skills_dir`, and matches what the skill actually does. If not,
   ask the user once for the correct name and update `skill_name`.

## Outputs

- `chosen_pattern` walker state key.
- Validated `skill_name` walker state key.

## Outgoing edges

- **`graph_driven`** → `sketch_topology`.
- **`cli_wrapper`** → `scaffold_cli_wrapper`.
- **`user_cancel`** → `summarize`.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from decide_pattern --to sketch_topology       --condition graph_driven
# or
scripts/walk.sh transition --state "$STATE" --from decide_pattern --to scaffold_cli_wrapper  --condition cli_wrapper
# or
scripts/walk.sh transition --state "$STATE" --from decide_pattern --to summarize             --condition user_cancel
```

## Failure modes

- **User picks graph-driven for a 2-phase skill.** Push back gently: "This
  has only X phases and no gates — it'll fight the pattern. Cli-wrapper or
  a simple procedural SKILL.md would be lighter. Want to reconsider?" Don't
  override; the user has final say.
- **User picks cli-wrapper for a multi-gated workflow.** Same shape of
  pushback in reverse. The dot-graph pattern earns its overhead when the
  skill has phases, gates, and loops — without those, it's overkill, but a
  skill with those that *isn't* on the pattern will rot.

## Notes

- A third pattern exists in theory ("simple procedural SKILL.md, no graph,
  no CLI") — Anthropic's default skill-creator targets it. We deliberately
  don't support it here because every skill in agent-config that didn't fit
  cli-wrapper has either grown into a graph-driven skill or become technical
  debt. If the user really wants a one-off procedural skill, send them to
  the backed-up Anthropic skill-creator at
  `skills/skill-creator.anthropic-backup/` (if it still exists) or hand-roll
  the SKILL.md.
