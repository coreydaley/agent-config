You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough Apple platform architecture review of the scope at
the project root you've been pointed at. Focus on SwiftUI / Swift
Concurrency / Swift Package patterns.

This audit runs no Phase 1 tooling — architecture findings come from
manual code reading. Read at least 5 representative Swift files
(especially the top-level app entry, primary view tree, and primary view
model) before generalizing any pattern.

Write all findings to claude.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Pattern | Title | Location | Platform | Alternative | Migration Cost | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002).

Pattern column: name the specific pattern (e.g.
SwiftUI:StateOwnership, Concurrency:MainActor, Concurrency:Sendable,
Modules:PackageBoundary, Navigation:Stack, Observable:Granularity,
Errors:LocalizedError, DI:EnvironmentVsConstructor).
Platform: iOS, iPadOS, macOS, MacCatalyst, watchOS, tvOS, visionOS,
or Multi.
Alternative: concrete alternative pattern to move toward — REQUIRED.
"Investigate options for [issue]" is acceptable when no clear
alternative exists, but "refactor this" is not.
Migration Cost: Low, Medium, or High.

Every finding MUST include a named Pattern and a concrete
Alternative. Skip any observation that is purely aesthetic.

Cover these 10 categories:

(1) SwiftUI state ownership — @State / @Binding / @Bindable /
@Observable / @ObservedObject / @StateObject / @Environment /
@EnvironmentObject boundaries; state ownership at the appropriate
level; @StateObject vs @ObservedObject placement.

(2) Observable granularity — @Observable macro vs ObservableObject;
fine-grained observation vs whole-object invalidation; computed
properties triggering unnecessary updates.

(3) View body complexity — bodies should be simple; extract
sub-views; avoid heavy computation in body; deterministic body;
predictable identity (id:, Identifiable).

(4) @MainActor isolation — Views and view models on MainActor; UI
updates from background contexts; await MainActor.run boundaries;
shared mutable state isolated to an actor.

(5) Sendable conformance — value types Sendable by default; reference
types explicit; cross-actor boundaries; nonisolated annotations;
eliminating @unchecked Sendable shortcuts.

(6) Structured concurrency — async/await over completion handlers
and Combine where modern; async let / TaskGroup for parallelism; Task
cancellation propagated; Task lifecycle vs view lifecycle.

(7) Navigation patterns — NavigationStack with NavigationPath typed
routing; NavigationSplitView for multi-column; deep linking via
.onOpenURL / scenes; coordinator vs SwiftUI-native navigation.

(8) Modularization — Swift Package boundaries; module-public
surface; circular dependencies; vertical-slice vs layer modules;
feature modules vs core modules.

(9) Dependency direction & DI — inversion of control; protocols at
boundaries; concrete types vs protocols in views; environment-based
DI vs constructor injection; testable seams.

(10) Error handling & propagation — throws vs Result vs custom error
types; error propagation across Task boundaries; user-facing vs
developer-facing errors; recovery suggestions; LocalizedError
conformance.

Rate severity on: does this prevent correct behavior, impede
extensibility, or create systematic debt?

Critical anchors:
- Architectural pattern that prevents correct behavior (e.g. shared
  mutable state with no actor isolation causing data races)
- Circular module dependencies blocking builds

High anchors:
- Wholesale @unchecked Sendable everywhere
- Navigation pattern that breaks deep-linking
- Significant blockers to extensibility or repeated defect sources

Medium anchors:
- @StateObject in places where @ObservedObject would do
- Over-broad @Environment keys
- Missing module boundary on a hot feature

Low anchors:
- @Observable vs ObservableObject upgrade where the deployment
  target allows it
- Minor view-body simplification

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
