---
description: Begin and complete the next incomplete sprint
---

# Task

Begin the next sprint. If `$ARGUMENTS` is a sprint number (e.g. `005`), run that sprint directly. Otherwise follow these steps:

1. **Find the next sprint to run**

   **If `$ARGUMENTS` is a sprint number:**
   - Use `/ledger list` to verify the sprint exists in the ledger.
   - If the sprint is not in the ledger: if the sprint doc exists on disk, instruct the user to run `/ledger sync`; if no doc exists, instruct the user to run `/ledger add NNN "Title"`. Then stop.
   - If one sprint is already `in_progress` and a different explicit NNN was given, the explicit argument takes precedence — but surface a note identifying the in-progress sprint (number + title) before continuing.
   - Proceed to Step 2 with the specified sprint number.

   **Otherwise (no argument):**
   - Use `/ledger stats` to see sprint status.
   - Check for an existing `in_progress` sprint using `/ledger current`.
     - If one exists: surface its number and title, then ask the user whether to continue it or abort. Default: continue the existing in-progress sprint. Do not auto-continue without surfacing the sprint identity.
   - If no `in_progress` sprint: identify the lowest-numbered sprint with status `planned`.
     - If no planned sprints exist: inform the user that there are no planned sprints and suggest running `/superplan` to create one. Then stop.
   - Read the sprint document: `docs/sprints/SPRINT-NNN.md`

   > If sprint docs and ledger entries appear out of sync, `/ledger sync` will reconcile them.

2. **Mark sprint in progress**
   - Use the `/ledger start NNN` skill

3. **Complete the sprint**
   - Work through ALL items in the Definition of Done
   - Implement all required functionality per the sprint document
   - To find build and test commands: check `README.md` for documented commands; check `Makefile` for available targets (e.g. `make all`, `make test`); fall back to the sprint document's own Definition of Done for validation steps
   - Fix any build or test failures
   - Ensure all validation passes per repo standards

4. **Mark sprint completed**
   - Use the `/ledger complete NNN` skill

> Do not commit, stage, or push any changes. Do not ask to commit or push.

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Ledger: `docs/sprints/ledger.tsv`

Use TaskCreate and TaskUpdate to track progress through these steps.
