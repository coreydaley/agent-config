# Apple Platform Architecture Audit Reference

Schema and severity reference for the `/audit-apple-architecture`
command. For platform-agnostic architecture principles, see
[`../architecture/README.md`](../architecture/README.md). For the
shared 5-phase audit pattern, see [`../../lib/audit-framework.md`](../../lib/audit-framework.md).

Audit artifacts: `~/Reports/<org>/<repo>/audits/<TS>-apple-architecture/`

## Output

| File | Description |
|------|-------------|
| `claude.md` | Claude's review (ID prefix `A`) |
| `codex.md` | Codex's review (ID prefix `C`) |
| `synthesis.md` | Unified findings (`S`-prefix IDs) |
| `devils-advocate.md` | Codex challenge |
| `REPORT.md` | Sprint-able findings report |

## Schema

```
| ID | Severity | Pattern | Title | Location | Platform | Alternative | Migration Cost | Why It Matters | Recommended Fix | Evidence/Notes |
```

**Pattern**: Named pattern the finding anchors to (e.g.
`SwiftUI:StateOwnership`, `Concurrency:MainActor`, `Concurrency:Sendable`,
`Modules:PackageBoundary`, `Navigation:Stack`, `Observable:Granularity`).

**Alternative**: Concrete alternative pattern — required. "Refactor this"
is not valid.

**Migration Cost**: `Low`, `Medium`, `High`.

**Evidence discipline**: A finding without a named `Pattern` and a
concrete `Alternative` is not a valid finding.

## Categories

1. SwiftUI state ownership (`@State` / `@Binding` / `@Bindable` / `@Observable`)
2. Observable granularity (`@Observable` macro vs `ObservableObject`)
3. View body complexity
4. `@MainActor` isolation
5. `Sendable` conformance
6. Structured concurrency (`async`/`await`, `TaskGroup`, cancellation)
7. Navigation patterns (`NavigationStack` typed routing, `NavigationSplitView`)
8. Modularization (Swift Package boundaries, module-public surface)
9. Dependency direction & DI (protocols at boundaries, environment vs constructor injection)
10. Error handling & propagation (`throws` vs `Result`, `LocalizedError`)

## Severity (default mapping)

| Issue | Severity |
|---|---|
| Shared mutable state with no actor isolation causing data races | Critical |
| Circular module dependencies blocking builds | Critical |
| Wholesale `@unchecked Sendable` everywhere | High |
| Navigation pattern that breaks deep-linking | High |
| `@StateObject` placement vs `@ObservedObject` confusion on hot flows | Medium |
| Over-broad `@Environment` keys | Medium |
| Migration to `@Observable` from `ObservableObject` for better perf | Low |

## Sprint Mapping

Baseline `P0/P1/Deferred`. **Migration Cost nuance**: P0 tasks with
`Migration Cost=High` get a "Requires team alignment and design
discussion before execution" note.

## Inherent Limitations

Architecture findings are hypothesis-generating, not prescriptive.
SwiftUI / actor / Sendable correctness is partly compiler-enforced,
but state ownership / modularization / navigation / async boundaries
are context-dependent. Treat findings as requiring team validation.

## References

- Subagent: [`../../subagents/audit-apple-architecture.md`](../../subagents/audit-apple-architecture.md)
- SwiftUI State and Data Flow: https://developer.apple.com/documentation/swiftui/state-and-data-flow
- @Observable: https://developer.apple.com/documentation/observation
- Swift Concurrency: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/
- Swift Strict Concurrency: https://www.swift.org/documentation/concurrency/
- NavigationStack: https://developer.apple.com/documentation/swiftui/navigationstack
