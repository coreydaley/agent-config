Perform a thorough accessibility review of the scope at the project
root you've been pointed at, against WCAG 2.1/2.2. Tooling output (if
any) is in the audit dir's tooling-raw/ subdirectory. Read those files
first: axe.json (axe-core DOM scan), pa11y.json (pa11y DOM scan),
lighthouse.json (Lighthouse accessibility category),
frontend-inventory.txt (HTML/component file inventory + existing a11y
tooling references).

If TARGET_URL was unset, the DOM scans were skipped and this audit is
source-level only — most findings will come from manual reading of
HTML, JSX/TSX, Vue, Svelte, Angular templates, CSS, and JS/TS that
manipulates ARIA or keyboard events. Validate, do not duplicate,
automated findings.

Write all findings to codex.md (in the audit dir you were granted
write access to) using this exact table format:

| ID | Severity | Title | Location | WCAG | Level | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where:
- ID uses prefix C (e.g. C001, C002).
- WCAG column: success criterion number (e.g. 1.4.3) or "Best
  Practice" for items beyond WCAG scope. WCAG 2.1/2.2 is the
  normative reference.
- Level column: A, AA, AAA, or BP.
- Verification column: code (inspectable from source) or runtime
  (requires browser and/or assistive-technology testing —
  VoiceOver / NVDA / JAWS / TalkBack / Switch Control).
- Default severity: Level A = Critical, AA = High, AAA = Medium,
  BP = Low. Override based on actual exclusion severity, task
  blockage, AT impact, and breadth of affected users.

Cover these 10 WCAG-anchored categories (skip if not applicable):

(1) Semantic structure and heading hierarchy — landmark regions
(<main>, <nav>, <header>, <footer>, <aside>), heading levels (no
skipped levels, one <h1> per page), list markup, document outline,
<title> on each page.

(2) Images and non-text content (WCAG 1.1.1) — alt on <img>,
decorative images with alt="" or role="presentation", complex images
with long descriptions, SVG with <title> or aria-label, icon-only
buttons / links with accessible names, background images conveying
information.

(3) Color and contrast (WCAG 1.4.3 minimum, 1.4.11 non-text, 1.4.1
not sole means) — text contrast ratios at the relevant size
thresholds, non-text contrast for UI components and focus indicators
(3:1), color never the sole means of conveying information
(error states, required fields, links in body text).

(4) Keyboard navigation and tab order (WCAG 2.1.1, 2.1.2) — every
interactive element reachable AND operable via keyboard, no keyboard
traps, logical tab order matching visual order, tabindex used
correctly (avoid tabindex > 0; tabindex="-1" for programmatic focus
only).

(5) Focus management and focus visibility (WCAG 2.4.3, 2.4.7, 2.4.11,
2.4.12) — visible focus indicators (:focus-visible / :focus styles
not removed without replacement), focus restoration after modal
close, focus moved into newly-opened dialogs, focus not stranded on
aria-hidden ancestors, focus not obscured by sticky headers /
footers.

(6) ARIA usage — correct roles (no role="button" on a <div> when
<button> exists; no redundant native semantics like role="link" on
<a>), valid states/properties for the role, no conflicting
native+ARIA semantics, aria-label / aria-labelledby /
aria-describedby resolving to real text, aria-* attributes valid for
the element they're on.

(7) Form labels and error messages (WCAG 1.3.1, 3.3.1, 3.3.2) —
every form control has a programmatic label (<label for>, aria-label,
aria-labelledby), placeholder is not a label, error messages
associated via aria-describedby and aria-invalid, error identification
doesn't rely on color alone, required fields programmatically
indicated.

(8) Dynamic content and live regions (WCAG 4.1.3) — aria-live /
role="status" / role="alert" on regions that update, polite vs
assertive used correctly, route changes announced in SPAs, loading
states announced, toast notifications reach AT.

(9) Motion and animation (WCAG 2.3.3 prefers-reduced-motion,
2.2.2 pause/stop/hide) — prefers-reduced-motion media query honored,
no auto-playing motion longer than 5 seconds without a pause/stop/
hide control, no flashes above 3/s, parallax / carousel autoplay
respect reduced-motion.

(10) Cognitive accessibility (WCAG 2.2.1, 3.3.4, 3.2.3) — adjustable
timeouts on session/idle timers, error prevention on consequential
actions (legal / financial / data deletion: confirm or undo),
consistent navigation across pages, clear / plain-language error
messages.

Rate severity on evidence: actual user exclusion, AT impact, blast
radius (one component vs. design system), reachability, compensating
controls.

Critical anchors:
- Level A violation blocking a primary user flow for AT users
- Form fields with no programmatic label on a checkout / signup /
  primary task
- Modal with focus trap broken so keyboard users can't escape
- All images on a content page with alt="" (content image as
  decorative)
- No <title> element on the page
- Auto-playing motion with no pause and ignoring
  prefers-reduced-motion
- Flashes above 3/s on a primary surface

High anchors:
- AA violation broadly applied (insufficient contrast across the
  design system; missing focus indicators sitewide; toasts not
  announced via live regions; navigation landmarks missing)
- Tab order divergent from visual order on a multi-step form
- aria-hidden="true" on an ancestor of focusable content
- Forms with errors identified by color only

Medium anchors:
- AAA violation, or AA violation in a narrow location with
  workarounds
- Heading-level skip inside a single section
- Decorative images missing alt="" (announces filename to AT but
  doesn't block task)

Low anchors:
- Best Practice gaps and defense-in-depth improvements
- Redundant role on native elements
- Minor aria-describedby polish

Grouping rule: when the same broken pattern appears across many
components (e.g. every <Button> in a design system missing
:focus-visible), create one representative finding and document the
extent in Evidence/Notes ("affects ~40 button instances across
src/components/**"). Do not produce one row per occurrence.

Every finding must include a Verification field marking whether it's
inspectable from source (code) or requires a built/running app plus
assistive technology to confirm (runtime). Focus restoration, live
region announcements, screen-reader name computation, and dynamic
ARIA state are typically runtime.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
