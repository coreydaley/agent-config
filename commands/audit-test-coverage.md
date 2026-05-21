---
description: >-
  Dual-agent test coverage audit — runs real coverage tooling, then Claude
  and Codex review independently (gaps, pyramid balance, test quality,
  missing categories), synthesize, devil's advocate pass, output as findings report
disable-model-invocation: true
---

Invoke the `audit-test-coverage` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty).
