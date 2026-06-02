Perform a thorough Apple platform localization audit of the scope at the
project root you've been pointed at. Tooling output is already snapshotted
in the audit dir's tooling-raw/ subdirectory. Read those files first:
supported-languages.txt (the project's declared CFBundleLocalizations —
THIS DRIVES SEVERITY CALIBRATION), string-catalogs.txt, legacy-strings.txt,
stringsdict.txt, lproj-dirs.txt, grep-candidates.txt.

Localization tooling is mostly filesystem inspection and grep — there is
no l10n equivalent of gitleaks/semgrep. Validate, do not duplicate, the
grep candidates — many hardcoded-looking strings are debug-only, logging,
or internal.

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Surface | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002). Surface column must be one of:
HardcodedString, Pluralization, RTL, Formatters, StringCatalog,
AttributedString, InfoPlist, AssetCatalog, AccessibilityStrings, Locale.
Verification: code (statically inspectable) or runtime (requires Simulator
language switch via Scheme → Run → Options → Application Language /
Application Region).

Read supported-languages.txt first to see what languages the project
declares — calibrate severity accordingly. A hardcoded English string is
Critical for an app that ships to 12 languages and Low for an en-US-only
app.

Cover these 10 categories (skip if not applicable):

(1) HardcodedString — any user-visible string literal not wrapped in
LocalizedStringResource, LocalizedStringKey, or loaded from a String
Catalog. Includes accessibility labels, Alert titles, error messages,
Button titles, Toolbar labels.

(2) StringCatalog — Xcode 15+ projects should use Localizable.xcstrings
(String Catalog) for new code, not the legacy .strings + .stringsdict
pair. Flag pure-legacy projects. Also flag String Catalog entries with
"needs review" or "stale" flags carried into shipping builds.

(3) Pluralization — .stringsdict (legacy) or String Catalog variations
for plural forms. Text("\(count) items") patterns using grammar-aware
formatters. CLDR plural categories (zero / one / two / few / many /
other). English-only plural handling on a multilingual app is wrong.

(4) RTL — leading/trailing not left/right;
flipsForRightToLeftLayoutDirection on asymmetric icons; SF Symbols
auto-mirror behavior; explicit layoutDirection checks where needed.
Findings escalate sharply if the project declares ar/he/fa as targets.

(5) Formatters — Date.FormatStyle, Number.FormatStyle,
Measurement.FormatStyle, Currency.FormatStyle over manual concatenation;
Locale.current; calendar / time-zone awareness; ISO format vs locale
format choice. Flag legacy DateFormatter / NumberFormatter on iOS 15+.

(6) AttributedString — AttributedString(localized:) for inline markdown
/ styling; Markdown in Text; placeholders preserved across languages.

(7) InfoPlist — InfoPlist.xcstrings (modern) or InfoPlist.strings per
locale; CFBundleDisplayName, purpose strings (NSCameraUsageDescription,
NSLocationWhenInUseUsageDescription, etc.) localized per supported
language. Missing purpose-string localization is an App Store review flag.

(8) AssetCatalog — App Icon variants, image assets with language
qualifiers; localized images via Localized Resources in asset catalog.

(9) AccessibilityStrings — .accessibilityLabel, .accessibilityHint,
.accessibilityValue localized via String Catalog (not hardcoded).
Hardcoded accessibility strings break VoiceOver in every non-English
locale.

(10) Locale — Calendar.current vs explicit calendar; time-zone awareness
on stored dates; numeric / currency entry handling commas vs periods;
non-Gregorian calendar support if relevant. Week-start-day, paper-size
formats, keyboard / input method assumptions.

Rate severity considering the project's declared target languages (read
supported-languages.txt). Hardcoded strings shipping to a multilingual
market are Critical; the same finding on an en-US-only app is Low.

Critical anchors:
- Layout broken in RTL on a primary surface (project ships to RTL)
- Pluralization wrong leading to user confusion at scale
- Hardcoded English strings shipping to a multilingual market

High anchors:
- Localization missing for any string the user sees in normal flow
- Locale-unaware formatter producing wrong currency / date for the
  user's locale
- Purpose strings (Info.plist) not localized (App Store review flag)

Medium anchors:
- Legacy .strings instead of String Catalog on a post-Xcode-15 project
- Missing pluralization handling on a low-frequency surface
- Manual string concatenation that would benefit from FormatStyle

Low anchors:
- Edge-case locale (Arabic numerals, non-Gregorian calendar) not
  supported when not in target market
- Minor formatter improvements

Every finding must include a Verification field — for localization this
often means runtime verification with Simulator language switching. Note
specific languages to test (e.g. ar-SA for RTL, pl for plural categories).

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
