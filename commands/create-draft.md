---
description: Create a new draft note in the Obsidian vault under Drafts/
---

# Create Vault Draft

Create a new draft note in the Obsidian vault.

## Step 1: Gather details

Parse `$ARGUMENTS` for any details already provided (title, type, tags, summary). Then check what is still missing.

If **title** or **type** are missing, or if `$ARGUMENTS` is empty, ask for all needed details in a single message using this exact format:

> Please provide the following details for the new draft:
>
> - **Title** (required) — becomes the note filename
> - **Type** (required) — `idea`, `linkedin-post`, `blog-post`, `email`, or `note`
> - **Summary** — one-liner description (optional)
> - **Tags** — comma-separated, e.g. `ai, career` (optional)

Wait for the user's response before proceeding.

## Step 2: Create the note

First attempt to create from the Draft template:

```bash
obsidian vault=Vault create path="Drafts/<title>.md" template="Draft"
```

If that fails (e.g. no template folder configured), fall back to inline frontmatter. Use today's date for `created`. Build the `content` string with all known values inline — do not run separate `property:set` commands when using this fallback:

```bash
obsidian vault=Vault create path="Drafts/<title>.md" content="---\ntype: <type>\nstatus: raw\ntags: [<tags-or-empty>]\ncreated: <today>\nsummary: <summary-or-empty>\n---\n"
```

If the template succeeded, set each property individually. Always set `type` and `status`; skip optional fields if not provided:

```bash
obsidian vault=Vault property:set name=type value=<type> path="Drafts/<title>.md"
obsidian vault=Vault property:set name=status value=raw path="Drafts/<title>.md"
```

If summary provided:
```bash
obsidian vault=Vault property:set name=summary value="<summary>" path="Drafts/<title>.md"
```

If tags provided (comma-separated list):
```bash
obsidian vault=Vault property:set name=tags value="<tags>" type=list path="Drafts/<title>.md"
```

## Step 3: Confirm

Report the path of the created note and the properties that were set.
