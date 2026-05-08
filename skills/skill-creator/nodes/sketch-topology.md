# Node: sketch-topology

Propose a topology (nodes, edges, gates) for the new graph-driven skill. The output is a **proposal**, not the final graph — the user reviews it at `ask-topology-approval`.

## Inputs

- Walker state keys: `skill_name`, `skill_summary`, `example_invocations`,
  `freedom_level`, `candidate_resources`.
- Reference: `docs/DOT-GRAPH-SKILL-PATTERN.md` — node types, edge condition
  conventions, common patterns (linear backbone, discuss loop, mode dispatch,
  cleanup sink, parallel delegation).

## Steps

1. **Sketch from common topology shapes** rather than starting blank. The
   pattern catalog in `docs/DOT-GRAPH-SKILL-PATTERN.md` covers:
   - Linear backbone with process nodes
   - User-input gate then act
   - Discuss loop (gate → discuss → back-edge to gate)
   - Decision node before destructive operation
   - Cleanup sink before terminal
   - Parallel delegation
   - Mode dispatch (flag-driven subgraphs)
   - Per-item loop internal to a node

   Most skills are a linear backbone with 1-3 of these shapes layered on.

2. **Identify the four node types** in the proposed flow:
   - **Process** — does work, single outgoing edge (or routing on persisted
     state). Light blue rounded box.
   - **Decision** — pure routing on observable state, no user input. Amber
     diamond.
   - **User-input** — `AskUserQuestion` gate. Coral diamond.
   - **Terminal** — sink, double-circle, no outgoing edges. Green.

3. **Identify edge condition labels** for nodes with multiple outgoing
   edges. Single-outgoing-edge nodes don't need labels. Conventions
   (snake_case, source-node scoped):
   `user_approve` / `user_revise` / `user_cancel` / `user_continue` /
   `user_done` / `discussion_done` / `prior_exists` / `setup_failed` /
   `addressable` / `keep_iterating` / `iter_cap` etc.

4. **Sanity-check the topology** against the doc's "When NOT to use this
   pattern" criteria:
   - At least 5 phases or distinct steps?
   - User-input gates that affect routing?
   - Loops or conditional branches?
   - Per-run artifacts that benefit from a session folder?

   If none of those apply, route back to the user — the cli-wrapper pattern
   probably fits better. (This is a soft check; the user already chose
   graph-driven at `decide-pattern`, so honor that unless the topology is
   clearly trivial.)

5. **Produce the proposal** in three forms, all included in the output:
   - **Prose summary** — 3-5 sentences naming the macro flow and any
     distinctive shapes (loops, forks, cleanup sinks).
   - **Node table** — one row per node, columns: `id` (snake_case in
     `graph.dot`, kebab-case as filename), `type`, `purpose`.
   - **Edge list** — one bullet per edge: `<src> -> <dst> [condition]`.

6. **Persist the proposal** for downstream nodes:
   ```bash
   scripts/walk.sh set --state "$STATE" --key topology_proposal --value "<full proposal text>"
   scripts/walk.sh set --state "$STATE" --key proposed_node_count --value "<N>"
   scripts/walk.sh set --state "$STATE" --key proposed_edge_count --value "<M>"
   ```

7. **Show the proposal to the user** before transitioning, so the next gate
   has something concrete to react to.

## Outputs

- Walker state keys: `topology_proposal`, `proposed_node_count`,
  `proposed_edge_count`.
- The proposal printed to the user's screen (no file written yet — that
  happens in `write-graph` after approval).

## Outgoing edges

Single outgoing edge — no condition needed.

```bash
scripts/walk.sh transition --state "$STATE" --from sketch_topology --to ask_topology_approval
```

## Failure modes

- **Topology has too few nodes (<5).** Push the user toward cli-wrapper at
  the next opportunity, or accept it but flag that the graph overhead may
  not earn out.
- **Topology has unbounded nodes (>25).** Suggest splitting into two
  composable skills (e.g., `/sprint-seed` + `/sprint-plan` rather than one
  monolith). Bring this up at the proposal step, before approval.

## Notes

- This node does not write any files. All writing happens in `scaffold-graph`
  and `write-graph` after the user approves the topology. Treat the proposal
  as cheap/disposable — iterating on it is the whole point of the discuss
  loop with `discuss-topology`.
