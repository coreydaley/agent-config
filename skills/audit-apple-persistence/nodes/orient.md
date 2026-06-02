# Node: orient

Phase 1 of the framework — run audit-specific tooling into `$AUDIT_DIR/tooling-raw/` and build a brief orientation note. **Apple persistence has Phase 1 tooling but no emergency-exit gate** — the persistence audit always proceeds to Phase 2.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
TO=$(bash ~/.claude/lib/audit-runner.sh timeout-bin)
mkdir -p "$AUDIT_DIR/tooling-raw"
[ -z "$TO" ] && echo "⚠️ no timeout command available; install via 'brew install coreutils' for tool timeouts" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

## Steps

### 1. Run Phase 1 tooling

Apple persistence "tooling" is mostly source-tree surveying — what stack(s) are in use, where the model files live, fetch / threading / merge patterns, UserDefaults misuse signal. There are no SAST tools that meaningfully cover persistence design. Document what's missing in `STATUS.md`. **Never block on a missing tool.**

```bash
# Detect persistence stack in use.
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

# Core Data model files (the *.xcdatamodeld is a directory — list it).
find "$PROJECT_CWD" -name "*.xcdatamodeld" -not -path '*/.*' 2>/dev/null \
  > "$AUDIT_DIR/tooling-raw/coredata-models.txt"

# Fetch patterns — predicates, fetchLimit usage, @Query / FetchRequest sites.
{
  echo "=== NSFetchRequest / FetchRequest / @Query patterns ===";
  grep -rn "NSFetchRequest\|FetchRequest\|@Query" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== Predicates ===";
  grep -rn "NSPredicate(\|#Predicate {" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -50;
  echo;
  echo "=== fetchLimit usage ===";
  grep -rn "fetchLimit" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
} > "$AUDIT_DIR/tooling-raw/fetch-patterns.txt"

# Merge policy + background context patterns.
{
  echo "=== Merge policy ===";
  grep -rn "mergePolicy\|NSMergePolicy" --include="*.swift" "$PROJECT_CWD" 2>/dev/null;
  echo;
  echo "=== Background contexts ===";
  grep -rn "performBackgroundTask\|newBackgroundContext\|@ModelActor" \
    --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -30;
} > "$AUDIT_DIR/tooling-raw/threading-patterns.txt"

# UserDefaults misuse signal — structured data stored in defaults.
grep -rn "UserDefaults" --include="*.swift" "$PROJECT_CWD" 2>/dev/null | head -100 \
  > "$AUDIT_DIR/tooling-raw/userdefaults-usage.txt"

# Target-platform detection — which Apple platforms this project targets.
PLATFORMS=""
for kind in IPHONEOS MACOSX WATCHOS TVOS XROS; do
  if grep -rqE "^[[:space:]]*${kind}_DEPLOYMENT_TARGET" "$PROJECT_CWD" \
       --include='*.pbxproj' --include='*.xcconfig' 2>/dev/null; then
    case "$kind" in
      IPHONEOS) PLATFORMS="$PLATFORMS iOS";;
      MACOSX)   PLATFORMS="$PLATFORMS macOS";;
      WATCHOS)  PLATFORMS="$PLATFORMS watchOS";;
      TVOS)     PLATFORMS="$PLATFORMS tvOS";;
      XROS)     PLATFORMS="$PLATFORMS visionOS";;
    esac
  fi
done
if [ -f "$PROJECT_CWD/Package.swift" ]; then
  for p in iOS macOS watchOS tvOS visionOS macCatalyst; do
    grep -qE "\.${p}\(" "$PROJECT_CWD/Package.swift" && PLATFORMS="$PLATFORMS $p"
  done
fi
PLATFORMS=$(echo "$PLATFORMS" | tr ' ' '\n' | sort -u | tr '\n' ',' | sed 's/^,//;s/,$//')
scripts/walk.sh set --state "$STATE" --key target_platforms --value "${PLATFORMS:-unknown}"
echo "Detected target platforms: ${PLATFORMS:-unknown}" >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

### 2. Emergency-exit check

**None.** Persistence has no Phase 1 emergency trigger — schema or migration risks are flagged as Critical findings in Phase 2, not as a halt-before-Phase-2 gate. Always take the `proceed` edge.

```bash
EMERGENCY=0
```

### 3. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and any obvious sub-paths (`*.xcodeproj/`, `Package.swift`)
- Which persistence stack(s) are in use per `persistence-stack.txt`
- For Core Data: any `*.xcdatamodeld` directories; current model version visible in the bundle
- For SwiftData: `Schema` declarations and any `SchemaMigrationPlan` if migrations exist
- Detected CloudKit usage — note whether it's via `NSPersistentCloudKitContainer` (managed) or direct `CKDatabase` (manual)
- Whether merge policy is set explicitly anywhere
- Whether `fetchLimit` is used at all
- Any test fixtures or test stores

This is for the user's situational awareness, not a persisted artifact.

**If no persistence stack is found**: tell the user, note it in `STATUS.md`, but still proceed to Phase 2 (reviewers may catch a hand-rolled `sqlite3_` path or a wrong-tool-for-the-job `UserDefaults` schema).

### 4. Persist any run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "$EMERGENCY"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/persistence-stack.txt`, `coredata-models.txt`, `fetch-patterns.txt`, `threading-patterns.txt`, `userdefaults-usage.txt`
- `$AUDIT_DIR/tooling-raw/STATUS.md` documents skipped tools (or absent timeout binary)
- Walker state has `emergency_exit=0`

## Outgoing edges

- **`proceed`** → `independent_reviews`. The only edge persistence ever takes from orient.
- **`emergency`** → `emergency_exit`. Never taken; persistence has no emergency trigger. The edge exists for graph uniformity with other audits.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- A grep times out → captured per-file; orient proceeds. Phase 2 reviewers see the partial output.
- All surveying fails (permission errors, etc.) → `STATUS.md` documents the degradation; orient still proceeds. Phase 2 reviewers do more manual reading.
