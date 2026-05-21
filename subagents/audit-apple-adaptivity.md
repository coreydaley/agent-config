---
name: audit-apple-adaptivity
description: Dual-agent Apple adaptive-UI audit — size classes, iPad multitasking (Slide Over / Split View / Stage Manager), visionOS windowing, Dynamic Type AX5 layout integrity, orientation, device-size adaptation, ViewThatFits usage, Mac Catalyst adaptation. The Apple-native analogue of `audit-web-responsive`.
---

# Apple Adaptive UI Audit

You are orchestrating a dual-agent audit of how a native Apple app
adapts to different size classes, orientations, multitasking modes,
and accessibility-driven text sizes.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-adaptivity` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-adaptivity/`

**Scope**: Swift source files for native Apple apps. For web frontend
responsive behavior, use `audit-web-responsive` instead.

**Inherent limitations**: Static code review can identify structural
adaptivity issues but cannot validate visual reflow, gesture
interaction, or window-management behavior without runtime testing on
device or in Simulator. Findings marked `runtime` require Simulator
testing at multiple device sizes, orientation toggles, AX1-AX5
Dynamic Type, and (for iPad/visionOS) multitasking-mode testing.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Surface` | The adaptive surface affected: `SizeClass`, `Orientation`, `Multitasking`, `DynamicType`, `Windowing`, `DeviceSize` |
| `Platform` | `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi` |
| `Verification` | `code` (inspectable) or `runtime` (requires Simulator / device testing across configurations) |

Full schema:
```
| ID | Severity | Surface | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews ten categories:

| # | Category | Covers |
|---|---|---|
| 1 | Size class adaptation | `@Environment(\.horizontalSizeClass)` / `\.verticalSizeClass` usage; UIKit `traitCollection`; compact vs regular layouts |
| 2 | `ViewThatFits` & adaptive layouts | Modern SwiftUI adaptive primitives; fallback chains; conditional layouts |
| 3 | Orientation | Landscape vs portrait handling; `supportedInterfaceOrientations`; SwiftUI orientation observation |
| 4 | iPad multitasking | Slide Over / Split View / Stage Manager support; multiple-window scenes (`UIWindowScene`, `WindowGroup`); state restoration across scenes |
| 5 | Mac Catalyst adaptation | `if targetEnvironment(macCatalyst)`; menu bar; window controls; pointer interactions; sidebars |
| 6 | macOS-native (AppKit/SwiftUI on macOS) | Resizable windows; min/max content size; window restoration; multiple-window groups; toolbar adaptation |
| 7 | visionOS windowing | `WindowGroup` for windowed apps; `ImmersiveSpace` for fully-immersive; ornaments; coexistence with other windows |
| 8 | Dynamic Type AX5 layout | Layouts must not truncate or clip at AX5 (`UIContentSizeCategoryAccessibilityExtraExtraExtraLarge`); `lineLimit(nil)` where text can wrap; `Layout` protocol for adaptive containers; no fixed-height containers around text |
| 9 | Device size adaptation | iPhone SE / mini → iPhone Pro Max ranges; iPad mini → iPad Pro 12.9"; safe area handling; Dynamic Island vs notch vs no-cutout |
| 10 | Pointer & keyboard adaptation (iPad / Mac / Mac Catalyst) | `.hoverEffect()`; `onContinuousHover`; pointer styles; keyboard shortcuts where relevant; hardware-keyboard navigation |

---

## Severity calibration

| Issue Type | Default Severity |
|---|---|
| Primary user flow inaccessible at a common configuration (split view, AX5, landscape) | Critical |
| App crashes or hangs on orientation / multitasking transition | Critical |
| Content truncated or clipped on iPhone SE / iPad mini for a primary surface | High |
| AX5 Dynamic Type breaks layout on a primary surface | High |
| No multiple-window support on iPadOS / macOS for a use case that warrants it | High |
| Hover / pointer interactions missing on Mac Catalyst | Medium |
| Static layout that should use `ViewThatFits` or `Layout` for resilience | Medium |
| Suboptimal but functional adaptation | Low |

Override upward when the issue blocks a primary user flow at a common
device size; override downward when the affected configuration is rare
in the project's actual user base.

---

## Phase 1: Audit-specific orient

### Tooling

None — pure-LLM audit. Reviewers note any existing snapshot tests
covering multiple device sizes (e.g. `SnapshotTesting` matrices).

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Identify Apple project artifacts and target platforms
  (`Package.swift` `platforms`, `Info.plist` device family,
  `UIDeviceFamily`, `UISupportedInterfaceOrientations`,
  `UIRequiredDeviceCapabilities`)
- Detect frameworks in use: SwiftUI (`WindowGroup`, `Scene`),
  UIKit (`UIWindowScene`, `UISceneDelegate`), AppKit, Mac Catalyst
  (`targetEnvironment(macCatalyst)` checks)
- Check `Info.plist` for `UIApplicationSupportsMultipleScenes`,
  `UIRequiresFullScreen` (iPad), `UISupportsDocumentBrowser`
- Identify size-class-aware code via grep for
  `horizontalSizeClass`, `verticalSizeClass`, `traitCollection`,
  `ViewThatFits`, `dynamicTypeSize`
- For visionOS: check for `ImmersiveSpace`, `RealityView`, `Volume`
- **If no Swift/Apple source found**: notify and stop, suggest
  `/audit-web-responsive` if it looks web

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple adaptive-UI audit of [RESOLVED_SCOPE].
Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
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
(4) iPad multitasking — Slide Over / Split View / Stage Manager
support; multiple-window scenes via UIWindowScene / WindowGroup;
state restoration; UIRequiresFullScreen flagged for iPad apps that
need to support multitasking.
(5) Mac Catalyst — targetEnvironment(macCatalyst) adaptations; menu
bar; pointer interactions; sidebars; window controls.
(6) macOS-native — resizable windows; min/max content size;
multiple-window groups; toolbar adaptation; resizable sidebars.
(7) visionOS windowing — WindowGroup vs ImmersiveSpace; ornaments;
coexistence with other apps' windows; volume / volumetric content.
(8) Dynamic Type AX5 layout — layouts must not truncate or clip at
AX5; lineLimit(nil) for wrappable text; fixed-height containers
flagged when text can grow; Layout protocol for adaptive layouts.
(9) Device size adaptation — iPhone SE through Pro Max ranges; iPad
mini through Pro 12.9"; safe area / Dynamic Island / notch handling;
no hardcoded dimensions for primary content.
(10) Pointer & keyboard adaptation (iPad / Mac / Mac Catalyst) —
.hoverEffect() on tappable views; onContinuousHover where relevant;
pointer styles; keyboard shortcuts; hardware-keyboard navigation.

Rate severity on: does this block a primary user flow at a common
configuration? Does it crash or hang during a transition? How common
is the affected configuration in the project's actual user base?

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. Mark `Verification` carefully — most adaptivity
findings only manifest in Simulator at specific configurations.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md. Your job is to attack it, not improve
it. Write your challenge to $AUDIT_DIR/devils-advocate.md covering:
(1) False positives — findings that don't apply because the affected
configuration isn't supported by the app's declared target (e.g. a
visionOS finding on an iPhone-only app; a Mac Catalyst finding when
Mac is not a deployment target).
(2) Severity miscalibrations — findings rated too high (rare
configurations in actual user base) or too low (Dynamic Type AX5 is
not actually that rare).
(3) Missing findings — adaptivity issues both reviewers missed,
especially: state restoration across scenes, Stage Manager
multi-window flows, window pinning on iPadOS, keyboard-only
navigation on Mac Catalyst, sidebar collapse behavior, RTL +
adaptive-layout interaction, watchOS Digital Crown adaptation.
(4) Remediation steps that are incorrect or would break other
configurations.
Be specific. Every challenge must cite the finding ID and the
affected Surface / Platform.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. Hand-off note: most findings
require Simulator verification at multiple device sizes + orientations
+ AX Dynamic Type sizes. Specify the verification configuration per
task.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, Surface, Platform, Verification
      mode, location, issue, remediation, verification matrix
      (device sizes + orientation + AX size)
- [ ] Runtime-verification note included in hand-off — at minimum
      test on iPhone SE, iPhone Pro Max, iPad mini, iPad Pro 12.9";
      AX1 + AX5 Dynamic Type; portrait + landscape; Split View on
      iPad
- [ ] Mac Catalyst / macOS / visionOS findings reviewed only where
      those are declared targets

---

## Reference

- Audit reference doc: [`docs/apple-adaptivity/README.md`](../docs/apple-adaptivity/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- Apple HIG — Adaptivity and Layout: https://developer.apple.com/design/human-interface-guidelines/layout
- Apple HIG — Multitasking on iPad: https://developer.apple.com/design/human-interface-guidelines/multitasking
- Mac Catalyst: https://developer.apple.com/mac-catalyst/
- visionOS: https://developer.apple.com/visionos/
- SwiftUI ViewThatFits: https://developer.apple.com/documentation/swiftui/viewthatfits
- SwiftUI Layout protocol: https://developer.apple.com/documentation/swiftui/layout
