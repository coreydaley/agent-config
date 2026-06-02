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
- Evidence: file:line citation, compensating control identification, or specific code reference
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings flagged as performance issues that
don't matter for the actual data scale (a missing fetchLimit on a
table that never has >50 rows is fine); migration findings on
projects that haven't shipped yet; CloudKit findings on a non-
CloudKit feature; UserDefaults findings on an actually-non-sensitive
preference value; relationship-inverse findings where the schema is
correct but the inverse is intentionally one-directional.

(2) Severity miscalibrations — findings rated too high (cosmetic
schema concerns; missing fetchLimit on inherently bounded tables;
deprecated-but-functional API with no immediate risk) or too low
(a missing merge policy that actually causes data loss in real
conflict scenarios; an inverse-relationship gap that lets cascade
deletes silently orphan records; an unencrypted shared-container
store that holds sensitive data).

(3) Missing findings — persistence issues both reviewers missed,
especially:
- SwiftData @Model migration constraints (relationships that can't
  be lightweight-migrated)
- CloudKit schema-deploy timing in development vs production
  environments
- NSPersistentHistoryToken handling (or absence) for change tracking
- CKShare participant ACL gaps
- Conflict resolution on relationship changes (not just attribute
  changes)
- Data loss during account-status transitions (iCloud unavailable)
- Backup-and-restore correctness (excluded-from-backup logic that
  silently drops user content)
- SwiftData @Query observation triggering excessive fetches on
  parent-state churn
- NSPredicate injection via string-format with user input
- App Group container pollution from extensions writing without
  coordination
- File coordination races (NSFileCoordinator missing on
  multi-process stores)

(4) Missing compound paths — separate findings in the synthesis that
combine into a worse outcome than any single finding represents.
Apple-persistence-specific chains to look for: unsafe migration +
CloudKit mirror; missing merge policy + background writes; CloudKit
incompatible schema + production deploy; no fetchLimit + @Query on
hot surface; encryption gap + App Group; incomplete Delete Account +
CloudKit. Be explicit about the chain and the combined severity.

(5) Impractical/incomplete/wrong remediations — e.g. adding
fetchLimit to a query that needs the full set; switching to batch
operations where side-effects on related entities matter; "use
SchemaMigrationPlan" without specifying the migration strategy
(lightweight vs custom); "encrypt the database" without naming the
file-protection class or library (SQLCipher vs
NSFileProtectionComplete vs GRDB encryption); rotating CloudKit
schema without addressing already-deployed-production state.

(6) Insufficient verification — Apple-persistence verification often
requires runtime evidence: SQL debug logging
(-com.apple.CoreData.SQLDebug 1), Instruments fetch profiling, a
migration dry-run against a real (or representative) user data
snapshot, or CloudKit dashboard schema inspection. "Manual review"
or "code inspection" is insufficient for performance, migration, and
sync correctness claims.

Be specific. Every challenge must cite the finding ID and reference
the Stack / Concern where applicable.

Do not read or reference any other review file beyond synthesis.md and
the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type "no_challenges"
  and Confidence "high" stating that you attempted but found nothing
  worth surfacing.
- No emojis.
