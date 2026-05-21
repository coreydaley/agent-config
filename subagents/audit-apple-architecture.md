---
name: audit-apple-architecture
description: Dual-agent Apple platform architecture audit — SwiftUI state ownership (@State / @Binding / @Bindable / @Observable / @Environment boundaries), @MainActor isolation, Sendable conformance, structured concurrency patterns, navigation, modularization via Swift Packages. For platform-agnostic architecture review, use `audit-architecture`.
---

# Apple Platform Architecture Audit

You are orchestrating a dual-agent architecture audit of native Apple
app code, focused on SwiftUI / Swift Concurrency / Swift Package
patterns.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-architecture` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-architecture/`

**Scope**: Swift source files for native Apple apps. For
platform-agnostic architecture principles (SOLID, coupling, cohesion,
DRY/YAGNI) that apply to any codebase, use `audit-architecture` —
prefer that one for cross-platform projects.

**Inherent limitations**: Architecture findings are
hypothesis-generating, not prescriptive. SwiftUI / actor / Sendable
correctness is partly enforced by the compiler, but design choices
around state ownership, modularization, navigation, and async
boundaries are context-dependent. Treat each finding as requiring
team validation.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Pattern` | Named Swift / SwiftUI pattern the finding anchors to (e.g. `SwiftUI:StateOwnership`, `Concurrency:MainActor`, `Concurrency:Sendable`, `Modules:PackageBoundary`, `Navigation:Stack`, `Observable:Granularity`) |
| `Platform` | `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, or `Multi` |
| `Alternative` | Concrete alternative pattern to move toward — required, like in `audit-architecture` |
| `Migration Cost` | `Low`, `Medium`, or `High` |

Full schema:
```
| ID | Severity | Pattern | Title | Location | Platform | Alternative | Migration Cost | Why It Matters | Recommended Fix | Evidence/Notes |
```

**Evidence discipline**: A finding without a named `Pattern` and a
concrete `Alternative` is **not a valid finding** and must be omitted.

---

## Categories

The audit reviews ten categories:

| # | Category | Covers |
|---|---|---|
| 1 | SwiftUI state ownership | `@State` / `@Binding` / `@Bindable` / `@Observable` / `@ObservedObject` / `@StateObject` / `@Environment` / `@EnvironmentObject` boundaries; state ownership at the appropriate level; passing `@Binding` vs reading from environment; `@StateObject` placement |
| 2 | Observable granularity | `@Observable` macro usage vs `ObservableObject` (legacy); fine-grained observation vs whole-object invalidation; computed properties that trigger unnecessary updates |
| 3 | View body complexity | Bodies should be simple; extract sub-views; avoid heavy computation in body; deterministic body; predictable identity |
| 4 | `@MainActor` isolation | Views and view models on MainActor; UI updates from background contexts; `await MainActor.run` boundaries; isolating shared mutable state to an actor |
| 5 | `Sendable` conformance | Value types Sendable by default; reference types explicit; cross-actor function boundaries; `nonisolated` annotations; eliminating `@unchecked Sendable` shortcuts |
| 6 | Structured concurrency | `async`/`await` over completion handlers and Combine where modern; `async let` / `TaskGroup` for parallelism; `Task` cancellation propagated; `Task` lifecycle vs view lifecycle |
| 7 | Navigation patterns | `NavigationStack` with `NavigationPath` typed routing; `NavigationSplitView` for multi-column; deep linking via `.onOpenURL` / scenes; coordinator vs SwiftUI-native navigation |
| 8 | Modularization | Swift Package boundaries; module-public surface; circular dependencies; vertical slice modules vs layer modules; feature modules vs core modules |
| 9 | Dependency direction & DI | Inversion of control; protocols at boundaries; concrete types vs protocols in views; environment-based DI vs constructor injection; testable seams |
| 10 | Error handling & propagation | `throws` vs `Result` vs custom error types; error propagation across `Task` boundaries; user-facing vs developer-facing errors; recovery suggestions; `LocalizedError` conformance |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | Architectural pattern that prevents correct behavior or creates an unmaintainable trajectory (e.g. shared mutable state with no actor isolation causing data races; circular module dependencies blocking builds) |
| **High** | Significantly impedes extensibility, causes repeated defects, or creates systematic blind spots (e.g. wholesale `@unchecked Sendable` everywhere; navigation pattern that breaks deep-linking) |
| **Medium** | Notable friction, inconsistency, or a pattern that degrades over time (e.g. `@StateObject` in places where `@ObservedObject` would do; over-broad `@Environment` keys; missing module boundary on a hot feature) |
| **Low** | Minor improvement backed by a named pattern (e.g. could use `@Observable` instead of `ObservableObject` for better performance; minor view-body simplification) |

---

## Phase 1: Audit-specific orient

### Tooling

None — pure-LLM audit. Reviewers note any existing `swift-format`
configuration, SwiftLint rules, or Build Settings (`SWIFT_STRICT_CONCURRENCY=complete`,
`SWIFT_VERSION`, deployment target) since they constrain what
patterns are even possible.

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Identify Apple project structure: `Package.swift` (+ `targets:` /
  `dependencies:`), `*.xcodeproj/`, Swift Package module count and
  layout
- Note `SWIFT_STRICT_CONCURRENCY` setting and Swift version — if
  strict, expect Sendable / actor compliance and findings are about
  pattern quality; if minimal, expect raw correctness gaps too
- Identify the navigation pattern in use (`NavigationStack` /
  `NavigationSplitView` / `TabView` / coordinator-style)
- Identify state-management style: `@Observable` macro (modern),
  `ObservableObject` (legacy), TCA (`Reducer`), custom flux-style
- Detect dependency direction: are views importing concrete
  models, or protocols? are modules layered or feature-sliced?
- Read at least 5 representative Swift files (especially top-level
  app entry, primary view tree, primary view model) before
  generalizing

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple platform architecture review of
[RESOLVED_SCOPE]. Focus on SwiftUI / Swift Concurrency / Swift
Package patterns.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | Pattern | Title | Location | Platform | Alternative | Migration Cost | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

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
extensibility, or create systematic debt? Read at least 5
representative files before generalizing any pattern.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. Evidence discipline applies: every finding has a
named `Pattern` and a concrete `Alternative`. Read at least 5
representative Swift files before generalizing.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md. Your job is to attack it, not improve
it. Write your challenge to $AUDIT_DIR/devils-advocate.md covering:
(1) False positives — patterns flagged as "wrong" that are actually
fine for this project's scale, deployment target, or constraints
(e.g. ObservableObject is fine if the deployment target is iOS 16;
@unchecked Sendable might be legitimate for a wrapper type around
a non-Sendable framework dependency).
(2) Severity miscalibrations — findings rated too high (works
fine; minor stylistic preference) or too low (data race or
correctness bug hidden behind a stylistic concern).
(3) Missing findings — Apple-specific architecture issues both
reviewers missed, especially: actor reentrancy hazards, Sendable
gaps in closures captured by Tasks, NavigationPath type erasure
issues, deep-link routing gaps, SwiftData model relationship cycles,
Combine subjects retained across actor boundaries, view identity
churn from non-stable IDs.
(4) Alternatives that are impractical or have misestimated migration
cost (e.g. migrating from ObservableObject to @Observable is not
"Low" cost when iOS 16 support is required).
Be specific. Every challenge must cite the finding ID and the
Pattern.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. **Migration Cost nuance**:
P0 tasks with `Migration Cost=High` get a "Requires team alignment
and design discussion before execution" note — module restructuring,
state-ownership rewrites, and navigation overhauls shouldn't ship
without team validation.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Every finding has a named Pattern and concrete Alternative
- [ ] P0 tasks with Migration Cost=High include the "requires team
      alignment" note
- [ ] Platform column populated correctly (some patterns only apply
      to a subset of platforms — e.g. @MainActor isolation is more
      tractable when iOS 15+ is the floor)

---

## Reference

- Audit reference doc: [`docs/apple-architecture/README.md`](../docs/apple-architecture/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- SwiftUI State and Data Flow: https://developer.apple.com/documentation/swiftui/state-and-data-flow
- @Observable macro: https://developer.apple.com/documentation/observation
- Swift Concurrency: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/
- Swift Strict Concurrency: https://www.swift.org/documentation/concurrency/
- Swift Package Manager: https://www.swift.org/package-manager/
- NavigationStack: https://developer.apple.com/documentation/swiftui/navigationstack
