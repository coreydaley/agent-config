# Node: kickoff

Open the discussion with a mode-specific message that grounds the conversation in real context from `orient`.

## Inputs

- `mode`, `arguments`, `repo_fallback`, `orient_summary`, `prd_summary` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
ARGS=$(scripts/walk.sh get --state "$STATE" --key arguments)
FALLBACK=$(scripts/walk.sh get --state "$STATE" --key repo_fallback)
PRD_SUMMARY=$(scripts/walk.sh get --state "$STATE" --key prd_summary)
```

## Steps

Compose the kickoff message based on mode. Keep it tight — one paragraph plus optional candidates list. Single message, no preamble.

**If a PRD was found** (`prd_summary` non-empty), ground the message in it: the strongest candidates are the PRD's next un-built phase or an open/neglected PRD area. Make the PRD linkage explicit in the reasoning ("PRD §3 (data pipeline) is the stated next phase and nothing's shipped against it yet"). In Seed mode, gently relate the user's idea to the PRD ("that fits PRD §2…" / "heads up — that's outside what the PRD currently scopes"). Don't lecture; one clause of PRD context per candidate is enough.

### Seed mode

> "Got it — you're thinking about [restate user's idea in your own words]. Before we go deeper, [one or two grounding questions informed by the orient]."

If `repo_fallback=true`, soften to:

> "Sounds like you want to talk through an idea. What's on your mind, and is there a particular direction or constraint we should start from?"

### Repo mode

> "Looking at recent sprints[ and the PRD]: [brief synthesis]. A few candidates for the next sprint:
>
> 1. **[Candidate]** — [reasoning, e.g. "PRD §3 (data pipeline) is the next un-built phase"]
> 2. **[Candidate]** — [reasoning, e.g. "deferred from the cache-warmup sprint"]
> 3. **[Candidate]** — [reasoning, e.g. "retro on the rate-limit sprint flagged this as recurring"]
>
> Which would you like to explore? Or propose your own."

When a PRD exists, lead with the PRD-derived candidate; sprint history and retros fill the rest.

## Tone

Senior engineering peer. Not sycophantic. Don't pad with affirmations or rhetorical scaffolding. The user wants substance.

## Outputs

- A single mode-specific opening message, printed to the user. No file changes, no state updates.

## Outgoing edges

- → `discuss` (always — single outgoing edge)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from kickoff --to discuss
```

## Notes

- **One message, then wait.** The user replies, and we move into `discuss`. Don't keep talking after the kickoff prompt.
- **2-3 candidates max** in Repo mode. More than three is a menu, not a discussion starter.
