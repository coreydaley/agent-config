---
name: sprint-work
description: Begin and complete the next incomplete sprint planned by sprint-plan
argument-hint: "[flags] [NNN]"
disable-model-invocation: true
---

# Task

Begin the next sprint.

## Arguments

`$ARGUMENTS` may begin with flags, followed by an optional sprint
number.

- `NNN` — run a specific local sprint (e.g. `005`)
- omitted — run the next available sprint from the ledger

## Flags

### Review

| Flag | Behavior |
|---|---|
| `--review` | Locate the sprint plan document, render it inline, and exit. No ledger changes, no implementation, no retro. |

Accepts an optional sprint number. If omitted, uses the same
lookup logic as a normal run (in-progress sprint first, otherwise
lowest-numbered planned sprint). `--review` also works on sprints
in any status (`planned`, `in_progress`, `completed`) so you can
re-read past plans as well.

When `--review` is passed:

1. Find the sprint document (by the given number, or by
   default-lookup if no number given).
2. Render its contents inline in your response.
3. Exit. No ledger mutations. No file writes.

If the sprint document cannot be located, report that clearly
and exit — do not fall back to running the sprint.

### Help

| Flag | Behavior |
|---|---|
| `--help` | Display usage summary and exit. |

When `--help` is passed, emit this text verbatim and exit without
doing any work:

```
/sprint-work — execute a sprint planned by /sprint-plan

Usage:
  /sprint-work [flags] [NNN]

Without flags or arguments, runs the next planned sprint from the
ledger. The session's current model (set via /model) determines
how the sprint is executed.

Arguments:
  NNN               Run a specific sprint number (e.g. 005).
                    Omit to run the next planned sprint.

Flags:
  --review          Print the sprint plan document and exit.
                    Does not run the sprint. Accepts optional NNN.
  --help            Show this help and exit.

Recommended workflow:
  1. Run /sprint-plan to produce a sprint plan.
  2. Read the sprint doc's "Recommended Execution" section.
     (Use /sprint-work --review [NNN] to re-read it later.)
  3. Set the session model: /model <name>
  4. Run: /sprint-work [NNN]

Full documentation: ~/.claude/skills/sprint-work/SKILL.md
```

### Precedence

- `--help` trumps everything else. Emit help and exit.
- `--review` trumps normal execution. Print the doc and exit —
  do not run any sprint work.
- Unknown flags are a configuration error — fail loudly; do not
  silently ignore.

## Workflow

If `--help` or `--review` was passed, handle it per the Flags
section and exit. Do not enter the workflow below.

1. **Find the next sprint to run**

   **If `$ARGUMENTS` contains a sprint number:**
   - Use `/sprints --list` to verify the sprint exists in the ledger.
   - If the sprint is not in the ledger: instruct the user to run
     `/sprints --add NNN "Title"`. Then stop.
   - Find the sprint document in `./docs/sprints/`:

     ```bash
     REPORT_DIR=./docs/sprints
     ls "$REPORT_DIR"/*-sprint-plan-SPRINT-NNN.md 2>/dev/null | tail -1
     ```

     If no file is found, inform the user and suggest re-running
     `/sprint-plan`.
   - If one sprint is already `in_progress` and a different
     explicit NNN was given, the explicit argument takes precedence
     — but surface a note identifying the in-progress sprint
     (number + title) before continuing.
   - Proceed to Step 2 with the specified sprint number.

   **Otherwise (no sprint number):**
   - Use `/sprints --stats` to see sprint status.
   - Check for an existing `in_progress` sprint using
     `/sprints --current`.
     - If one exists: surface its number and title, then ask the
       user whether to continue it or abort. Default: continue the
       existing in-progress sprint. Do not auto-continue without
       surfacing the sprint identity.
   - If no `in_progress` sprint: identify the lowest-numbered
     sprint with status `planned`.
     - If no planned sprints exist: inform the user that there are
       no planned sprints and suggest running `/sprint-plan` to
       create one. Then stop.
   - Find the sprint document in `./docs/sprints/`:

     ```bash
     REPORT_DIR=./docs/sprints
     ls "$REPORT_DIR"/*-sprint-plan-SPRINT-NNN.md 2>/dev/null | tail -1
     ```

     (Replace `NNN` with the zero-padded sprint number.)
     - If no matching file is found: inform the user and suggest
       re-running `/sprint-plan` to regenerate.
   - Read the located sprint document.

2. **Mark sprint in progress**
   - Identify the Claude model family running this session (`opus`,
     `sonnet`, or `haiku`) by inspecting your system context.
   - Invoke: `/sprints --start NNN --model=<that-family>` so the
     sprint record captures which model ran it. This data feeds
     future tier recommendations and velocity comparisons.

3. **Complete the sprint**
   - Work through ALL items in the Definition of Done.
   - Implement all required functionality per the sprint document.
   - To find build and test commands: check `README.md` for
     documented commands; check `Makefile` for available targets
     (e.g. `make all`, `make test`); fall back to the sprint
     document's own Definition of Done for validation steps.
   - Fix any build or test failures.
   - Ensure all validation passes per repo standards.

4. **Write the retrospective**

   Capture what this sprint actually taught us so the next
   `/sprint-plan` Orient phase can learn from it. Write to:

   ```bash
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   RETRO_FILE="$REPORT_DIR/$REPORT_TS-sprint-retro-SPRINT-NNN.md"
   ```

   Use this template:

   ```markdown
   # Sprint NNN Retrospective

   **Model used**: [opus / sonnet / haiku — name the model this
   session was running on]

   ## What was underestimated
   - Bullet the tasks or risks that took noticeably more effort
     than the plan anticipated. Name the specific file or
     subsystem where the surprise lived.

   ## What was deferred and why
   - Each P1/Deferred item that didn't ship, with the actual
     reason (out of scope vs. blocked vs. deprioritized vs.
     discovered unnecessary).

   ## What surprised me
   - Unexpected behavior, hidden dependencies, misread
     requirements, library quirks, infra constraints. Anything
     the plan didn't predict.

   ## What I'd do differently
   - Concrete adjustments — not generic wisdom. "Split the
     migration into two sprints" beats "estimate better."

   ## Model fit assessment
   - Was the model used appropriate for the actual work
     encountered? Over-powered, under-powered, or right-sized?
     This feeds the next Orient's tier recommendation.

   ## Lessons for next sprint
   - 1–3 bullets the next Orient phase should internalize. Keep
     it short — this is the high-signal line next time.
   ```

   Base the retro on what you actually observed during execution:
   which DoD items were trickier than expected, which tasks you
   had to clarify with the user, which files changed more than
   predicted, which tests required rework. Avoid generic
   platitudes.

   After writing the retro, also record the tier-fit verdict in
   the ledger so `/sprints --velocity` can aggregate it:

   ```bash
   /sprints --set-fit NNN <over_powered|right_sized|under_powered>
   ```

   Pick whichever verdict matches the retro's "Model fit
   assessment" section.

5. **Mark sprint completed**
   - Use the `/sprints --complete NNN` skill.

> Do not push changes. Do not ask to push.

## Reference

- Sprint documents: `./docs/sprints/*-sprint-plan-SPRINT-NNN.md`
- Retros: `./docs/sprints/*-sprint-retro-SPRINT-NNN.md`
- Ledger: `./docs/sprints/sprints.tsv`

Use `TaskCreate` and `TaskUpdate` to track progress through these
steps.
