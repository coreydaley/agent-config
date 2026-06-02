Perform a thorough Apple visionOS review of the scope at the project
root you've been pointed at. Tooling has already been run; raw output
is in the audit dir's tooling-raw/ subdirectory. Read those files
first:

- visionos-targets.txt — the visionOS-detection signals: which targets
  have XROS_DEPLOYMENT_TARGET set, the deployment-target value,
  Package.swift platforms array.
- scene-types.txt — every ImmersiveSpace / WindowGroup / Window /
  Volume / RealityView / .hoverEffect / .ornament usage in source.
  **Cross-referencing these against entitlements is the
  highest-yield activity for this audit.**
- arkit-providers.txt — ARKitSession + HandTrackingProvider /
  WorldTrackingProvider / SceneReconstructionProvider /
  PlaneDetectionProvider usages, plus PHASEEngine / SpatialAudioComponent.
- entitlements-per-target.txt — every .entitlements file in the
  project; check for `com.apple.developer.arkit.hand-tracking` against
  any HandTrackingProvider usage in arkit-providers.txt.
- info-plists.txt — Info.plist contents per target; check for
  `NSHandsTrackingUsageDescription` against HandTrackingProvider usage.
- usdz-assets.txt — USDZ / USDA / .reality file inventory with sizes.
  Anything >50MB is a "Memory crash" compound candidate.
- build-settings-debug.txt / build-settings-release.txt — XROS_DEPLOYMENT_TARGET
  and SUPPORTED_PLATFORMS resolution per configuration.

Write all findings to codex.md (in the audit dir you were granted
write access to) using this exact table format:

| ID | Severity | Anchor | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002). Every finding MUST include
an Anchor (e.g. `Apple:ImmersiveSpace`, `Apple:RealityView`,
`Entitlement:com.apple.developer.arkit.hand-tracking`,
`Apple:HoverEffect`, `File:Info.plist:NSHandsTrackingUsageDescription`,
`Apple:PHASEEngine`) and a Category from: SceneTypes, RealityKit,
ImmersiveSpaceLifecycle, GazePinch, Ornaments, SpatialAudio,
USDZAssets, HandTracking, WorldAnchors, AccessibilityVision,
InputModes, PrivacyHandTracking. Platform: almost always `visionOS`;
use `Multi` only when a shared scene-type usage affects more than one
platform.

DO NOT review visionOS *windowing* as part of broader adaptive UI
(size classes, multitasking, Mac Catalyst) — that belongs in
audit-apple-adaptivity. This skill covers RealityKit / ImmersiveSpace
/ gaze-pinch / hand-tracking depth. DO NOT audit the
PrivacyInfo.xcprivacy required-reason API declaration in detail —
that belongs in audit-apple-privacy. This skill flags the *absence*
of the declaration as a finding (PrivacyHandTracking category) but
the broader privacy-compliance audit lives separately.

Cover these 12 categories (skip if not applicable):

(1) SceneTypes — `WindowGroup` (regular SwiftUI window, multi-instance)
vs `Window` (single instance) vs `ImmersiveSpace` (immersive / full or
mixed) vs `Volume` (3D volumetric). Flag mixed scene types without a
clear UX rationale (an app jumping between Window and ImmersiveSpace
without intent confuses spatial mental model). Flag `defaultSize`
calls that specify volume dimensions in points rather than meters /
centimeters explicitly (use the `in: .meters` overload). Flag
`.windowStyle(.volumetric)` without `defaultSize` declaration.

(2) RealityKit — `RealityView` for 3D content (the visionOS path) vs
legacy `ARView` (deprecated for visionOS-only code). ECS pattern
correctness — `Component` + `System` rather than per-entity update
closures. Entity lifecycle (`addChild` / `removeFromParent` paired,
no orphaned entities). Loading USDZ via `Entity(named:in:)`
synchronously vs `Entity.load(named:in:)` async — synchronous load
of large USDZ on the main thread is the "Memory crash" candidate.

(3) ImmersiveSpaceLifecycle — `openImmersiveSpace(id:)` /
`dismissImmersiveSpace()` correctness; `ImmersionStyle`
(`.mixed` / `.progressive` / `.full`); error handling on space open
(`.userCancelled`, `.error` result cases handled, not silently
ignored); dismissal not awaited (`Task { await dismissImmersiveSpace() }`
is the correct pattern, fire-and-forget closure isn't); tracking
which space is currently presented; trying to open a second space
without dismissing the first (the system rejects this).

(4) GazePinch — Hover effect (`.hoverEffect(.highlight)` /
`.hoverEffect(.lift)`) on tappable elements — without one, the user
gazes at the element but has no feedback that the target acquired,
so the subsequent pinch tap appears to do nothing. Custom
`HoverEffectComponent` for RealityKit entities. `SpatialTapGesture`
for spatial-tap recognition. "Always-visible" UI patterns that don't
react to hover (flag for gaze-feedback gap).

(5) Ornaments — `.ornament(visibility:attachmentAnchor:contentAlignment:content:)`
for toolbar / inspector / control-strip affordances anchored around
windows. UIKit-style fixed top / bottom toolbars on visionOS should
be ornaments. Flag ornaments not localized.

(6) SpatialAudio — `PHASEEngine` for spatial audio; `SpatialAudioComponent`
on RealityKit entities for positional audio; `AmbientAudioComponent`
/ `ChannelAudioComponent` for non-positional. Flag mono / stereo
audio for in-volume sources that should be spatial (audio perceived
as stuck at center rather than localized to the entity position).

(7) USDZAssets — Asset pipeline via Reality Composer Pro for native
authoring; USDZ optimization (texture compression — typically ASTC,
polygon count in tens of thousands not millions, draw-call budget
per scene). Flag huge / unoptimized assets that bloat binary or RAM.
Vision Pro has ~8GB RAM shared with the system; a 200MB USDZ in a
Volume scene is a memory-crash candidate. Anything >50MB raw in
usdz-assets.txt is a candidate for the "Memory crash" compound
chain.

(8) HandTracking — `ARKitSession` with `HandTrackingProvider`;
entitlement `com.apple.developer.arkit.hand-tracking` MUST be
present in the target's `.entitlements`; Info.plist
`NSHandsTrackingUsageDescription` purpose string MUST be present.
Missing entitlement crashes the app at runtime when
`ARKitSession.run(_:)` is called with the hand-tracking provider.
Gesture recognition built on `HandSkeleton.Joint` data.

(9) WorldAnchors — `ARKitSession` + `WorldTrackingProvider` for
persistent placements; `WorldAnchor.id` stored locally (per-app
container) for re-attachment across launches; ARKit session
lifecycle (started in correct phase, stopped on backgrounding to
avoid sensor-budget drain — Apple actively rejects ARKit-leaking
apps).

(10) AccessibilityVision — VoiceOver in spatial UI (announcements
for window open / immersive-space transitions; spatial-audio cues
for sight-impaired users); high-contrast on volumetric content;
Reduce Motion adaptation for immersive content (no swirling
environment, gentler transitions); ensure tappable elements have
accessibility labels distinct from their hover labels.

(11) InputModes — Pointer (Bluetooth keyboard / trackpad) support
for users who pair input devices; eye-tracking-only as the primary
modality (the dominant mode); voice input via SiriKit / App Intents;
Look-to-Dictate (system input method on visionOS — exposed via the
standard text-input system, not custom).

(12) PrivacyHandTracking — Hand-tracking data is sensitive biometric
input. PrivacyInfo.xcprivacy required-reason API declaration for
hand-tracking data MUST be present if HandTrackingProvider is used.
Uplifting hand-tracking data to a server (analytics SDK, debugging,
training) without user consent / dialog is a privacy incident.
Cross-reference HandTrackingProvider usages in arkit-providers.txt
against PrivacyInfo.xcprivacy contents.

Rate severity on evidence: impact (runtime crash, App Review
rejection, user trapped in immersion, OOM termination, privacy
incident), reachability (does the path execute on first launch / on
entry to a specific flow / only worst-case), blast radius (every
user vs. specific flows), compensating controls (fallback when
`openImmersiveSpace` errors / async load already in place on the
worst-offender asset).

Critical anchors (visionOS-specific consequences):
- Hand tracking used without the `com.apple.developer.arkit.hand-tracking`
  entitlement (crashes on `ARKitSession.run` — app is unusable)
- Hand tracking used without `NSHandsTrackingUsageDescription` in
  Info.plist (crashes with TCC error)
- `ImmersiveSpace` opened without a dismissal handler / visible exit
  affordance on `.full` `ImmersionStyle` (user trapped — must
  crown-press to force-quit; documented App Review rejection)
- USDZ >50MB loaded synchronously on main thread via `Entity(named:)`
  inside `RealityView` (multi-second main-thread freeze, ANR-style
  termination on Vision Pro's smaller per-process memory budget)
- `HandTrackingProvider` without PrivacyInfo.xcprivacy required-reason
  API declaration (App Store rejects on submission + privacy-report
  flag)

High anchors:
- Volumetric content with mono / stereo audio (no `SpatialAudioComponent`,
  no `PHASEEngine` — audio perceived as stuck at center, breaks
  immersion)
- Missing `.hoverEffect()` on tappable elements (gaze-targeting fails
  silently — user can't tell the target acquired)
- `.mixed` or `.full` immersion without a visible exit affordance
- `ARKitSession` not stopped on scene transition / backgrounding
  (sensor leak, battery drain)

Every finding must include a Verification field. For visionOS this
is usually:
- `code` for entitlement / plist / file-size / scene-type-declaration
  findings (inspectable in the snapshot)
- `runtime` for gaze targeting, hand-tracking joint behavior,
  ImmersionStyle transition, spatial audio rendering, dismiss-affordance
  presence — these require a real Vision Pro device. Simulator
  approximates but does not reproduce eye / hand tracking or
  positional audio. "Manual code review" alone is not sufficient
  verification for a Critical runtime finding.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
