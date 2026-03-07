# Contributing

Thank you for your interest in contributing to agent-config!

## Ways to Contribute

- Report bugs or unexpected behavior
- Suggest new skills, commands, or subagent configurations
- Improve documentation
- Submit fixes or new features via pull request

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/<your-username>/agent-config.git`
3. Create a branch from `main`: `git checkout -b <type>/<short-description>`
4. Make your changes
5. Test that symlinks and configurations work correctly: `make all`
6. Submit a pull request

## Branch Naming

Use the format `<type>/<short-description>`, where type is one of:

- `feat` - new skill, command, subagent, or capability
- `fix` - bug fix
- `docs` - documentation only
- `chore` - maintenance, tooling, scripts
- `refactor` - restructuring without behavior change

## Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

<optional body explaining why, not what>
```

- **type**: `feat`, `fix`, `docs`, `chore`, `refactor`, `style`, `ci`, `test`
- **scope**: the directory or component affected (e.g., `skills`, `commands`, `agents/claude`, `scripts`)
- **summary**: imperative mood, lowercase, no trailing period, max 72 characters

## Pull Request Guidelines

- Keep PRs focused — one logical change per PR
- Update relevant README files if your change affects documented behavior
- Ensure `make all` runs without errors before submitting
- Fill out the pull request template

## Adding New Resources

| Resource type | Location | Notes |
|---|---|---|
| Skills | `skills/<name>/` | Include a `SKILL.md` |
| Commands | `commands/<name>.md` | Follow existing frontmatter format |
| Subagents | `subagents/<name>/` | Include agent instructions |
| Agent configs | `agents/<agent>/` | Edit `_<AGENT>.md`; run `make generate` |
| Prompts | `prompts/` | Document in `prompts/README.md` |

## Compatibility Note

Not all resources work with all agents. If your contribution is agent-specific, note that clearly in the relevant files.

## Reporting Issues

Please [open an issue](https://github.com/coreydaley/agent-config/issues) and use the appropriate issue template.
