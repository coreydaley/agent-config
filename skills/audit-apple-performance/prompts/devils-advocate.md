Read synthesis.md and the raw tooling output in tooling-raw/ in the
audit dir you've been granted access to. Your job is to attack the
synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated | missing_finding | missing_compound | impractical_remediation | insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, compensating control identification, or specific code reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that aren't actually a performance
issue in context. Specifically for Apple performance:
- A "main thread blocking" finding on code that runs once at startup
  (cold-path acceptable cost).
- A "retain cycle" that's intentional and bounded (singleton
  lifecycle, view-model owned by a long-lived coordinator).
- A "missing LazyVStack" on a list that's always <20 items.
- A "synchronous I/O" finding on a path that's already wrapped in
  Task.detached or on a known background queue.
- A "force-unwrap on UIImage" that's loading a guaranteed bundle asset.
- A "high-frequency timer" that's already gated on app foreground state.

(2) Severity miscalibrations — findings rated too high (cold-path
issues, code only reached in debug builds, work behind a feature flag
default-off) or too low (warm-path issues on the primary user surface,
under-counting blast radius via scroll-surface frame budgets, launch-
time impact compounding across cold-launch + first-screen).

(3) Missing findings — performance issues the review missed,
especially:
- Priority-inversion patterns (high-QoS Task awaiting low-QoS work).
- Actor reentrancy hazards (re-entering an actor while suspended).
- SwiftData / CoreData fetch-on-main via @Query without predicate
  bounds.
- Combine debounce/throttle gaps on text-input bound publishers.
- SwiftUI Animation blocking complex transitions; .animation modifier
  scope too broad.
- CALayer animation vs SwiftUI animation choice for performance-
  critical surfaces.
- Metal / GPU performance on visionOS RealityView or Metal-backed
  views.
- WatchKit complications memory budget.
- NSPredicate over-fetching (no fetchLimit; no relationship pre-fetch).
- AVAsset / AVPlayer keep-alive on background.
- ImageIO vs CGImageSource for thumbnail extraction (full-decode
  vs subset).

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse exploit than any single finding represents. Be
explicit about the chain and the combined severity. (E.g. heavy
App.init + sync network on main + image decode on launch → cold-launch
blowout; or missing LazyVStack + AsyncImage without placeholder +
on-main JSON decode → scroll-jank cascade.)

(5) Impractical/incomplete/wrong remediations — e.g. adding
[weak self] where it's not needed (and breaks intended lifecycle);
breaking correctness in pursuit of performance (e.g. dropping
@MainActor where required); moving work off-main into a Task without
considering actor isolation; switching to LazyVStack and losing
container scroll position; "use Equatable view" without checking the
view's state actually changes equivalently.

(6) Verification steps that don't actually prove the fix works —
performance verification requires before/after measurement with
Instruments; "looks faster" is not verification. Specifically:
- "Manual review" is insufficient.
- The named instrument must match the finding (retain cycle → Leaks
  or Allocations Generations; hang → Hangs Tool or Time Profiler;
  widget memory → Allocations + run as widget process).
- Before/after numbers must be recorded (cold-launch ms, scroll FPS,
  peak resident memory MB, energy log impact level).

Be specific. Every challenge must cite the finding ID and reference
the Instrument that would measure it where applicable.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
