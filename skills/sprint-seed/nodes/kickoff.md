# Node: kickoff

Open the discussion with a mode-specific message that grounds the conversation in real context from `orient`.

## Inputs

- `mode`, `arguments`, `direction_hint`, `repo_fallback`, `orient_summary` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
MODE=$(scripts/walk.sh get --state "$STATE" --key mode)
ARGS=$(scripts/walk.sh get --state "$STATE" --key arguments)
HINT=$(scripts/walk.sh get --state "$STATE" --key direction_hint)
FALLBACK=$(scripts/walk.sh get --state "$STATE" --key repo_fallback)
```

## Steps

Compose the kickoff message based on mode. Keep it tight — one paragraph plus optional candidates list. Single message, no preamble.

### Seed mode

> "Got it — you're thinking about [restate user's idea in your own words]. Before we go deeper, [one or two grounding questions informed by the orient]."

If `repo_fallback=true`, soften to:

> "Sounds like you want to talk through an idea. What's on your mind, and is there a particular direction or constraint we should start from?"

### Linear mode

> "Looking at this project: [brief synthesis from orient — goal, completion state]. Based on what's done and in flight, the natural next steps look like:
>
> 1. **[Candidate]** — [reasoning]
> 2. **[Candidate]** — [reasoning]
> 3. **[Candidate]** — [reasoning]
>
> Which feels right, or is there something else you had in mind?"

If `direction_hint` is present (user passed text after the URL), incorporate it: "Based on what you mentioned about [hint], the natural fit looks like..."

### Repo mode

> "Looking at recent sprints: [brief synthesis]. A few candidates for the next sprint:
>
> 1. **[Candidate]** — [reasoning, e.g. "deferred from the cache-warmup sprint"]
> 2. **[Candidate]** — [reasoning, e.g. "retro on the rate-limit sprint flagged this as recurring"]
> 3. **[Candidate]** — [reasoning, e.g. "natural sequel to last week's auth work"]
>
> Which would you like to explore? Or propose your own."

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
- **2-3 candidates max** in Linear / Repo modes. More than three is a menu, not a discussion starter.
