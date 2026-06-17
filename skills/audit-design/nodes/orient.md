# Node: orient

Phase 1 of the framework. **Design is a pure-LLM audit — there is no Phase 1 tooling.** This node is essentially a no-op aside from a brief survey and a Swift/Apple detection step that drives the heuristic-priority order downstream. Still write `$AUDIT_DIR/tooling-raw/STATUS.md` so the verify gate sees a consistent shape across audits.

## Inputs

- `$AUDIT_DIR`, `$PROJECT_CWD` from walker state
- The scope's source tree (read-only)

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
PROJECT_CWD=$(scripts/walk.sh get --state "$STATE" --key project_cwd)
```

## Steps

### 1. No Phase 1 tooling

Design has no automated SAST / scanner / linter equivalent appropriate for the heuristic-anchored review this audit performs. Record the no-op in `STATUS.md`:

```bash
cat > "$AUDIT_DIR/tooling-raw/STATUS.md" <<'EOF'
# Tooling Status — design

Design is a pure-LLM audit. No automated tooling was run in Phase 1.

The review sub-agent performs the entire review
manually in Phase 2 against the heuristic priority order documented in
the skill and the review prompt.
EOF
```

### 2. Detect Apple project (drives heuristic priority)

If the scope is a Swift / Apple-platform project, Apple HIG is **promoted to priority 2** (above Nielsen) in the heuristic anchor order. Detect via `Package.swift`, `*.xcodeproj/`, or a meaningful `*.swift` file count.

```bash
APPLE_PROJECT=0
if [ -f "$PROJECT_CWD/Package.swift" ] \
   || ls "$PROJECT_CWD"/*.xcodeproj >/dev/null 2>&1 \
   || [ "$(find "$PROJECT_CWD" -name '*.swift' -not -path '*/.*' 2>/dev/null | head -20 | wc -l | tr -d ' ')" -ge 10 ]; then
  APPLE_PROJECT=1
fi
scripts/walk.sh set --state "$STATE" --key apple_project --value "$APPLE_PROJECT"
echo "" >> "$AUDIT_DIR/tooling-raw/STATUS.md"
echo "Apple project detected: $([ "$APPLE_PROJECT" -eq 1 ] && echo yes || echo no)" \
  >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

The review sub-agent in Phase 2 reads this state and the review prompt instructs it to promote HIG accordingly.

### 3. Detect explicit design system (informs heuristic priority 1)

The audit's top-priority anchor is **the project's own design system**. Survey for token files, component libraries, and documented conventions:

```bash
DESIGN_SYSTEM_HINTS=()
for hint in \
  "design-system" "design_system" "designsystem" \
  "tokens.json" "tokens.css" "tokens.scss" \
  "tailwind.config.js" "tailwind.config.ts" \
  "Storybook" ".storybook" \
  "DesignTokens" "Assets.xcassets/Colors.colorset"; do
  found=$(find "$PROJECT_CWD" -maxdepth 4 -iname "$hint" -not -path '*/.*' 2>/dev/null | head -3)
  if [ -n "$found" ]; then
    DESIGN_SYSTEM_HINTS+=("$found")
  fi
done
{
  echo ""
  echo "Design system hints:"
  if [ "${#DESIGN_SYSTEM_HINTS[@]}" -eq 0 ]; then
    echo "- none found (heuristic priority 1 falls through to cross-pattern consistency)"
  else
    for h in "${DESIGN_SYSTEM_HINTS[@]}"; do echo "- $h"; done
  fi
} >> "$AUDIT_DIR/tooling-raw/STATUS.md"
```

### 4. Survey

In conversational text (not a persisted artifact), note:

- Resolved scope (`$PROJECT_CWD`) and obvious frontend sub-paths
- Frontend file types present: HTML, CSS/SCSS/LESS/SASS, components (.jsx/.tsx/.vue/.svelte/.astro), Angular templates, SwiftUI views, UIKit view controllers
- Whether an explicit design system was found (token files, component library, documented conventions, Figma references)
- Whether the project is Swift / Apple — and what that does to the heuristic priority order
- If **no frontend files found**: notify the user and stop without creating reviewer artifacts. The audit's scope is empty.

### 5. No emergency-exit conditions

Design has no live-credential / runtime-blocker class of finding that should halt the audit before Phase 2. The `orient → emergency_exit` edge is never taken from this audit; always take `proceed`.

## Outputs

- `$AUDIT_DIR/tooling-raw/STATUS.md` exists and documents the no-tooling status, the Apple-project detection, and any design-system hints
- Walker state has `apple_project` flag set

## Outgoing edges

- **`proceed`** → `independent_reviews`. Always taken — design has no emergency-exit conditions.

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to independent_reviews --condition proceed
```

## Failure modes

- No frontend files in scope → tell the user and stop the walk before transitioning. Do not produce reviewer artifacts for an empty scope.
