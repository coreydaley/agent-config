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
- Evidence: file:line citation, Apple API symbol reference, or specific tooling-raw/ line
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't actually apply in context.
Specifically for Apple networking:
- A flagged `URLSessionConfiguration.default` is for an unauthenticated,
  cacheable endpoint (e.g. CDN-served static content) where the default
  disk URLCache is the correct choice; the token-cache-poisoning chain
  requires an Authorization header which this endpoint doesn't carry.
- A flagged "pinning to a single cert" is actually pinning to the
  intermediate CA cert, which has a much longer rotation horizon than
  the leaf cert; check `auth-challenge.txt` for which cert / SPKI is
  being hashed before flagging Critical.
- A flagged "no exponential backoff" is for an idempotent GET to a
  paginated endpoint where the server returns 5xx only during scheduled
  maintenance windows announced via response headers; an upper-bounded
  retry with linear backoff is acceptable.
- A flagged URLCache.shared usage is for a debug-only network inspector
  feature gated behind `#if DEBUG`; it doesn't ship to Release.
- A flagged `URLSession.shared` for one-off requests is the intended
  pattern when there's no per-role configuration to share; flag only
  if `URLSession.shared` is the *only* session used across the entire
  app (no role separation).
- A flagged WebSocket library (Starscream / SocketIO) is justified by
  a specific protocol-level feature `URLSessionWebSocketTask` doesn't
  support (e.g. per-message-deflate compression, custom subprotocol
  negotiation); check the synthesis row's Evidence column.

(2) Severity miscalibrations — findings rated too high (the offending
config is only on a Debug-build session that doesn't ship; the affected
endpoint is non-authenticated and CDN-cached and the cache-poisoning
chain doesn't apply; the retry loop is on a low-frequency call where
DDOS-self isn't reachable; the multipart-upload finding is for an
endpoint that only accepts <1MB files by server-side limit) or too low
(an `Authorization` header set in `httpAdditionalHeaders` on a shared
`URLSessionConfiguration.default` is Critical not High because the
header rides every cached response; a pinned cert with `notAfter`
inside 30 days deserves Immediate Action even if no other condition
holds).

(3) Missing findings — Apple-networking issues the review may
have missed:
- **Per-host concurrency limits**: `httpMaximumConnectionsPerHost`
  default is 6 on iOS but 4 on macOS; an app that fires 20 parallel
  requests will queue most of them under the hood, masking apparent
  request latency as backend slowness.
- **Cookie-jar pollution across sessions**: `URLSessionConfiguration.default`
  shares `HTTPCookieStorage.shared` by default; if multiple roles
  share the default, a cookie set by Analytics rides every Auth
  request. Use `.httpCookieStorage = nil` on Auth sessions.
- **TLS protocol minimum**: `tlsMinimumSupportedProtocolVersion` (and
  the deprecated `tlsMinimumSupportedProtocol`) default to TLS 1.2;
  flag if it's set to anything lower in a non-ATS-exempted session.
- **Proxy support**: `connectionProxyDictionary` set in code for a
  hardcoded internal proxy; this breaks for any user not on the
  corp network and the Charles/mitmproxy override path.
- **Auth-credential storage**: `URLCredentialStorage.shared` is
  separate from the Keychain and is the *wrong* place to store OAuth
  tokens; flag if any code path uses it as a token store.
- **WebSocket close-code discipline**: missing distinction between
  `.normalClosure` (1000), `.goingAway` (1001), `.protocolError` (1002)
  in disconnection paths leads to misclassified reconnect behavior.
- **Background URLSession + foreground reuse**: a `URLSession` created
  with `.background(withIdentifier:)` cannot be used in the foreground
  for non-upload/download tasks; flag any data-task / streamTask /
  webSocketTask created on a background session. (Note: the
  *lifecycle* of background URLSession belongs to audit-apple-ios;
  this is the configuration-misuse finding within networking scope.)
- **Idempotency-key generation**: a UUID-based idempotency key
  regenerated per retry attempt defeats the entire purpose; the key
  must be generated once per logical operation and reused across
  retries.
- **Network.framework vs URLSession choice**: app uses raw `NWConnection`
  for plain HTTPS when `URLSession` would suffice (no streaming, no
  multipath, no quic-specific features); raw `NWConnection` opts out
  of every URLSession affordance (caching, cookies, ATS, proxy support).

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse outcome than any single finding represents:
- "Token cache poisoning" chain (URLSessionConfiguration.default +
  Authorization on URLRequest + cacheable response) — already covered,
  but check whether all three conditions are present at the *same*
  call site, not just present somewhere in the codebase.
- "Cert apocalypse" chain (single-cert pin + no fallback + expiration
  inside audit window) — check `auth-challenge.txt` for the actual
  pin set, not the synthesis's summary of it.
- "DDOS self" chain (tight retry + no backoff + APNs silent push that
  wakes the app to retry) — the silent-push trigger is what makes
  this catastrophic; without it, the retry storm is bounded to
  user-foreground time.
- "Memory bomb" chain (multipart Data load + UX that lets the user
  pick large files like Photo Library video) — the UX surface
  determines whether the OOM is reachable at all.
- "WebSocket stall" chain (reconnect without backoff + 429 + ignore
  Retry-After) — verify Retry-After parsing exists somewhere before
  flagging the chain as missing.

(5) Impractical / incomplete / wrong remediations — e.g.:
- "Switch to URLSessionConfiguration.ephemeral" without acknowledging
  that ephemeral has no HTTPCookieStorage either — if the app relies
  on cookies for the same session, ephemeral breaks login state.
- "Pin via SPKI hash" without specifying the public-key algorithm
  (RSA vs ECDSA — the hash input is the SubjectPublicKeyInfo DER
  encoding, which differs across algorithms).
- "Add exponential backoff" without specifying the base, max, and
  jitter strategy; "backoff" without a jitter component still
  thundering-herds because every client retries on the same boundary.
- "Use uploadTask(with:fromFile:)" without acknowledging that the
  file must outlive the upload (uploadTask streams from disk and
  holds the file open); if the source file is in a temporary location
  that the app deletes, the upload fails mid-stream.
- "Deduplicate refresh-token requests" without specifying the
  serialization primitive (an actor, a serial dispatch queue, a
  semaphore + lock); the wrong primitive is worse than no dedup.

(6) Verification steps that don't actually prove the fix works — e.g.
"verify by running the app and checking it loads" when the issue only
manifests under proxy capture; "Charles Proxy capture" verification
for a cert-pinning fix that *blocks* Charles by design; "an XCTest
assert that the configuration is .ephemeral" when the bug is that the
config is rebuilt with .default elsewhere; "manual code review" for a
multipart-upload-OOM finding that only manifests on a low-RAM device
with a 500MB asset.

Be specific. Every challenge must cite the finding ID and reference
the file path / API symbol / tooling-raw line where applicable.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted but
  found nothing worth surfacing.
- No emojis.
