# Apple Adaptive UI Audit Reference

Schema and severity reference for the `/audit-apple-adaptivity` command.
For web responsive behavior, see [`../web-responsive/README.md`](../web-responsive/README.md).
For the shared 5-phase audit pattern, see [`../../lib/audit-framework.md`](../../lib/audit-framework.md).

Audit artifacts: `~/Reports/<org>/<repo>/audits/<TS>-apple-adaptivity/`

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
| ID | Severity | Surface | Title | Location | Platform | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

**Surface**: `SizeClass`, `Orientation`, `Multitasking`, `DynamicType`,
`Windowing`, `DeviceSize`.

**Platform**: `iOS`, `iPadOS`, `macOS`, `MacCatalyst`, `watchOS`, `tvOS`,
`visionOS`, or `Multi`.

**Verification**: `code` or `runtime` (Simulator / device testing).

## Categories

1. Size class adaptation
2. `ViewThatFits` & adaptive layouts
3. Orientation
4. iPad multitasking (Slide Over / Split View / Stage Manager)
5. Mac Catalyst adaptation
6. macOS-native windowing
7. visionOS windowing (windowed vs immersive)
8. Dynamic Type AX5 layout integrity
9. Device size adaptation (SE → Pro Max, mini → Pro)
10. Pointer & keyboard adaptation

## Severity (default mapping)

| Issue | Severity |
|---|---|
| Primary flow inaccessible at common config (split view, AX5, landscape) | Critical |
| Crash / hang on orientation / multitasking transition | Critical |
| Content truncated / clipped on SE / iPad mini | High |
| AX5 Dynamic Type breaks layout | High |
| No multiple-window support where warranted | High |
| Hover / pointer interactions missing on Mac Catalyst | Medium |
| Static layout that should use `ViewThatFits` or `Layout` | Medium |

## Sprint Mapping

Baseline `P0/P1/Deferred`. Runtime verification required at minimum on
iPhone SE, iPhone Pro Max, iPad mini, iPad Pro 12.9"; AX1 + AX5
Dynamic Type; portrait + landscape; Split View on iPad.

## Inherent Limitations

Static review identifies structural adaptivity issues but cannot
validate visual reflow, gesture interaction, or window-management
behavior without runtime testing on device or in Simulator.

## References

- Subagent: [`../../subagents/audit-apple-adaptivity.md`](../../subagents/audit-apple-adaptivity.md)
- Apple HIG — Layout: https://developer.apple.com/design/human-interface-guidelines/layout
- Apple HIG — Multitasking on iPad: https://developer.apple.com/design/human-interface-guidelines/multitasking
- visionOS: https://developer.apple.com/visionos/
