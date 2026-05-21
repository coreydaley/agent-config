# Apple App Store Review Audit Reference

Schema and severity reference for the `/audit-apple-app-store-review`
command. Anchored to Apple's App Store Review Guidelines. For the
shared 5-phase audit pattern, see [`../../lib/audit-framework.md`](../../lib/audit-framework.md).

Audit artifacts: `~/Reports/<org>/<repo>/audits/<TS>-apple-app-store-review/`

**Goal**: preempt the most common App Review rejection reasons before
submission.

## Output

| File / Folder | Description |
|---|---|
| `tooling-raw/` | `info-plist-full.txt`, `privacy-manifests.txt`, `storekit-usage.txt`, `auth-and-push.txt`, `placeholder-content.txt` |
| `claude.md` | Claude's review (ID prefix `A`) |
| `codex.md` | Codex's review (ID prefix `C`) |
| `synthesis.md` | Unified findings (`S`-prefix IDs) |
| `devils-advocate.md` | Codex challenge |
| `REPORT.md` | Findings report with `Submission Blocker` section above P0 |

## Schema

```
| ID | Severity | Guideline | Section | Rejection Likelihood | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

**Guideline**: most-specific App Store Review Guidelines subsection
(e.g. `2.1`, `2.3.7`, `3.1.1`, `4.0`, `5.1.1`).

**Section**: `1. Safety`, `2. Performance`, `3. Business`, `4. Design`,
`5. Legal`.

**Rejection Likelihood**: `Will Reject` (clear violation), `Likely Reject`
(judgment call, unfavorable), `Risk` (gray area), `Best Practice`.

**Verification**: `code` or `runtime` (App Store Connect / TestFlight /
device review).

## Sections Reviewed

The audit walks all 5 Guidelines sections:

| Section | Most-common rejection patterns |
|---|---|
| **1. Safety** | UGC without moderation; missing report/block; kids-category violations; medical/firearms disclaimers; developer contact info |
| **2. Performance** | Crashes; placeholder content; broken features; "coming soon"; broken demo credentials; screenshots don't match shipping app; private API usage |
| **3. Business** | IAP rules for digital goods; subscription disclosure; auto-renewal terms in app + on web; restore mechanism; external-payment scope rules |
| **4. Design** | Low-quality / clone apps; minimum-functionality ("just a website"); push promotion without opt-in; Sign in with Apple required when third-party sign-in offered |
| **5. Legal** | Privacy policy accurate; ATT when IDFA accessed; Privacy Manifest accurate (see `audit-apple-privacy` for depth); HealthKit consent; COPPA / kids; location justification; IP / copycats |

## Severity (Rejection Likelihood drives it)

| Rejection Likelihood | Default Severity |
|---|---|
| Will Reject | Critical (Submission Blocker) |
| Likely Reject | High |
| Risk | Medium |
| Best Practice | Low |

## Sprint Mapping

**Critical findings → Submission Blocker section above P0**:

| Severity | Sprint Priority |
|---|---|
| **Critical (Will Reject)** | **Submission Blocker — fix before next App Store submission** |
| High (Likely Reject) | P0 — Must Ship |
| Medium (Risk) | P1 — Ship If Capacity Allows |
| Low (Best Practice) | Deferred |

## Inherent Limitations

App Review enforcement varies in practice. Static review surfaces
likely rejection causes, but reviewers exercise judgment and Apple
updates the Guidelines frequently. Treat findings as "high likelihood
of rejection" rather than "Apple will definitely reject."

This audit reflects the Guidelines structure as of late 2025. When in
doubt, read the current Guidelines.

If `audit-apple-privacy` has been run on the same scope, reference its
findings for Section 5.1.1 depth rather than duplicating.

## References

- Subagent: [`../../subagents/audit-apple-app-store-review.md`](../../subagents/audit-apple-app-store-review.md)
- Sibling: [`../apple-privacy/README.md`](../apple-privacy/README.md)
- App Store Review Guidelines (current): https://developer.apple.com/app-store/review/guidelines/
- App Store product page best practices: https://developer.apple.com/app-store/product-page/
- App Tracking Transparency: https://developer.apple.com/documentation/apptrackingtransparency
- Sign in with Apple: https://developer.apple.com/sign-in-with-apple/
- StoreKit: https://developer.apple.com/documentation/storekit
