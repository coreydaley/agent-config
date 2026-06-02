# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/`, scan for emergency-exit conditions, build a brief orientation note. **Web security has rich Phase 1 tooling AND an emergency-exit gate** — exercise both.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Run Phase 1 tooling

Run what's available, document what's missing in `STATUS.md`. **Never block on a missing tool.** Capture stdout+stderr; write to `$AUDIT_DIR/tooling-raw/`.

```bash
# Secrets — gitleaks. Required emergency-exit trigger source.
if command -v gitleaks >/dev/null; then
  ${TO:+$TO 300} gitleaks detect --source "$PROJECT_CWD" \
    --report-format json \
    --report-path "$AUDIT_DIR/tooling-raw/gitleaks.json" \
    --no-banner 2>&1 | tee "$AUDIT_DIR/tooling-raw/gitleaks.log" || true
else
  echo "⚠️ gitleaks not installed — secret scanning skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# SAST — semgrep with security-audit + OWASP Top 10 rulesets.
if command -v semgrep >/dev/null; then
  ${TO:+$TO 600} semgrep --config=p/security-audit --config=p/owasp-top-ten \
    --json --output "$AUDIT_DIR/tooling-raw/semgrep.json" "$PROJECT_CWD" \
    2>&1 | tee "$AUDIT_DIR/tooling-raw/semgrep.log" || true
else
  echo "⚠️ semgrep not installed — SAST skipped" \
    >> "$AUDIT_DIR/tooling-raw/STATUS.md"
fi

# Dep scanners — run the ones that match the lockfiles present.
if [ -f "$PROJECT_CWD/go.mod" ] && command -v govulncheck >/dev/null; then
  ( cd "$PROJECT_CWD" && ${TO:+$TO 300} govulncheck ./... ) \
    > "$AUDIT_DIR/tooling-raw/govulncheck.log" 2>&1 || true
fi
if [ -f "$PROJECT_CWD/package-lock.json" ] && command -v npm >/dev/null; then
  ( cd "$PROJECT_CWD" && ${TO:+$TO 300} npm audit --json ) \
    > "$AUDIT_DIR/tooling-raw/npm-audit.json" 2>&1 || true
fi
if { [ -f "$PROJECT_CWD/requirements.txt" ] || [ -f "$PROJECT_CWD/pyproject.toml" ]; } && command -v pip-audit >/dev/null; then
  ( cd "$PROJECT_CWD" && ${TO:+$TO 300} pip-audit --format json ) \
    > "$AUDIT_DIR/tooling-raw/pip-audit.json" 2>&1 || true
fi
if [ -f "$PROJECT_CWD/Cargo.toml" ] && command -v cargo-audit >/dev/null; then
  ( cd "$PROJECT_CWD" && ${TO:+$TO 300} cargo audit --json ) \
    > "$AUDIT_DIR/tooling-raw/cargo-audit.json" 2>&1 || true
fi

# IaC + container scanning — trivy on the working tree.
if command -v trivy >/dev/null; then
  ${TO:+$TO 600} trivy config --format json \
    -o "$AUDIT_DIR/tooling-raw/trivy-config.json" "$PROJECT_CWD" \
    2>&1 | tee "$AUDIT_DIR/tooling-raw/trivy.log" || true
fi

# CI/CD — actionlint on GitHub Actions workflows.
if [ -d "$PROJECT_CWD/.github/workflows" ] && command -v actionlint >/dev/null; then
  ( cd "$PROJECT_CWD" && ${TO:+$TO 60} actionlint -format '{{json .}}' ) \
    > "$AUDIT_DIR/tooling-raw/actionlint.json" 2>&1 || true
fi
```

### 2. Emergency-exit check

If `gitleaks.json` (or manual inspection) shows what appears to be a **live credential** (private key block, GitHub PAT `ghp_*`, Stripe `sk_live_*`, AWS `AKIA*`, GCP service account JSON, Slack token, OAuth client secret, database connection string with embedded password), halt the audit before Phase 2.

```bash
EMERGENCY=0
if [ -s "$AUDIT_DIR/tooling-raw/gitleaks.json" ]; then
  if command -v jq >/dev/null && jq -e '. | length > 0' \
       "$AUDIT_DIR/tooling-raw/gitleaks.json" >/dev/null 2>&1; then
    # Filter to high-confidence hits; gitleaks's own rules are the source.
    HITS=$(jq -r '.[] | select(.RuleID | test("private-key|github-pat|github-oauth|stripe|aws-access|gcp-service-account|slack-token|generic-api-key|database-url|oauth-client-secret")) | .RuleID' \
           "$AUDIT_DIR/tooling-raw/gitleaks.json" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$HITS" -gt 0 ]; then EMERGENCY=1; fi
  fi
fi
```

If `EMERGENCY=1`, take the `emergency_exit` outgoing edge. Manually re-confirm before exiting — gitleaks has known false positives on vendored source, test fixtures, and example credentials in docs / readmes.

### 3. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and detected stack (languages, frameworks, package manifests)
- Recent changes weighted heavily: `git log --oneline -20`
- Web-security trust-boundary checklist — enumerate which apply before findings begin:
  - HTTP/HTTPS handlers and API endpoints (REST, GraphQL, gRPC)
  - WebSocket frame handlers
  - CLI argument parsing
  - Environment variable consumption
  - File reads (especially user-supplied paths)
  - Deserialization sinks (pickle, YAML unsafe load, polymorphic JSON, Protobuf `Any`)
  - IPC and message queue consumers
  - File upload endpoints
  - Webhook receivers
  - OAuth/OIDC callbacks
  - SSRF candidates: outbound HTTP with user-controlled URL
  - IaC surface: K8s manifests, Helm charts, Terraform, Dockerfile
  - CI/CD surface: GitHub Actions workflows, especially `pull_request_target`
- For agent-config repos: `commands/*.md`, `skills/*/SKILL.md`, `agents/**/*.md` flow directly into agent prompts — apply prompt-injection scrutiny
- Which Phase 1 tools ran successfully vs. which are missing

This is for the user's situational awareness, not a persisted artifact.

### 4. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/` populated with whatever tools were available
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools
- Walker state has `emergency_exit` flag set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Normal path. Phase 1 ran, no emergency triggered.
- **`emergency`** → `emergency_exit`. `gitleaks` matched a high-confidence live-credential rule; **the audit halts before Phase 2.**

```bash
if [ "$EMERGENCY" -eq 1 ]; then
  scripts/walk.sh transition --state "$STATE" --from orient --to emergency_exit --condition emergency
else
  scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
fi
```

## Failure modes

- A tool times out → captured in its `.log` file; orient proceeds. Phase 2 reviewers see the partial output.
- All tooling fails / missing → `STATUS.md` documents the degradation; orient still proceeds. Phase 2 reviewers do more manual code reading.
- gitleaks reports a hit that turns out to be a false positive (vendored source, doc example, test fixture) → human judgment call before taking the `emergency` edge; if uncertain, take `proceed` and let the reviewers re-flag it as a finding rather than halting the audit.
