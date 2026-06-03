# Node: kickoff

Open the session with a mode-specific message that frames the work and asks the
first real question. One message, then wait.

## Inputs

- `prd_mode`, `org_repo`, `orient_summary`, `existing_summary`, `findings_path` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
PRD_MODE=$(scripts/walk.sh get --state "$STATE" --key prd_mode)
FINDINGS_PATH=$(scripts/walk.sh get --state "$STATE" --key findings_path)
```

## Steps

Compose a tight opening. No preamble, no "Great! Let's get started."

### Create mode

> "Let's build the PRD for **<org/repo>**. I'll walk you through it one piece at
> a time and push where the thinking's thin — the goal is a doc that's actually
> useful to plan against, not a checklist.
>
> Start at the top: **what problem does this project solve, and for whom?** One
> or two sentences on the pain and the people who feel it."

### Revise mode

> "There's already a PRD for **<org/repo>**. Here's its current shape:
> [2-3 line synthesis from `existing_summary` — sections + stated goals/phases].
>
> What do you want to change — extend a section, add a phase, re-scope, fix
> something that's drifted? Tell me where to start and we'll work through it."

**If `findings_path` is set** (e.g. a fresh `audit-prd` review handed off), read
that file and open against it instead — list the findings as a short agenda and
work them one at a time, deciding apply-vs-leave together:

> "I've got the audit findings for the **<org/repo>** PRD. Quick agenda — N to
> work through:
>   1. [Blocker] <finding> — suggested: <revision>
>   2. [Major]   <finding> — …
> Let's take them one at a time: for each, you decide apply / change / leave
> as-is, and I edit the live PRD accordingly. Start with #1?"

The findings doc is **discussion input only** — the PRD content being edited is
the live wiki copy `orient` fetched, never the findings file or the audit's
snapshot.

## The PRD sections we're walking toward

Hold this as the target structure (you don't recite it — you elicit it). Cover,
roughly in order, pulling each out of the user:

1. **Problem & Goal** — the pain, and what "solved" looks like.
2. **Target Users** — who it's for; primary vs secondary.
3. **Goals & Non-Goals** — explicit in-scope *and* out-of-scope. Non-goals are
   as load-bearing as goals — they prevent drift.
4. **Requirements / Core Features** — what it must do (capabilities, not tasks).
5. **Success Metrics** — how you'll know it's working (qualitative is fine if no
   numbers exist — don't fabricate metrics).
6. **Phases / Roadmap** — the sequence of meaningful chunks (MVP → v1 → …). This
   is load-bearing: `/sprint-seed` grounds its next-sprint candidates in these
   phases, so make them concrete and ordered.
7. **Constraints & Risks** — technical, organizational, deadlines, dependencies.
8. **Open Questions** — what's genuinely undecided.

## Tone

Senior product-minded peer. Not sycophantic. One question at a time.

## Outputs

- A single opening message printed to the user. No file/state changes.

## Outgoing edges

- → `discuss` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from kickoff --to discuss
```

## Notes

- **One message, then wait.** The user replies and we move into `discuss`.
- **Don't draft the whole PRD here.** Kickoff opens the conversation; `draft`
  assembles the document.
