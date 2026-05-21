---
name: audit-apple-accessibility
description: Dual-agent Apple platform accessibility audit — native Apple UI (SwiftUI, UIKit, AppKit, WatchKit) against Apple HIG accessibility guidelines and platform accessibility APIs. For web frontends, use `audit-web-accessibility`.
---

# Apple Platform Accessibility Audit

You are orchestrating a dual-agent accessibility audit for native
Apple platform code (Swift / SwiftUI / UIKit / AppKit / WatchKit)
against Apple's HIG accessibility guidelines and platform accessibility
APIs.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-accessibility` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-accessibility/`

**Scope**: Swift source files for native Apple apps. Obj-C coverage is
intentionally light — assume Swift unless `.m`/`.mm` files dominate
the scope. For web frontends, use `audit-web-accessibility`.

**Inherent limitations**: Static review cannot validate VoiceOver
output, focus behavior, gesture recognition, or visual-settings
interactions without runtime testing in Xcode's Accessibility
Inspector and on-device with VoiceOver / Switch Control / Voice
Control / Full Keyboard Access. Findings marked `runtime` require
these tools to confirm.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `API/Standard` | The Apple API or HIG principle the finding anchors to (e.g. `SwiftUI:.accessibilityLabel`, `UIKit:accessibilityTraits`, `HIG:TouchTarget`, `HIG:DynamicType`) |
| `Platform` | `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi`. Combine when relevant. |
| `Verification` | `code` (inspectable) or `runtime` (requires Accessibility Inspector / VoiceOver / Switch Control / Voice Control / FKA testing) |

Full schema:
```
| ID | Severity | Title | Location | API/Standard | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews ten categories:

| # | Category | Covers |
|---|---|---|
| 1 | Labels, hints, values | `.accessibilityLabel` / `.accessibilityHint` / `.accessibilityValue` on every interactive view |
| 2 | Traits & semantic roles | `.accessibilityAddTraits` (`.isButton`, `.isHeader`, `.isLink`, `.isSelected`, `.isToggle`); custom controls declare correct roles |
| 3 | Dynamic Type & typography scaling | Semantic font styles, `@ScaledMetric`, AX1–AX5 layout integrity |
| 4 | Contrast, color, visual settings | Increase Contrast, Differentiate Without Color, Reduce Transparency, contrast ratios |
| 5 | Reduce Motion | `@Environment(\.accessibilityReduceMotion)` gating; alternative transitions |
| 6 | Focus management & navigation order | `@AccessibilityFocusState`, `.accessibilityFocused()`, `.accessibilitySortPriority`, focus restoration |
| 7 | Element grouping & rotor | `.accessibilityElement(children: .combine)`, `.accessibilityHidden(true)`, `.accessibilityRotor` |
| 8 | Touch targets & hit testing | 44×44 pt minimum (HIG); `.contentShape` expansion; tap-target spacing |
| 9 | Announcements & live updates | `AccessibilityNotification.Announcement`, `UIAccessibility.post`, `.screenChanged`/`.layoutChanged` |
| 10 | Hardware keyboard, Switch Control, FKA | `.focusable()`, `keyboardShortcut()`, Mac/Mac Catalyst keyboard nav, Switch Control scan order |

---

## Severity calibration

| Issue Type | Default Severity |
|---|---|
| Interactive element with no accessibility label | Critical |
| Missing focus management in modal/sheet | Critical |
| Touch target below 44×44 pt for a primary action | High |
| No Dynamic Type support on important text | High |
| Missing Reduce Motion alternative for essential animation | High |
| Color used as sole signal (no icon/text/pattern) | High |
| Wrong or missing accessibility trait | Medium |
| Decorative element not marked `.accessibilityHidden(true)` | Medium |
| Missing rotor entries / sort priority for complex view | Medium |
| Label includes redundant trait suffix ("button button") | Low |
| Hint provided when label is self-explanatory | Low |

Override upward when exclusion is severe, task blockage is total, or
breadth of affected users is large.

---

## Phase 1: Audit-specific orient

### Tooling

None — pure-LLM audit. Reviewers note any existing snapshot/UI test
coverage with accessibility checks (e.g. `SnapshotTesting` with
accessibility snapshots, `AccessibilitySnapshot`, XCUITest a11y
queries, Xcode's built-in Accessibility Audit).

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Identify Apple project artifacts: `Package.swift` (+ `Package.resolved`),
  `*.xcodeproj/`, `*.xcworkspace/`, `Info.plist`, `*.xcassets/`,
  storyboards/XIBs
- Identify Swift files; detect framework via imports (`import SwiftUI`,
  `import UIKit`, `import AppKit`/`import Cocoa`, `import WatchKit`)
- Read `Package.swift` `platforms` array or `Info.plist` to determine
  target platforms — affects valid `Platform` values
- **If no Swift/Obj-C source found**: notify and stop, suggest
  `/audit-web-accessibility` if it looks like a web project

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple platform accessibility review of
[RESOLVED_SCOPE] against Apple HIG accessibility section and the
platform's accessibility APIs (SwiftUI, UIKit, AppKit, WatchKit).
Write all findings to $AUDIT_DIR/codex.md using this exact table
format for each finding:
| ID | Severity | Title | Location | API/Standard | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

API/Standard column: name the specific Apple API or HIG principle
(e.g. SwiftUI:.accessibilityLabel, UIKit:accessibilityTraits,
HIG:TouchTarget, HIG:DynamicType, HIG:ReduceMotion).
Platform column: iOS, iPadOS, macOS, MacCatalyst, watchOS, tvOS,
visionOS, or Multi.
Verification: code or runtime (where runtime means Accessibility
Inspector / VoiceOver / Switch Control / Voice Control / FKA).

Cover these 10 categories:
(1) Accessibility labels, hints, and values — every interactive view
(Button, TextField, Toggle, tappable Image, custom hit-test areas)
has accessibilityLabel; hints describe action not appearance; values
for stateful controls.
(2) Accessibility traits and semantic roles — correct traits applied
(.isButton, .isHeader, .isLink, .isImage, .isSelected, .isToggle);
custom controls have appropriate roles.
(3) Dynamic Type and typography scaling — uses semantic font styles
(.font(.body), .font(.headline)) or @ScaledMetric; avoids hardcoded
point sizes; supports AX1-AX5 accessibility sizes; layouts adapt
without truncation.
(4) Contrast, color usage, and visual settings — supports Increase
Contrast (@Environment(\.colorSchemeContrast)); Differentiate Without
Color (information not conveyed by color alone); Reduce Transparency;
minimum contrast ratios.
(5) Reduce Motion — @Environment(\.accessibilityReduceMotion) or
UIAccessibility.isReduceMotionEnabled checked before non-essential
animations; alternative transitions; parallax / auto-play honored.
(6) Focus management and navigation order — @AccessibilityFocusState
/ .accessibilityFocused() used to move focus on screen changes, modal
presentations, error states; .accessibilitySortPriority for
intentional traversal order; focus restored when modals dismiss.
(7) Element grouping and rotor support —
.accessibilityElement(children: .combine) on logically-grouped views;
.accessibilityHidden(true) on decorative elements;
.accessibilityRotor for custom navigation in long lists.
(8) Touch targets and hit testing — interactive elements meet 44x44pt
minimum (HIG); .contentShape(Rectangle()) used to expand hit areas
where visual size is smaller; spacing between tap targets.
(9) Announcements and live updates —
AccessibilityNotification.Announcement (the unified Swift
accessibility-notification API; works in SwiftUI, UIKit, and AppKit)
or the legacy UIAccessibility.post(notification: .announcement,
argument:) for transient status; .screenChanged / .layoutChanged on
major transitions; live regions for changing values.
(10) Hardware keyboard, Switch Control, Full Keyboard Access — custom
controls are .focusable(); keyboardShortcut() where appropriate; Mac
and Mac Catalyst keyboard navigation works; Switch Control scan
groups respect logical structure.

Grouping rule: when the same broken pattern appears across many
views, create one representative finding and document extent in
Evidence/Notes.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. Note that focus behavior, VoiceOver phrasing,
Switch Control navigation, and Voice Control labels often require
runtime verification — mark Verification column `runtime` accordingly.
Apply the grouping rule.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md. Your job is to attack it, not improve
it. Write your challenge to $AUDIT_DIR/devils-advocate.md covering:
(1) False positives — findings that are actually accessible in
context (e.g. a parent .accessibilityElement(children: .combine)
already provides the label; a SwiftUI Label view supplies the label
implicitly; a system control already has appropriate default traits).
(2) Severity miscalibrations — findings rated too high or too low
given the actual VoiceOver/Switch Control impact and user exclusion
severity.
(3) Missing findings — Apple accessibility issues both reviewers
missed, especially: focus traps in sheets/modals, missing
announcements on async state changes, Dynamic Type breakage at AX
sizes, Mac Catalyst keyboard gaps, watchOS Digital Crown focus,
visionOS-specific accessibility, App Intents accessibility, widget /
Live Activity accessibility.
(4) Remediation steps that are incorrect, incomplete, or would
introduce new issues (e.g. adding redundant trait suffixes,
over-using .accessibilityHidden).
Be specific. Every challenge must cite the finding ID and the Apple
API or HIG principle if applicable.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. Hand-off note: many Apple
accessibility findings require runtime verification (VoiceOver /
Accessibility Inspector / Switch Control / Voice Control / FKA) —
include this in task execution for items marked `runtime`.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, API/Standard, platform, verification
      mode, location, issue, remediation, verification guidance
- [ ] Runtime-verification note included in hand-off
- [ ] When platform list includes macOS: confirm Mac-specific patterns
      (Full Keyboard Access, custom NSView accessibility, AppKit
      accessibility APIs) were reviewed

---

## Reference

- Audit reference doc: [`docs/apple-accessibility/README.md`](../docs/apple-accessibility/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- Apple HIG — Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- SwiftUI Accessibility: https://developer.apple.com/documentation/swiftui/view-accessibility
- UIKit Accessibility: https://developer.apple.com/documentation/uikit/accessibility_for_uikit
- AppKit NSAccessibility: https://developer.apple.com/documentation/appkit/nsaccessibility
- WCAG 2.1 (referenced by HIG for contrast): https://www.w3.org/TR/WCAG21/
