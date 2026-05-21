---
name: audit-apple-performance
description: Dual-agent Apple performance audit — cold/warm launch time, SwiftUI body invalidation, main-thread blocking, retain cycles (Combine cancellables, async tasks, closure captures), memory growth, energy impact, Instruments anchors, widget memory budgets.
---

# Apple Platform Performance Audit

You are orchestrating a dual-agent performance audit of native Apple
app code (Swift / SwiftUI / UIKit / AppKit).

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-performance` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-performance/`

**Scope**: Swift source files for native Apple apps. For web
performance (Core Web Vitals, bundle size), no audit exists yet —
the web equivalent is on the roadmap.

**Inherent limitations**: Performance is fundamentally a runtime
property. Static review can identify likely performance issues
(retain cycles, main-thread blocking, expensive view bodies, missing
async boundaries) but cannot measure actual launch time, frame drops,
or memory growth without Instruments. Findings marked `runtime` need
profiling to confirm magnitude. Treat as a starting point for
profiling sessions, not a guarantee of measured improvement.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Instrument` | Which Xcode Instruments instrument would catch / measure this: `TimeProfiler`, `Allocations`, `Leaks`, `Hangs`, `MetricKit`, `SwiftUI Profiler`, `EnergyLog`, `Network` — or `static` if inspectable from source alone |
| `Platform` | `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`, `WidgetExtension`, or `Multi` |
| `Verification` | `code` (inspectable) or `runtime` (requires Instruments profiling) |

Full schema:
```
| ID | Severity | Instrument | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews ten categories:

| # | Category | Covers |
|---|---|---|
| 1 | App launch time | Synchronous work in `application(_:didFinishLaunchingWithOptions:)` / `App.init` / `@main`; heavy framework imports; image decoding on launch; main-thread network calls at startup |
| 2 | SwiftUI body invalidation | Frequent or unnecessary view rebuilds; `@State`/`@ObservedObject` granularity; `Equatable` view conformance; computed `body` complexity; `@ViewBuilder` patterns that explode |
| 3 | Main-thread blocking | Synchronous I/O on main thread; large JSON / Core Data fetches on main; image decode on main; `Thread.sleep` / busy loops; missing `@MainActor` / `Task.detached` boundaries |
| 4 | Async / concurrency correctness | Missing `await` boundaries; `@MainActor` violations; data races (`@Sendable` gaps); task cancellation not propagated; structured concurrency (`async let`, `TaskGroup`) used where it would help |
| 5 | Retain cycles & memory leaks | Closure captures (`[weak self]`, `[unowned self]`); Combine `AnyCancellable` retain; async `Task` retain cycles; delegate retain (non-`weak`); SwiftUI `@StateObject` vs `@ObservedObject` lifecycle |
| 6 | Memory growth | Image caching unbounded; large data in memory (favor streaming); Core Data fault realization; `UserDefaults` bloat; large in-memory arrays; `UIImage` retained when only `Data` is needed |
| 7 | List / scroll performance | `List` row identity (`Identifiable`, `id:`); `LazyVStack`/`LazyHStack` vs `VStack`; image loading patterns (`AsyncImage` with low-res placeholders); diffable data source on UIKit |
| 8 | Energy impact | Location updates without `desiredAccuracy` / pause; high-frequency timers; background tasks that should defer; continuous animations off-screen; CoreMotion always-on; Bluetooth scanning patterns |
| 9 | Widget / extension performance | Widget memory limits (~30 MB depending on family); timeline provider doing heavy work; `TimelineProvider.getTimeline` blocking; `AppIntent` perform() doing heavy work; Live Activity update frequency |
| 10 | Network & disk efficiency | URLSession cache config; redundant fetches (favor `URLCache` / ETag); large payload deserialization on main; sync `Data(contentsOf:)`; Core Data background context usage |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | App hangs / unresponsive (>500ms main-thread block on a hot path); crash from memory growth on a primary flow; launch time >2s on shipping app; widget exceeds memory budget and gets killed |
| **High** | Frame drops on a primary scroll surface (visible jank); main-thread network call on a non-rare path; clear retain cycle on a frequently-instantiated view; energy impact severe enough to trigger battery warnings |
| **Medium** | Suboptimal patterns that aren't yet causing visible issues but will at scale; missing `LazyVStack` on a list that may grow; image decode on main for a non-critical surface |
| **Low** | Micro-optimizations; defense-in-depth performance work; informational |

---

## Phase 1: Audit-specific orient

### Tooling

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"
# Detect a timeout command — macOS doesn't ship one by default.
# Falls back to no timeout (with warning to STATUS.md) if neither is available.
TO=$(command -v timeout || command -v gtimeout || echo "")
[[ -z "$TO" ]] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"


# Static code analysis (semgrep with Swift rules — limited but useful)
command -v semgrep >/dev/null && \
  ${TO:+$TO 600} semgrep --config=p/swift --config=p/performance \
    --json --output "$AUDIT_DIR/tooling-raw/semgrep.json" "$PROJECT_CWD" \
    2>&1 | tee "$AUDIT_DIR/tooling-raw/semgrep.log"

# Look for known performance anti-patterns via grep
mkdir -p "$AUDIT_DIR/tooling-raw/grep-patterns"
{
  echo "=== Synchronous I/O patterns ===";
  grep -rn "Data(contentsOf:" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== Thread.sleep ===";
  grep -rn "Thread.sleep\|sleep(" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== Strong-self closure captures (potential cycle) ===";
  grep -rn "\[self\]\|\[strong self\]" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== Force-unwrap in hot paths (UIImage / data) ===";
  grep -rn 'UIImage(.*)!\|Data(.*)!' --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
} > "$AUDIT_DIR/tooling-raw/grep-patterns/perf-patterns.txt"
```

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Identify Apple project artifacts and target platforms
- Detect framework usage via imports: `SwiftUI`, `Combine`, `Concurrency`,
  `CoreData` / `SwiftData`, `WidgetKit`, `ActivityKit`, `CoreLocation`,
  `CoreMotion`, `CoreBluetooth`, `Network`, `WebKit`
- Check for `@main` `App` struct (SwiftUI) or `AppDelegate` /
  `SceneDelegate` — note initialization patterns
- Note any existing MetricKit integration (`MXMetricManager`),
  os_signpost / `OSLog` performance markers, custom performance test
  targets
- Check for widget extensions, App Intents, Live Activities — flag for
  memory-budget review

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple platform performance review of
[RESOLVED_SCOPE]. Tooling output is in $AUDIT_DIR/tooling-raw/.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | Instrument | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

Instrument column: which Xcode Instruments instrument would catch /
measure this — TimeProfiler, Allocations, Leaks, Hangs, MetricKit,
SwiftUI Profiler, EnergyLog, Network — or static if inspectable from
source alone.
Platform: iOS, iPadOS, macOS, MacCatalyst, watchOS, tvOS, visionOS,
WidgetExtension, or Multi.
Verification: code or runtime (where runtime means Instruments
profiling required to confirm magnitude).

Cover these 10 categories:
(1) App launch time — synchronous work in
application(_:didFinishLaunchingWithOptions:) / App.init / @main;
heavy framework imports; image decoding on launch; main-thread
network calls at startup.
(2) SwiftUI body invalidation — frequent or unnecessary view
rebuilds; @State / @ObservedObject / @Observable granularity;
Equatable view conformance; computed body complexity; @ViewBuilder
patterns that explode the view tree.
(3) Main-thread blocking — synchronous I/O on main; large JSON or
Core Data fetches on main; image decode on main; Thread.sleep /
busy loops; missing @MainActor / Task.detached boundaries.
(4) Async / concurrency correctness — missing await; @MainActor
violations; data races (@Sendable gaps); task cancellation not
propagated; structured concurrency (async let, TaskGroup) where it
would help.
(5) Retain cycles & memory leaks — closure captures missing [weak
self] / [unowned self]; Combine AnyCancellable retain cycles; async
Task retain cycles; delegate retain (non-weak); SwiftUI @StateObject
vs @ObservedObject lifecycle confusion.
(6) Memory growth — image caching unbounded; large data in memory
(favor streaming); Core Data fault realization; UserDefaults bloat;
large in-memory arrays; UIImage retained when Data would do.
(7) List / scroll performance — List row identity (Identifiable,
id:); LazyVStack/LazyHStack vs VStack; AsyncImage patterns;
diffable data source on UIKit.
(8) Energy impact — location updates without desiredAccuracy / pause;
high-frequency timers; background tasks that should defer;
continuous animations off-screen; CoreMotion always-on; Bluetooth
scanning patterns.
(9) Widget / extension performance — widget memory limits (~30 MB);
TimelineProvider doing heavy work; getTimeline blocking; AppIntent
perform() doing heavy work; Live Activity update frequency.
(10) Network & disk efficiency — URLSession cache config; redundant
fetches; large payload deserialization on main; sync
Data(contentsOf:); Core Data background context usage.

Rate severity on: does this cause visible jank, hangs, crashes, or
battery drain? How common is the affected path?

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. Read `$AUDIT_DIR/tooling-raw/` first — the
grep-patterns folder has surfaced candidate locations. Validate
those candidates against actual usage context (some
`Data(contentsOf:)` calls are legitimately on background threads).

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md and the raw tooling output in
$AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not
improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md
covering:
(1) False positives — findings that aren't actually a performance
issue in context (e.g. a "main thread blocking" finding on code that
runs once at startup is acceptable; a "retain cycle" that's
intentional and bounded; a "missing LazyVStack" on a list that's
always <20 items).
(2) Severity miscalibrations — findings rated too high (cold-path
issues) or too low (warm-path issues on the primary user surface).
(3) Missing findings — performance issues both reviewers missed,
especially: priority-inversion patterns, actor reentrancy hazards,
SwiftData fetch-on-main, Combine debounce/throttle gaps, SwiftUI
`Animation` blocking complex transitions, CALayer animation vs
SwiftUI animation choice, Metal / GPU performance on visionOS
RealityView, WatchKit complications memory budget.
(4) Remediation steps that are wrong — e.g. adding [weak self]
where it's not needed, or breaking correctness in pursuit of
performance.
(5) Verification steps that don't actually prove the fix works —
performance verification requires before/after measurement with
Instruments; "looks faster" is not verification.
Be specific. Every challenge must cite the finding ID and the
Instrument that would measure it.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. Hand-off note: every task's
verification step should include the Instruments configuration to
use (Time Profiler with the relevant scheme, Allocations with
"Generations" marker, Hangs Tool window, etc.) — and require a
before/after measurement, not "looks faster".

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, Instrument, Platform, Verification
      mode, location, issue, remediation, verification with
      before/after measurement protocol
- [ ] Widget / extension findings include memory-budget context
- [ ] Runtime-verification note in hand-off — most tasks require
      Instruments to confirm magnitude

---

## Reference

- Audit reference doc: [`docs/apple-performance/README.md`](../docs/apple-performance/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- Instruments overview: https://help.apple.com/instruments/mac/current/
- SwiftUI performance: https://developer.apple.com/documentation/swiftui/optimizing-the-performance-of-your-app
- MetricKit: https://developer.apple.com/documentation/metrickit
- Hangs and slowness: https://developer.apple.com/documentation/xcode/diagnosing-performance-issues-early
- Widget memory: https://developer.apple.com/documentation/widgetkit/keeping-a-widget-up-to-date
