---
name: audit-security-web-application
description: Dual-agent security audit for backend services, web applications, infrastructure-as-code, CI/CD workflows, and agent-config repos. Runs real security tooling (secret scanners, dep auditors, semgrep, K8s scanners), then Claude and Codex review independently against expanded OWASP/CWE-anchored categories, synthesize, devil's advocate pass, output as findings report. For native Apple platforms (iOS/macOS/watchOS/tvOS/visionOS), use `audit-security-apple` instead. Invoke with a scope path or leave empty to audit the current working directory.
---

# Web Application & Services Security Audit: Dual-Agent Review

You are orchestrating a dual-agent security audit for backend services,
web applications, infrastructure-as-code, CI/CD workflows, and
agent-config repos. Real security tooling runs first; Claude and Codex
then review independently against OWASP/CWE-anchored categories,
findings are synthesized, Codex attacks the synthesis, and the final
output is a sprint document written to `$AUDIT_DIR/REPORT.md`.

For **native Apple platforms** (iOS, iPadOS, macOS, watchOS, tvOS,
visionOS), use `audit-security-apple` — the threat model (Keychain,
ATS, entitlements, Privacy Manifest, StoreKit, CloudKit ACLs) is
largely disjoint from web/backend security.

The scope to audit is provided in your input prompt. If no scope is
specified, audit the current working directory.

## Scope Handling

Parse your input prompt for a path or paths to audit. Examples:
- No path specified → scope is the current working directory
- `src/auth` → scope is `src/auth`
- `commands/ skills/` → scope is multiple paths
- `--diff-only` → scope is files changed in `git diff main...HEAD`

Scope is validated as a path in Phase 1 before being used anywhere else —
raw user input is never interpolated into shell strings.

## Workflow Overview

This is a **5-phase workflow** with an emergency-exit early in Phase 1:

1. **Orient** — Determine scope, run security tooling (secrets, deps,
   SAST, IaC), enumerate trust boundaries, **halt early if exposed
   credentials are found in source**
2. **Independent Reviews** — Claude and Codex review in parallel,
   grounded in the tooling output from Phase 1
3. **Synthesis** — Deduplicate findings; flag agreements as higher
   confidence; calibrate severity against the rubric; note compound
   findings (separate weaknesses that chain into a worse exploit)
4. **Devil's Advocate** — Codex attacks the synthesis for false
   positives, severity miscalibrations, and gaps
5. **Report Output** — Produce `$AUDIT_DIR/REPORT.md` with findings as
   tasks, with Critical findings broken out as "Immediate Action"
   above P0

**Inherent limitations**: Static review cannot assess runtime
exploitability, compensating controls (WAF, network ACLs, RASP), or
deployment-context-specific risk. Treat the output as a structured
starting point for human judgment, not a guarantee of full coverage.

---

## Finding Schema

All intermediate audit files must use this table format so synthesis
and devil's advocate phases operate on consistent data:

```
| ID | Severity | CWE/OWASP | Category | Title | Location | Why It Matters | Recommended Fix | Verification | Evidence/Notes |
|----|----------|-----------|----------|-------|----------|----------------|-----------------|--------------|----------------|
| X001 | High | CWE-89 / A03:2021 | Injection | Short title | path/to/file:line | Impact explanation | Concrete fix | How to prove it's fixed | Code quote |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis canonical)

**CWE/OWASP column**: Map every finding to a named weakness from
[CWE](https://cwe.mitre.org/) (preferred — more specific) and/or the
[OWASP Top 10 2021](https://owasp.org/Top10/). Examples:
- `CWE-89 / A03:2021` — SQL injection
- `CWE-78` — OS command injection
- `CWE-918 / A10:2021` — SSRF
- `CWE-502 / A08:2021` — Insecure deserialization
- `CWE-200 / A05:2021` — Information exposure
- `CWE-285 / A01:2021` — Broken access control
- `CWE-352 / A05:2021` — CSRF
- `CWE-798` — Hardcoded credentials
- `CWE-327` — Broken/risky crypto

A finding without a named CWE or OWASP category is not a valid finding
and must be omitted.

**Category column** (one per finding) — used for grouping in the report:

| Category | Covers |
|---|---|
| `AttackSurface` | New inputs, APIs, externally reachable paths, exposed endpoints |
| `Injection` | SQLi, command injection, XSS, prompt injection, path traversal, template injection, LDAP, NoSQL |
| `Crypto` | Weak algorithms, hardcoded keys, bad RNG, non-constant-time comparison, missing key rotation |
| `Deserialization` | Pickle, YAML unsafe load, polymorphic JSON, Java/PHP serialization |
| `SSRF` | Outbound HTTP with user-controlled URLs (esp. metadata service exfil) |
| `Secrets` | Hardcoded credentials, secrets in logs, secrets in config, env var leakage |
| `AuthN` | Authentication: weak password handling, session fixation, missing MFA enforcement, JWT misuse |
| `AuthZ` | Authorization: broken access control, IDOR, mass assignment, missing privilege checks, confused deputy |
| `Session` | Session ID predictability, missing rotation on privilege change, missing logout, cookie flags |
| `Headers` | CSP, X-Frame-Options, HSTS, CORS, SameSite, X-Content-Type-Options |
| `InfoDisclosure` | Stack traces, debug endpoints, verbose errors, source map exposure, banner grabbing |
| `Logging` | Under-logging (no audit trail), over-logging (secrets in logs), tampering risk |
| `Dependency` | Known-vulnerable deps, unpinned versions, post-install scripts, lockfile drift |
| `SupplyChain` | Build provenance, unpinned `uses:`, Dockerfile base image tags, package signing |
| `CICD` | GitHub Actions injection, `pull_request_target` misuse, missing `permissions:`, secret leakage in logs |
| `IaC` | Terraform/Helm/K8s manifest misconfigs — privileged containers, hostPath, missing NetworkPolicy, overly-permissive ServiceAccount, public S3, open security groups |
| `AgentConfig` | Prompt injection and privilege escalation in `commands/*.md`, `skills/*/SKILL.md`, `agents/**/*.md` files |

**Severity levels:** Critical, High, Medium, Low

### Severity Calibration

Severity is assessed on **evidence**, not impression:

- **Impact** — what does an exploit achieve? (data exfil, RCE, account
  takeover, denial-of-service, privilege escalation)
- **Exploitability** — what attacker capability is required?
  (unauthenticated remote, authenticated user, local network, physical)
- **Blast radius** — how many users / systems / records are affected?
- **Reachability** — is the vulnerable code reachable from untrusted
  input, or is it gated behind controls that already mitigate it?

Severity anchors (starting point — override based on the four factors
above):

| Severity | Anchor examples |
|---|---|
| **Critical** | Unauthenticated RCE on internet-exposed surface; SQL injection on a primary user endpoint; SSRF allowing cloud-metadata exfil; exposed live credentials in source; insecure deserialization of untrusted input on a reachable handler; privileged K8s container reachable from the cluster network |
| **High** | Authenticated RCE; stored XSS on a frequently-used surface; broken access control allowing horizontal privilege escalation; weak crypto on data that crosses trust boundaries; CSRF on state-changing endpoints; `pull_request_target` workflow that runs untrusted PR code with secrets in context |
| **Medium** | Reflected XSS requiring social-engineering; verbose error messages enabling enumeration; missing security headers (CSP, HSTS) on non-sensitive surfaces; unpinned GitHub Action `uses:` reference; outdated dependency with no known reachable exploit path |
| **Low** | Defense-in-depth gaps with no current exploit; cosmetic logging issues; deprecated-but-functional crypto with no immediate risk; informational findings |

Agreement between reviewers raises **confidence**, not severity.
Severity is also independent of remediation cost.

### Compound Findings

When two or more separate findings combine to enable a worse exploit
than either alone, the synthesis must add a `Compounded By` note:

- Blind SQL injection: SQLi (`S001`) + verbose error pages (`S007`) →
  exploit is feasible
- SSRF + cloud-metadata service exposure: SSRF (`S003`) + no IMDSv2
  enforcement (`S012`) → credential exfil

Reviewers should call these out explicitly during synthesis rather than
treating each in isolation.

---

## Phase 1: Orient

**Goal**: Validate scope, **run real security tooling**, enumerate
trust boundaries, halt early if exposed credentials are found, and
determine the output location.

### Orient Steps

1. **Validate and resolve scope** from the input prompt:
   - If no path specified: scope is the current working directory
   - If a path is provided: verify the path exists
   - If `--diff-only`: scope is files changed in `git diff main...HEAD`
     (or `upstream/main...HEAD` if `upstream` remote exists)
   - Scope should exclude `build/`, `dist/`, `node_modules/`, `vendor/`,
     generated files, vendored/third-party code, and binary files
     unless explicitly included
   - Store the resolved scope path — do not use raw input text in any
     Codex exec prompt string

2. **Determine output location**:
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   AUDIT_DIR="$REPORTS_BASE/audits/$REPORT_TS-security-web-application"
   PROJECT_CWD="$(pwd)"
   mkdir -p "$AUDIT_DIR/tooling-raw"
   ```

3. **Run security tooling** (best-effort; capture stdout+stderr; document
   what ran in `$AUDIT_DIR/tooling-raw/STATUS.md`). Pick the commands
   matching the detected stack. **Always run with a timeout** (e.g.
   `timeout 300 …`):

   ```bash
   # Secret scanning (always run if gitleaks is installed)
   command -v gitleaks >/dev/null && \
     timeout 300 gitleaks detect --source "$PROJECT_CWD" --report-format json \
       --report-path "$AUDIT_DIR/tooling-raw/gitleaks.json" \
       --no-banner 2>&1 | tee "$AUDIT_DIR/tooling-raw/gitleaks.log"

   # Static analysis (semgrep with security rulesets)
   command -v semgrep >/dev/null && \
     timeout 600 semgrep --config=p/security-audit --config=p/owasp-top-ten \
       --json --output "$AUDIT_DIR/tooling-raw/semgrep.json" "$PROJECT_CWD" \
       2>&1 | tee "$AUDIT_DIR/tooling-raw/semgrep.log"

   # Go dependency vulnerabilities
   [[ -f go.mod ]] && command -v govulncheck >/dev/null && \
     timeout 300 govulncheck ./... > "$AUDIT_DIR/tooling-raw/govulncheck.log" 2>&1

   # Node / npm dependency audit
   [[ -f package-lock.json ]] && command -v npm >/dev/null && \
     timeout 300 npm audit --json > "$AUDIT_DIR/tooling-raw/npm-audit.json" 2>&1

   # Python dependency audit
   [[ -f requirements.txt || -f pyproject.toml ]] && command -v pip-audit >/dev/null && \
     timeout 300 pip-audit --format json > "$AUDIT_DIR/tooling-raw/pip-audit.json" 2>&1

   # Rust dependency audit
   [[ -f Cargo.toml ]] && command -v cargo-audit >/dev/null && \
     timeout 300 cargo audit --json > "$AUDIT_DIR/tooling-raw/cargo-audit.json" 2>&1

   # Kubernetes / Docker / Terraform scanning
   command -v trivy >/dev/null && \
     timeout 600 trivy config --format json -o "$AUDIT_DIR/tooling-raw/trivy-config.json" \
       "$PROJECT_CWD" 2>&1 | tee "$AUDIT_DIR/tooling-raw/trivy.log"

   # GitHub Actions workflow lint (security)
   [[ -d .github/workflows ]] && command -v actionlint >/dev/null && \
     timeout 60 actionlint -format '{{json .}}' \
       > "$AUDIT_DIR/tooling-raw/actionlint.json" 2>&1
   ```

   If a tool isn't installed, isn't applicable, or fails: write a line
   to `$AUDIT_DIR/tooling-raw/STATUS.md` and continue. Both reviewers
   must be told what tooling ran and what's missing.

4. **🚨 EMERGENCY EXIT — exposed credentials**:

   After Phase 1 step 3, if `gitleaks.json` (or manual inspection)
   shows what appears to be a live credential (private key, API token
   with a recognized prefix like `ghp_`, `sk_live_`, `AKIA`, etc.)
   committed to the working tree:

   - **HALT the audit immediately**. Do not proceed to Phase 2.
   - Write `$AUDIT_DIR/EMERGENCY.md` with: which file, which line,
     which credential type was matched, and the rotation steps
     (rotate at provider → purge from git history → invalidate any
     downstream usage).
   - Tell the user out-of-band in the conversation: this is a
     rotate-immediately event, not a finding to deduplicate and
     prioritize next sprint.
   - Only resume the full audit after the user has confirmed rotation
     is underway.

5. **Survey the scope and enumerate trust boundaries**:
   - Review recent changes: `git log --oneline -20` (broader than
     other audits — recent changes are weighted heavily for security)
   - For `--diff-only` mode, focus reviewers on the changed surface
   - **Explicit trust-boundary checklist** (enumerate which apply,
     before findings begin):
     - HTTP/HTTPS handlers and API endpoints (REST, GraphQL, gRPC)
     - WebSocket frame handlers
     - CLI argument parsing
     - Environment variable consumption
     - File reads (especially user-supplied paths)
     - Deserialization sinks (pickle, YAML, polymorphic JSON,
       Protocol Buffers with `Any`)
     - IPC and message queue consumers (Kafka, RabbitMQ, SQS, Redis pub/sub)
     - Signal handlers
     - File upload endpoints
     - Webhook receivers
     - OAuth/OIDC callbacks
     - SSRF candidates: outbound HTTP with user-controlled URL/path
   - Note files with secrets, credentials, or sensitive config
   - For agent-config repos: `commands/*.md`, `skills/*/SKILL.md`,
     `agents/**/*.md` — these flow directly into agent system prompts

### Orient Deliverable

A brief orientation note (5-8 bullets) covering:
- Resolved scope and what it includes/excludes (note if `--diff-only`)
- Tooling that ran successfully vs. tooling missing (with link to
  `tooling-raw/STATUS.md`)
- **Whether the emergency-exit triggered** (yes/no — if yes, audit
  halted here)
- Enumerated trust-crossing surfaces (the checklist above, filtered to
  what's present)
- Audit output directory (`AUDIT_DIR`)
- Any immediately obvious high-priority areas surfaced by tooling

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent security perspectives, both grounded in
the tooling output from Phase 1.

### Step 1 — Launch Codex in Background

The flags below are non-negotiable; see [`lib/codex-invocation.md`](../lib/codex-invocation.md) for per-flag rationale and failure modes. `--add-dir` points at `$AUDIT_DIR` so Codex can write its artifact under `~/Reports/`; `-C` points at `$PROJECT_CWD` so Codex reads the code being audited.

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "Perform a thorough security review of [RESOLVED_SCOPE]. \
  Security tooling has already been run; raw output is in \
  $AUDIT_DIR/tooling-raw/. Read those files first — they list \
  known dependency vulnerabilities, semgrep findings, IaC misconfigs, \
  GitHub Actions issues, and possible secrets. Validate, do not \
  duplicate, those automated findings. \
  Write all findings to $AUDIT_DIR/codex.md using this exact \
  table format for each finding: \
  | ID | Severity | CWE/OWASP | Category | Title | Location | Why It Matters | Recommended Fix | Verification | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). Every finding MUST include \
  a CWE identifier (and OWASP A0X:2021 where applicable) and a Category \
  from this set: AttackSurface, Injection, Crypto, Deserialization, \
  SSRF, Secrets, AuthN, AuthZ, Session, Headers, InfoDisclosure, \
  Logging, Dependency, SupplyChain, CICD, IaC, AgentConfig. \
  Cover these categories (skip any not applicable to the scope): \
  (1) Attack surface and trust boundaries — new inputs, APIs, \
  externally reachable paths, deserialization sinks, SSRF candidates. \
  (2) Injection — SQL, command, prompt, XSS (including DOM-based and \
  postMessage), path traversal, template injection, LDAP, NoSQL. \
  (3) Cryptography — weak algorithms (MD5/SHA1, DES, ECB), hardcoded \
  keys/IVs, bad RNG, non-constant-time comparison, missing key rotation, \
  TLS config issues, certificate pinning gaps. \
  (4) Insecure deserialization — pickle, YAML unsafe load, polymorphic \
  JSON, Java/PHP serialization, Protocol Buffers with Any. \
  (5) SSRF — outbound HTTP with user-controlled URLs; cloud metadata \
  service exposure (169.254.169.254); missing IMDSv2 enforcement. \
  (6) Authentication and session management — fixation, predictable IDs, \
  missing rotation on privilege change, missing logout, cookie flag \
  gaps (HttpOnly/Secure/SameSite), JWT misuse (alg=none, weak secrets, \
  missing exp/aud/iss). \
  (7) Authorization — broken access control, IDOR, mass assignment, \
  missing privilege checks, confused deputy, function-level authz gaps. \
  (8) CSRF, CORS, security headers — missing CSRF tokens or SameSite; \
  permissive CORS (Access-Control-Allow-Origin: *, reflected origin); \
  missing CSP, X-Frame-Options, HSTS, X-Content-Type-Options. \
  (9) Error handling and information disclosure — stack traces in \
  responses, debug endpoints reachable in prod, verbose errors enabling \
  enumeration, source map exposure, banner grabbing. \
  (10) Logging — both under-logging (no audit trail for security events) \
  and over-logging (secrets, tokens, PII in logs). \
  (11) Dependencies — known-vulnerable libs (validate the dep-scanner \
  output in tooling-raw/), unpinned versions, post-install scripts. \
  (12) Supply chain — Dockerfile FROM unpinned tags, GitHub Action \
  uses: not pinned to SHA, npm install with no lockfile, missing \
  signature verification on artifacts. \
  (13) CI/CD workflow security — GitHub Actions script injection via \
  \${{ github.event.* }} in run: blocks, pull_request_target misuse, \
  missing top-level permissions:, secret leakage in workflow logs, \
  workflow_dispatch input injection. \
  (14) Infrastructure-as-code (Terraform, Helm, K8s manifests, \
  Dockerfile) — privileged containers, hostPath mounts, missing \
  NetworkPolicy, overly-permissive ServiceAccount, RBAC misconfig, \
  public S3 buckets, open security groups, missing encryption at rest. \
  (15) For agent-config repos specifically: prompt injection and \
  privilege escalation in commands/*.md, skills/*/SKILL.md, and \
  agents/**/*.md files — these are executed as agent instructions. \
  Be especially critical of any instruction that expands agent scope, \
  grants permissions, or runs shell commands. \
  Rate severity on evidence: impact, exploitability, blast radius, \
  reachability. Critical = unauthenticated RCE on internet surface, or \
  exposed live credentials, or SSRF allowing cloud-metadata exfil. \
  High = authenticated RCE, broken access control, weak crypto crossing \
  trust boundaries, pull_request_target with secrets and untrusted code. \
  Medium = reflected XSS, missing security headers on non-sensitive \
  surfaces, unpinned action references. Low = defense-in-depth gaps \
  with no current exploit. \
  Every finding must include a Verification field: how to confirm the \
  fix works — ideally a negative test (try the exploit, confirm it \
  now fails) plus a regression test. \
  Do not read or reference any other review file." \
  < /dev/null
```

### Step 1.5 — Verify the Codex artifact

The most common Codex failure mode is silent (sandbox denial, missing flag,
prompt parse error — see `lib/codex-invocation.md`). After the background
Codex job returns, verify:

```bash
[[ -s "$AUDIT_DIR/codex.md" ]] && grep -q '|.*|.*|' "$AUDIT_DIR/codex.md" \
  || echo "⚠️ Codex did not produce a usable $AUDIT_DIR/codex.md"
```

If verification fails: inspect the Codex stderr output, fix the issue if
identifiable, and re-run the command once. Only after a second failure
should you accept the single-agent degradation documented in Phase 3.

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent security review to
`$AUDIT_DIR/claude.md` using the same finding schema (ID prefix `A`).
Read `$AUDIT_DIR/tooling-raw/` first.

Cover the same 15 categories listed in Codex's prompt above:

1. **AttackSurface** — trust boundaries, deserialization sinks, SSRF candidates
2. **Injection** — SQL, command, prompt, XSS, path traversal, template, LDAP, NoSQL
3. **Crypto** — weak algos, hardcoded keys, bad RNG, non-constant-time, TLS, cert pinning
4. **Deserialization** — pickle, YAML unsafe load, polymorphic JSON
5. **SSRF** — outbound HTTP w/ user-controlled URLs, metadata service exfil
6. **AuthN / Session** — fixation, predictable IDs, rotation, logout, cookie flags, JWT
7. **AuthZ** — IDOR, mass assignment, function-level gaps, confused deputy
8. **CSRF / CORS / Headers** — tokens, SameSite, permissive CORS, missing headers
9. **InfoDisclosure** — stack traces, debug endpoints, verbose errors, source maps
10. **Logging** — under-logging vs over-logging, audit trail completeness
11. **Dependency** — validate scanner output, unpinned versions, post-install scripts
12. **SupplyChain** — unpinned `FROM`, unpinned `uses:`, missing lockfiles
13. **CICD** — Actions injection, `pull_request_target`, missing `permissions:`
14. **IaC** — K8s, Helm, Terraform, Dockerfile misconfigs
15. **AgentConfig** — prompt injection and privilege escalation in `commands/`, `skills/`, `agents/`

When auditing an agent-config repo, apply extra scrutiny to your own
instruction files — you may have systematic blind spots there. Be
especially critical of any instruction that expands agent scope,
grants permissions, or runs shell commands.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity, confidence, and explicit compound-finding notes.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - If Phase 2 Step 1.5 already triggered a single-agent fallback,
     the synthesis warning was already decided there
   - Otherwise, check `$AUDIT_DIR/claude.md` and `$AUDIT_DIR/codex.md`
     contain at least one finding row each
   - If one is missing or empty: add a prominent warning at the top of
     `$AUDIT_DIR/synthesis.md`: "⚠️ Single-agent synthesis — [agent]
     review was unavailable. Coverage may be incomplete."

2. **Deduplicate findings**:
   - Compare both reviews for overlapping findings
   - When the same vulnerability appears in both, merge into one
     synthesis row — note both source IDs (e.g. `A002, C003`)
   - When merging: preserve the most specific `Location` and the best
     `Evidence/Notes`; do not flatten two findings into one if they
     have different exploit preconditions or affected assets
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity** against the rubric in the Finding Schema
   section. Do not automatically escalate severity because both
   reviewers flagged the same issue. Re-evaluate each finding's
   impact, exploitability, blast radius, and reachability.

4. **Identify compound findings**: scan all unified findings for pairs
   or chains that combine into a worse exploit than any single finding
   represents (SQLi + verbose errors → blind SQLi; SSRF + no IMDSv2 →
   credential exfil; weak session + missing CSRF → account takeover).
   Add a `Compounded By` row to the synthesis output (see template
   below).

5. **Write synthesis** to `$AUDIT_DIR/synthesis.md`:

   ```markdown
   # Security Audit Synthesis — [REPORT_TS]

   ## Scope
   [Resolved scope path(s); note --diff-only if used]

   ## Tooling Summary
   - Ran: [list tools that produced output]
   - Skipped/failed: [tools not run, with reason from tooling-raw/STATUS.md]
   - Emergency exit triggered: [yes/no — if yes, audit halted before Phase 2]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - By category: AttackSurface: X, Injection: X, Crypto: X, ... (only non-zero)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | CWE/OWASP | Category | Title | Location | Why It Matters | Recommended Fix | Verification | Evidence/Notes | Sources |
   |----|----------|-----------|----------|-------|----------|----------------|-----------------|--------------|----------------|---------|
   | S001 | ... | CWE-89 / A03:2021 | Injection | ... | ... | ... | ... | ... | ... | A001, C002 |

   ## Compound Findings
   [Pairs/chains that escalate when combined. Each entry: which IDs
   compound, the resulting impact, the combined severity. Example:
   "S001 (SQLi, Medium) + S007 (verbose errors, Low) → blind SQLi feasible, effective severity High"]

   ## Findings Present in Only One Review
   [Note findings not corroborated by the other reviewer and why they
   are retained or dropped]
   ```

Phase 3 is complete when `$AUDIT_DIR/synthesis.md` is written.

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives, severity
miscalibrations, missed findings, and missed compound paths.

### Step 1 — Launch Codex Devil's Advocate

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "Read $AUDIT_DIR/synthesis.md and the raw tooling output in \
  $AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not \
  improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md \
  covering: \
  (1) False positives — findings that are not actually exploitable in \
  this specific codebase context (e.g. behind a WAF, behind an \
  authenticated admin gate, in code that isn't reachable from \
  untrusted input, in a CI-only path with no production exposure). \
  (2) Severity miscalibrations — findings rated too high (low-impact, \
  well-mitigated) or too low (underestimating reachability, blast \
  radius, or chained-exploit potential). \
  (3) Missing findings — vulnerabilities that both reviewers missed, \
  especially: cryptographic timing attacks, race conditions / TOCTOU, \
  side-channel leaks, business-logic flaws not captured by category \
  prompts, supply-chain attacks not covered by dep scanners. \
  (4) Missing compound paths — separate findings that should have \
  been flagged as combining into a worse exploit. \
  (5) Remediation steps that are impractical, incomplete, or wrong — \
  especially fixes that close a symptom while leaving the root cause \
  exploitable from a different path. \
  (6) Verification steps that don't actually prove the fix works — a \
  fix without a negative test is a fix on hope. \
  Be specific. Every challenge must cite the finding ID and reference \
  the CWE or OWASP category." \
  < /dev/null
```

After the call, verify the artifact: `[[ -s "$AUDIT_DIR/devils-advocate.md" ]] || echo "⚠️ Codex devil's advocate produced no output"`.

### Step 2 — Incorporate Valid Challenges

Once `$AUDIT_DIR/devils-advocate.md` is written, read it and:

- **Remove** confirmed false positives from the working finding list
- **Recalibrate** severity where the challenge is valid and evidence
  supports it
- **Add** genuinely missed findings with new synthesis IDs
- **Add** missed compound paths to the synthesis's Compound Findings
  section
- **Document every rejected challenge** in a "Rejected Challenges"
  section at the bottom of `$AUDIT_DIR/synthesis.md`:

  ```markdown
  ## Rejected Devil's Advocate Challenges

  | Finding/Claim | Reason Rejected |
  |---|---|
  | [Claim from devil's advocate] | [Why it was not accepted] |
  ```

Phase 4 is complete when challenges are incorporated and rejections
are documented.

---

## Phase 5: Report Output

**Goal**: Produce a findings report at `$AUDIT_DIR/REPORT.md` with
security findings as sprint tasks, **Critical findings broken out as
"Immediate Action" above P0** (Critical → ship-the-fix-this-week, not
plan-next-sprint).

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next deploy / out-of-band patch** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

This differs from other audits intentionally: the gap between Critical
(stop the line) and High (plan and ship) is operationally meaningful
for security.

Each sprint task must include:
- Finding ID (from synthesis)
- CWE / OWASP reference
- Category
- File and line reference where applicable
- Clear description of the vulnerability
- Concrete, specific remediation step (not just "fix the issue")
- **Verification step**: ideally a negative test that fails on the
  unpatched code and passes after the fix, plus a regression test —
  not "manual review confirms it's fixed"

### No-Findings Case

If the synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- The task description must document: what scope was covered, what
  tooling ran, what 15 categories were reviewed, date of review, and
  reviewer agents
- Do not produce an empty sprint

### Write the Report

Create `$AUDIT_DIR/REPORT.md`:

```markdown
# Security Audit (Web Application / Services) — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: audit scope, tooling summary, total findings by
severity, top 3 issues. Remind the reader that static LLM + scanner
review has inherent limitations — it cannot assess runtime
exploitability, compensating controls, or deployment-context-specific
risk.]

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

| Category | Count |
|---|---|
| [Only non-zero categories shown] | N |

Intermediate audit artifacts: `$AUDIT_DIR/tooling-raw/`, `$AUDIT_DIR/claude.md`, `$AUDIT_DIR/codex.md`, `$AUDIT_DIR/synthesis.md`, `$AUDIT_DIR/devils-advocate.md`

## Implementation Plan

### 🚨 Immediate Action (Critical)

[One task per Critical finding. These require out-of-band patching,
not a normal sprint cycle. Include a "blocker note" if any sequence
must be maintained.]

**Task: [Finding ID] — [Category] — [Title]**
- Location: `path/to/file:line`
- CWE / OWASP: [identifier]
- Issue: [vulnerability description]
- Remediation: [specific fix]
- Verification: [negative test + regression test]
- **Operational note**: [credential rotation needed? affected user
  comms? incident-report scope?]

### P0: Must Ship (High)

[One task per High finding, same format minus the Operational note
unless relevant]

### P1: Ship If Capacity Allows (Medium)

[One task per Medium finding, same format]

### Deferred (Low)

[Low findings with brief rationale]

## Compound Findings

[Reproduce the Compound Findings section from synthesis here so the
human reader sees combined-risk paths in context. Each entry: which
finding IDs combine, resulting impact, effective combined severity.]

## Definition of Done

- [ ] All Critical (Immediate Action) tasks completed and verified
- [ ] All P0 tasks completed and verified
- [ ] Each task's verification step executed — negative test fails on
      unpatched code, passes on patched code
- [ ] No new Critical/High findings introduced by the remediations
- [ ] Compound-finding paths confirmed closed (not just one half fixed)
- [ ] Reviewer confirms task ordering was appropriate for dependencies

## Security Considerations

- **Sensitive content**: this report may contain exploit details and
  attack-path descriptions. It lives under `~/Reports/` outside any
  git repo by default — review before sharing.
- **Task ordering matters**: some remediations depend on others (fix a
  sink before removing an injection point upstream); some compound
  findings require both halves fixed to actually close the path.
- These tasks were generated from static LLM + automated-tooling
  review. Validate each fix against runtime behavior where possible.

## Dependencies

- Raw tooling output: `$AUDIT_DIR/tooling-raw/`
- Audit intermediate files: `$AUDIT_DIR/claude.md`, `$AUDIT_DIR/codex.md`, `$AUDIT_DIR/synthesis.md`, `$AUDIT_DIR/devils-advocate.md`
- Emergency-exit document (if applicable): `$AUDIT_DIR/EMERGENCY.md`
```

### Register and Hand Off

Inform the user:

   > ✅ Security audit (web application / services) complete.
   >
   > **Report:** <literal absolute path to $AUDIT_DIR/REPORT.md>
   >
   > **Summary:** <Critical: X, High: Y, Medium: Z, Low: W>; top finding:
   > <one-line description>
   >
   > **⚠️ Sensitive content**: this report contains exploit details.
   > Review before sharing.
   >
   > **Next:** Run `/sprint-plan` against the report to create an
   > actionable sprint for the High/Medium/Low tiers:
   >
   > ```
   > /sprint-plan <literal absolute path>
   > ```
   >
   > **Important:** Critical findings in the "Immediate Action" section
   > should NOT wait for a sprint cycle — patch out-of-band and confirm
   > with a negative test before merging.

If the emergency-exit triggered in Phase 1, the hand-off message
instead points the user at `$AUDIT_DIR/EMERGENCY.md` and confirms the
audit did not proceed past Phase 1.

---

## Output Checklist

At the end of this workflow, verify:

- [ ] `$AUDIT_DIR/tooling-raw/` — populated with tool output (and
      `STATUS.md` documenting any tooling that didn't run)
- [ ] `$AUDIT_DIR/claude.md` — finding schema with CWE/OWASP +
      Category + Verification columns, ID prefix A
- [ ] `$AUDIT_DIR/codex.md` — finding schema with CWE/OWASP +
      Category + Verification columns, ID prefix C
- [ ] Both files are non-empty (or single-agent warning added to
      synthesis after Phase 2 Step 1.5 retry failure)
- [ ] `$AUDIT_DIR/synthesis.md` — unified findings with canonical
      S-prefix IDs, Compound Findings section, all extension columns
- [ ] `$AUDIT_DIR/devils-advocate.md` — Codex challenge complete
- [ ] Valid devil's advocate challenges incorporated into synthesis
- [ ] Rejected challenges documented with reasoning in synthesis
- [ ] `$AUDIT_DIR/REPORT.md` — Critical findings in **Immediate
      Action** section above P0
- [ ] Each task has: finding ID, CWE/OWASP, category, location, issue,
      remediation, verification (with negative test where applicable)
- [ ] No-findings case handled if applicable
- [ ] Sensitive-content warning included in hand-off
- [ ] Emergency-exit handled if triggered

---

## Reference

- Report output: `~/Reports/<org>/<repo>/audits/<TS>-security-web-application/`
- Audit artifacts: `$AUDIT_DIR/{tooling-raw/, claude,codex,synthesis,devils-advocate,REPORT}.md` plus optional `EMERGENCY.md`
- OWASP Top 10 (2021): https://owasp.org/Top10/
- CWE Top 25: https://cwe.mitre.org/top25/
- gitleaks: https://github.com/gitleaks/gitleaks
- semgrep security rulesets: https://semgrep.dev/p/security-audit
- govulncheck: https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck
- pip-audit: https://pypi.org/project/pip-audit/
- cargo audit: https://github.com/RustSec/rustsec
- trivy: https://github.com/aquasecurity/trivy
- actionlint: https://github.com/rhysd/actionlint
