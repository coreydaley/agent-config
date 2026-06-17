# Node: classify

User-input gate. Present the type menu **with a one-line description of each**, and
let the user pick exactly one. The choice sets the `type/*` label and parameterizes
`gather`'s template.

## Inputs

- `seed_idea`, `orient_summary` from walker state

```bash
STATE="$SESSION_DIR/.walk-state.json"
SEED_IDEA=$(scripts/walk.sh get --state "$STATE" --key seed_idea)
```

## Steps

Open with one short grounded line (restate the seed idea if present, in the context
of the project from `orient_summary`), then present the menu **verbatim with
descriptions** — the descriptions are the point; don't abbreviate them away:

```
What kind of issue is this?

  1. bug          — something is broken or behaves incorrectly.
  2. enhancement  — a new capability or improvement to existing behavior.
  3. performance  — a speed / memory / energy regression or improvement.
  4. security     — a vulnerability or hardening task.
  5. docs         — documentation only: README, wiki, help site, code comments.
  6. refactor     — internal restructuring with no user-visible behavior change.
  7. test         — missing or inadequate test coverage.
  8. chore        — maintenance: dependencies, tooling, build, CI, housekeeping.

(or cancel)
```

If the seed idea makes the type obvious, name your guess and let the user confirm
or correct — but still show the menu so the choice is theirs.

**If the item smells feature-sized** — multiple sub-deliverables, needs
decomposition, a spec rather than a single change — say so plainly and point at
`/feature-create`. The tracks are separate; don't try to capture a feature here.
The user may still insist on filing a single tracking issue; that's their call.

Persist the chosen type (lowercase, one of the eight):

```bash
scripts/walk.sh set --state "$STATE" --key issue_type --value "<bug|enhancement|performance|security|docs|refactor|test|chore>"
```

## Outgoing edges

- **`type_selected`** → `gather`. A type was chosen.
- **`user_cancel`** → `terminal`. Nothing created.

Record exactly one:

```bash
scripts/walk.sh transition --state "$STATE" --from classify --to gather   --condition type_selected
# or
scripts/walk.sh transition --state "$STATE" --from classify --to terminal --condition user_cancel
```

## Notes

- **The description is the feature.** The whole reason this node exists (vs. just
  asking "what type?") is to show what each type means, so the choice is informed.
- **One type only.** If it spans two (e.g. a bug whose fix is also a refactor),
  pick the dominant user-facing one; mention the secondary aspect in the body.
- **`security` biases priority later.** Just record the type here; `decide-priority`
  handles the severity nudge.
