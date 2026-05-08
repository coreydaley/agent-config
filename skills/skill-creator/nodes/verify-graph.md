# Node: verify-graph

Verify the new graph-driven skill is structurally sound: the validator passes, the graph renders, and the walker can be smoke-tested through key paths.

## Inputs

- Walker state keys: `new_skill_dir`, `files_written`,
  `proposed_node_count`, `proposed_edge_count`.

## Steps

1. **Run the validator:**
   ```bash
   cd "$new_skill_dir" && python3 scripts/validate.py
   ```
   Expected output:
   ```
   OK: <N> nodes, <M> edges, 1 terminal node(s).
   ```
   Where `N` matches `proposed_node_count` and `M` matches
   `proposed_edge_count`. If the counts disagree, the proposal and the
   actual `graph.dot` drifted — re-read both and reconcile.

   On any `FAIL:` lines, fix the underlying issue. Common failures:
   - **Edge endpoint not declared** — typo in the edge or a node was
     removed without removing its edges.
   - **Sidecar missing** — `nodes/<id>.md` was forgotten. Write it.
   - **Terminal has outgoing edge** — a node with `shape=doublecircle` got
     an outgoing edge by mistake. Re-shape or re-route.
   - **Orphan node** — a node has no incoming edges. Either route to it,
     remove it, or rename it to `init` if it's the entry point.

2. **Render the graph** (if not already done in `write-graph`):
   ```bash
   cd "$new_skill_dir" && bash scripts/render.sh
   ```
   Confirms `graphviz` parses `graph.dot`. If it fails with a syntax
   error, the DOT file has a typo; fix and re-run. If `dot` isn't
   installed, surface `brew install graphviz` and continue — rendering is
   nice-to-have, not blocking.

3. **Smoke-test the walker on representative routes.** Run from a temp
   state file so it doesn't pollute the skill-creator's state:
   ```bash
   SMOKE_STATE=$(mktemp)
   bash "$new_skill_dir/scripts/walk.sh" init --state "$SMOKE_STATE"
   bash "$new_skill_dir/scripts/walk.sh" transition --state "$SMOKE_STATE" --from init --to <next>
   # ... step through the happy path to terminal
   bash "$new_skill_dir/scripts/walk.sh" where --state "$SMOKE_STATE"
   ```
   Cover at least:
   - **Happy path** — full pipeline through to terminal.
   - **Each user-input gate's branches** — including cancel routes.
   - **Loops** — exercise the back-edge and the loop-exit.
   - **Illegal transition** — confirm the walker refuses with valid
     alternatives listed (e.g.
     `bash walk.sh transition --from init --to nonexistent` should error).

   Smoke tests don't run real node work. They verify the graph contract:
   the walker enforces documented routes.

4. **Capture results** in walker state for `ask-final-approval` to display:
   ```bash
   scripts/walk.sh set --state "$STATE" --key validation_result --value "OK: <N> nodes, <M> edges"
   scripts/walk.sh set --state "$STATE" --key smoke_test_routes --value "<list of routes exercised>"
   ```

## Outputs

- `$new_skill_dir/graph.svg` (if graphviz installed).
- Walker state keys: `validation_result`, `smoke_test_routes`.

## Outgoing edges

Single outgoing edge — no condition needed.

```bash
scripts/walk.sh transition --state "$STATE" --from verify_graph --to ask_final_approval
```

## Failure modes

- **Validator fails with errors that can't be fixed by tweaking the graph.**
  If the topology proposal turns out to be unworkable (e.g., graph has a
  cycle of process nodes with no exit, or an unreachable subgraph), surface
  the issue plainly and route to `user_cancel` at `ask-final-approval`.
  The user can re-run `/skill-creator` and propose a different topology
  rather than salvaging a broken one.
- **Walker refuses transitions during smoke-test.** This is a real
  contract violation — fix the graph or the test, don't bypass.
