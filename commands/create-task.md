---
description: Create a new task note in the Obsidian vault under Tasks/<project>/
---

# Create Vault Task

Create a new task note in the Obsidian vault.

## Step 1: Gather details

Parse `$ARGUMENTS` for any details already provided (title, project, priority, due date, url, tags). Then check what is still missing.

If **title** or **project** are missing, or if `$ARGUMENTS` is empty, ask for all needed details in a single message using this exact format:

> Please provide the following details for the new task:
>
> - **Title** (required) — becomes the note filename
> - **Project** (required) — subfolder under `Tasks/`, e.g. `agent-config`, `sandbox`
> - **Priority** — `low`, `medium`, `high`, or `urgent` (default: `medium`)
> - **Due date** — ISO date, e.g. `2026-04-15` (optional)
> - **URL** — link associated with this task (optional)
> - **Tags** — comma-separated, e.g. `cli, tooling` (optional)

Wait for the user's response before proceeding.

## Step 2: Create the note

First attempt to create from the Task template:

```bash
obsidian vault=Vault create path="Tasks/<project>/<title>.md" template="Task"
```

If that fails (e.g. no template folder configured), fall back to inline frontmatter. Use today's date for `created`. If a URL was provided, include `[LINK](<url>)` as the note body; otherwise leave the body empty. Build the full content string and create in one command — do not run separate `property:set` commands when using this fallback:

```bash
# With URL:
obsidian vault=Vault create path="Tasks/<project>/<title>.md" content="---\nstatus: todo\npriority: <priority>\ndue: <due-or-empty>\nproject: <project>\ntags: [<tags-or-empty>]\ncreated: <today>\nsummary: \nurl: <url>\n---\n\n[LINK](<url>)"

# Without URL:
obsidian vault=Vault create path="Tasks/<project>/<title>.md" content="---\nstatus: todo\npriority: <priority>\ndue: <due-or-empty>\nproject: <project>\ntags: [<tags-or-empty>]\ncreated: <today>\nsummary: \nurl: \n---\n"
```

If the template succeeded, set each property individually. Always set `status` and `priority`; skip optional fields if not provided:

```bash
obsidian vault=Vault property:set name=status value=todo path="Tasks/<project>/<title>.md"
obsidian vault=Vault property:set name=priority value=<priority> path="Tasks/<project>/<title>.md"
obsidian vault=Vault property:set name=project value="<project>" path="Tasks/<project>/<title>.md"
```

If due date provided:
```bash
obsidian vault=Vault property:set name=due value=<due> type=date path="Tasks/<project>/<title>.md"
```

If URL provided:
```bash
obsidian vault=Vault property:set name=url value="<url>" path="Tasks/<project>/<title>.md"
```

Then append the clickable link to the note body:
```bash
obsidian vault=Vault append path="Tasks/<project>/<title>.md" content="[LINK](<url>)"
```

If tags provided (comma-separated list):
```bash
obsidian vault=Vault property:set name=tags value="<tags>" type=list path="Tasks/<project>/<title>.md"
```

## Step 3: Confirm

Report the path of the created note and the properties that were set.
