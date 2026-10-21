---
name: pr-address
description: >-
  Address everything on one of our PRs: review threads and top-level
  reviews from humans and bots alike, triaged against the plan's scope
  before anything is fixed. Shorthand for /pr-fix <pr> --source all.
  Use when asked to "address the comments on this PR", "go through the
  PR feedback", "handle what Copilot said", or via /pr-address.
argument-hint: "<pr number or url> [--no-ci] [--help]"
disable-model-invocation: false
---

# PR Address

An alias. Everything here is `/pr-fix` in PR mode with `--source all`:
one source (the PR), every unresolved thread and non-empty top-level
review from humans and bots, triaged against PLAN.md before a single
edit, applied in the PR's commit regime, replies drafted for human
and bot threads, and failing checks come along by default. Add `--no-ci` to leave the checks out.

## How to run it

1. If the arguments include `--help` or `-h`, print the help blurb
   below and stop.
2. Otherwise invoke the `pr-fix` skill with the arguments
   `<pr> --source all` plus `--no-ci` if it was passed, and follow
   `pr-fix`'s graph from its `init` node. This skill has no graph, no
   state, and no nodes of its own. Every rule in
   `skills/pr-fix/SKILL.md` applies, including the Opus session check,
   the External Content Handling policy, and the Don'ts.

A PR argument is required. There's no REVIEW.md or TRIAGE.md form
here. Use `/pr-fix` directly for those.

## Help mode

```
/pr-address: address every comment on one of our PRs.

What it does
  Runs /pr-fix <pr> --source all: loads the PR's unresolved review
  threads and top-level reviews from humans and bots, triages each
  against PLAN.md Scope In/Out, shows the fix / defer / won't-fix
  table for approval, applies the approved fixes with targeted tests,
  commits in the PR's regime, gates the push, and drafts replies to
  human and bot threads for you to approve before posting.

Usage
  /pr-address <pr> [--no-ci] [--help]

  <pr>          PR number or URL. Required.
  --no-ci       Skip failing checks. They are addressed by default.
  --help, -h    Print this help.

Full documentation: /pr-fix --help
```

## ARGUMENTS

$ARGUMENTS
