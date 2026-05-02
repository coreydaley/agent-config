---
name: gh
description: >-
  Use the gh CLI for all GitHub and git operations. Trigger whenever the task
  involves commits, pull requests, issues, branches, releases, code search,
  repository management, or any other git/GitHub interaction. Prefer gh over
  GitHub MCP tools in all cases.
---

# GitHub via gh CLI

Always use the `gh` CLI for GitHub operations. Do not use GitHub MCP tools.

## Common operations

```bash
# Issues
gh issue list
gh issue view <number>
gh issue create --title "..." --body "..."
gh issue comment <number> --body "..."
gh issue close <number>

# Pull requests
gh pr list
gh pr view <number>
gh pr create --title "..." --body "..."
gh pr review <number> --approve
gh pr review <number> --request-changes --body "..."
gh pr merge <number> --squash
gh pr checkout <number>
gh pr comment <number> --body "..."

# Repositories
gh repo view
gh repo clone <owner>/<repo>
gh repo fork

# Branches
git checkout -b <branch>
git push -u origin <branch>
gh pr create   # after pushing

# Releases and tags
gh release list
gh release view <tag>
gh release create <tag> --title "..." --notes "..."

# Search
gh search issues "<query>"
gh search prs "<query>"
gh search code "<query>"

# CI / Actions
gh run list
gh run view <run-id>
gh run watch

# Raw API calls when gh commands don't cover it
gh api <endpoint>
```

## Useful flags

- `--json <fields>` — output specific fields as JSON
- `--jq <expr>` — filter JSON inline
- `--web` — open in browser
- `-R <owner>/<repo>` — target a different repo than cwd
