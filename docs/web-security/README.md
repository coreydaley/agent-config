# Web Application & Services Security Audit Reference

Schema and severity reference for the `/audit-web-security` command.
For native Apple platforms, see [`../security-apple/README.md`](../security-apple/README.md).

Audit artifacts are written outside this repo to
`~/Reports/<org>/<repo>/audits/<TS>-security-web-application/` —
`<org>/<repo>` is derived from the `upstream` remote (falling back to
`origin`), and `<TS>` is the audit start timestamp (`YYYY-MM-DDTHH-MM-SS`).

Unlike most other audits, Phase 1 of this one runs real security
tooling (secret scanners, dep auditors, SAST, IaC scanners, GitHub
Actions linters) and writes the raw output into a `tooling-raw/`
subfolder before reviewers begin. Findings are calibrated against
measured data, not just impressions from reading source.

## Output

Each audit run produces these files in its own timestamped
`$AUDIT_DIR`:

| File / Folder | Description |
|---|---|
| `tooling-raw/` | Raw output from security tooling: `gitleaks.json`, `semgrep.json`, `govulncheck.log` (Go), `npm-audit.json` (Node), `pip-audit.json` (Python), `cargo-audit.json` (Rust), `trivy-config.json` (K8s/Dockerfile/Terraform), `actionlint.json` (GitHub Actions). Includes `STATUS.md` noting which tools were skipped or failed. |
| `EMERGENCY.md` | **Only present if Phase 1 emergency-exit triggered.** Describes exposed credentials found, rotation steps, and confirms the audit halted before Phase 2. |
| `claude.md` | Claude's independent security review (ID prefix `A`) |
| `codex.md` | Codex's independent security review (ID prefix `C`) |
| `synthesis.md` | Unified, deduplicated findings (canonical `S`-prefix IDs), Compound Findings section, Rejected Devil's Advocate Challenges section |
| `devils-advocate.md` | Codex's challenge pass against the synthesis |
| `REPORT.md` | Final findings report — Critical broken out as **Immediate Action** above P0 |

`REPORT.md` is reference material. To act on the findings (High/Medium/Low),
run `/sprint-plan` with the report path as the seed prompt:

```
/sprint-plan ~/Reports/<org>/<repo>/audits/<TS>-security-web-application/REPORT.md
```

**Critical findings should not wait for a sprint cycle** — patch
out-of-band and confirm with a negative test before merging.

## Finding Schema

All intermediate audit files (`claude.md`, `codex.md`, `synthesis.md`)
use this table format:

```
| ID | Severity | CWE/OWASP | Category | Title | Location | Why It Matters | Recommended Fix | Verification | Evidence/Notes |
```

`synthesis.md` adds a `Sources` column listing the source review IDs
each unified finding merges (e.g. `A002, C003`).

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis canonical)

**Severity levels:** Critical, High, Medium, Low

### CWE/OWASP Column

Every finding maps to a named weakness from [CWE](https://cwe.mitre.org/)
and/or the [OWASP Top 10 2021](https://owasp.org/Top10/). A finding
without a named weakness anchor is invalid and is omitted.

Examples:
- `CWE-89 / A03:2021` — SQL injection
- `CWE-78` — OS command injection
- `CWE-918 / A10:2021` — SSRF
- `CWE-502 / A08:2021` — Insecure deserialization
- `CWE-200 / A05:2021` — Information exposure
- `CWE-285 / A01:2021` — Broken access control
- `CWE-352 / A05:2021` — CSRF
- `CWE-798` — Hardcoded credentials
- `CWE-327` — Broken/risky crypto

### Category Column

One per finding — used for grouping in the report:

| Category | Covers |
|---|---|
| `AttackSurface` | New inputs, APIs, externally reachable paths |
| `Injection` | SQLi, command, prompt, XSS, path traversal, template, LDAP, NoSQL |
| `Crypto` | Weak algos, hardcoded keys, bad RNG, non-constant-time, missing rotation |
| `Deserialization` | Pickle, YAML unsafe load, polymorphic JSON, Java/PHP |
| `SSRF` | Outbound HTTP w/ user-controlled URLs, metadata service exfil |
| `Secrets` | Hardcoded credentials, secrets in logs/config |
| `AuthN` | Weak password handling, session fixation, MFA gaps, JWT misuse |
| `AuthZ` | Broken access control, IDOR, mass assignment, function-level gaps |
| `Session` | ID predictability, missing rotation, missing logout, cookie flags |
| `Headers` | CSP, HSTS, X-Frame-Options, CORS, SameSite, X-Content-Type-Options |
| `InfoDisclosure` | Stack traces, debug endpoints, verbose errors, source maps |
| `Logging` | Under-logging (no audit trail), over-logging (secrets in logs) |
| `Dependency` | Known-vulnerable deps, unpinned versions, post-install scripts |
| `SupplyChain` | Build provenance, unpinned `uses:`, Dockerfile tags |
| `CICD` | GitHub Actions injection, `pull_request_target`, missing `permissions:` |
| `IaC` | K8s/Helm/Terraform/Dockerfile misconfigs |
| `AgentConfig` | Prompt injection / privilege escalation in `commands/`/`skills/`/`agents/` |

### Severity Calibration

Severity is assessed on evidence — impact, exploitability, blast radius,
reachability. Anchors (starting point):

| Severity | Anchor examples |
|---|---|
| **Critical** | Unauthenticated RCE on internet surface; SQL injection on primary endpoint; SSRF allowing cloud-metadata exfil; live credentials in source; insecure deserialization on a reachable handler; privileged K8s container reachable from cluster network |
| **High** | Authenticated RCE; stored XSS on frequently-used surface; broken access control allowing horizontal privesc; weak crypto crossing trust boundaries; `pull_request_target` with secrets + untrusted code |
| **Medium** | Reflected XSS requiring social engineering; verbose error messages; missing security headers on non-sensitive surfaces; unpinned Action references; outdated dep with no known reachable exploit |
| **Low** | Defense-in-depth gaps with no current exploit; cosmetic logging issues; deprecated crypto with no immediate risk |

Agreement between reviewers raises **confidence**, not severity.

### Compound Findings

`synthesis.md` and `REPORT.md` include a **Compound Findings** section
when separate weaknesses chain into a worse exploit:

- SQLi + verbose errors → blind SQLi feasible
- SSRF + no IMDSv2 enforcement → cloud-credential exfil
- Weak session + missing CSRF → account takeover

The combined effective severity is reported alongside the individual
finding severities.

## Sprint Mapping

Differs from other audits intentionally — security has a meaningful
gap between Critical (stop the line) and High (plan and ship):

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **Immediate Action — fix before next deploy / out-of-band patch** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each task includes a **negative test verification** — try the exploit,
confirm it fails on the patched code. "Manual review confirms" is
insufficient.

## Modes

| Flag | Behavior |
|---|---|
| (none) | Audit the resolved scope path |
| `--diff-only` | Restrict the audit to files changed in `git diff main...HEAD` — useful for PR review and recent-change focus |

## Tooling

The audit attempts each of the following in Phase 1; missing tools are
recorded in `tooling-raw/STATUS.md` and the audit continues without
them:

| Tool | When | What it catches |
|---|---|---|
| `gitleaks` | Always | Secrets in source / git history |
| `semgrep` | Always | SAST via `p/security-audit` + `p/owasp-top-ten` |
| `govulncheck` | If `go.mod` present | Go dependency CVEs |
| `npm audit` | If `package-lock.json` present | Node dependency CVEs |
| `pip-audit` | If `requirements.txt` / `pyproject.toml` present | Python dependency CVEs |
| `cargo audit` | If `Cargo.toml` present | Rust dependency CVEs |
| `trivy config` | Always | K8s / Helm / Terraform / Dockerfile misconfigs |
| `actionlint` | If `.github/workflows/` present | GitHub Actions issues |

## Sensitive Content

Reports describe vulnerabilities and may contain exploit details,
exposed credential patterns, or attack paths. Because they live under
`~/Reports/` (outside any git repo by default), they don't risk
accidental commit. Review before sharing.

## Inherent Limitations

Static review + automated tooling cannot assess:
- Runtime exploitability (does the path actually reach a sink?)
- Compensating controls (WAF, network ACLs, RASP)
- Deployment-context-specific risk (internet-exposed vs internal-only)
- Logic flaws not captured by category prompts

Treat output as a structured starting point for human judgment, not a
guarantee of full coverage. Validate each fix against runtime behavior.

## References

- Subagent definition: [`../../subagents/audit-web-security.md`](../../subagents/audit-web-security.md)
- OWASP Top 10 (2021): https://owasp.org/Top10/
- CWE Top 25: https://cwe.mitre.org/top25/
- gitleaks: https://github.com/gitleaks/gitleaks
- semgrep security rulesets: https://semgrep.dev/p/security-audit
- govulncheck: https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck
- pip-audit: https://pypi.org/project/pip-audit/
- cargo audit: https://github.com/RustSec/rustsec
- trivy: https://github.com/aquasecurity/trivy
- actionlint: https://github.com/rhysd/actionlint
