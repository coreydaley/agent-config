---
description: >-
  Dual-agent Apple platform privacy compliance audit — Privacy Manifest
  (PrivacyInfo.xcprivacy, required since May 2024), Info.plist purpose strings,
  ATT / IDFA, required-reason API declarations, third-party SDK privacy
  declarations, data-minimization patterns, App Privacy Report alignment.
  Preempts App Review rejection on privacy grounds.
disable-model-invocation: true
---

Invoke the `audit-apple-privacy` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty). Pass `--diff-only` through if present.
