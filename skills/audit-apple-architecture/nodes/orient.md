# Node: orient

Phase 1 of the framework — record an orientation note in `$AUDIT_DIR/tooling-raw/STATUS.md` and survey the project shape before Phase 2. **This audit runs no Phase 1 tooling — architecture findings come from manual code reading. The survey step identifies SwiftUI / Concurrency / Modules patterns to guide reviewers.**

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
```

## Steps

### 1. Record the no-tooling status

This audit runs no Phase 1 tooling — architecture findings come from manual code reading. The survey step identifies SwiftUI / Concurrency / Modules patterns to guide reviewers.

```bash
cat > "$AUDIT_DIR/tooling-raw/STATUS.md" <<'EOF'
# Phase 1 tooling — apple-architecture

This audit runs no Phase 1 tooling. Architecture findings come from
manual code reading by both reviewers in Phase 2. The survey step
below identifies SwiftUI / Concurrency / Modules patterns to guide the
reviewers.

Reviewers should still note any existing swift-format configuration,
SwiftLint rules, or Build Settings (SWIFT_STRICT_CONCURRENCY=complete,
SWIFT_VERSION, deployment target) since they constrain what patterns
are even possible.
EOF
```

### 2. Survey

In conversational text (not a persisted file), note:

- Resolved scope (`$PROJECT_CWD`) and Apple project structure: `Package.swift` (+ `targets:` / `dependencies:`), `*.xcodeproj/`, Swift Package module count and layout
- `SWIFT_STRICT_CONCURRENCY` setting and Swift version — if strict, expect Sendable / actor compliance and findings are about pattern quality; if minimal, expect raw correctness gaps too
- Target platforms from `Package.swift`'s `platforms:` array or `Info.plist`
- The navigation pattern in use (`NavigationStack` / `NavigationSplitView` / `TabView` / coordinator-style)
- State-management style: `@Observable` macro (modern), `ObservableObject` (legacy), TCA (`Reducer`), custom flux-style
- Dependency direction: are views importing concrete models, or protocols? are modules layered or feature-sliced?
- At least 5 representative Swift files to skim (especially top-level app entry, primary view tree, primary view model) before generalizing

This is for the user's situational awareness, not a persisted artifact.

### 3. Target-platform detection

```bash
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

### 4. Persist run-scoped state Phase 2 needs

```bash
scripts/walk.sh set --state "$STATE" --key emergency_exit --value "0"
```

## Outputs

- `$AUDIT_DIR/tooling-raw/STATUS.md` documents the no-tooling decision
- Walker state has `emergency_exit=0`

## Outgoing edges

- **`proceed`** → `independent_reviews`. Always — this audit has no emergency-exit conditions.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- `$AUDIT_DIR/tooling-raw/` not writable → bail; init should have created it.
