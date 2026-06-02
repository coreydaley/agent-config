Perform a thorough security review of the scope at the project root
you've been pointed at. Security tooling has already been run; raw
output is in the audit dir's tooling-raw/ subdirectory. Read those
files first: gitleaks.json (secrets), semgrep.json (SAST),
govulncheck.log / npm-audit.json / pip-audit.json / cargo-audit.json
(dependency vulnerabilities), trivy-config.json (IaC misconfigs),
actionlint.json (GitHub Actions). Validate, do not duplicate, those
automated findings.

Write all findings to codex.md (in the audit dir you were granted
write access to) using this exact table format:

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

(3) Cryptography — weak algos (MD5/SHA1, DES, ECB), hardcoded
keys/IVs, bad RNG, non-constant-time compare, missing rotation, TLS
config, cert pinning gaps.

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

(12) Supply chain — Dockerfile FROM unpinned tags, GitHub Action
uses: not pinned to SHA, npm install w/o lockfile, missing artifact
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
reachability, compensating controls.

Critical anchors:
- Unauthenticated RCE on internet surface
- SQL injection on primary endpoint
- SSRF allowing cloud-metadata exfil
- Live credentials in source (handled by orient emergency-exit; here
  flag near-misses and dev/test stubs that shouldn't ship)
- Insecure deserialization on reachable handler
- Privileged K8s container reachable from cluster network

High anchors:
- Authenticated RCE
- Stored XSS on frequently-used surface
- Broken access control allowing horizontal privesc
- Weak crypto crossing trust boundaries
- pull_request_target with secrets + untrusted code

Every finding must include a Verification field describing a negative
test (try the exploit, confirm it fails) plus a regression test.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
