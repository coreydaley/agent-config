---
description: Begin and complete the next incomplete sprint
---

## Task

Begin the next sprint. If `$ARGUMENTS` is a sprint number (e.g. `005`), run that sprint directly. Otherwise follow these steps:

1. **Find the next sprint to run**
   - Use the `/ledger stats` skill to see sprint status
   - Identify the lowest-numbered sprint with status `planned`
   - Read that sprint document: `docs/sprints/SPRINT-NNN.md`

2. **Mark sprint in progress**
   - Use the `/ledger start NNN` skill

3. **Complete the sprint**
   - Work through ALL items in the Definition of Done
   - Implement all required functionality per the sprint document
   - Run the project's build and test commands to validate
   - Fix any build or test failures
   - Ensure all validation passes per repo standards

4. **Mark sprint completed**
   - Use the `/ledger complete NNN` skill

> Do not commit, stage, or push any changes. Do not ask to commit or push.

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Ledger: `docs/sprints/ledger.tsv`

Use TaskCreate and TaskUpdate to track progress through these steps.
