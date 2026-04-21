---
name: commit
description: >-
  Analyze uncommitted changes and create well-organized, logically grouped
  conventional commits. Sprint-artifact groups get multi-agent co-authored-by
  trailers from the sprints ledger; everything else gets a single Claude
  trailer. Runs ~/.claude/lib/commit.py to build a deterministic plan, then
  the agent fills in type/scope/summary for unclassified groups.
disable-model-invocation: true
---

# Commit

Analyze all uncommitted changes in the current git repository and create
well-organized, atomic commits with proper Conventional Commits messages
and correct `Co-authored-by:` trailers.

**This skill never commits without explicit user invocation.** It is
invoked via `/commit` (or equivalent explicit user instruction); it does
not self-invoke from the model picker.

## Workflow

### Step 1: Build the plan

Run the commit planner to get a deterministic analysis of the working
tree:

```bash
python3 ~/.claude/lib/commit.py
```

The script outputs JSON with the following shape:

```json
{
  "ticket_id": "ENG-742" or null,
  "branch": "feature/foo",
  "warnings": ["..."],
  "groups": [
    {
      "kind": "pre-staged" | "sprint-artifact" | "unclassified",
      "label": "pre-staged" | "sprint-001" | "unclassified",
      "sprint_id": "001",               // sprint-artifact groups only
      "files": ["path/to/file", ...],
      "trailers": ["Co-authored-by: Claude <...>", ...],
      "needs_agent_decision": ["type", "scope", "summary", "body"],
      "suggested_type": "feat",         // sprint-artifact groups only
      "suggested_scope": "sprint-001"   // sprint-artifact groups only
    }
  ],
  "commit_order": ["pre-staged", "sprint-001", "unclassified"]
}
```

If the script exits non-zero:
- Exit 2 → not inside a git repo. Surface the error and stop.
- Exit 1 → bad args. Shouldn't happen from this skill, but stop and report.

If `warnings` is non-empty, surface each warning to the user before
proceeding. Don't block on warnings — they're informational — but the
user should see them.

If `groups` is empty, tell the user "Nothing to commit. Working tree
clean." and stop.

### Step 2: Walk the groups in `commit_order`

For each group, do the work described below. **Commit them in the order
specified** — the script has already sorted them foundationally
(pre-staged first, then sprint artifacts by sprint number, then
unclassified).

### Step 3: Handle each group by kind

**Kind: `pre-staged`**

Files are already in the index. Don't re-stage.

- Read the diff of staged files: `git diff --cached`
- Determine `type`, `scope`, and `summary` from the diff content
- Write the commit message (see "Commit message format" below) using the
  group's `trailers` and the plan's `ticket_id`
- Commit via heredoc (see "Heredoc commit" below)

**Kind: `sprint-artifact`**

Files are sprint planning artifacts. The script has already determined
the participants and appropriate trailers from the ledger.

- Stage exactly the files in this group: `git add <file> <file> ...`
- Use the suggested `type` (usually `feat`) and `suggested_scope`
  (e.g. `sprint-001`)
- Write a summary like `plan <sprint title>` — read the sprint doc to
  get the title from its `# Sprint: <title>` heading
- Write a body describing the deliberation path if one is obvious from
  the artifacts present (e.g. "Sprint planned via multi-model
  deliberation with Claude primary drafter, Codex competing drafter,
  Opus devil's advocate.")
- Commit via heredoc using the group's `trailers` (which may include
  both Claude and Codex) and the plan's `ticket_id`

**Kind: `unclassified`**

Files are everything else. The agent must group them by logical purpose.

Apply these grouping principles (same as the original /commit command):
- Files in the same directory that serve a common purpose belong together
- Configuration files of the same type belong together
- A feature's implementation file and its test file belong together
- Files with a clear parent-child or dependency relationship belong
  together
- Do NOT group unrelated files just because they were both modified

Read file content when path alone is ambiguous — a file's purpose
sometimes requires seeing its diff.

For each sub-group you form:
- Stage exactly those files (never `git add -A` or `git add .`)
- Determine `type`, `scope`, and `summary` from the diff
- Write the commit message using the group's single Claude trailer and
  the plan's `ticket_id`
- Commit via heredoc
- Order sub-groups from most foundational to most dependent (config
  before feature code, shared utilities before callers)

### Step 4: Show the result

After all commits are made, run:

```bash
git log --oneline -50
```

and display the output so the user can review.

---

## Commit message format

```
<type>(<scope>): <summary>

<optional body explaining why, not what>

Addresses <TICKET-ID>        (only if ticket_id is non-null)
<trailer 1>
<trailer 2>                  (sprint-artifact groups may have multiple)
```

**Rules:**
- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci`
- Summary: imperative mood, lowercase, no trailing period
- `type(scope): summary` line: max 72 characters total
- Scope: directory name or component affected (e.g. `commands`,
  `agents/claude`, `sprint-001`, `scripts`)
- Body: explain *why* not *what*; omit if the summary is self-evident
- `Addresses <TICKET-ID>` only if the plan provided a `ticket_id`; omit
  otherwise (no `Addresses: none`, no placeholder)
- Use the exact `trailers` strings from the plan — do not reconstruct or
  reorder them

## Heredoc commit

Always commit via heredoc to preserve newline formatting. The body and
closing `EOF` must be at column 0:

```bash
git commit -m "$(cat <<'EOF'
feat(sprint-001): plan participant tracking column

Sprint planned via multi-model deliberation: Claude primary drafter,
Codex competing drafter, Opus devil's advocate.

Addresses ENG-742
Co-authored-by: Claude <noreply@anthropic.com>
Co-authored-by: Codex <noreply@openai.com>
EOF
)"
```

## Constraints

- **Never use `--no-verify` or skip hooks.** Respect repo hooks as
  configured.
- **Never amend existing commits.** If a mistake lands, surface it
  and ask the user — don't silently fix with `--amend`.
- **Never force-push.** This skill doesn't push at all; pushes are
  always manual.
- **Never commit files that likely contain secrets** (`.env`,
  credentials, tokens, API keys). If `git diff` output contains
  patterns matching `password|secret|api[_-]?key|token`, stop and ask
  before committing.
- **Never `git add -A` or `git add .`.** Always stage explicit file
  lists.
- **Never reorder groups from the plan.** The script's `commit_order`
  is deterministic; respect it.
- **Never invent trailers.** The plan's `trailers` list is the source
  of truth.
- **Never silently skip warnings.** Always surface the plan's
  `warnings` array to the user before committing.
