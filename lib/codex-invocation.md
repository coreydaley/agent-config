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

Skills that invoke `codex exec` (directly, or via `lib/audit-codex.sh`)
should follow the canonical pattern above. Sync this file's pattern with
their invocations whenever it changes:

Non-audit skills (direct `codex exec` calls):
- `skills/sprint-plan/nodes/reviews.md`
- `skills/review-pr-comprehensive/nodes/independent-reviews.md`
- `skills/review-pr-comprehensive/nodes/devils-advocate.md`

Audit skills (all invoke `codex exec` through `lib/audit-codex.sh`, which
encapsulates the canonical flags — so the wrapper is the single drift
point, not each skill):
- `lib/audit-codex.sh` — owns the canonical invocation for every audit
- `skills/audit-apple-accessibility/`
- `skills/audit-apple-adaptivity/`
- `skills/audit-apple-app-store-review/`
- `skills/audit-apple-architecture/`
- `skills/audit-apple-design/`
- `skills/audit-apple-localization/`
- `skills/audit-apple-performance/`
- `skills/audit-apple-persistence/`
- `skills/audit-apple-privacy/`
- `skills/audit-apple-security/`
- `skills/audit-apple-testing/`
- `skills/audit-architecture/`
- `skills/audit-design/`
- `skills/audit-web-accessibility-human/`
- `skills/audit-web-responsive/`
- `skills/audit-web-security/`

All audit skills follow the dot-graph pattern (see
`docs/DOT-GRAPH-SKILL-PATTERN.md`). The shared `lib/audit-*.sh`
scripts (`audit-runner.sh`, `audit-codex.sh`, `audit-verify.sh`) own all
structural side effects: creating `$AUDIT_DIR`, launching `codex exec`
with verified output, and gating the handoff on artifact presence.

Verification:

```bash
# Direct codex invocations (non-audit skills):
grep -nE "codex exec" \
  skills/sprint-plan/nodes/reviews.md \
  skills/review-pr-comprehensive/nodes/*.md
# Should each include -s workspace-write, --add-dir, -C, --, < /dev/null.

# Audit skills go through the wrapper:
grep -nE "audit-codex.sh" skills/audit-*/nodes/*.md
# Each match should pass <audit-dir> <role> <prompt-file> as the three args.
```

Each direct `codex exec` should be followed (within ~8 lines) by
`-s workspace-write`, `--add-dir`, `-C`, `--`, and end with `< /dev/null`.
Audit skills pass `--add-dir "$AUDIT_DIR"` and `-C "$PROJECT_CWD"` from
inside `audit-codex.sh` — both variables are persisted in
`$AUDIT_DIR/MANIFEST.json` by `audit-runner.sh init` in Phase 1.
