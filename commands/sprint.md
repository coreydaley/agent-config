---
description: Begin and complete the next incomplete sprint
---

## Task

Begin the next sprint. Follow these steps:

1. **Find the next incomplete sprint**
   - Run `python3 docs/sprints/ledger.py stats` to see sprint status
   - Identify the lowest-numbered sprint that is NOT completed
   - Read that sprint document: `docs/sprints/SPRINT-NNN.md`

2. **Mark sprint in progress**
   - Run `python3 docs/sprints/ledger.py start NNN`

3. **Complete the sprint**
   - Work through ALL items in the Definition of Done
   - Implement all required functionality per the sprint document
   - Run the project's build and test commands to validate
   - Fix any build or test failures
   - Ensure all validation passes per repo standards

4. **Mark sprint completed**
   - Run `python3 docs/sprints/ledger.py complete NNN`

> Do not commit, stage, or push any changes. Do not ask to commit or push.

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Ledger: `docs/sprints/ledger.tsv`

Use the TodoWrite tool to track progress through these steps.
