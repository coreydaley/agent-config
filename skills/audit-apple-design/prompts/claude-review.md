You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough Apple platform design and UX review of the scope at
the project root you've been pointed at, anchored to Apple's Human
Interface Guidelines (HIG). The HIG is platform-aware — sheets,
popovers, toolbars, menus, modality, and navigation differ across iOS,
macOS, watchOS, tvOS, and visionOS — so each finding must record the
platform that owns the surface, and the HIG anchor must be the
platform-specific section (e.g. iOS HIG > Navigation, macOS HIG >
Toolbars). There is no Phase 1 tooling for this audit — design issues
come from manual reading of view code, asset catalogs, and Info.plist
against HIG.

Write all findings to claude.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | HIG | Category | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002). Every finding MUST include
the specific HIG principle (e.g. HIG:Navigation, HIG:Modality,
HIG:SF Symbols, HIG:Materials, HIG:Animation, HIG:Toolbars,
HIG:DarkMode) and a Category from: NativeIdiom, SFSymbols,
Colors&Materials, DarkMode, Navigation, Modality, Toolbars, Animation,
PlatformAffordance, DesignSystem. Platform: iOS, iPadOS, macOS,
MacCatalyst, watchOS, tvOS, visionOS, or Multi. Verification: code
(inspectable from source) or runtime (requires Simulator / device
review — animation timing, gesture feel, material rendering, motion).

If a project design system exists (custom Color extensions, modifier
libraries, component vendor folders, design tokens), it TAKES
PRECEDENCE over generic HIG. Findings should note deviations from the
design system in addition to HIG violations.

Cover these 10 categories (skip if not applicable):

(1) Native idiom usage — using stock SwiftUI / UIKit / AppKit
components vs reinventing them. Flag custom controls where Form, List,
Section, Menu, Picker, Toggle, Stepper, NavigationStack would work.

(2) SF Symbols — Image(systemName:) for iconography; appropriate
weight / rendering mode (hierarchical, palette, multicolor); custom
SF Symbols where needed; consistent symbol weight across a surface.

(3) System colors & materials — Color.accentColor / .primary /
.secondary / .background; Material (.regularMaterial, .thinMaterial);
flag hardcoded Color(red:green:blue:) for primary surfaces.

(4) Dark mode & color schemes — @Environment(\.colorScheme); assets
with light/dark variants in xcassets; semantic colors for foreground;
no hardcoded light-only colors on primary surfaces.

(5) Navigation patterns — platform-appropriate navigation. iOS / iPadOS:
NavigationStack (iPhone), NavigationSplitView (iPad), TabView, Sidebar.
macOS: NavigationSplitView with sidebar + content + detail, toolbar
back/forward; macOS-specific window-and-toolbar discipline (menu bar,
document-based, MenuBarExtra) is audited in audit-apple-macos. watchOS:
NavigationSplitView (watchOS 10+) or tab + page; Digital Crown
behavior is audited in audit-apple-watchos. tvOS: focus engine, side
nav. visionOS: ornaments + window groups; spatial layout is audited
in audit-apple-visionos. Appropriate navigation depth, back-button
behavior, deep-linking.

(6) Modality — Platform-specific. iOS / iPadOS: .sheet, .popover,
.fullScreenCover, .inspector, .alert, .confirmationDialog used
appropriately; modal stack depth; dismissal patterns. macOS: sheets
are window-attached, popovers are detached, inspector pane is a sidebar
or trailing panel — significantly different mental model from iOS.
watchOS: extremely shallow modal stack; alerts are typically the only
modal. visionOS: ornaments often replace traditional modals.

(7) Toolbar & menu placement — Platform-specific. iOS / iPadOS:
ToolbarItem placement (.primaryAction, .confirmationAction,
.cancellationAction, .bottomBar); context menus on long-press. macOS:
toolbar lives at top of window; menu bar (CommandGroup, CommandMenu)
is the primary command surface — depth here lives in audit-apple-macos.
context menus on right-click. watchOS: no toolbar; Digital Crown +
swipe instead. visionOS: ornaments outside the window perimeter.

(8) Animation appropriateness — withAnimation with semantic durations;
matched-geometry effects; transitions following the platform-specific
HIG (iOS animations vs macOS reduced motion expectations); no
gratuitous animation; honors accessibilityReduceMotion. visionOS has
distinct motion-sickness considerations — depth lives in
audit-apple-visionos.

(9) Platform-distinct affordances — Each platform owns a distinctive
affordance set. iOS: home indicator + safe area, Dynamic Island Live
Activity presentation (audit-apple-ios), Lock Screen / StandBy widget
visual depth (audit-apple-ios). iPadOS: pointer effects, sidebar,
multi-column, Apple Pencil + Magic Keyboard (audit-apple-ios). macOS:
window controls, sidebars, toolbar, menu bar discipline
(audit-apple-macos). visionOS: ornaments, spatial layout, gaze + pinch
(audit-apple-visionos). watchOS: list-row, complications, always-on
(audit-apple-watchos). tvOS: focus engine. This skill catches generic
"missing platform affordance" findings; depth lives in the platform
skills.

(10) Design system adherence — if a project design system exists,
note deviations from it. Token usage, component library compliance.

Rate severity on user impact, breadth of affected surface, task
interruption severity, how foreign the pattern feels on the platform.

Critical anchors:
- Component reinvented when a stock SwiftUI control exists and would
  work better on a primary user flow
- Navigation pattern fundamentally inappropriate for the platform
  (e.g. tab bar on macOS where a sidebar is expected)
- Dark mode broken across primary surfaces

High anchors:
- Major HIG violation on a primary surface
- Design-system deviation on a frequently-used component
- SF Symbols not used where iconography is expected
- Missing platform-distinct affordance on a primary flow

Every finding must include a Verification field. Animation timing,
gesture feel, and material rendering frequently require runtime
review — mark Verification=runtime where appropriate.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
