#!/usr/bin/env python3
"""Compare this run's requirement counts with the previous run's.

Each run directory holds a requirements.json written by the agent:
  {"run_date": "YYYY-MM-DD", "postings": N,
   "requirements": [{"name": "...", "count": n, "examples": [...]}, ...]}

Prints JSON with new, gone, rising and falling requirements, comparing shares
of postings (count / postings) so runs of different sizes compare fairly.

Usage: compare_runs.py --current RUN_DIR [--previous RUN_DIR]
Without --previous, the newest sibling run directory older than --current is used.
"""

import argparse
import json
import sys
from pathlib import Path


def load(run: Path) -> dict:
    data = json.loads((run / "requirements.json").read_text())
    total = max(data.get("postings", 0), 1)
    return {r["name"]: r["count"] / total for r in data["requirements"]}


def run_key(run: Path) -> tuple[str, int]:
    """Run directories are YYYY-MM-DD with an optional -N suffix for repeat runs."""
    date, n = run.name[:10], run.name[11:]
    return date, int(n) if n.isdigit() else 1


def previous_run(current: Path) -> Path | None:
    older = sorted((p for p in current.parent.iterdir()
                    if p.is_dir() and (p / "requirements.json").exists() and run_key(p) < run_key(current)),
                   key=run_key)
    return older[-1] if older else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--current", type=Path, required=True)
    ap.add_argument("--previous", type=Path)
    ap.add_argument("--threshold", type=float, default=0.10,
                    help="change in share of postings that counts as rising/falling (default 0.10)")
    args = ap.parse_args()

    prev_dir = args.previous or previous_run(args.current)
    cur = load(args.current)
    if not prev_dir:
        print(json.dumps({"previous": None, "note": "first run; nothing to compare"}, indent=2))
        return 0
    prev = load(prev_dir)
    pct = lambda x: round(100 * x)  # noqa: E731
    result = {
        "previous": prev_dir.name,
        "new": sorted(n for n in cur if n not in prev),
        "gone": sorted(n for n in prev if n not in cur),
        "rising": sorted(({"name": n, "from_pct": pct(prev[n]), "to_pct": pct(cur[n])}
                          for n in cur if n in prev and cur[n] - prev[n] >= args.threshold),
                         key=lambda r: r["to_pct"] - r["from_pct"], reverse=True),
        "falling": sorted(({"name": n, "from_pct": pct(prev[n]), "to_pct": pct(cur[n])}
                           for n in cur if n in prev and prev[n] - cur[n] >= args.threshold),
                          key=lambda r: r["from_pct"] - r["to_pct"], reverse=True),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
