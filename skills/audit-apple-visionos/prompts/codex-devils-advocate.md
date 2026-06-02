Read synthesis.md and the raw tooling output in tooling-raw/ in the
audit dir you've been granted access to. Your job is to attack the
synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated |
  missing_finding | missing_compound | impractical_remediation |
  insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged
  (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, entitlement / plist key reference, or
  USDZ size from usdz-assets.txt
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't actually apply in context.
Specifically for Apple visionOS:
- A "missing hand-tracking entitlement" flagged on a target that
  doesn't actually use `HandTrackingProvider` (re-check
  arkit-providers.txt — `ARKitSession` instantiated without ever
  running the hand-tracking provider doesn't need the entitlement).
- A "trapped immersion" flagged on `.mixed` immersion is incorrect —
  mixed immersion always keeps the system UI / crown accessible, so
  the user is never trapped. Trapped-immersion is `.full` only,
  and even `.full` is not trapped if `onImmersionChange` is
  observed and there's an in-app exit affordance.
- A large USDZ flagged as a memory-crash candidate that's actually
  loaded via `Entity.load(named:in:)` async on a Task — async load
  off main thread is the correct pattern; only synchronous
  `Entity(named:in:)` on main is the crash candidate.
- A "no SpatialAudioComponent" finding on a `WindowGroup` (regular
  2D window) — spatial audio is for volumes / immersive content,
  not flat windows; stereo audio on a flat WindowGroup is correct.
- A "deprecated ARView" finding on iOS-shared code that's
  conditionally compiled out for visionOS via `#if os(visionOS)` —
  the iOS path may legitimately still use ARView while the
  visionOS path uses RealityView.

(2) Severity miscalibrations — findings rated too high (a missing
hover effect on a Settings-deep-cut surface that 1% of users reach
is High, not Critical; a large USDZ that's only loaded on user
opt-in to a specific scene isn't first-launch-bites-everyone) or too
low (a missing `com.apple.developer.arkit.hand-tracking` entitlement
on the only flow with `HandTrackingProvider` is always Critical, no
matter how niche the flow seems — the app crashes on entry; a
missing PrivacyInfo required-reason API for an actively-used
hand-tracking provider is always Critical — App Store rejects on
submission).

(3) Missing findings — visionOS issues both reviewers may have
missed:
- `RealityView` `update:` closure invoked on main thread doing
  heavy ECS work per frame (frame-rate collapse on dense scenes;
  closures should defer work to a System or off-main task).
- `WorldAnchor` IDs persisted across launches but the
  `WorldTrackingProvider` not re-run / not awaited on launch —
  anchors silently fail to re-attach because the provider hasn't
  produced a tracking origin yet.
- `ARKitSession.run` invoked from a view's `task { ... }` modifier
  but not stopped in the matching cleanup — session leaks across
  view re-renders, eventually `ARKitSession.Errors.sessionAlreadyRunning`.
- Missing `SupportedDestinations` / `XRSupportsAdditionalDevices`
  Info.plist keys when targeting both Vision Pro and (future) Vision
  family devices.
- Custom `HoverEffectComponent` with non-default geometry that
  doesn't cover the entire tappable bounds — gaze acquires the
  visual element but the hover effect highlights only part of it.
- `.ornament(visibility: .visible, ...)` always-visible ornament
  that should be context-sensitive — uses spatial-attention budget
  for no benefit.
- `Volume` scene with a `RealityView` whose root entity has no
  bounding-volume metadata — RealityKit can't cull, perf degrades.
- USDZ assets shipped with PBR textures uncompressed (no ASTC) —
  binary bloat, RAM bloat.
- `SpatialTapGesture` used but no `simultaneously(with:)` chain with
  `DragGesture` for entities that should also support drag —
  gesture-disambiguation failure.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse outcome than any single finding represents:
- "Trapped immersion" chain (`.full` `ImmersionStyle` + no dismiss
  affordance + `onImmersionChange` not observed) — already covered,
  but check whether all three conditions are actually present.
- "Memory crash" chain (large USDZ + synchronous Entity load +
  main-thread RealityView + Volume scene with multiple instances) —
  the combined memory pressure is much worse than any single
  finding.
- "Privacy leak" chain (`HandTrackingProvider` + no PrivacyInfo
  required-reason + remote analytics SDK configured to capture
  events) — the analytics SDK may exfiltrate hand-tracking data
  shapes via event metadata even if the developer never explicitly
  sends hand-joint coordinates.
- "Hand-tracking entitlement chain" (`HandTrackingProvider` +
  entitlement missing OR `NSHandsTrackingUsageDescription` missing) —
  either gap crashes; the synthesis should flag both as part of one
  chain rather than two independent findings.

(5) Impractical / incomplete / wrong remediations — e.g.:
- "Switch to async Entity.load" without specifying that the
  `RealityView` `make:` closure needs to be restructured to return
  a placeholder entity and swap in the loaded one — naive switch
  produces nil-content RealityViews on first render.
- "Add the entitlement to the target" without specifying that
  hand-tracking also requires a Developer Account capability toggle
  in App Store Connect / Xcode Signing & Capabilities — without
  the capability, the entitlement won't survive provisioning.
- "Add SpatialAudioComponent" without addressing the underlying
  audio asset — a mono asset attached as spatial audio still
  sounds mono; the asset itself needs to be a positional source.
- "Show a dismiss button" remediation that places the button
  inside the immersive content — once the user has lost spatial
  reference, finding a button in 3D is hard; an ornament-anchored
  affordance is more reliable.

(6) Verification steps that don't actually prove the fix works:
- "Verify the entitlement is in the .entitlements file" doesn't
  prove the capability survived provisioning — only post-archive
  `codesign --display --entitlements -` confirms the shipped binary
  carries the entitlement.
- "Verify in Vision Pro simulator" for any gaze, hand-tracking, or
  spatial-audio finding — simulator approximates but does not
  reproduce these. Real Vision Pro hardware is required.
- "Verify the PrivacyInfo.xcprivacy entry is present" doesn't
  prove App Privacy Report alignment — the report is generated on
  the device (Settings > Privacy & Security > App Privacy Report)
  and must be inspected there.
- "Verify Entity load is async" by reading the code — must be
  confirmed by Instruments (Spatial Compute / RealityKit) showing
  no main-thread hang during the load window.

Be specific. Every challenge must cite the finding ID and reference
the entitlement string / Info.plist key / file:line / USDZ size
where applicable.

Do not read or reference any other review file beyond synthesis.md
and the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted
  but found nothing worth surfacing.
- No emojis.
