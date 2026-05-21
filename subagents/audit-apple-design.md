---
name: audit-apple-design
description: Dual-agent Apple platform design audit anchored to Apple HIG — native idiom usage, system colors / SF Symbols / materials, dark mode, navigation patterns, sheets / popovers / inspectors, animation appropriateness. For platform-agnostic / web design, use `audit-design`.
---

# Apple Platform Design Audit

You are orchestrating a dual-agent UI/UX audit of a native Apple app
anchored to Apple's Human Interface Guidelines (HIG).

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-design` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-design/`

**Scope**: Swift source files for native Apple apps. For web /
platform-agnostic design review, use `audit-design`. For adaptive
layout coverage, use `audit-apple-adaptivity`. For accessibility, use
`audit-apple-accessibility`.

**Inherent limitations**: LLM review against HIG can identify many
patterns but cannot validate visual rendering, animation timing,
gesture feel, or how a layout reads in motion. Findings marked
`runtime` require Simulator / on-device review.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `HIG` | The HIG principle or named guideline the finding anchors to (e.g. `HIG:Navigation`, `HIG:Modality`, `HIG:SF Symbols`, `HIG:Materials`, `HIG:Animation`) |
| `Platform` | `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi` |
| `Verification` | `code` (inspectable) or `runtime` (requires Simulator / device review) |

Full schema:
```
| ID | Severity | HIG | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

When a project has its own design system on top of HIG, the design
system **takes precedence**. The audit notes design-system
deviations in addition to HIG violations.

---

## Categories

The audit reviews ten categories:

| # | Category | Covers |
|---|---|---|
| 1 | Native idiom usage | Using stock SwiftUI / UIKit / AppKit components vs reinventing them; `Form`, `List`, `Section`, `Menu`, `Picker`, `Toggle`, `Stepper`, `NavigationStack` |
| 2 | SF Symbols | `Image(systemName:)` for iconography; appropriate symbol weight / rendering mode (`hierarchical`, `palette`, `multicolor`); fallback for custom symbols |
| 3 | System colors & materials | `Color.accentColor` / semantic colors (`.primary`, `.secondary`, `.background`); `Material` (`.regularMaterial`, `.thinMaterial`); avoid hardcoded `Color(red:green:blue:)` for primary surfaces |
| 4 | Dark mode & color schemes | `@Environment(\.colorScheme)`; assets with light/dark variants in `xcassets`; semantic colors for foreground; no hardcoded light-only colors |
| 5 | Navigation patterns | Platform-appropriate navigation: `NavigationStack` (iPhone), `NavigationSplitView` (iPad + Mac), `Sidebar`; navigation depth; back-button behavior; deep-linking |
| 6 | Modality — sheets / popovers / inspectors / alerts | `.sheet`, `.popover`, `.fullScreenCover`, `.inspector`, `.alert`, `.confirmationDialog` used appropriately; modal stack depth; dismissal patterns |
| 7 | Toolbar & menu placement | `ToolbarItem` placement (`.primaryAction`, `.confirmationAction`, `.cancellationAction`, `.bottomBar`); Mac menu bar (`CommandGroup`, `CommandMenu`); context menus |
| 8 | Animation appropriateness | `withAnimation` with semantic durations; matched-geometry effects; transitions that follow HIG guidance (slide, fade, scale); no gratuitous animation; honors `accessibilityReduceMotion` |
| 9 | Platform-distinct affordances | iPad-specific: hover effects, sidebar, multi-column. macOS-specific: window controls, sidebars, toolbar. visionOS: ornaments, spatial layout. watchOS: list-row, complication. tvOS: focus engine. |
| 10 | Design system adherence | If a project design system exists (custom `Color` extensions, modifier libraries, component library), findings note deviations from it |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | Component reinvented when a stock SwiftUI control exists and would work better; navigation pattern fundamentally inappropriate for the platform (e.g. tab bar on macOS); dark-mode broken across primary surfaces |
| **High** | Major HIG violation on a primary surface; design-system deviation on a frequently-used component; SF Symbols not used where iconography is expected |
| **Medium** | Suboptimal but functional native-idiom usage; minor HIG inconsistency; missing platform-distinct affordance on a secondary surface |
| **Low** | Aesthetic preference backed by HIG; minor design-system deviation; informational |

Severity is assessed on user impact, breadth of affected surface, and
how foreign the pattern feels on the platform.

---

## Phase 1: Audit-specific orient

### Tooling

None — pure-LLM audit.

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Identify Apple project artifacts and target platforms
- Detect framework usage via imports: `SwiftUI`, `UIKit`, `AppKit`,
  `WatchKit`, `RealityKit` (visionOS), `WidgetKit`
- **Check for a project design system**: custom `Color` extensions
  (`Color.appPrimary` etc.), modifier libraries, component
  vendor folders, design tokens
- Note Asset catalog (`*.xcassets/`) — color sets with light/dark
  variants, App Icon, Accent Color, custom SF Symbols
- Identify navigation patterns in use: `NavigationStack`,
  `NavigationSplitView`, `TabView`, sidebar patterns, custom
  navigation
- **If no Swift/Apple source found**: notify and stop

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple platform design and UX review of
[RESOLVED_SCOPE] against Apple's Human Interface Guidelines (HIG).
Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | HIG | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

HIG column: name the specific HIG principle (e.g. HIG:Navigation,
HIG:Modality, HIG:SF Symbols, HIG:Materials, HIG:Animation,
HIG:Toolbars, HIG:DarkMode).
Platform: iOS, iPadOS, macOS, MacCatalyst, watchOS, tvOS, visionOS,
or Multi.
Verification: code (inspectable from source) or runtime (requires
Simulator / device review).

If a project design system exists (custom Color extensions, modifier
libraries, component vendor folders), it TAKES PRECEDENCE over
generic HIG. Findings should note deviations from the design system
in addition to HIG violations.

Cover these 10 categories:
(1) Native idiom usage — using stock SwiftUI / UIKit / AppKit
components vs reinventing them. Flag custom controls where Form,
List, Section, Menu, Picker, Toggle, Stepper, NavigationStack would
work.
(2) SF Symbols — Image(systemName:) for iconography; appropriate
weight / rendering mode (hierarchical, palette, multicolor); custom
SF Symbols where needed.
(3) System colors & materials — Color.accentColor / .primary /
.secondary / .background; Material (.regularMaterial, .thinMaterial);
flag hardcoded Color(red:green:blue:) for primary surfaces.
(4) Dark mode & color schemes — @Environment(\.colorScheme); assets
with light/dark variants in xcassets; semantic colors for foreground;
no hardcoded light-only colors on primary surfaces.
(5) Navigation patterns — platform-appropriate navigation:
NavigationStack (iPhone), NavigationSplitView (iPad + Mac), Sidebar;
appropriate navigation depth; back-button behavior; deep-linking.
(6) Modality — .sheet, .popover, .fullScreenCover, .inspector,
.alert, .confirmationDialog used appropriately; modal stack depth;
dismissal patterns.
(7) Toolbar & menu placement — ToolbarItem placement (.primaryAction,
.confirmationAction, .cancellationAction, .bottomBar); Mac menu bar
(CommandGroup, CommandMenu); context menus.
(8) Animation appropriateness — withAnimation with semantic
durations; matched-geometry effects; transitions following HIG; no
gratuitous animation; honors accessibilityReduceMotion.
(9) Platform-distinct affordances — iPad hover effects, sidebar,
multi-column. macOS window controls, sidebars, toolbar. visionOS
ornaments, spatial layout. watchOS list-row, complication. tvOS
focus engine.
(10) Design system adherence — if project design system exists, note
deviations from it. Token usage, component library compliance.

Rate severity on user impact, breadth of affected surface, task
interruption severity, how foreign the pattern feels on the platform.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. If a project design system is detected, prioritize
design-system deviation findings over generic HIG findings. Note that
animation timing and gesture feel often require runtime review.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md. Your job is to attack it, not improve
it. Write your challenge to $AUDIT_DIR/devils-advocate.md covering:
(1) False positives — findings that reflect intentional design
choices or are platform-appropriate (e.g. a tab bar on macOS Catalyst
might be intentional for cross-platform consistency; a custom control
might exist for a deliberate brand reason).
(2) Severity miscalibrations — findings rated too high (aesthetic
preferences) or too low (broken navigation on the primary flow).
(3) Missing findings — design issues both reviewers missed,
especially: focus-engine handling on tvOS, Digital Crown on watchOS,
crown / ornament patterns on visionOS, Mac Catalyst menu bar gaps,
window-state restoration on macOS, App Icon variants (alternate
icons, tinted icons), Live Activity / Dynamic Island layouts.
(4) Remediation steps that are impractical or would introduce new
inconsistencies (e.g. switching to NavigationSplitView when the data
model doesn't fit).
Be specific. Every challenge must cite the finding ID and the HIG
section if applicable.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. Hand-off note: some design
remediations depend on shared tokens, design-system components, or
asset-catalog updates — review task ordering. Animation and gesture
findings benefit from a quick Simulator review before signing off.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, HIG principle, Platform,
      Verification mode, location, issue, remediation, verification
      guidance
- [ ] When a project design system is detected: design-system
      deviations dominate over generic HIG findings
- [ ] Runtime-verification note in hand-off — animation, gesture,
      and material findings benefit from Simulator review

---

## Reference

- Audit reference doc: [`docs/apple-design/README.md`](../docs/apple-design/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- Apple HIG: https://developer.apple.com/design/human-interface-guidelines/
- SF Symbols: https://developer.apple.com/sf-symbols/
- HIG — Materials: https://developer.apple.com/design/human-interface-guidelines/materials
- HIG — Animation: https://developer.apple.com/design/human-interface-guidelines/motion
- HIG — Dark Mode: https://developer.apple.com/design/human-interface-guidelines/dark-mode
