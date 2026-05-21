---
name: audit-accessibility-apple
description: Dual-agent Apple platform accessibility audit — Claude and Codex review native Apple UI (SwiftUI, UIKit, AppKit, WatchKit) independently against Apple HIG accessibility guidelines, synthesize, devil's advocate pass, output as findings report. For web frontends (HTML/CSS/JS), use `audit-accessibility-web` instead. Invoke with a scope path or leave empty to audit the current working directory.
---

# Apple Platform Accessibility Audit: Dual-Agent Review

You are orchestrating a dual-agent **Apple platform** accessibility audit
that produces a findings report. Claude and Codex review native Apple UI
code (Swift / SwiftUI / UIKit / AppKit / WatchKit) independently against
Apple's Human Interface Guidelines (HIG) accessibility section and the
platform's accessibility APIs. Findings are synthesized, Codex attacks the
synthesis, and the final output is a sprint document written to
`$AUDIT_DIR/REPORT.md`.

For **web frontends** (HTML, CSS, React/Vue/Svelte/etc.), use
`audit-accessibility-web` — that audit uses WCAG criteria and web-native
APIs (ARIA, semantic HTML) which do not apply to native Apple platforms.

The scope to audit is provided in your input prompt. If no scope is
specified, audit the current working directory.

The `audit-accessibility-apple` finding schema extends the core schema with
`API/Standard`, `Platform`, and `Verification` columns that anchor each
finding to a named Apple API or HIG principle.

**Inherent limitations**: Static code review can identify likely
accessibility issues but cannot fully validate VoiceOver output, focus
behavior, gesture recognition, or visual settings interactions without
running the app with Xcode's Accessibility Inspector and on-device with
VoiceOver / Switch Control / Voice Control / Full Keyboard Access. Findings
marked `runtime` in the Verification column require these tools to confirm.
This review is a structured starting point, not a conformance
certification.

## Scope Handling

Parse your input prompt for a path or paths to audit. Examples:
- No path specified → scope is the current working directory
- `Sources/Views` → scope is `Sources/Views`
- `App/Features App/Components` → scope is multiple paths

Scope is validated as a path in Phase 1 before being used anywhere else —
raw user input is never interpolated into shell strings.

## Workflow Overview

This is a **5-phase workflow**:

1. **Orient** — Determine scope, identify Apple project type and target
   platforms, note existing accessibility tooling
2. **Independent Reviews** — Claude and Codex review in parallel (Codex
   in background, Claude simultaneously)
3. **Synthesis** — Deduplicate findings; flag agreements as higher confidence;
   calibrate severity
4. **Devil's Advocate** — Codex attacks the synthesis for false positives,
   severity miscalibrations, and gaps
5. **Report Output** — Produce `$AUDIT_DIR/REPORT.md` with findings as
   tasks for human review; present to user for review

---

## Finding Schema

All intermediate audit files must use this table format so synthesis
and devil's advocate phases operate on consistent data:

```
| ID | Severity | Title | Location | API/Standard | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
|----|----------|-------|----------|--------------|----------|--------------|----------------|-----------------|----------------|
| A001 | Critical | Missing label on icon button | Sources/Views/PlayerControls.swift:42 | SwiftUI:accessibilityLabel | iOS,iPadOS | code | Impact explanation | Concrete fix | Code quote |
```

**ID prefix convention:**
- Claude's review: `A001`, `A002`... (Audit)
- Codex's review: `C001`, `C002`... (Codex)
- Synthesis: `S001`, `S002`... (Synthesis)

**Severity levels:** Critical, High, Medium, Low

**API/Standard column**: The named Apple API or HIG principle the finding
anchors to. Examples:
- `SwiftUI:.accessibilityLabel`, `SwiftUI:.accessibilityFocused`,
  `SwiftUI:.accessibilityElement(children:)`
- `UIKit:accessibilityTraits`, `UIKit:UIAccessibility.post`,
  `UIKit:isAccessibilityElement`
- `AppKit:accessibilityRole`, `AppKit:setAccessibilityLabel`
- `HIG:TouchTarget` (44×44pt minimum), `HIG:DynamicType`,
  `HIG:ReduceMotion`, `HIG:ContrastMinimum`
- `WCAG:1.4.3` when citing the contrast ratio explicitly referenced by HIG

**Platform column**: Which Apple platforms are affected. Use:
`iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`, `visionOS`,
or `Multi` for cross-platform code. Combine when relevant
(e.g. `iOS,iPadOS`).

**Verification column**: `code` (inspectable from source alone) or
`runtime` (requires Accessibility Inspector, VoiceOver, Switch Control,
Voice Control, Full Keyboard Access, or device testing).

**Default severity guidance** (starting point; override based on
actual user impact evidence):

| Issue Type | Default Severity | Rationale |
|---|---|---|
| Interactive element with no accessibility label | Critical | Element is invisible to VoiceOver users |
| Missing focus management in modal/sheet | Critical | Traps assistive tech users |
| Touch target below 44×44pt for a primary action | High | HIG minimum; physical-disability impact |
| No Dynamic Type support on important text | High | Excludes users with low vision |
| Missing Reduce Motion alternative for essential animation | High | Triggers motion-sensitivity discomfort |
| Color used as sole signal (no icon/text/pattern) | High | Excludes color-blind users |
| Wrong or missing accessibility trait | Medium | VoiceOver announces incorrectly |
| Decorative element not marked `.accessibilityHidden(true)` | Medium | Adds noise to VoiceOver |
| Missing rotor entries or sort priority for complex view | Medium | Slows VoiceOver navigation |
| Label includes redundant trait suffix ("button button") | Low | Minor verbosity |
| Hint provided when label is self-explanatory | Low | Best-practice nit |

Override upward when exclusion is severe, task blockage is total, or
breadth of affected users is large. Override downward when impact
evidence is limited.

---

## Phase 1: Orient

**Goal**: Understand the scope, identify the Apple project type and target
platforms, note existing accessibility tooling, and determine the output
location.

### Orient Steps

1. **Validate and resolve scope** from the input prompt:
   - If no path specified: scope is the current working directory
   - If a path is provided: verify the path exists
   - Exclude: `.build/`, `DerivedData/`, `Pods/`, `Carthage/Build/`,
     `.swiftpm/`, generated files, and vendored third-party Swift code
     unless explicitly included
   - Store the resolved scope path — do not use raw input text in any
     Codex exec prompt string

2. **Identify Apple project artifacts** in or above the resolved scope:
   - `Package.swift` (Swift Package Manager)
   - `*.xcodeproj/`, `*.xcworkspace/` (Xcode project)
   - `Info.plist` (declared target capabilities and supported platforms)
   - Asset catalogs (`*.xcassets/`) — color sets, image accessibility
     descriptions, App Icon
   - Storyboards and XIBs (`*.storyboard`, `*.xib`) — legacy but still
     relevant for accessibility audit

3. **Identify Swift source files** in the resolved scope:
   - `*.swift` — the primary review surface
   - Inspect imports to detect frameworks in use:
     - `import SwiftUI` — modern declarative UI
     - `import UIKit` — iOS/iPadOS/tvOS/Mac Catalyst classic
     - `import AppKit` / `import Cocoa` — macOS classic
     - `import WatchKit` — watchOS
     - `import SwiftData` / `import Combine` — supporting

4. **Determine target platforms**: read `Package.swift` platforms array or
   `Info.plist` to identify which Apple platforms this code ships on.
   Record this — it determines which Platform values are valid for
   findings and which APIs apply (e.g. `@AccessibilityFocusState` is
   iOS 15+ / macOS 12+).

5. **No Apple source files found**: if no Swift files exist in the resolved
   scope, notify the user and stop:
   > No Swift/Apple platform source files found in [scope]. Re-scope to a
   > directory containing Apple UI code, or use `/audit-accessibility-web`
   > if this is a web frontend.
   Do not create a sprint or artifact files.

6. **Note existing accessibility tooling** in the project:
   - Xcode Accessibility Inspector usage in `Package.swift`/test targets
   - Accessibility-focused snapshot tests (e.g. `SnapshotTesting` with
     accessibility snapshots)
   - XCUITest accessibility queries
   - Third-party tools (`AccessibilitySnapshot`, `a11ysnapshot`)
   - Xcode's built-in Accessibility Audit (Xcode 15+) — note if results
     have been captured anywhere
   - These tools complement but do not replace manual/LLM review

7. **Determine output location**:
   ```bash
   REMOTE=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
   ORG_REPO=$(echo "$REMOTE" | sed 's|.*github\.com[:/]||; s|\.git$||')
   REPORTS_BASE="$HOME/Reports/$ORG_REPO"
   REPORT_TS=$(date +%Y-%m-%dT%H-%M-%S)
   AUDIT_DIR="$REPORTS_BASE/audits/$REPORT_TS-accessibility-apple"
   PROJECT_CWD="$(pwd)"
   mkdir -p "$AUDIT_DIR"
   ```
   Each audit run gets its own timestamped folder under
   `~/Reports/<org>/<repo>/audits/`, matching the layout `/sprint-plan`
   uses for sprint sessions. All audit artifacts for this run live in
   `$AUDIT_DIR`. Create this before launching Codex in Phase 2.

### Orient Deliverable

A brief orientation note (4-6 bullets) covering:
- Resolved scope and what it includes/excludes
- Detected frameworks (SwiftUI / UIKit / AppKit / WatchKit) and Swift
  file count
- Target platforms from `Package.swift` / `Info.plist`
- Any existing accessibility tooling, snapshot tests, or audit artifacts
- Audit output directory (`AUDIT_DIR`)
- Any immediately obvious high-priority areas (e.g. legacy XIB without
  any accessibility identifiers, a primary CTA with no label)

---

## Phase 2: Independent Reviews (Parallel)

**Goal**: Get two independent Apple accessibility perspectives without
cross-contamination.

### Step 1 — Launch Codex in Background

The flags below are non-negotiable; see [`lib/codex-invocation.md`](../lib/codex-invocation.md) for per-flag rationale and failure modes. `--add-dir` points at `$AUDIT_DIR` so Codex can write its artifact under `~/Reports/`; `-C` points at `$PROJECT_CWD` so Codex reads the code being audited.

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "Perform a thorough Apple platform accessibility review of [RESOLVED_SCOPE] \
  against Apple's Human Interface Guidelines (HIG) accessibility section \
  and the platform's accessibility APIs (SwiftUI, UIKit, AppKit, WatchKit). \
  Write all findings to $AUDIT_DIR/codex.md using this exact table format \
  for each finding: \
  | ID | Severity | Title | Location | API/Standard | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes | \
  where ID uses prefix C (e.g. C001, C002). \
  API/Standard column: name the specific Apple API or HIG principle \
  (e.g. SwiftUI:.accessibilityLabel, UIKit:accessibilityTraits, \
  AppKit:accessibilityRole, HIG:TouchTarget, HIG:DynamicType, \
  HIG:ReduceMotion, HIG:ContrastMinimum). \
  Platform column: iOS, iPadOS, macOS, MacCatalyst, watchOS, tvOS, visionOS, \
  or Multi. \
  Verification column: code (inspectable from source) or runtime \
  (requires Accessibility Inspector / VoiceOver / Switch Control / Voice \
  Control / Full Keyboard Access). \
  Cover these 10 categories: \
  (1) Accessibility labels, hints, and values — every interactive view \
  (Button, TextField, Toggle, tappable Image, custom hit-test areas) has \
  an accessibilityLabel; hints describe action not appearance; values used \
  for stateful controls. \
  (2) Accessibility traits and semantic roles — correct traits applied \
  (.isButton, .isHeader, .isLink, .isImage, .isSelected, .isToggle, \
  .startsMediaSession); custom controls have appropriate roles; AppKit \
  uses accessibilityRole correctly. \
  (3) Dynamic Type and typography scaling — uses semantic font styles \
  (.font(.body), .font(.headline)) or @ScaledMetric; avoids hardcoded \
  point sizes; supports AX1-AX5 accessibility sizes; layouts adapt without \
  truncation. \
  (4) Contrast, color usage, and visual settings — supports Increase \
  Contrast (@Environment(\\.colorSchemeContrast) or \
  UIAccessibility.isDarkerSystemColorsEnabled); Differentiate Without \
  Color (information not conveyed by color alone); Reduce Transparency \
  (@Environment(\\.accessibilityReduceTransparency)); minimum contrast \
  ratios for foreground/background pairs (HIG references WCAG 1.4.3). \
  (5) Reduce Motion — @Environment(\\.accessibilityReduceMotion) or \
  UIAccessibility.isReduceMotionEnabled checked before non-essential \
  animations; alternative transitions provided; parallax / auto-play \
  honored. \
  (6) Focus management and navigation order — @AccessibilityFocusState / \
  .accessibilityFocused() used to move focus on screen changes, modal \
  presentations, and error states; .accessibilitySortPriority for \
  intentional traversal order; focus restored when modals dismiss. \
  (7) Element grouping and rotor support — .accessibilityElement(children: \
  .combine) on logically-grouped views to reduce VoiceOver chatter; \
  .accessibilityElement(children: .ignore) where appropriate; \
  .accessibilityRotor for custom navigation entries in long lists. \
  (8) Touch targets and hit testing — interactive elements meet 44×44 pt \
  minimum (HIG); .contentShape(Rectangle()) used to expand hit areas where \
  visual size is smaller; tap targets not crowded (adequate spacing). \
  (9) Announcements and live updates — AccessibilityNotification.Announcement \
  (SwiftUI) or UIAccessibility.post(notification: .announcement, ...) \
  used for transient status; .screenChanged or .layoutChanged posted on \
  major view transitions; live regions for changing values. \
  (10) Hardware keyboard, Switch Control, and Full Keyboard Access — \
  custom controls are .focusable() / focusable; keyboard shortcuts via \
  .keyboardShortcut() where appropriate; Mac and Mac Catalyst keyboard \
  navigation works; Switch Control scan groups respect logical structure. \
  Grouping rule: when the same broken pattern appears across many views, \
  create one representative finding and document the extent in \
  Evidence/Notes rather than duplicating per instance. \
  Do not read or reference any other review file." \
  < /dev/null
```

### Step 1.5 — Verify the Codex artifact

The most common Codex failure mode is silent (sandbox denial, missing flag,
prompt parse error — see `lib/codex-invocation.md`). After the background
Codex job returns, verify:

```bash
[[ -s "$AUDIT_DIR/codex.md" ]] && grep -q '|.*|.*|' "$AUDIT_DIR/codex.md" \
  || echo "⚠️ Codex did not produce a usable $AUDIT_DIR/codex.md"
```

If verification fails: inspect the Codex stderr output, fix the issue if
identifiable, and re-run the command once. Only after a second failure
should you accept the single-agent degradation documented in Phase 3.

### Step 2 — Claude's Independent Review (Simultaneous)

While Codex runs, write your own independent Apple accessibility review to
`$AUDIT_DIR/claude.md` using the same finding schema (ID prefix `A`).
Cover the same 10 categories:

1. **Accessibility labels, hints, and values** — every interactive view
   has a label; hints describe actions, not appearance; values used for
   stateful controls (Toggle, Slider, ProgressView)
2. **Traits and semantic roles** — correct traits for buttons, headers,
   links, images, selected/toggle states; custom controls (e.g.
   `.onTapGesture` on a non-Button view) declare `.isButton`
3. **Dynamic Type and typography scaling** — semantic font styles or
   `@ScaledMetric`; no hardcoded `.font(.system(size: 14))`; verify
   AX1-AX5 layout doesn't break (truncation, clipping)
4. **Contrast, color usage, and visual settings** — Increase Contrast,
   Differentiate Without Color, Reduce Transparency honored; semantic
   colors (system colors) over hardcoded; minimum contrast ratios
5. **Reduce Motion** — non-essential animations gated behind
   `@Environment(\.accessibilityReduceMotion)`; alternative transitions
   for users who need them
6. **Focus management and navigation order** — `@AccessibilityFocusState`
   moves focus on screen change, modal present, error state;
   `.accessibilitySortPriority` for intentional order; focus restored on
   sheet dismiss
7. **Element grouping and rotor support** — `.accessibilityElement(children:
   .combine)` to reduce chatter; `.accessibilityHidden(true)` on decorative
   elements; `.accessibilityRotor` for navigation
8. **Touch targets and hit testing** — 44×44 pt minimum; `.contentShape`
   expanded where visual size is smaller; spacing between tap targets
9. **Announcements and live updates** — `AccessibilityNotification.Announcement`
   for status; `.screenChanged`/`.layoutChanged` on major transitions
10. **Hardware keyboard, Switch Control, Full Keyboard Access** —
    `.focusable()` on custom controls; `keyboardShortcut()` where
    relevant; Mac/Mac Catalyst keyboard nav; Switch Control scan order

Note: focus behavior, VoiceOver phrasing, Switch Control navigation, and
Voice Control labels often require `runtime` verification — mark
Verification column accordingly.

When the same broken pattern appears across many views, create one
representative finding and document the extent in Evidence/Notes.

Wait for Codex to finish before proceeding to Phase 3.

---

## Phase 3: Synthesis

**Goal**: Produce a unified, deduplicated finding list with calibrated
severity and confidence.

### Synthesis Steps

1. **Verify both reviews exist and are non-empty**:
   - Check `$AUDIT_DIR/claude.md` and `$AUDIT_DIR/codex.md` exist and
     contain at least one finding row
   - If one file is missing or empty: proceed with single-agent
     synthesis and add a prominent warning at the top of
     `$AUDIT_DIR/synthesis.md`: "⚠️ Single-agent synthesis — [agent]
     review was unavailable. Coverage may be incomplete."

2. **Deduplicate findings**:
   - Compare both reviews for overlapping findings
   - When the same issue appears in both, merge into one synthesis
     row — note both source IDs (e.g. `A002, C003`)
   - When merging: preserve the most specific `Location` and best
     `Evidence/Notes`; preserve the most specific `Platform` (if one
     reviewer noted iOS+iPadOS and the other just iOS, keep the broader)
   - A single view may have multiple distinct accessibility issues —
     keep them separate if remediation differs
   - Grouping rule: one representative finding per broken pattern
   - Agreement = higher confidence, not higher severity

3. **Calibrate severity**:
   - Use the severity guidance table from the Finding Schema section
   - Override based on: VoiceOver impact, breadth of affected users,
     whether the issue blocks a primary task flow
   - Do not automatically escalate severity because both reviewers
     flagged the same issue

4. **Write synthesis**:

   Write `$AUDIT_DIR/synthesis.md`:

   ```markdown
   # Apple Accessibility Audit Synthesis — [REPORT_TS]

   ## Scope
   [Resolved scope path(s)]

   ## Target Platforms
   [iOS / iPadOS / macOS / etc., from Package.swift or Info.plist]

   ## Frameworks
   [SwiftUI / UIKit / AppKit / WatchKit detected in scope]

   ## Summary
   - Total findings: N (Critical: X, High: X, Medium: X, Low: X)
   - Reviewers: Claude (A-prefix), Codex (C-prefix)
   - [Single-agent warning if applicable]

   ## Unified Findings

   | ID | Severity | Title | Location | API/Standard | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes | Sources |
   |----|----------|-------|----------|--------------|----------|--------------|----------------|-----------------|----------------|---------|
   | S001 | ... | ... | ... | ... | ... | ... | ... | ... | ... | A001, C002 |

   ## Findings Present in Only One Review
   [Note findings not corroborated by the other reviewer and why they
   are retained or dropped]
   ```

Phase 3 is complete when `$AUDIT_DIR/synthesis.md` is written.

---

## Phase 4: Devil's Advocate

**Goal**: Challenge the synthesis for false positives, severity
miscalibrations, and missed findings.

### Step 1 — Launch Codex Devil's Advocate

```bash
codex exec \
  -s workspace-write \
  --add-dir "$AUDIT_DIR" \
  -C "$PROJECT_CWD" \
  -- "Read $AUDIT_DIR/synthesis.md. Your job is to attack it, not improve it. \
  Write your challenge to $AUDIT_DIR/devils-advocate.md covering: \
  (1) False positives — findings that are actually accessible in context \
  (e.g. a parent .accessibilityElement(children: .combine) already provides \
  the label; a SwiftUI Label view supplies the label implicitly; a system \
  control already has appropriate default traits). \
  (2) Severity miscalibrations — findings rated too high or too low given \
  the actual VoiceOver/Switch Control impact and user exclusion severity. \
  (3) Missing findings — Apple accessibility issues both reviewers missed, \
  especially: focus traps in sheets/modals, missing announcements on async \
  state changes, Dynamic Type breakage at AX sizes, Mac Catalyst keyboard \
  gaps, watchOS Digital Crown focus, visionOS-specific accessibility. \
  (4) Remediation steps that are incorrect, incomplete, or would \
  themselves introduce new accessibility issues (e.g. adding redundant \
  trait suffixes to labels, over-using .accessibilityHidden). \
  Be specific. Every challenge must cite the finding ID and the Apple API \
  or HIG principle if applicable." \
  < /dev/null
```

After the call, verify the artifact: `[[ -s "$AUDIT_DIR/devils-advocate.md" ]] || echo "⚠️ Codex devil's advocate produced no output"`.

### Step 2 — Incorporate Valid Challenges

Once `$AUDIT_DIR/devils-advocate.md` is written, read it and:

- **Remove** confirmed false positives from the working finding list
- **Recalibrate** severity where the challenge is valid and evidence
  supports it
- **Add** genuinely missed findings with new synthesis IDs
- **Document every rejected challenge** in a "Rejected Challenges"
  section at the bottom of `$AUDIT_DIR/synthesis.md`:

  ```markdown
  ## Rejected Devil's Advocate Challenges

  | Finding/Claim | Reason Rejected |
  |---|---|
  | [Claim from devil's advocate] | [Why it was not accepted] |
  ```

Phase 4 is complete when challenges are incorporated and rejections are
documented.

---

## Phase 5: Report Output

**Goal**: Produce a findings report at `$AUDIT_DIR/REPORT.md` with
Apple accessibility findings as sprint tasks.

### Sprint Mapping Rules

| Finding Severity | Sprint Priority |
|---|---|
| Critical | P0 — Must Ship |
| High | P0 — Must Ship |
| Medium | P1 — Ship If Capacity Allows |
| Low | Deferred |

Each sprint task must include:
- Finding ID (from synthesis)
- API/Standard reference (Apple API or HIG principle)
- Platform(s) affected
- Verification mode (`code` or `runtime`)
- File and line reference where applicable
- Clear description of the accessibility issue
- Concrete remediation: the specific Apple API to add/change and where
- Verification step: how to confirm the fix, including whether
  Accessibility Inspector, VoiceOver, Switch Control, Voice Control, or
  Full Keyboard Access testing is required

### No-Findings Case

If the synthesis contains zero findings after Phase 4:
- Create a single P0 task: "Verify no findings — [scope], [date]"
- The task description must document: scope covered, 10 categories
  reviewed, target platforms, date of review, and reviewer agents
- Do not produce an empty sprint

### Write the Sprint

Create `$AUDIT_DIR/REPORT.md`:

```markdown
# Apple Accessibility Audit — [scope] ([YYYY-MM-DD])

## Overview

[1-2 paragraphs: audit scope, target platforms, total findings by
severity, top 3 issues. Remind the reader that static LLM review cannot
fully validate VoiceOver output, focus behavior, gesture recognition, or
visual settings interactions — runtime verification with Accessibility
Inspector, VoiceOver, and on-device testing is required for `runtime`
findings.]

## Audit Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Total | N |

Target platforms: [iOS / iPadOS / macOS / etc.]
Frameworks: [SwiftUI / UIKit / AppKit / WatchKit]

Intermediate audit artifacts: `$AUDIT_DIR/claude.md`, `$AUDIT_DIR/codex.md`, `$AUDIT_DIR/synthesis.md`, `$AUDIT_DIR/devils-advocate.md`

## Implementation Plan

### P0: Must Ship

[One task per Critical/High finding]

**Task: [Finding ID] — [Title]**
- Location: `path/to/file.swift:line`
- API/Standard: [Apple API or HIG principle]
- Platform: [iOS / macOS / etc.]
- Verification: [code / runtime]
- Issue: [accessibility problem description]
- Remediation: [specific Apple API to add/change]
- Verification: [how to confirm; note if Accessibility Inspector / VoiceOver / Switch Control / Voice Control / FKA testing required]

### P1: Ship If Capacity Allows

[One task per Medium finding, same format]

### Deferred

[Low findings with brief rationale]

## Definition of Done

- [ ] All P0 tasks completed and verified
- [ ] Runtime-verification findings tested with Accessibility Inspector
      and on-device VoiceOver (and Switch Control / Voice Control / FKA
      where flagged)
- [ ] Dynamic Type tested at AX5 size for views with HIG:DynamicType findings
- [ ] No new accessibility issues introduced by the remediations
- [ ] Xcode's built-in Accessibility Audit re-run if available

## Notes

Some findings require runtime verification with Apple's accessibility
tooling. At minimum:
- **VoiceOver** (Settings → Accessibility → VoiceOver on device, or
  Simulator → Accessibility Inspector) — verify label/hint/value
  announcements
- **Accessibility Inspector** (Xcode → Open Developer Tool) — audit
  Mac targets and iOS Simulator targets
- **Dynamic Type** (Settings → Accessibility → Display & Text Size →
  Larger Text) — test AX1 through AX5
- **Reduce Motion** / **Reduce Transparency** / **Increase Contrast** /
  **Differentiate Without Color** — toggle each and verify
- **Switch Control** / **Voice Control** / **Full Keyboard Access**
  (iOS 14+) — verify for complex/custom controls

This report was generated from static code review against Apple HIG and
accessibility APIs and is a structured starting point, not a conformance
certification.

## Dependencies

- Audit intermediate files: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate}.md`
```

### Register and Hand Off

Inform the user:

   > ✅ Apple accessibility audit complete.
   >
   > **Report:** <literal absolute path to $AUDIT_DIR/REPORT.md>
   >
   > **Next:** Run `/sprint-plan` against the report to create an actionable sprint:
   >
   > ```
   > /sprint-plan <literal absolute path>
   > ```
   >
   > **Note:** Many Apple accessibility findings require runtime verification with VoiceOver / Accessibility Inspector / Switch Control / Voice Control / Full Keyboard Access — include this in task execution for items marked `runtime`. Some remediations (e.g., adding focus management before fixing labels) must be sequenced — review the task ordering before executing.

Substitute the literal absolute path of `$AUDIT_DIR/REPORT.md`
(e.g. `~/Reports/myorg/myrepo/audits/2026-04-22T10-30-00-accessibility-apple/REPORT.md`)
so the user can copy-paste the `/sprint-plan` command directly.

---

## Output Checklist

At the end of this workflow, verify:

- [ ] `$AUDIT_DIR/claude.md` — written using finding schema, ID prefix A
- [ ] `$AUDIT_DIR/codex.md` — written using finding schema, ID prefix C
- [ ] Both files are non-empty (or single-agent warning added to synthesis)
- [ ] `$AUDIT_DIR/synthesis.md` — unified findings with canonical
      S-prefix IDs and API/Standard + Platform columns populated
- [ ] `$AUDIT_DIR/devils-advocate.md` — Codex challenge complete
- [ ] Valid devil's advocate challenges incorporated into synthesis
- [ ] Rejected challenges documented with reasoning in synthesis
- [ ] `$AUDIT_DIR/REPORT.md` — written with P0/P1/Deferred tiering
- [ ] Each P0/P1 task has: finding ID, API/Standard, platform,
      verification mode, location, issue, remediation, verification guidance
- [ ] No-findings case handled if applicable
- [ ] Runtime-verification note included before hand-off
- [ ] User instructed to review task ordering before executing the sprint

---

## Reference

- Report output: `~/Reports/<repo-path>/audits/<TS>-accessibility-apple/`
- Audit artifacts: `$AUDIT_DIR/{claude,codex,synthesis,devils-advocate,REPORT}.md`
- Apple HIG — Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Accessibility on iOS: https://developer.apple.com/accessibility/ios/
- Accessibility on macOS: https://developer.apple.com/accessibility/macos/
- SwiftUI Accessibility documentation: https://developer.apple.com/documentation/swiftui/view-accessibility
- UIKit UIAccessibility documentation: https://developer.apple.com/documentation/uikit/accessibility_for_uikit
- AppKit NSAccessibility documentation: https://developer.apple.com/documentation/appkit/nsaccessibility
- WCAG 2.1 (referenced by HIG for contrast): https://www.w3.org/TR/WCAG21/
