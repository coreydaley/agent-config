# Node: persist

Write the run's record. `ADDRESSED.md` is the one file where internal finding IDs live. PLAN.md gets a Log line (Follow-ups were appended during apply).

## Inputs

- `fix_dir`, `plan_dir`, `plan_available`, `outcomes_path`, `push_result`, `pr_number`, `branch`, `mode`, `regime` from walker state
- `$FIX_DIR/addressed.json`, `replied.json` (optional), `TRIAGE.md`

```bash
STATE="$PLAN_DIR/.walk-state.fix.json"
FIX_DIR=$(scripts/walk.sh get --state "$STATE" --key fix_dir)
```

## Steps

1. **`$FIX_DIR/ADDRESSED.md`:**
   ```markdown
   # Addressed: PR #<N> (<branch>) — <TS>

   Source: <REVIEW.md path | PR #N human threads>
   Regime: <squash | append>    Push: <squashed | pushed | local | rejected | nothing>

   | ID | Sev | Class | File:Line | Action | Commit | Note |
   |---|---|---|---|---|---|---|

   ## Replies
   | Thread | Posted | Error |
   (omit when none)

   ## Diff
   <git diff --stat $BASE_REF...HEAD>
   ```
   Empty sections are dropped, not left as headings.

2. **PLAN.md Log**, one line:
   ```
   <date> pr-fix: <source>, <f> fixed, <d> deferred, <w> won't-fix<, b blocked><, s stale>, <push_result>
   ```

   If a run stopped at `ask-triage` (`user_stop`), the line is `<date> pr-fix: triage proposed, not applied (<path to TRIAGE.md>)` and there's no ADDRESSED.md.

3. **No PLAN.md** (`plan_available=false`): write `ADDRESSED.md` only. Say in finalize that deferrals have nowhere durable to live and list them.

## Outputs

- `$FIX_DIR/ADDRESSED.md`
- PLAN.md Log appended

## Outgoing edges

- → `finalize` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from persist --to finalize
```

## Notes

- **Internal IDs stop here.** SR/H/PA identifiers appear in TRIAGE.md and ADDRESSED.md. Not in code, commits, replies, PLAN.md Follow-ups, or the finalize summary.
