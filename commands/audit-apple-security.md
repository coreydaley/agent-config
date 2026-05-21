---
description: >-
  Dual-agent Apple platform security audit — Claude and Codex review
  native Apple apps (iOS/iPadOS/macOS/watchOS/tvOS/visionOS) independently
  against Apple's platform-specific threat model: Keychain, ATS,
  entitlements, App Sandbox, Hardened Runtime, Privacy Manifest, StoreKit,
  CloudKit, WKWebView, code signing. Runs available tooling (gitleaks,
  semgrep, optionally xcodebuild analyze), synthesize, devil's advocate
  pass, output as findings report with Critical findings broken out as
  Immediate Action. For backend services / web apps, use
  /audit-web-security.
disable-model-invocation: true
---

Invoke the `audit-apple-security` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty). Pass `--diff-only` through if present.
