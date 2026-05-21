---
description: >-
  Dual-agent web accessibility audit — Claude and Codex review web frontends
  (HTML/CSS/JS/component files) against WCAG 2.1/2.2 independently, synthesize,
  devil's advocate pass, output as findings report. For native Apple platforms,
  use /audit-accessibility-apple.
disable-model-invocation: true
---

Invoke the `audit-accessibility-web` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty).
