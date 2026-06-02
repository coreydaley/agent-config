# Node: report

Phase 5 of the framework. Convert the synthesized findings into a sprint-able audit deliverable with networking-specific tier mapping.

## Inputs

- `$AUDIT_DIR/synthesis.md` (with devil's-advocate challenges incorporated)
- `$AUDIT_DIR/tooling-raw/STATUS.md` (for the overview's tooling summary)
- Walker state: `audit_dir`, `da_status`, `codex_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Apple-networking sprint mapping (default tiered)

| Finding Severity | Sprint Priority |
|---|---|
| **Critical** | **P0 — Must Ship** |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

**Default is tiered, not `Immediate Action`.** Most networking findings (token-cache poisoning, retry-DDOS chains, OOM-prone uploads) hurt at scale but don't block the next archive the way a missing dSYM or a wrong App Icon size does. Treat them as P0 to be addressed before release, but they don't justify halting the build pipeline by themselves.

### Contextual escalation to Immediate Action

There is **one well-defined exception**: a **cert-pinning expiration finding inside the audit window** must be contextually escalated to **Immediate Action**. The criteria:

- Category = `CertPinning`
- The pinned certificate's `notAfter` date falls within the audit window (defined as: from the run timestamp through 60 days after; configurable via `IMMEDIATE_ACTION_PIN_WINDOW_DAYS` env var, default 60)
- AND there is no documented multi-pin fallback (current + next + backup) confirmed in the source

Why escalate: a pin failure bricks every install of every shipped version simultaneously, with no client-side remediation. The fix can take days to propagate through App Review even on expedited review. The deadline is the cert's expiration, not a sprint boundary.

How to escalate: in the deliverable, place the finding under an explicit `### Immediate Action — cert-pinning expiration` block (above `P0 — Must Ship`) and annotate the task with the cert `notAfter` date. Cite the cert chain inspection step (`openssl s_client -connect host:443 -servername host | openssl x509 -noout -dates`) in the Verification field.

If no `CertPinning` finding qualifies, the deliverable has no Immediate Action section at all — that's the normal case.

## Per-task contents

Each task in the Implementation Plan must include:

- **ID** — the synthesis S-prefix ID
- **Category** — one of the 12 networking categories
- **Location** — `path/to/file.swift:line` or `<symbol>(<args>) in <file>` (never just "the network layer")
- **Anchor** — required (`Apple:URLSessionConfiguration`, `Apple:URLAuthenticationChallenge`, `RFC:6749`, etc.)
- **Platform** — `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`
- **Verification** — `code` (inspectable in the snapshot) or `runtime` (needs Charles / mitmproxy / Network Link Conditioner / a real backend round-trip to confirm)
- **Issue** — clear description
- **Remediation** — concrete, specific (e.g. `Replace URLSessionConfiguration.default with .ephemeral for the AuthService session at NetworkClient.swift:42; URLCache will be in-memory only and won't persist Authorization-bearing responses across app launches`)
- **Verification step** — proxy capture (Charles / mitmproxy), Network Link Conditioner profile, or an XCTest that asserts the configuration value (e.g. `XCTAssertNil(session.configuration.urlCache)` for the .ephemeral fix)

## No-findings case

If `synthesis.md` contains zero findings after Phase 4:

- Create a single P0 task: `Verify no findings — apple-networking — <scope>, <date>`
- Task description: scope covered, 12 categories reviewed, tooling that ran, date, reviewer agents
- Do not produce an empty sprint

## Output template

Write the per-run audit deliverable to `$AUDIT_DIR/REPORT.md` with the following structure:

- Title `# Apple Networking Audit — <scope> (<YYYY-MM-DD>)`.
- `## Overview` — 1-2 paragraphs: scope, tooling summary, total findings by severity, top 3 issues. Note the audit's inherent limitations: most network-layer findings require a proxy-driven reproduction (Charles / mitmproxy) or a real backend round-trip; the audit catches the misconfig but only the proxy capture or load test confirms the fix.
- If a cert-pinning expiration falls inside the audit window, include a callout at the top: `Immediate Action — cert-pinning expiration inside audit window. The pinned certificate at <host> expires <date> with no documented multi-pin fallback. Pin failure bricks every install of every shipped version simultaneously. See Immediate Action section below.`
- `## Audit Summary` — severity-count table (Critical / High / Medium / Low / Total) and category-count table (non-zero categories only).
- Intermediate-artifacts list: `tooling-raw/`, `claude.md`, `codex.md` (or `MISSING — single-agent run`), `synthesis.md`, `devils-advocate.md` (or `MISSING — DA failed`).
- `## Implementation Plan` with subsections:
  - `### Immediate Action — cert-pinning expiration inside audit window` — only if a qualifying CertPinning finding exists; one task block per finding.
  - `### P0 — Must Ship` — one block per Critical and High finding.
  - `### P1 — Ship If Capacity Allows` — one block per Medium finding.
  - `### Deferred` — one line per Low finding.
- Each task block carries the per-task fields above (ID, Category, Location, Anchor, Platform, Verification, Issue, Remediation, Verification step).
- `## Compound Findings` — reproduce the compound chains identified in synthesis (token cache poisoning, cert apocalypse, DDOS self, memory bomb, WebSocket stall) when present.
- `## Definition of Done`:
  - [ ] All Immediate Action and P0 tasks completed and verified
  - [ ] Each task's verification step executed
  - [ ] No new Critical/High findings introduced by the remediations
  - [ ] CachePolicy / URLSessionConfig fixes: verified via Charles Proxy that Authorization-bearing responses do NOT appear in URLCache (`URLCache.shared.cachedResponse(for: request)` returns nil)
  - [ ] CertPinning fixes: verified via `openssl s_client -connect host:443` that the new pin set matches the live chain; tested against staging with a rotated cert
  - [ ] RetryBackoff fixes: verified via a forced-failure proxy test that retry intervals follow the expected exponential backoff with jitter and respect `Retry-After`
  - [ ] MultipartUpload fixes: verified via Instruments Allocations that memory does not grow with file size
  - [ ] WebSocketURLSession fixes: verified via Network Link Conditioner with a Lossy profile that reconnect uses backoff and ultimately succeeds
- `## Sensitive-content warning` — references to internal API endpoints, OAuth client IDs, pinned-cert fingerprints. Treat as confidential. Proxy captures generated during verification may contain auth tokens; redact before sharing externally.
- `## Dependencies` — `$AUDIT_DIR/tooling-raw/` and `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`.

## Outputs

- `$AUDIT_DIR/REPORT.md` exists, non-empty, contains the Implementation Plan with appropriate tiers populated

## Outgoing edges

- → `verify` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from report --to verify
```

## Failure modes

- Synthesis has zero findings → produce the single-task no-findings deliverable; still transition to `verify`.
- Critical finding without a concrete remediation → write what's known and flag `**REMEDIATION INCOMPLETE**` in the task body; verify will still pass on artifact existence, but the user sees the gap.
- Cert-pinning finding present but the `notAfter` date couldn't be determined from the source (pin is opaque) → keep the finding in P0 and annotate the task with `cert-expiration-unknown — manual chain inspection required` rather than escalating to Immediate Action.
