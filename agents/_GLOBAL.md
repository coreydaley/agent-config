# Global Agent Instructions

These instructions apply to all AI agents configured from this repository.

## Commit Style

Use Conventional Commits for all git commits:

```
<type>(<scope>): <short summary>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci`

- Summary: imperative mood, lowercase, no trailing period, max 72 chars
- Always include a `Co-authored-by:` trailer identifying the AI agent

## Code Conventions

- Prefer editing existing files over creating new ones
- Avoid over-engineering; implement only what is needed
- Do not add comments unless the logic is non-obvious
- Never commit secrets, credentials, or `.env` files

## Disclaimer

This repository contains AI-generated content. Review all configurations, scripts, and instructions before use in production or sensitive environments. See SECURITY.md for details.
