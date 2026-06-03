# Node: check-milestone

Decision (automatic). After the work summary, decide whether this run
just **completed the sprint's milestone**. A milestone is complete when
it has **zero open issues left** — whether the last ones were *closed*
(their `Closes #N` commits landed) or *moved out* of the milestone. When
complete, fall straight into the retrospective (`write-retro`) so closing
out a sprint needs no separate `/sprint-work --retro` run. Otherwise stop
— more work remains for a later run.

This is the autonomous closeout. It never prompts.

## Inputs

- `path_mode`, `milestone_repo`, `milestone_name`, `session_dir` from
  walker state. `summarize` already computed and persisted the open count
  — prefer that; only re-query if it's missing.

```bash
STATE="<path>"
PATH_MODE=$(scripts/walk.sh get --state "$STATE" --key path_mode)
MILESTONE_REPO=$(scripts/walk.sh get --state "$STATE" --key milestone_repo)
MILESTONE_NAME=$(scripts/walk.sh get --state "$STATE" --key milestone_name)
OPEN_LEFT=$(scripts/walk.sh get --state "$STATE" --key milestone_open_count)
TOKEN=$(awk '/name: homelab/{f=1} f&&/token:/{print $2; exit}' "$HOME/Library/Application Support/tea/config.yml")
```

## Steps

### 1. Is there a milestone to complete?

Auto-retro is milestone-scoped. Resolve the milestone this run was
working in:

- **`forgejo-walk`** — `milestone_repo` + `milestone_name` are already
  set (the target was a milestone). Use them.
- **`forgejo-issue`** (single issue) — `milestone_name` is usually empty.
  Derive it from the issue itself, so closing a milestone's **last**
  issue still triggers the retro even when you targeted just that issue:
  ```bash
  if [ -z "$MILESTONE_NAME" ] && [ "$PATH_MODE" = "forgejo-issue" ]; then
    REF=$(scripts/walk.sh get --state "$STATE" --key issue_ids | jq -r '.[0]')  # owner/repo#n
    OWNER_REPO=${REF%#*}; N=${REF#*#}
    MS=$(curl -sk -H "Authorization: token $TOKEN" \
      "https://mac-mini.example:3000/api/v1/repos/$OWNER_REPO/issues/$N" \
      | jq -r '.milestone.title // empty')
    if [ -n "$MS" ]; then MILESTONE_NAME="$MS"; MILESTONE_REPO="$OWNER_REPO"; fi
  fi
  ```
  If the issue has no milestone, there's nothing to complete →
  `milestone_incomplete`.
- **`sprintmd` path** (repo-less / untracked local `SPRINT.md`) → **no
  milestone**. Route `milestone_incomplete`. (The user can still run
  `/sprint-work --retro` manually.)

### 2. Count the milestone's open issues

Use the count `summarize` persisted (`milestone_open_count`). If it's
empty/unset — or you just derived the milestone in step 1 (the
single-issue case, where `summarize` saw no milestone) — query it
directly. Count open issues **still attached** to the milestone:

```bash
if [ -z "$OPEN_LEFT" ] && [ -n "$MILESTONE_NAME" ]; then
  OPEN_LEFT=$(tea issues list --repo "$MILESTONE_REPO" \
    --milestones "$MILESTONE_NAME" --state open --output json | jq 'length')
fi
```

`--state open` already excludes closed issues; issues *moved out* of the
milestone are no longer attached, so they don't count either. Both of the
user's "terminal state" cases collapse to **`OPEN_LEFT == 0`**.

### 3. Route

- **`OPEN_LEFT == 0`** → the milestone is done. Print one line and route
  `milestone_complete`:
  ```
  Milestone "<name>" has no open issues left — writing the retrospective
  and closing the sprint.
  ```
- **`OPEN_LEFT > 0`** → route `milestone_incomplete`:
  ```
  Milestone "<name>": <OPEN_LEFT> issue(s) still open — run /sprint-work
  again to continue, or /sprint-work --retro to close out early.
  ```

A query failure (network/auth) is **non-fatal**: log it and route
`milestone_incomplete` (don't auto-close on uncertain state — a missed
auto-retro is recoverable with `--retro`; a wrong one closes the
milestone prematurely).

## Outgoing edges

- **`milestone_complete`** → `write-retro`. The run closed the last open
  issue; auto-write the retro, append it to the milestone, and close it.
- **`milestone_incomplete`** → `terminal`. Work remains, this isn't a
  milestone run, or the count couldn't be determined.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from check_milestone --to write_retro --condition milestone_complete
# or
scripts/walk.sh transition --state "$STATE" --from check_milestone --to terminal --condition milestone_incomplete
```

## Notes

- **Automatic — never prompt.** This is the autonomous closeout; the run
  decides and acts.
- **Open count is the single signal.** Closed *or* moved-out both reduce
  the open-attached count; don't special-case them separately.
- **`write-retro` reuses the `--retro` machinery.** It tolerates the
  absence of `verify-merged`'s `unshipped_warnings` (there are none — the
  milestone is empty of open work) and writes one retro per milestone.
- **Don't double-fire.** The explicit `--retro` flag takes its own
  subgraph (`dispatch-mode → verify-merged → write-retro`) and never
  reaches `check-milestone`, so there's no risk of two retros in one run.
