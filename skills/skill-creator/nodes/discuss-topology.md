# Node: discuss-topology

Iterate on the topology proposal in a back-and-forth with the user. Updates `topology_proposal` and loops back to `ask-topology-approval`.

## Inputs

- Walker state keys: `topology_proposal`, `proposed_node_count`,
  `proposed_edge_count`, plus everything from `discuss-skill`.

## Steps

1. **Ask the user what they want to change.** Be concrete: "Which nodes,
   edges, or condition labels would you adjust?" Common requests:
   - Add a node (often a missing decision or cleanup step)
   - Remove a node (over-decomposed; merge with neighbor)
   - Rename a node or condition label
   - Add a back-edge (turn a path into a loop)
   - Split or merge a fork
   - Change a process node into a decision/user-input node (or vice versa)

2. **Apply the change to the running proposal.** Don't write `graph.dot`
   yet — keep the proposal in walker `extra` until approval. Update:
   ```bash
   scripts/walk.sh set --state "$STATE" --key topology_proposal --value "<updated proposal>"
   scripts/walk.sh set --state "$STATE" --key proposed_node_count --value "<N>"
   scripts/walk.sh set --state "$STATE" --key proposed_edge_count --value "<M>"
   ```

3. **Show the updated proposal.** Same three-form format as
   `sketch-topology` (prose / node table / edge list), so the user can
   compare against the prior version.

4. **Decide on transition.** This node has a single back-edge to
   `ask-topology-approval`, but the discuss loop is *internal* — keep
   iterating in this node until the user signals they're ready to re-evaluate
   the gate. When ready, transition.

## Outputs

- Updated walker state keys (per step 2).

## Outgoing edges

Single outgoing edge — no condition needed.

```bash
scripts/walk.sh transition --state "$STATE" --from discuss_topology --to ask_topology_approval
```

## Failure modes

- **User keeps redesigning indefinitely.** If the discussion has spiraled
  past 5-6 rounds and the proposal keeps churning, stop and ask: "Is the
  topology actually wrong, or is the underlying skill scope wrong?" If
  the latter, route to `user_cancel` at the next gate and re-run
  `/skill-creator` from scratch — fixing scope by tweaking nodes is a
  losing game.
