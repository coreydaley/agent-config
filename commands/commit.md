# Commit

Analyze all uncommitted changes in the current git repository and create well-organized commits grouped by related file paths.

## Instructions

1. **Detect a ticket ID from the branch name** by running `git branch --show-current`:
   - If the branch name starts with a pattern matching a project tracker ticket ID — such as `ENG-1234`, `PROJ-42`, `ABC-999` (one or more uppercase letters, a hyphen, one or more digits) — extract that ticket ID
   - The ticket ID may be followed by a hyphen, slash, or other separator and a description, e.g. `ENG-1234-add-login-button` → ticket is `ENG-1234`
   - Store the ticket ID for use in every commit message in this session; if no ticket ID is found, omit it from all commit messages

2. **Discover all changes** by running:
   - `git status` to see all modified, added, deleted, and untracked files
   - `git diff` to see unstaged changes
   - `git diff --staged` to see already-staged changes
   - For untracked files, read each file to understand its content

3. **Group files logically** by examining their paths and content. Use these grouping principles:
   - Files in the same directory that serve a common purpose belong together
   - Configuration files of the same type belong together (e.g., all `*.json` config files)
   - A feature's implementation file and its test file belong together
   - Files with a clear parent-child or dependency relationship belong together
   - Do NOT group unrelated files just because they are both modified

4. **Analyze each group** by reading the diffs to understand:
   - What changed (added, removed, or modified lines)
   - Why the change was likely made (new feature, bug fix, refactor, config update, docs, etc.)
   - The scope and impact of the change

5. **Create one commit per group**:
   - Stage only the files for that group using `git add <file> [<file> ...]` — never use `git add .` or `git add -A`
   - Identify which AI agent is executing this commit and use the corresponding `Co-authored-by` trailer:
     - Claude Code → `Co-authored-by: Claude Sonnet 4.6 <noreply@anthropic.com>`
     - ChatGPT / Codex → `Co-authored-by: ChatGPT <noreply@openai.com>`
     - GitHub Copilot → `Co-authored-by: GitHub Copilot <noreply@github.com>`
   - Write a commit message following this format:
     ```
     <type>(<scope>): <short summary>

     <optional body explaining why, not what>

     Addresses <TICKET-ID>
     Co-authored-by: <AI agent name> <noreply@example.com>
     ```
   - Include the `Addresses <TICKET-ID>` trailer line only if a ticket ID was detected in step 1; omit it entirely if no ticket ID was found
   - Always include the `Co-authored-by` trailer for the agent executing the commit
   - Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `style`, `ci`
   - Scope: the directory name or component affected (e.g., `commands`, `agents/claude`, `scripts`)
   - Summary: imperative mood, lowercase, no period, max 72 chars
   - Commit using: `git commit -m "$(cat <<'EOF'\n<message>\nEOF\n)"`

6. **Order commits** from most foundational to most dependent (e.g., config changes before feature code, shared utilities before callers).

7. **After all commits**, run `git log --oneline -20` and display the result so the user can review what was created.

## Constraints

- Never use `--no-verify` or skip hooks
- Never amend existing commits
- Never force push
- Never commit files that likely contain secrets (`.env`, credentials, tokens)
- If a file's purpose is unclear, read it before deciding how to group or describe it
- If $ARGUMENTS is provided, treat it as additional context or scoping instructions (e.g., a subdirectory to limit commits to, or a description of the work done)
