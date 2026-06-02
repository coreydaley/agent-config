#!/usr/bin/env python3
"""One-shot mechanical patch: insert a `plane-audit-ingest` step between
the `verify` and `handoff` nodes in every audit-apple-* skill.

For each skill:
  1. graph.dot — declare an `ingest` process node; rewrite the
     `verify -> handoff [label="ok"]` edge to flow through ingest.
  2. nodes/ingest.md — write the canonical sidecar prose.
  3. graph.svg — re-render via `dot`.
  4. SKILL.md — update the edge-conditions table to point `ok` at
     ingest (best-effort; idempotent).

Idempotent — re-running on already-patched skills is a no-op.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"


INGEST_NODE_DECL = """    ingest              [shape=box, style="rounded,filled", fillcolor="#e1f5fe",
                         label="ingest\\n(plane-audit-ingest:\\nREPORT.md → audit work-items)"];
"""

OLD_EDGE_RE = re.compile(
    r"^\s*verify\s*->\s*handoff\s*\[label=\"ok\"\];\s*$", re.MULTILINE
)

NEW_EDGES = """    verify              -> ingest              [label="ok"];
    ingest              -> handoff;"""

# Insertion anchor: right after the terminal-node declaration. Matches the
# canonical audit-apple-* graph.dot from the dot-graph skill pattern.
TERMINAL_DECL_RE = re.compile(
    r"^(    terminal\s+\[shape=doublecircle[^;]*?;\s*)$",
    re.MULTILINE | re.DOTALL,
)


INGEST_NODE_MD = """# Node: ingest

Invoke `/plane-audit-ingest` against this audit's `$AUDIT_DIR`. Parses
the just-verified `REPORT.md` into Plane-shaped work-item files under
`$AUDIT_DIR/work-items/` plus an `INGEST.md` manifest. Audit-scoped only
— does NOT touch the project work-items pool (promotion is the separate
`/plane-audit-promote` step, run manually).

This node runs **after** `verify` passes, so REPORT.md is guaranteed to
exist and be non-empty. Ingest failures are non-fatal — the audit
artifacts are still good; only the plane-side post-processing failed.
The hand-off message will note the status.

## Inputs

- Walker state: `audit_dir`

```bash
AUDIT_DIR=$(scripts/walk.sh get --state "$STATE" --key audit_dir)
```

## Steps

### 1. Honor the opt-out env var

```bash
if [ "${PLANE_INGEST_SKIP:-0}" = "1" ]; then
  scripts/walk.sh set --state "$STATE" --key ingest_status --value "skipped"
  scripts/walk.sh set --state "$STATE" --key ingest_log --value "skipped via PLANE_INGEST_SKIP=1"
  scripts/walk.sh transition --state "$STATE" --from ingest --to handoff
  exit 0
fi
```

### 2. Run plane-audit-ingest

```bash
INGEST_SCRIPT="$HOME/.claude/skills/plane-audit-ingest/scripts/ingest.py"
if [ ! -f "$INGEST_SCRIPT" ]; then
  scripts/walk.sh set --state "$STATE" --key ingest_status --value "unavailable"
  scripts/walk.sh set --state "$STATE" --key ingest_log --value "plane-audit-ingest script not found at $INGEST_SCRIPT"
else
  INGEST_LOG="$AUDIT_DIR/.ingest.log"
  if python3 "$INGEST_SCRIPT" "$AUDIT_DIR" > "$INGEST_LOG" 2>&1; then
    scripts/walk.sh set --state "$STATE" --key ingest_status --value "ok"
  else
    scripts/walk.sh set --state "$STATE" --key ingest_status --value "failed"
  fi
  scripts/walk.sh set --state "$STATE" --key ingest_log --value "$(cat "$INGEST_LOG")"
fi
```

## Outputs

- `$AUDIT_DIR/work-items/*.md` — one per finding (on success)
- `$AUDIT_DIR/INGEST.md` — manifest (on success)
- `$AUDIT_DIR/.ingest.log` — captured stdout/stderr
- Walker state: `ingest_status` ∈ {ok, failed, skipped, unavailable}, `ingest_log`

## Outgoing edges

- → `handoff` (always — single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from ingest --to handoff
```

## Failure modes

Non-fatal by design:

- **Parse error / unknown audit-name** → `ingest_status=failed`, log
  captured. Handoff message includes a "Plane ingest failed" note;
  audit is still useful via `/plane-audit-ingest <audit-dir>` rerun
  after the parser is fixed.
- **plane-audit-ingest script missing** → `ingest_status=unavailable`.
  Likely means `make all` wasn't run in agent-config. Same handoff
  note; same fallback.

## Notes

- This node is **the only auto-Plane step**. Promotion into the
  project pool (`/plane-audit-promote`) stays manual on purpose so
  the user can review the audit-scoped work items first.
- The opt-out env var `PLANE_INGEST_SKIP=1` exists for cases where
  the user is iterating on the audit's REPORT.md format and doesn't
  want repeated ingestions polluting the work-items dir.
"""


HANDOFF_INGEST_BLURB = """\nIf `INGEST_STATUS=failed` or `INGEST_STATUS=unavailable`, add to the warnings:\n\n```\n> - **Plane ingest not run**: audit-scoped work items were not created.\n>   Run `/plane-audit-ingest <audit-dir>` to ingest manually.\n```\n"""


def patch_graph(graph: Path) -> bool:
    text = graph.read_text()
    if "    ingest " in text:
        return False  # already patched
    # Insert the ingest node declaration after the terminal decl.
    m = TERMINAL_DECL_RE.search(text)
    if not m:
        print(f"  warn: no terminal decl anchor in {graph}", file=sys.stderr)
        return False
    insertion = m.group(1) + "\n" + INGEST_NODE_DECL
    text2 = text[:m.start()] + insertion + text[m.end():]
    # Replace the verify->handoff edge with the through-ingest pair.
    text3, n = OLD_EDGE_RE.subn(NEW_EDGES, text2, count=1)
    if n == 0:
        print(f"  warn: no verify->handoff edge in {graph}", file=sys.stderr)
        return False
    graph.write_text(text3)
    return True


def patch_skill_md(skill_md: Path) -> bool:
    """Best-effort: rewrite the `verify → handoff: ok` edge-condition
    bullet to `verify → ingest: ok` + add ingest line. Idempotent."""
    text = skill_md.read_text()
    if "verify → ingest" in text or "verify -> ingest" in text:
        return False
    # The canonical line in audit-apple-*/SKILL.md
    for pat, repl in [
        ("- `verify → handoff`: `ok`",
         "- `verify → ingest`: `ok`\n- `ingest → handoff`: (single outgoing edge)"),
    ]:
        if pat in text:
            text = text.replace(pat, repl, 1)
            skill_md.write_text(text)
            return True
    return False


def render_svg(skill_dir: Path) -> bool:
    """Re-render graph.svg via dot. Skips silently if dot is unavailable."""
    graph = skill_dir / "graph.dot"
    svg = skill_dir / "graph.svg"
    try:
        subprocess.run(["dot", "-Tsvg", str(graph), "-o", str(svg)], check=True)
        return True
    except FileNotFoundError:
        print("  warn: graphviz `dot` not installed; SVG not re-rendered", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"  warn: dot failed: {e}", file=sys.stderr)
        return False


def main() -> int:
    audit_dirs = sorted(SKILLS.glob("audit-apple-*"))
    patched_count = 0
    for d in audit_dirs:
        if not d.is_dir():
            continue
        graph = d / "graph.dot"
        if not graph.exists():
            continue
        print(f"=== {d.name} ===")
        graph_patched = patch_graph(graph)
        print(f"  graph.dot: {'patched' if graph_patched else 'already / skipped'}")

        node_md = d / "nodes" / "ingest.md"
        node_md.parent.mkdir(parents=True, exist_ok=True)
        if not node_md.exists():
            node_md.write_text(INGEST_NODE_MD)
            print(f"  nodes/ingest.md: created")
        else:
            print(f"  nodes/ingest.md: exists")

        skill_md = d / "SKILL.md"
        if skill_md.exists():
            skill_patched = patch_skill_md(skill_md)
            print(f"  SKILL.md edge bullet: {'patched' if skill_patched else 'already / not found'}")

        rendered = render_svg(d)
        print(f"  graph.svg: {'rendered' if rendered else 'skipped'}")

        if graph_patched:
            patched_count += 1

    print(f"\n--- Patched {patched_count}/{len(audit_dirs)} audit-apple-* skill(s) ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
