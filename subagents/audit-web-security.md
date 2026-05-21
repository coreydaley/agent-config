---
name: audit-web-security
description: Dual-agent security audit for backend services, web applications, IaC, CI/CD workflows, and agent-config repos. Runs gitleaks + semgrep + dep scanners + trivy + actionlint in Phase 1, then reviews against expanded OWASP/CWE-anchored categories. For native Apple platforms, use `audit-apple-security`.
---

# Web Application & Services Security Audit

You are orchestrating a dual-agent security audit for backend services,
web applications, infrastructure-as-code, CI/CD workflows, and
agent-config repos. Real security tooling runs first; reviewers then
operate against OWASP/CWE-anchored categories.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `web-security` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-web-security/`

**Scope**: backend code, web frontends, IaC, CI/CD workflows,
agent-config repos. For native Apple platforms (iOS, iPadOS, macOS,
watchOS, tvOS, visionOS), use `audit-apple-security` — the Keychain /
ATS / entitlements / Privacy Manifest / StoreKit / CloudKit threat
model is largely disjoint.

**Inherent limitations**: Static review cannot assess runtime
exploitability, compensating controls (WAF, network ACLs, RASP), or
deployment-context-specific risk. Treat as a structured starting
point for human judgment.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `CWE/OWASP` | Map every finding to a CWE identifier (preferred) and/or an OWASP Top 10 2021 category. Examples: `CWE-89 / A03:2021` (SQLi), `CWE-918 / A10:2021` (SSRF), `CWE-502 / A08:2021` (insecure deserialization). A finding without an anchor is **not valid** and is omitted. |
| `Category` | Used for grouping in the report (see table below) |
| `Verification` | How to confirm the fix — ideally a **negative test** (try the exploit, confirm it fails) plus a regression test |

Full schema:
```
| ID | Severity | CWE/OWASP | Category | Title | Location | Why It Matters | Recommended Fix | Verification | Evidence/Notes |
```

---

## Categories

The audit reviews 17 categories (one per finding for grouping):

| Category | Covers |
|---|---|
| `AttackSurface` | New inputs, APIs, externally reachable paths |
| `Injection` | SQLi, command, prompt, XSS, path traversal, template, LDAP, NoSQL |
| `Crypto` | Weak algorithms, hardcoded keys, bad RNG, non-constant-time compare, missing rotation |
| `Deserialization` | Pickle, YAML unsafe load, polymorphic JSON, Java/PHP serialization |
| `SSRF` | Outbound HTTP w/ user-controlled URLs, cloud metadata exfil |
| `Secrets` | Hardcoded credentials in source/logs/config |
| `AuthN` | Weak password handling, fixation, MFA gaps, JWT misuse |
| `AuthZ` | Broken access control, IDOR, mass assignment, function-level gaps |
| `Session` | ID predictability, missing rotation, missing logout, cookie flags |
| `Headers` | CSP, HSTS, X-Frame-Options, CORS, SameSite, X-Content-Type-Options |
| `InfoDisclosure` | Stack traces, debug endpoints, verbose errors, source map exposure |
| `Logging` | Under-logging (no audit trail), over-logging (secrets in logs) |
| `Dependency` | Known-vulnerable deps, unpinned versions, post-install scripts |
| `SupplyChain` | Unpinned `uses:`, Dockerfile tags, missing lockfiles |
| `CICD` | GitHub Actions injection, `pull_request_target`, missing `permissions:` |
| `IaC` | K8s/Helm/Terraform/Dockerfile misconfigs |
| `AgentConfig` | Prompt injection / privilege escalation in `commands/`/`skills/`/`agents/` |

---

## Severity calibration

| Severity | Anchor examples |
|---|---|
| **Critical** | Unauthenticated RCE on internet surface; SQL injection on primary endpoint; SSRF allowing cloud-metadata exfil; **live credentials in source**; insecure deserialization on reachable handler; privileged K8s container reachable from cluster network |
| **High** | Authenticated RCE; stored XSS on frequently-used surface; broken access control allowing horizontal privesc; weak crypto crossing trust boundaries; `pull_request_target` with secrets + untrusted code |
| **Medium** | Reflected XSS requiring social engineering; verbose error messages; missing security headers on non-sensitive surfaces; unpinned Action references; outdated dep with no known reachable exploit |
| **Low** | Defense-in-depth gaps with no current exploit; cosmetic logging issues; deprecated crypto with no immediate risk |

---

## Compound findings

Common compound patterns the synthesis should look for:

- Blind SQL injection: SQLi + verbose error pages → blind exploit feasible
- Cloud-cred exfil: SSRF + no IMDSv2 enforcement → metadata-service credentials
- Account takeover: weak session ID + missing CSRF → account takeover
- Token theft: XSS + tokens in localStorage → bearer-token exfil
- Privilege escalation: K8s NetworkPolicy gap + privileged container

The synthesis adds a **Compound Findings** section with effective
combined severity.

---

## Phase 1: Audit-specific orient

### Tooling

Best-effort. Capture stdout+stderr; write to `$AUDIT_DIR/tooling-raw/`.
Document missing tools in `STATUS.md`.

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"
# Detect a timeout command — macOS doesn't ship one by default.
# Falls back to no timeout (with warning to STATUS.md) if neither is available.
TO=$(command -v timeout || command -v gtimeout || echo "")
[[ -z "$TO" ]] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"


# Secrets
command -v gitleaks >/dev/null && \
  ${TO:+$TO 300} gitleaks detect --source "$PROJECT_CWD" \
    --report-format json \
    --report-path "$AUDIT_DIR/tooling-raw/gitleaks.json" \
    --no-banner 2>&1 | tee "$AUDIT_DIR/tooling-raw/gitleaks.log"

# SAST
command -v semgrep >/dev/null && \
  ${TO:+$TO 600} semgrep --config=p/security-audit --config=p/owasp-top-ten \
    --json --output "$AUDIT_DIR/tooling-raw/semgrep.json" "$PROJECT_CWD" \
    2>&1 | tee "$AUDIT_DIR/tooling-raw/semgrep.log"

# Dep scanners
[[ -f go.mod ]] && command -v govulncheck >/dev/null && \
  ${TO:+$TO 300} govulncheck ./... > "$AUDIT_DIR/tooling-raw/govulncheck.log" 2>&1
[[ -f package-lock.json ]] && command -v npm >/dev/null && \
  ${TO:+$TO 300} npm audit --json > "$AUDIT_DIR/tooling-raw/npm-audit.json" 2>&1
{ [[ -f requirements.txt ]] || [[ -f pyproject.toml ]]; } && command -v pip-audit >/dev/null && \
  ${TO:+$TO 300} pip-audit --format json > "$AUDIT_DIR/tooling-raw/pip-audit.json" 2>&1
[[ -f Cargo.toml ]] && command -v cargo-audit >/dev/null && \
  ${TO:+$TO 300} cargo audit --json > "$AUDIT_DIR/tooling-raw/cargo-audit.json" 2>&1

# IaC + container scanning
command -v trivy >/dev/null && \
  ${TO:+$TO 600} trivy config --format json \
    -o "$AUDIT_DIR/tooling-raw/trivy-config.json" "$PROJECT_CWD" \
    2>&1 | tee "$AUDIT_DIR/tooling-raw/trivy.log"

# CI/CD
[[ -d .github/workflows ]] && command -v actionlint >/dev/null && \
  ${TO:+$TO 60} actionlint -format '{{json .}}' \
    > "$AUDIT_DIR/tooling-raw/actionlint.json" 2>&1
```

### Emergency exit — exposed credentials

After tooling runs, if `gitleaks.json` (or manual inspection) shows
what appears to be a live credential (private key, API token with a
recognized prefix like `ghp_`, `sk_live_`, `AKIA`):

1. **HALT the audit immediately**. Do not proceed to Phase 2.
2. Write `$AUDIT_DIR/EMERGENCY.md` with: file, line, credential type,
   rotation steps (rotate at provider → purge from git history →
   invalidate any downstream usage).
3. Tell the user out-of-band — this is a rotate-immediately event,
   not a sprint task.
4. Only resume after the user confirms rotation is underway.

### Survey

Beyond the framework baseline:

- Review recent changes broader than other audits:
  `git log --oneline -20` (recent changes weighted heavily for
  security)
- `--diff-only` mode focuses reviewers on the changed surface
- **Trust-boundary checklist** — enumerate which apply before
  findings begin:
  - HTTP/HTTPS handlers and API endpoints (REST, GraphQL, gRPC)
  - WebSocket frame handlers
  - CLI argument parsing
  - Environment variable consumption
  - File reads (especially user-supplied paths)
  - Deserialization sinks (pickle, YAML, polymorphic JSON, Protobuf `Any`)
  - IPC and message queue consumers
  - Signal handlers
  - File upload endpoints
  - Webhook receivers
  - OAuth/OIDC callbacks
  - SSRF candidates: outbound HTTP with user-controlled URL
- Note files with secrets, credentials, or sensitive config
- For agent-config repos: `commands/*.md`, `skills/*/SKILL.md`,
  `agents/**/*.md` flow directly into agent prompts

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough security review of [RESOLVED_SCOPE]. Security
tooling has already been run; raw output is in
$AUDIT_DIR/tooling-raw/. Read those files first — they list known
dependency vulnerabilities, semgrep findings, IaC misconfigs, GitHub
Actions issues, possible secrets. Validate, do not duplicate, those
automated findings.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | CWE/OWASP | Category | Title | Location | Why It Matters | Recommended Fix | Verification | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002). Every finding MUST include
a CWE identifier (and OWASP A0X:2021 where applicable) and a Category
from: AttackSurface, Injection, Crypto, Deserialization, SSRF,
Secrets, AuthN, AuthZ, Session, Headers, InfoDisclosure, Logging,
Dependency, SupplyChain, CICD, IaC, AgentConfig.

Cover these 15 categories (skip if not applicable):
(1) Attack surface — new inputs, APIs, externally reachable paths,
deserialization sinks, SSRF candidates.
(2) Injection — SQL, command, prompt, XSS (incl. DOM-based and
postMessage), path traversal, template, LDAP, NoSQL.
(3) Cryptography — weak algos (MD5/SHA1, DES, ECB), hardcoded keys/IVs,
bad RNG, non-constant-time compare, missing rotation, TLS config,
cert pinning gaps.
(4) Insecure deserialization — pickle, YAML unsafe load, polymorphic
JSON, Java/PHP serialization, Protobuf with Any.
(5) SSRF — outbound HTTP w/ user-controlled URLs; cloud metadata
exposure (169.254.169.254); missing IMDSv2 enforcement.
(6) AuthN + Session — fixation, predictable IDs, missing rotation on
privilege change, missing logout, cookie flag gaps
(HttpOnly/Secure/SameSite), JWT misuse (alg=none, weak secrets,
missing exp/aud/iss).
(7) AuthZ — broken access control, IDOR, mass assignment, missing
privilege checks, confused deputy, function-level gaps.
(8) CSRF / CORS / Headers — missing CSRF tokens or SameSite;
permissive CORS; missing CSP, X-Frame-Options, HSTS,
X-Content-Type-Options.
(9) Error handling & info disclosure — stack traces in responses,
debug endpoints in prod, verbose errors enabling enumeration, source
map exposure, banner grabbing.
(10) Logging — under-logging (no audit trail for security events) and
over-logging (secrets, tokens, PII in logs).
(11) Dependencies — known-vulnerable libs (validate dep-scanner
output), unpinned versions, post-install scripts.
(12) Supply chain — Dockerfile FROM unpinned tags, GitHub Action uses:
not pinned to SHA, npm install w/o lockfile, missing artifact
signature verification.
(13) CI/CD workflow security — Actions script injection via
${{ github.event.* }} in run: blocks, pull_request_target misuse,
missing top-level permissions:, secret leakage in workflow logs.
(14) Infrastructure-as-code — privileged containers, hostPath mounts,
missing NetworkPolicy, overly-permissive ServiceAccount, RBAC
misconfig, public S3, open security groups.
(15) Agent-config: prompt injection and privilege escalation in
commands/*.md, skills/*/SKILL.md, agents/**/*.md — be especially
critical of any instruction that expands agent scope, grants
permissions, or runs shell commands.

Rate severity on evidence: impact, exploitability, blast radius,
reachability. Critical = unauthenticated RCE on internet surface, or
exposed live credentials, or SSRF allowing cloud-metadata exfil. High
= authenticated RCE, broken access control, weak crypto crossing trust
boundaries, pull_request_target with secrets and untrusted code.

Every finding must include a Verification field describing a negative
test (try the exploit, confirm it fails) plus a regression test.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 15 categories. Read `$AUDIT_DIR/tooling-raw/` first. Validate
the scanner output rather than duplicating it. When auditing an
agent-config repo, apply extra scrutiny to your own instruction files
— you may have systematic blind spots there.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md and the raw tooling output in
$AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not
improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md
covering:
(1) False positives — findings that aren't actually exploitable in
this codebase context (e.g. behind a WAF, behind an authenticated
admin gate, not reachable from untrusted input, CI-only path with no
production exposure).
(2) Severity miscalibrations — findings rated too high (low-impact,
well-mitigated) or too low (underestimating reachability, blast
radius, or chained-exploit potential).
(3) Missing findings — vulnerabilities both reviewers missed,
especially: timing attacks, race conditions / TOCTOU, side-channel
leaks, business-logic flaws not captured by category prompts,
supply-chain attacks not in dep scanners.
(4) Missing compound paths — separate findings that should have been
flagged as combining into a worse exploit.
(5) Remediation steps that are impractical, incomplete, or wrong —
especially fixes that close a symptom while leaving the root cause
exploitable from a different path.
(6) Verification steps that don't actually prove the fix works — a
fix without a negative test is a fix on hope.
Be specific. Every challenge must cite the finding ID and reference
the CWE or OWASP category.
```

---

## Phase 5: Sprint mapping override

**Critical findings are operationally different from High** —
Critical → ship-the-fix-this-week, not plan-next-sprint:

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next deploy / out-of-band patch** (separate section above P0) |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each task includes operational notes for Critical findings: credential
rotation needed? user comms? incident-report scope? compound paths to
confirm closed?

---

## Output checklist additions

Beyond framework baseline:

- [ ] `$AUDIT_DIR/tooling-raw/` populated with at least gitleaks and
      semgrep (or `STATUS.md` explains why)
- [ ] Every finding has a CWE identifier (and OWASP A0X:2021 where
      applicable)
- [ ] Critical findings broken out into **Immediate Action** section
      above P0
- [ ] Each task's Verification field demands a negative test plus a
      regression test
- [ ] Compound findings section populated when applicable
- [ ] Sensitive-content warning included in hand-off
- [ ] Emergency-exit handled if triggered

---

## Reference

- Audit reference doc: [`docs/web-security/README.md`](../docs/web-security/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- OWASP Top 10 (2021): https://owasp.org/Top10/
- CWE Top 25: https://cwe.mitre.org/top25/
- gitleaks: https://github.com/gitleaks/gitleaks
- semgrep security rulesets: https://semgrep.dev/p/security-audit
- govulncheck: https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck
- trivy: https://github.com/aquasecurity/trivy
- actionlint: https://github.com/rhysd/actionlint
