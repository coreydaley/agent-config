Perform a thorough responsive design audit of the scope at the project
root you've been pointed at for mobile and tablet viewports. No
automated tooling has been run for this audit (web responsive design is
a pure-LLM review); $AUDIT_DIR/tooling-raw/STATUS.md notes any
project-existing visual-regression tooling (Percy, Chromatic,
BrowserStack) you should reference or defer to rather than duplicate.

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format for each finding:

| ID | Severity | Title | Location | Breakpoint | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002).

Breakpoint column: xs (<576px), sm (576-767px), md (768-991px),
lg (992-1199px), xl (>=1200px), All, or framework-specific names
(Tailwind sm/md/lg/xl/2xl, Bootstrap xs/sm/md/lg/xl/xxl, Foundation
small/medium/large, etc.).
Verification column: code (inspectable from source) or runtime
(requires browser/device testing).

Cover these 10 categories:

(1) Viewport meta tag — presence, correctness, no user-scalable=no.
Flag missing <meta name="viewport"> in primary HTML entry points; flag
user-scalable=no or maximum-scale=1 as accessibility violations
(WCAG 1.4.4).

(2) Fluid layouts — fixed pixel widths that prevent reflow; use of
percentage, vw/vh, fr, or clamp() units; max-width usage. Flag
container widths > 320px without max-width or fluid alternative.

(3) Breakpoint coverage — missing breakpoints for common device widths;
desktop-only CSS with no mobile override; breakpoint order issues
(mobile-first vs desktop-first); inconsistent breakpoint values across
the codebase.

(4) Typography scaling — font sizes that are too small (<16px body)
on mobile; lack of clamp() or responsive type scale; line-length too
wide/narrow at small viewports (45-75ch target). Flag pixel-fixed
font-size in body copy.

(5) Touch targets — interactive elements below 44x44px (WCAG 2.5.5);
tap targets too close together (< 8px gap); hover-only interactions
with no touch equivalent (:hover styles without :focus-visible or
click-to-toggle counterpart).

(6) Horizontal overflow — elements wider than the viewport;
overflow-x not handled; tables, code blocks, or images causing forced
horizontal scroll; fixed-width containers inside narrow viewports.

(7) Images and media — missing max-width:100% on images;
non-responsive video/iframe embeds (need aspect-ratio container);
missing srcset or <picture> element for HiDPI/small screens;
background-image without background-size on decorative imagery.

(8) Navigation and menus — desktop-only navigation with no mobile
alternative; hamburger menus inaccessible or below the 44px target;
dropdowns that are unusable on touch (hover-trigger with no click
fallback); sticky-nav obscuring viewport content on small screens.

(9) Forms and inputs — input fields too small or misaligned on mobile;
missing autocomplete/inputmode/type attributes (type=email,
type=tel, inputmode=numeric); labels not associated; submit buttons
below the minimum touch target size; multi-column form layouts that
don't collapse on mobile.

(10) Component-level issues — modals/dialogs that overflow the
viewport (no max-height + overflow-y:auto on body); carousels or
sliders with no swipe support; data tables with no horizontal scroll
container or stacked-card mobile variant; cards or grid items that
collapse poorly (orphaned items, broken proportions); fixed-position
elements that cover primary content on small screens.

Grouping rule: when the same broken pattern appears across many
components, create one representative finding and document the extent
in Evidence/Notes rather than duplicating per instance.

Rate severity on evidence: impact on primary user flow,
device-size commonality (375px, 768px, 1024px are the anchor sizes),
breadth of affected components, compensating controls.

Critical anchors:
- Broken layout / content inaccessible at a common viewport
- Primary user flow blocked on mobile

High anchors:
- Horizontal overflow forcing scroll on mobile
- Touch targets below 44x44px on critical CTAs
- Missing viewport meta tag
- Tap targets too close to be distinguishable

Medium anchors:
- Fixed widths causing reflow problems
- Typography not scaling appropriately at mobile
- Images not constrained / overflow container
- Hover-only patterns with no touch equivalent

Low anchors:
- Minor spacing / padding inconsistencies on small screens

Every finding must include a Verification field — many responsive
issues only appear on actual device emulation. Mark "code" only when
the issue is structurally inspectable from source (e.g. a hardcoded
width:1200px, a missing viewport meta tag). Mark "runtime" when the
fix needs to be validated in DevTools or on a real device.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
