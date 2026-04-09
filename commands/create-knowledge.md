---
description: Create a new knowledge note in the Obsidian vault under Knowledge/<topic>/
---

# Create Vault Knowledge Note

Create a new knowledge note in the Obsidian vault.

## Step 1: Gather details

Parse `$ARGUMENTS` for any details already provided (title, topic, type, status, source, tags, summary). Then check what is still missing.

If **title** or **topic** are missing, or if `$ARGUMENTS` is empty, ask for all needed details in a single message using this exact format:

> Please provide the following details for the new knowledge note:
>
> - **Title** (required) — becomes the note filename
> - **Topic** (required) — subfolder under `Knowledge/`, e.g. `ai`, `devtools`, `productivity`
> - **Type** (required) — `concept`, `reference`, `how-to`, `decision`, `tool`, or `person`
> - **Status** — `draft`, `review`, `stable`, or `archived` (default: `draft`)
> - **Source** — URL, book, person, etc. (optional)
> - **Summary** — one-liner description (optional)
> - **Tags** — comma-separated, e.g. `cli, tooling` (optional)

Wait for the user's response before proceeding.

## Step 2: Create the note

First attempt to create from the Knowledge template:

```bash
obsidian vault=Vault create path="Knowledge/<topic>/<title>.md" template="Knowledge"
```

If that fails (e.g. no template folder configured), fall back to inline frontmatter. Use today's date for `created`. Build the `content` string with all known values inline — do not run separate `property:set` commands when using this fallback:

```bash
obsidian vault=Vault create path="Knowledge/<topic>/<title>.md" content="---\ntype: <type>\nstatus: <status>\nsource: <source-or-empty>\ntags: [<tags-or-empty>]\ncreated: <today>\nsummary: <summary-or-empty>\n---\n"
```

If the template succeeded, set each property individually. Always set `type` and `status`; skip optional fields if not provided:

```bash
obsidian vault=Vault property:set name=type value=<type> path="Knowledge/<topic>/<title>.md"
obsidian vault=Vault property:set name=status value=<status> path="Knowledge/<topic>/<title>.md"
```

If source provided:
```bash
obsidian vault=Vault property:set name=source value="<source>" path="Knowledge/<topic>/<title>.md"
```

If summary provided:
```bash
obsidian vault=Vault property:set name=summary value="<summary>" path="Knowledge/<topic>/<title>.md"
```

If tags provided (comma-separated list):
```bash
obsidian vault=Vault property:set name=tags value="<tags>" type=list path="Knowledge/<topic>/<title>.md"
```

## Step 3: Confirm

Report the path of the created note and the properties that were set.
