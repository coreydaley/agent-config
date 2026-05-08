#!/usr/bin/env python3
"""Validate the sprint-self-review state machine graph.

Checks structural integrity of graph.dot:
- Every node ID referenced by an edge is also declared as a node.
- Every declared node has a corresponding nodes/<id>.md sidecar.
- Terminal nodes (declared via shape=doublecircle) have no outgoing edges.
- Every node except `init` has at least one incoming edge (no orphans).

Run from anywhere; paths are resolved relative to this script.
Exits non-zero on any integrity failure.
"""

import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DOT_PATH = SKILL_DIR / "graph.dot"
NODES_DIR = SKILL_DIR / "nodes"

# A node declaration looks like:  init [shape=box, ...];  on one or more lines
# We match the identifier (greedy non-whitespace) up to its opening bracket.
NODE_DECL_RE = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[", re.MULTILINE)
# An edge looks like:  src -> dst [label="..."];  (label optional).
EDGE_RE = re.compile(
    r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*->\s*([a-zA-Z_][a-zA-Z0-9_]*)",
    re.MULTILINE,
)
# Terminal nodes are declared with shape=doublecircle.
TERMINAL_DECL_RE = re.compile(
    r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[[^\]]*shape=doublecircle",
    re.MULTILINE | re.DOTALL,
)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)


def main() -> int:
    if not DOT_PATH.exists():
        fail(f"graph.dot not found at {DOT_PATH}")
        return 1

    text = DOT_PATH.read_text()
    # DOT reserved keywords that show up at the start of attribute-default
    # statements (`node [...]`, `edge [...]`, `graph [...]`). They are not
    # node identifiers.
    DOT_KEYWORDS = {"node", "edge", "graph", "digraph", "subgraph", "strict"}
    nodes: set[str] = {
        n for n in NODE_DECL_RE.findall(text) if n.lower() not in DOT_KEYWORDS
    }
    edges: list[tuple[str, str]] = EDGE_RE.findall(text)
    terminals: set[str] = set(TERMINAL_DECL_RE.findall(text))

    errors = 0

    # 1. Every edge endpoint must be a declared node.
    for src, dst in edges:
        if src not in nodes:
            fail(f"edge source not declared: {src} -> {dst}")
            errors += 1
        if dst not in nodes:
            fail(f"edge target not declared: {src} -> {dst}")
            errors += 1

    # 2. Every node must have a sidecar markdown file.
    for n in sorted(nodes):
        sidecar = NODES_DIR / f"{n.replace('_', '-')}.md"
        if not sidecar.exists():
            # Also accept underscored filenames.
            alt = NODES_DIR / f"{n}.md"
            if not alt.exists():
                fail(f"node {n} has no sidecar at {sidecar} (or {alt})")
                errors += 1

    # 3. Terminal nodes have no outgoing edges.
    for src, _ in edges:
        if src in terminals:
            fail(f"terminal node {src} has an outgoing edge (should be a sink)")
            errors += 1

    # 4. Every node except `init` has at least one incoming edge.
    targets = {dst for _, dst in edges}
    for n in nodes:
        if n == "init":
            continue
        if n not in targets:
            fail(f"node {n} has no incoming edges (orphan)")
            errors += 1

    if errors:
        print(f"\n{errors} error(s) found.", file=sys.stderr)
        return 1

    print(
        f"OK: {len(nodes)} nodes, {len(edges)} edges, "
        f"{len(terminals)} terminal node(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
