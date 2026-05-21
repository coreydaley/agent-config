# Apple Platform Accessibility Audit Reference

Schema and severity reference for the `/audit-apple-accessibility` command.
For web frontends, see [`../accessibility-web/README.md`](../accessibility-web/README.md).

Audit artifacts are written outside this repo to
`~/Reports/<org>/<repo>/audits/<TS>-accessibility-apple/` — `<org>/<repo>`
is derived from the `upstream` remote (falling back to `origin`), and
`<TS>` is the audit start timestamp (`YYYY-MM-DDTHH-MM-SS`).

## Output

Each audit run produces these files in its own timestamped
`$AUDIT_DIR`:

| File | Description |
|------|-------------|
| `claude.md` | Claude's independent Apple accessibility review (ID prefix `A`) |
| `codex.md` | Codex's independent Apple accessibility review (ID prefix `C`) |
| `synthesis.md` | Unified, deduplicated findings with calibrated severity (canonical `S`-prefix IDs); appends a "Rejected Devil's Advocate Challenges" section after Phase 4 |
| `devils-advocate.md` | Codex's challenge pass against the synthesis |
| `REPORT.md` | Final findings report (the human-facing artifact, P0/P1/Deferred sprint task layout) |

`REPORT.md` is reference material. To act on the findings, run
`/sprint-plan` with the report path as the seed prompt:

```
/sprint-plan ~/Reports/<org>/<repo>/audits/<TS>-accessibility-apple/REPORT.md
```

## Finding Schema

All intermediate audit files (`claude.md`, `codex.md`, `synthesis.md`) use
this table format:

```
| ID | Severity | Title | Location | API/Standard | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

`synthesis.md` adds a `Sources` column that lists the source review IDs
each unified finding merges (e.g. `A002, C003`).

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis canonical)

**Severity levels:** Critical, High, Medium, Low

**API/Standard column**: The named Apple API or HIG principle the
finding anchors to. Examples:
- `SwiftUI:.accessibilityLabel`, `SwiftUI:.accessibilityFocused`,
  `SwiftUI:.accessibilityElement(children:)`
- `UIKit:accessibilityTraits`, `UIKit:UIAccessibility.post`,
  `UIKit:isAccessibilityElement`
- `AppKit:accessibilityRole`, `AppKit:setAccessibilityLabel`
- `HIG:TouchTarget` (44×44 pt minimum), `HIG:DynamicType`,
  `HIG:ReduceMotion`, `HIG:ContrastMinimum`
- `WCAG:1.4.3` when citing the contrast ratio explicitly referenced by HIG

**Platform column**: Which Apple platforms are affected. Values:
`iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`,
or `Multi` for cross-platform code. Combine when relevant
(e.g. `iOS,iPadOS`).

**Verification column**: `code` (inspectable from source alone) or
`runtime` (requires Accessibility Inspector, VoiceOver, Switch Control,
Voice Control, Full Keyboard Access, or device testing).

**Default severity guidance** (starting point — override based on actual
VoiceOver / assistive-tech impact, breadth of affected users, and
whether the issue blocks a primary task flow):

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
| Missing rotor entries or sort priority for complex view | Medium |
| Label includes redundant trait suffix ("button button") | Low |
| Hint provided when label is self-explanatory | Low |

## Categories Reviewed

The subagent reviews ten Apple-platform-anchored categories:

1. Accessibility labels, hints, and values
2. Traits and semantic roles
3. Dynamic Type and typography scaling
4. Contrast, color usage, and visual accessibility settings (Increase
   Contrast, Differentiate Without Color, Reduce Transparency, Smart
   Invert)
5. Reduce Motion
6. Focus management and navigation order
7. Element grouping and rotor support
8. Touch targets and hit testing (HIG 44×44 pt minimum)
9. Announcements and live updates
10. Hardware keyboard, Switch Control, Voice Control, and Full Keyboard
    Access (iOS 14+ / macOS)

## Sprint Mapping

`REPORT.md` maps findings to sprint priorities:

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

## Inherent Limitations

These artifacts reflect static code review against Apple HIG and the
platform's accessibility APIs. They are a structured starting point, not
a conformance certification. Findings marked `runtime` in the Verification
column require Apple's accessibility tooling and on-device testing to
confirm:

- **VoiceOver** (Settings → Accessibility → VoiceOver on device, or
  Simulator) — verify label / hint / value announcements
- **Accessibility Inspector** (Xcode → Open Developer Tool) — audit
  Mac targets and iOS Simulator targets, including the Audit feature
- **Dynamic Type** (Settings → Accessibility → Display & Text Size →
  Larger Text) — verify AX1 through AX5 sizes don't break layout
- **Reduce Motion** / **Reduce Transparency** / **Increase Contrast** /
  **Differentiate Without Color** — toggle each and verify behavior
- **Switch Control** / **Voice Control** / **Full Keyboard Access**
  (iOS 14+) — verify complex / custom controls are reachable and operable
- **Xcode's Accessibility Audit** (Xcode 15+) — run alongside the LLM
  review for automated-checker coverage

## References

- Apple HIG — Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Accessibility on iOS: https://developer.apple.com/accessibility/ios/
- Accessibility on macOS: https://developer.apple.com/accessibility/macos/
- SwiftUI Accessibility documentation: https://developer.apple.com/documentation/swiftui/view-accessibility
- UIKit Accessibility documentation: https://developer.apple.com/documentation/uikit/accessibility_for_uikit
- AppKit NSAccessibility documentation: https://developer.apple.com/documentation/appkit/nsaccessibility
- WCAG 2.1 (referenced by HIG for contrast ratios): https://www.w3.org/TR/WCAG21/
- Subagent definition: [`../../subagents/audit-apple-accessibility.md`](../../subagents/audit-apple-accessibility.md)
