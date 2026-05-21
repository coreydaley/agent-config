---
description: >-
  Dual-agent security audit for backend services, web applications, IaC,
  CI/CD workflows, and agent-config repos. Runs real security tooling
  (gitleaks, semgrep, dep auditors, trivy, actionlint), then Claude and
  Codex review independently against OWASP/CWE-anchored categories,
  synthesize, devil's advocate pass, output as findings report with
  Critical findings broken out as Immediate Action. For native Apple
  platforms, use /audit-security-apple.
disable-model-invocation: true
---

Invoke the `audit-security-web-application` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty). Pass `--diff-only` through if present.
