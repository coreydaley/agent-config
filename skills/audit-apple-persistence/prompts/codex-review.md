Perform a thorough Apple platform persistence audit of the scope at the
project root you've been pointed at. Tooling output is in the audit
dir's tooling-raw/ subdirectory — includes detected persistence
stack(s), Core Data model file paths, fetch patterns, threading
patterns, merge policies, and UserDefaults usage. Read those files
first.

Write all findings to codex.md (in the audit dir you were granted write
access to) using this exact table format:

| ID | Severity | Stack | Concern | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where ID uses prefix C (e.g. C001, C002).

Stack column: SwiftData, CoreData, GRDB, SQLite, Realm,
CloudKit-direct, or UserDefaults (when misused for structured data).
Concern: Schema, Migration, Threading, Fetch, Predicate, Batch,
Sync, Conflict, Storage, Backup.
Verification: code or runtime (requires SQL debug logging, fetch
profiling, or migration testing).

Cover these 10 categories (skip if not applicable):

(1) Schema design — entity / @Model relationships (one-to-many,
many-to-many, inverse set correctly); cascade rules; optionality;
default values; identifier strategy (UUID vs auto vs natural key).

(2) Migration safety — lightweight vs custom migration plans;
SchemaMigrationPlan for SwiftData; NSMappingModel for Core Data;
testing migrations on real data; downgrade behavior graceful.

(3) Threading & context — background contexts for heavy work (Core
Data); @ModelActor for SwiftData; @MainActor model fetches kept
fast; no model objects across thread boundaries (use object IDs);
viewContext / main context for UI only.

(4) Fetch efficiency — predicate uses indexed properties; fetchLimit
set for unbounded queries; propertiesToFetch for partial fetches;
N+1 prevention via prefetching
(relationshipKeyPathsForPrefetching).

(5) Predicate quality — #Predicate (SwiftData) macro usage; correct
NSPredicate patterns for Core Data; no string-format predicates with
user input (injection risk); index-friendly queries.

(6) Batch operations — NSBatchInsertRequest / NSBatchUpdateRequest /
NSBatchDeleteRequest for large updates (avoid object-graph
round-trip); SwiftData transactions; merge policy after batch.

(7a) CloudKit sync via NSPersistentCloudKitContainer (Core Data
mirroring): mirrors to the CloudKit PRIVATE database; schema
compatible with CloudKit constraints (no Date-as-relationship-key;
only attribute types CloudKit supports; no required-non-default
attributes added in later model versions); persistent-history
tracking enabled; share integration via the container's share APIs
(share(_:to:)); accountStatus checked before sync; schema deployed
to production environment.

(7b) CloudKit direct (CKDatabase / CKContainer outside the
persistent container): CUSTOM-ZONE partitioning for shared content;
manual CKSubscription setup + silent-push handling; CKShare
participant ACLs when not using the container share APIs;
CKContainer.default() vs explicit identifier; CloudKit Web Services
tokens never embedded.

(8) Conflict resolution & merge — NSMergePolicy set explicitly (not
default NSErrorMergePolicy); SwiftData merge configuration; "last
writer wins" implications; field-level merge where it matters.

(9) Storage location & encryption — DB in app sandbox vs App Group;
NSPersistentStoreFileProtectionKey for sensitive data; SQLCipher /
GRDB encryption; UserDefaults misuse for structured data.

(10) Backup & data lifecycle —
URLResourceKey.isExcludedFromBackupKey for caches / reproducible
data; iCloud backup considerations; data deletion on Sign Out /
Delete Account (including CloudKit mirror).

Rate severity on evidence: impact, exploitability/reachability (data
scale matters), blast radius, compensating controls.

Critical anchors:
- Migration that would corrupt or destroy user data
- Data race causing crashes
- CloudKit schema incompatibility that prevents sync
- Sensitive data unencrypted in shared App Group container
- Missing Delete Account data wipe (especially when CloudKit mirror persists)

High anchors:
- Main-thread blocking on Core Data / SwiftData fetches on a primary surface
- N+1 fetch on a frequently-visited list
- Missing NSMergePolicy allowing silent data loss
- Cache files included in iCloud backup
- Predicate injection via string-format NSPredicate with user input

Medium anchors:
- Missing fetchLimit on bounded-in-practice queries
- Relationship without inverse
- UserDefaults used for structured but non-sensitive data

Low anchors:
- Style improvements; better predicate ergonomics; minor schema cleanup

Every finding must include a Verification field — for persistence this
often means runtime verification: enable -com.apple.CoreData.SQLDebug 1,
profile fetches in Instruments, dry-run migrations against a snapshot
of real user data, or check CloudKit schema state in the developer
console.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to codex.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.
