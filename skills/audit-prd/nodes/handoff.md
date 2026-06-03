# Node: handoff

**Verify already passed.** This audit is **read-only** — it never modifies the
PRD and never writes anything to the source (no wiki page, no file beside the
source). The review is the ephemeral local `REPORT.md` under `~/Reports`. This
node just extracts the verdict and prints the hand-off.

## Inputs

- Walker state: `audit_dir`, `verify_output`, `da_status`, `codex_status`,
  `source_kind`, `source_ref`, `prd_title`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
VERIFY_OUTPUT=$(scripts/walk.sh get --state "$STATE" --key verify_output)
SOURCE_REF=$(scripts/walk.sh get --state "$STATE" --key source_ref)
SOURCE_KIND=$(scripts/walk.sh get --state "$STATE" --key source_kind)
PRD_TITLE=$(scripts/walk.sh get --state "$STATE" --key prd_title)
```

## Step 1 — Extract verdict + counts from REPORT.md

Parse the `## Verdict:` line and the Summary table for the hand-off.

## Step 2 — Print the hand-off

The review is local and ephemeral; the next step is to **apply the agreed
changes to the actual PRD** (after discussing which findings to take and which
to leave). Nothing on the source has changed yet.

```
> ✅ PRD Audit complete — <Verdict>.
>
> **PRD:** <prd_title>   (<source_ref> — not modified)
> **Review:** <$AUDIT_DIR/REPORT.md>   (local, ephemeral)
>
> **Findings:** Blocker: X, Major: Y, Minor: Z, Nit: W.
> Top issue: <one-line description of the highest-severity finding>.
>
> **Verification:**
> <verify_output verbatim>
>
> **Next — apply it to the PRD?** I can take these findings straight into the
> PRD revise flow: we work them one at a time (apply / change / leave), and it
> edits the live PRD. The report is just the findings — the PRD content comes
> live from the wiki. Git-backed, so versioned/rollback-able.
>   • Wiki PRD →  /project-manage-prd --from-review <$AUDIT_DIR/REPORT.md>
>   • File PRD →  I'll edit <source_ref> directly, working from the report.
>
> Want me to start it now, or stop here with the review?
```

Pick the relevant "Next" line by `source_kind` (wiki vs file). **Offer it
explicitly** — don't just stop. The `--from-review` path is the *fresh* report
this run just produced (handed off immediately), so it's findings input, not a
stale disk artifact; `/project-manage-prd` still sources the PRD live from the
wiki.

If `CODEX_STATUS=failed`, add: `- **Degraded run**: Codex review unavailable;
single-agent audit. Consider re-running once codex is reachable.`

If `DA_STATUS=failed`, add: `- **Degraded run**: Devil's advocate pass did not
complete; synthesis was not stress-tested.`

## Step 3 — Mark complete

```bash
scripts/walk.sh set --state "$STATE" --key handoff_printed --value "yes"
scripts/walk.sh transition --state "$STATE" --from handoff --to terminal
```

## Outputs

- Hand-off message printed; walker state updated. **No writes to the source.**

## Failure modes

- REPORT.md unparseable for counts → fall back to "see REPORT.md" without
  numbers.
