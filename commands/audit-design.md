---
description: >-
  Dual-agent design audit — Claude and Codex review UI/UX independently,
  synthesize findings, devil's advocate pass, output as findings report
disable-model-invocation: true
---

Invoke the `audit-design` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty).
