---
description: >-
  Dual-agent Apple platform test-design audit — XCTest vs Swift Testing
  (Xcode 16), XCUITest critical-flow coverage, SwiftUI view-testing strategy,
  Preview coverage, snapshot testing, @MainActor in tests, async test patterns.
  Goes beyond line coverage into test quality. Uses /audit-test-coverage raw
  data if present.
disable-model-invocation: true
---

Invoke the `audit-apple-testing` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty). Pass `--diff-only` through if present.
