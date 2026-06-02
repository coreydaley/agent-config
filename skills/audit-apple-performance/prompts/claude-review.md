You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough Apple platform performance review of the scope at the
project root you've been pointed at. Tooling has already been run; raw
output is in the audit dir's tooling-raw/ subdirectory. Read those files
first: semgrep.json (SAST), grep-patterns/perf-patterns.txt (candidate
locations for synchronous I/O, Thread.sleep, strong-self captures,
force-unwraps on UIImage/Data, launch entry points, widget timeline
providers), instruments-traces.txt (any pre-captured .trace bundles).

Apple performance is fundamentally runtime — Instruments owns the
high-fidelity signal. Static review can identify likely issues (retain
cycles, main-thread blocking, expensive view bodies, missing async
boundaries) but cannot measure actual launch time, frame drops, or
memory growth without Instruments. Validate the grep-pattern candidates
against actual usage context — some Data(contentsOf:) calls are
legitimately on background threads, some [self] captures are bounded
and intentional.

Write all findings to claude.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Instrument | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix A (e.g. A001, A002). Every finding MUST include:
- Instrument: which Xcode Instruments instrument would catch / measure
  this — TimeProfiler, Allocations, Leaks, Hangs, MetricKit,
  SwiftUI Profiler, EnergyLog, Network — or static if inspectable from
  source alone.
- Platform: iOS, iPadOS, macOS, MacCatalyst, watchOS, tvOS, visionOS,
  WidgetExtension, or Multi.
- Verification: code (inspectable) or runtime (Instruments profiling
  required to confirm magnitude).

Cover these 10 categories (skip if not applicable):

(1) Cold/warm launch time — synchronous work in
application(_:didFinishLaunchingWithOptions:) / App.init / @main;
heavy framework imports; image decoding on launch; main-thread
network calls at startup. iOS / iPadOS / visionOS / watchOS have
a much tighter launch-time budget than macOS (mobile launch perf
is enforced via OS watchdog termination). macOS launches are
slower but still relevant to UX.

(2) SwiftUI body invalidation — frequent or unnecessary view rebuilds;
@State / @ObservedObject / @Observable granularity; Equatable view
conformance; computed body complexity; @ViewBuilder patterns that
explode the view tree.

(3) Main-thread blocking — synchronous I/O on main; large JSON or
Core Data fetches on main; image decode on main; Thread.sleep /
busy loops; missing @MainActor / Task.detached boundaries.

(4) Async / concurrency correctness — missing await; @MainActor
violations; data races (@Sendable gaps); task cancellation not
propagated; structured concurrency (async let, TaskGroup) where it
would help.

(5) Retain cycles & memory leaks — closure captures missing
[weak self] / [unowned self]; Combine AnyCancellable retain cycles;
async Task retain cycles; delegate retain (non-weak); SwiftUI
@StateObject vs @ObservedObject lifecycle confusion.

(6) Memory growth — image caching unbounded; large data in memory
(favor streaming); Core Data fault realization; UserDefaults bloat;
large in-memory arrays; UIImage retained when Data would do.

(7) List / scroll performance — List row identity (Identifiable,
id:); LazyVStack/LazyHStack vs VStack; AsyncImage patterns;
diffable data source on UIKit.

(8) Energy impact — location updates without desiredAccuracy / pause;
high-frequency timers; background tasks that should defer;
continuous animations off-screen; CoreMotion always-on; Bluetooth
scanning patterns. Battery-energy budget is much tighter on iOS /
iPadOS / watchOS than macOS; flag accordingly.

(9) Widget / extension performance — memory caps differ per
extension type AND per platform:
- iOS / iPadOS widget (small/medium/large): ~30 MB
- iOS / iPadOS Lock Screen / accessory widget: tighter, design for
  ~16 MB
- watchOS complication widget: ~30 MB (shares OS budget)
- watchOS active app: ~24 MB (extreme — flag accordingly)
- Notification Service Extension: 24 MB hard cap (cross it and the
  push reverts unmodified)
- App Intent perform(): ~120 MB
TimelineProvider doing heavy work; getTimeline blocking; AppIntent
perform() doing heavy work; Live Activity update frequency. Note
which platform the extension targets — a widget on macOS has
different headroom than on watchOS. Cross-ref `audit-apple-extensions`
for the lifecycle-contract depth; this audit flags the perf cost.

(10) Network & disk efficiency — URLSession cache config; redundant
fetches; large payload deserialization on main; sync
Data(contentsOf:); Core Data background context usage.

Rate severity on evidence: does this cause visible jank, hangs, crashes,
or battery drain? How common is the affected path? Hot-path on a
primary surface, or cold-path one-shot?

Critical anchors:
- App hangs / unresponsive (>500ms main-thread block on a hot path)
- Crash from memory growth on a primary flow
- Launch time >2s on iOS / iPadOS / visionOS / watchOS shipping app
  (macOS launch budget is laxer but still flag >3s as High)
- Widget / extension exceeds its platform-specific memory budget and
  gets killed (NSE 24MB, iOS widget ~30MB, watchOS active app ~24MB)

High anchors:
- Frame drops on a primary scroll surface (visible jank)
- Main-thread network call on a non-rare path
- Clear retain cycle on a frequently-instantiated view
- Energy impact severe enough to trigger battery warnings

Medium anchors:
- Suboptimal patterns that aren't yet causing visible issues but will
  at scale (missing LazyVStack on a list that may grow; image decode
  on main for a non-critical surface).

Low anchors:
- Micro-optimizations; defense-in-depth performance work.

Every finding must include a Verification field — for performance this
nearly always means runtime verification with Instruments. Note when
verification requires a built app and which instrument template to use.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
