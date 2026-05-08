# Node: ask-resolve-threads

Replies posted. Ask whether to resolve the threads we replied to. **Default: no** — resolution is the reviewer's call by convention.

## Inputs

- `replied_threads_path` from walker state
- `$SESSION_DIR/replied-threads.json` (list of threads we just replied to)

```bash
STATE="$SESSION_DIR/.walk-state.json"
REPLIED_PATH=$(scripts/walk.sh get --state "$STATE" --key replied_threads_path)
```

## Steps

Use `AskUserQuestion`. Offer:

1. **Leave open** *(default)* — reviewers decide when to resolve.
2. **Resolve all** — mark every replied-to thread as resolved.
3. **Pick which to resolve** — show the list, user marks specific threads.

Persist:

```bash
scripts/walk.sh set --state "$STATE" --key resolve_choice --value "<leave|all|pick>"
# If pick: also write $SESSION_DIR/threads-to-resolve.json with the chosen subset.
```

## Outputs

- `resolve_choice` in walker state
- `$SESSION_DIR/threads-to-resolve.json` (when `pick`)

## Outgoing edges

- **`user_resolve`** → `resolve-threads`. User picked options 2 or 3.
- **`user_no_resolve`** → `persist`. User picked 1 (or default).

Record exactly one:

```bash
# Resolving:
scripts/walk.sh transition --state "$STATE" --from ask_resolve_threads --to resolve_threads --condition user_resolve

# Leaving open:
scripts/walk.sh transition --state "$STATE" --from ask_resolve_threads --to persist --condition user_no_resolve
```

## Notes

- **Leave-open is the default for a reason.** Resolving threads we just replied to looks presumptuous unless the reviewer explicitly delegated. Make the user opt in.
