# Node: commit-groups

Walk the groups in the plan's `commit_order`, handling each by `kind`. Stage explicitly, write conventional commit messages, commit via heredoc. Single node, internal per-group loop.

## Inputs

- `plan_json` (or `plan_path`), `ticket_id`, `group_count` from walker state

```bash
STATE="<path>"
PLAN=$(scripts/walk.sh get --state "$STATE" --key plan_json)  # or read plan_path
TICKET_ID=$(scripts/walk.sh get --state "$STATE" --key ticket_id)
```

## Per-group loop

For each group in `plan["commit_order"]`, dispatch by `kind`:

### Kind: `pre-staged`

Files are already in the index. Don't re-stage.

1. Read the staged diff:
   ```bash
   git diff --cached
   ```
2. Determine `type`, `scope`, and `summary` from the diff content. (See "Commit message format" below.)
3. Write the commit message using the group's `trailers` and the plan's `ticket_id`.
4. Commit via heredoc.

### Kind: `unclassified`

Files are everything else. Group them by logical purpose:

- Files in the same directory serving a common purpose belong together.
- Configuration files of the same type belong together.
- A feature's implementation file and its test file belong together.
- Files with a clear parent-child or dependency relationship belong together.
- **Do NOT group unrelated files** just because they were both modified.

Read file content when path alone is ambiguous — a file's purpose sometimes requires seeing its diff.

For each sub-group:

1. **Stage exactly those files** with explicit paths. **Never `git add -A` or `git add .`**.
2. Read the staged diff and determine `type`, `scope`, `summary`.
3. Write the commit message using the group's single Claude trailer and the plan's `ticket_id`.
4. Commit via heredoc.

Order sub-groups from most foundational to most dependent (config before feature code, shared utilities before callers).

## Commit message format

```
<type>(<scope>): <summary>

<optional body explaining why, not what>

Addresses <TICKET-ID>        (only if ticket_id is non-null)
<trailer 1>
```

Rules:

- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci`.
- Summary: imperative mood, lowercase, no trailing period.
- `type(scope): summary` line: max 72 characters total.
- Scope: directory name or component affected (e.g. `commands`, `agents/claude`, `scripts`).
- Body: explain *why*, not *what*. Omit if the summary is self-evident.
- `Addresses <TICKET-ID>` only if the plan supplied a `ticket_id`. Omit otherwise — no `Addresses: none`, no placeholder.
- Use the **exact** `trailers` strings from the plan. Don't reconstruct or reorder them.

## Heredoc commit

Always commit via heredoc to preserve newline formatting. Body and closing `EOF` at column 0:

```bash
git commit -m "$(cat <<'EOF'
feat(scripts): add participant resolution helper

Centralizes the lookup so commit and sprint tools share one path.

Addresses ENG-742
Co-authored-by: Claude <noreply@anthropic.com>
EOF
)"
```

## Secret detection

Before staging, scan diffs for likely secret patterns: `password`, `secret`, `api[_-]?key`, `token`. If a match appears in the diff content (not just in code that legitimately handles those concepts — read the surrounding context), **stop and ask the user** before committing. Options:

- Drop the file from this group and continue.
- Drop the specific lines (manual edit, then re-stage).
- Abort the whole skill — surface the issue and stop.

This is an inline user dialogue inside this node, not a separate graph route. If the user aborts, surface clearly and route to `show-result` anyway so they can see what (if anything) committed before the stop.

## Hook failures

If a pre-commit hook fails, **don't retry with `--no-verify`** and don't `--amend`. Surface the hook error verbatim, stop the loop, and route to `show-result`. The user will see what got committed and decide how to fix the hook issue (typically: fix the underlying problem and re-run `/commit` for the remaining groups).

## Constraints

- **Never `--no-verify`.** Respect repo hooks.
- **Never `--amend`.** Surface mistakes; ask the user.
- **Never force-push.** This skill doesn't push at all.
- **Never `git add -A` or `git add .`.** Always explicit file lists.
- **Never reorder groups.** The plan's `commit_order` is deterministic; respect it.
- **Never invent trailers.** The plan's `trailers` are the source of truth.

## Outputs

- N new commits in the local git history (where N = sum of pre-staged groups + sub-groups derived from unclassified groups).
- Per-commit messages on stdout (from `git commit`).

## Outgoing edges

- → `show-result` (always — single outgoing edge, even on partial success)

Record the transition:

```bash
scripts/walk.sh transition --state "$STATE" --from commit_groups --to show_result
```

## Failure modes

- A hook fails on commit N of M → stop the loop, surface the error, transition to `show-result`. Commits 1..N-1 are already in.
- Secret detected and user aborts → stop, transition to `show-result`. Whatever committed before the abort stays committed; user decides whether to revert.
- A staging command fails (file vanished, permissions) → surface the error, skip that group, continue with the rest. Note the skip in the running output.
