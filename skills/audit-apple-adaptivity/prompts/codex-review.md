Perform a thorough Apple adaptive-UI audit of the scope at the project
root you've been pointed at. There is no Phase 1 tooling for this audit
— it's a pure code-reading review. Note any existing snapshot tests
(SnapshotTesting, iOSSnapshotTestCase, preview macros with multiple
device traits) as a signal of which configurations the project actually
exercises.

Write all findings to codex.md (in the audit dir you've been granted
write access to) using this exact table format:

| ID | Severity | Surface | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002).

Surface column: SizeClass, Orientation, Multitasking, DynamicType,
Windowing, or DeviceSize.

Platform column: iOS, iPadOS, macOS, MacCatalyst, watchOS, tvOS,
visionOS, or Multi.

Verification: code (inspectable from source) or runtime (requires
Simulator / device testing across configurations).

Cover these 10 categories:

(1) Size class adaptation — @Environment(\.horizontalSizeClass) /
\.verticalSizeClass usage in SwiftUI; UITraitCollection in UIKit;
compact vs regular distinct layouts where appropriate.

(2) ViewThatFits & adaptive layouts — modern SwiftUI adaptive
primitives used where appropriate; fallback chains.

(3) Orientation — landscape vs portrait handling;
supportedInterfaceOrientations correctness; SwiftUI orientation
observation where needed.

(4) iPad multitasking — iOS / iPadOS only. Slide Over / Split View /
Stage Manager support; multiple-window scenes via UIWindowScene /
WindowGroup; state restoration; UIRequiresFullScreen flagged for
iPad apps that need to support multitasking. The iOS-specific
Info.plist key depth (UIApplicationSceneManifest,
UIRequiresFullScreen) lives in audit-apple-ios.

(5) Mac Catalyst — Mac Catalyst only. targetEnvironment(macCatalyst)
adaptations; menu bar; pointer interactions; sidebars; window
controls. Mac Idiom vs iPad-on-Mac choice + AppKit↔SwiftUI hosting
depth lives in audit-apple-macos.

(6) macOS-native — macOS only. Resizable windows; min/max content
size; multiple-window groups; toolbar adaptation; resizable
sidebars. MenuBarExtra, Settings scene, document-based apps via
DocumentGroup live in audit-apple-macos.

(7) visionOS windowing — visionOS only. WindowGroup vs
ImmersiveSpace; ornaments; coexistence with other apps' windows;
volume / volumetric content. RealityKit / RealityView / gaze-pinch
depth lives in audit-apple-visionos — this category covers the
windowing surface only.

(8) Dynamic Type AX5 layout — layouts must not truncate or clip at
AX5; lineLimit(nil) for wrappable text; fixed-height containers
flagged when text can grow; Layout protocol for adaptive layouts.

(9) Device size adaptation — iPhone SE through Pro Max ranges; iPad
mini through Pro 12.9"; safe area / Dynamic Island / notch handling;
no hardcoded dimensions for primary content.

(10) Pointer & keyboard adaptation (iPad / Mac / Mac Catalyst /
visionOS) — .hoverEffect() on tappable views; onContinuousHover
where relevant; pointer styles; keyboard shortcuts; hardware-keyboard
navigation. iPad-specific pencil / pointer / Magic Keyboard
affordance depth lives in audit-apple-ios.

Rate severity on: does this block a primary user flow at a common
configuration? Does it crash or hang during a transition? How common
is the affected configuration in the project's actual user base?

Critical anchors:
- Primary user flow inaccessible at a common configuration (Split
  View, AX5 Dynamic Type, landscape)
- App crashes or hangs on orientation / multitasking transition

High anchors:
- Content truncated or clipped on iPhone SE / iPad mini for a primary
  surface
- AX5 Dynamic Type breaks layout on a primary surface
- No multiple-window support on iPadOS / macOS for a use case that
  warrants it

Mark Verification carefully — most adaptivity findings only manifest
in Simulator at specific configurations and should be runtime.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
