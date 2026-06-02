Perform a thorough Apple platform accessibility review of the scope at
the project root you've been pointed at against Apple's HIG
accessibility section and the platform's accessibility APIs (SwiftUI,
UIKit, AppKit, WatchKit). This audit runs no Phase 1 tooling — it is a
pure-LLM review against the categories and severity anchors below.

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Title | Location | API/Standard | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002).

API/Standard column: name the specific Apple API or HIG principle
(e.g. SwiftUI:.accessibilityLabel, UIKit:accessibilityTraits,
HIG:TouchTarget, HIG:DynamicType, HIG:ReduceMotion).

Platform column: iOS, iPadOS, macOS, MacCatalyst, watchOS, tvOS,
visionOS, or Multi.

Verification: code or runtime (where runtime means Accessibility
Inspector / VoiceOver / Switch Control / Voice Control / Full Keyboard
Access).

Cover these 10 categories (skip a category only when it is truly not
applicable to the scope):

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

(8) Touch targets and hit testing — iOS / iPadOS / watchOS / visionOS
(touch + gaze input). Interactive elements meet 44x44pt minimum
(iOS HIG); .contentShape(Rectangle()) used to expand hit areas where
visual size is smaller; spacing between tap targets. watchOS has its
own minimum target sizes (smaller absolute, larger relative —
`audit-apple-watchos`). visionOS gaze + pinch has distinct hit
testing semantics (`audit-apple-visionos`). On macOS this category is
not applicable in the touch sense — pointer + keyboard are the
primary input; for Mac pointer-target sizing and AppKit-specific
hit-testing, see `audit-apple-macos`.

(9) Announcements and live updates —
AccessibilityNotification.Announcement (the unified Swift
accessibility-notification API; works in SwiftUI, UIKit, and AppKit)
or the legacy UIAccessibility.post(notification: .announcement,
argument:) for transient status; .screenChanged / .layoutChanged on
major transitions; live regions for changing values.

(10) Hardware keyboard, Switch Control, Full Keyboard Access — All
platforms but with distinct emphasis. iOS / iPadOS: Switch Control
scan groups, hardware-keyboard navigation (iPad with Magic Keyboard).
macOS / MacCatalyst: Full Keyboard Access traversal order, focus
ring visibility, menu-bar keyboard equivalents — depth lives in
`audit-apple-macos`. tvOS: focus engine + Siri Remote. watchOS:
Digital Crown rotor — depth lives in `audit-apple-watchos`. visionOS:
gaze + pinch + Bluetooth keyboard — depth in `audit-apple-visionos`.
Custom controls are .focusable(); keyboardShortcut() where
appropriate; scan groups respect logical structure.

Grouping rule: when the same broken pattern appears across many
views, create one representative finding and document extent in
Evidence/Notes.

Rate severity on evidence: impact, exploitability, blast radius,
reachability, compensating controls.

Severity anchors:

- Critical — Interactive element with no accessibility label; missing
  focus management in modal/sheet that blocks task completion for AT
  users.
- High — Touch target below 44x44pt for a primary action; no Dynamic
  Type support on important text; missing Reduce Motion alternative
  for essential animation; color used as sole signal (no icon / text
  / pattern).
- Medium — Wrong or missing accessibility trait; decorative element
  not marked .accessibilityHidden(true); missing rotor entries / sort
  priority for complex view.
- Low — Label includes redundant trait suffix ("button button"); hint
  provided when label is self-explanatory.

Override upward when exclusion is severe, task blockage is total, or
breadth of affected users is large.

Every finding must include a Verification field — for Apple
accessibility this often means runtime verification with
Accessibility Inspector / VoiceOver / Switch Control / Voice Control
/ Full Keyboard Access on a built app.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
