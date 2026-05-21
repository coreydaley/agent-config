# Apple Performance Audit Reference

Schema and severity reference for the `/audit-apple-performance` command.
For the shared 5-phase audit pattern, see [`../../lib/audit-framework.md`](../../lib/audit-framework.md).

Audit artifacts: `~/Reports/<org>/<repo>/audits/<TS>-apple-performance/`

## Output

| File / Folder | Description |
|---|---|
| `tooling-raw/` | `semgrep.json`, `grep-patterns/perf-patterns.txt` (sync I/O, `Thread.sleep`, strong-self captures, force-unwraps in hot paths) |
| `claude.md` | Claude's review (ID prefix `A`) |
| `codex.md` | Codex's review (ID prefix `C`) |
| `synthesis.md` | Unified findings (`S`-prefix IDs) |
| `devils-advocate.md` | Codex challenge |
| `REPORT.md` | Sprint-able findings report |

## Schema

```
| ID | Severity | Instrument | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

**Instrument**: Which Xcode Instruments tool would catch/measure this —
`TimeProfiler`, `Allocations`, `Leaks`, `Hangs`, `MetricKit`,
`SwiftUI Profiler`, `EnergyLog`, `Network` — or `static` if
inspectable from source alone.

**Platform**: includes `WidgetExtension` as a value (widget memory
limits ~30 MB).

**Verification**: `code` or `runtime` (Instruments profiling).

## Categories

1. App launch time
2. SwiftUI body invalidation
3. Main-thread blocking
4. Async / concurrency correctness
5. Retain cycles & memory leaks
6. Memory growth
7. List / scroll performance
8. Energy impact
9. Widget / extension performance (memory budgets)
10. Network & disk efficiency

## Severity (default mapping)

| Issue | Severity |
|---|---|
| App hangs / unresponsive (>500ms main-thread block on hot path) | Critical |
| Crash from memory growth on primary flow | Critical |
| Launch time >2s on shipping app | Critical |
| Widget exceeds memory budget and gets killed | Critical |
| Frame drops on primary scroll surface (visible jank) | High |
| Main-thread network call on non-rare path | High |
| Clear retain cycle on frequently-instantiated view | High |
| Energy impact severe enough to trigger battery warnings | High |
| Suboptimal patterns not yet causing visible issues | Medium |
| Micro-optimizations; informational | Low |

## Sprint Mapping

Baseline `P0/P1/Deferred`. Every task's verification must include the
Instruments configuration (Time Profiler, Allocations Generations,
Hangs window, etc.) and require a before/after measurement — "looks
faster" is not verification.

## Inherent Limitations

Performance is fundamentally a runtime property. Static review
identifies likely issues but cannot measure actual launch time, frame
drops, or memory growth without Instruments. Findings marked `runtime`
need profiling to confirm magnitude.

## References

- Subagent: [`../../subagents/audit-apple-performance.md`](../../subagents/audit-apple-performance.md)
- Instruments: https://help.apple.com/instruments/mac/current/
- SwiftUI performance: https://developer.apple.com/documentation/swiftui/optimizing-the-performance-of-your-app
- MetricKit: https://developer.apple.com/documentation/metrickit
- Widget memory: https://developer.apple.com/documentation/widgetkit/keeping-a-widget-up-to-date
