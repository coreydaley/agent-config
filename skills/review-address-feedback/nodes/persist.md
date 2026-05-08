# Node: persist

Write `ADDRESSED.md` — the only place internal finding IDs are written. Sole writer of the artifact.

## Inputs

- All run-scoped state and JSON sidecars in `$SESSION_DIR/`:
  - `addressed.json` (per-finding outcomes from `address`)
  - `replied-threads.json` (Phase 4 results, optional)
  - `resolved-threads.json` (Phase 4 results, optional)
- `pr_number`, `pr_head`, `mode`, `strategy`, `session_ts`, `session_dir` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
PR_NUMBER=$(scripts/walk.sh get --state "$STATE" --key pr_number)
PR_HEAD=$(scripts/walk.sh get --state "$STATE" --key pr_head)
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
STRATEGY=$(scripts/walk.sh get --state "$STATE" --key strategy)
SESSION_TS=$(scripts/walk.sh get --state "$STATE" --key session_ts)
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
```

## Steps

1. **Compute the diff stat:**
   ```bash
   git diff --stat > "$SESSION_DIR/diff.stat"
   ```

2. **Write `$SESSION_DIR/ADDRESSED.md`** to this template:

   ```markdown
   # Addressed: PR #<N> — <SESSION_TS>

   **Source**: <Mode A — live PR comments | Mode B — `<path to REVIEW.md>`>
   **Strategy**: <strategy>
   **Branch**: <PR_HEAD>

   ## Outcomes

   | ID | Severity | File:Line | Action | Note |
   |----|----------|-----------|--------|------|
   | ... | ... | ... | fixed / won't-fix / deferred / skipped | short note |

   ## Diff Summary

   ```
   <contents of diff.stat>
   ```

   ## GitHub Replies

   | Thread | Posted | Body |
   |--------|--------|------|
   | ... | yes/no | terse body |

   ## Resolved Threads

   | Thread | Resolved | Error |
   |--------|----------|-------|
   | ... | yes/no | (verbatim if any) |

   ## Deferred Work

   | ID | Where | Link |
   |----|-------|------|
   | ... | Linear / Obsidian / record-only | URL or path |
   ```

3. **Skip empty sections.** If no replies were posted, drop the GitHub Replies and Resolved Threads tables. If no deferrals, drop Deferred Work. The artifact should reflect what actually happened.

## ID Suppression — exception zone

This is the **only** file where internal review IDs (`R001`, `SR042`, `CR007`, `CX012`) appear. They never reach code, commits, or PR replies — that's a hard line elsewhere.

## Outputs

- `$SESSION_DIR/ADDRESSED.md`
- `$SESSION_DIR/diff.stat`

## Outgoing edges

- → `finalize` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from persist --to finalize
```

## Failure modes

- One of the JSON sidecars is missing (e.g., `replied-threads.json` because user picked `nothing` for replies) → just skip that section. The file's absence isn't an error.
- `git diff --stat` fails (somehow not in a git repo by this point) → leave the section empty with a note. Should never happen given `verify-worktree`.
