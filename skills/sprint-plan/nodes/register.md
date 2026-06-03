# Node: register

Phase 9 Step 6: register the sprint as a Forgejo milestone so `/sprint-work` can find it. Compute the participants list, create the milestone (the canonical plan + tracking record, with the SPRINT doc as its description), then repeat the Recommended Execution block in the final message.

## Inputs

- `session_dir`, `report_ts`, `recommended_model`, `recommended_tier`, plus all phase-completion flags from walker state

```bash
STATE="<path>"
SESSION_DIR=$(scripts/walk.sh get --state "$STATE" --key session_dir)
REPORT_TS=$(scripts/walk.sh get --state "$STATE" --key report_ts)
RECOMMENDED_MODEL=$(scripts/walk.sh get --state "$STATE" --key recommended_model)
```

## Step 1: Extract title

Extract the sprint title from the first `# Title` heading in `$SESSION_DIR/SPRINT.md`. The session timestamp `$REPORT_TS` is the sprint's identifier; there's no separate sprint number.

## Step 2: Compute participants list

Who actually produced planning artifacts? Compute from which phases *ran*, not which were enabled. A phase that was enabled but produced no artifact (e.g., worker failed) does NOT count.

- Include `claude` if any Claude-side worker ran:
  - Phase 5a or 5b delegated to a Claude-side worker
  - Phase 6a or 6b delegated to a Claude-side worker
  - Any Phase 8 review routed to Claude (Security, Architecture, Observability, Breaking Change)
- Include `codex` if any Codex-side worker ran:
  - Phase 5a or 5b delegated to a Codex-side worker
  - Phase 6a or 6b delegated to a Codex-side worker
  - Any Phase 8 review routed to Codex (Devil's Advocate, Test Strategy, Performance & Scale)

The orchestrator itself does NOT count as a participant — only delegated workers that produced artifacts. Emit alphabetically.

Examples:

- Single-agent (only Claude-side workers ran): `claude`
- Both-sides: `claude,codex`

This list is what the `/commit` skill reads to build multi-agent `Co-authored-by:` trailers for the sprint-artifact commit.

## Step 3: Register the sprint as a Forgejo milestone

A sprint **is** a Forgejo milestone in its primary repo, and **the milestone's description is the SPRINT document itself** (the milestone page renders the full plan), plus a small `## Sprint metadata` footer carrying the fine status, models, fit, participants, and session. The local `SPRINT.md` is just the working copy. The sprint tracker (`~/.claude/lib/forgejo_sprints.py --add --doc-file`) creates the milestone (status `planned`, open) with the SPRINT doc as its description.

Resolve the primary repo from the `## Repositories` manifest in `$SESSION_DIR/SPRINT.md` (the entry tagged `(primary)`, else the first):

```bash
PRIMARY_REPO="<owner>/<repo>"   # from SPRINT.md's Repositories manifest

# PRD linkage: if this sprint came from a /sprint-seed SEED, that file carries a
# machine-readable `<!-- prd-advances: <section> -->` marker. Carry it onto the
# milestone so drift reporting can later compare shipped sprints against the PRD.
PRD_REF=""
if [ -f "$SESSION_DIR/SEED.md" ]; then
  PRD_REF=$(sed -n 's/.*<!-- prd-advances:[[:space:]]*\(.*[^[:space:]]\)[[:space:]]*-->.*/\1/p' "$SESSION_DIR/SEED.md" | head -1)
fi

if [ -n "$PRIMARY_REPO" ]; then
  python3 ~/.claude/lib/forgejo_sprints.py --add "$REPORT_TS" "$TITLE" --repo "$PRIMARY_REPO" \
    --doc-file "$SESSION_DIR/SPRINT.md" \
    --recommended-model="$RECOMMENDED_MODEL" \
    --participants="$PARTICIPANTS" \
    ${PRD_REF:+--prd-ref "$PRD_REF"}
  # The command prints the milestone URL — capture it for the final message.
fi
```

`$REPORT_TS` is the sprint identifier (the milestone's meta `Session`). `--doc-file` makes the milestone description the SPRINT doc. `--prd-ref` records which PRD section the sprint advances (only when the SEED supplied one — empty/absent for inline-prompt or audit-seeded plans, and for intentionally out-of-PRD work). `--add` is idempotent — if a milestone for this session already exists, it's a no-op.

**Nothing goes to the wiki** — the SPRINT doc lives in the milestone description, and the RETRO gets appended to that same milestone at close by `/sprint-work` (automatically when it closes the last issue, or via `--retro`). The SEED that fed this plan was an ephemeral local artifact; it isn't published anywhere.

**Repo-less sprints** (cross-cutting under `~/Reports/seeds/`, `~/Reports/forgejo/`, `~/Reports/no-repo/` — no repo in the manifest) have **no milestone home and are not tracked in Forgejo**; they stay local-only (`SPRINT.md` on disk). Skip this step; the tracker `--add` with no `--repo` just prints a "local-only" note.

## Step 4: Final message

Print:

```
Sprint registered:
  Session:       $REPORT_TS
  Title:         $TITLE
  SPRINT.md:     $SESSION_DIR/SPRINT.md  (working copy)
  Milestone:     $MILESTONE_URL          (canonical — the plan lives here; or "skipped: no repo")
  Participants:  $PARTICIPANTS
  Recommended:   $RECOMMENDED_MODEL ($RECOMMENDED_TIER tier)

To run the sprint:
    /model $RECOMMENDED_MODEL
    /sprint-work $REPORT_TS
```

**Always emit the explicit session timestamp** in the `/sprint-work` command, not the bare `/sprint-work`. The bare form falls back to the in-progress milestone, which may not be this one. The explicit timestamp resolves the right sprint directly. For repo-scoped sprints both usually work, but emitting the explicit form is consistently correct.

Repeat the **Recommended Execution** block fully so the exact `/model` and `/sprint-work` commands are the last thing the user sees.

## Outputs

- A Forgejo milestone for the sprint (status `planned`, open) whose **description is the SPRINT document** + a `## Sprint metadata` footer — the canonical plan + tracking record — when the sprint has a repo
- The local `SPRINT.md` working copy (already written by an earlier phase)
- Printed final message (with the milestone URL)

## Outgoing edges

- → `terminal` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from register --to terminal
```

## Notes

- **The orchestrator doesn't count** as a participant. Only delegated workers that produced artifacts. (The orchestrator's `Co-authored-by:` trailer comes from `/commit`'s default; it's not from the participants list.)
- **Don't run `git commit` / `git push`.** This skill doesn't touch git. Milestone creation goes through the Forgejo API (the tracker lib), not a local clone/push.
- **Create the milestone, not the issues.** This skill creates the sprint's milestone (the plan's home). Decomposing it into Forgejo **issues** is `/sprint-plan-to-issues`'s job, run separately if the user wants tracked issues.
