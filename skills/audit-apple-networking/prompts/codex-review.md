Perform a thorough Apple platform networking review of the scope at
the project root you've been pointed at. Tooling has already been run;
raw output is in the audit dir's tooling-raw/ subdirectory. Read those
files first:

- urlsession-config.txt — every URLSessionConfiguration / httpAdditionalHeaders /
  timeoutIntervalForRequest / timeoutIntervalForResource hit. **Cross-referencing
  this against auth-challenge.txt and cachepolicy.txt is the single
  highest-yield activity for this audit.**
- urlsession-shared.txt — every URLSession.shared and URLSession(configuration:)
  call site
- auth-challenge.txt — URLAuthenticationChallenge, urlSession(_:didReceive:completionHandler:),
  SecTrust*, NWConnection sec_protocol_options_set_verify_block hits
- websocket.txt — URLSessionWebSocketTask + send/ping hits
- pathmonitor.txt — NWPathMonitor + Reachability hits
- cachepolicy.txt — URLRequest.cachePolicy, URLCache, diskCapacity, memoryCapacity hits
- ats-info-plists.txt — NSAppTransportSecurity blocks extracted from each
  Info.plist (cross-ref to audit-apple-security for ATS specifics)

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002). Every finding MUST include an
Anchor — an Apple API symbol, framework reference, or RFC pointer
(e.g. Apple:URLSessionConfiguration, Apple:URLAuthenticationChallenge,
Apple:NWPathMonitor, Apple:URLSessionWebSocketTask, Apple:URLCache,
RFC:6749, RFC:7235, RFC:6455) — and a Category from: URLSessionConfig,
CertPinning, CachePolicy, NWPathMonitor, RetryBackoff, RequestSigning,
AuthTokenLifecycle, MultipartUpload, WebSocketURLSession, HTTP2HTTP3,
NetworkExtension, NetworkLogging. Platform: iOS, iPadOS, macOS,
MacCatalyst, watchOS, tvOS, visionOS, or Multi.

DO NOT review ATS or certificate pinning at the threat-model level
(MITM resistance, public-key vs cert pinning posture, ATS exception
audit) — that belongs in audit-apple-security. This audit treats
pinning as a discipline (rotation, multi-pin fallback, algorithm,
fallback path). DO NOT review iOS-distinctive background URLSession
lifecycle (BGTask wakeup, session-identifier handoff, app-suspended
uploads, `handleEventsForBackgroundURLSession`) — that belongs in
audit-apple-ios. This audit covers .background configuration *choice*
but stops at the iOS wakeup boundary. DO NOT review macOS-distinctive
NetworkExtension provider configuration depth (Content Filter / Packet
Tunnel / DNS Proxy provider configurations, system-extension
activation) — that belongs in audit-apple-macos.

Cover these 12 categories (skip if not applicable):

(1) URLSessionConfig — All platforms. URLSessionConfiguration.default
vs .ephemeral vs .background(withIdentifier:) chosen appropriately
for each call site. `.background` is iOS / iPadOS / visionOS only —
its *configuration choice* is audited here; its *wakeup lifecycle*
(BGTask handoff, `handleEventsForBackgroundURLSession`) lives in
audit-apple-ios. .default has a persistent on-disk URLCache + HTTPCookieStorage;
.ephemeral has neither; .background runs out-of-process and survives
app suspension. Per-session sharing strategy: one shared session per
role (Auth, Media, Analytics) is the canonical pattern; new-session-
per-request leaks. httpAdditionalHeaders discipline: Authorization
headers belong on the URLRequest, not the configuration (a
configuration-baked header rotates only when you rebuild the session).
timeoutIntervalForRequest defaults to 60s (too long for foreground UX);
timeoutIntervalForResource defaults to 7 days (too long for foreground,
appropriate only for background tasks).

(2) CertPinning — Pinning implementation via urlSession(_:didReceive:
completionHandler:) (URLAuthenticationChallenge) or NWConnection's
sec_protocol_options_set_verify_block. Pinning algorithm: SPKI (Subject
Public Key Info) hash rotates cleanly across cert renewals when the
key stays the same; cert-hash pinning forces an app update on every
cert renewal. Rotation strategy: multi-pin (current + next + backup)
gives a graceful rotation window. **Critical**: pinning hardcoded to
a single cert that expires within the audit window — every user is
locked out on cert renewal day with no client-side remediation.
Missing fallback path when the pin fails (cancelAuthenticationChallenge
without any user-facing affordance) → app appears broken.

(3) CachePolicy — URLRequest.cachePolicy set explicitly. Defaults are
useProtocolCachePolicy which honors server Cache-Control but is
surprising for app development. URLCache.shared.diskCapacity default
is too small for media-heavy apps. Cache invalidation strategy when
the server doesn't set Vary or ETag. Critical: an Authorization-bearing
request that hits URLCache.shared returns the same response to the
next user on a shared device — token cache poisoning.

(4) NWPathMonitor — NWPathMonitor for online/offline UI affordances
replaces the deprecated Reachability hack. Start with start(queue:);
cancel() when the observer is no longer needed. Continuous monitoring
that's never cancelled wastes battery and produces stale state if the
app reuses the monitor across app lifecycle transitions.

(5) RetryBackoff — Retry logic for 5xx / URLError network errors uses
exponential backoff with jitter (e.g. base * 2^attempt + Random in 0..base).
**Critical**: tight retry loop on 5xx with no backoff DDOS'es the
backend during a partial-outage incident. Maximum retry count required.
Idempotency-key handling for non-GET retries (so a retried POST doesn't
double-charge). Respect Retry-After header.

(6) RequestSigning — HMAC / AWS SigV4 / OAuth1 / OAuth2 client-side
signing implemented correctly. Canonical-string construction must
match server expectations exactly (case sensitivity in header names,
trailing newlines, sort order). Signature algorithm matches what the
server validates against. Signing on the main thread for
high-frequency requests stalls the UI.

(7) AuthTokenLifecycle — OAuth2 / OIDC access-token refresh via
refresh_token (RFC:6749). Concurrent-refresh deduplication: when the
app foregrounds with 10 in-flight requests that each hit a 401, you
want ONE refresh request, not 10. Token storage in Keychain is owned
by audit-apple-security — flag it as a cross-ref breadcrumb here.
Token redaction in logs: an Authorization header value should never
land in OSLog at .public privacy level (cross-ref to
audit-apple-observability).

(8) MultipartUpload — Multipart/form-data construction: boundary
uniqueness (UUID-based), Content-Length set correctly, trailing CRLF
after the final boundary. **Critical**: loading the full file into Data
before uploading OOMs on large assets (4K video from iOS Photo Library
~500MB). Use uploadTask(with:fromFile:) for streaming upload from
disk. Progress reporting via URLSessionTaskDelegate
urlSession(_:task:didSendBodyData:totalBytesSent:totalBytesExpectedToSend:).

(9) WebSocketURLSession — URLSessionWebSocketTask (iOS 13+) preferred
over Starscream / Socket.IO / custom. Ping/pong handling via
sendPing(pongReceiveHandler:); without pongs, the connection silently
dies behind a NAT timeout. Reconnection strategy with exponential
backoff (not tight reconnect-on-failure loop). Backpressure on the
receive side: receive() callback must drain or fall behind the server.
Explicit close codes (.normalClosure, .goingAway).

(10) HTTP2HTTP3 — URLSessionConfiguration defaults to HTTP/2 over TLS
(no manual opt-in needed; it negotiates). QUIC / HTTP/3 requires
assumesHTTP3Capable on the URLRequest (iOS 16+ / macOS 13+) AND server
Alt-Svc advertisement. Flag downgrades to HTTP/1.1 due to
misconfiguration (e.g. setting httpMaximumConnectionsPerHost=1 stalls
HTTP/2 multiplexing).

(11) NetworkExtension — iOS / iPadOS / macOS / tvOS / visionOS. VPN /
Content Filter / DNS Proxy extension correctness when the project
ships NE. On-demand rules in the NEVPNProtocol configuration.
Provider lifecycle (startTunnel / stopTunnel completion handlers).
Entitlement parity between host and extension
(com.apple.developer.networking.networkextension). macOS-distinctive
provider depth (system-extension activation flow, configuration UI in
System Settings, Packet Tunnel `NEAppProxyProvider` semantics) lives
in audit-apple-macos.

(12) NetworkLogging — Charles Proxy / mitmproxy / Wireshark visibility
during development. If cert pinning is on in Debug and the debug-
proxy CA isn't trusted, developers can't intercept their own traffic.
Flag conditional-pinning code that's effectively always-on, or a
debug-build CA-trust path that's missing. This is a hygiene category
for the dev loop, not a security issue.

Rate severity on evidence: impact (token leak across users, cert
renewal day brick, backend DDOS, OOM on uploads), reachability (auth
endpoints matter most), blast radius (every user vs one platform vs
one feature), compensating controls (backend rate limit, ATS, refresh-
token grace window).

Critical anchors:
- URLSessionConfiguration.default + Authorization header set on URLRequest →
  next user's auth response served from cache via URLCache (token cache
  poisoning)
- Pinning hardcoded to a single cert that expires within the audit
  window → every user locked out on cert renewal day
- Tight retry loop on 5xx with no exponential backoff → DDOS own
  backend during a partial-outage incident
- Multipart upload via Data(contentsOf:) for files of unbounded size
  → OOM termination on every device with less RAM than the host dev's
  iPhone 15 Pro Max

High anchors:
- URLSessionConfiguration.default (disk URLCache enabled) used for
  auth-bearing endpoints
- URLCache used for endpoints returning Set-Cookie or Authorization
  response headers
- WebSocket reconnect without backoff (tight reconnect loop on 429)
- OAuth refresh without concurrent-refresh deduplication (token storm
  on app foreground)
- Pinning to a single cert that expires 30–90 days outside the audit
  window

Every finding must include a Verification field — for networking this
is usually a proxy capture (Charles Proxy / mitmproxy with the device
debug cert installed), a Network Link Conditioner profile (System
Settings > Developer > Network Link Conditioner), or an XCTest that
asserts the configuration value (e.g. XCTAssertNil(session.configuration.urlCache)).
"Manual code review" alone is not sufficient verification for a
Critical finding.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
