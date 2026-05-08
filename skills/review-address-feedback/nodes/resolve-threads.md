# Node: resolve-threads

Resolve the threads the user opted into. Pure side-effect node, single outgoing edge.

## Inputs

- `resolve_choice`, `replied_threads_path` from walker state
- `$SESSION_DIR/replied-threads.json` (or `threads-to-resolve.json` if user picked)

```bash
STATE="$SESSION_DIR/.walk-state.json"
RESOLVE_CHOICE=$(scripts/walk.sh get --state "$STATE" --key resolve_choice)
```

## Steps

Build the list of `thread_id`s to resolve:

- `all` → every entry in `replied-threads.json`.
- `pick` → entries listed in `threads-to-resolve.json`.

For each thread id:

```bash
gh api graphql -f query='
  mutation($id:ID!){
    resolveReviewThread(input:{threadId:$id}){ thread{ id isResolved } }
  }' -F id="$THREAD_ID"
```

Track results in `$SESSION_DIR/resolved-threads.json` for `ADDRESSED.md`:

```json
[{"thread_id": "...", "resolved": true, "error": null}, ...]
```

## Outputs

- Resolved threads on GitHub
- `$SESSION_DIR/resolved-threads.json`

## Outgoing edges

- → `persist` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from resolve_threads --to persist
```

## Failure modes

- One mutation fails (permission, thread already resolved by reviewer, etc.) → record `error` for that entry, continue with the rest. Don't bail on one failure.
- All mutations fail (auth, network) → still route to `persist`. The user needs the artifact regardless. Surface the errors in the printed output.
