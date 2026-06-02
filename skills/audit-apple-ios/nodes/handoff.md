# Node: handoff

Print the audit hand-off message to the user. **Verify already passed** — this node just communicates the result and the next-step pointer.

## Inputs

- Walker state: `audit_dir`, `verify_output`, `da_status`, `codex_status`, `ingest_status`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
VERIFY_OUTPUT=$(scripts/walk.sh get --state "$STATE" --key verify_output)
CODEX_STATUS=$(scripts/walk.sh get --state "$STATE" --key codex_status)
DA_STATUS=$(scripts/walk.sh get --state "$STATE" --key da_status)
INGEST_STATUS=$(scripts/walk.sh get --state "$STATE" --key ingest_status)
```

## Steps

### 1. Extract finding counts from REPORT.md

Parse the audit summary table to populate the hand-off counts.

### 2. Print the hand-off

```
> Apple iOS Audit complete.
>
> **Report:** <absolute path to $AUDIT_DIR/REPORT.md>
>
> **Summary:** Critical: X, High: Y, Medium: Z, Low: W. Top finding:
> <one-line description of the highest-severity finding>.
>
> **Verification output:**
> <verify_output verbatim>
>
> **Apple-iOS-specific warnings:**
> - **Verify on real iPhone hardware where the surface demands it.**
>   Dynamic Island Live Activities only render on iPhone 14 Pro+; the
>   simulator does NOT show the Island regardless of the chosen device
>   family. Any `Apple:DynamicIsland` finding marked
>   `Verification=runtime` must be confirmed on a real iPhone 14 Pro+
>   (or newer Pro) before sign-off.
> - **Stage Manager + Split View + Slide Over verification needs a
>   real iPad** — the iPad simulator approximates the multitasking
>   geometry but does not reproduce real Stage Manager behavior under
>   memory pressure or the external-display fan-out. After any
>   `Plist:UIRequiresFullScreen` / `Plist:UIApplicationSceneManifest`
>   fix, test on a physical iPad (preferably with an external
>   display) before shipping.
> - **Action Button (iPhone 15 Pro+) is assigned via Settings →
>   Action Button → Shortcut → <app>.** After any `Apple:AppShortcut`
>   fix, assign the app to the Action Button on a physical
>   iPhone 15 Pro+ and trigger the button to confirm the intent runs.
>   The simulator does not surface the Action Button.
> - **BGTaskScheduler tasks can be debug-launched via lldb**:
>   `e -l objc -- (void)[[BGTaskScheduler sharedScheduler] _simulateLaunchForTaskWithIdentifier:@"<your.task.id>"]`
>   while the app is paused at a breakpoint. This is the only
>   developer-time way to confirm the task is registered AND its
>   handler runs. Tasks that "never fire" almost always fail this
>   check because the `register(forTaskWithIdentifier:)` call happens
>   after `applicationDidFinishLaunching` returns or the identifier
>   isn't in `BGTaskSchedulerPermittedIdentifiers`.
> - **Focus integration** requires adding the app to a Focus filter
>   in Settings → Focus → <FocusName> → Apps. After any
>   `Apple:FocusFilterIntent` fix, toggle the Focus on/off and
>   confirm the app's content adapts.
> - **Critical findings here block the next iOS release** — App
>   Review flags for `UIRequiresFullScreen=YES` on non-game apps,
>   silently-broken BGTasks, and Dynamic Island crashes are all
>   user-visible and revenue-impacting.
> - **Most remediations require a real rebuild + relaunch** — "set
>   the Info.plist key" is not a verified fix until the app is
>   relaunched and the new lifecycle plays out (cold-launch deep
>   link, scene-restoration round-trip, BGTask scheduler reload).
> - Sensitive-content warning: REPORT.md may reference internal team
>   IDs, bundle identifiers, BGTask identifiers, notification topics,
>   Live Activity push tokens, and Focus filter intent payloads.
>   Treat as confidential before sharing.
>
> **Next:** Run `/sprint-plan` against the report:
>
> ```
> /sprint-plan <absolute path to $AUDIT_DIR/REPORT.md>
> ```
```

If `CODEX_STATUS=failed`, add to the warnings:

```
> - **Degraded run**: Codex review unavailable; this was a single-agent
>   audit. Consider re-running once codex is reachable.
```

If `DA_STATUS=failed`, add:

```
> - **Degraded run**: Devil's advocate pass did not complete; synthesis
>   was not stress-tested. False positives may be present.
```

If `INGEST_STATUS` is `failed` or `unavailable`, add:

```
> - **Plane ingest**: <failed | unavailable>. Audit artifacts are
>   complete; only the work-item generation failed. Re-run with
>   `/plane-audit-ingest <audit-dir>` after fixing the underlying issue.
```

### 3. Mark the audit complete in walker state

```bash
scripts/walk.sh set --state "$STATE" --key handoff_printed --value "yes"
```

## Outputs

- Hand-off message printed to the user
- Walker state updated

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from handoff --to terminal
```

## Failure modes

- REPORT.md unparseable for counts → fall back to "see REPORT.md for findings" without specific numbers.
