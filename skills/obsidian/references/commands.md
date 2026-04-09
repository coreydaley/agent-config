# Obsidian CLI — Full Command Reference

## Table of Contents
1. [File Operations](#file-operations)
2. [Content Operations](#content-operations)
3. [Properties](#properties)
4. [Search](#search)
5. [Tasks](#tasks)
6. [Bases](#bases)
7. [Tags & Links](#tags--links)
8. [Daily Notes](#daily-notes)
9. [Navigation & UI](#navigation--ui)
10. [Sync & History](#sync--history)
11. [Vault Info](#vault-info)
12. [Plugins & Themes](#plugins--themes)

---

## File Operations

| Command | Key options | Notes |
|---|---|---|
| `create` | `name=`, `path=`, `content=`, `template=`, `overwrite`, `open`, `newtab` | Use `template=` with template name (no path) |
| `read` | `file=`, `path=` | Returns full file contents |
| `delete` | `file=`, `path=`, `permanent` | Sends to trash by default |
| `move` | `file=`/`path=`, `to=<dest path>` | Moves or renames |
| `rename` | `file=`/`path=`, `name=<new name>` | Rename in place |
| `open` | `file=`, `path=`, `newtab` | Opens in Obsidian UI |
| `file` | `file=`, `path=` | Show file metadata |
| `files` | `folder=`, `ext=`, `total` | List files; filter by folder or extension |

## Content Operations

| Command | Key options | Notes |
|---|---|---|
| `append` | `file=`/`path=`, `content=` (required), `inline` | `inline` skips leading newline |
| `prepend` | `file=`/`path=`, `content=` (required), `inline` | |
| `outline` | `file=`/`path=`, `format=tree\|md\|json`, `total` | Headings hierarchy |
| `wordcount` | `file=`/`path=`, `words`, `characters` | |

## Properties

| Command | Key options | Notes |
|---|---|---|
| `property:read` | `name=` (required), `file=`/`path=` | Get a single property value |
| `property:set` | `name=` (required), `value=` (required), `type=`, `file=`/`path=` | Types: `text`, `list`, `number`, `checkbox`, `date`, `datetime` |
| `property:remove` | `name=` (required), `file=`/`path=` | |
| `properties` | `file=`/`path=`, `name=`, `total`, `sort=count`, `counts`, `format=yaml\|json\|tsv`, `active` | List all properties in vault or file |

## Search

| Command | Key options | Notes |
|---|---|---|
| `search` | `query=` (required), `path=`, `limit=`, `total`, `case`, `format=text\|json` | Full-text search |
| `search:context` | `query=` (required), `path=`, `limit=`, `case`, `format=text\|json` | Returns matching lines with context |
| `search:open` | `query=` | Opens search in Obsidian UI |

## Tasks

| Command | Key options | Notes |
|---|---|---|
| `tasks` | `file=`/`path=`, `total`, `done`, `todo`, `status="<char>"`, `verbose`, `format=json\|tsv\|csv\|text`, `active`, `daily` | Lists checkbox tasks |
| `task` | `ref=<path:line>`, `file=`/`path=`, `line=`, `toggle`, `done`, `todo`, `daily`, `status="<char>"` | Show or update a single task |

## Bases

| Command | Key options | Notes |
|---|---|---|
| `base:query` | `file=`/`path=`, `view=`, `format=json\|csv\|tsv\|md\|paths` | Query an Obsidian Base view |
| `base:create` | `file=`/`path=`, `view=`, `name=`, `content=`, `open`, `newtab` | Create a new item via a base |
| `base:views` | — | List views in the current base file |
| `bases` | — | List all base files in vault |

## Tags & Links

| Command | Key options | Notes |
|---|---|---|
| `tags` | `file=`/`path=`, `total`, `counts`, `sort=count`, `format=json\|tsv\|csv`, `active` | List tags |
| `tag` | `name=` (required), `total`, `verbose` | Get tag info and usage |
| `links` | `file=`/`path=`, `total` | Outgoing links from a file |
| `backlinks` | `file=`/`path=`, `counts`, `total`, `format=json\|tsv\|csv` | Incoming links |
| `aliases` | `file=`/`path=`, `total`, `verbose` | List aliases |
| `unresolved` | `total`, `counts`, `verbose`, `format=json\|tsv\|csv` | Broken links |
| `orphans` | `total`, `all` | Files with no incoming links |
| `deadends` | `total`, `all` | Files with no outgoing links |

## Daily Notes

| Command | Key options | Notes |
|---|---|---|
| `daily` | `paneType=tab\|split\|window` | Open today's daily note |
| `daily:read` | — | Read today's daily note contents |
| `daily:append` | `content=` (required), `inline`, `open`, `paneType=` | |
| `daily:prepend` | `content=` (required), `inline`, `open`, `paneType=` | |
| `daily:path` | — | Get the path of today's daily note |

## Navigation & UI

| Command | Key options | Notes |
|---|---|---|
| `command` | `id=` (required) | Execute any Obsidian command by ID |
| `commands` | `filter=<prefix>` | List available commands |
| `hotkey` | `id=` (required), `verbose` | Get hotkey for a command |
| `hotkeys` | `total`, `verbose`, `format=`, `all` | List hotkeys |
| `tabs` | `ids` | List open tabs |
| `tab:open` | `group=`, `file=`, `view=` | Open a new tab |
| `recents` | `total` | Recently opened files |
| `random` | `folder=`, `newtab` | Open a random note |
| `random:read` | `folder=` | Read a random note |
| `workspace` | `ids` | Show workspace tree |
| `bookmark` | `file=`, `subpath=`, `folder=`, `search=`, `url=`, `title=` | Add a bookmark |
| `bookmarks` | `total`, `verbose`, `format=` | List bookmarks |
| `template:insert` | `name=` (required) | Insert template into active file |
| `template:read` | `name=` (required), `resolve`, `title=` | Read template content |
| `templates` | `total` | List templates |

## Sync & History

| Command | Key options | Notes |
|---|---|---|
| `sync:status` | — | Show sync status |
| `sync` | `on`, `off` | Pause/resume sync |
| `sync:history` | `file=`/`path=`, `total` | Version history for a file |
| `sync:read` | `file=`/`path=`, `version=` (required) | Read a sync version |
| `sync:restore` | `file=`/`path=`, `version=` (required) | Restore a sync version |
| `sync:deleted` | `total` | List deleted files in sync |
| `sync:open` | `file=`/`path=` | Open sync history in UI |
| `diff` | `file=`/`path=`, `from=`, `to=`, `filter=local\|sync` | Diff versions |
| `history` | `file=`/`path=` | List file history versions |
| `history:list` | — | List files with history |
| `history:read` | `file=`/`path=`, `version=` | Read a history version (default: 1) |
| `history:restore` | `file=`/`path=`, `version=` (required) | Restore a history version |
| `history:open` | `file=`/`path=` | Open file recovery in UI |

## Vault Info

| Command | Key options | Notes |
|---|---|---|
| `vault` | `info=name\|path\|files\|folders\|size` | Show vault info |
| `vaults` | `total`, `verbose` | List all known vaults |
| `folders` | `folder=`, `total` | List folders |
| `folder` | `path=` (required), `info=files\|folders\|size` | Show folder info |
| `version` | — | Show Obsidian version |
| `reload` | — | Reload the vault |
| `restart` | — | Restart Obsidian |

## Plugins & Themes

| Command | Key options | Notes |
|---|---|---|
| `plugins` | `filter=core\|community`, `versions`, `format=` | List installed plugins |
| `plugins:enabled` | `filter=`, `versions`, `format=` | List enabled plugins |
| `plugin` | `id=` (required) | Get plugin info |
| `plugin:enable` | `id=` (required), `filter=` | Enable a plugin |
| `plugin:disable` | `id=` (required), `filter=` | Disable a plugin |
| `plugin:install` | `id=` (required), `enable` | Install a community plugin |
| `plugin:uninstall` | `id=` (required) | Uninstall a community plugin |
| `plugin:reload` | `id=` (required) | Reload a plugin (dev use) |
| `plugins:restrict` | `on`, `off` | Toggle restricted mode |
| `snippets` | — | List CSS snippets |
| `snippets:enabled` | — | List enabled CSS snippets |
| `snippet:enable` | `name=` (required) | Enable a CSS snippet |
| `snippet:disable` | `name=` (required) | Disable a CSS snippet |
| `themes` | `versions` | List installed themes |
| `theme` | `name=` | Show active theme or get info |
| `theme:set` | `name=` (required) | Set active theme (empty = default) |
| `theme:install` | `name=` (required), `enable` | Install a community theme |
| `theme:uninstall` | `name=` (required) | Uninstall a theme |
