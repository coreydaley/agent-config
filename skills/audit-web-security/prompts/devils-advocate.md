Read synthesis.md and the raw tooling output in tooling-raw/ in the
audit dir you've been granted access to. Your job is to attack the
synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated | missing_finding | missing_compound | impractical_remediation | insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, compensating control identification, or specific code reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that aren't actually exploitable in
this codebase context:
- Behind a WAF / RASP / network ACL that already mitigates.
- Behind an authenticated admin gate not reachable from untrusted
  input.
- Not reachable from untrusted input at all (purely internal, behind
  service mesh mTLS, etc.).
- CI-only path with no production exposure.
- Vendored source warnings the project has already triaged.

(2) Severity miscalibrations — findings rated too high (low actual
exploitability given compensating controls; not internet-reachable;
gated by strong auth) or too low (underestimating reachability,
blast radius, chained-exploit potential, or default-on attack
surface).

(3) Missing findings — vulnerabilities the review missed:
- Timing attacks / non-constant-time comparisons.
- Race conditions / TOCTOU.
- Side-channel leaks (response timing, cache, error-message
  enumeration).
- Business-logic flaws not captured by category prompts (idempotency
  bypasses, replay, sequencing).
- Supply-chain attacks not captured by dep scanners (typosquatting,
  install-time scripts, malicious post-install hooks).
- GraphQL-specific issues (depth/complexity, batching abuse,
  introspection in prod).
- gRPC / Protobuf Any deserialization gaps.
- WebSocket frame-handler injection.
- File-upload content-type / magic-byte / path-traversal gaps.
- OAuth/OIDC redirect_uri / state / PKCE gaps.
- Webhook signing verification gaps.
- IaC: hostPath / privileged / capabilities-add / runAsNonRoot:false.
- CI/CD: pull_request_target with checkout of untrusted ref;
  workflow_run with untrusted payload; reusable workflow with
  inherited secrets.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse exploit than any single finding represents. Be
explicit about the chain and the combined severity (e.g. SSRF +
no-IMDSv2 = cloud-cred exfil; XSS + tokens in localStorage = bearer
exfil; pull_request_target + secret env = workflow takeover).

(5) Impractical/incomplete/wrong remediations — e.g. parameterizing
SQL but leaving an ORDER BY clause concatenated; adding a CSP but
permitting unsafe-inline; rotating a credential without restarting
downstream services; closing one SSRF vector while leaving the
underlying URL fetch unbounded.

(6) Verification steps that don't actually prove the fix works — a
fix without a negative test is a fix on hope. Web-specific: HTTP
request that previously demonstrated the exploit must be re-run and
confirmed to fail; regression test added.

Be specific. Every challenge must cite the finding ID and reference
the CWE or OWASP category where applicable.

Do not read or reference any other review file beyond synthesis.md
and the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
