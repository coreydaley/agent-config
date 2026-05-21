# Apple Platform Persistence Audit Reference

Schema and severity reference for the `/audit-apple-persistence`
command. For the shared 5-phase audit pattern, see
[`../../lib/audit-framework.md`](../../lib/audit-framework.md).

Audit artifacts: `~/Reports/<org>/<repo>/audits/<TS>-apple-persistence/`

**High value for SwiftData + CloudKit apps.**

## Output

| File / Folder | Description |
|---|---|
| `tooling-raw/` | `persistence-stack.txt` (detected stack), `coredata-models.txt`, `fetch-patterns.txt`, `threading-patterns.txt`, `userdefaults-usage.txt` |
| `claude.md` | Claude's review (ID prefix `A`) |
| `codex.md` | Codex's review (ID prefix `C`) |
| `synthesis.md` | Unified findings (`S`-prefix IDs) |
| `devils-advocate.md` | Codex challenge |
| `REPORT.md` | Sprint-able findings report |

## Schema

```
| ID | Severity | Stack | Concern | Title | Location | Verification | Why It Matters | Recommended Fix | Evidence/Notes |
```

**Stack**: `SwiftData`, `CoreData`, `GRDB`, `SQLite`, `Realm`,
`CloudKit-direct`, or `UserDefaults` (when misused for structured data).

**Concern**: `Schema`, `Migration`, `Threading`, `Fetch`, `Predicate`,
`Batch`, `Sync`, `Conflict`, `Storage`, `Backup`.

**Verification**: `code` or `runtime` (SQL debug logging, fetch profiling,
or migration testing on real data snapshots).

## Categories

1. Schema design (relationships, cascade, optionality, identifier strategy)
2. Migration safety (`SchemaMigrationPlan`, `NSMappingModel`, real-data testing)
3. Threading & context (`@ModelActor`, background contexts, object IDs across threads)
4. Fetch efficiency (`fetchLimit`, `propertiesToFetch`, prefetching, N+1 prevention)
5. Predicate quality (`#Predicate`, no string-format with user input)
6. Batch operations (`NSBatchInsertRequest`, transactions, merge after batch)
7. CloudKit sync (`NSPersistentCloudKitContainer`, record zones, `CKShare`, subscriptions)
8. Conflict resolution & merge (`NSMergePolicy`, field-level merge)
9. Storage location & encryption (`NSPersistentStoreFileProtectionKey`, SQLCipher, App Group containers)
10. Backup & data lifecycle (`isExcludedFromBackupKey`, Delete Account wipe)

## Severity (default mapping)

| Issue | Severity |
|---|---|
| Migration that could corrupt or destroy user data | Critical |
| Data race causing crashes | Critical |
| CloudKit schema incompatibility preventing sync | Critical |
| Sensitive data unencrypted in shared container | Critical |
| Missing Delete Account data wipe | Critical |
| Main-thread blocking on fetch on primary surface | High |
| N+1 fetch on a frequently-visited list | High |
| Missing `NSMergePolicy` (silent data loss) | High |
| Cache files included in iCloud backup | High |
| Suboptimal but functional patterns | Medium |
| UserDefaults used for structured data | Medium |
| Style improvements | Low |

## Sprint Mapping

Baseline `P0/P1/Deferred`. **Migration findings are
sequencing-sensitive** — shipped migrations cannot be reverted; the
recommendation must be forward-compatible. Test migrations against
real user data snapshots before shipping.

## Inherent Limitations

Schema design is partly subjective. Static review catches schema
correctness, threading correctness, and clear performance issues but
cannot benchmark fetch performance — `runtime` verification with
`-com.apple.CoreData.SQLDebug 1` or SwiftData equivalents is required
to confirm magnitude.

## References

- Subagent: [`../../subagents/audit-apple-persistence.md`](../../subagents/audit-apple-persistence.md)
- SwiftData: https://developer.apple.com/documentation/swiftdata
- Core Data: https://developer.apple.com/documentation/coredata
- NSPersistentCloudKitContainer: https://developer.apple.com/documentation/coredata/nspersistentcloudkitcontainer
- CloudKit: https://developer.apple.com/documentation/cloudkit
- SwiftData migrations: https://developer.apple.com/documentation/swiftdata/schemamigrationplan
- Core Data performance: https://developer.apple.com/documentation/coredata/optimizing_core_data_performance
- GRDB: https://github.com/groue/GRDB.swift
