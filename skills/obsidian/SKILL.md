---
name: obsidian
description: Interact with the user's Obsidian vault using the `obsidian` CLI. Use when creating, reading, updating, or deleting vault notes (tasks, knowledge, drafts); querying bases; setting or reading note properties; searching the vault; managing tasks; or performing any vault operation. The vault lives at ~/Vault/ with subfolders Tasks/, Knowledge/, and Drafts/. Templates are in ~/Vault/Templates/.
---

# Obsidian CLI Skill

## Invocation

```bash
obsidian <command> [options]
```

The vault is named **Vault**. Always target it explicitly:

```bash
obsidian vault=Vault <command> [options]
```

## Syntax Rules

- Options use `key=value` form, not flags: `file=MyNote`, `path=Tasks/MyTask.md`
- Quote values with spaces: `name="My Note"`, `content="Hello world"`
- Use `\n` for newline, `\t` for tab in content values
- `file=` resolves by name (wikilink-style); `path=` is exact relative path from vault root
- Most commands default to the active file when `file`/`path` is omitted

## Vault Structure

| Path | Note type | Template |
|---|---|---|
| `Tasks/<project>/` | Task | `Templates/Task.md` |
| `Knowledge/<topic>/` | Knowledge | `Templates/Knowledge.md` |
| `Drafts/` | Draft | `Templates/Draft.md` |

## Common Operations

### Read a note
```bash
obsidian vault=Vault read path=Tasks/MyProject/Fix bug.md
```

### Create a note from template
```bash
obsidian vault=Vault create path=Tasks/MyProject/Fix bug.md template="Task"
```

After creating, set properties individually with `property:set`.

### Append content
```bash
obsidian vault=Vault append path=Tasks/MyProject/Fix bug.md content="New paragraph\n"
```

### Read a property
```bash
obsidian vault=Vault property:read name=status path=Tasks/MyProject/Fix bug.md
```

### Set a property
```bash
obsidian vault=Vault property:set name=status value=in-progress path=Tasks/MyProject/Fix bug.md
obsidian vault=Vault property:set name=due value=2026-04-15 type=date path=Tasks/MyProject/Fix bug.md
obsidian vault=Vault property:set name=tags value="ai, tools" type=list path=Tasks/MyProject/Fix bug.md
```

### Search the vault
```bash
obsidian vault=Vault search query="my search term" path=Tasks/
obsidian vault=Vault search:context query="my term" format=json
```

### Query a base
```bash
obsidian vault=Vault base:query path=Tasks.base view="Table" format=json
obsidian vault=Vault base:query path=Tasks.base view="Board" format=json
```

### List tasks (checkbox items)
```bash
obsidian vault=Vault tasks todo path=Tasks/
obsidian vault=Vault tasks done format=json
```

### Delete a note
```bash
obsidian vault=Vault delete path=Tasks/MyProject/Old note.md
```

## Note Property Schemas

### Task
| Property | Type | Valid values |
|---|---|---|
| `status` | text | `todo`, `in-progress`, `done`, `blocked` |
| `priority` | text | `low`, `medium`, `high`, `urgent` |
| `due` | date | ISO date (`2026-04-15`) |
| `project` | text | free text |
| `tags` | list | free text |
| `created` | date | ISO date |

### Knowledge
| Property | Type | Valid values |
|---|---|---|
| `type` | text | `concept`, `reference`, `how-to`, `decision`, `tool`, `person` |
| `status` | text | `draft`, `review`, `stable`, `archived` |
| `source` | text | URL, book, person, etc. |
| `tags` | list | free text |
| `created` | date | ISO date |
| `summary` | text | one-liner description |

### Draft
| Property | Type | Valid values |
|---|---|---|
| `type` | text | `idea`, `linkedin-post`, `blog-post`, `email`, `note` |
| `status` | text | `raw`, `in-progress`, `ready`, `published`, `abandoned` |
| `tags` | list | free text |
| `created` | date | ISO date |
| `summary` | text | one-liner description |

## Full Command Reference

See [references/commands.md](references/commands.md) for all available commands and options.
