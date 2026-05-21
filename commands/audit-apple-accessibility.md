---
description: >-
  Dual-agent Apple platform accessibility audit — Claude and Codex review
  native Apple UI (SwiftUI/UIKit/AppKit/WatchKit) against Apple HIG and the
  platform's accessibility APIs independently, synthesize, devil's advocate
  pass, output as findings report. For web frontends, use /audit-web-accessibility.
disable-model-invocation: true
---

Invoke the `audit-apple-accessibility` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty).
