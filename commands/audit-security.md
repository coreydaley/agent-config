---
description: >-
  Dual-agent security audit — Claude and Codex review independently,
  synthesize, devil's advocate pass, output as findings report
disable-model-invocation: true
---

Invoke the `audit-security` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty).
