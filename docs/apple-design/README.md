# Apple Platform Design Audit Reference

Schema and severity reference for the `/audit-apple-design` command,
anchored to Apple's Human Interface Guidelines (HIG). For
platform-agnostic / web design, see [`../design/README.md`](../design/README.md).
For the shared 5-phase audit pattern, see [`../../lib/audit-framework.md`](../../lib/audit-framework.md).

Audit artifacts: `~/Reports/<org>/<repo>/audits/<TS>-apple-design/`

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
| ID | Severity | HIG | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

**HIG**: The HIG principle the finding anchors to (e.g.
`HIG:Navigation`, `HIG:Modality`, `HIG:SF Symbols`, `HIG:Materials`,
`HIG:Animation`, `HIG:DarkMode`, `HIG:Toolbars`).

When a project has its own design system, **the design system takes
precedence** over generic HIG and findings note design-system
deviations.

**Platform**: `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`,
`visionOS`, or `Multi`.

## Categories

1. Native idiom usage (`Form`, `List`, `Menu`, `Picker`, `Toggle`, …)
2. SF Symbols
3. System colors & materials
4. Dark mode & color schemes
5. Navigation patterns (`NavigationStack` / `NavigationSplitView`)
6. Modality (sheets / popovers / inspectors / alerts)
7. Toolbar & menu placement
8. Animation appropriateness (honors `accessibilityReduceMotion`)
9. Platform-distinct affordances (iPad hover, Mac menu bar, visionOS ornaments, watchOS Digital Crown, tvOS focus engine)
10. Design system adherence

## Severity (default mapping)

| Issue | Severity |
|---|---|
| Component reinvented when a stock SwiftUI control would work; navigation pattern fundamentally inappropriate for the platform | Critical |
| Dark-mode broken across primary surfaces | Critical |
| Major HIG violation on a primary surface; design-system deviation on a frequently-used component | High |
| SF Symbols not used where iconography is expected | High |
| Suboptimal but functional native-idiom usage | Medium |
| Aesthetic preference backed by HIG | Low |

## Sprint Mapping

Baseline `P0/P1/Deferred`. Animation, gesture, and material findings
benefit from a Simulator review before signing off.

## Inherent Limitations

LLM review against HIG identifies many patterns but cannot validate
visual rendering, animation timing, gesture feel, or how a layout
reads in motion. Findings marked `runtime` require Simulator /
on-device review.

## References

- Subagent: [`../../subagents/audit-apple-design.md`](../../subagents/audit-apple-design.md)
- Apple HIG: https://developer.apple.com/design/human-interface-guidelines/
- SF Symbols: https://developer.apple.com/sf-symbols/
- HIG — Materials: https://developer.apple.com/design/human-interface-guidelines/materials
- HIG — Animation: https://developer.apple.com/design/human-interface-guidelines/motion
- HIG — Dark Mode: https://developer.apple.com/design/human-interface-guidelines/dark-mode
