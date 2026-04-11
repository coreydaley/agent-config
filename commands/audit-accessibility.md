---
description: >-
  Dual-agent accessibility audit — Claude and Codex review against WCAG
  2.1/2.2 independently, synthesize, devil's advocate pass, output as
  findings report
disable-model-invocation: true
---

Invoke the `audit-accessibility` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty).
