# Node: show-diff

Render the proposals inline so the user can read the full picture before answering Prompt 1.

## Inputs

- `proposals_path`, `has_cleanup`, `cleanup_skip_reason` from walker state

```bash
STATE="<path>"
PROPOSALS=$(scripts/walk.sh get --state "$STATE" --key proposals_path)
HAS_CLEANUP=$(scripts/walk.sh get --state "$STATE" --key has_cleanup)
CLEANUP_SKIP_REASON=$(scripts/walk.sh get --state "$STATE" --key cleanup_skip_reason)
```

## Steps

For each PR, render inline:

```
PR: <owner>/<repo>#<N> — <current title>

Title:
  Current:  <current title>
  Proposed: <new title>      [no change / change reason]

Body:
  <unified diff between current body and proposed body, or
   "no changes needed" if body is fine>

Cross-links (multi-repo only):
  ✓ <- PR-B URL matches expected companion
  ✗ <- PR-B URL is stale / missing — will be fixed in body rewrite

Threads to resolve (likely resolved by code):
  - <thread.path:line> "<first 60 chars of comment>..."
    addressed by: <commit SHA> "<commit summary>"

Ambiguous threads (need your call):
  - <thread.path:line> "<comment summary>"
    code touched in <commit SHA>, but concern may still apply

Commit cleanup (optional — REQUIRES force-push):
  Internal refs found:
    - <SHA> "<title>" — strips: SR001, SR003, ~/Reports/...
    - <SHA> "<title>" — strips: "per the synthesis pass"
  Verbose bodies to tighten:
    - <SHA> "<title>" — current: <N> lines → proposed: 1 line
  Proposed regrouping (<orig N> commits → <new M> groups):
    1. fix(api/handler): guard ResultLimit overflow
       files: pkg/api/handler.go
              pkg/api/handler_test.go
       trailers: Addresses CON-1148
                 Co-authored-by: Claude <noreply@anthropic.com>
    2. docs(api/handler): clarify ListItems auto-iterate semantics
       files: pkg/api/handler.go
       trailers: Co-authored-by: Claude <noreply@anthropic.com>
  (or "Skipped: <reason>" — see cleanup_skip_reason)

Code comment cleanup:
  Strip (contain internal refs):
    - pkg/api/handler.go:153
      current:  "// addresses SR001 — guard against int32 overflow"
      proposed: "// guard against int32 overflow"
  Shorten (verbose):
    - pkg/api/handler.go:79-82 (4-line block)
      proposed: 1 line
  Strip entirely (restates code):
    - foo/bar.go:42 "// increment counter"  → DELETE
```

Skip sections that don't apply (e.g., "Cross-links" if not multi-repo; "Ambiguous threads" if none).

When `cleanup_skip_reason` is set, render the cleanup section as:

```
Commit cleanup: SKIPPED — <reason>
```

## Outputs

- All proposals rendered inline. No file or state changes.

## Outgoing edges

- → `ask-title-body` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from show_diff --to ask_title_body
```

## Notes

- **Render the full picture** so the user can answer both Prompt 1 (title/body/threads) and Prompt 2 (cleanup) with full context. Even though the gates are sequential, showing everything up front avoids "wait, what was the cleanup proposal again?" later.
- **Don't ask anything yet.** The user-input gate is `ask-title-body`.
