# Apple Platform Privacy Audit Reference

Schema and severity reference for the `/audit-apple-privacy` command.
For the shared 5-phase audit pattern, see [`../../lib/audit-framework.md`](../../lib/audit-framework.md).

Audit artifacts: `~/Reports/<org>/<repo>/audits/<TS>-apple-privacy/`

**Relationship to `audit-apple-security`**: Privacy compliance is a
separate audit because Apple treats it separately at App Review and
the concerns differ (privacy = data-practice compliance; security =
attack-resistant code). This audit handles Privacy Manifest, purpose
strings, ATT, required-reason APIs, SDK privacy. `audit-apple-security`
handles Keychain, ATS, entitlements, code signing.

## Output

| File / Folder | Description |
|---|---|
| `tooling-raw/` | `privacy-manifests.txt`, `info-plist-privacy.txt`, `third-party-sdks.txt`, `idfa-att.txt`, `required-reason-candidates.txt` |
| `EMERGENCY.md` | **Only if Phase 1 emergency-exit triggered.** App Store rejection imminent (missing Privacy Manifest; required SDK missing manifest; IDFA without ATT) |
| `claude.md` | Claude's review (ID prefix `A`) |
| `codex.md` | Codex's review (ID prefix `C`) |
| `synthesis.md` | Unified findings (`S`-prefix IDs) |
| `devils-advocate.md` | Codex challenge |
| `REPORT.md` | Findings report with `Submission Blocker` section above P0 |

## Schema

```
| ID | Severity | Concern | Submission Impact | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

**Concern**: `PrivacyManifest`, `PurposeStrings`, `ATT`,
`RequiredReason`, `SDKPrivacy`, `DataMinimization`, `Tracking`,
`Permissions`.

**Submission Impact**: `Submission Blocker` (App Review will reject),
`Submission Risk` (likely flagged), `Compliance` (legally required
regardless of Apple), or `Best Practice`.

**Verification**: `code` or `runtime` (App Privacy Report on device or
App Store Connect Privacy Manifest validation).

## Categories

1. Privacy Manifest presence & accuracy (`PrivacyInfo.xcprivacy`)
2. `Info.plist` purpose strings (`NS*UsageDescription`)
3. App Tracking Transparency (ATT) flow
4. Required-reason APIs (Apple May 2024 rules)
5. Third-party SDK privacy declarations
6. Data minimization
7. Tracking domains
8. Permission UX (point-of-use, pre-prompts, graceful degradation)

## Severity (default mapping)

| Submission Impact | Default Severity |
|---|---|
| Submission Blocker | Critical |
| Submission Risk | High |
| Compliance | Medium |
| Best Practice | Low |

Critical anchors include: missing `PrivacyInfo.xcprivacy` for an app
submitting after May 2024; third-party SDK on Apple's required list
missing its manifest; IDFA accessed without ATT flow; missing purpose
string for accessed sensitive resource.

## Sprint Mapping

**Critical findings → Submission Blocker section above P0**:

| Severity | Sprint Priority |
|---|---|
| **Critical (Submission Blocker)** | **Submission Blocker — fix before next App Store submission** |
| High (Submission Risk) | P0 — Must Ship |
| Medium (Compliance) | P1 — Ship If Capacity Allows |
| Low (Best Practice) | Deferred |

## Inherent Limitations

Privacy compliance is partly mechanical (manifest present? purpose
strings present?) and partly about actual app behavior matching
declared behavior. Static review catches the mechanical parts;
runtime verification catches divergences.

## References

- Subagent: [`../../subagents/audit-apple-privacy.md`](../../subagents/audit-apple-privacy.md)
- Privacy Manifest files: https://developer.apple.com/documentation/bundleresources/privacy_manifest_files
- Required reason APIs: https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api
- App Tracking Transparency: https://developer.apple.com/documentation/apptrackingtransparency
- Apple privacy hub: https://developer.apple.com/privacy/
- Apple's "commonly used SDKs" list: https://developer.apple.com/support/third-party-SDK-requirements/
