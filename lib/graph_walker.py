#!/usr/bin/env python3
"""Walker for skills built on the DOT-graph state-machine pattern.

The walker is the structural enforcer for skills like /sprint-self-review.
It reads a graph.dot file, maintains a state file recording the current node
plus a transition history, and validates every transition against the graph
before recording it. Skills call this from each node's prose to advance
state — invalid transitions are refused with a list of valid alternatives.

The walker is skill-agnostic. Any skill adopting the dot-graph pattern can
use this lib by pointing at its own graph.dot and a per-run state file.

Usage:

    python3 graph_walker.py init \\
        --graph path/to/graph.dot \\
        --state path/to/.walk-state.json \\
        [--start-node init]

    python3 graph_walker.py transition \\
        --state path/to/.walk-state.json \\
        --from <node-id> \\
        --to <node-id> \\
        [--condition <edge-condition-label>]

    python3 graph_walker.py where \\
        --state path/to/.walk-state.json

    python3 graph_walker.py history \\
        --state path/to/.walk-state.json

State file shape (JSON):

    {
      "graph_path": "...",
      "current_node": "decide",
      "started_at": "ISO-8601",
      "history": [
        {
          "from": "init",
          "to": "compute_diff",
          "condition": null,
          "at": "ISO-8601"
        },
        ...
      ],
      "extra": {}
    }

`extra` is reserved for skills to stash their own per-run state without
colliding with walker invariants (e.g. iteration counter, run ID).
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

# DOT parsing — same patterns as scripts/validate.py would use.
_NODE_DECL_RE = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[", re.MULTILINE)
_EDGE_RE = re.compile(
    r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*->\s*([a-zA-Z_][a-zA-Z0-9_]*)"
    r"(?:\s*\[(?P<attrs>[^\]]*)\])?",
    re.MULTILINE,
)
_LABEL_RE = re.compile(r'label\s*=\s*"([^"]*)"')
_DOT_KEYWORDS = {"node", "edge", "graph", "digraph", "subgraph", "strict"}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _parse_graph(path: Path) -> tuple[set[str], list[tuple[str, str, str | None]]]:
    """Return (nodes, edges).

    Edges are 3-tuples: (source, target, condition_label_or_None).
    The condition is the cleaned-up label string from the edge's `label=`
    attribute if present, or None.
    """
    text = path.read_text()
    nodes = {
        n for n in _NODE_DECL_RE.findall(text)
        if n.lower() not in _DOT_KEYWORDS
    }
    edges: list[tuple[str, str, str | None]] = []
    for match in _EDGE_RE.finditer(text):
        src, dst, attrs = match.group(1), match.group(2), match.group("attrs")
        if src.lower() in _DOT_KEYWORDS or dst.lower() in _DOT_KEYWORDS:
            continue
        label: str | None = None
        if attrs:
            lab = _LABEL_RE.search(attrs)
            if lab:
                label = lab.group(1).replace("\\n", " ").strip()
        edges.append((src, dst, label))
    return nodes, edges


def _load_state(path: Path) -> dict:
    if not path.exists():
        die(f"state file not found: {path}. Run `init` first.")
    return json.loads(path.read_text())


def _save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2) + "\n")


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def cmd_init(args: argparse.Namespace) -> int:
    graph_path = Path(args.graph).resolve()
    state_path = Path(args.state).resolve()
    if not graph_path.exists():
        die(f"graph not found: {graph_path}")
    nodes, _edges = _parse_graph(graph_path)
    if args.start_node not in nodes:
        die(f"start node '{args.start_node}' not declared in graph")
    state = {
        "graph_path": str(graph_path),
        "current_node": args.start_node,
        "started_at": _now(),
        "history": [],
        "extra": {},
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    _save_state(state_path, state)
    print(f"OK. Initialized at node '{args.start_node}'.")
    print(f"State: {state_path}")
    return 0


def cmd_transition(args: argparse.Namespace) -> int:
    state_path = Path(args.state).resolve()
    state = _load_state(state_path)
    graph_path = Path(state["graph_path"])
    if not graph_path.exists():
        die(f"graph referenced by state no longer exists: {graph_path}")
    nodes, edges = _parse_graph(graph_path)

    src, dst, cond = args.source, args.target, args.condition

    # 1. The "from" must match where we currently are.
    if state["current_node"] != src:
        die(
            f"current node is '{state['current_node']}', not '{src}'. "
            f"Cannot transition from a node we aren't at."
        )

    # 2. Some edge from src to dst must exist.
    matching = [e for e in edges if e[0] == src and e[1] == dst]
    if not matching:
        valid = sorted({
            f"{s} -> {d}" + (f" [{c}]" if c else "")
            for s, d, c in edges if s == src
        })
        msg = f"no edge from '{src}' to '{dst}'."
        if valid:
            msg += " Valid transitions from '" + src + "':\n  " + "\n  ".join(valid)
        else:
            msg += f" '{src}' is a sink (no outgoing edges)."
        die(msg)

    # 3. If a condition was named, it must match a real edge label.
    if cond is not None:
        cond_match = [e for e in matching if e[2] == cond]
        if not cond_match:
            valid_conds = sorted({c or "<unlabeled>" for _, _, c in matching})
            die(
                f"condition '{cond}' is not a valid label on '{src} -> {dst}'. "
                f"Valid: {', '.join(valid_conds)}"
            )

    # 4. Record the transition.
    state["history"].append({
        "from": src,
        "to": dst,
        "condition": cond,
        "at": _now(),
    })
    state["current_node"] = dst
    _save_state(state_path, state)

    cond_str = f" [{cond}]" if cond else ""
    print(f"OK. {src} -> {dst}{cond_str}")
    print(f"Now at: {dst}")
    return 0


def cmd_where(args: argparse.Namespace) -> int:
    state = _load_state(Path(args.state).resolve())
    print(state["current_node"])
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    state = _load_state(Path(args.state).resolve())
    if not state["history"]:
        print("(no transitions recorded yet)")
        return 0
    for entry in state["history"]:
        cond = f" [{entry['condition']}]" if entry["condition"] else ""
        print(f"{entry['at']}  {entry['from']} -> {entry['to']}{cond}")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    """Store a key/value in the state file's `extra` dict.

    Skills use this to persist run-scoped variables (pr_number, base_ref,
    iteration counters, etc.) so they survive across tool calls and sessions.
    """
    state_path = Path(args.state).resolve()
    state = _load_state(state_path)
    state.setdefault("extra", {})
    state["extra"][args.key] = args.value
    _save_state(state_path, state)
    print(f"OK. extra.{args.key} = {args.value}")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    """Print a key's value from the state file's `extra` dict.

    Exits non-zero if the key is unset, so shell `if !` patterns work.
    """
    state = _load_state(Path(args.state).resolve())
    val = state.get("extra", {}).get(args.key)
    if val is None:
        die(f"extra.{args.key} is not set", code=2)
    print(val)
    return 0


def cmd_dump(args: argparse.Namespace) -> int:
    """Print the full state file as JSON (for debugging or audit)."""
    state = _load_state(Path(args.state).resolve())
    print(json.dumps(state, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="graph_walker",
        description="Walker for skills built on the DOT-graph state-machine pattern.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="initialize a new run state")
    p_init.add_argument("--graph", required=True)
    p_init.add_argument("--state", required=True)
    p_init.add_argument("--start-node", default="init")
    p_init.set_defaults(func=cmd_init)

    p_trans = sub.add_parser("transition", help="record and validate a transition")
    p_trans.add_argument("--state", required=True)
    p_trans.add_argument("--from", dest="source", required=True)
    p_trans.add_argument("--to", dest="target", required=True)
    p_trans.add_argument("--condition", default=None)
    p_trans.set_defaults(func=cmd_transition)

    p_where = sub.add_parser("where", help="print the current node")
    p_where.add_argument("--state", required=True)
    p_where.set_defaults(func=cmd_where)

    p_hist = sub.add_parser("history", help="print the transition history")
    p_hist.add_argument("--state", required=True)
    p_hist.set_defaults(func=cmd_history)

    p_set = sub.add_parser("set", help="set a key/value in extra state")
    p_set.add_argument("--state", required=True)
    p_set.add_argument("--key", required=True)
    p_set.add_argument("--value", required=True)
    p_set.set_defaults(func=cmd_set)

    p_get = sub.add_parser("get", help="get a key from extra state")
    p_get.add_argument("--state", required=True)
    p_get.add_argument("--key", required=True)
    p_get.set_defaults(func=cmd_get)

    p_dump = sub.add_parser("dump", help="print the full state file as JSON")
    p_dump.add_argument("--state", required=True)
    p_dump.set_defaults(func=cmd_dump)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
