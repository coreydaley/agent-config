# Apple Platform Localization Audit Reference

Schema and severity reference for the `/audit-apple-localization`
command. For the shared 5-phase audit pattern, see
[`../../lib/audit-framework.md`](../../lib/audit-framework.md).

Audit artifacts: `~/Reports/<org>/<repo>/audits/<TS>-apple-localization/`

## Output

| File / Folder | Description |
|---|---|
| `tooling-raw/` | Snapshots of `*.xcstrings` (String Catalogs), legacy `.strings`, `.stringsdict`, `Info.plist` purpose strings, `CFBundleLocalizations`, IDFA/ATT usage, hardcoded-string candidates |
| `claude.md` | Claude's review (ID prefix `A`) |
| `codex.md` | Codex's review (ID prefix `C`) |
| `synthesis.md` | Unified findings (`S`-prefix IDs) |
| `devils-advocate.md` | Codex challenge |
| `REPORT.md` | Sprint-able findings report |

## Schema

```
| ID | Severity | Surface | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

**Surface**: `HardcodedString`, `Pluralization`, `RTL`, `Formatters`,
`StringCatalog`, `AttributedString`, `InfoPlist`, `AssetCatalog`,
`AccessibilityStrings`, `Locale`.

**Verification**: `code` or `runtime` (Simulator language switch).

## Categories

1. Hardcoded user-facing strings
2. String Catalog (Xcode 15+) migration
3. Pluralization (CLDR plural categories)
4. RTL (right-to-left) layout
5. Locale-aware formatters (`Date.FormatStyle`, `Number.FormatStyle`, …)
6. `AttributedString` localization
7. `Info.plist` localization (`InfoPlist.xcstrings` / per-locale `.strings`)
8. Asset catalog localization
9. Accessibility-string localization
10. Locale / calendar / time-zone correctness

## Severity (default mapping)

| Issue | Severity |
|---|---|
| Layout broken in RTL on primary surface | Critical |
| Pluralization wrong leading to user confusion at scale | Critical |
| Hardcoded English strings shipping to multilingual market | Critical |
| Localization missing for any string the user sees in normal flow | High |
| Locale-unaware formatter producing wrong currency / date | High |
| Purpose strings (Info.plist) not localized (App Store flag) | High |
| Legacy `.strings` instead of String Catalog | Medium |
| Missing pluralization on low-frequency surface | Medium |
| Edge-case locale not supported when not in target market | Low |

**Severity is calibrated to declared target languages.** If the project
ships only to en-US: most findings drop a tier. If RTL languages are
declared targets: RTL findings escalate.

## Sprint Mapping

Baseline `P0/P1/Deferred`. Verification requires Simulator language
testing (Scheme → Run → Options → Application Language / Region).

## Inherent Limitations

Static review catches hardcoded strings, missing pluralization rules,
RTL gaps, and locale-unaware formatters, but cannot judge translation
quality. Findings marked `runtime` require Simulator language testing.

## References

- Subagent: [`../../subagents/audit-apple-localization.md`](../../subagents/audit-apple-localization.md)
- String Catalogs: https://developer.apple.com/documentation/xcode/localizing-and-varying-text-with-a-string-catalog
- Foundation Localization: https://developer.apple.com/documentation/foundation/localization
- FormatStyle: https://developer.apple.com/documentation/foundation/formatstyle
- CLDR plural rules: https://unicode-org.github.io/cldr/ldml/tr35-numbers.html#Language_Plural_Rules
