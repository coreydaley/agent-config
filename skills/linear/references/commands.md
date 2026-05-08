# Linear CLI Command Reference

## Issues

| Command | Description |
|---------|-------------|
| `linear issue query` | Query issues with filters |
| `linear issue view [id]` | View issue details |
| `linear issue create` | Create a new issue |
| `linear issue update [id]` | Update an issue |
| `linear issue delete [id]` | Delete an issue |
| `linear issue start [id]` | Mark issue as started |
| `linear issue comment add` | Add a comment |
| `linear issue comment list` | List comments |
| `linear issue relation add` | Add a relation (blocks, duplicate, etc.) |
| `linear issue link <url>` | Link a URL to an issue |
| `linear issue attach <id> <file>` | Attach a file |
| `linear issue pr [id]` | Create a GitHub PR from issue |
| `linear issue url [id]` | Print issue URL |
| `linear issue id` | Print issue from current git branch |

### `issue query` flags

| Flag | Description |
|------|-------------|
| `--team <key>` | Filter by team (can repeat) |
| `--all-teams` | Query across all teams |
| `--assignee <user>` | Filter by assignee (`@me` for self) |
| `--state <state>` | `triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled` |
| `--all-states` | Include all states (default) |
| `--cycle <name\|number\|active>` | Filter by cycle |
| `--project <name>` | Filter by project |
| `--label <name>` | Filter by label (can repeat) |
| `--sort <manual\|priority>` | Sort order (required) |
| `--limit <n>` | Max results (default 50, 0 = unlimited) |
| `--created-after <date>` | ISO 8601 or YYYY-MM-DD |
| `--updated-after <date>` | ISO 8601 or YYYY-MM-DD |
| `--search <term>` | Full-text search |
| `-j, --json` | JSON output |
| `--no-pager` | Disable paging |

### `issue update` flags

| Flag | Values |
|------|--------|
| `--state` | `triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled` |
| `--priority` | `urgent`, `high`, `medium`, `low`, `no-priority` |
| `--assignee` | username or `@me` |
| `--title` | New title |
| `--description` | New description |
| `--label` | Label name (can repeat) |
| `--cycle` | Cycle name, number, or `active` |
| `--project` | Project name |
| `--milestone` | Milestone name |

## Cycles

| Command | Description |
|---------|-------------|
| `linear cycle list --team <key>` | List cycles |
| `linear cycle view <id>` | View cycle details |

## Projects

| Command | Description |
|---------|-------------|
| `linear project list --team <key>` | List projects |
| `linear project view <id>` | View project details |
| `linear project-update list` | List project status updates |

## Teams

| Command | Description |
|---------|-------------|
| `linear team list` | List all teams |
| `linear team view <key>` | View team details |

## Labels

| Command | Description |
|---------|-------------|
| `linear label list --team <key>` | List labels |
| `linear label create` | Create a label |

## Documents

| Command | Description |
|---------|-------------|
| `linear document list` | List documents |
| `linear document view <id>` | View a document |

## Milestones & Initiatives

| Command | Description |
|---------|-------------|
| `linear milestone list` | List milestones |
| `linear initiative list` | List initiatives |

## Raw API

```bash
# Run a raw GraphQL query
linear api "query { viewer { id name email } }"

# Print full GraphQL schema
linear schema
```
