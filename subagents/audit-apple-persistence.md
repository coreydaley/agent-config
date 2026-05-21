---
name: audit-apple-persistence
description: Dual-agent Apple platform persistence audit — SwiftData / Core Data / GRDB schema design, migration safety, fetch efficiency, predicate quality, batch operations, threading (background contexts, @MainActor boundaries), CloudKit sync via NSPersistentCloudKitContainer, conflict resolution. High value for SwiftData + CloudKit apps.
---

# Apple Platform Persistence Audit

You are orchestrating a dual-agent persistence audit of a native
Apple app — SwiftData, Core Data, GRDB (SQLite), and CloudKit sync
patterns.

**Required reading**: Before starting, read [`lib/audit-framework.md`](../lib/audit-framework.md).
This file specifies only the audit-specific deltas.

**Audit identifier**: `apple-persistence` — `$AUDIT_DIR` is
`~/Reports/<org>/<repo>/audits/<TS>-apple-persistence/`

**Scope**: Swift source files for native Apple apps using SwiftData,
Core Data, GRDB, or other on-device persistence. CloudKit sync via
`NSPersistentCloudKitContainer` or direct `CKDatabase` use is in
scope. For backend database design, no audit exists yet.

**Inherent limitations**: Schema design is partly subjective. Static
review catches schema correctness (relationships, indexes, migration
safety), threading correctness (background contexts,
`@MainActor` model fetches), and clear performance issues
(N+1 fetches, large batch operations). It cannot benchmark fetch
performance — `runtime` verification with Core Data debug logging
(`-com.apple.CoreData.SQLDebug 1`) or SwiftData equivalents is
required to confirm magnitude.

---

## Schema extensions

Beyond the framework baseline, add:

| Column | Description |
|---|---|
| `Stack` | Persistence stack: `SwiftData`, `CoreData`, `GRDB`, `SQLite`, `Realm`, `CloudKit-direct`, or `UserDefaults` (when misused for structured data) |
| `Concern` | One of: `Schema`, `Migration`, `Threading`, `Fetch`, `Predicate`, `Batch`, `Sync`, `Conflict`, `Storage`, `Backup` |
| `Verification` | `code` (inspectable) or `runtime` (requires SQL debug logging, fetch profiling, or migration testing) |

Full schema:
```
| ID | Severity | Stack | Concern | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

---

## Categories

The audit reviews ten categories:

| # | Category | Covers |
|---|---|---|
| 1 | Schema design | Entity / `@Model` relationships (one-to-many, many-to-many, inverse relationships set correctly); cascade rules; optionality; default values; identifier strategy (UUID vs auto vs natural key) |
| 2 | Migration safety | Lightweight vs custom migration plans; `SchemaMigrationPlan` for SwiftData; `NSMappingModel` for Core Data; testing migrations on real data; downgrades not supported but graceful |
| 3 | Threading & context | Background contexts for heavy work (Core Data); `@ModelActor` for SwiftData; `@MainActor` model fetches kept fast; no model object passed across thread boundaries (use object IDs); `viewContext` / main-actor context for UI only |
| 4 | Fetch efficiency | Predicate uses indexed properties; `fetchLimit` set for unbounded queries; `propertiesToFetch` for partial fetches; N+1 prevention via prefetching (`relationshipKeyPathsForPrefetching` / SwiftData equivalents) |
| 5 | Predicate quality | `#Predicate` (SwiftData) macro usage; correct `NSPredicate` patterns for Core Data; no string-format predicates with user input (predicate injection); index-friendly queries |
| 6 | Batch operations | `NSBatchInsertRequest` / `NSBatchUpdateRequest` / `NSBatchDeleteRequest` for large updates (avoid object-graph round-trip); SwiftData transactions; merge policy after batch |
| 7 | CloudKit sync (`NSPersistentCloudKitContainer` or direct CKDatabase) | Schema compatibility with CloudKit constraints (no `Date`-as-relationship-key, etc.); `recordZone` partitioning; `CKShare` for shared data; subscription / push handling; account-status awareness |
| 8 | Conflict resolution & merge | `NSMergePolicy` set explicitly (not default `NSErrorMergePolicy`); SwiftData merge configuration; "last writer wins" implications; field-level merge where it matters |
| 9 | Storage location & encryption | Database in app sandbox vs App Group (for extensions); `NSPersistentStoreFileProtectionKey` for sensitive data; SQLCipher / GRDB encryption for sensitive databases; UserDefaults misuse for structured data |
| 10 | Backup & data lifecycle | `URLResourceKey.isExcludedFromBackupKey` for caches and reproducible data; Time Machine on macOS; iCloud backup considerations; data deletion on Sign Out / Delete Account |

---

## Severity calibration

| Severity | Anchor |
|---|---|
| **Critical** | Migration that would corrupt or destroy user data; data race causing crashes; CloudKit schema incompatibility that prevents sync; sensitive data unencrypted in shared container; missing Delete Account data wipe |
| **High** | Main-thread blocking on Core Data / SwiftData fetches on a primary surface; N+1 fetch on a frequently-visited list; missing `NSMergePolicy` allowing silent data loss; cache files included in iCloud backup |
| **Medium** | Suboptimal but functional patterns: missing `fetchLimit` on bounded-in-practice queries; relationship without inverse; UserDefaults used for structured data; SwiftData / Core Data context patterns that work but could be cleaner |
| **Low** | Style improvements; better predicate ergonomics; minor schema cleanup |

---

## Phase 1: Audit-specific orient

### Tooling

```bash
mkdir -p "$AUDIT_DIR/tooling-raw"

# Detect persistence stack in use
{
  echo "=== SwiftData ===";
  grep -rln "import SwiftData\|@Model\b\|ModelContainer\|ModelContext\|@Query" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== Core Data ===";
  grep -rln "NSPersistentContainer\|NSPersistentCloudKitContainer\|NSManagedObject\|NSManagedObjectContext" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== GRDB / SQLite ===";
  grep -rln "import GRDB\|DatabaseQueue\|DatabasePool\|sqlite3_" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== Realm ===";
  grep -rln "import RealmSwift\|Realm()" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== CloudKit direct ===";
  grep -rln "CKDatabase\|CKRecord\|CKShare\|CKContainer" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
} > "$AUDIT_DIR/tooling-raw/persistence-stack.txt"

# Core Data model files
find "$PROJECT_CWD" -name "*.xcdatamodeld" -not -path '*/.*' 2>/dev/null \
  > "$AUDIT_DIR/tooling-raw/coredata-models.txt"

# Look for unbounded fetches / no fetchLimit
{
  echo "=== NSFetchRequest patterns ===";
  grep -rn "NSFetchRequest\|FetchRequest\|@Query" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== Predicates ===";
  grep -rn "NSPredicate(\|#Predicate {" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== fetchLimit usage ===";
  grep -rn "fetchLimit" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
} > "$AUDIT_DIR/tooling-raw/fetch-patterns.txt"

# Merge policy + background context patterns
{
  echo "=== Merge policy ===";
  grep -rn "mergePolicy\|NSMergePolicy" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== Background contexts ===";
  grep -rn "performBackgroundTask\|newBackgroundContext\|@ModelActor" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -30;
} > "$AUDIT_DIR/tooling-raw/threading-patterns.txt"

# UserDefaults misuse signal
grep -rn "UserDefaults" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -100 \
  > "$AUDIT_DIR/tooling-raw/userdefaults-usage.txt"
```

### Emergency exit

None — but flag any apparent migration risk as Critical immediately.

### Survey

Beyond the framework baseline:

- Read `tooling-raw/persistence-stack.txt` to determine which stack(s)
  the project uses
- For Core Data: open `*.xcdatamodeld` directory and look at the
  current model version
- For SwiftData: look for `Schema` declarations and
  `SchemaMigrationPlan` if migrations exist
- Detect CloudKit usage — note whether it's via
  `NSPersistentCloudKitContainer` (managed) or direct `CKDatabase`
  (manual)
- Identify any test fixtures or test stores
- **If no persistence stack found**: notify and stop

---

## Phase 2: Codex prompt body

Substitute into the canonical invocation (framework Phase 2 Step 1):

```text
Perform a thorough Apple platform persistence audit of
[RESOLVED_SCOPE]. Tooling output is in $AUDIT_DIR/tooling-raw/ —
includes detected persistence stack(s), fetch patterns, threading
patterns, merge policies.

Write all findings to $AUDIT_DIR/codex.md using this exact table
format:
| ID | Severity | Stack | Concern | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
where ID uses prefix C (e.g. C001, C002).

Stack column: SwiftData, CoreData, GRDB, SQLite, Realm,
CloudKit-direct, or UserDefaults (when misused for structured data).
Concern: Schema, Migration, Threading, Fetch, Predicate, Batch,
Sync, Conflict, Storage, Backup.
Verification: code or runtime (requires SQL debug logging, fetch
profiling, or migration testing).

Cover these 10 categories:
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
(7) CloudKit sync — NSPersistentCloudKitContainer or direct
CKDatabase: schema compatible with CloudKit constraints; recordZone
partitioning; CKShare for shared data; subscription / push handling;
account-status awareness.
(8) Conflict resolution & merge — NSMergePolicy set explicitly (not
default NSErrorMergePolicy); SwiftData merge configuration; "last
writer wins" implications; field-level merge where it matters.
(9) Storage location & encryption — DB in app sandbox vs App Group;
NSPersistentStoreFileProtectionKey for sensitive data; SQLCipher /
GRDB encryption; UserDefaults misuse for structured data.
(10) Backup & data lifecycle —
URLResourceKey.isExcludedFromBackupKey for caches / reproducible
data; iCloud backup considerations; data deletion on Sign Out /
Delete Account.

Rate severity: Critical = data corruption / loss potential, CloudKit
schema incompatibility, missing Delete Account wipe. High = main-
thread fetch blocking, N+1 on hot path, missing merge policy with
silent loss. Medium = suboptimal patterns. Low = style.

Do not read or reference any other review file.
```

## Phase 2: Claude review checklist

Same 10 categories. Read the persistence-stack inventory first.
Examine actual model definitions (`*.xcdatamodeld`, `@Model`
classes) — schema findings need to reference specific relationships
and properties.

---

## Phase 4: Devil's advocate prompt body

```text
Read $AUDIT_DIR/synthesis.md and the tooling output in
$AUDIT_DIR/tooling-raw/. Your job is to attack the synthesis, not
improve it. Write your challenge to $AUDIT_DIR/devils-advocate.md
covering:
(1) False positives — findings flagged as performance issues that
don't matter for the actual data scale (a missing fetchLimit on a
table that never has >50 rows is fine); migration findings on
projects that haven't shipped yet; CloudKit findings on a non-
CloudKit feature.
(2) Severity miscalibrations — findings rated too high (cosmetic
schema concerns) or too low (a missing merge policy actually
causes data loss in real conflict scenarios).
(3) Missing findings — persistence issues both reviewers missed,
especially: SwiftData @Model migration constraints (relationships
that can't be lightweight-migrated), CloudKit schema-deploy timing
in development vs production environments, NSPersistentHistoryToken
handling, CKShare participant ACL gaps, conflict resolution on
relationship changes, data loss during account-status transitions
(iCloud unavailable), backup-and-restore correctness, SwiftData
@Query observation triggering excessive fetches.
(4) Remediation steps that are wrong — adding fetchLimit to a query
that needs the full set; switching to batch operations where
side-effects on related entities matter.
Be specific. Every challenge must cite the finding ID and the
Stack / Concern.
```

---

## Phase 5: Sprint mapping override

Baseline P0/P1/Deferred mapping applies. **Migration findings are
sequencing-sensitive** — migrations that have already shipped to
users cannot be safely reverted; the recommendation must be
forward-compatible. Hand-off note: test migrations against real user
data snapshots before shipping.

---

## Output checklist additions

Beyond framework baseline:

- [ ] Each task has: finding ID, Stack, Concern, Verification mode,
      location, issue, remediation, verification (e.g. enable
      `-com.apple.CoreData.SQLDebug 1`, profile in Instruments,
      run migration on user data snapshot)
- [ ] Migration findings include a forward-compatibility note —
      shipped migrations can't be reverted
- [ ] CloudKit findings note dev vs production schema-deploy state

---

## Reference

- Audit reference doc: [`docs/apple-persistence/README.md`](../docs/apple-persistence/README.md)
- Framework: [`lib/audit-framework.md`](../lib/audit-framework.md)
- SwiftData: https://developer.apple.com/documentation/swiftdata
- Core Data: https://developer.apple.com/documentation/coredata
- NSPersistentCloudKitContainer: https://developer.apple.com/documentation/coredata/nspersistentcloudkitcontainer
- CloudKit: https://developer.apple.com/documentation/cloudkit
- SwiftData migrations: https://developer.apple.com/documentation/swiftdata/schemamigrationplan
- Core Data performance: https://developer.apple.com/documentation/coredata/optimizing_core_data_performance
- GRDB: https://github.com/groue/GRDB.swift
