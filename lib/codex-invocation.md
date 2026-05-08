# Codex Invocation Pattern

Canonical pattern for invoking `codex exec` non-interactively from a skill.
Drift here is silent: skip a flag and codex hangs, fails to write the artifact,
or misparses the prompt without an obvious error.

## Canonical command

```bash
codex exec \
  -s workspace-write \
  --add-dir "$WRITE_DIR" \
  -C "$PROJECT_CWD" \
  -- "<prompt or $(cat /tmp/codex-prompt.txt)>" \
  < /dev/null
```

## Flag rationale

Each piece is load-bearing.

- **`< /dev/null`** — codex's `exec` mode reads stdin even when a positional
  prompt is provided. Per `codex exec --help`: *"If stdin is piped and a prompt
  is also provided, stdin is appended as a `<stdin>` block."* Background bash
  and most non-TTY contexts inherit an open stdin that never sends EOF, so
  codex blocks forever showing only `Reading additional input from stdin...`.
  `< /dev/null` gives it an immediately-closed empty stdin and codex proceeds.

- **`-s workspace-write`** — the default sandbox is effectively read-only for
  sub-processes. Without this codex cannot write its output artifact and the
  phase silently produces no file.

- **`--add-dir "$WRITE_DIR"`** — `workspace-write` only grants write access
  inside the cwd workspace. Artifact targets like `~/Reports/…/codex-draft.md`
  live outside the project repo, so without `--add-dir` the write fails. Pass
  the directory codex needs to write into (typically `$SESSION_DIR` or
  `$PR_DIR`).

- **`-C "$PROJECT_CWD"`** — set the workspace root to where the code lives
  (e.g. the mono main worktree, or the PR-review worktree). Codex reads
  project files relative to this. Omitting `-C` makes codex use the shell's
  cwd, which may not be the codebase.

- **`-- "<prompt>"`** — the `--` ends option processing so any leading `-`
  inside the prompt isn't parsed as a codex flag. For long prompts, write to
  a temp file and use `"$(cat /tmp/codex-prompt.txt)"` to sidestep shell
  quoting issues with newlines, backticks, and `$` references.

## What not to do

- **Never `-m`.** There is no `-m` flag in `codex exec`. Passing it hangs the
  CLI on stdin (a separate failure mode from the missing-`< /dev/null` case).
  To override the model, use `-c model="<name>"` (TOML-parsed value).

- **Never skip `< /dev/null`** in non-TTY contexts. The hang is silent.

- **Never invoke codex without `--add-dir`** when the artifact path is outside
  the workspace. The write failure is silent.

## Verify the artifact

After the codex call returns, check that the expected output file exists at
the path you specified in the prompt. If it doesn't, read the codex output
(stderr or the captured background log) before proceeding. Silent failure
(sandbox denial, prompt misroute, missing flag) is the most common codex
failure mode.

---

## Drift detection

Skills that invoke `codex exec` should follow the canonical pattern above.
Sync this file's pattern with their invocations whenever it changes:

- `skills/sprint-plan/SKILL.md`
- `skills/review-pr-comprehensive/SKILL.md`

Verification:

```bash
# Every codex invocation in these skills should include all four hygiene flags.
grep -nE "codex exec" skills/sprint-plan/SKILL.md skills/review-pr-comprehensive/SKILL.md
```

Each match should be followed by `-s workspace-write`, `--add-dir`, `-C`, `--`,
and the call should end with `< /dev/null`.
