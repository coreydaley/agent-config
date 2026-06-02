# Node: emergency-exit

Phase 1 detected an imminent App Store rejection condition: missing app-level Privacy Manifest, third-party SDK without its required Privacy Manifest, or IDFA access without an ATT flow. **Halt the audit before Phase 2.** Write `EMERGENCY.md` describing the trigger, what App Review will reject on, and the remediation plan.

## Inputs

- `$AUDIT_DIR/tooling-raw/privacy-manifests.txt`, `third-party-sdks.txt`, `idfa-att.txt`, `distribution-channel.txt`
- Walker state: `audit_dir`, `emergency_reasons`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
EMERGENCY_REASONS=$(scripts/walk.sh get --state "$STATE" --key emergency_reasons)
```

## Steps

### 1. Identify the specific trigger(s)

For each emergency reason recorded by `orient`, classify into one of:

- **Missing app-level Privacy Manifest** — App Review (post-May-2024) will reject any submission lacking `PrivacyInfo.xcprivacy`. Remediation: create one declaring real `NSPrivacyCollectedDataTypes`, `NSPrivacyTracking`, `NSPrivacyAccessedAPITypes`, and `NSPrivacyTrackingDomains`.
- **Third-party SDK without manifest** — Apple's "commonly used SDKs" list (Firebase, Branch, GoogleSignIn, AppsFlyer, Amplitude, Adjust, OneSignal, FBSDK, Mixpanel, Segment, Crashlytics, etc.) MUST ship a `PrivacyInfo.xcprivacy` AND a signature. If the bundled SDK version is too old to include one: (a) pin to a version that includes the manifest, (b) replace with an equivalent SDK that ships compliant, or (c) remove the SDK if its functionality isn't essential.
- **IDFA accessed without ATT** — Any access to `ASIdentifierManager.shared().advertisingIdentifier` requires a prior `ATTrackingManager.requestTrackingAuthorization` call (and the corresponding `NSUserTrackingUsageDescription` purpose string). Remediation: gate IDFA reads behind an ATT-authorized check, or remove IDFA access entirely if not actually needed.

### 2. Write EMERGENCY.md

```bash
cat > "$AUDIT_DIR/EMERGENCY.md" <<EOF
# EMERGENCY EXIT — apple-privacy — $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Trigger

Phase 1 detected one or more **App Store submission blockers**. The audit
has **halted before Phase 2**. No reviewer artifacts will be produced.

## Reasons

$(printf '%b' "$EMERGENCY_REASONS")

## Why App Review will reject

Since Apple's May 2024 enforcement:
- Every App Store submission must include a top-level \`PrivacyInfo.xcprivacy\`.
- Every third-party SDK on Apple's "commonly used SDKs" list must ship its own
  \`PrivacyInfo.xcprivacy\` AND a code signature.
- Any access to IDFA without a preceding ATT flow is a hard rejection.

These are not gray-area policy gaps; App Review rejects deterministically.

## Required actions (in order)

1. **Resolve every reason above before the next App Store submission.**
   - Missing app manifest → author \`PrivacyInfo.xcprivacy\` reflecting
     actual data practices. Validate via App Store Connect's Privacy
     Manifest report after a TestFlight build.
   - SDK missing manifest → pin to a manifest-compliant version, replace,
     or remove. Confirm the resulting bundle contains the SDK's
     \`PrivacyInfo.xcprivacy\` and \`.xcprivacy.sig\`.
   - IDFA without ATT → wrap IDFA reads behind \`ATTrackingManager\`
     authorization; add \`NSUserTrackingUsageDescription\` to Info.plist;
     verify on-device that the prompt appears.
2. **Test on a TestFlight build before re-submitting.**
   App Store Connect surfaces a Privacy Manifest validation report
   automatically; review it before submitting for App Review.
3. **Re-run \`/audit-apple-privacy\`** once the blockers are resolved.
EOF
```

### 3. Tell the user out-of-band

This is not a finding for the next sprint — it's a "next submission will fail" event. Print a stark message to the conversation and point at `$AUDIT_DIR/EMERGENCY.md`.

## Outputs

- `$AUDIT_DIR/EMERGENCY.md` written
- No reviewer artifacts will be produced for this run

## Outgoing edges

- → `terminal` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from emergency_exit --to terminal
```

## Failure modes

- False positive (the project isn't actually App Store-bound; the SDK list match is on a string in vendored docs) → still produce `EMERGENCY.md` with the user-visible "if this is a false positive, re-run with `--allow-noncompliant`" note. Better to over-alert than ship a rejection.

## Notes

- This node is **terminal-bound**. The handoff message format is different: point the user at `EMERGENCY.md` and confirm no Phase 2+ work ran. `audit-verify.sh` handles this case (an `EMERGENCY.md` present in `$AUDIT_DIR` short-circuits the artifact gate).
