# Node: synthesize

Produce a refined seed prompt (2-3 paragraphs, tight, action-oriented) capturing what the discussion uncovered. In-memory only. `write-seed` is the sole writer.

## Inputs

- Discussion context (in-conversation memory)
- Walker state (mode, arguments, project_url, direction_hint) for source attribution

## What goes in the seed

- **Core goal / outcome** — what done looks like
- **Scope** — what's in, what's out
- **Key constraints** discovered in discussion (technical, organizational, deadlines)
- **Approach direction** if decided (or explicitly "left open for `/sprint-plan` to evaluate")
- **Open questions** for `/sprint-plan`'s Phase 4 interview to surface
- **Critical context** — dependencies, related sprints, past decisions

## What does NOT go in the seed

- **No tasks.** That's `/sprint-plan`'s output.
- **No file lists.** Same.
- **No DoD enumeration.** Same.
- **No invented details.** If something didn't come up in the discussion, leave it out — don't make it up to round out the seed.

If you find yourself drafting steps or files, you've drifted out of the seed and into the plan. Pull back.

## Format

2-3 paragraphs of tight prose. Action-oriented. No bullets in the seed itself (bullets belong in `/sprint-plan` SPRINT.md). The "Context discussed" section in `write-seed` can use bullets for the audit trail.

## Outputs

Hold the synthesized seed in working memory. `write-seed` reads it.

If useful for resume safety, persist:
```bash
scripts/walk.sh set --state "$STATE" --key seed_text --value "<the 2-3 paragraphs>"
```

## Outgoing edges

- → `write-seed` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from synthesize --to write_seed
```

## Notes

- **Tight beats comprehensive.** A short, sharp seed is easier for `/sprint-plan` to work with than a long one that re-litigates the discussion.
- **Don't quote the user back at themselves.** Synthesize, don't transcribe.
