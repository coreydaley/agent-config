---
description: Begin and complete the next incomplete sprint
---

# Task

Begin the next sprint.

## Arguments

`$ARGUMENTS` may be one of these forms:

- `NNN` to run a specific local sprint number such as `005`
- `TOOL_NAME` to pull the next sprint from an external tool
  such as `linear` or `jira`
- `TOOL_NAME NNN` only if that tool flow supports explicit
  sprint selection

If the first argument is a recognized tool name, prefer the
external tool workflow below. Otherwise, use the local
ledger-based workflow.

If a tool name is provided but the corresponding tool or
MCP integration is not available in the current environment,
stop and explain the missing dependency clearly.

## Local Workflow

If `$ARGUMENTS` is a sprint number (e.g. `005`), run that sprint directly. Otherwise follow these steps:

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
     - If no planned sprints exist: inform the user that there are no planned sprints and suggest running `/sprint-plan` to create one. Then stop.
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

## Tool-Backed Workflow

If `$ARGUMENTS` begins with a supported tool name such as
`linear` or `jira`, use this flow instead of the local
ledger flow:

1. **Connect to the tool**
   - Verify the corresponding tool integration is available
   - If it is not available, stop and tell the user exactly
     what is missing

2. **Find the sprint to run from the tool**
   - If an explicit sprint identifier was also provided and
     the tool supports it, load that sprint
   - Otherwise, locate the next sprint that is ready to be
     executed in that tool
   - Prefer the active/in-progress sprint if one already
     exists; otherwise choose the next planned sprint in the
     tool's ordering
   - Surface the sprint identity to the user before work
     begins

3. **Load execution context**
   - Read the sprint, stories, and tasks from the tool
   - If there is a matching local sprint document on disk,
     use it as additional execution context
   - If the tool and local document disagree materially,
     call out the mismatch and use the tool as the source of
     truth for execution when the user explicitly invoked the
     tool-backed flow

4. **Mark sprint in progress in the tool**
   - Update the sprint or iteration status in the external
     tool if needed
   - Update story/task status as work starts when the tool's
     workflow requires it

5. **Complete the sprint**
   - Work through all required stories and tasks from the
     tool-backed sprint
   - Implement all required functionality
   - Use the sprint's acceptance criteria, task breakdown,
     and Definition of Done as the execution contract
   - To find build and test commands: check `README.md` for
     documented commands; check `Makefile` for available
     targets; fall back to the sprint's own validation steps
   - Fix build or test failures
   - Ensure validation passes per repo standards

6. **Update the tool as work progresses**
   - Mark stories and tasks complete as they are finished
   - Preserve any status, assignee, dependency, or comment
     conventions that matter for the chosen tool

7. **Mark sprint completed in the tool**
   - Close or complete the sprint in the external tool when
     the sprint's required work is done
   - If the repo has a matching local sprint doc and a
     ledger entry, also run `/ledger complete NNN` to keep
     the local ledger in sync

> Do not push changes. Do not ask to push.

## Reference

- Sprint conventions: `docs/sprints/README.md`
- Ledger: `docs/sprints/ledger.tsv`

Use TaskCreate and TaskUpdate to track progress through these steps.
