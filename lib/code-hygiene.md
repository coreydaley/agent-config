# Code Hygiene

The rules the `pr-*` family enforces on code it writes or cleans up.
One definition, cited by `/pr-build` (at write time and in its final
sweep), `/pr-fix` (when applying fixes), and `/pr-polish` (as the safety
net before merge). Repo-local `CLAUDE.md` conventions add to these, they
don't replace them.

## Comments

Comments are for two things: function-level doc comments, and an inline
*why* the code can't show (a guard that skips validation on purpose, a
workaround for a dependency bug, an ordering constraint). Everything
else is noise.

Banned outright:

- Restating the code or the diff (`// increment the counter`).
- Explaining why a change is correct. That's PR-review talk and it dies
  at merge.
- Pointer comments (`// documented on the variable`, `// see PLAN.md`).
- Purpose editorials on constants (`// this is the mode that stops
  table growth`).
- Enumerating enum or mode semantics in more than one place. Semantics
  live at the definition, one clause per value. Other sites reference
  the name.
- AI-flavored openers: `This function ...`, `This module ...`, `We
  refactor ...`, `We add ...`, `Note that ...`, `Importantly ...`,
  `It's worth noting ...`.
- Internal review or plan identifiers (`SR042`, `PA003`, `CR007`,
  GitHub comment IDs). Issue numbers don't belong in code comments
  either; a PR number for provenance is fine.

Length: one line by default. A multi-line comment has to earn it with a
*why* that genuinely takes more than about 80 characters.

The test when sweeping: delete the comment in your head. If a future
reader would be confused without it, keep it. Otherwise it goes.

## Tests

A test earns its place by failing when the claim it covers is false.
Sweep for:

- **Tautologies.** Asserting a value equals itself, asserting a mock
  returns what it was told to return, `assert.NoError` on a function
  that can't error.
- **Doubles that certify the buggy path.** A fake whose behavior was
  written to match the implementation instead of the contract. If the
  implementation is wrong, the fake is wrong the same way and the test
  passes.
- **Missing negative cases.** Every behavior change gets at least one
  test for the input it should reject, the error it should return, or
  the branch it should not take.
- **Assertions on incidental detail.** Exact log strings, map ordering,
  timing. They break on unrelated changes and prove nothing about the
  claim.
- **Tests that don't run.** Wrong build tag, misspelled `Test` prefix,
  skipped without a reason.

Match the package's existing conventions (table-driven, fixtures,
fakes, harness). A test in a foreign style is a review finding waiting
to happen.

## Commits

Conventional Commits: `<type>(<scope>): <summary>`. Types: `feat`,
`fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci`. Imperative
mood, lowercase, no trailing period, the whole first line at most 72
characters. Scope is the component or directory.

Body explains *why*, not *what*, and only when the summary doesn't
already say it. Reference the implementation issue as `Refs #N` when the
work has a GitHub issue source; `Closes #N` belongs in the PR body, so
the issue closes on merge rather than on the first push. Never reference
a feature (parent) issue. Never cite private conversations. No internal
review or plan IDs.

Trailer, always: `Co-authored-by: Claude <noreply@anthropic.com>`.

Mechanics:

- Stage explicit paths. Never `git add -A` or `git add .`.
- Commit via heredoc so the body's newlines survive.
- Never `--no-verify`, never `--amend`, never force-push from a build
  skill. Hook failure: surface it and stop.
- Never read the exit status through a pipe. `git commit ... > /tmp/out
  2>&1; EXIT=$?`, then confirm `git log -1` shows your subject.
- `go build ./cmd/<name>` drops a binary in the cwd. Build with `-o
  /dev/null` or delete it before staging.
- Before staging, scan the diff for `password|secret|api[_-]?key|token`
  in *values*, not identifiers. A hit stops the commit and asks.

## PR bodies

Self-contained: a reader with only the PR and the linked issue can
verify every claim. Justify on technical merit. No "per our chat
discussion," no attributing positions to people, no internal IDs, no
parent issue numbers. Say what changed and how it was tested. Anything
the plan declined to do that a reviewer will predictably ask about goes
in a short "Not in this PR" list with the one-clause reason.

## Files

New source, test, and fixture files are fine when they're the narrowest
way to satisfy a planned task and follow local layout. New docs, helper
scripts, config files, and top-level directories are restricted: the
plan has to list them, or the user has to say yes when asked. Prefer
extending the closest existing file.
