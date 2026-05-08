# Node: ask-topology-approval

Gate the topology proposal. The user approves to start scaffolding, requests discussion to iterate, or cancels.

## Inputs

- Walker state keys: `topology_proposal`, `proposed_node_count`,
  `proposed_edge_count`.

## Steps

1. **Re-display the proposal recap.** Don't dump the full proposal again —
   the user already saw it in `sketch-topology` (or in the previous
   `discuss-topology` round). Show:
   - Node count + edge count
   - The macro flow in one sentence
   - Any distinctive shapes (discuss loops, parallel delegation, etc.)

2. **Ask the gate question** via `AskUserQuestion`:

   > Approve this topology and start scaffolding?
   >
   > - **approve** — looks good; create the skill directory and start
   >   writing files
   > - **discuss** — keep iterating on the topology
   > - **cancel** — stop; don't create the skill

3. **Record exactly one transition** based on the answer.

## Outputs

- No new state keys; pure gate.

## Outgoing edges

- **`user_approve`** → `scaffold_graph`. Topology is locked; start writing.
- **`user_discuss`** → `discuss_topology`. Iterate on the proposal.
- **`user_cancel`** → `summarize`. Bail without scaffolding.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from ask_topology_approval --to scaffold_graph    --condition user_approve
# or
scripts/walk.sh transition --state "$STATE" --from ask_topology_approval --to discuss_topology  --condition user_discuss
# or
scripts/walk.sh transition --state "$STATE" --from ask_topology_approval --to summarize         --condition user_cancel
```

## Failure modes

- **User wants to switch to cli-wrapper after seeing the topology.** Treat
  as `user_cancel` here, then advise the user to re-run `/skill-creator`
  and pick `cli_wrapper` at `decide-pattern`. The walker can't jump
  backward across the pattern fork — graphs don't have that edge by design.
