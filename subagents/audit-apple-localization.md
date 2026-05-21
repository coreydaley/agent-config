---
name: audit-apple-localization
description: Dual-agent Apple platform localization audit — String Catalogs (Xcode 15+), pluralization rules, RTL support, locale-aware formatters (Date / Number / Currency / Measurement), AttributedString localization, mixed-localizations handling.
---

# Apple Platform Localization Audit

You are orchestrating a dual-agent localization (l10n) and
internationalization (i18n) audit of a native Apple app.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-localization` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-localization/`

**Scope**: Swift source files for native Apple apps, plus
`Localizable.xcstrings` (String Catalog), `.strings`, `.stringsdict`,
and `Info.plist` localization keys. For web localization, no audit
exists yet.

**Inherent limitations**: Localization is partly cultural / linguistic
and partly mechanical. Static review can catch hardcoded strings,
missing pluralization rules, RTL gaps, and locale-unaware formatters,
but cannot judge translation quality. Findings marked `runtime`
require Scheme → Run → Options → Language testing in Simulator across
languages.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Surface` | The localization surface affected: `HardcodedString`, `Pluralization`, `RTL`, `Formatters`, `StringCatalog`, `AttributedString`, `InfoPlist`, `AssetCatalog`, `AccessibilityStrings`, `Locale` |
| `Verification` | `code` (inspectable) or `runtime` (requires Simulator language switch) |

Full schema:
```
| ID | Severity | Surface | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews ten categories:

| # | Category | Covers |
|---|---|---|
| 1 | Hardcoded user-facing strings | Any user-visible string literal not in a String Catalog / `Localizable.strings` / `LocalizedStringResource` / `LocalizedStringKey`; including `Alert` titles, error messages, accessibility labels |
| 2 | String Catalog (Xcode 15+) migration | Project should use `Localizable.xcstrings` (String Catalog) for new code, not the legacy `.strings` + `.stringsdict` pair; flag legacy-only projects post-Xcode 15 |
| 3 | Pluralization | `.stringsdict` (legacy) or String Catalog variations for plural forms; `Text("\(count) items")` patterns using grammar-aware formatters; CLDR plural categories (zero / one / two / few / many / other) |
| 4 | RTL (right-to-left) layout | Use `leading` / `trailing` not `left` / `right`; flip-mirror for asymmetric icons (`flipsForRightToLeftLayoutDirection`); `Image(systemName:)` SF Symbols auto-mirror appropriate ones; explicit `Environment(\.layoutDirection)` checks when needed |
| 5 | Locale-aware formatters | `Date.FormatStyle`, `Number.FormatStyle`, `Measurement.FormatStyle`, `Currency.FormatStyle` over manual string concatenation; `Locale.current`; calendar / time-zone awareness; ISO format vs locale-format choice |
| 6 | AttributedString localization | `AttributedString(localized:)` for inline markdown / styling in localized strings; `Markdown` support in `Text`; placement of placeholders preserved across languages |
| 7 | `Info.plist` localization | `InfoPlist.xcstrings` (Xcode 15+) or `InfoPlist.strings` per locale; `CFBundleDisplayName`, purpose strings (`NSCameraUsageDescription`, etc.) localized per supported language; `LSApplicationQueriesSchemes` reviewed |
| 8 | Asset catalog localization | App Icon variants, image assets with language qualifiers; localized images via `Localized Resources` in asset catalog |
| 9 | Accessibility strings | `.accessibilityLabel`, `.accessibilityHint`, `.accessibilityValue` localized via String Catalog (not hardcoded) |
| 10 | Locale, calendar, time zone correctness | `Calendar.current` vs explicit calendar; time-zone awareness on stored dates; numeric inputs / currency entry handling commas vs periods; non-Gregorian calendar support if relevant |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | Layout broken in RTL on a primary surface; pluralization wrong leading to user confusion at scale; hardcoded English strings shipping to multilingual market |
| **High** | Localization missing for any string the user sees in normal flow; locale-unaware formatter producing wrong currency / date for the user's locale; purpose strings (Info.plist) not localized (App Store flag) |
| **Medium** | Legacy `.strings` instead of String Catalog; missing pluralization handling on a low-frequency surface; manual string concatenation that would benefit from `FormatStyle` |
| **Low** | Edge-case locale (Arabic numerals, non-Gregorian calendar) not supported when not in target market; minor formatter improvements |

If the project ships only to en-US: most findings drop a tier. If the
project ships to RTL languages: RTL findings escalate.

---

## Phase 1: Audit-specific orient

### Tooling

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"

# Snapshot localization assets
find "$PROJECT_CWD" -name "*.xcstrings" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; head -100 "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/string-catalogs.txt" 2>&1

find "$PROJECT_CWD" -name "*.strings" -not -path '*/.*' \
  -not -path '*/Pods/*' \
  -exec sh -c 'echo "=== $1 ==="; head -50 "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/legacy-strings.txt" 2>&1

find "$PROJECT_CWD" -name "*.stringsdict" -not -path '*/.*' \
  -exec sh -c 'echo "=== $1 ==="; cat "$1"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/stringsdict.txt" 2>&1

# Detect declared supported languages
find "$PROJECT_CWD" -name "Info.plist" -not -path '*/.*' -not -path '*/Pods/*' \
  -exec sh -c '/usr/libexec/PlistBuddy -c "Print :CFBundleLocalizations" "$1" 2>/dev/null \
    && echo "[from $1]"' _ {} \; \
  > "$AUDIT_DIR/tooling-raw/supported-languages.txt" 2>&1

# Grep for hardcoded-looking strings near UI code (candidate signal)
{
  echo "=== Candidate hardcoded strings in Text(\"...\") ===";
  grep -rn 'Text("[A-Z]' --include="*.swift" "$PROJECT_CWD" 2>/dev/null \
    | grep -v "LocalizedStringKey\|String(localized:" | head -100;
  echo;
  echo "=== Alert/Button hardcoded titles ===";
  grep -rn 'Alert(title.*Text("\|Button("' --include="*.swift" "$PROJECT_CWD" 2>/dev/null \
    | grep -v "LocalizedStringKey" | head -50;
} > "$AUDIT_DIR/tooling-raw/grep-candidates.txt"
```

### Emergency exit

None.

### Survey

Beyond the framework baseline:

- Read `tooling-raw/supported-languages.txt` to determine declared
  target languages — affects severity calibration
- Note whether the project uses String Catalogs (`*.xcstrings`),
  legacy `.strings`, or mixed; and whether `.stringsdict` is used for
  pluralization
- Check whether RTL languages (Arabic, Hebrew, Persian) are declared
  targets — if yes, RTL findings escalate
- Identify the formatter style in use: modern `FormatStyle` API
  (iOS 15+) or legacy `DateFormatter` / `NumberFormatter`
- Read at least 5 representative SwiftUI views to assess hardcoded-
  string patterns
- **If no Swift/Apple source found**: notify and stop

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple platform localization audit of
[RESOLVED_SCOPE]. Tooling output is in $AUDIT_DIR/tooling-raw/.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | Surface | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

Surface column: HardcodedString, Pluralization, RTL, Formatters,
StringCatalog, AttributedString, InfoPlist, AssetCatalog,
AccessibilityStrings, Locale.
Verification: code (inspectable) or runtime (requires Simulator
language switch).

Read tooling-raw/supported-languages.txt first to see what languages
the project declares — calibrate severity accordingly.

Cover these 10 categories:
(1) Hardcoded user-facing strings — any user-visible string literal
not wrapped in LocalizedStringResource, LocalizedStringKey, or
loaded from a String Catalog. Includes accessibility labels, alert
titles, error messages.
(2) String Catalog migration — Xcode 15+ projects should use
Localizable.xcstrings (String Catalog). Flag pure-legacy projects.
(3) Pluralization — .stringsdict (legacy) or String Catalog
variations for plural forms; CLDR plural categories (zero / one /
two / few / many / other).
(4) RTL layout — leading/trailing not left/right;
flipsForRightToLeftLayoutDirection on asymmetric icons; SF Symbols
auto-mirror behavior; layoutDirection checks where needed.
(5) Locale-aware formatters — Date.FormatStyle, Number.FormatStyle,
Measurement.FormatStyle, Currency.FormatStyle over manual
concatenation; Locale.current; calendar / time-zone awareness; ISO
vs locale format choice.
(6) AttributedString localization — AttributedString(localized:) for
inline markdown / styling; Markdown in Text; placeholders preserved
across languages.
(7) Info.plist localization — InfoPlist.xcstrings (modern) or
InfoPlist.strings per locale; CFBundleDisplayName, purpose strings
localized per supported language.
(8) Asset catalog localization — App Icon variants, image assets
with language qualifiers; localized images via Localized Resources.
(9) Accessibility strings — .accessibilityLabel, .accessibilityHint,
.accessibilityValue localized via String Catalog (not hardcoded).
(10) Locale / calendar / time-zone correctness — Calendar.current vs
explicit calendar; time-zone awareness on stored dates; numeric and
currency entry; non-Gregorian calendar support if relevant.

Rate severity considering the project's declared target languages
(read supported-languages.txt). Hardcoded strings shipping to a
multilingual market are Critical; same finding on an en-US-only app
is Low.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. Read `tooling-raw/supported-languages.txt` first.
Use the grep candidates as a starting point but validate each (some
hardcoded-looking strings are debug-only or internal).

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md and the tooling output in
$AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not
improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md
covering:
(1) False positives — hardcoded strings that are debug-only or
internal-only (e.g. logging strings, internal admin tools); RTL
findings on an en-US-only app; pluralization findings on a string
that doesn't actually take a count.
(2) Severity miscalibrations — findings rated too high for the
project's declared target languages; or too low if the project is
about to add languages.
(3) Missing findings — localization issues both reviewers missed,
especially: localized-string keys that lost their placeholders,
String Catalog "needs review" flags ignored, regional differences
within a language (en-GB vs en-US date formats), keyboard / input
method assumptions, currency symbol placement, week-start-day
assumptions, paper-size formats.
(4) Remediation steps that are impractical (e.g. migrating
everything to String Catalog when the deployment target is iOS 16
where String Catalog isn't fully supported).
Be specific. Every challenge must cite the finding ID and the
Surface.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. Hand-off note: localization
verification requires Simulator language testing (Scheme → Run →
Options → Application Language / Application Region) — specify the
languages to test in each task.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, Surface, Verification mode,
      location, issue, remediation, verification with specific
      language(s) to test
- [ ] Severity calibrated to the declared target languages in
      `Info.plist` `CFBundleLocalizations`
- [ ] Runtime-verification note included in hand-off

---

## Reference

- Audit reference doc: [`docs/apple-localization/README.md`](../docs/apple-localization/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- String Catalogs: https://developer.apple.com/documentation/xcode/localizing-and-varying-text-with-a-string-catalog
- Localizing strings programmatically: https://developer.apple.com/documentation/foundation/localization
- FormatStyle: https://developer.apple.com/documentation/foundation/formatstyle
- AttributedString localization: https://developer.apple.com/documentation/foundation/attributedstring
- CLDR plural rules: https://unicode-org.github.io/cldr/ldml/tr35-numbers.html#Language_Plural_Rules
