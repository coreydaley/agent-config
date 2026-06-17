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
- Evidence: file:line citation, supported-languages.txt reference, or specific code reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that don't actually apply in context.
Specifically for Apple localization:
- Hardcoded strings that are debug-only, logging, or internal admin tools
  (not user-visible).
- RTL findings on an en-US-only app (project declares no RTL targets in
  CFBundleLocalizations).
- Pluralization findings on a string that doesn't actually take a count.
- "Hardcoded English" findings on string literals that are deliberate
  brand names, product names, or technical identifiers that don't
  translate.
- Legacy .strings flagged for migration on a project with iOS 16
  deployment target where String Catalog isn't fully supported.

(2) Severity miscalibrations — findings rated too high for the
project's declared target languages (per supported-languages.txt) — or
too low if the project is about to add languages. Specifically:
- A hardcoded string rated Critical when the project only declares en.
- An RTL finding rated Low when the project ships to ar/he/fa.
- A formatter finding rated Low when currency handling is involved
  (financial implications).

(3) Missing findings — localization issues the review missed,
especially:
- Localized-string keys that lost their placeholders across translations
  (placeholder count mismatch).
- String Catalog "needs review" or "stale" flags ignored.
- Regional differences within a language (en-GB vs en-US date formats,
  metric vs imperial Measurement).
- Keyboard / input method assumptions (e.g. assuming Latin-script
  numeric entry).
- Currency symbol placement (prefix vs suffix vs surrounding spacing).
- Week-start-day assumptions (Sunday vs Monday).
- Paper-size format assumptions (Letter vs A4).
- Non-Gregorian calendar support gaps where the user's locale uses one
  (Japanese era, Hebrew, Islamic).
- Plural-bearing strings in StringsDict missing categories required by
  declared languages (Arabic needs zero/one/two/few/many/other).
- Mixed-localizations flag in Info.plist (CFBundleAllowMixedLocalizations)
  set inappropriately.

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse exploit than any single finding represents. Be
explicit about the chain and the combined severity (e.g. "multilingual
market declaration + 30 hardcoded strings on Home = the locale launch
is effectively English-only despite the listing").

(5) Impractical/incomplete/wrong remediations — e.g. recommending
String Catalog migration on a deployment target where String Catalog
isn't supported; recommending FormatStyle on iOS 14; recommending RTL
fixes that don't address all the affected surfaces; recommending
"localize this string" without specifying which existing String
Catalog / .strings file should receive it.

(6) Verification steps that don't actually prove the fix works —
Apple-localization verification requires Simulator language switching
(Scheme → Run → Options → Application Language / Application Region) on
the specific affected locales. "Manual review" is insufficient.
Pseudo-locale (Right-to-Left Pseudolanguage, Double-Length
Pseudolanguage) is acceptable for layout / overflow checks.

Be specific. Every challenge must cite the finding ID and reference the
Surface where applicable.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
